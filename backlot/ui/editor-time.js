// Timeline arithmetic shared by ruler, cursor and source-time editing controls.
export function clipDuration(clip, edl, video=true) {
  const raw=(clip.out_seconds-clip.in_seconds)/clip.speed;
  return video?Math.round(raw*edl.output.fps)/edl.output.fps:raw;
}
export function videoDuration(edl){return edl.cuts.reduce((sum,c)=>sum+clipDuration(c,edl),0);}
export function timelineEnd(edl){return Math.max(videoDuration(edl),0,...edl.audio_tracks.map(c=>c.start_seconds+clipDuration(c,edl,false)),...edl.cues.map(c=>c.end_seconds));}
export function fitZoom(edl,width){return Math.max(.001,Math.min(10000,(Math.max(64,width)-50)/Math.max(1/edl.output.fps,timelineEnd(edl))));}
export function tickStep(zoom,fps){
  const target=80/zoom, power=10**Math.floor(Math.log10(target));
  return Math.max(1/fps,[1,2,5,10].map(n=>n*power).find(n=>n>=target));
}
export function clipStart(edl,clip,track){return track==='audio'?clip.start_seconds:edl.cuts.slice(0,edl.cuts.indexOf(clip)).reduce((sum,c)=>sum+clipDuration(c,edl),0);}
export function sourceTime(edl,clip,track,time){return clip.in_seconds+(time-clipStart(edl,clip,track))*clip.speed;}
export function splitAtCursor(edl,clip,track,cursor){
  const at=sourceTime(edl,clip,track,cursor), minimum=track==='video'?clip.speed/edl.output.fps:.001;
  if(at<clip.in_seconds+minimum-1e-8||at>clip.out_seconds-minimum+1e-8)throw Error('El cursor debe estar dentro del clip y dejar al menos un fotograma a cada lado.');
  return {id:clip.id,track,at};
}
