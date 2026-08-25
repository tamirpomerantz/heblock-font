#!/usr/bin/env python3
"""Add circled / pill figures to Heblock.

Two ways to type them:

1. Unicode enclosed alphanumerics (always on):
   ①–⑳ ⓪  and filled ❶–❿ ⓿
2. Stylistic sets on ordinary digits:
   ss11  outline circle, stretching to a pill for 2+ digits (185)
   ss12  filled (knockout) circle, same pill behavior

Geometry uses O's height and stroke, drawn as true circles / stadiums so
single digits match the Vol. 2 badge and runs match the 185 capsule.
"""

from __future__ import annotations

from glyphsLib import GSFont
from glyphsLib.classes import GSComponent, GSFeature, GSGlyph, GSLayer, GSNode, GSPath

SOURCE = "sources/Heblock.glyphs"
KAPPA = 0.5519150244935106

DIGITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]

CIRCLED_UNI = {
    "zero": "24EA",
    "one": "2460",
    "two": "2461",
    "three": "2462",
    "four": "2463",
    "five": "2464",
    "six": "2465",
    "seven": "2466",
    "eight": "2467",
    "nine": "2468",
    "ten": "2469",
    "eleven": "246A",
    "twelve": "246B",
    "thirteen": "246C",
    "fourteen": "246D",
    "fifteen": "246E",
    "sixteen": "246F",
    "seventeen": "2470",
    "eighteen": "2471",
    "nineteen": "2472",
    "twenty": "2473",
}

BLACK_UNI = {
    "zero": "24FF",
    "one": "2776",
    "two": "2777",
    "three": "2778",
    "four": "2779",
    "five": "277A",
    "six": "277B",
    "seven": "277C",
    "eight": "277D",
    "nine": "277E",
    "ten": "277F",
}

TEENS = {
    "ten": ("one", "zero"),
    "eleven": ("one", "one"),
    "twelve": ("one", "two"),
    "thirteen": ("one", "three"),
    "fourteen": ("one", "four"),
    "fifteen": ("one", "five"),
    "sixteen": ("one", "six"),
    "seventeen": ("one", "seven"),
    "eighteen": ("one", "eight"),
    "nineteen": ("one", "nine"),
    "twenty": ("two", "zero"),
}


def ensure_glyph(font: GSFont, name: str) -> GSGlyph:
    existing = [g.name for g in font.glyphs]
    if name in existing:
        g = font.glyphs[name]
    else:
        g = GSGlyph(name)
        font.glyphs.append(g)
    for master in font.masters:
        ly = g.layers[master.id]
        if ly is None:
            ly = GSLayer()
            ly.layerId = master.id
            ly.associatedMasterId = master.id
            g.layers.append(ly)
    return g


def clear_layer(layer) -> None:
    layer.paths = []
    layer.components = []
    layer.anchors = []


def o_metrics(font: GSFont, master) -> dict[str, float]:
    ly = font.glyphs["O"].layers[master.id]
    paths = sorted(
        ly.paths,
        key=lambda p: p.bounds.size.width * p.bounds.size.height,
        reverse=True,
    )
    outer, inner = paths[0].bounds, paths[1].bounds
    stroke = ((outer.size.width - inner.size.width) + (outer.size.height - inner.size.height)) / 4
    return {
        "y0": outer.origin.y,
        "h": outer.size.height,
        "stroke": max(stroke, 18),
        "width_o": ly.width,
    }


def append_curve(path: GSPath, c1, c2, p) -> None:
    path.nodes.append(GSNode(c1, "offcurve"))
    path.nodes.append(GSNode(c2, "offcurve"))
    path.nodes.append(GSNode(p, "curve"))


