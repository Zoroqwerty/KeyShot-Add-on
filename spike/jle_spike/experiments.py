"""Phase 1 spike experiments (doc 03). KeyShot only.

Each experiment:
  * starts from an empty scene (refuses to touch a scene with non-spike content),
  * wraps every KeyShot call so failures are recorded rather than fatal,
  * writes one JSONL log in ~/JLE_Spike/results (see summarize.py).

These scripts were written without access to KeyShot. Treat errors in the
logs as information about the API, not necessarily as harness bugs, but do
check the traceback before drawing conclusions.
"""

import importlib
import json
import math
import os
import time

from . import common as C
from .common import FAILED, PREFIX, lux, luxmath


# ---------------------------------------------------------------- helpers

def _vec(t):
    return luxmath.Vector(tuple(float(x) for x in t))


def _identity():
    return luxmath.Matrix().makeIdentity()


def _bbox(node):
    bb = C.safe(node.getBoundingBox, world=True)
    if isinstance(bb, (tuple, list)) and len(bb) == 2:
        return C.vec3(bb[0]), C.vec3(bb[1])
    return None


def _center(bb):
    return tuple((a + b) / 2 for a, b in zip(bb[0], bb[1]))


def _extent(bb):
    return tuple(b - a for a, b in zip(bb[0], bb[1]))


def _set_camera(rec, name, pos, look_at, up, fov):
    rec.call("newCamera", lux.newCamera, name, unique=True)
    rec.call("setCameraPosition", lux.setCameraPosition, tuple(pos))
    rec.call("setCameraLookAt", lux.setCameraLookAt, pt=tuple(look_at))
    rec.call("setCameraUp", lux.setCameraUp, tuple(up))
    rec.call("setCameraFieldOfView", lux.setCameraFieldOfView, fov)
    rec.call("saveCamera", lux.saveCamera)
    state = {
        "pos": C.vec3(C.safe(lux.getCameraPosition)),
        "look_at": C.vec3(C.safe(lux.getCameraLookAt)),
        "up": C.vec3(C.safe(lux.getCameraUp)),
        "fov": C.safe(lux.getCameraFieldOfView),
        "lens": C.safe(lux.getCameraLens),
    }
    rec.write("camera_readback", requested={"pos": pos, "look_at": look_at, "up": up, "fov": fov},
              actual=state)
    return state


def _dark_environment(rec):
    env = rec.call("getActiveEnvironment", lux.getActiveEnvironment)
    if env is FAILED:
        return
    rec.call("env.setBrightness(0)", env.setBrightness, 0.0)
    rec.call("env.setBackgroundColor(black)", env.setBackgroundColor, (0, 0, 0))
    rec.call("env.setGroundShadows(False)", env.setGroundShadows, False)
    rec.call("env.setGroundReflections(False)", env.setGroundReflections, False)


def _reference_jewelry(rec):
    """A ring (axis Z, head at +Y) and a stone on top, imported like a user would (mm)."""
    ring = C.transform_object(C.torus(PREFIX + "_ring", major=9.0, minor=1.0), rotate=C.rot_x(90))
    stone = C.simple_brilliant(PREFIX + "_stone", radius=3.0, center=(0.0, 11.5, 0.0))
    opts = C.safe_import_options(geometry_units=1000.0)
    return C.import_objects(rec, "reference_jewelry", PREFIX + "_jewelry.obj", [ring, stone], opts)


def _apply_library_material(rec, node, keywords, label, explicit=None, link=False):
    """Apply the first library material that matches; returns the material name now on the node."""
    if explicit:
        entries = [explicit]
    else:  # keywords in priority order: first keyword with any hit wins
        entries = []
        for kw in keywords:
            entries = C.find_library_materials(rec, [kw])
            if entries:
                break
    for entry in entries:
        for candidate in C.material_name_candidates(entry):
            r = rec.call("%s.setMaterial(%s)" % (label, candidate), node.setMaterial, candidate, link=link)
            if r is not FAILED:
                mat = C.safe(node.getMaterial)
                rec.write("material_applied", label=label, requested=candidate, now=mat)
                return mat
    rec.check("%s: a library material matching %s could be applied" % (label, keywords), False)
    return None


def _is_light_type(dump):
    return bool(dump) and "light" in json.dumps(dump.get("root_type", "")).lower()


# ---------------------------------------------------------------- E0 inventory

