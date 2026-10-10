"""A crude stand-in for KeyShot's lux/luxmath, used ONLY to smoke-test the harness code paths.

It does not model KeyShot behaviour. Passing smoke tests means "the harness has no
Python-level bugs on these paths", nothing more.
"""

import itertools
import os
import struct
import types
import zlib

_ids = itertools.count(1)


def _png(path, w, h):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            v = 255 if abs(x - w // 2) < 2 and abs(y - h // 2) < 2 else 0
            raw += bytes((v, v, v))

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(bytes(raw))) + chunk(b"IEND", b""))


class Vector:
    def __init__(self, *a):
        self._v = tuple(a[0]) if len(a) == 1 and isinstance(a[0], (tuple, list)) else tuple(a)

    def val(self):
        return self._v


class Matrix:
    def __init__(self, data=None):
        self._ops = []

    def makeIdentity(self):
        return Matrix()

    def _with(self, op):
        m = Matrix()
        m._ops = self._ops + [op]
        return m

    def translate(self, v):
        return self._with(("t", v.val()))

    def scale(self, s):
        return self._with(("s", s))

    def rotateAroundAxis(self, axis, angle):
        return self._with(("r", axis.val(), angle))

    def val(self):
        return tuple(float(i % 5 == 0) for i in range(16))


class ShaderParameter:
    def __init__(self, name, value):
        self.name, self.value = name, value

    def getName(self):
        return self.name

    def getDisplayName(self):
        return self.name.title()

    def getType(self):
        return 7

    def isPure(self):
        return False

    def getValue(self):
        return self.value

    def setValue(self, v):
        self.value = v


class ShaderNode:
    def __init__(self, stype):
        self.id = next(_ids)
        self.stype = stype
        self.params = ([ShaderParameter("power", 100.0), ShaderParameter("color", (1, 1, 1)),
                        ShaderParameter("camera_visible", True)] if "light" in stype
                       else [ShaderParameter("diffuse", (0.5, 0.5, 0.5))])

    def getID(self):
        return self.id

    def getName(self):
        return self.stype

    def getType(self):
        return (self.stype, self.stype.replace("lux_", "").title())

    def getParameters(self):
        return list(self.params)

    def getInputEdges(self):
        return []


class MaterialGraph:
    def __init__(self, stype):
        self.root = ShaderNode(stype)
        self.nodes = [self.root]

    def getRoot(self):
        return self.root

    def getNodes(self):
        return list(self.nodes)

    def newNode(self, stype):
        n = ShaderNode(stype)
        self.nodes.append(n)
        return n

    def newEdge(self, source, target, param):
        raise ValueError("fake: unknown parameter %s" % param)


class SceneNode:
    def __init__(self, name, kind, bbox=None, parent=None):
        self.id, self.name, self.kind, self.parent = next(_ids), name, kind, parent
        self.children, self.hidden, self.deleted = [], False, False
        self.material = "Default" if kind == 2 else None
        self.bbox = bbox

    def getID(self):
        return self.id

    def getName(self):
        return self.name

    def getPath(self, text=False):
        p, n = [], self
        while n:
            p.append(n.name if text else n)
            n = n.parent
        return tuple(reversed(p))

    def getKind(self):
        return self.kind

    def isObject(self):
        return self.kind == 2

    def isGroup(self):
        return self.kind == 1

    def isHidden(self):
        return self.hidden

    def isDeleted(self):
        return self.deleted

    def hide(self):
        self.hidden = True

    def show(self):
        self.hidden = False

    def delete(self):
        self.deleted = True

    def getMaterial(self):
        return self.material

    def setMaterial(self, mat, link=False):
        if mat not in _state["materials"] and mat not in _LIBRARY:
            raise ValueError("fake: unknown material %s" % mat)
        if link:
            self.material = mat
        else:
            name = "%s #%d" % (mat, next(_ids))
            stype = _state["materials"].get(mat) or _LIBRARY[mat]
            _state["materials"][name] = stype if isinstance(stype, str) else stype.root.stype
            self.material = name

    def getBoundingBox(self, world=False):
        return (Vector(self.bbox[0]), Vector(self.bbox[1])) if self.bbox else (Vector(0, 0, 0), Vector(0, 0, 0))

    def getTransform(self, world=False):
        return Matrix()

    def applyTransform(self, m, absolute=False):
        return True

    def duplicate(self, amount=1, linkMats=False):
        d = SceneNode(self.name, self.kind, self.bbox, self.parent)
        self.parent.children.append(d)
        return True

    def _walk(self):
        for c in self.children:
            yield c
            yield from c._walk()

    def find(self, name=None, mat=None, all=False, types=None, depth=-1, deleted=False):
        return [n for n in self._walk() if (deleted or not n.deleted)
                and (not name or name in n.name)]

    def getDeleted(self):
        return [n for n in self._walk() if n.deleted]


_LIBRARY = {"Area Light 100W": "lux_mesh_light", "Polished Chrome": "lux_metal",
            "Gold Polished": "lux_metal", "Diamond": "lux_gem"}
_state = {}


def _reset():
    _state.clear()
    _state.update({"root": SceneNode("root", 1), "materials": {"Default": "lux_diffuse"},
                   "camera": {"pos": (0, 0, 10), "look": (0, 0, 0), "up": (0, 1, 0), "fov": 30,
                              "name": "default", "unsaved": False},
                   "cameras": ["default"], "env": "Env", "envs": {"Env": {"brightness": 1.0}},
                   "preset": "Product", "changed": False})


def _parse_obj(path):
    objs, cur = [], None
    with open(path) as f:
        for line in f:
            if line.startswith("o "):
                cur = [line[2:].strip(), []]
                objs.append(cur)
            elif line.startswith("v "):
                cur[1].append(tuple(float(x) for x in line.split()[1:4]))
    return objs


