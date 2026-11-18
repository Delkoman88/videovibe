"""Internal reading windows shared by production and previews; no storyboard migration."""
from scripts.composer.timing import caption_enter, caption_exit, CAPTION_OUT, PANEL_IN, LIQUID_SHAPE, OVERLAY_OUT
from formats.text import kinetic_duration, plain


def windows(sb, caps, brand):
    result = {}
    for s in sb.get('scenes', []):
        enter = sb.get('motion', {}).get('enter_s', .5)
        leave = sb.get('motion', {}).get('exit_s', .25)
        result[s['id']] = {'start': s['in'], 'end': s['out'],
            'read_start': s['in'] + enter + min(1.5, max(.5, (s['out']-s['in'])*.2)),
            'read_end': s['out']-leave, 'mask': True}
        if sb.get('motion',{}).get('version') == 2:
            from formats.direction import budget
            read=budget(s,sb['motion'])['reading']
            result[s['id']]['read_start']=s['in']+read[0]
            result[s['id']]['read_end']=s['in']+read[1]
        # kinetic-title animates its text and kicker out before the scene's outer fade.
        if s.get('format') == 'kinetic-title':
            duration = s['out'] - s['in']
            result[s['id']]['read_end'] = min(result[s['id']]['read_end'], s['in'] + max(duration - .6, .9))
            result[s['id']]['read_start'] = max(result[s['id']]['read_start'], s['in'] + .12 + kinetic_duration(s.get('params', {}).get('variant', 'rise'), plain(s['params']['text'])))
    for o in sb.get('overlays', []):
        delay = LIQUID_SHAPE if brand.get('overlays', {}).get('style') == 'liquid' else PANEL_IN
        variant = o.get('text_fx') if o.get('type') != 'cta' else None
        if variant: delay = max(delay, .12 + kinetic_duration(variant, plain(o.get('text', ''))))
        result[o['id']] = {'start': o['in'], 'end': o['out'], 'read_start': o['in']+delay,
                          'read_end': o['out']-(0 if o.get('type')=='cta' else OVERLAY_OUT),
                          'mask': variant in ('rise','wave','blur','mask')}
    for f in sb.get('fx', []):
        a=f.get('in', f.get('at')); b=f.get('out', a+f.get('duration',1.2))
        variant=f.get('variant','rise'); text=plain(f.get('text',''))
        delay=.05+kinetic_duration(variant,text) if text else .35
        for ident in ('fx-'+f['id'],'fxt-'+f['id'],'fxtf-'+f['id']):
            result[ident]={'start':a,'end':b,'read_start':a+delay,'read_end':b-.4,'mask':bool(text) and variant in ('rise','wave','blur','mask')}
    for g in caps.get('groups', []):
        result[g['id']] = {'start': g['in'], 'end': g['out'], 'read_start':g['in']+caption_enter(g['out']-g['in'],brand.get('captions',{}).get('style','classic')),
                          'read_end':g['out']-caption_exit(g['out']-g['in']), 'mask':False}
    return result
