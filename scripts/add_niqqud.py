#!/usr/bin/env python3
"""Build Heblock niqqud from existing square/bar geometry and attach GPOS anchors.

Design notes
------------
Heblock's period and i-dot are squares; Hebrew letters are blocky. Niqqud is
drawn as squares and rectangles in that language (not the round Latin
dotaccent). RoundCorner at export turns those squares into the same
squircles as the period.

Anchor model follows Glyphs / Google Fonts Hebrew practice so several marks
can sit on one letter at once:

  bottom      below vowels, sheva, hatafim, qubuts, lower dot
  bottomleft  meteg (beside a vowel, not on top of it)
  center      dagesh / mapiq
  topleft     holam, holam haser, sin dot
  top         rafe, upper dot
  topright    shin dot

Marks are combining (width 0). Each also has a matching mkmk outgoing
anchor so a second mark can stack if needed.
"""

from __future__ import annotations

from glyphsLib import GSFont
from glyphsLib.classes import GSAnchor, GSGlyph, GSLayer, GSNode, GSPath

SOURCE = "sources/Heblock.glyphs"
HEBREW_TOP = 555.0

LETTERS = [
    "alef-hb",
    "bet-hb",
    "gimel-hb",
    "dalet-hb",
    "he-hb",
    "vav-hb",
    "zayin-hb",
    "het-hb",
    "tet-hb",
    "yod-hb",
    "kafFinal-hb",
    "kaf-hb",
    "lamed-hb",
    "memFinal-hb",
    "mem-hb",
    "nunFinal-hb",
    "nun-hb",
    "samekh-hb",
    "ayin-hb",
    "peFinal-hb",
    "pe-hb",
    "tsadiFinal-hb",
    "tsadi-hb",
    "qof-hb",
    "resh-hb",
    "shin-hb",
    "tav-hb",
]

# Dagesh / mapiq at Regular, x scaled by width on other masters. y is stable
# because Hebrew body height is 555 in every master.
REG_DAGESH = {
    "alef-hb": (378, 300),
    "bet-hb": (220, 310),
    "gimel-hb": (200, 300),
    "dalet-hb": (180, 300),
    "he-hb": (290, 300),
    "vav-hb": (169, 300),
    "zayin-hb": (171, 280),
    "het-hb": (300, 280),
    "tet-hb": (296, 270),
    "yod-hb": (134, 400),
    "kaf-hb": (180, 300),
    "kafFinal-hb": (170, 300),
    "lamed-hb": (200, 280),
    "mem-hb": (280, 280),
    "memFinal-hb": (287, 276),
    "nun-hb": (140, 300),
    "nunFinal-hb": (95, 300),
    "samekh-hb": (301, 271),
    "ayin-hb": (280, 320),
    "pe-hb": (330, 300),
    "peFinal-hb": (300, 350),
    "tsadi-hb": (220, 300),
    "tsadiFinal-hb": (220, 300),
    "qof-hb": (424, 280),
    "resh-hb": (180, 300),
    "shin-hb": (410, 250),
    "tav-hb": (370, 280),
}

NARROW = {"vav-hb", "yod-hb", "nun-hb", "nunFinal-hb", "zayin-hb"}


def metrics(master_name: str) -> dict[str, float]:
    """Per-master sizes, interpolated-friendly, large enough for RoundCorner."""
    if master_name == "Thin":
        return dict(dot=52, gap=48, stack=16, bar_w=150, bar_h=28, stem_h=72, top_gap=36, meteg_h=120)
    if master_name == "Regular":
        return dict(dot=72, gap=64, stack=20, bar_w=220, bar_h=42, stem_h=96, top_gap=48, meteg_h=150)
    if master_name == "ExtraBlack":
        return dict(dot=96, gap=80, stack=24, bar_w=280, bar_h=58, stem_h=120, top_gap=56, meteg_h=180)
    raise KeyError(master_name)


def rect(x: float, y: float, w: float, h: float) -> GSPath:
    path = GSPath()
    path.closed = True
    for px, py in ((x, y), (x + w, y), (x + w, y + h), (x, y + h)):
        path.nodes.append(GSNode((px, py), "line"))
    return path


def tee(x: float, y_bottom: float, bar_w: float, bar_h: float, stem_w: float, stem_h: float) -> GSPath:
    """Inverted-T qamats: bar on top, stem down from center. 8 nodes, CCW."""
    x0 = x
    x1 = x + bar_w
    cx0 = x + (bar_w - stem_w) / 2
    cx1 = cx0 + stem_w
    y_bar = y_bottom + stem_h
    y_top = y_bar + bar_h
    path = GSPath()
    path.closed = True
    for px, py in (
        (cx0, y_bottom),
        (cx1, y_bottom),
        (cx1, y_bar),
        (x1, y_bar),
        (x1, y_top),
        (x0, y_top),
        (x0, y_bar),
        (cx0, y_bar),
    ):
        path.nodes.append(GSNode((px, py), "line"))
    return path


