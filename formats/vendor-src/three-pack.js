// Paquete de Three.js para las escenas 3D (formats/packs/cinematic.py). Lo construye formats/vendors.py con
// esbuild (IIFE, sin red ni CDN): deja THREE, POSTPROCESSING y los complementos que usan los formatos.
import * as THREE from "three";
import * as POSTPROCESSING from "postprocessing";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

globalThis.THREE = THREE;
globalThis.POSTPROCESSING = POSTPROCESSING;
globalThis.THREE_ADDONS = { GLTFLoader, RoomEnvironment };