class Env:
    def __init__(self, name):
        self.name = name

    def getName(self):
        return self.name

    def getBrightness(self):
        return _state["envs"][self.name]["brightness"]

    def setBrightness(self, v):
        _state["envs"][self.name]["brightness"] = v

    def setBackgroundColor(self, c):
        _state["envs"][self.name]["bg"] = c

    def getBackgroundColor(self):
        return _state["envs"][self.name].get("bg", (0, 0, 0))

    def setGroundShadows(self, v):
        pass

    def setGroundReflections(self, v):
        pass


class RenderOptions:
    def __init__(self):
        self.d = {"samples": 64}

    def getDict(self):
        return dict(self.d)

    def setMaxSamplesRendering(self, n):
        self.d["samples"] = n


def build_modules():
    lux = types.ModuleType("lux")
    luxmath = types.ModuleType("luxmath")
    luxmath.Vector, luxmath.Matrix = Vector, Matrix
    _reset()

    def importFile(path, showOpts=False, dontAsk=True, opts=None):
        grp = SceneNode(os.path.basename(path), 1, parent=_state["root"])
        _state["root"].children.append(grp)
        for name, verts in _parse_obj(path):
            xs, ys, zs = zip(*verts)
            grp.children.append(SceneNode(name, 2, ((min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))), grp))
        _state["changed"] = True
        return True

    def getMaterialGraph(name):
        stype = _state["materials"].get(name)
        if stype is None:
            raise ValueError("fake: no material %s" % name)
        if isinstance(stype, str):
            _state["materials"][name] = MaterialGraph(stype)
        return _state["materials"][name]

    def createSceneMaterial(name):
        _state["materials"][name] = "lux_diffuse"

    def renderImage(path, width=None, height=None, opts=None, format=None):
        _png(path, width or 64, height or 64)
        return True

    def newCamera(name, unique=False):
        _state["cameras"].append(name)
        _state["camera"]["name"] = name
        return True

    def setCamera(name):
        _state["camera"]["name"] = name

    cam = lambda key: (lambda: _state["camera"][key])

    def setter(key):
        def f(v=None, pt=None, **kw):
            _state["camera"][key] = pt if pt is not None else v
            _state["camera"]["unsaved"] = True
        return f

    funcs = dict(
        getSceneTree=lambda: _state["root"],
        hasContents=lambda: bool(_state["root"].children),
        newScene=lambda dontAsk=True: _reset(),
        importFile=importFile,
        getImportOptions=lambda **k: {"import_type": 0},
        getSceneMaterials=lambda: sorted(_state["materials"]),
        getMaterialGraph=getMaterialGraph,
        createSceneMaterial=createSceneMaterial,
        getLibraryMaterials=lambda filter=None: list(_LIBRARY),
        importMaterials=lambda f, folder=".": True,
        deleteMaterial=lambda name: _state["materials"].pop(name, None),
        getCamera=cam("name"), getCameras=lambda: list(_state["cameras"]),
        getCameraPosition=cam("pos"), getCameraLookAt=cam("look"), getCameraUp=cam("up"),
        getCameraFieldOfView=cam("fov"), getCameraLens=lambda: {"lens": 16384},
        getCameraDistance=lambda: 10.0, setCameraDistance=lambda d: None,
        setCameraPosition=setter("pos"), setCameraLookAt=setter("look"), setCameraUp=setter("up"),
        setCameraFieldOfView=setter("fov"), saveCamera=lambda: None, newCamera=newCamera,
        setCamera=setCamera, isCameraUnsaved=lambda: _state["camera"]["unsaved"],
        getActiveEnvironment=lambda: Env(_state["env"]),
        getEnvironments=lambda: list(_state["envs"]),
        newEnvironment=lambda name, activate=True, clone=True: (
            _state["envs"].__setitem__(name, dict(_state["envs"][_state["env"]])),
            _state.__setitem__("env", name if activate else _state["env"])),
        setActiveEnvironment=lambda name: _state.__setitem__("env", name),
        removeEnvironment=lambda name: _state["envs"].pop(name, None),
        getLightingPreset=lambda: _state["preset"],
        getLightingPresets=lambda: ["Performance Mode", "Basic", "Product", "Interior", "Jewelry"],
        setLightingPreset=lambda n: _state.__setitem__("preset", n),
        getRenderOptions=lambda defaults=False: RenderOptions(),
        getRenderEngine=lambda: 0, renderImage=renderImage,
        getSceneInfo=lambda: {"file": _state.get("file")}, getModelSets=lambda: ["Default"],
        isSceneChanged=lambda: _state["changed"], isUndoEnabled=lambda: True,
        saveFile=lambda path=None, excludeFlags=None: (_state.__setitem__("file", path),
                                                       open(path, "w").write("fake")),
        openFile=lambda path, dontAsk=True: None,
        getKeyShotVersion=lambda: (2026, 2, 0, 0), getKeyShotDisplayVersion=lambda: (2026, 2),
        isHeadless=lambda: False, getOS=lambda: "fake", getSystemInfo=lambda: {},
        getKeyShotFolder=lambda t: "/tmp",
    )
    for k, v in funcs.items():
        setattr(lux, k, v)
    lux.SceneNode, lux.MaterialGraph, lux.ShaderNode = SceneNode, MaterialGraph, ShaderNode
    lux.ShaderParameter, lux.Env, lux.RenderOptions = ShaderParameter, Env, RenderOptions
    lux.FOLDER_SCRIPTS = 12
    lux.SHADER_TYPE_MESH_LIGHT = "lux_mesh_light"
    lux.SHADER_TYPE_METAL = "lux_metal"
    return lux, luxmath
