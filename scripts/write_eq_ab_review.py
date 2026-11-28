"""Write one offline human A/B page beside two already verified MP4s."""
import argparse
from pathlib import Path

HTML='''<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Una escucha A/B · EQ y compresor</title>
<style>body{font:17px system-ui;background:#0d1117;color:#e6edf3;max-width:960px;margin:32px auto;padding:20px}button{background:#21262d;color:#e6edf3;border:1px solid #8b949e;border-radius:6px;padding:12px;cursor:pointer}button[aria-pressed=true]{border:2px solid #58a6ff}button:focus-visible{outline:3px solid #f2cc60}video{width:100%;margin:18px 0}p{line-height:1.55}output{display:block;margin:16px 0}</style>
<h1>Una sola escucha A/B</h1><p>Compara A y B con el mismo volumen del reproductor. Fíjate en el primer impacto, entre <strong>1,000 y 1,527 s</strong>. A usa bypass; B aplica EQ y compresor a ese mismo clip. El resto del montaje no cambia. No hay compensación automática de volumen.</p>
<button id="a" aria-pressed="true">A · Bypass</button> <button id="b" aria-pressed="false">B · EQ + compresor</button>
<output id="state" aria-live="polite">A · Bypass</output><video controls preload="metadata" src="A-bypass.mp4"></video>
<p>En este único A/B, indica cuál prefieres (A/B) y si notas distorsión o bombeo. La escucha humana sigue pendiente hasta tu respuesta.</p>
<p>Archivos locales de 4 s; sin red, modelos ni generación. Cambiar A/B conserva el instante de reproducción.</p>
<script>const v=document.querySelector('video'),state=document.querySelector('#state');let current='a';function select(id){if(id===current)return;const at=v.currentTime||0,play=!v.paused;v.pause();current=id;document.querySelector('#a').setAttribute('aria-pressed',String(id==='a'));document.querySelector('#b').setAttribute('aria-pressed',String(id==='b'));state.textContent=id==='a'?'A · Bypass':'B · EQ + compresor';v.addEventListener('loadedmetadata',()=>{v.currentTime=Math.min(at,v.duration);if(play)v.play().catch(e=>state.textContent=e.message);},{once:true});v.src=id==='a'?'A-bypass.mp4':'B-eq-compresor.mp4';v.load();}document.querySelector('#a').onclick=()=>select('a');document.querySelector('#b').onclick=()=>select('b');v.onerror=()=>state.textContent='No se pudo abrir el MP4 local. Conserva los tres archivos en esta carpeta.';</script></html>'''


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--directory',required=True,type=Path);args=parser.parse_args()
    for name in ('A-bypass.mp4','B-eq-compresor.mp4'):
        if not (args.directory/name).is_file():raise SystemExit('Falta '+name+'; no se genera ni descarga')
    path=args.directory/'escucha-ab.html'
    if path.exists():
        if path.read_text(encoding='utf-8')!=HTML:raise SystemExit('La página existente difiere; se conserva')
    else:path.write_text(HTML,encoding='utf-8')
    print(path.resolve())


if __name__=='__main__':main()
