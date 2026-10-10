"""Unit tests for the KeyShot-independent parts of the spike harness (plain CPython)."""

import math
import os
import struct
import sys
import tempfile
import unittest
import zlib

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from jle_spike import common as C  # noqa: E402


def encode_png(width, height, channels, rows, filters, bitdepth=8):
    """Tiny PNG encoder used only to test the decoder, applying the given filter per row."""
    colortype = {1: 0, 2: 4, 3: 2, 4: 6}[channels]
    bpp = channels * bitdepth // 8
    stride = width * bpp
    raw = bytearray()
    prev = bytearray(stride)
    for y, row in enumerate(rows):
        if bitdepth == 8:
            line = bytearray(row)
        else:
            line = bytearray(struct.pack(">%dH" % len(row), *row))
        f = filters[y % len(filters)]
        out = bytearray(stride)
        for x in range(stride):
            left = line[x - bpp] if x >= bpp else 0
            up = prev[x]
            ul = prev[x - bpp] if x >= bpp else 0
            pred = [0, left, up, (left + up) >> 1, C._paeth(left, up, ul)][f]
            out[x] = (line[x] - pred) & 255
        raw.append(f)
        raw += out
        prev = line

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, bitdepth, colortype, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(raw)))
            + chunk(b"IEND", b""))


class PngTests(unittest.TestCase):
    def _roundtrip(self, channels, bitdepth):
        w, h = 7, 6
        maxv = 255 if bitdepth == 8 else 65535
        rows = [[(x * 37 + y * 91 + c * 13) % (maxv + 1) for x in range(w) for c in range(channels)]
                for y in range(h)]
        data = encode_png(w, h, channels, rows, filters=[0, 1, 2, 3, 4, 4], bitdepth=bitdepth)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(data)
            path = f.name
        try:
            img = C.read_png(path)
        finally:
            os.unlink(path)
        self.assertEqual((img.width, img.height, img.channels), (w, h, channels))
        flat = [v / maxv for row in rows for v in row]
        for a, b in zip(img.samples, flat):
            self.assertAlmostEqual(a, b, places=6)

    def test_rgb8_all_filters(self):
        self._roundtrip(3, 8)

    def test_rgba8(self):
        self._roundtrip(4, 8)

    def test_rgb16(self):
        self._roundtrip(3, 16)

    def test_blob_centroid(self):
        w, h = 20, 10
        rows = [[0] * (w * 3) for _ in range(h)]
        for y in (4, 5):
            for x in (15, 16):
                rows[y][x * 3:x * 3 + 3] = [255, 255, 255]
        data = encode_png(w, h, 3, rows, filters=[0])
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(data)
            path = f.name
        try:
            cx, cy, n, _ = C.brightest_blob_centroid(C.read_png(path))
        finally:
            os.unlink(path)
        self.assertEqual(n, 4)
        self.assertAlmostEqual(cx, 16.0)
        self.assertAlmostEqual(cy, 5.0)


class GeometryTests(unittest.TestCase):
    def _assert_outward(self, obj, center):
        name, verts, faces, normals = obj
        for face in faces:
            pts = [verts[i] for i in face]
            # skip degenerate pole faces
            uniq = {tuple(round(c, 9) for c in p) for p in pts}
            if len(uniq) < 3:
                continue
            a, b, c = pts[0], pts[1], pts[2]
            n = C.cross(C.sub(b, a), C.sub(c, a))
            if C.length(n) < 1e-12:
                a, b, c = pts[0], pts[2], pts[3]
                n = C.cross(C.sub(b, a), C.sub(c, a))
            centroid = tuple(sum(p[k] for p in pts) / len(pts) for k in range(3))
            self.assertGreater(C.dot(n, C.sub(centroid, center)), 0, "inward face in " + name)
            self.assertGreater(C.dot(n, normals[face[0]]), 0, "normal disagrees with winding in " + name)

    def test_brilliant_is_outward(self):
        self._assert_outward(C.simple_brilliant("g"), (0, 0, 0))

    def test_sphere_is_outward(self):
        self._assert_outward(C.uv_sphere("s", rings=8, segments=12), (0, 0, 0))

    def test_torus_faces_agree_with_normals(self):
        name, verts, faces, normals = C.torus("t", segments=16, sides=8)
        for face in faces:
            a, b, c = (verts[i] for i in face[:3])
            n = C.cross(C.sub(b, a), C.sub(c, a))
            self.assertGreater(C.dot(n, normals[face[0]]), 0)

    def test_obj_text_indices(self):
        txt = C.obj_text([C.rect("A"), C.rect("B")])
        lines = txt.splitlines()
        self.assertIn("o A", lines)
        self.assertIn("o B", lines)
        self.assertIn("f 5//5 6//6 7//7 8//8", lines)

    def test_brilliant_bbox(self):
        (x0, y0, z0), (x1, y1, z1) = C.object_bbox(C.simple_brilliant("g", radius=2.0))
        self.assertAlmostEqual(x1, 2.0, places=6)
        self.assertLess(y0, 0)
        self.assertGreater(y1, 0)


class MathTests(unittest.TestCase):
    def test_mirror_placement_reflects(self):
        cam = (0.0, 0.0, 10.0)
        for p in [(0, 0, 1), (0.6, 0, 0.8), (0, 0.6, 0.8), (-0.48, 0.36, 0.8)]:
            n = C.normalize(p)
            light, i = C.mirror_light_position(p, n, cam, 5.0)
            o = C.normalize(C.sub(cam, p))
            # incoming and outgoing directions make equal angles with the normal
            self.assertAlmostEqual(C.dot(i, n), C.dot(o, n), places=9)
            self.assertAlmostEqual(C.length(C.sub(light, p)), 5.0, places=9)

    def test_projection_center_and_edges(self):
        cam, look, up = (0, 0, 10), (0, 0, 0), (0, 1, 0)
        x, y = C.project_point((0, 0, 0), cam, look, up, 40, 400, 200, "h")
        self.assertAlmostEqual(x, 200)
        self.assertAlmostEqual(y, 100)
        half = 10 * math.tan(math.radians(20))
        x, _ = C.project_point((half, 0, 0), cam, look, up, 40, 400, 200, "h")
        self.assertAlmostEqual(x, 400)
        _, y = C.project_point((0, half, 0), cam, look, up, 40, 400, 200, "v")
        self.assertAlmostEqual(y, 0)

    def test_angular_direction(self):
        d = C.angular_direction((0, 0, 1), (0, 1, 0), 0, 0)
        self.assertAlmostEqual(d[2], 1)
        d = C.angular_direction((0, 0, 1), (0, 1, 0), 90, 0)  # top of frame
        self.assertAlmostEqual(d[1], 1)
        d = C.angular_direction((0, 0, 1), (0, 1, 0), 90, 90)  # screen right
        r = C.normalize(C.cross((0, 0, -1), (0, 1, 0)))  # camera looks along -z
        self.assertAlmostEqual(C.dot(d, r), 1)

    def test_diff(self):
        a = {"x": 1.0, "y": [1, 2], "z": {"k": "v"}}
        b = {"x": 1.0 + 1e-9, "y": [1, 3], "z": {"k": "v"}, "new": 1}
        changes = C.diff(a, b)
        self.assertEqual({c[0] for c in changes}, {"/y[1]", "/new"})


if __name__ == "__main__":
    unittest.main()
