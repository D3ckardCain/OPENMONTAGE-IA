$ErrorActionPreference = 'Stop'
$prepare = Join-Path $PSScriptRoot '../../scripts/prepare_windows_studio.ps1'
$temp = Join-Path ([IO.Path]::GetTempPath()) ('openmontage-test-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temp | Out-Null
Add-Type -AssemblyName System.IO.Compression.FileSystem
$revision = 'a' * 40
function Make-Archive([string]$Name, [bool]$Missing, [bool]$Traversal) {
    $path = Join-Path $temp "$Name.zip"
    $zip = [IO.Compression.ZipFile]::Open($path, [IO.Compression.ZipArchiveMode]::Create)
    try {
        foreach ($file in @('OPENMONTAGE_ESTUDIO.cmd', 'backlot/server.py', 'lib/production_studio.py', 'requirements.txt')) {
            if ($Missing -and $file -eq 'OPENMONTAGE_ESTUDIO.cmd') { continue }
            $entry = $zip.CreateEntry("OPENMONTAGE-IA-$revision/$file")
            $writer = New-Object IO.StreamWriter($entry.Open())
            $writer.Write('fixture'); $writer.Dispose()
        }
        if ($Traversal) { $null = $zip.CreateEntry("OPENMONTAGE-IA-$revision/../../escape.txt") }
    } finally { $zip.Dispose() }
    return $path
}
function Assert([bool]$Value, [string]$Message) { if (-not $Value) { throw $Message } }
try {
    $archive = Make-Archive 'valid' $false $false
    $blender = Join-Path $temp 'blender.exe'
    Set-Content -LiteralPath $blender -Value 'fixture'
    $dest = Join-Path $temp 'studio'
    & $prepare -Destination $dest -Revision $revision -ArchivePath $archive -BlenderPath $blender
    $receipt = Get-Content -Raw (Join-Path $dest 'INSTALACION_LOCAL.json') | ConvertFrom-Json
    Assert ($receipt.revision -eq $revision -and -not $receipt.dependencies_installed) 'Invalid receipt'
    $binding = Get-Content -Raw (Join-Path $dest '.backlot/studio/applications.json') | ConvertFrom-Json
    Assert ($binding.blender.executable -eq $blender) 'Missing Blender binding'
    $rejected = $false
    try { & $prepare -Destination $dest -Revision $revision -ArchivePath $archive } catch { $rejected = $true }
    Assert $rejected 'Existing target accepted'
    Assert ((Get-Content -Raw (Join-Path $dest 'requirements.txt')).Trim() -eq 'fixture') 'Existing target changed'
    foreach ($case in @('missing', 'traversal')) {
        $bad = Make-Archive $case ($case -eq 'missing') ($case -eq 'traversal')
        $badDest = Join-Path $temp $case
        $rejected = $false
        try { & $prepare -Destination $badDest -Revision $revision -ArchivePath $bad } catch { $rejected = $true }
        Assert $rejected "Invalid archive accepted: $case"
        Assert (-not (Test-Path $badDest)) "Failed copy left target: $case"
    }
    Assert (-not (Test-Path (Join-Path $temp 'escape.txt'))) 'Traversal escaped'
    Assert (@(Get-ChildItem $temp -Filter '.openmontage-preparacion-*').Count -eq 0) 'Staging leaked'
    Write-Host 'PASS: source copy, receipt, Blender binding, existing target, missing launcher, traversal, cleanup.'
} finally { Remove-Item -LiteralPath $temp -Recurse -Force }
