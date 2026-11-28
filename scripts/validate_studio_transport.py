"""Isolated loopback probe. Never addresses 4750 or saved external paths."""
import sys,os,json,time,socket,subprocess,urllib.request,signal,asyncio
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

def child(work,fixed):
 work=work.resolve();work.relative_to((ROOT/'.runtime/qa').resolve())
 os.environ['OPENMONTAGE_PROJECTS_DIR']=str(work/'projects')
 from lib import production_studio as studio
 studio.CONFIG_DIR=work/'config'
 from lib import studio_editor as editor
 p=editor.create('Synthetic HTTP journal fixture')
 artifact=work/'projects'/p['project_id']/editor.ARTIFACT
 data=json.loads(artifact.read_text(encoding='utf-8'))
 data['events']=[{'origin':'user','operation':'synthetic','text':'x'*7500} for _ in range(12)]
 artifact.write_text(json.dumps(data),encoding='utf-8')
 from backlot.server import create_app
 import uvicorn
 app=create_app()
 send_results=[]
 def traced_proactor():
  loop=asyncio.ProactorEventLoop()
  send=loop._proactor.send
  def traced(sock,buf,flags=0):
   future=send(sock,buf,flags)
   def done(f):
    try:send_results.append({'requested':len(buf),'sent':f.result()})
    except BaseException as e:send_results.append({'requested':len(buf),'error':repr(e)})
   future.add_done_callback(done)
   return future
  loop._proactor.send=traced
  return loop
 if os.environ.get('QA_NO_BASE_MIDDLEWARE')=='1':
  app.user_middleware=[m for m in app.user_middleware if m.cls.__name__!='BaseHTTPMiddleware']
 @app.get('/__qa/diagnostics')
 async def diagnostics():
  connections=[]
  for c in server.server_state.connections:
   connections.append({'path':getattr(c,'scope',{}).get('path'),'buffer':c.transport.get_write_buffer_size(),'write_paused':c.flow.write_paused,'read_paused':c.flow.read_paused,'response_complete':getattr(c.cycle,'response_complete',None),'response_started':getattr(c.cycle,'response_started',None)})
  return {'loop':type(asyncio.get_running_loop()).__name__,'send_results':send_results,'connections':connections,'tasks':[repr(t) for t in asyncio.all_tasks()]}
 @app.post('/__qa/sigint')
 async def interrupt():
  asyncio.get_running_loop().call_later(.1,signal.raise_signal,signal.SIGINT)
  return {'signal':'SIGINT','synthetic_delivery':True}
 if os.environ.get('QA_RAW_ASGI')=='1':
  real_app=app
  async def app(scope,receive,send):
   if scope['type']=='http' and scope['path'].startswith('/api/studio/editor/'):
    from starlette.responses import JSONResponse
    await JSONResponse(data)(scope,receive,send)
   else:await real_app(scope,receive,send)
 sock=socket.socket();sock.bind(('127.0.0.1',0));assert sock.getsockname()[1]!=4750
 (work/'ready.json').write_text(json.dumps({'port':sock.getsockname()[1],'project':p['project_id'],'server_pid':os.getpid(),'launcher_pid':os.getppid(),'new_console':os.environ.get('QA_CONSOLE_SIGINT')=='1'}))
 if fixed:
  from backlot.runtime import StudioServer
  cls=StudioServer
 else:cls=uvicorn.Server
 if os.environ.get('QA_SELECTOR')=='1':
  asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
 config=uvicorn.Config(app,host='127.0.0.1',log_level='info',loop='asyncio:SelectorEventLoop' if os.environ.get('QA_SELECTOR')=='1' else 'auto')
 if os.environ.get('QA_TRACE_SEND')=='1':config.loop=traced_proactor
 if fixed:
  from backlot.server import hub
  server=cls(config,stop_notifications=hub.close)
 else:server=cls(config)
 server.run(sockets=[sock])

