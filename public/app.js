'use strict';
let db, topic='panorama', months=36;
const $ = s => document.querySelector(s);
const nf = new Intl.NumberFormat('es-AR',{maximumFractionDigits:2,minimumFractionDigits:1});
const esc = v => String(v ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const period = (d,daily=false) => new Date(d+'T12:00:00').toLocaleDateString('es-AR',daily?{day:'numeric',month:'short',year:'numeric'}:{month:'long',year:'numeric'});
const pct = n => nf.format(n)+'%';
const definitions = [
 {key:'ipc',topic:'inflacion',title:'Inflación mensual',unit:'Variación mensual del IPC nacional, %',type:'bar',scale:100},
 {key:'ipc',topic:'inflacion',title:'Inflación interanual',unit:'Variación compuesta de doce meses, %',type:'line',yoy:true},
 {key:'nucleo',topic:'inflacion',title:'Inflación núcleo',unit:'Variación mensual, %',type:'bar',scale:100},
 {key:'regulados',topic:'inflacion',title:'Precios regulados',unit:'Variación mensual, %',type:'bar',scale:100},
 {key:'emae',topic:'actividad',title:'Nivel de actividad económica',unit:'EMAE desestacionalizado · 2004=100',type:'line'},
 {key:'emae',topic:'actividad',title:'Actividad: variación mensual',unit:'EMAE desestacionalizado · variación mensual, %',type:'bar',change:true},
 {key:'emae_original',topic:'actividad',title:'Actividad: variación interanual',unit:'EMAE original · variación interanual, %',type:'line',change:12},
 {key:'dolar',topic:'cambio',title:'Tipo de cambio mayorista',unit:'Referencia BCRA · pesos por dólar',type:'line'},
 {key:'dolar',topic:'cambio',title:'Movimiento diario del dólar',unit:'Variación frente a la observación anterior, %',type:'line',change:true}
];
function pointsFor(def){
 const src=db.series[def.key];if(!src)return[];
 let p=src.data.map(p=>({...p,value:p.value*(def.scale||1)}));
 if(def.yoy) p=p.slice(11).map((v,i)=>({...v,value:(src.data.slice(i,i+12).reduce((a,b)=>a*(1+b.value),1)-1)*100}));
 if(def.change){const n=def.change===true?1:def.change;p=p.slice(n).map((v,i)=>({...v,value:(v.value/src.data[i].value-1)*100}));}
 if(months&&p.length){let cutoff=new Date(p.at(-1).date+'T12:00:00');cutoff.setMonth(cutoff.getMonth()-months);p=p.filter(v=>new Date(v.date+'T12:00:00')>=cutoff);}
 return p;
}
function download(def){const p=pointsFor(def);const text='fecha;valor\r\n'+p.map(v=>v.date+';'+String(v.value).replace('.',',')).join('\r\n');const url=URL.createObjectURL(new Blob(['\ufeff'+text],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download=def.key+(def.yoy?'_interanual':def.change?'_variacion':'')+'.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function graph(def,index){
 const p=pointsFor(def);if(p.length<2)return '';
 const s=db.series[def.key],w=520,h=250,left=49,right=12,top=14,bottom=35,pw=w-left-right,ph=h-top-bottom;
 let min=Math.min(...p.map(v=>v.value)),max=Math.max(...p.map(v=>v.value));
 if(def.type==='bar'){min=Math.min(0,min);max=Math.max(0,max);}
 const pad=(max-min||1)*.12;max+=pad;if(def.type==='line')min-=pad;
 const x=i=>left+(p.length>1?i/(p.length-1):0)*pw;
 const y=v=>top+(max-v)/(max-min)*ph;
 let marks='';
 if(def.type==='line')marks=`<path class="plot-line" d="${p.map((v,i)=>(i?'L':'M')+x(i).toFixed(2)+','+y(v.value).toFixed(2)).join(' ')}"/>`;
 else{const step=pw/p.length,bw=step/1.55;marks=p.map((v,i)=>`<rect class="bar" x="${left+i*step+(step-bw)/2}" y="${Math.min(y(0),y(v.value))}" width="${bw}" height="${Math.max(.2,Math.abs(y(0)-y(v.value)))}"/>`).join('');}
 const tickIdx=[0,Math.round((p.length-1)/3),Math.round(2*(p.length-1)/3),p.length-1];
 const ticks=tickIdx.map((i,j)=>`<text x="${x(i)}" y="${h-10}" text-anchor="${j===0?'start':j===3?'end':'middle'}">${esc(new Date(p[i].date+'T12:00:00').toLocaleDateString('es-AR',{month:'short',year:'2-digit'}).replace(/\s+de\s+|\s/g,'-').replace('.',''))}</text>`).join('');
 const nums=[min,(min+max)/2,max].map(v=>`<text x="${left-10}" y="${y(v)+3}" text-anchor="end">${esc(nf.format(v))}</text>`).join('');
 const warning=s.status!=='verified'||s.lag_warning;
 return `<article class="chart-card"><div class="chart-head"><div><h3>${esc(def.title)}</h3><p class="chart-sub">${esc(def.unit)}</p></div><button class="download" data-download="${index}" aria-label="Descargar datos de ${esc(def.title)}">CSV ↓</button></div><div class="chart-wrap" data-chart="${index}"><svg viewBox="0 0 ${w} ${h}" role="img" aria-label="${esc(def.title)} entre ${esc(period(p[0].date))} y ${esc(period(p.at(-1).date))}"><line x1="${left}" y1="${h-bottom}" x2="${w-right}" y2="${h-bottom}" stroke="#0a2540" stroke-width="1"/>${nums}${marks}${ticks}<rect x="${left}" y="${top}" width="${pw}" height="${ph}" fill="transparent" class="hit-area"/></svg><div class="tooltip"></div></div><div class="chart-foot"><span>${esc(s.source)} · hasta ${esc(period(p.at(-1).date,s.frequency==='day'))}</span><span class="${warning?'stale':''}">${warning?'Copia conservada / revisar rezago':'Fuente consultada'}</span></div></article>`;
}
function render(){
 const wanted=topic==='panorama'?definitions.filter(d=>['Inflación mensual','Inflación interanual','Nivel de actividad económica','Tipo de cambio mayorista'].includes(d.title)):definitions.filter(d=>d.topic===topic);
 $('#charts').innerHTML=wanted.map(d=>graph(d,definitions.indexOf(d))).join('')||'<p class="empty">No hay observaciones disponibles para este tema.</p>';
 $('#topic-title').textContent=({panorama:'El panorama en gráficos',inflacion:'Inflación: ritmo y composición',actividad:'Actividad: nivel y movimiento',cambio:'Tipo de cambio: nivel y variación'})[topic];
 document.querySelectorAll('[data-topic]').forEach(b=>{b.classList.toggle('active',b.dataset.topic===topic);b.setAttribute('aria-pressed',String(b.dataset.topic===topic));});
 document.querySelectorAll('.masthead nav a').forEach(a=>{a.classList.toggle('selected',a.hash==='#'+topic);if(a.hash==='#'+topic)a.setAttribute('aria-current','page');else a.removeAttribute('aria-current');});
 document.querySelectorAll('[data-download]').forEach(b=>b.onclick=()=>download(definitions[Number(b.dataset.download)]));
 document.querySelectorAll('[data-chart]').forEach(wrap=>{
 const def=definitions[Number(wrap.dataset.chart)],p=pointsFor(def),svg=wrap.querySelector('svg'),tip=wrap.querySelector('.tooltip');
 svg.addEventListener('pointermove',e=>{const r=svg.getBoundingClientRect(),vx=(e.clientX-r.left)/r.width*520;const i=Math.max(0,Math.min(p.length-1,Math.round((vx-49)/(520-61)*(p.length-1))));tip.textContent=period(p[i].date,db.series[def.key].frequency==='day')+' · '+nf.format(p[i].value);tip.style.display='block';tip.style.left=Math.min(Math.max(0,e.clientX-r.left-60),Math.max(0,r.width-190))+'px';tip.style.top='20px';});
 svg.addEventListener('pointerleave',()=>tip.style.display='none');
 });
 const reports=db.report.sections.filter(s=>topic==='panorama'||s.topic===topic);
 $('#reports').innerHTML=reports.map((s,i)=>`<article class="report"><span class="report-num">0${i+1} / ${esc(({inflacion:'INFLACIÓN',actividad:'ACTIVIDAD',cambio:'TIPO DE CAMBIO'})[s.topic])}</span><h3>${esc(s.title)}</h3><p class="period">Dato de ${esc(period(s.period,s.topic==='cambio'))}</p><p>${esc(s.fact)}</p><p>${esc(s.reading)}</p><p class="report-limit"><strong>Hasta dónde llega la evidencia.</strong> ${esc(s.limit)}</p></article>`).join('');
}
function metrics(){
 const cards=[{key:'ipc',label:'Inflación',value:s=>pct(s.data.at(-1).value*100),unit:'Variación mensual · IPC nacional'},
 {key:'emae',label:'Actividad',value:s=>pct((s.data.at(-1).value/s.data.at(-2).value-1)*100),unit:'Variación mensual · EMAE desestacionalizado'},
 {key:'dolar',label:'Tipo de cambio',value:s=>'$ '+nf.format(s.data.at(-1).value),unit:'Pesos por dólar · mayorista de referencia'}];
 $('#metrics').innerHTML=cards.map(c=>{const s=db.series[c.key];return `<article class="metric"><p class="label">${c.label}</p><span class="arrow">↗</span><p class="number">${s?c.value(s):'Sin dato'}</p><p class="unit">${c.unit}</p><p class="period">${s?esc(period(s.data.at(-1).date,s.frequency==='day')):'Pendiente de fuente'}</p></article>`;}).join('');
}
function syncHash(){const hash=location.hash.slice(1);topic=['inflacion','actividad','cambio'].includes(hash)?hash:'panorama';if(db)render();}
window.addEventListener('hashchange',syncHash);
document.querySelectorAll('[data-topic]').forEach(b=>b.onclick=()=>{location.hash=b.dataset.topic;});
document.querySelectorAll('[data-months]').forEach(b=>b.onclick=()=>{months=Number(b.dataset.months);document.querySelectorAll('[data-months]').forEach(x=>{x.classList.toggle('active',x===b);x.setAttribute('aria-pressed',String(x===b));});if(db)render();});
const dialog=$('#newsletter-dialog');['#newsletter-open','#newsletter-details'].forEach(id=>$(id).onclick=()=>dialog.showModal());$('.close').onclick=()=>dialog.close();$('#dialog-ok').onclick=()=>dialog.close();dialog.addEventListener('click',e=>{if(e.target===dialog){const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close();}});
fetch('data.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json();}).then(data=>{
 db=data;const issues=Object.values(db.series).filter(s=>s.status!=='verified'||s.lag_warning).length;
 if(db.pilot?.email_active){
   document.querySelector('.newsletter-band>div:last-child>p').textContent='El envío privado del piloto superó una prueba de correo. El resumen está programado para los viernes; las suscripciones públicas todavía no están abiertas.';
   document.querySelector('#newsletter-dialog>p:not(.eyebrow)').textContent='El piloto utiliza ChatGPT en la nube para elaborar los análisis y Gmail conectado para el envío privado. La prueba inicial de correo fue verificada; el resumen semanal está programado para los viernes.';
 }
 $('#edition-date').textContent='Archivo consultado: '+new Date(db.generated_at).toLocaleString('es-AR',{dateStyle:'medium',timeStyle:'short',timeZone:'America/Argentina/Buenos_Aires'})+' (Argentina). Cada indicador tiene su propio período.';
 $('#load-status').textContent=issues?'Piloto con datos de referencia o fuentes con rezago. Consultá el período de cada indicador; esta vista no garantiza contener la última publicación oficial.':'Fuentes consultadas. Los indicadores tienen distintos períodos de referencia; revisá las fechas de cada tarjeta.';
 $('#load-status').classList.toggle('error',issues>0);
 $('#analysis-kind').textContent=db.report.label;
 $('#analysis-note').textContent=db.note||'Los hechos se calculan a partir de las series. La interpretación automática no cuenta con revisión humana y no identifica causalidad por sí sola.';
 if(db.report.kind==='ai')$('#method-ai').textContent='Los hechos se calculan con reglas y el texto interpretativo se genera con IA, sin revisión humana. Un control comprueba que se conserven los hechos y períodos y no se agreguen cifras en la interpretación. Ese control no garantiza que toda interpretación sea correcta.';
 $('#sources').innerHTML=Object.entries(db.series).map(([key,s])=>`<a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)} · ${esc(s.source)} ↗</a>`).join('');
 metrics();syncHash();
}).catch(()=>{$('#load-status').textContent='No se pudo cargar la base de datos. Reintentá más tarde o consultá el repositorio.';$('#load-status').classList.add('error');});
