// Version-pinned adapter to the SAME compiler, runtime, browser and seek as HyperFrames snapshot.
import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
const repo=path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const dist=path.join(repo,'node_modules/hyperframes/dist');
const version=JSON.parse(fs.readFileSync(path.join(dist,'../package.json'))).version;
if(version!=='0.9.32') throw new Error('QA runtime adapter requires HyperFrames 0.9.32; revalidate before upgrading');
const {bundleToSingleHtml}=await import(path.join(dist,'compiler-ETXRTUQC.js'));
const {serveStaticProjectHtml}=await import(path.join(dist,'chunk-6MTSP2XE.js'));
const {openSettledCompositionPage,seekCompositionTimeline}=await import(path.join(dist,'chunk-LJMTEZOP.js'));
const [hf, storyboard, optionsPath]=process.argv.slice(2);
const sb=JSON.parse(fs.readFileSync(storyboard,'utf8'));
const options=optionsPath?JSON.parse(fs.readFileSync(optionsPath,'utf8')):{};
const out=path.join(hf,'quality');fs.mkdirSync(out,{recursive:true});
const total=options.duration ?? Math.max(0,...(sb.scenes||[]).map(s=>s.out));
const times=new Set();
function sample(t){if(t>=0&&t<total)times.add(Math.round(t*1000)/1000);}
for(let t=.05;t<total;t+=.5)sample(t);
for(const list of [sb.scenes,sb.overlays,sb.fx,sb.beat_fx,sb.transitions, options.groups])
 for(const s of list||[]) for(const t of [s.in,s.out,s.at]) if(typeof t==='number')for(const delta of [-.04,.04,.25])sample(t+delta);
for(const s of sb.scenes||[])if(s.format==='narrative-sequence')
 for(const [i,step] of s.params.steps.entries())for(const delta of [.04,.6])sample(s.in+(step.at??i*(s.out-s.in)/s.params.steps.length)+delta);