def circle_path(cx: float, cy: float, r: float, clockwise: bool = False) -> GSPath:
    k = KAPPA * r
    pts = [
        (cx + r, cy),
        (cx, cy + r),
        (cx - r, cy),
        (cx, cy - r),
    ]
    if clockwise:
        pts = [pts[0], pts[3], pts[2], pts[1]]
        sign = -1
    else:
        sign = 1
    path = GSPath()
    path.closed = True
    path.nodes.append(GSNode(pts[0], "line"))
    for i in range(4):
        a = pts[i]
        b = pts[(i + 1) % 4]
        # tangent handles perpendicular to radius
        def handle(pt, toward_next):
            dx, dy = toward_next[0] - pt[0], toward_next[1] - pt[1]
            # For circle cubics the handles are axis-aligned
            return pt

        # axis-aligned kappa handles
        if abs(b[0] - a[0]) < 1:  # vertical move
            c1 = (a[0] + sign * (0 if clockwise else 0), a[1] + (k if b[1] > a[1] else -k) * (1 if not clockwise else 1))
        # do it explicitly per segment
        ax, ay = a
        bx, by = b
        if abs(ay - cy) < 1 and ax > cx:  # right -> next
            pass
    # Explicit 4 segments from east, CCW: E-N-W-S
    if not clockwise:
        path = GSPath()
        path.closed = True
        path.nodes.append(GSNode((cx + r, cy), "line"))
        append_curve(path, (cx + r, cy + k), (cx + k, cy + r), (cx, cy + r))
        append_curve(path, (cx - k, cy + r), (cx - r, cy + k), (cx - r, cy))
        append_curve(path, (cx - r, cy - k), (cx - k, cy - r), (cx, cy - r))
        append_curve(path, (cx + k, cy - r), (cx + r, cy - k), (cx + r, cy))
        return path
    path = GSPath()
    path.closed = True
    path.nodes.append(GSNode((cx + r, cy), "line"))
    append_curve(path, (cx + r, cy - k), (cx + k, cy - r), (cx, cy - r))
    append_curve(path, (cx - k, cy - r), (cx - r, cy - k), (cx - r, cy))
    append_curve(path, (cx - r, cy + k), (cx - k, cy + r), (cx, cy + r))
    append_curve(path, (cx + k, cy + r), (cx + r, cy + k), (cx + r, cy))
    return path


def circle_ring(cx: float, cy: float, r: float, stroke: float) -> list[GSPath]:
    return [circle_path(cx, cy, r, False), circle_path(cx, cy, r - stroke, True)]


def filled_circle(cx: float, cy: float, r: float) -> GSPath:
    return circle_path(cx, cy, r, False)


def left_cap_c(w: float, y0: float, h: float, stroke: float, overlap: float) -> GSPath:
    """C-shaped left stadium cap, open on the right, bars extend by overlap."""
    r = h / 2
    cy = y0 + r
    k_out = KAPPA * r
    r_in = r - stroke
    k_in = KAPPA * r_in
    y_top, y_bot = y0 + h, y0
    x1 = w + overlap
    path = GSPath()
    path.closed = True
    path.nodes.append(GSNode((x1, y_top - stroke), "line"))
    path.nodes.append(GSNode((r, y_top - stroke), "line"))
    append_curve(path, (r - k_in, y_top - stroke), (stroke, cy + k_in), (stroke, cy))
    append_curve(path, (stroke, cy - k_in), (r - k_in, y_bot + stroke), (r, y_bot + stroke))
    path.nodes.append(GSNode((x1, y_bot + stroke), "line"))
    path.nodes.append(GSNode((x1, y_bot), "line"))
    path.nodes.append(GSNode((r, y_bot), "line"))
    append_curve(path, (r - k_out, y_bot), (0, cy - k_out), (0, cy))
    append_curve(path, (0, cy + k_out), (r - k_out, y_top), (r, y_top))
    path.nodes.append(GSNode((x1, y_top), "line"))
    return path


def right_cap_c(w: float, y0: float, h: float, stroke: float, overlap: float) -> GSPath:
    """C-shaped right stadium cap, open on the left, bars extend by overlap."""
    r = h / 2
    cy = y0 + r
    cx = w - r
    k_out = KAPPA * r
    r_in = r - stroke
    k_in = KAPPA * r_in
    y_top, y_bot = y0 + h, y0
    x0 = -overlap
    path = GSPath()
    path.closed = True
    path.nodes.append(GSNode((x0, y_top), "line"))
    path.nodes.append(GSNode((cx, y_top), "line"))
    append_curve(path, (cx + k_out, y_top), (w, cy + k_out), (w, cy))
    append_curve(path, (w, cy - k_out), (cx + k_out, y_bot), (cx, y_bot))
    path.nodes.append(GSNode((x0, y_bot), "line"))
    path.nodes.append(GSNode((x0, y_bot + stroke), "line"))
    path.nodes.append(GSNode((cx, y_bot + stroke), "line"))
    append_curve(path, (cx + k_in, y_bot + stroke), (w - stroke, cy - k_in), (w - stroke, cy))
    append_curve(path, (w - stroke, cy + k_in), (cx + k_in, y_top - stroke), (cx, y_top - stroke))
    path.nodes.append(GSNode((x0, y_top - stroke), "line"))
    return path