def add_anchor(layer: GSLayer, name: str, x: float, y: float) -> None:
    layer.anchors.append(GSAnchor(name, (round(x), round(y))))


def clear_layer(layer: GSLayer) -> None:
    layer.paths = []
    layer.components = []
    layer.anchors = []
    layer.width = 0


def place_dot(layer: GSLayer, cx: float, cy: float, size: float) -> None:
    layer.paths.append(rect(cx - size / 2, cy - size / 2, size, size))


def recenter_x(layer: GSLayer) -> None:
    xs = [n.position.x for p in layer.paths for n in p.nodes]
    if not xs:
        return
    mid = (min(xs) + max(xs)) / 2
    for p in layer.paths:
        for n in p.nodes:
            n.position = (n.position.x - mid, n.position.y)


def below_top(m: dict[str, float]) -> float:
    """y of the top of the first below-mark row (still under the baseline)."""
    return -m["gap"]


def row_center(m: dict[str, float], row: int) -> float:
    """Center y of a below-dot row. row 0 is closest to the letter."""
    size = m["dot"]
    top = below_top(m)
    return top - size / 2 - row * (size + m["stack"])


def build_marks(font: GSFont) -> None:
    for master in font.masters:
        m = metrics(master.name)
        d, g, st = m["dot"], m["gap"], m["stack"]
        bw, bh, sh = m["bar_w"], m["bar_h"], m["stem_h"]
        tg = m["top_gap"]

        def layer(name: str) -> GSLayer:
            return font.glyphs[name].layers[master.id]

        # --- single below dot: hiriq, lowerDot ---
        for name in ("hiriq-hb", "lowerDot-hb"):
            ly = layer(name)
            clear_layer(ly)
            place_dot(ly, 0, row_center(m, 0), d)
            add_anchor(ly, "_bottom", 0, 0)
            add_anchor(ly, "bottom", 0, below_top(m) - d - st)

        # --- sheva: two stacked dots ---
        ly = layer("sheva-hb")
        clear_layer(ly)
        place_dot(ly, 0, row_center(m, 0), d)
        place_dot(ly, 0, row_center(m, 1), d)
        add_anchor(ly, "_bottom", 0, 0)
        add_anchor(ly, "bottom", 0, below_top(m) - 2 * d - st)

        # --- tsere: two horizontal dots ---
        ly = layer("tsere-hb")
        clear_layer(ly)
        spread = d + st
        place_dot(ly, -spread / 2, row_center(m, 0), d)
        place_dot(ly, spread / 2, row_center(m, 0), d)
        add_anchor(ly, "_bottom", 0, 0)
        add_anchor(ly, "bottom", 0, below_top(m) - d - st)

        # --- segol: two on top, one below center (triangle pointing down) ---
        ly = layer("segol-hb")
        clear_layer(ly)
        place_dot(ly, -spread / 2, row_center(m, 0), d)
        place_dot(ly, spread / 2, row_center(m, 0), d)
        place_dot(ly, 0, row_center(m, 1), d)
        add_anchor(ly, "_bottom", 0, 0)
        add_anchor(ly, "bottom", 0, below_top(m) - 2 * d - st)

        # --- patah ---
        ly = layer("patah-hb")
        clear_layer(ly)
        y_bar = below_top(m) - bh
        ly.paths.append(rect(-bw / 2, y_bar, bw, bh))
        add_anchor(ly, "_bottom", 0, 0)
        add_anchor(ly, "bottom", 0, y_bar - st)

        # --- qamats / qamats qatan ---
        stem_w = bh
        for name, bar_scale, stem_scale in (("qamats-hb", 1.0, 1.0), ("qamatsQatan-hb", 0.78, 0.72)):
            ly = layer(name)
            clear_layer(ly)
            bar_w = bw * bar_scale
            stem_h = sh * stem_scale
            y_bar = below_top(m) - bh
            y_bot = y_bar - stem_h
            ly.paths.append(tee(-bar_w / 2, y_bot, bar_w, bh, stem_w, stem_h))
            add_anchor(ly, "_bottom", 0, 0)
            add_anchor(ly, "bottom", 0, y_bot - st)

        # --- qubuts: three dots down-right (GF / Noto convention) ---
        ly = layer("qubuts-hb")
        clear_layer(ly)
        step_x = d * 0.85
        for i in range(3):
            place_dot(ly, (i - 1) * step_x, row_center(m, i * 0.55), d)
        add_anchor(ly, "_bottom", 0, 0)
        add_anchor(ly, "bottom", 0, below_top(m) - 2 * d - 2 * st)

        # --- hatafim: vowel on the left, sheva on the right ---
        sheva_x = bw / 2 + st + d

        ly = layer("hatafPatah-hb")
        clear_layer(ly)
        y_bar = below_top(m) - bh
        ly.paths.append(rect(-bw / 2, y_bar, bw, bh))
        place_dot(ly, sheva_x, row_center(m, 0), d)
        place_dot(ly, sheva_x, row_center(m, 1), d)
        recenter_x(ly)
        add_anchor(ly, "_bottom", 0, 0)
        add_anchor(ly, "bottom", 0, below_top(m) - 2 * d - st)

        ly = layer("hatafQamats-hb")
        clear_layer(ly)
        y_bar = below_top(m) - bh
        y_bot = y_bar - sh
        ly.paths.append(tee(-bw / 2, y_bot, bw, bh, stem_w, sh))
        place_dot(ly, sheva_x, row_center(m, 0), d)
        place_dot(ly, sheva_x, row_center(m, 1), d)
        recenter_x(ly)
        add_anchor(ly, "_bottom", 0, 0)
        add_anchor(ly, "bottom", 0, y_bot - st)

        ly = layer("hatafSegol-hb")
        clear_layer(ly)
        seg_spread = d + st
        place_dot(ly, -seg_spread / 2, row_center(m, 0), d)
        place_dot(ly, seg_spread / 2, row_center(m, 0), d)
        place_dot(ly, 0, row_center(m, 1), d)
        sheva_hx = seg_spread / 2 + st + d
        place_dot(ly, sheva_hx, row_center(m, 0), d)
        place_dot(ly, sheva_hx, row_center(m, 1), d)
        recenter_x(ly)
        add_anchor(ly, "_bottom", 0, 0)
        add_anchor(ly, "bottom", 0, below_top(m) - 2 * d - st)

        # --- holam / holam haser / shin / sin / upper: dots above ---
        above_cy = HEBREW_TOP + tg + d / 2
        for name, anchor in (
            ("holam-hb", "_topleft"),
            ("holamHaser-hb", "_topleft"),
            ("sinDot-hb", "_topleft"),
            ("shinDot-hb", "_topright"),
            ("upperDot-hb", "_top"),
        ):
            ly = layer(name)
            clear_layer(ly)
            place_dot(ly, 0, above_cy, d)
            add_anchor(ly, anchor, 0, HEBREW_TOP)
            # mkmk outgoing at the top of the dot
            out = "top" if "topright" not in anchor and "topleft" not in anchor else anchor[1:]
            add_anchor(ly, out, 0, HEBREW_TOP + tg + d + st)

        # --- dagesh: square around origin, attaches to `center` ---
        ly = layer("dagesh-hb")
        clear_layer(ly)
        place_dot(ly, 0, 0, d)
        add_anchor(ly, "_center", 0, 0)

        # --- rafe: bar above ---
        ly = layer("rafe-hb")
        clear_layer(ly)
        y_rafe = HEBREW_TOP + tg
        ly.paths.append(rect(-bw / 2, y_rafe, bw, bh * 0.85))
        add_anchor(ly, "_top", 0, HEBREW_TOP)
        add_anchor(ly, "top", 0, y_rafe + bh * 0.85 + st)

        # --- meteg: vertical bar, attaches to bottomleft so it can sit beside a vowel ---
        ly = layer("meteg-hb")
        clear_layer(ly)
        mw = bh * 0.85
        mh = m["meteg_h"]
        y_meteg = below_top(m) - mh
        ly.paths.append(rect(-mw / 2, y_meteg, mw, mh))
        add_anchor(ly, "_bottomleft", 0, 0)
        add_anchor(ly, "bottom", 0, y_meteg - st)


