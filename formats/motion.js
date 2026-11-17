// Local adapter: only CSS entrances. No source-code replacements or global timeScale.
const vvMotion = __CONFIG__;
const vvPaths=[];
const vvDrawInitialized=new Set();
const vvFromTo = tl.fromTo.bind(tl);
tl.fromTo = (target, from, to, at) => {
  if(to.drawSVG && typeof target === 'string'){
    if(!vvDrawInitialized.has(target)){tl.set(target,{drawSVG:from.drawSVG},0);vvDrawInitialized.add(target);}
    to={...to,immediateRender:false};
  }
  const cssTarget = typeof target === 'string' || target instanceof Element;
  const entrance = target !== '#' + vvMotion.sid + '-stage' && cssTarget && ((from.opacity === 0 && to.opacity > 0) || (from.yPercent && to.yPercent === 0)) && !to.repeat && !to.onUpdate;
  if (!entrance) return vvFromTo(target, from, to, at);
  const p = vvMotion.profile;
  const initial = {...from}, final = {...to};
  // Coordinates are offsets of decorative entrances, not positions of data or anatomy.
  for (const key of ['x', 'y', 'rotation', 'rotate']) {
    if (typeof initial[key] === 'number' && (final[key] === 0 || final[key] === undefined))
      initial[key] *= p.amplitude / 28;
  }
  if (typeof initial.scale === 'number' && final.scale === 1)
    initial.scale = Math.max(.05, 1 + (initial.scale - 1) * p.amplitude / 28);
  final.duration = Math.min((to.duration ?? .35) * p.internal_ratio, .8);
  final.ease = p.ease;
  if (typeof final.stagger === 'number') final.stagger = Math.min(p.stagger_s, .9 / Math.max(1, gsap.utils.toArray(target).length));
  const start = typeof at === 'number' ? at : 0;
  if (start + final.duration > vvMotion.windows.exit[0])
    throw new Error('Entrada sin tiempo de lectura: ' + vvMotion.sid);
  return vvFromTo(target, initial, final, at);
};
