"""Glyphs-compatible RoundCorner filter for ufo2ft / fontmake.

Glyphs `Filter = RoundCorner;24;1;` becomes a ufo2ft filter named
RoundCorner with args (24, 1). Positive radius rounds outward corners,
negative rounds inward. The second argument is visual correction.

This matches Glyphs export: round the final outline (after overlap
removal), including line-to-curve corners, not only polylines.
"""

from __future__ import annotations

import logging
from math import atan2, degrees, hypot, pi, sin, tan

from fontTools.misc.bezierTools import splitCubicAtT, splitQuadraticAtT
from ufo2ft.filters import BaseFilter, BaseIFilter
from ufoLib2.objects import Contour, Point

log = logging.getLogger(__name__)

MIN_TURN_DEG = 6.0
MAX_TURN_DEG = 176.0


def _copy_point(p: Point) -> Point:
    return Point(p.x, p.y, type=p.type, smooth=p.smooth, name=p.name)


def _copy_contour(contour: Contour) -> Contour:
    return Contour(points=[_copy_point(p) for p in contour])


def _area(points) -> float:
    n = len(points)
    if n < 3:
        return 0.0
    acc = 0.0
    for i, p in enumerate(points):
        q = points[(i + 1) % n]
        acc += p.x * q.y - q.x * p.y
    return acc * 0.5


def _vsub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def _vadd(a, b):
    return (a[0] + b[0], a[1] + b[1])


def _vmul(a, s):
    return (a[0] * s, a[1] * s)


def _vlen(a):
    return hypot(a[0], a[1])


def _vnorm(a):
    n = _vlen(a)
    if n < 1e-9:
        return (0.0, 0.0)
    return (a[0] / n, a[1] / n)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def _cross(a, b):
    return a[0] * b[1] - a[1] * b[0]


def _xy(p):
    return (float(p[0]), float(p[1])) if not hasattr(p, "x") else (float(p.x), float(p.y))


def _sample_length(points, steps=12) -> float:
    total = 0.0
    prev = points[0]
    for i in range(1, steps + 1):
        t = i / steps
        if len(points) == 3:
            a, b, c = points
            u = 1 - t
            cur = (u * u * a[0] + 2 * u * t * b[0] + t * t * c[0],
                   u * u * a[1] + 2 * u * t * b[1] + t * t * c[1])
        else:
            a, b, c, d = points
            u = 1 - t
            cur = (
                u * u * u * a[0] + 3 * u * u * t * b[0] + 3 * u * t * t * c[0] + t * t * t * d[0],
                u * u * u * a[1] + 3 * u * u * t * b[1] + 3 * u * t * t * c[1] + t * t * t * d[1],
            )
        total += hypot(cur[0] - prev[0], cur[1] - prev[1])
        prev = cur
    return total


def _length_to_t(points, t) -> float:
    if t <= 0:
        return 0.0
    if t >= 1:
        return _sample_length(points)
    if len(points) == 3:
        segs = splitQuadraticAtT(points[0], points[1], points[2], t)
    else:
        segs = splitCubicAtT(points[0], points[1], points[2], points[3], t)
    return _sample_length(segs[0])


def _t_at_distance(points, distance, from_start=True) -> float:
    total = _sample_length(points)
    if total < 1e-6:
        return 0.0 if from_start else 1.0
    target = distance if from_start else max(0.0, total - distance)
    target = min(max(target, 0.0), total)
    lo, hi = 0.0, 1.0
    for _ in range(18):
        mid = (lo + hi) / 2.0
        if _length_to_t(points, mid) < target:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2.0


