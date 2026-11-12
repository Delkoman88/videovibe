#!/usr/bin/env python3
"""Valida que un canal esté completo y coherente con el motor.

Uso: scripts/tools/check_channel.py <id-del-canal> [--allow-todo]

Comprueba: archivos obligatorios, channel.json (claves, idioma con lang/<idioma>.json, plataformas con
preset, paquetes de formatos existentes), brand.json (colores por función, roles de resaltado, fuentes
presentes en <canal>/fonts/ o assets/fonts/), recetas de efectos (audio/sfx/recipes.json) y que no
queden marcadores «TODO» (salvo --allow-todo).
Salida JSON. Exit 0 completo, 1 incompleto, 2 error de uso. Lo usa `bin/doctor --channel <id>`.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402
from scripts.audio import sfxrecipes  # noqa: E402

COLOR_KEYS = {"bg", "surface", "surface_line", "depth", "depth2", "accent", "accent2", "accent3", "warn", "text", "muted"}
ROLES = {"keyword", "data", "punchline", "warning"}


def check(cid, allow_todo=False):
    d = oslib.channel_path(cid)
    problems = []
    if not d.is_dir():
        return [f"no existe channels/{cid}"]
    for f in oslib.CHANNEL_FILES + ["learnings.md"]:
        if not (d / f).exists():
            problems.append(f"falta {f}")
    if problems:
        return problems
    cfg = oslib.read_json(d / "channel.json")
    for k in ("id", "name", "language", "persons", "platforms", "format_packs"):
        if k not in cfg:
            problems.append(f"channel.json sin «{k}»")
    if cfg.get("id") != cid and not cid.startswith("_"):
        problems.append(f"channel.json id «{cfg.get('id')}» ≠ carpeta «{cid}»")
    if not (oslib.LANG_DIR / f"{cfg.get('language')}.json").exists():
        problems.append(f"idioma «{cfg.get('language')}» sin lang/{cfg.get('language')}.json")
    for p in cfg.get("platforms", []):
        if not (oslib.ROOT / "presets" / f"{p}.json").exists():
            problems.append(f"plataforma «{p}» sin presets/{p}.json")
    import formats
    for p in cfg.get("format_packs", []):
        if p not in formats.available_packs():
            problems.append(f"paquete de formatos «{p}» no existe (disponibles: {formats.available_packs()})")
    brand = oslib.read_json(d / "brand.json")
    missing = COLOR_KEYS - set(brand.get("colors", {}))
    if missing:
        problems.append(f"brand.json: faltan colores {sorted(missing)}")
    roles = brand.get("highlight_roles", {})
    if set(roles) != ROLES or any(v not in brand.get("colors", {}) for v in roles.values()):
        problems.append(f"brand.json: highlight_roles debe mapear {sorted(ROLES)} a colores existentes")
    for key in ("display", "mono"):
        f = brand.get("fonts", {}).get(key, {}).get("file")
        if not f or not any((x / f).exists() for x in (d / "fonts", oslib.ROOT / "assets" / "fonts")):
            problems.append(f"brand.json: fuente {key} «{f}» no está en {cid}/fonts/ ni en assets/fonts/")
    if not allow_todo:
        for f in sorted(d.glob("*.md")) + [d / "channel.json", d / "brand.json"]:
            if "TODO" in f.read_text(encoding="utf-8"):
                problems.append(f"{f.name} tiene marcadores TODO sin completar")
    rf = d / "audio" / "sfx" / "recipes.json"
    if rf.exists():
        import json
        try:
            root = float(brand.get("sound", {}).get("root_hz", 880))
            problems += [f"audio/sfx/recipes.json: {e}" for e in sfxrecipes.validate(json.loads(rf.read_text()), root)]
        except json.JSONDecodeError as e:
            problems.append(f"audio/sfx/recipes.json: JSON inválido ({e})")
    uf = d / "audio" / "sfx" / "user.json"
    if uf.exists():
        import json
        for name, u in json.loads(uf.read_text()).get("sounds", {}).items():
            if not u.get("license"):
                problems.append(f"audio/sfx/user.json: «{name}» sin licencia")
            if not (d / "audio" / "sfx" / "user" / u.get("original", "")).exists():
                problems.append(f"audio/sfx/user/{u.get('original')}: falta el original del efecto «{name}» "
                                "(los originales no van a git: cópialo o vuelve a registrarlo)")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("channel")
    ap.add_argument("--allow-todo", action="store_true")
    args = ap.parse_args()
    problems = check(args.channel, args.allow_todo)
    oslib.emit({"ok": not problems, "channel": args.channel, "problems": problems}, 0 if not problems else 1)


if __name__ == "__main__":
    main()