def e0_inventory(cfg):
    rec = C.Recorder("E0_inventory")

    def names(obj):
        return sorted(n for n in dir(obj) if not n.startswith("_"))

    inv = {"lux": names(lux), "luxmath": names(luxmath), "classes": {}}
    for n in names(lux):
        obj = getattr(lux, n)
        if isinstance(obj, type):
            inv["classes"][n] = names(obj)
    inv["shader_types"] = {n: getattr(lux, n) for n in dir(lux) if n.startswith("SHADER_TYPE_")}
    inv["constants"] = {n: repr(getattr(lux, n)) for n in dir(lux) if n.isupper()}
    rec.write("inventory", **inv)

    base_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "baseline_2023_2.json")
    with open(base_path, encoding="utf-8") as f:
        base = json.load(f)
    funcs_now = {n for n in inv["lux"] if callable(getattr(lux, n)) and not isinstance(getattr(lux, n), type)}
    rec.write("diff_vs_2023_2",
              functions_missing=sorted(set(base["lux_functions"]) - funcs_now),
              functions_new=sorted(funcs_now - set(base["lux_functions"])),
              classes_missing=sorted(set(base["lux_classes"]) - set(inv["classes"])),
              classes_new=sorted(set(inv["classes"]) - set(base["lux_classes"])),
              methods_missing={k: sorted(set(v) - set(inv["classes"].get(k, [])))
                               for k, v in base["lux_classes"].items()},
              methods_new={k: sorted(set(inv["classes"][k]) - set(base["lux_classes"].get(k, [])))
                           for k in inv["classes"]},
              shader_types_new={k: v for k, v in inv["shader_types"].items()
                                if k not in base["shader_types"]})

    mvp_path = {
        "lux": ["getSceneTree", "importFile", "getImportOptions", "getMaterialGraph",
                "createSceneMaterial", "importMaterials", "getLibraryMaterials", "getCameraPosition",
                "getCameraLookAt", "getCameraUp", "getCameraFieldOfView", "getActiveEnvironment",
                "newEnvironment", "setActiveEnvironment", "getLightingPreset", "setLightingPreset",
                "getRenderOptions", "renderImage", "getInputDialog", "getBrowserDialog",
                "isUndoEnabled", "setUndoEnabled", "isSceneChanged", "getKeyShotFolder"],
        "SceneNode": ["applyTransform", "getTransform", "getBoundingBox", "setMaterial", "getMaterial",
                      "find", "delete", "hide", "show", "setName", "getSelected", "duplicate"],
        "MaterialGraph": ["getRoot", "newNode", "newEdge", "getNodesFromType"],
        "ShaderNode": ["getParameters", "getParameter", "getType"],
        "ShaderParameter": ["getValue", "setValue", "getName", "getType"],
    }
    for cls, members in mvp_path.items():
        have = inv["lux"] if cls == "lux" else inv["classes"].get(cls, [])
        for m in members:
            rec.check("present: %s.%s" % (cls, m), m in have)

    for kw in ("light", "primitive", "geometry", "layer", "pin", "undo", "plane", "create", "add",
               "metadata", "keyframe"):
        rec.write("keyword_hits", keyword=kw,
                  hits=[n for n in inv["lux"] if kw in n.lower()],
                  scenenode_hits=[n for n in inv["classes"].get("SceneNode", []) if kw in n.lower()])
    rec.write("planar_light_constants",
              hits={k: v for k, v in inv["shader_types"].items() if "planar" in (k + str(v)).lower()})

    for mod in ("zlib", "json", "struct", "subprocess", "tempfile", "pydoc", "hashlib", "threading"):
        rec.call("import " + mod, importlib.import_module, mod)
    rec.call("getLightingPresets", lux.getLightingPresets)
    rec.call("getKeyShotFolder(SCRIPTS)", lux.getKeyShotFolder, lux.FOLDER_SCRIPTS)
    rec.call("getSystemInfo", lux.getSystemInfo)
    rec.call("getImportOptions", lux.getImportOptions)
    rec.call("getRenderOptions().getDict()", lambda: lux.getRenderOptions().getDict())

    try:
        import pydoc
        text = pydoc.render_doc(lux, renderer=pydoc.plaintext)
        ver = "_".join(str(x) for x in C.safe(lux.getKeyShotVersion) or ["unknown"])
        path = os.path.join(C.results_dir(), "E0_help_lux_%s.txt" % ver)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        rec.note("full help(lux) written", path=path)
    except Exception as e:
        rec.note("help(lux) export failed: %s" % e)
    return rec.summary()