class Segment:
    __slots__ = ("p0", "offs", "p1")

    def __init__(self, p0, offs, p1):
        self.p0 = p0
        self.offs = offs
        self.p1 = p1

    @property
    def kind(self) -> str:
        n = len(self.offs)
        if n == 0:
            return "line"
        if n == 1:
            return "qcurve"
        return "curve"

    def points(self):
        return [_xy(self.p0), *(_xy(o) for o in self.offs), _xy(self.p1)]

    def length(self) -> float:
        pts = self.points()
        if len(pts) == 2:
            return hypot(pts[1][0] - pts[0][0], pts[1][1] - pts[0][1])
        return _sample_length(pts)

    def tangent_start(self):
        pts = self.points()
        return _vnorm(_vsub(pts[1], pts[0]))

    def tangent_end(self):
        pts = self.points()
        return _vnorm(_vsub(pts[-1], pts[-2]))

    def cut_end(self, dist: float) -> tuple[tuple[float, float], "Segment"]:
        pts = self.points()
        if len(pts) == 2:
            direction = _vnorm(_vsub(pts[1], pts[0]))
            new_end = _vsub(pts[1], _vmul(direction, dist))
            end = Point(new_end[0], new_end[1], type="line")
            return new_end, Segment(self.p0, [], end)
        t = _t_at_distance(pts, dist, from_start=False)
        if len(pts) == 3:
            left, _right = splitQuadraticAtT(pts[0], pts[1], pts[2], t)
            end = Point(left[2][0], left[2][1], type="qcurve")
            off = Point(left[1][0], left[1][1], type=None)
            return (left[2][0], left[2][1]), Segment(self.p0, [off], end)
        left, _right = splitCubicAtT(pts[0], pts[1], pts[2], pts[3], t)
        end = Point(left[3][0], left[3][1], type="curve")
        offs = [Point(left[1][0], left[1][1], type=None), Point(left[2][0], left[2][1], type=None)]
        return (left[3][0], left[3][1]), Segment(self.p0, offs, end)

    def cut_start(self, dist: float) -> tuple[tuple[float, float], "Segment"]:
        pts = self.points()
        if len(pts) == 2:
            direction = _vnorm(_vsub(pts[1], pts[0]))
            new_start = _vadd(pts[0], _vmul(direction, dist))
            start = Point(new_start[0], new_start[1], type=self.p0.type or "line")
            return new_start, Segment(start, [], self.p1)
        t = _t_at_distance(pts, dist, from_start=True)
        if len(pts) == 3:
            _left, right = splitQuadraticAtT(pts[0], pts[1], pts[2], t)
            start = Point(right[0][0], right[0][1], type="qcurve")
            off = Point(right[1][0], right[1][1], type=None)
            return (right[0][0], right[0][1]), Segment(start, [off], self.p1)
        _left, right = splitCubicAtT(pts[0], pts[1], pts[2], pts[3], t)
        start = Point(right[0][0], right[0][1], type="curve")
        offs = [Point(right[1][0], right[1][1], type=None), Point(right[2][0], right[2][1], type=None)]
        return (right[0][0], right[0][1]), Segment(start, offs, self.p1)


def _contour_segments(contour: Contour) -> list[Segment]:
    pts = list(contour)
    on_idx = [i for i, p in enumerate(pts) if p.type is not None]
    if len(on_idx) < 2:
        return []
    segs = []
    for k, i in enumerate(on_idx):
        j = on_idx[(k + 1) % len(on_idx)]
        if j > i:
            offs = list(pts[i + 1 : j])
        else:
            offs = list(pts[i + 1 :]) + list(pts[:j])
        start, end = pts[i], pts[j]
        if len(offs) <= 1:
            segs.append(Segment(start, offs, end))
            continue
        # TrueType implied on-curves between consecutive off-curves.
        prev = start
        for n, off in enumerate(offs):
            if n < len(offs) - 1:
                nxt = offs[n + 1]
                implied = Point((off.x + nxt.x) / 2.0, (off.y + nxt.y) / 2.0, type="qcurve")
                segs.append(Segment(prev, [off], implied))
                prev = implied
            else:
                segs.append(Segment(prev, [off], end))
    return segs


def _segments_to_contour(segments: list[Segment]) -> Contour:
    if not segments:
        return Contour(points=[])
    points = [_copy_point(segments[0].p0)]
    if points[0].type is None:
        points[0].type = "line"
    for seg in segments:
        for off in seg.offs:
            points.append(_copy_point(off))
        end = _copy_point(seg.p1)
        if end.type is None:
            end.type = "qcurve" if seg.offs else "line"
        points.append(end)
    # Closed contour: last point is the same as first; drop duplicate close.
    if len(points) > 1:
        a, b = points[0], points[-1]
        if abs(a.x - b.x) < 0.05 and abs(a.y - b.y) < 0.05:
            points[0].type = b.type or points[0].type
            points.pop()
    return Contour(points=points)


def _intersect(p, d1, q, d2):
    det = _cross(d1, d2)
    if abs(det) < 1e-8:
        return None
    s = _cross(_vsub(q, p), d2) / det
    return _vadd(p, _vmul(d1, s))


def _cut_both(seg: Segment, d_start: float, d_end: float) -> Segment:
    out = seg
    if d_start > 0.5:
        _, out = out.cut_start(d_start)
    if d_end > 0.5:
        _, out = out.cut_end(d_end)
    return out


