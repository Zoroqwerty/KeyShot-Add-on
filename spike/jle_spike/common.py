"""Shared helpers for the Phase 1 spike (doc 03).

Everything except the functions marked "KeyShot only" runs in plain CPython,
so the geometry, maths and PNG code can be unit-tested outside KeyShot.

Spike code is throw-away: its job is to record what KeyShot actually does.
Every KeyShot call goes through Recorder.call(), so an exception is logged as
a finding instead of stopping the run.
"""

import json
import math
import os
import platform
import struct
import sys
import time
import traceback
import zlib

try:
    import lux
    import luxmath
    IN_KEYSHOT = True
except ImportError:  # plain CPython (unit tests)
    lux = None
    luxmath = None
    IN_KEYSHOT = False

PREFIX = "JLESPIKE"
FAILED = object()  # returned by Recorder.call() when the call raised


# ---------------------------------------------------------------- config / io

DEFAULT_CONFIG = {
    "clear_scene": False,        # allow newScene() on a scene that holds non-spike content
    "repeats": 1,
    "render": True,              # experiments that render may be switched off
    "render_size": [400, 400],
    "render_samples": 32,
    "light_material": None,      # library light material name; None = auto-detect
    "kmp_path": None,            # E2 route (b): KMP built in the GUI
    "lighting_preset_to_test": "Jewelry",
}


def spike_home():
    env = os.environ.get("JLE_SPIKE_HOME")
    if env:
        return env
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config():
    cfg = dict(DEFAULT_CONFIG)
    path = os.environ.get("JLE_SPIKE_CONFIG") or os.path.join(spike_home(), "config.json")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            cfg.update(json.load(f))
    variant = os.environ.get("JLE_SPIKE_VARIANT")
    if variant:
        cfg.update(json.loads(variant))
    return cfg


def results_dir():
    d = os.environ.get("JLE_SPIKE_OUT") or os.path.join(os.path.expanduser("~"), "JLE_Spike", "results")
    os.makedirs(d, exist_ok=True)
    return d


def scratch_dir():
    d = os.path.join(os.path.dirname(results_dir()), "scratch")
    os.makedirs(d, exist_ok=True)
    return d


def to_jsonable(v, depth=0):
    if depth > 8:
        return repr(v)
    if v is None or isinstance(v, (bool, int, float, str)):
        if isinstance(v, float) and not math.isfinite(v):
            return repr(v)
        return v
    if isinstance(v, (list, tuple, set)):
        return [to_jsonable(x, depth + 1) for x in v]
    if isinstance(v, dict):
        return {str(k): to_jsonable(x, depth + 1) for k, x in v.items()}
    val = getattr(v, "val", None)  # luxmath.Vector / luxmath.Matrix
    if callable(val):
        try:
            return to_jsonable(val(), depth + 1)
        except Exception:
            pass
    return repr(v)


class Recorder:
    """Appends one JSON object per line to results/<experiment>_<stamp>_<pid>.jsonl."""

    def __init__(self, experiment, variant=None):
        self.experiment = experiment
        self.variant = variant or {}
        stamp = time.strftime("%Y%m%d-%H%M%S")
        self.path = os.path.join(results_dir(), "%s_%s_%d.jsonl" % (experiment, stamp, os.getpid()))
        self.calls_ok = 0
        self.calls_failed = 0
        self.checks_passed = 0
        self.checks_failed = 0
        self.write("meta", **environment_info())

    def write(self, kind, **data):
        rec = {"t": round(time.time(), 3), "experiment": self.experiment,
               "variant": self.variant, "kind": kind}
        rec.update(to_jsonable(data))
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec) + "\n")

    def call(self, label, fn, *args, **kwargs):
        t0 = time.perf_counter()
        try:
            value = fn(*args, **kwargs)
        except Exception as e:
            self.calls_failed += 1
            self.write("call", label=label, ok=False, seconds=round(time.perf_counter() - t0, 4),
                       error="%s: %s" % (type(e).__name__, e),
                       trace=traceback.format_exc(limit=4))
            return FAILED
        self.calls_ok += 1
        self.write("call", label=label, ok=True, seconds=round(time.perf_counter() - t0, 4),
                   value=value)
        return value

    def check(self, label, passed, **details):
        if passed:
            self.checks_passed += 1
        else:
            self.checks_failed += 1
        self.write("check", label=label, passed=bool(passed), **details)
        return passed

    def note(self, text, **details):
        self.write("note", text=text, **details)

    def summary(self):
        s = {"calls_ok": self.calls_ok, "calls_failed": self.calls_failed,
             "checks_passed": self.checks_passed, "checks_failed": self.checks_failed,
             "log": self.path}
        self.write("summary", **s)
        print("[%s] %s" % (self.experiment, json.dumps(s)))
        return s