def letter_anchors(layer: GSLayer, name: str, regular_width: float) -> None:
    w = layer.width
    b = layer.bounds
    bx = b.origin.x
    bw = b.size.width
    cx = bx + bw / 2

    # Below: optical center of the body (ignore descenders by clamping y to 0).
    bottom_x = cx
    if name in {"qof-hb"}:
        # Sit under the head, not the descender.
        bottom_x = bx + bw * 0.62
    elif name in {"lamed-hb"}:
        bottom_x = bx + bw * 0.48
    elif name in {"kafFinal-hb", "peFinal-hb"}:
        bottom_x = bx + bw * 0.42
    elif name in NARROW:
        bottom_x = cx

    layer.anchors = []
    add_anchor(layer, "bottom", bottom_x, 0)
    add_anchor(layer, "bottomleft", bottom_x - max(70, w * 0.16), 0)

    # Holam / sin: above-left, except on vav/yod where holam sits on the letter.
    if name in {"vav-hb", "yod-hb"}:
        holam_x = cx
    elif name == "shin-hb":
        holam_x = bx + bw * 0.14
    else:
        holam_x = bx + min(24, bw * 0.08)
    add_anchor(layer, "topleft", holam_x, HEBREW_TOP)

    # Rafe / upper dot: centered on the body top (not lamed's ascender).
    add_anchor(layer, "top", cx, HEBREW_TOP)

    # Shin dot: right arm. Other letters still get topright for completeness.
    if name == "shin-hb":
        shin_x = bx + bw * 0.88
    else:
        shin_x = bx + bw * 0.86
    add_anchor(layer, "topright", shin_x, HEBREW_TOP)

    rx, ry = REG_DAGESH[name]
    dx = rx * (w / regular_width)
    add_anchor(layer, "center", dx, ry)


