// Edits the existing layer document; preview/export use the same render graph.
import {curveValue,readControls,addBezierEditor} from './editor-keyframe-curves.js';
export function initializeLayerKeyframes({root,q,getEdl,getProject,has,run}){
  const panel=document.createElement('details');panel.id='edit-layer-keyframes';panel.hidden=true;
  panel.innerHTML='<summary>Keyframes de posición de la capa</summary><p>Tiempo absoluto en la fuente (s). Se conserva al recortar y quitar silencios. La interpolación de cada fila llega hasta la siguiente. Prepara vista previa para comprobar el resultado audiovisual.</p><div style="overflow:auto"><table><thead><tr><th>Fuente (s)</th><th>X</th><th>Y</th><th>Interpolación</th><th>Acción</th></tr></thead><tbody></tbody></table></div><button type="button" data-action="add">Añadir punto</button><button type="button" data-action="save">Guardar keyframes</button><button type="button" data-action="remove">Quitar keyframes</button><svg viewBox="0 0 320 100" role="img" aria-label="Curvas de posición X e Y" style="width:100%;height:100px"></svg><p data-status role="status"></p>';
  const note=document.createElement('p');note.textContent='La curva activa sustituye X/Y estáticos y el movimiento lineal; quita los keyframes para volver a esos controles.';panel.append(note);
  const heading=document.createElement('th');heading.textContent='Bézier';panel.querySelector('thead tr').insertBefore(heading,panel.querySelector('thead tr').lastChild);
  root.append(panel);const body=panel.querySelector('tbody'),svg=panel.querySelector('svg'),status=panel.querySelector('[data-status]');let key;
  const layer=()=>getEdl().layers?.find(l=>l.id===q('edit-layer-select').value);
  const points=()=>[...body.rows].map(row=>({seconds:Number(row.querySelector('[name=seconds]').value),x:Number(row.querySelector('[name=x]').value),y:Number(row.querySelector('[name=y]').value),interpolation:row.querySelector('select').value,...readControls(row)}));
  function curve(){
    const values=points().sort((a,b)=>a.seconds-b.seconds);svg.replaceChildren();if(values.length<2)return;
    const start=values[0].seconds,span=values.at(-1).seconds-start;if(!(span>0))return;
    for(const [axis,color]of [['x','#79c0ff'],['y','#ffa657']]){
      const path=document.createElementNS('http://www.w3.org/2000/svg','path');const samples=[];
      for(let i=0;i<=100;i++){
        const t=start+span*i/100;
        samples.push(`${i?'L':'M'}${i*3.2},${95-curveValue(values,axis,t)*90}`);
      }
      path.setAttribute('d',samples.join(' '));path.setAttribute('fill','none');path.setAttribute('stroke',color);path.setAttribute('stroke-width','2');svg.append(path);
    }
  }
  function row(point){
    const tr=document.createElement('tr');
    for(const field of ['seconds','x','y']){const td=tr.insertCell(),input=document.createElement('input');input.type='number';input.name=field;input.min='0';input.step='.001';input.value=point[field];input.setAttribute('aria-label',field==='seconds'?'Tiempo en fuente':`Posición ${field.toUpperCase()}`);input.style.width='6em';td.append(input);}
    const select=document.createElement('select');select.setAttribute('aria-label','Interpolación');for(const [value,label]of [['linear','Lineal'],['hold','Mantener'],['smooth','Suave'],...(has('layer_transform_keyframes')?[['bezier','Bézier']]:[])])select.add(new Option(label,value));select.value=point.interpolation;tr.insertCell().append(select);
    const box=addBezierEditor(tr.insertCell(),point,curve);box.hidden=select.value!=='bezier';select.onchange=()=>{box.hidden=select.value!=='bezier';curve();};
    const button=document.createElement('button');button.type='button';button.textContent='Quitar punto';button.onclick=()=>{tr.remove();curve();};tr.insertCell().append(button);body.append(tr);
  }
  body.addEventListener('input',curve);body.addEventListener('change',curve);
  panel.querySelector('[data-action=add]').onclick=()=>{const l=layer();if(!l)return;const values=points();row({seconds:values.length?Math.min(getEdl().sources[l.source_id].duration,values.at(-1).seconds+1):l.in_seconds,x:l.x,y:l.y,interpolation:'linear'});curve();};
  const submit=async value=>{const l=layer();if(!l)return;const focused=panel.contains(document.activeElement);status.textContent='';try{await run('layer_position_keyframes',{id:l.id,keyframes:value});if(focused&&(document.activeElement===document.body||document.activeElement.disabled))body.querySelector('input')?.focus();}catch(error){status.textContent=error.message;}};
  panel.querySelector('[data-action=save]').onclick=()=>submit({clock:'source_seconds',points:points()});
  panel.querySelector('[data-action=remove]').onclick=()=>submit(null);
  function draw(){
    const l=layer();panel.hidden=!has('layer_position_keyframes')||!l;
    if(panel.hidden)return;const next=JSON.stringify([getProject(),l]);if(key===next)return;key=next;body.replaceChildren();
    for(const point of l.position_keyframes?.points||[{seconds:l.in_seconds,x:l.x,y:l.y,interpolation:'linear'},{seconds:l.out_seconds,x:l.x,y:l.y,interpolation:'linear'}])row(point);
    status.textContent='';panel.querySelector('[data-action=remove]').disabled=!l.position_keyframes;curve();
  }
  return {draw};
}