def environment_info():
    info = {"python": sys.version, "platform": platform.platform(), "in_keyshot": IN_KEYSHOT}
    if IN_KEYSHOT:
        for name in ("getKeyShotVersion", "getKeyShotDisplayVersion", "isHeadless", "getOS"):
            fn = getattr(lux, name, None)
            if fn:
                try:
                    info[name] = fn()
                except Exception as e:
                    info[name] = "error: %s" % e
    return info


def safe(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception as e:
        return {"__error__": "%s: %s" % (type(e).__name__, e)}


def lux_call(name, *args, **kwargs):
    """Call lux.<name> if it exists in this KeyShot version; record absence otherwise."""
    fn = getattr(lux, name, None)
    if fn is None:
        return {"__error__": "lux.%s not present" % name}
    return safe(fn, *args, **kwargs)


# ---------------------------------------------------------------- vector maths

def add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def length(a):
    return math.sqrt(dot(a, a))


def normalize(a):
    n = length(a)
    if n == 0:
        raise ValueError("zero-length vector")
    return (a[0] / n, a[1] / n, a[2] / n)


def mirror_light_position(surface_point, surface_normal, camera_pos, distance):
    """Doc 06 §6.4.3: put a light on the mirror ray so its highlight lands on surface_point."""
    n = normalize(surface_normal)
    o = normalize(sub(camera_pos, surface_point))
    if dot(n, o) <= 0:
        raise ValueError("surface point faces away from the camera")
    i = sub(mul(n, 2 * dot(n, o)), o)
    return add(surface_point, mul(i, distance)), i


def angular_direction(view, up, alpha_deg, beta_deg):
    """Doc 06 §6.4.2: camera-relative direction (alpha off-axis, beta clock angle)."""
    v = normalize(view)
    r = normalize(cross(up, v))
    u = cross(v, r)
    a, b = math.radians(alpha_deg), math.radians(beta_deg)
    side = add(mul(u, math.cos(b)), mul(r, math.sin(b)))
    return normalize(add(mul(v, math.cos(a)), mul(side, math.sin(a))))


def project_point(point, cam_pos, look_at, up, fov_deg, width, height, fov_axis="h"):
    """Pinhole projection to pixel coordinates (x right, y down). fov_axis: 'h' or 'v'."""
    f = normalize(sub(look_at, cam_pos))
    r = normalize(cross(f, up))
    u = cross(r, f)
    d = sub(point, cam_pos)
    x, y, z = dot(d, r), dot(d, u), dot(d, f)
    if z <= 0:
        return None
    t = math.tan(math.radians(fov_deg) / 2)
    if fov_axis == "h":
        sx, sy = t, t * height / width
    else:
        sy, sx = t, t * width / height
    return ((0.5 + 0.5 * x / (z * sx)) * width, (0.5 - 0.5 * y / (z * sy)) * height)


# ---------------------------------------------------------------- OBJ geometry

def rect(name, w=1.0, h=1.0):
    """Unit rectangle in the local XY plane, normal +Z (an area-light host)."""
    hw, hh = w / 2, h / 2
    verts = [(-hw, -hh, 0), (hw, -hh, 0), (hw, hh, 0), (-hw, hh, 0)]
    return (name, verts, [[0, 1, 2, 3]], [(0, 0, 1)] * 4)


def uv_sphere(name, radius=1.0, rings=24, segments=48, center=(0, 0, 0)):
    verts, normals, faces = [], [], []
    for i in range(rings + 1):
        th = math.pi * i / rings
        for j in range(segments):
            ph = 2 * math.pi * j / segments
            n = (math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph))
            normals.append(n)
            verts.append(add(center, mul(n, radius)))
    for i in range(rings):
        for j in range(segments):
            a = i * segments + j
            b = i * segments + (j + 1) % segments
            c = (i + 1) * segments + (j + 1) % segments
            d = (i + 1) * segments + j
            faces.append([a, b, c, d])  # counter-clockwise seen from outside
    return (name, verts, faces, normals)