def add_dotted_circle(font: GSFont) -> None:
    """Fallback carrier for invalid marks (Microsoft Hebrew OT spec)."""
    if "dottedCircle" in [g.name for g in font.glyphs]:
        g = font.glyphs["dottedCircle"]
    else:
        g = GSGlyph("dottedCircle")
        g.unicode = "25CC"
        g.category = "Symbol"
        font.glyphs.append(g)
        # Ensure a layer exists per master (GSGlyph usually creates them).
        for master in font.masters:
            if master.id not in [ly.layerId for ly in g.layers]:
                ly = GSLayer()
                ly.layerId = master.id
                ly.associatedMasterId = master.id
                g.layers.append(ly)

    src = font.glyphs["o"]
    for master in font.masters:
        ly = g.layers[master.id]
        src_ly = src.layers[master.id]
        ly.paths = []
        ly.components = []
        ly.anchors = []
        # Clone `o` outlines — closest existing round/geometric carrier.
        for p in src_ly.paths:
            np = GSPath()
            np.closed = p.closed
            for n in p.nodes:
                nn = GSNode((n.position.x, n.position.y), n.type)
                nn.smooth = n.smooth
                np.nodes.append(nn)
            ly.paths.append(np)
        ly.width = src_ly.width
        add_anchor(ly, "bottom", ly.width / 2, 0)
        add_anchor(ly, "bottomleft", ly.width / 2 - 80, 0)
        add_anchor(ly, "center", ly.width / 2, HEBREW_TOP / 2)
        add_anchor(ly, "top", ly.width / 2, HEBREW_TOP)
        add_anchor(ly, "topleft", 40, HEBREW_TOP)
        add_anchor(ly, "topright", ly.width - 40, HEBREW_TOP)
        # Latin ogonek: FontBakery requires every combining mark to attach
        # to dotted circle. Copy placement from o, whose outline we cloned.
        for a in src_ly.anchors:
            if a.name == "ogonek":
                add_anchor(ly, "ogonek", a.position.x, a.position.y)


def set_hebrew_info(font: GSFont) -> None:
    for g in font.glyphs:
        if not g.name.endswith("-hb") and g.name not in {"sheqel", "dottedCircle"}:
            continue
        if g.category == "Mark":
            g.script = "hebrew"
            g.subCategory = "Nonspacing"
        elif g.name.endswith("-hb") and g.unicode and int(g.unicode, 16) >= 0x05D0:
            g.script = "hebrew"
            if not g.category:
                g.category = "Letter"


def main() -> None:
    font = GSFont(SOURCE)
    regular = next(m for m in font.masters if m.name == "Regular")
    regular_widths = {name: font.glyphs[name].layers[regular.id].width for name in LETTERS}

    build_marks(font)
    for master in font.masters:
        for name in LETTERS:
            letter_anchors(font.glyphs[name].layers[master.id], name, regular_widths[name])
    add_dotted_circle(font)
    set_hebrew_info(font)
    font.save(SOURCE)
    print(f"Saved {SOURCE}")
    print("Masters:", ", ".join(m.name for m in font.masters))
    print("Marks rebuilt:", ", ".join(g.name for g in font.glyphs if g.category == "Mark" and g.name.endswith("-hb")))


if __name__ == "__main__":
    main()