# ---------------------------------------------------------------- E1 light hosts via import

def e1_import_hosts(cfg):
    variant = cfg.get("e1_variant", {})
    rec = C.Recorder("E1_import_hosts", variant=variant)
    C.ensure_fresh_scene(rec, cfg)
    _reference_jewelry(rec)
    _set_camera(rec, PREFIX + "_cam", (0, 20, 90), (0, 5, 0), (0, 1, 0), 30)

    hosts = [
        C.rect(PREFIX + "_host_01", 5, 5),
        C.transform_object(C.rect(PREFIX + "_host_02", 8, 2), translate=(30, 0, 0)),
        C.transform_object(C.rect(PREFIX + "_host_03", 3, 6), rotate=C.rot_x(-90), translate=(0, 40, 10)),
    ]
    before = C.snapshot()
    opts = C.safe_import_options(**variant)
    t0 = time.perf_counter()
    new_nodes = C.import_objects(rec, "hosts", PREFIX + "_hosts.obj", hosts, opts)
    rec.write("timing", import_seconds=round(time.perf_counter() - t0, 3))
    after = C.snapshot()
    changes, new_ids = C.snapshot_diff_excluding_new_nodes(before, after)
    rec.write("scene_changes", changes=changes, new_node_ids=new_ids)

    camera_changes = [c for c in changes if c[0].startswith("/camera")]
    env_changes = [c for c in changes if c[0].startswith("/environment")]
    unit_changes = [c for c in changes if "unit" in c[0].lower()]
    existing_node_changes = [c for c in changes if c[0].startswith("/nodes")]
    rec.check("camera unchanged by import", not camera_changes, changes=camera_changes)
    rec.check("environment unchanged by import", not env_changes, changes=env_changes)
    rec.check("scene units unchanged by import", not unit_changes, changes=unit_changes)
    rec.check("existing nodes unchanged by import", not existing_node_changes, changes=existing_node_changes[:20])

    objs = C.objects_named(new_nodes, PREFIX + "_host_")
    rec.check("one object node per OBJ object (3)", len(objs) == 3,
              names=[C.safe(n.getName) for n in objs])
    groups = [C.node_info(n) for n in new_nodes if C.safe(n.isGroup) is True]
    rec.write("new_groups", groups=groups)
    rec.check("import created a containing group", bool(groups))
    new_materials = [c for c in changes if c[0].startswith("/scene/getSceneMaterials")]
    rec.write("materials_after_import", materials=C.safe(lux.getSceneMaterials),
              host_materials=[C.safe(n.getMaterial) for n in objs])

    by_name = {C.safe(n.getName): n for n in objs}
    ordered = [by_name.get(h[0]) for h in hosts]
    if all(ordered):
        actual = [_bbox(n) for n in ordered]
        fit = C.fit_import_mapping(hosts, actual)
        rec.write("import_mapping_fit", fit=fit, actual_bboxes=actual,
                  expected_obj_bboxes=[C.object_bbox(h) for h in hosts])
        rec.check("a consistent axis/scale mapping explains host placement",
                  fit["relative_error"] < 1e-3, fit=fit)

        dup = rec.call("duplicate host_01", ordered[0].duplicate)
        dup_nodes = [n for n in C.all_nodes() if str(C.safe(n.getID)) not in after["nodes"]]
        rec.write("duplicate_result", returned=dup, new_nodes=[C.node_info(n) for n in dup_nodes])
    return rec.summary()


# ---------------------------------------------------------------- E2 light materials

PARAM_TESTS = (
    # (keywords in name/display name, how to change the value)
    (("power", "watt", "lumen", "intensity", "lux"), "scale2"),
    (("color", "colour"), "orange"),
    (("camera",), "toggle"),
    (("reflection",), "toggle"),
    (("shadow",), "toggle"),
    (("front", "back", "side"), "toggle"),
    (("unit",), "next"),
)


def _changed_value(value, how):
    if how == "scale2" and isinstance(value, (int, float)) and not isinstance(value, bool):
        return value * 2 if value else 10.0
    if how == "orange":
        return (1.0, 0.5, 0.25)
    if how == "toggle" and isinstance(value, bool):
        return not value
    if how == "next" and isinstance(value, int) and not isinstance(value, bool):
        return value + 1
    return None