def bar_pair(w: float, y0: float, h: float, stroke: float, overlap: float) -> list[GSPath]:
    x0, x1 = -overlap, w + overlap
    top = GSPath()
    top.closed = True
    yt = y0 + h - stroke
    for pt in ((x0, yt), (x1, yt), (x1, y0 + h), (x0, y0 + h)):
        top.nodes.append(GSNode(pt, "line"))
    bot = GSPath()
    bot.closed = True
    for pt in ((x0, y0), (x1, y0), (x1, y0 + stroke), (x0, y0 + stroke)):
        bot.nodes.append(GSNode(pt, "line"))
    return [top, bot]


def filled_left_d(w: float, y0: float, h: float, overlap: float) -> GSPath:
    r = h / 2
    cy = y0 + r
    k = KAPPA * r
    x1 = w + overlap
    path = GSPath()
    path.closed = True
    path.nodes.append(GSNode((x1, y0 + h), "line"))
    path.nodes.append(GSNode((r, y0 + h), "line"))
    append_curve(path, (r - k, y0 + h), (0, cy + k), (0, cy))
    append_curve(path, (0, cy - k), (r - k, y0), (r, y0))
    path.nodes.append(GSNode((x1, y0), "line"))
    return path


def filled_right_d(w: float, y0: float, h: float, overlap: float) -> GSPath:
    r = h / 2
    cy = y0 + r
    cx = w - r
    k = KAPPA * r
    x0 = -overlap
    path = GSPath()
    path.closed = True
    path.nodes.append(GSNode((x0, y0), "line"))
    path.nodes.append(GSNode((cx, y0), "line"))
    append_curve(path, (cx + k, y0), (w, cy - k), (w, cy))
    append_curve(path, (w, cy + k), (cx + k, y0 + h), (cx, y0 + h))
    path.nodes.append(GSNode((x0, y0 + h), "line"))
    return path


def filled_bar(w: float, y0: float, h: float, overlap: float) -> GSPath:
    x0, x1 = -overlap, w + overlap
    path = GSPath()
    path.closed = True
    for pt in ((x0, y0), (x1, y0), (x1, y0 + h), (x0, y0 + h)):
        path.nodes.append(GSNode(pt, "line"))
    return path


def optical_digit(font: GSFont, name: str, master):
    """Scaled-down digits use the next heavier master, uninterpolated.

    Thin → Regular, Regular → ExtraBlack. ExtraBlack/Black keeps ExtraBlack.
    """
    ordered = sorted(font.masters, key=lambda m: m.axes[0])
    idx = next(i for i, m in enumerate(ordered) if m.id == master.id)
    src_master = ordered[min(idx + 1, len(ordered) - 1)]
    return font.glyphs[name].layers[src_master.id]


def clone_digit_paths(src_layer, scale: float, dx: float, dy: float, reverse: bool) -> list[GSPath]:
    out = []
    for p in src_layer.paths:
        np = p.clone()
        np.applyTransform((scale, 0, 0, scale, dx, dy))
        if reverse:
            np.reverse()
        out.append(np)
    return out


def digit_placement(src_layer, box_x: float, box_w: float, y0: float, h: float, stroke: float, scale_factor: float = 0.72):
    b = src_layer.bounds
    inner_h = h - 2 * stroke
    target_h = inner_h * scale_factor
    scale = target_h / b.size.height if b.size.height else 1
    dw, dh = b.size.width * scale, b.size.height * scale
    dx = box_x + (box_w - dw) / 2 - b.origin.x * scale
    dy = y0 + (h - dh) / 2 - b.origin.y * scale
    return scale, dx, dy, dw


