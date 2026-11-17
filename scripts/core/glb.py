"""Modelos 3D en glTF binario (.glb): leer el resumen (validar) y escribir mallas simples.

`summary(data)` valida la cabecera y devuelve lo que importa para usarlo en una escena: mallas, triángulos,
materiales, texturas y si depende de archivos externos (no se admite: el render no usa red ni rutas sueltas).
`write(meshes)` arma un .glb con mallas de posiciones, normales e índices y material PBR; lo usan los modelos
de ejemplo del motor (scripts/tools/models.py builtins), hechos aquí y no descargados.
"""
import json
import struct

import numpy as np

MAGIC, JSON_T, BIN_T = 0x46546C67, 0x4E4F534A, 0x004E4942
MAX_MB = 25  # más pesado infla el proyecto (se sirve en base64) y tarda en cargar antes del primer cuadro


def _chunks(data):
    if len(data) < 20:
        raise ValueError("archivo demasiado corto para ser .glb")
    magic, version, length = struct.unpack_from("<III", data, 0)
    if magic != MAGIC:
        raise ValueError("no es un glTF binario (.glb); convierte .gltf/.obj/.fbx a .glb (p. ej. con Blender)")
    if version != 2:
        raise ValueError(f"glTF versión {version}: se necesita 2.0")
    if length != len(data):
        raise ValueError("archivo .glb incompleto")
    off, out = 12, {}
    while off + 8 <= len(data):
        n, kind = struct.unpack_from("<II", data, off)
        out.setdefault(kind, data[off + 8:off + 8 + n])
        off += 8 + n
    if JSON_T not in out:
        raise ValueError(".glb sin bloque JSON")
    return json.loads(out[JSON_T].decode("utf-8")), out.get(BIN_T, b"")


def summary(data):
    """{meshes, triangles, materials, textures, generator, mb} o ValueError con el motivo."""
    g, _ = _chunks(data)
    external = [b.get("uri") for b in g.get("buffers", []) if b.get("uri")] + \
               [i.get("uri") for i in g.get("images", []) if i.get("uri") and not i["uri"].startswith("data:")]
    if external:
        raise ValueError(f"el modelo usa archivos externos ({external[:3]}); expórtalo con todo incrustado (.glb)")
    tris = 0
    acc = g.get("accessors", [])
    for m in g.get("meshes", []):
        for p in m.get("primitives", []):
            if p.get("mode", 4) != 4:
                continue
            n = acc[p["indices"]]["count"] if "indices" in p else acc[p["attributes"]["POSITION"]]["count"]
            tris += n // 3
    if not g.get("meshes"):
        raise ValueError("el modelo no tiene mallas")
    return {"meshes": len(g.get("meshes", [])), "triangles": tris, "materials": len(g.get("materials", [])),
            "textures": len(g.get("textures", [])), "animations": len(g.get("animations", [])),
            "generator": g.get("asset", {}).get("generator", ""), "mb": round(len(data) / 1e6, 2)}


def _normals(pos, idx):
    n = np.zeros_like(pos)
    tri = pos[idx.reshape(-1, 3)]
    fn = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    for k in range(3):
        np.add.at(n, idx.reshape(-1, 3)[:, k], fn)
    return n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-9)


def lathe(profile, segments=64):
    """Superficie de revolución alrededor del eje Y. profile: [(radio, y), …] → (posiciones, índices)."""
    prof = np.asarray(profile, np.float32)
    a = np.linspace(0, 2 * np.pi, segments, endpoint=False)
    pos = np.stack([np.outer(np.cos(a), prof[:, 0]), np.tile(prof[:, 1], (segments, 1)),
                    np.outer(np.sin(a), prof[:, 0])], axis=-1).reshape(-1, 3).astype(np.float32)
    m = len(prof)
    idx = []
    for s in range(segments):
        s2 = (s + 1) % segments
        for k in range(m - 1):
            a0, a1, b0, b1 = s * m + k, s * m + k + 1, s2 * m + k, s2 * m + k + 1
            idx += [a0, b0, a1, a1, b0, b1]
    return pos, np.asarray(idx, np.uint32)


def write(meshes, generator="VideoVibe"):
    """meshes: [{name, positions (N,3), indices (M,), material: {name, color (r,g,b,a), metallic, roughness,
    emissive?, blend?, double?}}] → bytes .glb (un nodo por malla, todo incrustado)."""
    g = {"asset": {"version": "2.0", "generator": generator}, "scene": 0, "scenes": [{"nodes": []}],
         "nodes": [], "meshes": [], "materials": [], "accessors": [], "bufferViews": [], "buffers": []}
    blob = bytearray()

    def view(arr, target):
        while len(blob) % 4:
            blob.append(0)
        g["bufferViews"].append({"buffer": 0, "byteOffset": len(blob), "byteLength": arr.nbytes, "target": target})
        blob.extend(arr.tobytes())
        return len(g["bufferViews"]) - 1

    for i, m in enumerate(meshes):
        pos = np.asarray(m["positions"], np.float32)
        idx = np.asarray(m["indices"], np.uint32)
        nor = _normals(pos, idx).astype(np.float32)
        acc = []
        for arr, kind, target in ((pos, "VEC3", 34962), (nor, "VEC3", 34962)):
            a = {"bufferView": view(arr, target), "componentType": 5126, "count": len(arr), "type": kind}
            if arr is pos:
                a.update(min=pos.min(0).tolist(), max=pos.max(0).tolist())
            g["accessors"].append(a)
            acc.append(len(g["accessors"]) - 1)
        g["accessors"].append({"bufferView": view(idx, 34963), "componentType": 5125, "count": len(idx),
                               "type": "SCALAR"})
        mat = m["material"]
        md = {"name": mat["name"], "pbrMetallicRoughness": {"baseColorFactor": list(mat["color"]),
              "metallicFactor": mat.get("metallic", 0.0), "roughnessFactor": mat.get("roughness", 0.5)}}
        if mat.get("emissive"):
            md["emissiveFactor"] = list(mat["emissive"])
        if mat.get("blend"):
            md["alphaMode"] = "BLEND"
        if mat.get("double"):
            md["doubleSided"] = True
        g["materials"].append(md)
        g["meshes"].append({"name": m["name"], "primitives": [{"attributes": {"POSITION": acc[0], "NORMAL": acc[1]},
                            "indices": len(g["accessors"]) - 1, "material": i}]})
        g["nodes"].append({"name": m["name"], "mesh": i})
        g["scenes"][0]["nodes"].append(i)
    while len(blob) % 4:
        blob.append(0)
    g["buffers"].append({"byteLength": len(blob)})
    js = json.dumps(g, separators=(",", ":")).encode()
    js += b" " * (-len(js) % 4)
    total = 12 + 8 + len(js) + 8 + len(blob)
    return (struct.pack("<III", MAGIC, 2, total) + struct.pack("<II", len(js), JSON_T) + js
            + struct.pack("<II", len(blob), BIN_T) + bytes(blob))