def _exercise_parameters(rec, material_name):
    graph = C.safe(lux.getMaterialGraph, material_name)
    if isinstance(graph, dict):
        return
    root = C.safe(graph.getRoot)
    params = C.safe(root.getParameters)
    if isinstance(params, dict):
        return
    for p in params:
        name = "%s/%s" % (C.safe(p.getName), C.safe(p.getDisplayName))
        for keywords, how in PARAM_TESTS:
            if not any(k in name.lower() for k in keywords):
                continue
            before = C.safe(p.getValue)
            new = _changed_value(before, how)
            if new is None:
                rec.write("param_skip", param=name, value=before, reason="no test value for type")
                break
            r = rec.call("setValue(%s)" % name, p.setValue, new)
            after = C.safe(p.getValue)
            rec.check("parameter settable and reads back: %s" % name,
                      r is not FAILED and C.to_jsonable(after) != C.to_jsonable(before),
                      before=before, requested=new, after=after)
            break


def _emission_check(rec, cfg, light_node, others):
    """Render with the light shown vs hidden; a clear difference means it emits light."""
    if not cfg.get("render"):
        return
    for n in others:
        C.safe(n.hide)
    lum = {}
    for state in ("hidden", "shown"):
        C.safe(light_node.hide if state == "hidden" else light_node.show)
        path = C.render_png(rec, "e2_emission_%s" % state, cfg, 160, 160, samples=16)
        if path:
            img = C.read_png(path)
            values = img.luminance_display()
            lum[state] = sum(values) / len(values)
    for n in others:
        C.safe(n.show)
    if len(lum) == 2:
        rec.check("light host emits light (mean luminance rises when shown)",
                  lum["shown"] > lum["hidden"] + 0.01, mean_luminance=lum)


def e2_light_materials(cfg):
    rec = C.Recorder("E2_light_materials")
    C.ensure_fresh_scene(rec, cfg)
    _dark_environment(rec)
    floor = C.transform_object(C.rect(PREFIX + "_floor", 200, 200), rotate=C.rot_x(-90), translate=(0, -20, 0))
    hosts = [C.transform_object(C.rect(PREFIX + "_L%d" % i, 10, 10), rotate=C.rot_x(90),
                                translate=(-30 + 30 * i, 20, 0)) for i in range(3)]
    nodes = C.import_objects(rec, "e2_geometry", PREFIX + "_e2.obj", [floor] + hosts)
    objs = {C.safe(n.getName): n for n in C.objects_named(nodes, PREFIX)}
    L = [objs.get(PREFIX + "_L%d" % i) for i in range(3)]
    if not all(L):
        rec.check("E2 hosts available", False, found=list(objs))
        return rec.summary()
    _set_camera(rec, PREFIX + "_cam", (0, 60, 120), (0, 0, 0), (0, 1, 0), 40)

    # Route (a): rebuild a scene material's graph around a light shader node.
    mname = PREFIX + "_routeA"
    rec.call("createSceneMaterial", lux.createSceneMaterial, mname)
    C.dump_material(rec, mname)
    graph = rec.call("getMaterialGraph(routeA)", lux.getMaterialGraph, mname)
    if graph is not FAILED:
        root = C.safe(graph.getRoot)
        light = rec.call("newNode(SHADER_TYPE_MESH_LIGHT)", graph.newNode, lux.SHADER_TYPE_MESH_LIGHT)
        if light is not FAILED and not isinstance(root, dict):
            params = [C.safe(p.getName) for p in (C.safe(root.getParameters) or [])
                      if not isinstance(p, str)]
            for param in ["surface", "material", "shader"] + [p for p in params if isinstance(p, str)]:
                r = rec.call("newEdge(light -> root, %s)" % param, graph.newEdge,
                             source=light, target=root, param=param)
                if r is not FAILED:
                    break
        rec.write("routeA_graph", nodes=[{"id": C.safe(n.getID), "type": C.safe(n.getType)}
                                         for n in (C.safe(graph.getNodes) or [])
                                         if not isinstance(n, str)])
    rec.call("L0.setMaterial(routeA)", L[0].setMaterial, mname, link=True)
    dump_a = C.dump_material(rec, C.safe(L[0].getMaterial))
    rec.check("route (a): scene material became a light", _is_light_type(dump_a),
              root_type=dump_a and dump_a.get("root_type"))

    # Route (c): KeyShot's bundled library light (route (b) uses cfg["kmp_path"]).
    if cfg.get("kmp_path"):
        rec.call("importMaterials(kmp)", lux.importMaterials, cfg["kmp_path"], folder="JLE_Spike")
    explicit = cfg.get("light_material")
    mat_c = _apply_library_material(rec, L[1], ["area light", "arealight", "light"], "L1", explicit=explicit)
    dump_c = C.dump_material(rec, mat_c) if mat_c else None
    rec.check("route (b/c): library light material applied", _is_light_type(dump_c),
              material=mat_c, root_type=dump_c and dump_c.get("root_type"))

    mat_c2 = _apply_library_material(rec, L[2], ["area light", "arealight", "light"], "L2", explicit=explicit)
    rec.check("link=False gives each host its own material", bool(mat_c and mat_c2 and mat_c != mat_c2),
              materials=[mat_c, mat_c2])

    if _is_light_type(dump_c):
        snapshot_l2 = C.dump_material(rec, mat_c2) if mat_c2 else None
        _exercise_parameters(rec, mat_c)
        after_l2 = C.dump_material(rec, mat_c2) if mat_c2 else None
        rec.check("editing one light's material leaves the other unchanged",
                  snapshot_l2 is not None and C.diff(snapshot_l2["parameters"], after_l2["parameters"]) == [],
                  changes=C.diff(snapshot_l2["parameters"], after_l2["parameters"]) if snapshot_l2 else None)
        _emission_check(rec, cfg, L[1], [L[0], L[2]])
    return rec.summary()