def round_contour(contour: Contour, radius: float, visual: bool, as_quadratic: bool) -> Contour:
    segs = _contour_segments(contour)
    if len(segs) < 3 or radius == 0:
        return _copy_contour(contour)
    area = _area(list(contour))
    if area == 0:
        return _copy_contour(contour)

    n = len(segs)
    d_start = [0.0] * n
    d_end = [0.0] * n
    fillets: list[Segment | None] = [None] * n

    for i, incoming in enumerate(segs):
        outgoing = segs[(i + 1) % n]
        corner = incoming.p1
        if getattr(corner, "smooth", False):
            continue
        in_dir = incoming.tangent_end()
        out_dir = outgoing.tangent_start()
        if _vlen(in_dir) < 0.5 or _vlen(out_dir) < 0.5:
            continue
        cr = _cross(in_dir, out_dir)
        dot = max(-1.0, min(1.0, _dot(in_dir, out_dir)))
        turn = atan2(cr, dot)
        turn_deg = abs(degrees(turn))
        if turn_deg < MIN_TURN_DEG or turn_deg > MAX_TURN_DEG:
            continue

        is_convex = area * cr > 0
        if radius > 0 and not is_convex:
            continue
        if radius < 0 and is_convex:
            continue

        half = abs(turn) / 2.0
        tval = tan(half)
        if tval < 1e-6:
            continue
        r = abs(radius)
        if visual:
            # Glyphs visual correction: smaller radius on acute, larger on obtuse.
            r *= sin(half) / sin(pi / 4.0)
        cut = r * tval
        cut = min(cut, 0.49 * incoming.length(), 0.49 * outgoing.length())
        if cut < 0.51:
            continue

        t1, _ = incoming.cut_end(cut)
        t2, _ = outgoing.cut_start(cut)
        ctrl = _intersect(t1, in_dir, t2, (-out_dir[0], -out_dir[1])) or _xy(corner)

        if as_quadratic:
            fillet = Segment(
                Point(t1[0], t1[1], type="line"),
                [Point(ctrl[0], ctrl[1], type=None)],
                Point(t2[0], t2[1], type="qcurve"),
            )
        else:
            r_eff = cut / tval
            handle = (4.0 / 3.0) * tan(abs(turn) / 4.0) * r_eff
            h1 = _vadd(t1, _vmul(in_dir, handle))
            h2 = _vsub(t2, _vmul(out_dir, handle))
            fillet = Segment(
                Point(t1[0], t1[1], type="line"),
                [Point(h1[0], h1[1], type=None), Point(h2[0], h2[1], type=None)],
                Point(t2[0], t2[1], type="curve"),
            )

        d_end[i] = cut
        d_start[(i + 1) % n] = cut
        fillets[i] = fillet

    rebuilt = []
    for i, seg in enumerate(segs):
        rebuilt.append(_cut_both(seg, d_start[i], d_end[i]))
        if fillets[i] is not None:
            rebuilt.append(fillets[i])
    return _segments_to_contour(rebuilt)


def _parse_args(*args, **kwargs) -> tuple[float, bool]:
    if args:
        radius = float(args[0])
    else:
        radius = float(kwargs.get("radius", 0) or 0)
    visual = True
    if len(args) > 1:
        visual = bool(int(float(args[1])))
    elif "visualCorrection" in kwargs:
        visual = bool(kwargs["visualCorrection"])
    return radius, visual


class RoundCornerFilter(BaseFilter):
    _args = ()
    _kwargs = {}
    _pre = False

    def __init__(self, *args, **kwargs):
        radius, visual = _parse_args(*args, **kwargs)
        kwargs.pop("radius", None)
        kwargs.pop("visualCorrection", None)
        kwargs.pop("pre", None)
        super().__init__(
            include=kwargs.get("include"),
            exclude=kwargs.get("exclude"),
            pre=False,
        )
        self.options.radius = radius
        self.options.visualCorrection = visual

    def filter(self, glyph) -> bool:
        radius = self.options.radius
        if radius == 0 or not glyph.contours:
            return False

        original = [_copy_contour(c) for c in glyph.contours]
        orig_area = sum(abs(_area(c)) for c in original)
        as_quadratic = True
        rounded = [
            round_contour(c, radius, self.options.visualCorrection, as_quadratic)
            for c in glyph.contours
        ]
        new_area = sum(abs(_area(c)) for c in rounded)

        if orig_area > 1 and (new_area < orig_area * 0.25 or new_area > orig_area * 1.5):
            log.warning(
                "RoundCorner skipped %s (area %.0f -> %.0f)",
                getattr(glyph, "name", "?"),
                orig_area,
                new_area,
            )
            return False
        if new_area < 1:
            return False

        glyph.clearContours()
        for contour in rounded:
            glyph.contours.append(contour)
        return True


class RoundCornerIFilter(BaseIFilter):
    _args = ()
    _kwargs = {}
    _pre = False

    def __init__(self, *args, **kwargs):
        radius, visual = _parse_args(*args, **kwargs)
        kwargs.pop("radius", None)
        kwargs.pop("visualCorrection", None)
        kwargs.pop("pre", None)
        super().__init__(
            include=kwargs.get("include"),
            exclude=kwargs.get("exclude"),
            pre=False,
        )
        self.options.radius = radius
        self._delegate = RoundCornerFilter(radius, int(visual))

    def filter(self, glyphName: str, glyphs: list) -> bool:
        modified = False
        for glyph in glyphs:
            if glyph is not None and self._delegate.filter(glyph):
                modified = True
        return modified