def set_layer_paths(layer, paths, width: float) -> None:
    clear_layer(layer)
    for p in paths:
        layer.paths.append(p)
    layer.width = width


def build_digits(font: GSFont) -> None:
    for master in font.masters:
        m = o_metrics(font, master)
        y0, h, stroke = m["y0"], m["h"], m["stroke"]
        r = h / 2
        cy = y0 + r
        sb = max(h * 0.16, 100)  # keep ①②③ from kissing
        cx = r + sb
        circle_w = h + 2 * sb
        pad = max(stroke * 1.25, 96)
        outline_overlap = min(max(stroke * 0.18, 4), 12)
        fill_overlap = 1.5
        join = pad * 0.85

        for name in DIGITS:
            src = optical_digit(font, name, master)
            scale, dx, dy, dw = digit_placement(
                src, sb + stroke, h - 2 * stroke, y0, h, stroke
            )

            ly = font.glyphs[f"{name}.circled"].layers[master.id]
            paths = circle_ring(cx, cy, r, stroke) + clone_digit_paths(src, scale, dx, dy, False)
            set_layer_paths(ly, paths, circle_w)

            ly = font.glyphs[f"{name}.blackCircled"].layers[master.id]
            paths = [filled_circle(cx, cy, r)] + clone_digit_paths(src, scale, dx, dy, True)
            set_layer_paths(ly, paths, circle_w)

            content_w = dw + pad
            start_w = r + content_w + join
            mid_w = join + dw + join
            end_w = join + content_w + r

            s_scale, s_dx, s_dy, _ = digit_placement(src, r - stroke * 0.1, content_w, y0, h, stroke)
            ly = font.glyphs[f"{name}.circled.start"].layers[master.id]
            paths = [left_cap_c(start_w, y0, h, stroke, outline_overlap)] + clone_digit_paths(
                src, s_scale, s_dx, s_dy, False
            )
            set_layer_paths(ly, paths, start_w)

            ly = font.glyphs[f"{name}.blackCircled.start"].layers[master.id]
            paths = [filled_left_d(start_w, y0, h, fill_overlap)] + clone_digit_paths(
                src, s_scale, s_dx, s_dy, True
            )
            set_layer_paths(ly, paths, start_w)

            m_scale, m_dx, m_dy, _ = digit_placement(src, join, dw, y0, h, stroke)
            ly = font.glyphs[f"{name}.circled.middle"].layers[master.id]
            paths = bar_pair(mid_w, y0, h, stroke, outline_overlap) + clone_digit_paths(
                src, m_scale, m_dx, m_dy, False
            )
            set_layer_paths(ly, paths, mid_w)

            ly = font.glyphs[f"{name}.blackCircled.middle"].layers[master.id]
            paths = [filled_bar(mid_w, y0, h, fill_overlap)] + clone_digit_paths(
                src, m_scale, m_dx, m_dy, True
            )
            set_layer_paths(ly, paths, mid_w)

            e_scale, e_dx, e_dy, _ = digit_placement(src, join, content_w, y0, h, stroke)
            ly = font.glyphs[f"{name}.circled.end"].layers[master.id]
            paths = [right_cap_c(end_w, y0, h, stroke, outline_overlap)] + clone_digit_paths(
                src, e_scale, e_dx, e_dy, False
            )
            set_layer_paths(ly, paths, end_w)

            ly = font.glyphs[f"{name}.blackCircled.end"].layers[master.id]
            paths = [filled_right_d(end_w, y0, h, fill_overlap)] + clone_digit_paths(
                src, e_scale, e_dx, e_dy, True
            )
            set_layer_paths(ly, paths, end_w)


def build_teens(font: GSFont, suffix: str) -> None:
    for name, (a, b) in TEENS.items():
        g = font.glyphs[f"{name}{suffix}"]
        for master in font.masters:
            ly = g.layers[master.id]
            clear_layer(ly)
            left = font.glyphs[f"{a}{suffix}.start"].layers[master.id]
            right = font.glyphs[f"{b}{suffix}.end"].layers[master.id]
            ly.components.append(GSComponent(f"{a}{suffix}.start", (0, 0)))
            ly.components.append(GSComponent(f"{b}{suffix}.end", (left.width, 0)))
            ly.width = left.width + right.width