def probe(work,fixed=False,sse=True):
 work=work.resolve();work.relative_to((ROOT/'.runtime/qa').resolve())
 work.mkdir(parents=True,exist_ok=False)
 log=(work/'server.log').open('w',encoding='utf-8')
 native_console=os.name=='nt' and os.environ.get('QA_CONSOLE_SIGINT')=='1'
 options={'creationflags':getattr(subprocess,'CREATE_NO_WINDOW',0)}
 if native_console:
  startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
  options={'creationflags':subprocess.CREATE_NEW_CONSOLE,'startupinfo':startup}
 process=subprocess.Popen([sys.executable,'-B',__file__,'child',str(work),str(int(fixed))],cwd=ROOT,stdout=log,stderr=log,**options)
 streams=[];report={'launcher_pid':process.pid,'fixed':fixed,'sse':sse,'http':[]}
 try:
  for _ in range(100):
   if (work/'ready.json').exists():break
   if process.poll() is not None:raise RuntimeError((work/'server.log').read_text())
   time.sleep(.05)
  ready=json.loads((work/'ready.json').read_text());assert ready['port']!=4750
  report.update(port=ready['port'],server_pid=ready['server_pid'])
  base='http://127.0.0.1:'+str(ready['port'])
  op=urllib.request.build_opener(urllib.request.ProxyHandler({}))
  def request(path,method='GET',headers=None):return op.open(urllib.request.Request(base+path,method=method,headers=headers or {}),timeout=3)
  for _ in range(100):
   try:
    with request('/api/health') as r:r.read()
    break
   except (OSError,urllib.error.URLError):time.sleep(.05)
  if sse:
   for route in ['/api/library/events','/api/project/'+ready['project']+'/events']:
    stream=request(route);assert b'hello' in stream.readline();streams.append(stream)
  for headers in [{},{'Connection':'close'},{'Connection':'keep-alive'}]:
   for i in range(6):
    for route in ['/api/studio/queue','/api/studio/editor/'+ready['project']]:
     t=time.monotonic()
     try:
      chunks=[];expected=None
      with request(route,headers=headers) as response:
       expected=int(response.headers['Content-Length'])
       while True:
        chunk=response.read1(16384)
        if not chunk:break
        chunks.append(chunk)
       raw=b''.join(chunks);assert len(raw)==expected;json.loads(raw)
       report['http'].append({'route':route,'connection':headers.get('Connection','urllib default'),'bytes':len(raw),'seconds':round(time.monotonic()-t,3),'ok':True})
     except Exception as e:
      report['http'].append({'route':route,'connection':headers.get('Connection','urllib default'),'error':repr(e),'received':sum(map(len,chunks)),'expected':expected,'ok':False})
      with request('/__qa/diagnostics') as diag:report.setdefault('diagnostics',[]).append(json.load(diag))
      break
    else:continue
    break
  if native_console:
   result=subprocess.run([sys.executable,'-B',__file__,'console-sigint',str(work)],capture_output=True,text=True,timeout=5,creationflags=subprocess.CREATE_NO_WINDOW)
   if result.returncode:raise RuntimeError(result.stderr)
   report['signal_delivery']='Windows GenerateConsoleCtrlEvent CTRL_C_EVENT to the owned NEW console'
  else:
   with request('/__qa/sigint',method='POST') as r:r.read()
   report['signal_delivery']='signal.raise_signal(SIGINT) in isolated server main loop, not keyboard'
  t=time.monotonic()
  try:process.wait(timeout=2);report['exited_with_streams_open']=True
  except subprocess.TimeoutExpired:report['exited_with_streams_open']=False
  report['signal_wait_seconds']=round(time.monotonic()-t,3)
  for s in streams:s.close()
  streams=[]
  try:process.wait(timeout=5)
  except subprocess.TimeoutExpired:report['cleanup_forced']=True;os.kill(ready['server_pid'],signal.SIGTERM);process.wait(timeout=5)
  report['exit_code']=process.returncode
 finally:
  for s in streams:s.close()
  if process.poll() is None:
   if 'ready' in locals():os.kill(ready['server_pid'],signal.SIGTERM)
   else:process.terminate()
   process.wait(timeout=5)
  log.close()
  report['log']=(work/'server.log').read_text(encoding='utf-8')
  (work/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
 print(json.dumps({k:v for k,v in report.items() if k not in ('http','log','diagnostics')},indent=2),flush=True)
 print('HTTP',len(report['http']),'failures',sum(not r['ok'] for r in report['http']),flush=True)
 return report

if __name__=='__main__':
 if sys.argv[1]=='console-sigint':
  import ctypes
  work=Path(sys.argv[2]).resolve();work.relative_to((ROOT/'.runtime/qa').resolve())
  ready=json.loads((work/'ready.json').read_text())
  assert ready['new_console'] and ready['port']!=4750
  kernel=ctypes.WinDLL('kernel32',use_last_error=True)
  # ERROR_ACCESS_DENIED here also means this helper is already attached.
  # Detach only the disposable helper, then join the NEW console we own.
  kernel.FreeConsole()
  if not kernel.AttachConsole(ready['server_pid']):raise ctypes.WinError(ctypes.get_last_error())
  try:
   members=(ctypes.c_uint32*16)()
   count=kernel.GetConsoleProcessList(members,len(members))
   allowed={ready['server_pid'],ready['launcher_pid'],os.getpid(),os.getppid()}
   assert 0<count<=len(members) and ready['server_pid'] in members[:count]
   assert set(members[:count])<=allowed, 'Unexpected process in isolated console; refusing signal'
   if not kernel.SetConsoleCtrlHandler(None,True):raise ctypes.WinError(ctypes.get_last_error())
   if not kernel.GenerateConsoleCtrlEvent(0,0):raise ctypes.WinError(ctypes.get_last_error())
   time.sleep(.2)
  finally:kernel.FreeConsole()
 elif sys.argv[1]=='child':child(Path(sys.argv[2]),bool(int(sys.argv[3])))
 else:
  report=probe(Path(sys.argv[2]),fixed='--baseline' not in sys.argv,sse='--no-sse' not in sys.argv)
  raise SystemExit(int(not report['exited_with_streams_open'] or report['exit_code']!=0 or any(not r['ok'] for r in report['http'])))
