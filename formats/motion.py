"""Opt-in adapters at the timeline API boundary; data and library clocks stay absolute."""
from contextvars import ContextVar
from pathlib import Path
import json

CURRENT = ContextVar('videovibe_motion', default=None)


def value(key, legacy):
    context = CURRENT.get()
    return context['profile'].get(key, legacy) if context else legacy


def factor(key, legacy, base=1):
    context = CURRENT.get()
    return float(legacy) * context['profile'][key] / base if context else legacy


def prelude(sid):
    context = CURRENT.get()
    if not context: return ''
    config = json.dumps({**context, 'sid': sid}, ensure_ascii=False)
    return (Path(__file__).with_suffix('.js').read_text().replace('__CONFIG__', config))


def path_move(target, path, at, duration, start=0, end=1, progress=False):
    return 'vvPaths.push('+json.dumps(dict(target=target,path=path,at=at,duration=duration,start=start,end=end,progress=progress))+');'


def postlude(duration):
    if not CURRENT.get(): return ''
    return '''
if(vvPaths.length){
 const clock={t:0};
 const drawPath=()=>{
  const t=clock.t;
  const seg=[...vvPaths].reverse().find(s=>t>=s.at)||vvPaths[0];
  const q=gsap.parseEase('power1.inOut')(Math.max(0,Math.min(1,(t-seg.at)/seg.duration)));
  const path=document.querySelector(seg.path);
  const point=path.getPointAtLength(path.getTotalLength()*(seg.start+(seg.end-seg.start)*q));
  gsap.set(seg.target,{x:point.x,y:point.y});
  if(seg.progress) gsap.set(seg.path,{drawSVG:"0% "+((seg.start+(seg.end-seg.start)*q)*100)+"%"});
 };
 tl.fromTo(clock,{t:0},{t:DURATION,duration:DURATION,ease:'none'},0);
 tl.eventCallback('onUpdate',drawPath);
 drawPath();
}
'''.replace('DURATION',str(duration))
