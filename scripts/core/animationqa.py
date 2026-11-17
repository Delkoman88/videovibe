"""Hallazgos estructurales; nunca presenta inspección humana como aprobada."""

def inspect(sb, registry):
    issues=[]
    def add(level,path,time,message):
        issues.append(dict(level=level,path=path,time=time,message=message))
    def overlap(a,b): return max(a.get('in',0),b.get('in',0)) < min(a.get('out',0),b.get('out',0))
    overlays=[o for o in sb.get('overlays',[]) if isinstance(o,dict)]
    scenes=[s for s in sb.get('scenes',[]) if isinstance(s,dict)]
    for i,o in enumerate(overlays):
        for j,other in enumerate(overlays[:i]):
            if overlap(o,other):add('error',f'overlays[{i}]',o.get('in',0),f'solapa tarjeta {j}')
        words=len(str(o.get('text','')).split())
        if o.get('out',0)-o.get('in',0)<max(1,words/3):
            add('warning',f'overlays[{i}]',o.get('in',0),'poco tiempo de lectura (referencia: 3 palabras/s)')
    full=lambda s:s.get('layout',registry.get(s.get('format'),{}).get('layout'))=='full'
    ordered=sorted(scenes,key=lambda x:x.get('in',0))
    for i,s in enumerate(ordered):
        if i:
            before=ordered[i-1]
            if before.get('format')==s.get('format'): add('warning',s.get('id','scene'),s.get('in',0),'formato repetido consecutivamente')
            if full(s) and full(before) and s.get('in',0)-before.get('out',0)<.5:
                add('warning',s.get('id','scene'),s.get('in',0),'falta respiro entre escenas completas')
        if full(s):
            for o in overlays:
                if overlap(s,o):add('warning',s.get('id','scene'),s.get('in',0),'tarjeta simultánea a escena completa')
    density=sb.get('motion',{}).get('density',3)
    items=scenes+overlays+sb.get('broll',[])+sb.get('fx',[])
    for t in sorted({x.get('in',x.get('at',0)) for x in items}):
        active=[x for x in items if x.get('in',x.get('at',0))<=t<x.get('out',x.get('at',0)+x.get('duration',0))]
        if len(active)>density:add('warning','density',t,f'{len(active)} elementos simultáneos')
    return {'issues':issues,'ok':not any(x['level']=='error' for x in issues),
            'visual_review':'pending','manual_checks':['rostro y manos libres','legibilidad en teléfono','claridad narrativa']}
