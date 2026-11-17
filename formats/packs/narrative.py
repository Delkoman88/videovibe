"""Secuencias conectadas con un objeto persistente y un solo reloj."""
from formats.core import fmt, wrap, esc
import json
from formats import icons
from formats.motion import value


def check(p):
    errors=[]
    if p.get('recipe') not in ('process','compare','locate'):errors.append('recipe: process, compare o locate')
    steps=p.get('steps',[])
    if not isinstance(steps,list) or not 2<=len(steps)<=5:return errors+['steps: entre 2 y 5 pasos']
    for i,s in enumerate(steps):
        if not isinstance(s,dict) or not isinstance(s.get('text'),str) or not 1<=len(s['text'])<=80:
            errors.append(f'steps[{i}].text: 1–80 caracteres')
    times=[s.get('at',i) for i,s in enumerate(steps) if isinstance(s,dict)]
    if any(not isinstance(v,(int,float)) or isinstance(v,bool) or v<0 for v in times):
        errors.append('steps.at: segundos locales no negativos')
    elif times!=sorted(times) or len(set(times))!=len(times):
        errors.append('steps.at: deben estar en orden y ser distintos')
    objects=p.get('objects', [])
    ids=set()
    if not isinstance(objects,list): return errors+['objects: lista obligatoria']
    for obj in objects:
        if not isinstance(obj,dict) or not isinstance(obj.get('id'),str) or not obj['id'].replace('-','').isalnum():
            errors.append('objects.id: identificador alfanumérico obligatorio');continue
        if obj['id'] in ids: errors.append('objects.id: repetido')
        ids.add(obj['id'])
        if obj.get('kind') not in ('shape','text','icon','image'): errors.append('objects.kind: shape, text, icon o image')
        if obj.get('kind')=='icon' and not icons.exists(obj.get('icon')): errors.append('objects.icon: fuera del catálogo')
        if obj.get('kind')=='image' and not isinstance(obj.get('image'),str): errors.append('objects.image: id de biblioteca obligatorio')
        if obj.get('kind')=='text' and not isinstance(obj.get('text'),str): errors.append('objects.text: texto obligatorio')
        if obj.get('shape','circle') not in ('circle','square'): errors.append('objects.shape: circle o square')
    for step in steps:
        if not isinstance(step,dict):continue
        if 'object' in step and step['object'] not in ids:errors.append('steps.object: objeto inexistente')
        for key,lo,hi in (('x',-250,250),('y',-250,250),('scale',.5,1.5),('rotation',-180,180)):
            n=step.get(key,1 if key=='scale' else 0)
            if not isinstance(n,(int,float)) or isinstance(n,bool) or not lo<=n<=hi:errors.append(f'steps.{key}: fuera de {lo}–{hi}')
    return errors


def uses(p):
    return [('images',obj['image']) for obj in p.get('objects',[]) if obj.get('kind')=='image']


@fmt('narrative-sequence',required=('recipe','steps'),check=check,uses=uses,
     example={'recipe':'process','steps':[{'text':'Observa'},{'text':'Compara'},{'text':'Explica'}]})
def sequence(sid,d,p,layout='full'):
    """Proceso, comparación o acercamiento con un elemento persistente y etiquetas sucesivas."""
    if p.get('objects'): return objects_sequence(sid,d,p,layout)
    steps=p['steps']; segment=d/len(steps)
    body=f'<div id="{sid}-object" class="object"></div>'
    css='.object {position:absolute;left:340px;top:470px;width:400px;height:400px;border:5px solid var(--accent);border-radius:50%;background:var(--surface)} .step {position:absolute;left:110px;top:970px;width:860px;text-align:center;font:600 54px var(--font-display);color:var(--text)}'
    js=[]
    for i,step in enumerate(steps):
        at=step.get('at',i*segment)
        finish=steps[i+1].get('at',(i+1)*segment) if i+1<len(steps) else d
        body+=f'<div id="{sid}-step-{i}" class="step" data-vv-text>{esc(step["text"])}</div>'
        js += [f'tl.set("#{sid}-step-{i}",{{opacity:0}},0);',
               f'tl.to("#{sid}-step-{i}",{{opacity:1,duration:.25}},{at+.1});',
               f'tl.to("#{sid}-step-{i}",{{opacity:0,duration:.2}},{finish-.25});']
        scale=1+.18*i if p['recipe']=='locate' else 1
        x=(-120 if i%2==0 else 120) if p['recipe']=='compare' else 0
        radius=50 if p['recipe']!='process' or i%2==0 else 15
        js.append(f'tl.to("#{sid}-object",{{x:{x},scale:{scale},borderRadius:"{radius}%",duration:.5,ease:"power2.inOut"}},{at});')
    return wrap(sid,d,layout,css,body,'\n'.join(js))


def objects_sequence(sid,d,p,layout):
    """Reuse identified objects; animate properties, never regenerate source images."""
    body=[];js=[]
    css='.n-object {position:absolute;left:340px;top:460px;width:400px;height:400px;display:flex;align-items:center;justify-content:center;color:var(--accent);font:600 60px var(--font-display);text-align:center} .n-object img {width:100%;height:100%;object-fit:contain} .n-label {position:absolute;left:100px;top:960px;width:800px;text-align:center;font:600 48px var(--font-display);color:var(--text)}'
    for obj in p['objects']:
        oid=f"{sid}-obj-{obj['id']}";kind=obj['kind']
        content='';style=''
        if kind=='shape':style=f"background:var(--surface);border:5px solid var(--accent);border-radius:{50 if obj.get('shape','circle')=='circle' else 8}%"
        elif kind=='text': content=esc(obj['text'])
        elif kind=='icon': content=icons.icon(obj['icon'],size=240)
        else:
            alt=esc(obj.get("alt", ""))
            content=f'<img id="{oid}-img" alt="{alt}">'
            js.append(f'document.getElementById({json.dumps(oid+"-img")}).src=window.__vv[{json.dumps("images:"+obj["image"])}].url;')
        body.append(f'<div id="{oid}" class="n-object" style="{style}">{content}</div>')
        js.append(f'tl.set("#{oid}",{{opacity:0}},0);')
    steps=p['steps']
    for i,step in enumerate(steps):
        at=step.get('at',i*d/len(steps));end=steps[i+1].get('at',(i+1)*d/len(steps)) if i+1<len(steps) else d
        obj=step.get('object',p['objects'][0]['id']);oid=f'{sid}-obj-{obj}'
        for other in p['objects']:
            if other['id']!=obj:js.append(f'tl.set("#{sid}-obj-{other["id"]}",{{opacity:0}},{at});')
        props={'opacity':1,'x':step.get('x',(-120 if i%2==0 else 120) if p['recipe']=='compare' else 0),
               'y':step.get('y',0),'scale':step.get('scale',min(1.5,1+i*.15) if p['recipe']=='locate' else 1),
               'rotation':step.get('rotation',0),'duration':value('enter_s',.35),'ease':value('ease','power2.out')}
        js.append(f'tl.to("#{oid}",{json.dumps(props)},{at});')
        lid=f'{sid}-step-{i}'
        body.append(f'<div id="{lid}" class="n-label" data-vv-text>{esc(step["text"])}</div>')
        js.extend([f'tl.set("#{lid}",{{opacity:0}},0);',f'tl.to("#{lid}",{{opacity:1,duration:.2}},{at+.35});',f'tl.to("#{lid}",{{opacity:0,duration:.15}},{end-.2});'])
    return wrap(sid,d,layout,css,''.join(body),'\n'.join(js))
