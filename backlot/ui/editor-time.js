// Timeline arithmetic shared by ruler, cursor and source-time editing controls.
import {forwardClock,inverseClock} from './editor-smooth-clock.js';
export function clipDuration(clip, edl, video=true) {
  if(clip.time_warp){const w=clip.time_warp;if(w.role==='primary')return w.map.output_frames/w.map.fps;return forwardClock(w.map,w.old_start_seconds+(clip.out_seconds-clip.in_seconds)/w.old_speed)-forwardClock(w.map,w.old_start_seconds);}
  const raw=(clip.out_seconds-clip.in_seconds)/clip.speed;
  return video?Math.round(raw*edl.output.fps)/edl.output.fps:raw;
}
export function videoDuration(edl){return edl.cuts.reduce((sum,c)=>sum+clipDuration(c,edl),0);}
export function timelineEnd(edl){return Math.max(videoDuration(edl),0,...edl.audio_tracks.map(c=>c.start_seconds+clipDuration(c,edl,false)),...edl.cues.map(c=>c.end_seconds),...(edl.markers||[]).map(m=>m.seconds));}
export function fitZoom(edl,width){return Math.max(.001,Math.min(10000,(Math.max(64,width)-50)/Math.max(1/edl.output.fps,timelineEnd(edl))));}
export function tickStep(zoom,fps){
  const target=80/zoom, power=10**Math.floor(Math.log10(target));
  return Math.max(1/fps,[1,2,5,10].map(n=>n*power).find(n=>n>=target));
}
export function clipStart(edl,clip,track){return track==='audio'?clip.start_seconds:edl.cuts.slice(0,edl.cuts.indexOf(clip)).reduce((sum,c)=>sum+clipDuration(c,edl),0);}
export function sourceTime(edl,clip,track,time){if(clip.time_warp){const w=clip.time_warp;return clip.in_seconds+(inverseClock(w.map,time)-w.old_start_seconds)*w.old_speed;}return clip.in_seconds+(time-clipStart(edl,clip,track))*clip.speed;}
export function sourceToTimeline(edl,clip,track,time){if(clip.time_warp){const w=clip.time_warp;return forwardClock(w.map,w.old_start_seconds+(time-clip.in_seconds)/w.old_speed);}return clipStart(edl,clip,track)+(time-clip.in_seconds)/clip.speed;}
export function splitAtCursor(edl,clip,track,cursor){
  const at=sourceTime(edl,clip,track,cursor), minimum=track==='video'?clip.speed/edl.output.fps:.001;
  if(at<clip.in_seconds+minimum-1e-8||at>clip.out_seconds-minimum+1e-8)throw Error('El cursor debe estar dentro del clip y dejar al menos un fotograma a cada lado.');
  return {id:clip.id,track,at};
}
export function snapTime(time,points,zoom,enabled=true){
  if(!enabled)return time;
  let result=time,distance=8/zoom;
  for(const point of points){const d=Math.abs(point-time);if(d<=distance){result=point;distance=d;}}
  return result;
}
export function editPoints(edl,cursor=0,nearTime=null){
  const points=[0,cursor];let t=0;
  if(Number.isFinite(nearTime))points.push(Math.round(nearTime*edl.output.fps)/edl.output.fps);
  for(const clip of edl.cuts){points.push(t);t+=clipDuration(clip,edl);points.push(t);}
  for(const clip of edl.audio_tracks)points.push(clip.start_seconds,clip.start_seconds+clipDuration(clip,edl,false));
  for(const cue of edl.cues)points.push(cue.start_seconds,cue.end_seconds);
  // Composition intervals use montage time, not the source file's in/out.
  const interval=(start,end)=>{if(Number.isFinite(start)&&Number.isFinite(end)&&start>=0&&end>start)points.push(start,end);};
  for(const layer of edl.layers||[]){
    if(Number.isFinite(layer.speed)&&layer.speed>0&&Number.isFinite(layer.in_seconds)&&Number.isFinite(layer.out_seconds))
      interval(layer.start_seconds,layer.start_seconds+(layer.out_seconds-layer.in_seconds)/layer.speed);
  }
  for(const title of edl.titles||[])interval(title.start_seconds,title.end_seconds);
  return points;
}
export function trimByDelta(edl,clip,track,edge,delta){
  if(edge!=='in'&&edge!=='out')throw Error('Borde desconocido');
  if(track==='audio'&&edge==='in')throw Error('El borde de entrada de audio requiere recorte y desplazamiento atómicos; usa el inspector.');
  const step=track==='video'?clip.speed/edl.output.fps:.001;
  const amount=track==='video'?Math.round(delta*edl.output.fps)/edl.output.fps:delta;
  let start=clip.in_seconds,end=clip.out_seconds;
  if(edge==='in')start=Math.max(0,Math.min(end-step,start+amount*clip.speed));
  else end=Math.max(start+step,Math.min(clip.kind==='gap'?clip.gap_duration:edl.sources[clip.source_id].duration,end+amount*clip.speed));
  return {id:clip.id,track,in_seconds:start,out_seconds:end};
}
export function moveCue(edl,cue,start){
  const length=cue.end_seconds-cue.start_seconds;
  const at=Math.max(0,Math.min(videoDuration(edl)-length,start));
  return {start_seconds:Math.round(at*1000)/1000,end_seconds:Math.round((at+length)*1000)/1000,text:cue.text};
}
export function previewMatches(preview,state){
  if(preview.render_sha256&&state.render_sha256)return preview.render_sha256===state.render_sha256;
  if(preview.edit_sha256&&state.edit_sha256)return preview.edit_sha256===state.edit_sha256;
  return preview.revision===state.revision;
}
export function audioTrimByDelta(edl,clip,delta){
  const start=Math.max(0,Math.min(clip.out_seconds-.001,clip.in_seconds+delta*clip.speed));
  const bounded=Math.max(clip.in_seconds-clip.start_seconds*clip.speed,start);
  return {id:clip.id,track:'audio',in_seconds:bounded,out_seconds:clip.out_seconds,
    start_seconds:clip.start_seconds+(bounded-clip.in_seconds)/clip.speed};
}
