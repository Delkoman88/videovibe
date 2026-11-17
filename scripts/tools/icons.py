#!/usr/bin/env python3
"""Regenera los conjuntos de iconos de formats/icons/ desde sus selecciones versionadas.

Uso:
  scripts/tools/icons.py --from <carpeta icons/ de lucide-static> [--version X.Y.Z]   (Lucide, ISC)
  scripts/tools/icons.py --sets [--only bio|health]                                     (Bioicons y Health Icons)

- Lucide: `npm pack lucide-static@<versión>` y descomprimir (package/icons/). Guarda solo el interior de cada
  SVG (24×24, trazo `currentColor`) en lucide.json, desde selection.txt.
- --sets descarga de GitHub, en el commit fijado en SETS (cambiarlo = actualizar a propósito), los iconos de
  selection-health.txt (Health Icons, CC0) y selection-bio.txt (Bioicons, solo la carpeta CC0). Los limpia para
  usarlos dentro del HTML: sin XML ni metadatos de editores, estilos de clase (`.st0{…}`) pasados a cada
  elemento (si no, se aplicarían a toda la página), ids con prefijo propio, y en Health Icons el color pasa a
  `currentColor` (toma el color de la marca). Guarda health.json y bio.json con licencia y autor por icono.
Salida JSON. Exit 0 ok, 2 error.
"""
import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.core import oslib  # noqa: E402

DIR = ROOT / "formats" / "icons"
MAX_KB = 80  # un icono más pesado (dibujo calcado de una foto) infla cada escena que lo usa

SETS = {
    "health": {"repo": "resolvetosavelives/healthicons", "commit": "2080c1b40e4829f2f4217e03bc22908b4e402f6b",
               "root": "public/icons/svg/filled/", "license": "CC0 1.0", "site": "https://healthicons.org",
               "mono": True},
    "bio": {"repo": "duerrsimon/bioicons", "commit": "d29e766ea7580b8063c4f47b29e872db40a4d979",
            "root": "static/icons/cc-0/", "license": "CC0 1.0", "site": "https://bioicons.com", "mono": False},
}


def inner_svg(text):
    body = re.search(r"<svg[^>]*>(.*)</svg>", text, re.S)
    if not body:
        raise ValueError("no es un SVG")
    return re.sub(r"\s+", " ", re.sub(r"<!--.*?-->", "", body.group(1), flags=re.S)).replace(" />", "/>").strip()


def slug(name):
    return re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")


def _viewbox(root_tag):
    m = re.search(r'viewBox="([^"]+)"', root_tag)
    if m:
        return " ".join(m.group(1).replace(",", " ").split())
    w = re.search(r'\bwidth="([\d.]+)', root_tag)
    h = re.search(r'\bheight="([\d.]+)', root_tag)
    if w and h:
        return f"0 0 {w.group(1)} {h.group(1)}"
    raise ValueError("SVG sin viewBox ni tamaño")


def _inline_classes(body):
    """`.st0{fill:#123}` de los <style> → style="fill:#123" en cada elemento con esa clase; quita los <style>."""
    rules = {}
    for css in re.findall(r"<style[^>]*>(.*?)</style>", body, re.S):
        css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
        for sels, decl in re.findall(r"([^{}]+)\{([^}]*)\}", css):
            for sel in sels.split(","):
                sel = sel.strip()
                if re.fullmatch(r"\.[\w-]+", sel):
                    rules[sel[1:]] = rules.get(sel[1:], "") + decl.strip().rstrip(";") + ";"
    body = re.sub(r"<style[^>]*>.*?</style>", "", body, flags=re.S)

    def repl(m):
        tag, attrs = m.group(1), m.group(2)
        cls = re.search(r'\sclass="([^"]*)"', attrs)
        if not cls:
            return m.group(0)
        style = "".join(rules.get(c, "") for c in cls.group(1).split())
        attrs = attrs.replace(cls.group(0), "")
        if style:
            old = re.search(r'\sstyle="([^"]*)"', attrs)
            if old:
                attrs = attrs.replace(old.group(0), f' style="{style}{old.group(1)}"')
            else:
                attrs = f' style="{style}"' + attrs
        return f"<{tag}{attrs}"
    return re.sub(r"<([\w:-]+)((?:\s[^<>]*?)?)(?=/?>)", repl, body)