def torus(name, major=1.0, minor=0.2, segments=64, sides=24):
    """Ring in the XZ plane (axis = Y)."""
    verts, normals, faces = [], [], []
    for i in range(segments):
        u = 2 * math.pi * i / segments
        cu, su = math.cos(u), math.sin(u)
        for j in range(sides):
            v = 2 * math.pi * j / sides
            n = (math.cos(v) * cu, math.sin(v), math.cos(v) * su)
            normals.append(n)
            verts.append(((major + minor * math.cos(v)) * cu, minor * math.sin(v),
                          (major + minor * math.cos(v)) * su))
    for i in range(segments):
        for j in range(sides):
            a = i * sides + j
            b = ((i + 1) % segments) * sides + j
            c = ((i + 1) % segments) * sides + (j + 1) % sides
            d = i * sides + (j + 1) % sides
            faces.append([a, d, c, b])
    return (name, verts, faces, normals)


def simple_brilliant(name, radius=1.0, n=16, table=0.53, crown_deg=34.5, pavilion_deg=40.75,
                     center=(0, 0, 0)):
    """Faceted round-brilliant stand-in (table up = +Y). Flat normals per facet.

    Not a real 57-facet brilliant: good enough to exercise gem materials and
    lights, not for optical conclusions (doc 12 asks for proper reference stones).
    """
    rt = radius * table
    hc = (radius - rt) * math.tan(math.radians(crown_deg))
    hp = radius * math.tan(math.radians(pavilion_deg))
    ring = lambda r, y, k: (r * math.cos(2 * math.pi * k / n), y, r * math.sin(2 * math.pi * k / n))
    polys = [[ring(rt, hc, k) for k in reversed(range(n))]]  # table
    for k in range(n):
        k2 = (k + 1) % n
        polys.append([ring(radius, 0, k), ring(radius, 0, k2), ring(rt, hc, k2), ring(rt, hc, k)][::-1])
        polys.append([ring(radius, 0, k), (0, -hp, 0), ring(radius, 0, k2)][::-1])
    polys = [[add(center, p) for p in poly] for poly in polys]
    return flat_mesh(name, polys)


def transform_object(obj, rotate=None, translate=(0, 0, 0), scale=1.0, name=None):
    """Apply p -> rotate(p) * scale + translate to an OBJ tuple. rotate maps (x,y,z) -> (x,y,z)."""
    rot = rotate or (lambda p: p)
    oname, verts, faces, normals = obj
    verts = [add(mul(rot(v), scale), translate) for v in verts]
    normals = [normalize(rot(nv)) for nv in normals] if normals else normals
    return (name or oname, verts, faces, normals)