def write_feature(font: GSFont, tag: str, title: str, suffix: str) -> None:
    circ = " ".join(f"{n}{suffix}" for n in DIGITS)
    start = " ".join(f"{n}{suffix}.start" for n in DIGITS)
    mid = " ".join(f"{n}{suffix}.middle" for n in DIGITS)
    end = " ".join(f"{n}{suffix}.end" for n in DIGITS)
    subs = "\n".join(f"    sub {n} by {n}{suffix};" for n in DIGITS)
    code = f"""featureNames {{
    name "{title}";
}};
lookup {tag}_SUB {{
{subs}
}} {tag}_SUB;
@circ_{tag} = [{circ}];
@start_{tag} = [{start}];
@mid_{tag} = [{mid}];
@end_{tag} = [{end}];
lookup {tag}_START {{
    ignore sub [@circ_{tag} @start_{tag} @mid_{tag}] @circ_{tag}';
    sub @circ_{tag}' @circ_{tag} by @start_{tag};
}} {tag}_START;
lookup {tag}_END {{
    ignore sub @circ_{tag}' @circ_{tag};
    sub [@start_{tag} @mid_{tag} @circ_{tag}] @circ_{tag}' by @end_{tag};
}} {tag}_END;
lookup {tag}_MID {{
    sub [@start_{tag} @mid_{tag}] @circ_{tag}' [@end_{tag} @mid_{tag} @circ_{tag}] by @mid_{tag};
}} {tag}_MID;
"""
    existing = [f.name for f in font.features]
    if tag in existing:
        font.features[tag].code = code
        font.features[tag].automatic = False
    else:
        feat = GSFeature(tag)
        feat.automatic = False
        feat.code = code
        font.features.append(feat)


def prepare_glyphs(font: GSFont) -> None:
    for name in DIGITS:
        for suffix, uni in ((".circled", CIRCLED_UNI[name]), (".blackCircled", BLACK_UNI[name])):
            g = ensure_glyph(font, name + suffix)
            g.unicode = uni
            g.category = "Number"
            g.subCategory = "Decimal Digit"
        for suffix in (
            ".circled.start",
            ".circled.middle",
            ".circled.end",
            ".blackCircled.start",
            ".blackCircled.middle",
            ".blackCircled.end",
        ):
            g = ensure_glyph(font, name + suffix)
            g.unicode = None
            g.category = "Number"
            g.export = True
    for name in TEENS:
        g = ensure_glyph(font, name + ".circled")
        g.unicode = CIRCLED_UNI[name]
        g.category = "Number"
        if name in BLACK_UNI:
            g = ensure_glyph(font, name + ".blackCircled")
            g.unicode = BLACK_UNI[name]
            g.category = "Number"
    # ten is in BLACK_UNI; 11-20 black exist as U+24EB–24F4 but skip for now


def main() -> None:
    font = GSFont(SOURCE)
    prepare_glyphs(font)
    build_digits(font)
    build_teens(font, ".circled")
    # ten filled (❶… already 1-9; ❿ is ten)
    build_teens_ten_only = True
    g = ensure_glyph(font, "ten.blackCircled")
    g.unicode = BLACK_UNI["ten"]
    g.category = "Number"
    for master in font.masters:
        ly = g.layers[master.id]
        clear_layer(ly)
        left = font.glyphs["one.blackCircled.start"].layers[master.id]
        right = font.glyphs["zero.blackCircled.end"].layers[master.id]
        ly.components.append(GSComponent("one.blackCircled.start", (0, 0)))
        ly.components.append(GSComponent("zero.blackCircled.end", (left.width, 0)))
        ly.width = left.width + right.width

    write_feature(font, "ss11", "Circled figures", ".circled")
    write_feature(font, "ss12", "Negative circled figures", ".blackCircled")
    font.save(SOURCE)
    print("Saved", SOURCE)
    print("ss11: type digits with Circled figures on → 185 becomes a pill")
    print("ss12: filled knockout badges")
    print("Unicode: ①-⑳ ⓪ ❶-❿ ⓿")


if __name__ == "__main__":
    main()
