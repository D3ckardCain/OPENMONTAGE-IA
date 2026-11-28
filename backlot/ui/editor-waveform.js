// Peaks always come from decoded samples, never from clip names or placeholders.
export function makePeaks(channel,sampleRate,block=256){
  const count=Math.ceil(channel.length/block),low=new Float32Array(count),high=new Float32Array(count);
  for(let i=0;i<count;i++){
    let min=Infinity,max=-Infinity;
    for(let n=i*block;n<Math.min(channel.length,(i+1)*block);n++){min=Math.min(min,channel[n]);max=Math.max(max,channel[n]);}
    low[i]=min;high[i]=max;
  }
  return {low,high,sampleRate,block,duration:channel.length/sampleRate};
}
export function paintPeaks(canvas,peaks,start=0,end=peaks.duration){
  const ctx=canvas.getContext('2d'),width=canvas.width,height=canvas.height;
  ctx.clearRect(0,0,width,height);ctx.strokeStyle='#3fb950';ctx.beginPath();
  for(let x=0;x<width;x++){
    const first=Math.max(0,Math.floor((start+(end-start)*x/width)*peaks.sampleRate/peaks.block));
    const last=Math.min(peaks.low.length,Math.max(first+1,Math.ceil((start+(end-start)*(x+1)/width)*peaks.sampleRate/peaks.block)));
    let min=0,max=0;for(let n=first;n<last;n++){min=Math.min(min,peaks.low[n]);max=Math.max(max,peaks.high[n]);}
    ctx.moveTo(x,(1+min)*height/2);ctx.lineTo(x,(1+max)*height/2);
  }
  ctx.stroke();
}
export function signalLevel(samples){
  let sum=0,peak=0;for(const sample of samples){sum+=sample*sample;peak=Math.max(peak,Math.abs(sample));}
  const rms=samples.length?Math.sqrt(sum/samples.length):0;
  return {rms,peak,dbfs:rms>0?Math.max(-96,20*Math.log10(rms)):-96};
}
