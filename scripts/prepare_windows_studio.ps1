# Source preparation only. No Python, dependencies, applications or models are executed.
[CmdletBinding()]
param(
    [string]$Destination = 'C:\OPENMONTAGE-IA',
    [string]$Revision = '',
    [string]$ArchivePath = '',
    [string]$BlenderPath = ''
)
$ErrorActionPreference = 'Stop'
$repo = 'D3ckardCain/OPENMONTAGE-IA'
$branch = 'feat/local-agent-research-foundation'
$Destination = [IO.Path]::GetFullPath($Destination)
if (Test-Path -LiteralPath $Destination) { throw "La carpeta ya existe: $Destination. No se sobrescribe." }
$parent = Split-Path -Parent $Destination
if (-not (Test-Path -LiteralPath $parent -PathType Container)) { throw 'No existe la carpeta padre del destino.' }
if ($BlenderPath) {
    if (-not [IO.Path]::IsPathRooted($BlenderPath) -or
        [IO.Path]::GetFileName($BlenderPath) -ine 'blender.exe' -or
        -not (Test-Path -LiteralPath $BlenderPath -PathType Leaf)) { throw 'BlenderPath debe indicar el blender.exe existente.' }
}
if ($ArchivePath -and -not $Revision) { throw 'Un archivo local requiere Revision explicita.' }
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
if (-not $Revision) {
    $ref = [uri]::EscapeDataString($branch)
    $head = Invoke-RestMethod -Uri "https://api.github.com/repos/$repo/commits/$ref" -Headers @{ 'User-Agent' = 'OPENMONTAGE-local-setup' }
    $Revision = $head.sha
}
if ($Revision -notmatch '^[a-fA-F0-9]{40}$') { throw 'Revision debe ser un commit SHA de 40 caracteres.' }
$Revision = $Revision.ToLowerInvariant()
$stage = Join-Path $parent ('.openmontage-preparacion-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stage | Out-Null
try {
    if (-not $ArchivePath) {
        $ArchivePath = Join-Path $stage 'source.zip'
        Write-Host "Descargando codigo: $Revision"
        Invoke-WebRequest -UseBasicParsing -Uri "https://github.com/$repo/archive/$Revision.zip" -OutFile $ArchivePath
    }
    $ArchivePath = [IO.Path]::GetFullPath($ArchivePath)
    $archiveHash = (Get-FileHash -LiteralPath $ArchivePath -Algorithm SHA256).Hash.ToLowerInvariant()
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::OpenRead($ArchivePath)
    $rootName = "OPENMONTAGE-IA-$Revision"
    $expanded = Join-Path $stage 'expanded'
    $prefix = [IO.Path]::GetFullPath($expanded) + [IO.Path]::DirectorySeparatorChar
    try {
        foreach ($entry in $zip.Entries) {
            $name = $entry.FullName.Replace('\', '/')
            if (-not $name.StartsWith("$rootName/", [StringComparison]::Ordinal) -or $name.Contains(':')) { throw "Entrada ZIP fuera de la raiz esperada: $name" }
            $target = [IO.Path]::GetFullPath((Join-Path $expanded $name))
            if (-not $target.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) { throw 'Ruta ZIP fuera del destino.' }
            if (($name.Split('/') | Where-Object { $_ -eq '..' }).Count -gt 0) { throw 'Ruta ZIP con ascenso de directorio.' }
        }
    } finally { $zip.Dispose() }
    [IO.Compression.ZipFile]::ExtractToDirectory($ArchivePath, $expanded)
    $source = Join-Path $expanded $rootName
    foreach ($required in @('OPENMONTAGE_ESTUDIO.cmd', 'backlot/server.py', 'lib/production_studio.py', 'requirements.txt')) {
        if (-not (Test-Path -LiteralPath (Join-Path $source $required) -PathType Leaf)) { throw "Falta archivo del estudio: $required" }
    }
    if ($BlenderPath) {
        $config = Join-Path $source '.backlot/studio'
        New-Item -ItemType Directory -Path $config -Force | Out-Null
        $binding = @{ blender = @{ executable = $BlenderPath } } | ConvertTo-Json -Depth 4
        [IO.File]::WriteAllText((Join-Path $config 'applications.json'), $binding, (New-Object Text.UTF8Encoding($false)))
    }
    $receipt = @{
        repository = $repo; branch = $branch; revision = $Revision
        archive_sha256 = $archiveHash; prepared_at = [DateTime]::UtcNow.ToString('o')
        status = 'code_prepared'; dependencies_installed = $false; models_installed = $false
    } | ConvertTo-Json
    [IO.File]::WriteAllText((Join-Path $source 'INSTALACION_LOCAL.json'), $receipt, (New-Object Text.UTF8Encoding($false)))
    [IO.Directory]::Move($source, $Destination)
    Write-Host "CODIGO PREPARADO: $Destination"
    Write-Host 'Siguiente paso: preparar Python y dependencias en un entorno aislado.'
} finally {
    if (Test-Path -LiteralPath $stage) { Remove-Item -LiteralPath $stage -Recurse -Force }
}