# ---------------------------------------------------------------- E3 placement maths

def e3_placement(cfg):
    rec = C.Recorder("E3_placement")
    C.ensure_fresh_scene(rec, cfg)
    _dark_environment(rec)
    R, D = 10.0, 40.0
    cam_intended = (0.0, 0.0, 60.0)

    # Target points on the sphere, 25-45 degrees off the view axis, so lights land off-frame.
    targets = []
    for k, (theta, phi) in enumerate([(25, 0), (35, 90), (45, 200), (30, 300), (40, 150)]):
        t, p = math.radians(theta), math.radians(phi)
        n = (math.sin(t) * math.cos(p), math.sin(t) * math.sin(p), math.cos(t))
        point = C.mul(n, R)
        light_pos, _ = C.mirror_light_position(point, n, cam_intended, D)
        targets.append({"k": k, "point": point, "normal": n, "light": light_pos})
    rec.write("targets", targets=targets)

    sphere = C.uv_sphere(PREFIX + "_sphere", radius=R)
    lights = [C.uv_sphere(PREFIX + "_e3L%d" % t["k"], radius=0.6, rings=8, segments=12, center=t["light"])
              for t in targets]
    nodes = C.import_objects(rec, "e3_geometry", PREFIX + "_e3.obj", [sphere] + lights)
    objs = {C.safe(n.getName): n for n in C.objects_named(nodes, PREFIX)}
    sph = objs.get(PREFIX + "_sphere")
    light_nodes = [objs.get(PREFIX + "_e3L%d" % t["k"]) for t in targets]
    if not sph or not all(light_nodes):
        rec.check("E3 geometry available", False, found=list(objs))
        return rec.summary()

    # The importer may rescale or re-orient OBJ coordinates (that is E1's question). A similarity
    # transform preserves mirror geometry, so map the camera and targets the same way instead.
    actual = [_bbox(n) for n in [sph] + light_nodes]
    fit = C.fit_import_mapping([sphere] + lights, actual)
    rec.write("import_mapping_fit", fit=fit)
    if not rec.check("OBJ placement explained by one axis/scale mapping", fit["relative_error"] < 1e-3, fit=fit):
        return rec.summary()
    fn, s = C.AXIS_MAPPINGS[fit["mapping"]], fit["scale"]
    T = lambda p: C.mul(fn(p), s)
    for t in targets:
        t["point_scene"] = T(t["point"])
    cam = _set_camera(rec, PREFIX + "_cam", T(cam_intended), T((0, 0, 0)), fn((0, 1, 0)), 30)
    cam_pos = cam["pos"] or T(cam_intended)

    _apply_library_material(rec, sph, ["chrome", "mirror", "polished metal", "polished"], "sphere")
    light_mat = cfg.get("light_material")
    for node in light_nodes:
        _apply_library_material(rec, node, ["area light", "arealight", "light"], "e3light", explicit=light_mat)

    if not cfg.get("render"):
        return rec.summary()
    for w, h in ((400, 400), (640, 360)):
        for t, node in zip(targets, light_nodes):
            for other in light_nodes:
                C.safe(other.hide if other is not node else other.show)
            path = C.render_png(rec, "e3_k%d_%dx%d" % (t["k"], w, h), cfg, w, h)
            if not path:
                continue
            blob = C.brightest_blob_centroid(C.read_png(path))
            pred = {axis: C.project_point(t["point_scene"], cam_pos, cam["look_at"] or T((0, 0, 0)),
                                          cam["up"] or fn((0, 1, 0)), cam["fov"] or 30, w, h, axis)
                    for axis in ("h", "v")}
            errors = {axis: (math.hypot(blob[0] - p[0], blob[1] - p[1]) / w if blob and p else None)
                      for axis, p in pred.items()}
            rec.write("highlight", k=t["k"], size=[w, h], blob=blob, predicted=pred, error_rel_width=errors)
            best = min(e for e in errors.values() if e is not None) if any(errors.values()) else None
            rec.check("highlight within 2%% of width of prediction (k=%d, %dx%d)" % (t["k"], w, h),
                      best is not None and best <= 0.02, errors=errors)
    for node in light_nodes:
        C.safe(node.show)

    # E3b: transform semantics on a rectangle host.
    tnodes = C.import_objects(rec, "e3b_rect", PREFIX + "_e3b.obj", [C.rect(PREFIX + "_T", 4, 2)])
    tn = (C.objects_named(tnodes, PREFIX + "_T") or [None])[0]
    if tn is not None:
        steps = [
            ("relative translate (5,0,0)", _identity().translate(_vec((5, 0, 0))), False),
            ("absolute translate (1,2,3)", _identity().translate(_vec((1, 2, 3))), True),
            ("relative rotate 90deg about X", _identity().rotateAroundAxis(_vec((1, 0, 0)), 90), False),
            ("relative scale 2", _identity().scale(2.0), False),
            ("absolute translate (10,0,0) after rotate+scale", _identity().translate(_vec((10, 0, 0))), True),
        ]
        for label, m, absolute in steps:
            before = _bbox(tn)
            r = rec.call("applyTransform: " + label, tn.applyTransform, m, absolute=absolute)
            after = _bbox(tn)
            rec.write("transform_step", step=label, absolute=absolute, ok=r is not FAILED,
                      bbox_before=before, bbox_after=after,
                      center_after=_center(after) if after else None,
                      extent_after=_extent(after) if after else None,
                      world_matrix=C.to_jsonable(C.safe(tn.getTransform, world=True)))
    return rec.summary()


