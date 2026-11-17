"""Estructuras moleculares (PDB, mmCIF, SDF/MOL): leer, resumir y descargar de RCSB PDB y PubChem.

La descarga ocurre solo al agregar la estructura a la biblioteca (`scripts/tools/structures.py`); el render
usa la copia local (ADR 0024). Licencias de los datos: PDB, CC0 1.0; PubChem, dominio público (NCBI).
"""
import json
import re
import urllib.request
from pathlib import Path

FORMATS = {".pdb": "pdb", ".ent": "pdb", ".cif": "cif", ".mmcif": "cif", ".sdf": "sdf", ".mol": "sdf", ".mol2": "mol2"}
WATER = {"HOH", "WAT", "DOD"}
LICENSES = {"pdb": "CC0 1.0 (datos del PDB, wwPDB)", "pubchem": "Dominio público (PubChem, NCBI)"}
UA = {"User-Agent": "VideoVibe structures (https://github.com/Delkoman88/videovibe)"}


def fmt_of(path):
    f = FORMATS.get(Path(path).suffix.lower())
    if not f:
        raise ValueError(f"formato no reconocido: {Path(path).suffix} (usa {', '.join(sorted(FORMATS))})")
    return f


def summary(text, fmt):
    """{title, atoms, chains: {cadena: residuos}, ligands: [resn], residues: {cadena: [min, max]}}."""
    if fmt == "pdb":
        title = " ".join(l[10:].strip() for l in text.splitlines() if l.startswith("TITLE")).strip()
        chains, rng, ligands, atoms = {}, {}, set(), 0
        for l in text.splitlines():
            rec = l[:6]
            if rec in ("ATOM  ", "HETATM"):
                atoms += 1
                ch, resn = l[21].strip() or "_", l[17:20].strip()
                try:
                    resi = int(l[22:26])
                except ValueError:
                    continue
                if rec == "ATOM  ":
                    chains.setdefault(ch, set()).add(resi)
                    lo, hi = rng.get(ch, (resi, resi))
                    rng[ch] = (min(lo, resi), max(hi, resi))
                elif resn not in WATER:
                    ligands.add(resn)
            if l.startswith("ENDMDL"):
                break  # solo el primer modelo (RMN)
        return {"title": title.title() if title.isupper() else title, "atoms": atoms,
                "chains": {c: len(r) for c, r in sorted(chains.items())},
                "residues": {c: list(v) for c, v in sorted(rng.items())}, "ligands": sorted(ligands)}
    if fmt == "sdf":
        lines = text.splitlines()
        counts = lines[3] if len(lines) > 3 else ""
        try:
            atoms = int(counts[:3])
        except ValueError:
            atoms = 0
        return {"title": lines[0].strip() if lines else "", "atoms": atoms, "chains": {}, "residues": {}, "ligands": []}
    if fmt == "cif":
        title = next((m.group(1).strip("'\" ") for m in [re.search(r"^_struct\.title\s+(.+)$", text, re.M)] if m), "")
        atoms = sum(1 for l in text.splitlines() if l.startswith(("ATOM ", "HETATM ")))
        return {"title": title, "atoms": atoms, "chains": {}, "residues": {}, "ligands": []}
    return {"title": "", "atoms": 0, "chains": {}, "residues": {}, "ligands": []}


def _get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def fetch_pdb(code):
    """Texto PDB de RCSB (o mmCIF si la entrada es muy grande para formato PDB)."""
    code = code.strip().upper()
    if not re.fullmatch(r"[0-9][A-Z0-9]{3}", code):
        raise ValueError(f"código PDB inválido: {code} (4 caracteres, p. ej. 1HHO)")
    try:
        return _get(f"https://files.rcsb.org/download/{code}.pdb"), "pdb", f"RCSB PDB {code}"
    except Exception:  # noqa: BLE001 — las entradas grandes solo existen en mmCIF
        return _get(f"https://files.rcsb.org/download/{code}.cif"), "cif", f"RCSB PDB {code}"


def fetch_pubchem(cid=None, name=None):
    """SDF 3D de PubChem por CID o por nombre (inglés)."""
    if name and not cid:
        data = json.loads(_get("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"
                               f"{urllib.request.quote(name)}/cids/JSON"))
        cid = data["IdentifierList"]["CID"][0]
    cid = int(cid)
    sdf = _get(f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/SDF?record_type=3d")
    return sdf, "sdf", f"PubChem CID {cid}"


def selection_problems(sel, item):
    """Revisa {chain, resi, resn} contra el resumen guardado en la biblioteca."""
    errs = []
    chains = item.get("chains") or {}
    if "chain" in sel and chains and sel["chain"] not in chains:
        errs.append(f"cadena «{sel['chain']}» no existe (cadenas: {', '.join(chains)})")
    if "resn" in sel and item.get("format") == "pdb" and sel["resn"] not in item.get("ligands", []) \
            and not item.get("chains"):
        errs.append(f"«{sel['resn']}» no aparece en la estructura")
    if "resi" in sel and "chain" in sel and sel["chain"] in (item.get("residues") or {}):
        lo, hi = item["residues"][sel["chain"]]
        vals = sel["resi"] if isinstance(sel["resi"], list) else [sel["resi"]]
        bad = [v for v in vals if not isinstance(v, int) or not lo <= v <= hi]
        if bad:
            errs.append(f"residuos {bad} fuera de la cadena {sel['chain']} ({lo}–{hi})")
    return errs