def rot_x(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return lambda p: (p[0], c * p[1] - s * p[2], s * p[1] + c * p[2])


def rot_y(deg):
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    return lambda p: (c * p[0] + s * p[2], p[1], -s * p[0] + c * p[2])


AXIS_MAPPINGS = {
    # how an importer might convert OBJ axes; E1 reports which one KeyShot applied
    "identity": lambda p: (p[0], p[1], p[2]),
    "z_up_to_y_up": lambda p: (p[0], p[2], -p[1]),
    "z_up_to_y_up_alt": lambda p: (p[0], -p[2], p[1]),
}


def bbox_of_points(points):
    xs, ys, zs = zip(*points)
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def fit_import_mapping(expected_objects, actual_bboxes, scales=(1.0, 0.001, 1000.0, 0.01, 100.0, 0.1, 10.0)):
    """Find the axis mapping and scale that best explains imported world bboxes (E1)."""
    best = None
    for mname, fn in AXIS_MAPPINGS.items():
        for s in scales:
            err = 0.0
            for obj, actual in zip(expected_objects, actual_bboxes):
                lo, hi = bbox_of_points([mul(fn(v), s) for v in obj[1]])
                err += sum(abs(a - b) for a, b in zip(lo + hi, tuple(actual[0]) + tuple(actual[1])))
            size = max(1e-12, sum(length(sub(a[1], a[0])) for a in actual_bboxes))
            rel = err / size
            if best is None or rel < best["relative_error"]:
                best = {"mapping": mname, "scale": s, "relative_error": rel}
    return best


def flat_mesh(name, polygons):
    verts, normals, faces = [], [], []
    for poly in polygons:
        nrm = normalize(cross(sub(poly[1], poly[0]), sub(poly[2], poly[0])))
        start = len(verts)
        verts.extend(poly)
        normals.extend([nrm] * len(poly))
        faces.append(list(range(start, start + len(poly))))
    return (name, verts, faces, normals)


def obj_text(objects):
    """objects: (name, verts, faces (0-based), normals or None). Normals index == vertex index."""
    out = ["# JLE spike geometry"]
    base = 1
    for name, verts, faces, normals in objects:
        out.append("o " + name)
        out.extend("v %.9g %.9g %.9g" % v for v in verts)
        if normals:
            out.extend("vn %.9g %.9g %.9g" % nv for nv in normals)
        for face in faces:
            if normals:
                out.append("f " + " ".join("%d//%d" % (base + i, base + i) for i in face))
            else:
                out.append("f " + " ".join(str(base + i) for i in face))
        base += len(verts)
    return "\n".join(out) + "\n"


def write_obj(filename, objects):
    path = os.path.join(scratch_dir(), filename)
    with open(path, "w", encoding="ascii") as f:
        f.write(obj_text(objects))
    return path


def object_bbox(obj):
    xs, ys, zs = zip(*obj[1])
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


# ---------------------------------------------------------------- PNG (stdlib)

class Image:
    def __init__(self, width, height, channels, bitdepth, samples):
        self.width, self.height, self.channels, self.bitdepth = width, height, channels, bitdepth
        self.samples = samples  # flat list of floats in [0, 1], row-major, interleaved channels

    def rgb(self, x, y):
        i = (y * self.width + x) * self.channels
        s = self.samples
        if self.channels >= 3:
            return s[i], s[i + 1], s[i + 2]
        return s[i], s[i], s[i]

    def luminance_display(self):
        """Rec.709 weights on display-referred values (fine for blob finding)."""
        lum = []
        c, s = self.channels, self.samples
        for i in range(0, len(s), c):
            if c >= 3:
                lum.append(0.2126 * s[i] + 0.7152 * s[i + 1] + 0.0722 * s[i + 2])
            else:
                lum.append(s[i])
        return lum


def _paeth(a, b, c):
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def read_png(path):
    with open(path, "rb") as f:
        data = f.read()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG file: %s" % path)
    pos, idat, header = 8, [], None
    while pos < len(data):
        n, ctype = struct.unpack(">I4s", data[pos:pos + 8])
        chunk = data[pos + 8:pos + 8 + n]
        pos += 12 + n
        if ctype == b"IHDR":
            header = struct.unpack(">IIBBBBB", chunk)
        elif ctype == b"IDAT":
            idat.append(chunk)
        elif ctype == b"IEND":
            break
    width, height, bitdepth, colortype, _, _, interlace = header
    if interlace:
        raise ValueError("interlaced PNG not supported")
    channels = {0: 1, 2: 3, 4: 2, 6: 4}.get(colortype)
    if channels is None or bitdepth not in (8, 16):
        raise ValueError("unsupported PNG (colour type %d, bit depth %d)" % (colortype, bitdepth))
    bpp = channels * bitdepth // 8
    stride = width * bpp
    raw = zlib.decompress(b"".join(idat))
    prev = bytearray(stride)
    rows = bytearray()
    i = 0
    for _ in range(height):
        ftype = raw[i]
        line = bytearray(raw[i + 1:i + 1 + stride])
        i += 1 + stride
        if ftype == 1:
            for x in range(bpp, stride):
                line[x] = (line[x] + line[x - bpp]) & 255
        elif ftype == 2:
            for x in range(stride):
                line[x] = (line[x] + prev[x]) & 255
        elif ftype == 3:
            for x in range(stride):
                left = line[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + ((left + prev[x]) >> 1)) & 255
        elif ftype == 4:
            for x in range(stride):
                left = line[x - bpp] if x >= bpp else 0
                upleft = prev[x - bpp] if x >= bpp else 0
                line[x] = (line[x] + _paeth(left, prev[x], upleft)) & 255
        elif ftype != 0:
            raise ValueError("bad PNG filter type %d" % ftype)
        rows += line
        prev = line
    if bitdepth == 8:
        samples = [b / 255.0 for b in rows]
    else:
        samples = [v / 65535.0 for v in struct.unpack(">%dH" % (len(rows) // 2), bytes(rows))]
    return Image(width, height, channels, bitdepth, samples)


def brightest_blob_centroid(image, rel_threshold=0.9):
    """Centroid of pixels within rel_threshold of the maximum luminance (black-background tests)."""
    lum = image.luminance_display()
    peak = max(lum)
    if peak <= 0:
        return None
    cut = peak * rel_threshold
    sx = sy = n = 0
    w = image.width
    for idx, v in enumerate(lum):
        if v >= cut:
            sx += idx % w
            sy += idx // w
            n += 1
    return (sx / n + 0.5, sy / n + 0.5, n, peak)


# ---------------------------------------------------------------- scene state (KeyShot only)

def vec3(v):
    """Convert luxmath.Vector / tuple to a plain tuple."""
    if v is None:
        return None
    val = getattr(v, "val", None)
    if callable(val):
        v = val()
    return tuple(float(x) for x in v)


def all_nodes():
    return lux.getSceneTree().find("")


def node_info(node):
    info = {"id": safe(node.getID), "name": safe(node.getName),
            "path": safe(node.getPath, text=True), "kind": safe(node.getKind),
            "hidden": safe(node.isHidden)}
    if safe(node.isObject) is True:
        info["material"] = safe(node.getMaterial)
        bb = safe(node.getBoundingBox, world=True)
        if isinstance(bb, (tuple, list)) and len(bb) == 2:
            info["bbox_world"] = [vec3(bb[0]), vec3(bb[1])]
        else:
            info["bbox_world"] = bb
        info["transform_world"] = to_jsonable(safe(node.getTransform, world=True))
    return info


def snapshot():
    """Everything the tool promises not to change. Used for before/after diffs."""
    s = {"camera": {}, "environment": {}, "render": {}, "scene": {}, "nodes": {}}
    for name in ("getCamera", "getCameraPosition", "getCameraLookAt", "getCameraUp",
                 "getCameraFieldOfView", "getCameraLens", "isCameraUnsaved", "getCameras"):
        s["camera"][name] = to_jsonable(lux_call(name))
    env = safe(lux.getActiveEnvironment)
    if not isinstance(env, dict):
        for name in ("getName", "getBrightness", "getRotation", "getSize", "getHeight",
                     "getBackgroundColor", "getLightingEnvironment", "getGroundShadows",
                     "getGroundReflections", "getFlattenGround"):
            fn = getattr(env, name, None)
            if fn:
                s["environment"][name] = to_jsonable(safe(fn))
    s["environment"]["all"] = to_jsonable(safe(lux.getEnvironments))
    s["render"]["lighting_preset"] = to_jsonable(safe(lux.getLightingPreset))
    s["render"]["engine"] = to_jsonable(safe(lux.getRenderEngine))
    ro = safe(lux.getRenderOptions)
    s["render"]["options"] = to_jsonable(safe(ro.getDict)) if not isinstance(ro, dict) else ro
    for name in ("getSceneInfo", "getSceneMaterials", "getModelSets", "isSceneChanged",
                 "isUndoEnabled"):
        s["scene"][name] = to_jsonable(lux_call(name))
    for node in all_nodes():
        info = node_info(node)
        s["nodes"][str(info["id"])] = info
    return s


def diff(a, b, path="", tol=1e-6, out=None):
    """Recursive diff of two jsonable structures; floats compared with tolerance."""
    out = [] if out is None else out
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a:
                out.append((path + "/" + k, "<missing>", b[k]))
            elif k not in b:
                out.append((path + "/" + k, a[k], "<missing>"))
            else:
                diff(a[k], b[k], path + "/" + k, tol, out)
    elif isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        for i, (x, y) in enumerate(zip(a, b)):
            diff(x, y, "%s[%d]" % (path, i), tol, out)
    elif isinstance(a, (int, float)) and isinstance(b, (int, float)) \
            and not isinstance(a, bool) and not isinstance(b, bool):
        if abs(a - b) > tol * max(1.0, abs(a), abs(b)):
            out.append((path, a, b))
    elif a != b:
        out.append((path, a, b))
    return out


def snapshot_diff_excluding_new_nodes(before, after):
    """Diff that ignores nodes created during the step (reported separately)."""
    b2 = dict(after)
    b2["nodes"] = {k: v for k, v in after["nodes"].items() if k in before["nodes"]}
    changes = diff(before, b2)
    new_ids = [k for k in after["nodes"] if k not in before["nodes"]]
    return changes, new_ids


def ensure_fresh_scene(rec, cfg):
    """Start from an empty scene. Refuse to clear anything that is not spike content."""
    if not lux.hasContents():
        return True
    foreign = [n.getName() for n in all_nodes()
               if safe(n.isObject) is True and not str(n.getName()).startswith(PREFIX)]
    if foreign and not cfg.get("clear_scene"):
        rec.note("refused: scene holds non-spike objects; open a new empty scene first",
                 foreign_objects=foreign[:20])
        raise RuntimeError("Scene is not empty. Save your work, open a NEW empty scene, "
                           "then run the spike again. Nothing was changed.")
    rec.call("newScene", lux.newScene, dontAsk=True)
    return True


def safe_import_options(**overrides):
    """Import options intended to leave camera, environment and placement untouched (E1)."""
    opts = lux.getImportOptions()
    opts.update({"import_type": 0, "center_geometry": False, "snap_to_ground": False,
                 "adjust_camera_look_at": False, "adjust_environment": False,
                 "separate_parts": True, "merge_objects": False, "merge_groups": False,
                 "retain_materials": False})
    opts.update(overrides)
    return opts


def import_objects(rec, label, filename, objects, opts=None):
    """Write an OBJ, import it, and return the nodes that appeared (by ID diff)."""
    path = write_obj(filename, objects)
    before = {safe(n.getID) for n in all_nodes()}
    ok = rec.call(label + ".importFile", lux.importFile, path, showOpts=False, dontAsk=True,
                  opts=opts if opts is not None else safe_import_options())
    new_nodes = [n for n in all_nodes() if safe(n.getID) not in before]
    rec.write("import_result", label=label, ok=ok, new_nodes=[node_info(n) for n in new_nodes])
    return new_nodes


def objects_named(nodes, prefix):
    return [n for n in nodes if safe(n.isObject) is True and str(safe(n.getName)).startswith(prefix)]


def find_library_materials(rec, keywords_any, filters=(None, "Materials/Light", "Light", "Materials/Metal", "Metal")):
    """Return library entries whose text contains any keyword (case-insensitive)."""
    found = []
    for flt in filters:
        res = rec.call("getLibraryMaterials(%s)" % flt, lux.getLibraryMaterials,
                       **({} if flt is None else {"filter": flt}))
        if res is FAILED or not res:
            continue
        for entry in res:
            text = str(entry).lower()
            if any(k.lower() in text for k in keywords_any) and entry not in found:
                found.append(entry)
        if found:
            break
    rec.write("library_search", keywords=keywords_any, found=found[:50])
    return found


def material_name_candidates(entry):
    """Library entries may be names or relative paths; try both forms with setMaterial."""
    s = str(entry)
    base = os.path.splitext(os.path.basename(s))[0]
    return [x for x in (s, base) if x]


def dump_material(rec, material_name):
    graph = rec.call("getMaterialGraph(%s)" % material_name, lux.getMaterialGraph, material_name)
    if graph is FAILED:
        return None
    root = rec.call("graph.getRoot", graph.getRoot)
    if root is FAILED:
        return None
    params = []
    plist = rec.call("root.getParameters", root.getParameters)
    for p in (plist if plist is not FAILED else []):
        params.append({"name": safe(p.getName), "display": safe(p.getDisplayName),
                       "type": safe(p.getType), "pure": safe(p.isPure),
                       "value": to_jsonable(safe(p.getValue))})
    edges = rec.call("root.getInputEdges", root.getInputEdges)
    dump = {"material": material_name, "root_type": to_jsonable(safe(root.getType)),
            "root_name": safe(root.getName), "parameters": params,
            "input_edges": to_jsonable(edges if edges is not FAILED else None),
            "node_count": len(safe(graph.getNodes) or [])}
    rec.write("material_dump", **dump)
    return dump


def make_render_options(cfg, samples=None):
    opts = lux.getRenderOptions()
    opts.setMaxSamplesRendering(int(samples or cfg["render_samples"]))
    return opts


def render_png(rec, label, cfg, width=None, height=None, samples=None):
    w, h = width or cfg["render_size"][0], height or cfg["render_size"][1]
    path = os.path.join(scratch_dir(), "%s_%s_%d.png" % (PREFIX, label, int(time.time() * 1000)))
    t0 = time.perf_counter()
    ok = rec.call("renderImage(%s)" % label, lux.renderImage, path, width=w, height=h,
                  opts=make_render_options(cfg, samples))
    seconds = time.perf_counter() - t0
    rec.write("render", label=label, ok=ok, path=path, width=w, height=h, seconds=round(seconds, 3),
              exists=os.path.exists(path))
    return path if (ok is not FAILED and os.path.exists(path)) else None