const failures=[],issues=[],frames=[],measurements=[];let sampleIndex=0;const capturedIssues=new Set();
let browser,server;
try {
 const html=await bundleToSingleHtml(path.resolve(hf));
 server=await serveStaticProjectHtml(path.resolve(hf),html);
 const opened=await openSettledCompositionPage(html,server.url,{
  renderReadyTimeoutMs:30000,renderReadyWarningSuffix:'QA cannot continue',
  beforeNavigate:async page=>{
   page.on('pageerror',e=>failures.push(String(e)));
   page.on('requestfailed',r=>{if(!r.url().endsWith('favicon.ico') && !(r.resourceType()==='media' && r.failure()?.errorText==='net::ERR_ABORTED'))failures.push(r.url()+': '+r.failure()?.errorText);});
   page.on('response',r=>{if(r.status()>=400&&!r.url().endsWith('favicon.ico'))failures.push(r.status()+': '+r.url());});
  }
 });browser=opened.browser;const page=opened.page;
 if(opened.renderReadyTimedOut)throw new Error('runtime not ready');
 await page.evaluate(async()=>{await document.fonts.ready;if([...document.fonts].some(f=>f.status==='error'))throw new Error('font failed');});
 const sorted=options.times||[...times].sort((a,b)=>a-b);
 for(const time of sorted){
  await seekCompositionTimeline(page,time,{waitForImagesMs:5000});
  const active=(sb.scenes||[]).filter(s=>s.in<=time&&time<s.out);
  const reading=active.every(s=>{
   const enter=sb.motion?.enter_s??.5,leave=sb.motion?.exit_s??.25;
   if(time<s.in+enter+Math.min(1.5,Math.max(.5,(s.out-s.in)*.2))||time>s.out-leave)return false;
   if(s.format==='narrative-sequence')return s.params.steps.every((step,i)=>Math.abs(time-s.in-(step.at??i*(s.out-s.in)/s.params.steps.length))>.55);
   return true;
  });
  const measured=await page.evaluate(({time,reading,safe})=>{
   const result=[],texts=[], textNodes=[];
   const visible=el=>{for(let n=el;n;n=n.parentElement){const s=getComputedStyle(n);if(s.display==='none'||s.visibility==='hidden'||Number(s.opacity)<.15)return false;}return true;};
   const roots=[document];for(let i=0;i<roots.length;i++)for(const e of roots[i].querySelectorAll('*'))if(e.shadowRoot)roots.push(e.shadowRoot);
   const els=roots.flatMap(r=>[...r.querySelectorAll('*')]);
   for(const e of els){
    if(!(e instanceof Element)||e.closest('[data-layout-ignore]')||!visible(e))continue;
    const nodes=[...e.childNodes].filter(n=>n.nodeType===Node.TEXT_NODE&&n.textContent.trim());
    if(!nodes.length)continue;
    const style=getComputedStyle(e); if(['SCRIPT','STYLE','TITLE','OPTION'].includes(e.tagName))continue;
    const range=document.createRange();range.selectNodeContents(e);const box=range.getBoundingClientRect();
    let b={left:box.left,right:box.right,top:box.top,bottom:box.bottom,x:box.x,y:box.y,width:box.width,height:box.height};
    // Range rectangles include font leading, which is not ink and may exceed a mask safely.
    const canvas=document.createElement('canvas'),ctx=canvas.getContext('2d');ctx.font=style.font;
    const metrics=ctx.measureText(nodes.map(n=>n.textContent).join(''));
    if(box.height<parseFloat(style.fontSize)*1.5&&Number.isFinite(metrics.fontBoundingBoxAscent)){
      const top=box.top+metrics.fontBoundingBoxAscent-metrics.actualBoundingBoxAscent;
      const bottom=box.top+metrics.fontBoundingBoxAscent+metrics.actualBoundingBoxDescent;
      b={...b,top,bottom,y:top,height:bottom-top};
    }
    if(b.width<1||b.height<1)continue;
    const id=e.id||e.closest('[id]')?.id||e.tagName;
    const text=nodes.map(n=>n.textContent).join('').trim();
    const add=(level,code,message)=>result.push({level,code,path:id,time,message,text:text.slice(0,100)});
    const leaf={id,text,x:b.x,y:b.y,w:b.width,h:b.height,font:parseFloat(style.fontSize)};texts.push(leaf);textNodes.push({element:e,box:b,id,text});
    if(!reading)continue;
    if(b.left<-.5||b.right>1080.5||b.top<-.5||b.bottom>1920.5)add('error','canvas_clip','texto fuera del lienzo');
    for(let p=e.parentElement;p;p=p.parentElement){const ps=getComputedStyle(p);if(['hidden','clip'].includes(ps.overflow)||['hidden','clip'].includes(ps.overflowX)){
      const r=p.getBoundingClientRect();if(b.left<r.left-1||b.right>r.right+1||b.top<r.top-1||b.bottom>r.bottom+1){add('error','container_clip','texto recortado por contenedor');break;}
    }}
    if(parseFloat(style.fontSize)<28)add('warning','phone_size','texto menor a 28px: revisar legibilidad en teléfono');
    if(safe&&(b.left<safe.left-1||b.right>1080-safe.right+1||b.top<safe.top-1||b.bottom>1920-safe.bottom+1))add('warning','safe_zone','texto fuera de la zona segura de plataforma');
    // Contrast only for measurable opaque backgrounds; video/transparent backgrounds remain manual.
    const rgb=s=>(s.match(/[\d.]+/g)||[]).map(Number);
    let bg;for(let p=e;p;p=p.parentElement){let c=rgb(getComputedStyle(p).backgroundColor);if(c.length===3||(c.length===4&&c[3]===1)){bg=c;break;}}
    const fg=rgb(style.color);
    if(bg&&fg.length>=3){const lum=c=>c.slice(0,3).map(x=>{x/=255;return x<=.04045?x/12.92:((x+.055)/1.055)**2.4;}).reduce((a,x,i)=>a+x*[.2126,.7152,.0722][i],0);
      const a=lum(fg),b=lum(bg),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
      if(ratio<3)add('error','contrast','contraste sobre fondo opaco menor a 3:1');
      else if(ratio<4.5)add('warning','contrast','contraste sobre fondo opaco menor a 4.5:1');
    }
    // Occlusion across compositions; children of a text container do not count as occluders.
    const cx=Math.max(0,Math.min(1079,b.x+b.width/2)),cy=Math.max(0,Math.min(1919,b.y+b.height/2));
    const hits=document.elementsFromPoint(cx,cy).filter(x=>visible(x)&&!x.contains(e)&&!e.contains(x));
    const ownComp=e.closest('[data-composition-id]');
    for(const hit of hits){
      if(hit===e||hit.closest('[data-composition-id]')===ownComp)continue;
      if(e.compareDocumentPosition(hit)&Node.DOCUMENT_POSITION_FOLLOWING){
       const color=rgb(getComputedStyle(hit).backgroundColor);
       if(color.length===3||(color.length===4&&color[3]>.95)){add('warning','occlusion','posible oclusión por otra capa: '+(hit.id||hit.tagName));break;}
      }
    }
   }
   if(reading){
    const regions=els.filter(e=>e.matches?.('[data-vv-protected], .cap .line, .ov .panel')&&visible(e));
    for(const t of textNodes)for(const region of regions){
     if(region.contains(t.element)||t.element.contains(region))continue;
     const r=region.getBoundingClientRect(),b=t.box;
     const area=Math.max(0,Math.min(b.right,r.right)-Math.max(b.left,r.left))*Math.max(0,Math.min(b.bottom,r.bottom)-Math.max(b.top,r.top));
     if(area>b.width*b.height*.2)result.push({level:'error',code:'protected_overlap',path:t.id,time,text:t.text,message:'texto solapa subtítulos o región protegida'});
    }
   }
   return {issues:result,texts};
  },{time,reading,safe:options.safe});
  issues.push(...measured.issues);measurements.push({time,reading,texts:measured.texts});
  // Every sampled state has evidence; caller may render a compact subset for matrix jobs.
  const frame=path.resolve(out,`at-${time.toFixed(3)}.png`);
  const freshIssue=measured.issues.some(i=>i.level==='error'&&!capturedIssues.has(i.code+':'+i.path));
  if(options.times || sampleIndex++ % 10===0 || freshIssue){
   await page.screenshot({path:frame,type:'png'});frames.push(frame);
   measured.issues.forEach(i=>capturedIssues.add(i.code+':'+i.path));
  }
 }
 if(failures.length)throw new Error([...new Set(failures)].join('\n'));
 const unique=[...new Map(issues.map(i=>[`${i.code}:${i.path}:${i.text}`,i])).values()];
 fs.writeFileSync(path.join(out,'measurements.json'),JSON.stringify(measurements));
 process.stdout.write(JSON.stringify({version:2,runtime:version,ok:!unique.some(i=>i.level==='error'),issues:unique,frames,
  visual_review:'pending',samples:sorted.length,coverage:['production runtime','scenes','captions','overlays','fx','beat_fx','transitions'],
  manual_checks:['rostro y manos','texto en canvas/WebGL','contraste sobre video','sentido narrativo','zonas seguras en la aplicación móvil']}));
}finally{await browser?.close();await server?.close();}
