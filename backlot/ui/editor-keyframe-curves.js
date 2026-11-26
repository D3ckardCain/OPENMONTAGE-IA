export function curveProgress(point,amount){
  const p=Math.max(0,Math.min(1,amount));
  if(point.interpolation==='hold')return p>=1?1:0;
  if(point.interpolation==='smooth')return p*p*(3-2*p);
  if(point.interpolation!=='bezier'||p===0||p===1)return p;
  const [x1,y1,x2,y2]=point.control_points;let lo=0,hi=1;
  for(let i=0;i<24;i++){const t=(lo+hi)/2,x=3*(1-t)**2*t*x1+3*(1-t)*t*t*x2+t**3;if(x<p)lo=t;else hi=t;}
  const t=(lo+hi)/2;return 3*(1-t)**2*t*y1+3*(1-t)*t*t*y2+t**3;
}
export function curveValue(points,axis,time){
  const next=points.findIndex(p=>p.seconds>time);if(next===0)return points[0][axis];if(next<0)return points.at(-1)[axis];
  const a=points[next-1],b=points[next],p=curveProgress(a,(time-a.seconds)/(b.seconds-a.seconds));return a[axis]+(b[axis]-a[axis])*p;
}
export const readControls=row=>row.querySelector('select').value==='bezier'?{control_points:[...row.querySelectorAll('[data-bezier-input]')].map(i=>Number(i.value))}:{};
export function addBezierEditor(cell,point,change){
  const box=document.createElement('div');cell.append(box);const inputs=[];
  for(const [i,label]of ['X1','Y1','X2','Y2'].entries()){const input=document.createElement('input');input.type='number';input.min=0;input.max=1;input.step=.01;input.value=(point.control_points||[.25,.1,.25,1])[i];input.dataset.bezierInput='';input.setAttribute('aria-label',`Bézier ${label}`);input.style.width='5em';input.oninput=()=>{draw();change();};box.append(input);inputs.push(input);}
  const svg=document.createElementNS('http://www.w3.org/2000/svg','svg');svg.setAttribute('viewBox','0 0 100 100');svg.style.cssText='width:100px;height:100px;touch-action:none;border:1px solid #8b949e';svg.setAttribute('role','img');svg.setAttribute('aria-label','Curva Bézier; arrastra sus controles o edita los números');box.prepend(svg);
  const node=(tag,attrs)=>{const n=document.createElementNS(svg.namespaceURI,tag);for(const [k,v]of Object.entries(attrs))n.setAttribute(k,v);svg.append(n);return n;};
  function draw(){const [x1,y1,x2,y2]=inputs.map(i=>Math.max(0,Math.min(1,Number(i.value))));svg.replaceChildren();node('path',{d:`M0,100 L${100*x1},${100*(1-y1)} M100,0 L${100*x2},${100*(1-y2)}`,stroke:'#8b949e',fill:'none'});node('path',{d:`M0,100 C${100*x1},${100*(1-y1)} ${100*x2},${100*(1-y2)} 100,0`,stroke:'#79c0ff',fill:'none','stroke-width':2});for(const [index,x,y]of [[0,x1,y1],[2,x2,y2]]){const c=node('circle',{cx:x*100,cy:(1-y)*100,r:5,fill:'#ffa657'});c.dataset.control=index;}}
  let drag=null;svg.onpointerdown=e=>{if(e.target.dataset.control===undefined)return;drag=Number(e.target.dataset.control);svg.setPointerCapture(e.pointerId);};svg.onpointermove=e=>{if(drag===null)return;const r=svg.getBoundingClientRect();inputs[drag].value=Math.max(0,Math.min(1,(e.clientX-r.left)/r.width)).toFixed(4);inputs[drag+1].value=Math.max(0,Math.min(1,1-(e.clientY-r.top)/r.height)).toFixed(4);draw();change();};svg.onpointerup=svg.onpointercancel=()=>{drag=null;};draw();return box;
}