def clean(text, prefix, mono):
    """SVG de un conjunto → (viewBox, interior listo para HTML)."""
    text = re.sub(r"<\?xml.*?\?>|<!DOCTYPE[^>]*>|<!--.*?-->", "", text, flags=re.S)
    root = re.search(r"<svg[^>]*>", text, re.S)
    if not root:
        raise ValueError("no es un SVG")
    vb = _viewbox(root.group(0))
    body = text[root.end():text.rfind("</svg>")]
    body = re.sub(r"<(metadata|sodipodi:namedview|title|desc)\b.*?(</\1>|/>)", "", body, flags=re.S)
    body = re.sub(r"<((?:inkscape|sodipodi):[\w-]+)\b[^>]*?(/>|>.*?</\1>)", "", body, flags=re.S)
    body = _inline_classes(body)
    body = re.sub(r'\s(?:inkscape|sodipodi|serif|data-name|xml:space|enable-background)[\w:-]*="[^"]*"', "", body)
    ids = re.findall(r'\sid="([^"]+)"', body)
    for i in sorted(set(ids), key=len, reverse=True):
        new = f"{prefix}-{slug(i) or 'x'}"
        body = body.replace(f'id="{i}"', f'id="{new}"').replace(f"url(#{i})", f"url(#{new})") \
                   .replace(f'href="#{i}"', f'href="#{new}"')
    if mono:  # el gris de Health Icons pasa a currentColor: toma el color del elemento (la marca)
        body = re.sub(r'(fill|stroke)="(#333333|#333|#000000|#000|black)"', r'\1="currentColor"', body, flags=re.I)
    body = re.sub(r"\s+", " ", body).replace(" />", "/>").replace("> <", "><").strip()
    return vb, body


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "videovibe-icons"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def build_set(name):
    cfg = SETS[name]
    wanted = [line.strip() for line in (DIR / f"selection-{name}.txt").read_text().splitlines()
              if line.strip() and not line.startswith("#")]
    tree = json.loads(_get(f"https://api.github.com/repos/{cfg['repo']}/git/trees/{cfg['commit']}?recursive=1"))
    paths = [t["path"] for t in tree["tree"] if t["path"].startswith(cfg["root"]) and t["path"].endswith(".svg")]
    icons, missing, heavy = {}, [], []
    for w in wanted:
        cat, nm = w.split("/", 1)
        hit = [p for p in paths if p.startswith(cfg["root"] + cat + "/") and p.endswith("/" + nm + ".svg")]
        if not hit:
            missing.append(w)
            continue
        p = hit[0]
        raw = _get(f"https://raw.githubusercontent.com/{cfg['repo']}/{cfg['commit']}/{urllib.parse.quote(p)}").decode("utf-8", "replace")
        ident = slug(nm)
        vb, body = clean(raw, f"{name}-{ident}", cfg["mono"])
        if len(body) > MAX_KB * 1024:
            heavy.append(f"{w} ({len(body) // 1024} KB)")
            continue
        parts = p[len(cfg["root"]):].split("/")
        author = parts[1].replace("_", " ").replace("-", " ") if name == "bio" and len(parts) > 2 else ""
        icons[ident] = {"viewBox": vb, "svg": body, "license": cfg["license"],
                        "author": author or ("Health Icons (Resolve to Save Lives)" if name == "health" else ""),
                        "source": f"{cfg['site']} · {p}"}
    oslib.write_json(DIR / f"{name}.json", {"source": cfg["repo"], "commit": cfg["commit"], "license": cfg["license"],
                                            "site": cfg["site"], "mono": cfg["mono"], "icons": icons})
    return {"set": name, "icons": len(icons), "missing": missing, "too_heavy": heavy}


def lucide(src, version):
    names = [line.strip() for line in (DIR / "selection.txt").read_text().splitlines()
             if line.strip() and not line.startswith("#")]
    missing = [n for n in names if not (src / f"{n}.svg").exists()]
    if missing:
        oslib.die(f"no existen en {src}: {missing}")
    version = version or (re.search(r"lucide-static v([\d.]+)", (src / f"{names[0]}.svg").read_text())
                          or [None, ""])[1]
    icons = {n: inner_svg((src / f"{n}.svg").read_text()) for n in names}
    oslib.write_json(DIR / "lucide.json", {"source": "lucide-static", "version": version, "license": "ISC",
                                           "icons": icons})
    return {"icons": len(icons), "version": version, "file": str(DIR / "lucide.json")}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--from", dest="src", type=Path)
    ap.add_argument("--version", default="")
    ap.add_argument("--sets", action="store_true")
    ap.add_argument("--only", choices=sorted(SETS))
    args = ap.parse_args()
    if not args.src and not args.sets:
        ap.error("usa --from <carpeta de lucide-static> o --sets")
    out = {"ok": True}
    if args.src:
        out["lucide"] = lucide(args.src, args.version)
    if args.sets:
        try:
            out["sets"] = [build_set(n) for n in ([args.only] if args.only else SETS)]
        except OSError as e:
            oslib.die(f"no se pudo descargar: {e}")
    oslib.emit(out)


if __name__ == "__main__":
    main()