# ---------------------------------------------------------------- E4 preview cost and stability

def e4_preview_cost(cfg):
    rec = C.Recorder("E4_preview_cost")
    if not cfg.get("render"):
        rec.note("render disabled in config")
        return rec.summary()
    C.ensure_fresh_scene(rec, cfg)
    nodes = _reference_jewelry(rec)
    objs = {C.safe(n.getName): n for n in C.objects_named(nodes, PREFIX)}
    if objs.get(PREFIX + "_ring"):
        _apply_library_material(rec, objs[PREFIX + "_ring"], ["gold", "polished"], "ring")
    if objs.get(PREFIX + "_stone"):
        _apply_library_material(rec, objs[PREFIX + "_stone"], ["diamond", "gem"], "stone")
    _set_camera(rec, PREFIX + "_cam", (0, 25, 60), (0, 6, 0), (0, 1, 0), 30)
    sizes = cfg.get("e4_sizes", [256, 384, 512])
    samples = cfg.get("e4_samples", [16, 32, 64, 128])
    repeats = int(cfg.get("e4_repeats", 3))
    for s in sizes:
        for n in samples:
            stats = []
            for r in range(repeats):
                t0 = time.perf_counter()
                path = C.render_png(rec, "e4_%d_%d_%d" % (s, n, r), cfg, s, s, samples=n)
                t_render = time.perf_counter() - t0
                if not path:
                    continue
                t1 = time.perf_counter()
                img = C.read_png(path)
                lum = img.luminance_display()
                t_decode = time.perf_counter() - t1
                mean = sum(lum) / len(lum)
                bright = sum(1 for v in lum if v > 0.9) / len(lum)
                stats.append({"render_s": t_render, "decode_s": t_decode, "mean": mean, "bright": bright})
            if stats:
                def cv(key):
                    vals = [x[key] for x in stats]
                    m = sum(vals) / len(vals)
                    sd = math.sqrt(sum((v - m) ** 2 for v in vals) / max(1, len(vals) - 1))
                    return sd / m if m else None
                rec.write("preview_cost", size=s, samples=n, runs=stats,
                          median_render_s=sorted(x["render_s"] for x in stats)[len(stats) // 2],
                          cv_mean_luminance=cv("mean"), cv_bright_fraction=cv("bright"))
    return rec.summary()


# ---------------------------------------------------------------- E6 + E13 delete / save / identity

def e6_persistence(cfg):
    rec = C.Recorder("E6_E13_persistence")
    C.ensure_fresh_scene(rec, cfg)
    nodes = C.import_objects(rec, "e6_hosts", PREFIX + "_e6.obj",
                             [C.rect(PREFIX + "_keep", 2, 2),
                              C.transform_object(C.rect(PREFIX + "_gone", 2, 2), translate=(5, 0, 0))])
    objs = {C.safe(n.getName): n for n in C.objects_named(nodes, PREFIX)}
    keep, gone = objs.get(PREFIX + "_keep"), objs.get(PREFIX + "_gone")
    if not keep or not gone:
        rec.check("E6 hosts available", False)
        return rec.summary()

    # Scene-only material deletion.
    mname = PREFIX + "_tmpmat"
    rec.call("createSceneMaterial(tmp)", lux.createSceneMaterial, mname)
    rec.call("keep.setMaterial(tmp)", keep.setMaterial, mname, link=True)
    rec.call("keep.setMaterial back to default", keep.setMaterial,
             C.safe(gone.getMaterial), link=False)
    rec.write("materials_before_delete", scene=C.safe(lux.getSceneMaterials))
    rec.call("deleteMaterial(tmp)", lux.deleteMaterial, mname)
    rec.write("materials_after_delete", scene=C.safe(lux.getSceneMaterials))

    # Node deletion is it soft?
    gone_id = C.safe(gone.getID)
    rec.call("gone.delete", gone.delete)
    root = lux.getSceneTree()
    rec.write("after_delete", is_deleted=C.safe(gone.isDeleted),
              deleted=[C.node_info(n) for n in (C.safe(root.getDeleted) or []) if not isinstance(n, str)])

    # Save: does saveFile(path) re-target the open scene?
    info_before = C.safe(lux.getSceneInfo)
    path = os.path.join(C.scratch_dir(), "%s_e6_%d.bip" % (PREFIX, int(time.time())))
    rec.call("saveFile(new path)", lux.saveFile, path)
    info_after = C.safe(lux.getSceneInfo)
    rec.write("save_retarget", before=info_before, after=info_after, saved_exists=os.path.exists(path))

    ids_before = {C.safe(n.getName): C.safe(n.getID) for n in C.all_nodes()}
    rec.call("openFile(saved)", lux.openFile, path, dontAsk=True)
    ids_after = {C.safe(n.getName): C.safe(n.getID) for n in C.all_nodes()}
    rec.write("ids_across_reload", before=ids_before, after=ids_after)
    rec.check("node IDs stable across save/reload",
              all(ids_after.get(k) == v for k, v in ids_before.items() if k in ids_after),
              before=ids_before, after=ids_after)
    rec.check("names survive save/reload", PREFIX + "_keep" in ids_after)
    deleted_after = C.safe(lux.getSceneTree().find, name=PREFIX + "_gone", deleted=True)
    rec.write("deleted_node_after_reload", found=[C.node_info(n) for n in (deleted_after or [])
                                                  if not isinstance(n, str)], original_id=gone_id)
    rec.note("MANUAL: after this run, press Undo repeatedly in KeyShot and note what reverts.")
    return rec.summary()


# ---------------------------------------------------------------- E7 non-destructive restore

def e7_restore(cfg):
    rec = C.Recorder("E7_restore")
    C.ensure_fresh_scene(rec, cfg)
    _reference_jewelry(rec)
    _set_camera(rec, PREFIX + "_camA", (0, 25, 60), (0, 6, 0), (0, 1, 0), 30)

    env = lux.getActiveEnvironment()
    original_name = C.safe(env.getName)
    keys = ("getBrightness", "getRotation", "getSize", "getHeight", "getBackgroundColor",
            "getLightingEnvironment", "getGroundShadows", "getGroundReflections")
    before_env = {k: C.to_jsonable(C.safe(getattr(env, k))) for k in keys if hasattr(env, k)}
    rec.call("newEnvironment(clone)", lux.newEnvironment, PREFIX + "_env", activate=True, clone=True)
    clone = lux.getActiveEnvironment()
    rec.write("clone_active", name=C.safe(clone.getName))
    rec.call("clone.setBrightness(0.1)", clone.setBrightness, 0.1)
    rec.call("clone.setBackgroundColor(white)", clone.setBackgroundColor, (1, 1, 1))
    rec.call("setActiveEnvironment(original)", lux.setActiveEnvironment, original_name)
    env2 = lux.getActiveEnvironment()
    after_env = {k: C.to_jsonable(C.safe(getattr(env2, k))) for k in keys if hasattr(env2, k)}
    rec.check("original environment active again", C.safe(env2.getName) == original_name)
    rec.check("original environment parameters untouched by edits to the clone",
              C.diff(before_env, after_env) == [], changes=C.diff(before_env, after_env))
    rec.call("removeEnvironment(clone)", lux.removeEnvironment, PREFIX + "_env")

    preset_before = C.safe(lux.getLightingPreset)
    opts_before = C.to_jsonable(C.safe(lambda: lux.getRenderOptions().getDict()))
    presets = C.safe(lux.getLightingPresets) or []
    target = cfg.get("lighting_preset_to_test")
    rec.write("lighting_presets", available=presets, current=preset_before)
    if target and target in (presets if isinstance(presets, (list, tuple)) else []):
        rec.call("setLightingPreset(%s)" % target, lux.setLightingPreset, target)
        rec.write("options_under_preset", options=C.to_jsonable(C.safe(lambda: lux.getRenderOptions().getDict())))
        rec.call("setLightingPreset(restore)", lux.setLightingPreset, preset_before)
        opts_after = C.to_jsonable(C.safe(lambda: lux.getRenderOptions().getDict()))
        rec.check("render options identical after preset round-trip", C.diff(opts_before, opts_after) == [],
                  changes=C.diff(opts_before, opts_after))

    if cfg.get("render"):
        before = C.to_jsonable(C.safe(lambda: lux.getRenderOptions().getDict()))
        C.render_png(rec, "e7_opts_isolation", cfg, 96, 96, samples=7)
        after = C.to_jsonable(C.safe(lambda: lux.getRenderOptions().getDict()))
        rec.check("passing opts to renderImage leaves scene render options unchanged",
                  C.diff(before, after) == [], changes=C.diff(before, after))

    # Unsaved camera edits across camera switches.
    _set_camera(rec, PREFIX + "_camB", (40, 10, 40), (0, 6, 0), (0, 1, 0), 30)
    rec.call("setCamera(A)", lux.setCamera, PREFIX + "_camA")
    dist = C.safe(lux.getCameraDistance)
    if isinstance(dist, (int, float)):
        rec.call("setCameraDistance(+10%)", lux.setCameraDistance, dist * 1.1)
    modified = C.vec3(C.safe(lux.getCameraPosition))
    unsaved = C.safe(lux.isCameraUnsaved)
    rec.call("setCamera(B)", lux.setCamera, PREFIX + "_camB")
    rec.call("setCamera(A) again", lux.setCamera, PREFIX + "_camA")
    back = C.vec3(C.safe(lux.getCameraPosition))
    rec.write("unsaved_camera", unsaved_flag=unsaved, modified_pos=modified, after_switch_back=back)
    rec.check("unsaved camera edit survives a camera switch",
              modified is not None and back is not None and C.length(C.sub(modified, back)) < 1e-6)
    return rec.summary()


EXPERIMENTS = {
    "E0": e0_inventory,
    "E1": e1_import_hosts,
    "E2": e2_light_materials,
    "E3": e3_placement,
    "E4": e4_preview_cost,
    "E6": e6_persistence,
    "E7": e7_restore,
}


def run(names, cfg=None):
    cfg = cfg or C.load_config()
    results = {}
    for name in names:
        for vi, variant in enumerate(cfg.get("variants", {}).get(name, [{}])):
            vcfg = dict(cfg)
            vcfg.update(variant)
            for rep in range(int(vcfg.get("repeats", 1))):
                key = "%s/v%d#%d" % (name, vi, rep)
                try:
                    results[key] = EXPERIMENTS[name](vcfg)
                except Exception as e:  # harness or precondition failure; keep going
                    results[key] = {"aborted": "%s: %s" % (type(e).__name__, e)}
                    print("[%s] aborted: %s" % (key, e))
                    if "Scene is not empty" in str(e):
                        return results
    return results
