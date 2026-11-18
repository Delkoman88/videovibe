"""Shared visual composition writer for production, style comparisons and galleries."""
import formats
from scripts.composer.visual import captions_html, overlays_html, index_html
from scripts.composer import transitions


def write(hf, sb, caps, brand, safe, ctx, duration, total, cuts=(), cta=None,
          audio='', music=None, media=None, fx=('', '', ''), beat=('', '', '')):
    from scripts.composer.reading import windows
    from scripts.core import oslib
    oslib.write_json(hf/'reading-windows.json', windows(sb, caps, brand))
    compositions = hf/'compositions';compositions.mkdir(parents=True, exist_ok=True)
    (compositions/'captions.html').write_text(captions_html(caps, sb.get('emphasis', {}), brand, safe, ctx, sb.get('caption_zones', [])))
    (compositions/'overlays.html').write_text(overlays_html(sb, brand, safe, ctx))
    for old in compositions.glob('scene-*.html'): old.unlink()
    for scene in sb.get('scenes', []):
        (compositions/f"scene-{scene['id']}.html").write_text(formats.render(scene,ctx.packs,motion=sb.get('motion')))
    transition = transitions.composition(sb, ctx.font_faces)
    target = compositions/'transitions.html'
    if transition: target.write_text(transition)
    else: target.unlink(missing_ok=True)
    (hf/'index.html').write_text(index_html(sb,brand,safe,duration,total,cuts,cta,audio,ctx,music,media,fx,beat))
