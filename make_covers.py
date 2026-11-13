"""Pembuat sampul buku v2: SETIAP buku mendapat gambar sampul sendiri (PNG 400x600).

- Ilustrasi dipilih sesuai isi/cerita buku (kapal untuk Moby Dick, kastil & kelelawar untuk Dracula,
  batik/candi untuk sastra klasik Nusantara, terminal untuk buku pemrograman, dst.).
- Buku pelajaran memakai templat khusus: lencana kelas + ikon mata pelajaran.
- Kombinasi (ilustrasi, tata letak, palet warna) dijamin tidak ada yang kembar.
Hasil: static/img/covers/<slug>.png.   Jalankan:  python make_covers.py   (butuh Pillow)"""
import colorsys
import math
import os
import random
import re

from PIL import Image, ImageDraw, ImageFont

from catalog import BOOKS, slugify

S = 2                      # supersampling (gambar dibuat 2x lalu diperkecil agar halus)
W, H = 400 * S, 600 * S
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static", "img", "covers")
FONT_DIRS = ["/usr/share/fonts/truetype/dejavu", "/usr/share/fonts/truetype/liberation", "C:/Windows/Fonts",
             "/Library/Fonts", "/System/Library/Fonts/Supplemental"]
FONTS = {
    "serif": ["DejaVuSerif-Bold.ttf", "LiberationSerif-Bold.ttf", "georgiab.ttf", "timesbd.ttf"],
    "serifc": ["DejaVuSerifCondensed-Bold.ttf", "DejaVuSerif-Bold.ttf", "georgiab.ttf"],
    "italic": ["DejaVuSerif-Italic.ttf", "LiberationSerif-Italic.ttf", "georgiai.ttf"],
    "sans": ["DejaVuSans-Bold.ttf", "LiberationSans-Bold.ttf", "arialbd.ttf"],
    "sansc": ["DejaVuSansCondensed-Bold.ttf", "DejaVuSans-Bold.ttf", "arialbd.ttf"],
    "light": ["DejaVuSans.ttf", "LiberationSans-Regular.ttf", "arial.ttf"],
    "mono": ["DejaVuSansMono-Bold.ttf", "LiberationMono-Bold.ttf", "consolab.ttf"],
}
_fc = {}


def font(kind, size):
    key = (kind, int(size))
    if key not in _fc:
        for d in FONT_DIRS:
            for n in FONTS[kind]:
                p = os.path.join(d, n)
                if os.path.exists(p):
                    _fc[key] = ImageFont.truetype(p, int(size))
                    break
            if key in _fc:
                break
        else:
            _fc[key] = ImageFont.load_default()
    return _fc[key]


def hsl(h, s, l, a=None):
    r, g, b = colorsys.hls_to_rgb(h % 1, max(0, min(1, l)), max(0, min(1, s)))
    c = (int(r * 255), int(g * 255), int(b * 255))
    return c + (a,) if a is not None else c


# ====================================================================== PALET
class Pal:
    """mode 'dark' = sampul gelap, 'light' = sampul terang/pastel."""
    def __init__(self, h, ah, mode, idx):
        self.idx, self.mode = idx, mode
        if mode == "dark":
            self.top, self.bot = hsl(h, .50, .36), hsl(h + .03, .55, .17)
            self.dk, self.mid = hsl(h, .45, .07), hsl(h, .40, .15)
            self.ac, self.lt = hsl(ah, .85, .62), hsl(ah, .90, .86)
            self.paper, self.ink, self.sub = hsl(h, .45, .09), (255, 255, 255), hsl(ah, .6, .80)
        else:
            self.top, self.bot = hsl(ah, .75, .80), hsl(h, .55, .90)
            self.dk, self.mid = hsl(h, .50, .25), hsl(h, .38, .45)
            self.ac, self.lt = hsl(ah, .90, .52), (255, 255, 255)
            self.paper, self.ink, self.sub = hsl(h, .40, .94), hsl(h, .60, .13), hsl(h, .35, .35)


# (hue badan, hue aksen, mode) — 40 palet berbeda
PAL_DEF = [(.97, .10, "dark"), (.58, .12, "dark"), (.38, .15, "dark"), (.75, .13, "dark"), (.08, .55, "dark"),
           (.52, .95, "dark"), (.12, .60, "dark"), (.30, .92, "dark"), (.66, .10, "dark"), (.02, .14, "dark"),
           (.85, .15, "dark"), (.46, .08, "dark"), (.20, .78, "dark"), (.62, .98, "dark"), (.92, .13, "dark"),
           (.33, .08, "dark"), (.70, .16, "dark"), (.05, .50, "dark"), (.55, .08, "dark"), (.80, .12, "dark"),
           (.97, .10, "light"), (.58, .08, "light"), (.38, .95, "light"), (.75, .10, "light"), (.08, .60, "light"),
           (.52, .02, "light"), (.12, .62, "light"), (.30, .90, "light"), (.66, .06, "light"), (.02, .55, "light"),
           (.85, .12, "light"), (.46, .04, "light"), (.20, .80, "light"), (.62, .95, "light"), (.92, .10, "light"),
           (.33, .06, "light"), (.70, .14, "light"), (.05, .52, "light"), (.55, .03, "light"), (.80, .10, "light")]


# ================================================================ PRIMITIF GAMBAR
class T:
    """Koordinat 0..100 (persen) di dalam kotak seni."""
    def __init__(self, w, h):
        self.w, self.h = w, h

    def p(self, u, v):
        return (u / 100 * self.w, v / 100 * self.h)

    def L(self, u):
        return u / 100 * self.w


def poly(d, t, pts, fill, outline=None):
    d.polygon([t.p(u, v) for u, v in pts], fill=fill, outline=outline)


def circ(d, t, u, v, r, fill=None, outline=None, width=0):
    x, y, rr = u / 100 * t.w, v / 100 * t.h, r / 100 * t.w
    d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=fill, outline=outline, width=int(width * S))


def ell(d, t, u, v, ru, rv, fill=None, outline=None, width=0):
    x, y = t.p(u, v)
    d.ellipse([x - ru / 100 * t.w, y - rv / 100 * t.h, x + ru / 100 * t.w, y + rv / 100 * t.h], fill=fill, outline=outline, width=int(width * S))


def line(d, t, pts, fill, width=1):
    d.line([t.p(u, v) for u, v in pts], fill=fill, width=max(1, int(width * S)), joint="curve")


def rect(d, t, u0, v0, u1, v1, fill, radius=0):
    a, b = t.p(u0, v0), t.p(u1, v1)
    if radius:
        d.rounded_rectangle([a, b], radius=radius * S, fill=fill)
    else:
        d.rectangle([a, b], fill=fill)


def rot(pts, cx, cy, ang):
    a = math.radians(ang)
    return [(cx + (x - cx) * math.cos(a) - (y - cy) * math.sin(a), cy + (x - cx) * math.sin(a) + (y - cy) * math.cos(a)) for x, y in pts]


def glyph(d, t, text, u, v, size, fill, kind="sans"):
    d.text(t.p(u, v), text, font=font(kind, size * S), fill=fill, anchor="mm")


def sun(d, t, P, u=72, v=28, r=11):
    for k, a in ((2.2, 40), (1.6, 80), (1.25, 140)):
        circ(d, t, u, v, r * k, P.ac + (a,))
    circ(d, t, u, v, r, P.lt + (255,))


def stars(d, t, P, rnd, n=40, vmax=62):
    for _ in range(n):
        circ(d, t, rnd.uniform(0, 100), rnd.uniform(0, vmax), rnd.choice((.25, .4, .7)), P.lt + (rnd.randint(110, 255),))


def clouds(d, t, rnd, n=4, col=(255, 255, 255, 170), vmin=8, vmax=40):
    for _ in range(n):
        u, v, s = rnd.uniform(5, 90), rnd.uniform(vmin, vmax), rnd.uniform(5, 9)
        for du, dv, k in ((0, 0, 1), (-s * .8, s * .25, .7), (s * .85, s * .2, .75), (0, s * .35, .85)):
            circ(d, t, u + du, v + dv, s * k * .6, col)


def hills(d, t, rnd, base, amp, col, step=3):
    ph, f = rnd.uniform(0, 6), rnd.uniform(.05, .11)
    pts = [(0, 100)] + [(u, base + amp * math.sin(u * f + ph) + amp * .45 * math.sin(u * f * 2.3 + ph * 1.7)) for u in range(0, 101, step)] + [(100, 100)]
    poly(d, t, pts, col)


def waves(d, t, rnd, v0, rows, cols):
    for i in range(rows):
        ph = rnd.uniform(0, 6)
        v = v0 + i * (100 - v0) / rows
        pts = [(0, 100)] + [(u, v + 1.6 * math.sin(u * .22 + ph + i)) for u in range(0, 101, 3)] + [(100, 100)]
        poly(d, t, pts, cols[i % len(cols)])


def gear(d, t, u, v, r, teeth, fill, hole=None, rot0=0):
    pts = []
    for i in range(teeth * 2):
        a = math.radians(rot0 + i * 180 / teeth)
        rr = r if i % 2 == 0 else r * .78
        for da in (-.4, .4):
            aa = a + da * math.pi / teeth
            pts.append((u + rr * math.cos(aa), v + rr * math.sin(aa) * t.w / t.h))
    poly(d, t, pts, fill)
    circ(d, t, u, v, r * .55, hole or (0, 0, 0, 0)) if hole else None


# ================================================================== ADEGAN (SCENE)
def s_ship(d, t, P, rnd, var="ship"):
    stars(d, t, P, rnd, 18, 40) if P.mode == "dark" else clouds(d, t, rnd, 3)
    sun(d, t, P, rnd.choice((22, 75)), 25, 9)
    if var == "ship":
        poly(d, t, [(26, 58), (74, 58), (66, 68), (34, 68)], P.dk)
        for mu, h0, w in ((40, 20, 14), (52, 12, 17), (63, 24, 12)):
            rect(d, t, mu - .6, h0, mu + .6, 60, P.dk)
            poly(d, t, [(mu + .6, h0 + 3), (mu + w, 54), (mu + .6, 56)], P.lt + (235,))
        poly(d, t, [(26, 58), (18, 54), (30, 58)], P.dk)
    elif var == "whale":
        poly(d, t, [(48, 70), (49, 52), (45, 40), (30, 34), (40, 46), (46, 38), (50, 36), (54, 38), (58, 46), (70, 34), (55, 40), (51, 52), (52, 70)], P.dk)
        for i in range(8):
            circ(d, t, 40 + i * 3.2, 70 + rnd.uniform(-1, 1), rnd.uniform(1, 2.2), P.lt + (210,))
    else:  # kapal selam
        ell(d, t, 50, 56, 30, 8, P.dk)
        rect(d, t, 44, 44, 56, 52, P.dk, 2)
        rect(d, t, 49, 36, 51, 46, P.dk)
        rect(d, t, 49, 36, 56, 38, P.dk)
        for i in range(5):
            circ(d, t, 36 + i * 7, 56, 1.8, P.ac + (255,))
        poly(d, t, [(20, 56), (12, 48), (14, 62)], P.dk)
        for i in range(10):
            circ(d, t, 70 + rnd.uniform(0, 14), 50 - i * 2.2, rnd.uniform(.5, 1.4), P.lt + (170,))
    waves(d, t, rnd, 64, 5, [P.mid + (230,), P.dk + (240,)])


def s_castle(d, t, P, rnd, var="castle"):
    stars(d, t, P, rnd, 35, 55)
    circ(d, t, 70, 24, 12, P.lt + (255,))
    for _ in range(4):
        circ(d, t, 70 + rnd.uniform(-6, 6), 24 + rnd.uniform(-6, 6), rnd.uniform(1, 2.2), P.top + (90,))
    hills(d, t, rnd, 78, 4, P.mid + (255,))
    if var == "castle":
        rect(d, t, 25, 48, 75, 82, P.dk)
        for u in (22, 40, 58, 72):
            rect(d, t, u, 32, u + 8, 82, P.dk)
            poly(d, t, [(u - 1, 32), (u + 4, 18), (u + 9, 32)], P.dk)
        for u in range(28, 74, 9):
            rect(d, t, u, 40, u + 3, 46, P.dk)
    elif var == "lightning":
        rect(d, t, 38, 36, 62, 84, P.dk)
        poly(d, t, [(35, 36), (50, 14), (65, 36)], P.dk)
        rect(d, t, 20, 58, 38, 84, P.dk)
        poly(d, t, [(48, 0), (42, 22), (49, 22), (40, 44), (58, 18), (50, 18), (56, 0)], P.ac + (255,))
    else:  # rumah besar + pohon gundul
        rect(d, t, 24, 52, 70, 82, P.dk)
        poly(d, t, [(20, 52), (47, 32), (74, 52)], P.dk)
        rect(d, t, 30, 38, 34, 52, P.dk)
        rect(d, t, 60, 40, 64, 52, P.dk)
        line(d, t, [(86, 84), (86, 56), (80, 46), (86, 56), (92, 44), (86, 62), (80, 66)], P.dk, 2)
    for _ in range(14):
        u, v = rnd.uniform(28, 70), rnd.uniform(56, 78)
        rect(d, t, u, v, u + 1.8, v + 3.2, P.ac + (255,))
    for _ in range(5):
        u, v = rnd.uniform(8, 80), rnd.uniform(8, 38)
        poly(d, t, [(u, v), (u + 2.5, v - 2), (u + 5, v), (u + 2.5, v + 1)], P.dk + (255,))


def s_mountains(d, t, P, rnd, var="sun"):
    sun(d, t, P, rnd.choice((26, 70)), 24, 10)
    for k, (base, col) in enumerate(((52, P.mid + (255,)), (62, P.dk + (255,)))):
        pts, u = [(0, 100)], -5
        while u < 105:
            pts.append((u, base + rnd.uniform(-2, 3)))
            pk = base - rnd.uniform(18, 34) + k * 5
            pts.append((u + rnd.uniform(6, 11), pk))
            if k == 0:
                poly(d, t, [(u + 6, pk + 8), (u + 8.5, pk), (u + 11, pk + 7)], P.lt + (230,))
            u += rnd.uniform(18, 26)
        pts.append((100, 100))
        poly(d, t, pts, col)
    for i in range(14):
        u, v = rnd.uniform(0, 100), rnd.uniform(76, 98)
        poly(d, t, [(u, v), (u + 3, v - 12), (u + 6, v)], P.dk + (255,))


def s_skyline(d, t, P, rnd, var="plain"):
    stars(d, t, P, rnd, 25, 45) if P.mode == "dark" else clouds(d, t, rnd, 3)
    circ(d, t, rnd.choice((22, 78)), 20, 8, P.lt + (255,))
    u = -2
    while u < 100:
        w, h = rnd.uniform(6, 13), rnd.uniform(22, 52)
        rect(d, t, u, 90 - h, u + w, 100, P.dk + (255,) if rnd.random() < .6 else P.mid + (255,))
        for _ in range(int(w * h / 40)):
            wu, wv = u + rnd.uniform(1, w - 2), 90 - h + rnd.uniform(3, h - 3)
            rect(d, t, wu, wv, wu + 1.3, wv + 2, P.ac + (rnd.randint(130, 255),))
        u += w + rnd.uniform(0, 1.5)
    if var == "london":
        rect(d, t, 44, 24, 56, 100, P.dk)
        poly(d, t, [(42, 24), (50, 4), (58, 24)], P.dk)
        circ(d, t, 50, 34, 4, P.lt + (255,))
        line(d, t, [(50, 34), (50, 31)], P.dk, 1)
        line(d, t, [(50, 34), (52, 35)], P.dk, 1)
    elif var == "domes":
        for cu, r in ((30, 9), (58, 11), (80, 7)):
            rect(d, t, cu - r * .6, 62, cu + r * .6, 100, P.dk)
            circ(d, t, cu, 58, r * .75, P.dk)
            poly(d, t, [(cu - r * .45, 52), (cu, 40 - r * .6), (cu + r * .45, 52)], P.dk)
            line(d, t, [(cu, 40 - r * .6), (cu, 34 - r * .6)], P.ac + (255,), 1.5)


def s_forest(d, t, P, rnd, var="pine"):
    circ(d, t, rnd.choice((24, 74)), 22, 10, P.lt + (255,))
    if var == "pine":
        for k, (v0, col) in enumerate(((60, P.mid + (255,)), (72, P.dk + (255,)), (88, P.dk + (255,)))):
            u = -4
            while u < 104:
                h = rnd.uniform(16, 30) - k * 3
                for j in range(3):
                    poly(d, t, [(u - 5 + j, v0 - h * (.5 + j * .0) + j * h * .3 + h * .3), (u + 3, v0 - h + j * h * .3), (u + 11 - j, v0 - h * .5 + j * h * .3 + h * .3)], col)
                rect(d, t, u + 2.3, v0 + 1, u + 3.7, v0 + 6, col)
                u += rnd.uniform(7, 12)
    else:  # hutan rimba: daun besar + mata
        for _ in range(16):
            cx, cy, a = rnd.uniform(0, 100), rnd.uniform(40, 100), rnd.uniform(0, 360)
            L = rnd.uniform(18, 34)
            pts = [(cx, cy)] + [(cx + L * math.cos(math.radians(a)) * s_ / 10 + 4 * math.sin(s_ * math.pi / 10) * math.cos(math.radians(a + 90)), cy + L * math.sin(math.radians(a)) * s_ / 10 * t.w / t.h + 4 * math.sin(s_ * math.pi / 10) * math.sin(math.radians(a + 90))) for s_ in range(11)]
            pts += [(cx + L * math.cos(math.radians(a)) * s_ / 10 - 4 * math.sin(s_ * math.pi / 10) * math.cos(math.radians(a + 90)), cy + L * math.sin(math.radians(a)) * s_ / 10 * t.w / t.h - 4 * math.sin(s_ * math.pi / 10) * math.sin(math.radians(a + 90))) for s_ in range(10, -1, -1)]
            poly(d, t, pts, (P.dk if rnd.random() < .6 else P.mid) + (255,))
        ell(d, t, 40, 62, 2.2, 1.2, P.ac + (255,)); ell(d, t, 52, 62, 2.2, 1.2, P.ac + (255,))


def s_flowers(d, t, P, rnd, var="garden"):
    clouds(d, t, rnd, 3)
    sun(d, t, P, 80, 18, 7)
    hills(d, t, rnd, 64, 5, P.mid + (255,))
    for i in range(7):
        u, v, r = 10 + i * 13 + rnd.uniform(-3, 3), rnd.uniform(34, 56), rnd.uniform(5, 8.5)
        line(d, t, [(u, v), (u + rnd.uniform(-3, 3), 100)], P.dk + (255,), 2.2)
        poly(d, t, [(u, v + 22), (u + 8, v + 17), (u + 2, v + 26)], P.dk + (255,))
        col = P.ac if i % 2 == 0 else P.lt
        for k in range(8):
            a = k * math.pi / 4
            circ(d, t, u + r * .9 * math.cos(a), v + r * .9 * math.sin(a) * t.w / t.h, r * .55, col + (235,))
        circ(d, t, u, v, r * .5, P.dk + (255,))


def s_space(d, t, P, rnd, var="planet"):
    stars(d, t, P, rnd, 70, 100)
    if var == "tripod":
        circ(d, t, 70, 18, 6, P.lt + (255,))
        poly(d, t, [(38, 52), (50, 42), (62, 52), (50, 56)], P.dk)
        for u0, u1 in ((40, 30), (50, 50), (60, 70)):
            line(d, t, [(u0, 55), ((u0 + u1) / 2, 74), (u1, 100)], P.dk + (255,), 1.8)
        line(d, t, [(48, 56), (30, 62)], P.ac + (255,), 1.6)
        hills(d, t, rnd, 92, 2, P.dk + (255,))
        return
    if var == "clock":
        circ(d, t, 50, 46, 32, None, P.lt + (255,), 2)
        for k in range(12):
            a = k * math.pi / 6
            line(d, t, [(50 + 26 * math.cos(a), 46 + 26 * math.sin(a) * t.w / t.h), (50 + 30 * math.cos(a), 46 + 30 * math.sin(a) * t.w / t.h)], P.lt + (255,), 1.5)
        line(d, t, [(50, 46), (50, 28)], P.ac + (255,), 2); line(d, t, [(50, 46), (62, 52)], P.ac + (255,), 2)
        for r in range(6, 36, 6):
            circ(d, t, 50, 46, r, None, P.ac + (70,), 1)
        return
    col = P.ac if var != "mars" else (200, 80, 50)
    circ(d, t, 50, 48, 24, col + (255,))
    for k in range(5):
        v = 36 + k * 7
        ell(d, t, 50, v, 22 - abs(v - 48) * .7, 1.5, tuple(max(0, c - 40) for c in col) + (120,))
    ell(d, t, 50, 52, 40, 6, None, P.lt + (210,), 1.6)
    circ(d, t, 50, 48, 24, None, P.lt + (90,), 1)
    if var == "mars":
        circ(d, t, 82, 24, 3, P.lt + (255,)); circ(d, t, 20, 16, 2, P.lt + (255,))
    else:
        circ(d, t, 80, 20, 4, P.lt + (255,))


def s_train(d, t, P, rnd):
    clouds(d, t, rnd, 3); hills(d, t, rnd, 58, 6, P.mid + (255,))
    rect(d, t, 0, 80, 100, 82, P.dk)
    for u in range(0, 100, 5):
        rect(d, t, u, 82, u + 2, 86, P.dk)
    rect(d, t, 20, 58, 66, 76, P.dk, 3); rect(d, t, 54, 46, 78, 76, P.dk, 3); rect(d, t, 14, 48, 22, 58, P.dk)
    rect(d, t, 58, 50, 74, 58, P.ac + (255,), 2)
    for u in (28, 42, 56, 70):
        circ(d, t, u, 78, 5, P.dk + (255,)); circ(d, t, u, 78, 2.4, P.lt + (255,))
    for i, (u, v, r) in enumerate(((17, 38, 4), (12, 28, 5.5), (6, 16, 7), (1, 4, 8))):
        circ(d, t, u, v, r, (255, 255, 255, 190 - i * 30))


def s_cards(d, t, P, rnd, var="alice"):
    if var == "chess":
        for r in range(8):
            for c in range(8):
                if (r + c) % 2 == 0:
                    poly(d, t, [(10 + c * 10 - r * 1.2, 40 + r * 7.5), (20 + c * 10 - r * 1.2, 40 + r * 7.5), (20 + c * 10 - (r + 1) * 1.2, 47.5 + r * 7.5), (10 + c * 10 - (r + 1) * 1.2, 47.5 + r * 7.5)], P.lt + (200,))
        poly(d, t, [(42, 40), (46, 14), (50, 30), (54, 12), (58, 30), (62, 14), (66, 40)], P.dk)
        circ(d, t, 54, 9, 3, P.ac + (255,))
        return
    for k, (a, col) in enumerate(((-18, P.lt), (0, P.lt), (18, P.lt))):
        pts = rot([(34, 18), (66, 18), (66, 66), (34, 66)], 50, 70, a)
        d.polygon([(x / 100 * t.w, y / 100 * t.h) for x, y in pts], fill=col + (255,), outline=P.dk + (255,))
        cx, cy = rot([(50, 40)], 50, 70, a)[0]
        d.text((cx / 100 * t.w, cy / 100 * t.h), "♥♠♦"[k], font=font("serif", 34 * S), fill=(P.ac if k != 1 else P.dk) + (255,), anchor="mm")
    circ(d, t, 20, 78, 5, P.ac + (255,)); poly(d, t, [(17, 80), (23, 80), (20, 92)], P.ac + (255,))
    stars(d, t, P, rnd, 20, 30)


def s_oz(d, t, P, rnd):
    clouds(d, t, rnd, 3, (255, 255, 255, 120))
    for i, u in enumerate((34, 42, 50, 58, 66)):
        h = 22 + (i % 2) * 14 + (6 if i == 2 else 0)
        rect(d, t, u - 2.5, 52 - h, u + 2.5, 66, (60, 190, 120, 255))
        poly(d, t, [(u - 3, 52 - h), (u, 46 - h), (u + 3, 52 - h)], (30, 150, 90, 255))
    hills(d, t, rnd, 64, 3, (40, 130, 70, 255))
    poly(d, t, [(48, 66), (52, 66), (80, 100), (20, 100)], (235, 190, 50, 255))
    for k in range(6):
        line(d, t, [(50 - k * 9, 70 + k * 5), (50 + k * 9, 70 + k * 5)], (190, 140, 30, 255), 1)
    poly(d, t, [(4, 8), (24, 8), (16, 30), (13, 46), (11, 30)], P.dk + (210,))


def s_moonship(d, t, P, rnd):
    stars(d, t, P, rnd, 60, 70)
    circ(d, t, 50, 40, 26, P.lt + (255,))
    for _ in range(5):
        circ(d, t, 50 + rnd.uniform(-14, 14), 40 + rnd.uniform(-14, 14), rnd.uniform(1.5, 4), P.top + (70,))
    poly(d, t, [(24, 62), (76, 62), (68, 70), (32, 70)], P.dk); rect(d, t, 49, 36, 51, 64, P.dk)
    poly(d, t, [(51, 40), (66, 58), (51, 60)], P.dk); poly(d, t, [(49, 44), (36, 58), (49, 60)], P.dk)
    poly(d, t, [(80, 14), (82, 20), (88, 20), (83, 24), (85, 30), (80, 26), (75, 30), (77, 24), (72, 20), (78, 20)], P.ac + (255,))
    waves(d, t, rnd, 80, 3, [P.mid + (255,), P.dk + (255,)])


def s_fairy(d, t, P, rnd):
    stars(d, t, P, rnd, 45, 60)
    for u, h, w in ((26, 44, 11), (50, 58, 14), (74, 40, 11)):
        rect(d, t, u - w / 2, 92 - h, u + w / 2, 92, P.dk)
        poly(d, t, [(u - w / 2 - 1.5, 92 - h), (u, 92 - h - 20), (u + w / 2 + 1.5, 92 - h)], P.dk)
        line(d, t, [(u, 92 - h - 20), (u, 92 - h - 27)], P.dk + (255,), 1.2)
        poly(d, t, [(u, 92 - h - 27), (u + 7, 92 - h - 25), (u, 92 - h - 23)], P.ac + (255,))
        rect(d, t, u - 1, 92 - h + 8, u + 1, 92 - h + 14, P.ac + (255,))
    rect(d, t, 36, 62, 64, 92, P.dk)
    ell(d, t, 50, 92, 8, 9, P.ac + (255,))
    hills(d, t, rnd, 90, 2, P.mid + (255,))


def s_magnifier(d, t, P, rnd):
    for i in range(5):
        ell(d, t, rnd.uniform(20, 80), 70 + i * 6, rnd.uniform(25, 40), 2, P.lt + (60,))
    circ(d, t, 42, 42, 24, P.lt + (60,)); circ(d, t, 42, 42, 24, None, P.dk + (255,), 5)
    poly(d, t, [(58, 59), (64, 53), (88, 80), (82, 86)], P.dk)
    for k in range(4):
        ell(d, t, 24 + k * 8, 66 + (k % 2) * 6, 2.2, 3.2, P.dk + (200,)) if k < 4 else None
    glyph(d, t, "?", 42, 42, 80, P.ac + (255,), "serif")


def s_swords(d, t, P, rnd, var="swords"):
    if var == "windmill":
        sun(d, t, P, 78, 22, 8); hills(d, t, rnd, 76, 4, P.mid + (255,))
        poly(d, t, [(44, 80), (47, 46), (53, 46), (56, 80)], P.dk)
        for a in (20, 110, 200, 290):
            pts = rot([(49, 44), (51, 44), (51, 14), (49, 14)], 50, 45, a)
            d.polygon([(x / 100 * t.w, y / 100 * t.h) for x, y in pts], fill=P.dk + (255,))
            pts = rot([(51, 14), (60, 14), (60, 30), (51, 30)], 50, 45, a)
            d.polygon([(x / 100 * t.w, y / 100 * t.h) for x, y in pts], fill=P.lt + (230,), outline=P.dk + (255,))
        circ(d, t, 50, 45, 3, P.ac + (255,))
        poly(d, t, [(10, 84), (20, 62), (26, 84)], P.dk)
        return
    poly(d, t, [(24, 20), (76, 20), (76, 54), (50, 80), (24, 54)], P.dk + (255,), P.ac + (255,))
    poly(d, t, [(30, 26), (70, 26), (70, 52), (50, 72), (30, 52)], P.ac + (255,))
    for a in (45, -45):
        base = [(48.5, 6), (51.5, 6), (51.5, 78), (48.5, 78)]
        pts = rot(base, 50, 45, a)
        d.polygon([(x / 100 * t.w, y / 100 * t.h) for x, y in pts], fill=P.lt + (255,), outline=P.dk + (255,))
        pts = rot([(42, 66), (58, 66), (58, 69), (42, 69)], 50, 45, a)
        d.polygon([(x / 100 * t.w, y / 100 * t.h) for x, y in pts], fill=P.ac + (255,))
    stars(d, t, P, rnd, 18, 100)


def s_lantern(d, t, P, rnd):
    hills(d, t, rnd, 84, 3, (240, 244, 255, 255))
    rect(d, t, 47, 60, 53, 90, P.dk); rect(d, t, 36, 28, 64, 34, P.dk); rect(d, t, 38, 54, 62, 60, P.dk)
    poly(d, t, [(40, 28), (50, 16), (60, 28)], P.dk); rect(d, t, 39, 34, 61, 54, P.ac + (140,)); circ(d, t, 50, 44, 11, P.ac + (70,))
    ell(d, t, 50, 46, 3, 5.5, P.lt + (255,))
    for i in (41, 47, 53, 59):
        rect(d, t, i - .5, 34, i + .5, 54, P.dk)
    for _ in range(60):
        u, v = rnd.uniform(0, 100), rnd.uniform(0, 84)
        circ(d, t, u, v, rnd.uniform(.4, 1.1), (255, 255, 255, 220))


def s_temple(d, t, P, rnd, var="greek"):
    sun(d, t, P, 78, 20, 8)
    poly(d, t, [(12, 36), (50, 14), (88, 36)], P.dk)
    rect(d, t, 14, 36, 86, 40, P.mid)
    for i in range(7):
        u = 18 + i * 10
        rect(d, t, u, 40, u + 5, 80, P.dk); rect(d, t, u - 1, 40, u + 6, 42, P.mid)
    for k in range(3):
        rect(d, t, 10 - k * 2, 80 + k * 4, 90 + k * 2, 84 + k * 4, P.dk if k % 2 == 0 else P.mid)
    if var == "laurel":
        for s_ in (-1, 1):
            for i in range(7):
                ell(d, t, 50 + s_ * (8 + i * 1.8), 24 + i * 5, 3.4, 1.6, P.ac + (230,))


def s_compass(d, t, P, rnd):
    for i in range(9):
        line(d, t, [(0, i * 12 + 4), (100, i * 12 - 4)], P.lt + (40,), 1)
    circ(d, t, 50, 46, 34, P.lt + (50,)); circ(d, t, 50, 46, 34, None, P.dk + (255,), 3); circ(d, t, 50, 46, 28, None, P.dk + (255,), 1)
    for k in range(16):
        a = k * math.pi / 8
        r0 = 28 if k % 2 == 0 else 30
        line(d, t, [(50 + r0 * math.cos(a), 46 + r0 * math.sin(a) * t.w / t.h), (50 + 34 * math.cos(a), 46 + 34 * math.sin(a) * t.w / t.h)], P.dk + (255,), 1.2)
    poly(d, t, [(50, 14), (56, 46), (50, 78), (44, 46)], P.ac + (255,))
    poly(d, t, [(50, 78), (56, 46), (44, 46)], P.dk + (255,))
    circ(d, t, 50, 46, 3, P.lt + (255,))
    glyph(d, t, "N", 50, 8, 30, P.dk + (255,), "serif")


def s_globe(d, t, P, rnd):
    stars(d, t, P, rnd, 30, 100) if P.mode == "dark" else None
    circ(d, t, 50, 46, 34, P.ac + (230,)); circ(d, t, 50, 46, 34, None, P.dk + (255,), 3)
    for k in (.0, .35, .7):
        ell(d, t, 50, 46, 34 * k + 1, 34 * 1.0 * t.w / t.h, None, P.lt + (200,), 1.4)
    for v in (26, 46, 66):
        w = math.sqrt(max(0, 34 ** 2 - ((v - 46) * t.h / t.w) ** 2))
        line(d, t, [(50 - w, v), (50 + w, v)], P.lt + (200,), 1.4)
    for _ in range(5):
        ell(d, t, rnd.uniform(36, 64), rnd.uniform(32, 60), rnd.uniform(3, 7), rnd.uniform(2, 5), P.dk + (200,))
    poly(d, t, [(40, 88), (60, 88), (56, 94), (44, 94)], P.dk); rect(d, t, 48, 78, 52, 88, P.dk)


def s_atom(d, t, P, rnd):
    stars(d, t, P, rnd, 40, 100)
    for a in (0, 60, 120):
        pts = []
        for k in range(61):
            th = k * 2 * math.pi / 60
            x, y = 36 * math.cos(th), 13 * math.sin(th)
            ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
            pts.append((50 + x * ca - y * sa * t.w / t.h * 1.0, 46 + (x * sa + y * ca) * t.w / t.h))
        d.line([t.p(u, v) for u, v in pts], fill=P.lt + (230,), width=2 * S)
        th = rnd.uniform(0, 6.28); x, y = 36 * math.cos(th), 13 * math.sin(th)
        ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
        circ(d, t, 50 + x * ca - y * sa, 46 + (x * sa + y * ca) * t.w / t.h, 2.6, P.ac + (255,))
    circ(d, t, 50, 46, 8, P.ac + (90,)); circ(d, t, 50, 46, 5, P.ac + (255,)); circ(d, t, 48, 44, 1.6, P.lt + (255,))


def s_prism(d, t, P, rnd):
    stars(d, t, P, rnd, 25, 100)
    line(d, t, [(0, 58), (40, 48)], (255, 255, 255, 255), 2.4)
    cols = [(255, 60, 60), (255, 150, 40), (255, 230, 60), (80, 210, 90), (60, 150, 255), (140, 90, 230)]
    for i, c in enumerate(cols):
        poly(d, t, [(56, 49), (100, 52 + i * 5.4), (100, 57 + i * 5.4)], c + (230,))
    poly(d, t, [(50, 22), (22, 72), (78, 72)], P.lt + (60,), P.lt + (255,))
    line(d, t, [(50, 22), (22, 72), (78, 72), (50, 22)], P.lt + (255,), 2)


def s_candle(d, t, P, rnd):
    for r in (40, 30, 20):
        circ(d, t, 50, 36, r, P.ac + (22,))
    rect(d, t, 42, 48, 58, 88, P.lt + (255,), 2); rect(d, t, 42, 48, 46, 88, (0, 0, 0, 30))
    for k in range(3):
        poly(d, t, [(42 + k * 6, 48), (44 + k * 6, 60), (46 + k * 6, 48)], P.lt + (255,))
    line(d, t, [(50, 48), (50, 40)], P.dk + (255,), 1.4)
    poly(d, t, [(50, 12), (44, 30), (45, 40), (50, 44), (55, 40), (56, 30)], P.ac + (255,))
    poly(d, t, [(50, 24), (47.5, 34), (50, 41), (52.5, 34)], P.lt + (255,))
    rect(d, t, 30, 88, 70, 92, P.dk)


def s_telescope(d, t, P, rnd):
    stars(d, t, P, rnd, 60, 100)
    circ(d, t, 76, 22, 7, P.ac + (255,)); ell(d, t, 76, 22, 12, 2, None, P.lt + (220,), 1.2)
    for a, L in ((-32, 46), (-32, 0)):
        pass
    pts = rot([(20, 50), (66, 50), (66, 58), (20, 58)], 40, 54, -28)
    d.polygon([(x / 100 * t.w, y / 100 * t.h) for x, y in pts], fill=P.mid + (255,), outline=P.lt + (255,))
    pts = rot([(60, 48), (70, 48), (70, 60), (60, 60)], 40, 54, -28)
    d.polygon([(x / 100 * t.w, y / 100 * t.h) for x, y in pts], fill=P.ac + (255,))
    line(d, t, [(40, 56), (28, 94)], P.dk + (255,), 2.4); line(d, t, [(40, 56), (52, 94)], P.dk + (255,), 2.4); line(d, t, [(40, 56), (40, 94)], P.dk + (255,), 2.4)


def s_dna(d, t, P, rnd, var="dna"):
    if var == "cell":
        circ(d, t, 50, 46, 36, P.lt + (90,)); circ(d, t, 50, 46, 36, None, P.lt + (255,), 3)
        circ(d, t, 44, 42, 13, P.ac + (230,)); circ(d, t, 44, 42, 5, P.dk + (230,))
        for _ in range(9):
            ell(d, t, rnd.uniform(30, 70), rnd.uniform(30, 64), rnd.uniform(2, 4), rnd.uniform(1.5, 3), (P.dk if rnd.random() < .5 else P.mid) + (220,))
        return
    for k in range(25):
        v = 4 + k * 3.9
        x1, x2 = 50 + 22 * math.sin(k * .55), 50 - 22 * math.sin(k * .55)
        line(d, t, [(x1, v), (x2, v)], P.lt + (130,), 1.2)
        circ(d, t, x1, v, 2.6, P.ac + (255,)); circ(d, t, x2, v, 2.6, P.lt + (255,))


def s_hex(d, t, P, rnd):
    def hexa(u, v, r, col, wd=2):
        pts = [(u + r * math.cos(math.radians(60 * i + 30)), v + r * math.sin(math.radians(60 * i + 30)) * t.w / t.h) for i in range(6)]
        line(d, t, pts + [pts[0]], col, wd)
    for r, c in ((30, P.lt + (255,)), (20, P.ac + (255,))):
        hexa(50, 40, r, c, 2.5)
    circ(d, t, 50, 40, 8, None, P.lt + (255,), 1.8)
    for i in range(6):
        a = math.radians(60 * i + 30)
        circ(d, t, 50 + 30 * math.cos(a), 40 + 30 * math.sin(a) * t.w / t.h, 3, P.ac + (255,))
    poly(d, t, [(44, 66), (56, 66), (56, 70), (70, 88), (30, 88), (44, 70)], P.lt + (90,), P.lt + (255,))
    for i in range(4):
        circ(d, t, 40 + i * 7, 78 - i % 2 * 4, 1.6, P.ac + (255,))


def s_graph(d, t, P, rnd, var="curve"):
    for i in range(1, 8):
        line(d, t, [(8, 10 + i * 10), (92, 10 + i * 10)], P.lt + (40,), 1); line(d, t, [(8 + i * 10.5, 10), (8 + i * 10.5, 90)], P.lt + (40,), 1)
    line(d, t, [(8, 90), (92, 90)], P.lt + (255,), 2); line(d, t, [(8, 10), (8, 90)], P.lt + (255,), 2)
    if var == "bell":
        pts = [(8 + k * 1.2, 90 - 70 * math.exp(-((k - 35) ** 2) / 220)) for k in range(0, 71)]
        poly(d, t, pts + [(92, 90), (8, 90)], P.ac + (110,)); line(d, t, pts, P.ac + (255,), 2.6)
        for i in range(10):
            h = 70 * math.exp(-((i * 7 + 3.5 - 35) ** 2) / 220)
            rect(d, t, 10 + i * 8, 90 - h * .8, 16 + i * 8, 90, P.lt + (120,))
    else:
        pts = [(8 + k * 1.2, 80 - 60 * math.sin(k * .09) * math.exp(-k * .004) - k * .1) for k in range(0, 71)]
        line(d, t, pts, P.ac + (255,), 3)
        line(d, t, [(40, 38), (80, 12)], P.lt + (255,), 1.6); circ(d, t, 60, 24.7, 2.4, P.lt + (255,))
        glyph(d, t, "∫", 22, 28, 54, P.lt + (255,), "serif")


def s_heart(d, t, P, rnd):
    pts = []
    for k in range(60):
        a = k * 2 * math.pi / 60
        x, y = 16 * math.sin(a) ** 3, -(13 * math.cos(a) - 5 * math.cos(2 * a) - 2 * math.cos(3 * a) - math.cos(4 * a))
        pts.append((50 + x * 2.1, 38 + y * 1.9 * t.w / t.h))
    for sc, al in ((1.18, 60), (1.0, 255)):
        poly(d, t, [(50 + (x - 50) * sc, 38 + (y - 38) * sc) for x, y in pts], P.ac + (al,))
    line(d, t, [(0, 80), (22, 80), (28, 66), (36, 92), (44, 58), (50, 80), (100, 80)], P.lt + (255,), 2.4)


def s_terminal(d, t, P, rnd, var="term"):
    rect(d, t, 10, 14, 90, 82, P.dk + (255,), 6); rect(d, t, 10, 14, 90, 24, P.mid + (255,), 6)
    for i, c in enumerate(((255, 95, 86), (255, 189, 46), (39, 201, 63))):
        circ(d, t, 16 + i * 5, 19, 1.5, c + (255,))
    v = 32
    for i in range(8):
        u = 16 + (rnd.choice((0, 0, 6, 12)))
        for _ in range(rnd.randint(1, 3)):
            w = rnd.uniform(6, 22)
            if u + w < 86:
                rect(d, t, u, v, u + w, v + 2.4, (P.ac, P.lt, P.mid)[rnd.randint(0, 2)] + (255,), 1)
            u += w + 3
        v += 6.8
    glyph(d, t, ">_", 74, 72, 26, P.ac + (255,), "mono")


def s_symbol(d, t, P, rnd, text="{ }", size=120):
    for r in (46, 34, 22):
        circ(d, t, 50, 44, r, None, P.ac + (80,), 1.2)
    glyph(d, t, text, 50, 44, size, P.ac + (255,), "mono" if text in ("{ }", "</>", ">_") else "serif")
    for _ in range(14):
        glyph(d, t, rnd.choice("01{}();<>=+λ"), rnd.uniform(5, 95), rnd.uniform(5, 95), rnd.randint(10, 16), P.lt + (70,), "mono")


def s_tree(d, t, P, rnd):
    pos, lv = {}, 4
    for l in range(lv):
        for i in range(2 ** l):
            pos[(l, i)] = (100 * (i + .5) / 2 ** l, 14 + l * 22)
    for (l, i), (u, v) in pos.items():
        if l + 1 < lv:
            for c in (2 * i, 2 * i + 1):
                line(d, t, [(u, v), pos[(l + 1, c)]], P.lt + (180,), 1.6)
    for (l, i), (u, v) in pos.items():
        circ(d, t, u, v, 4.6 - l * .5, (P.ac if (l + i) % 3 == 0 else P.lt) + (255,))
        glyph(d, t, str(rnd.randint(1, 99)), u, v, 14 - l * 2, P.dk + (255,), "mono")


def s_network(d, t, P, rnd, var="net"):
    layers = [3, 5, 5, 2] if var == "neural" else None
    nodes = []
    if layers:
        for li, n in enumerate(layers):
            for k in range(n):
                nodes.append((12 + li * 25.3, 50 + (k - (n - 1) / 2) * 14))
        idx = 0
        for li in range(len(layers) - 1):
            a = [nodes[j] for j in range(sum(layers[:li]), sum(layers[:li + 1]))]
            b = [nodes[j] for j in range(sum(layers[:li + 1]), sum(layers[:li + 2]))]
            for p1 in a:
                for p2 in b:
                    line(d, t, [p1, p2], P.lt + (60,), 1)
    else:
        nodes = [(rnd.uniform(8, 92), rnd.uniform(8, 92)) for _ in range(16)]
        for i, p1 in enumerate(nodes):
            for p2 in sorted(nodes, key=lambda q: (q[0] - p1[0]) ** 2 + (q[1] - p1[1]) ** 2)[1:3]:
                line(d, t, [p1, p2], P.lt + (130,), 1.4)
    for i, (u, v) in enumerate(nodes):
        circ(d, t, u, v, 2.8, (P.ac if i % 3 == 0 else P.lt) + (255,))


def s_gears(d, t, P, rnd):
    gear(d, t, 40, 46, 24, 12, P.mid + (255,), P.top + (255,)); gear(d, t, 74, 30, 14, 8, P.ac + (255,), P.top + (255,), 10); gear(d, t, 70, 70, 17, 9, P.lt + (255,), P.top + (255,), 5)


def s_lotus(d, t, P, rnd):
    stars(d, t, P, rnd, 20, 40) if P.mode == "dark" else clouds(d, t, rnd, 2)
    sun(d, t, P, 50, 22, 9)
    for i in range(4):
        ell(d, t, 50, 78 + i * 5, 46 - i * 6, 1.4, P.lt + (120,), None)
    for a, col in ((-60, P.mid), (60, P.mid), (-32, P.ac), (32, P.ac), (0, P.lt)):
        pts = [(50, 78)] + [(50 + 14 * math.sin(math.radians(a)) * k / 10 + 7 * math.sin(k * math.pi / 10) * math.cos(math.radians(a)), 78 - 34 * math.cos(math.radians(a * .55)) * k / 10) for k in range(11)] + [(50 + 14 * math.sin(math.radians(a)) * k / 10 - 7 * math.sin(k * math.pi / 10) * math.cos(math.radians(a)), 78 - 34 * math.cos(math.radians(a * .55)) * k / 10) for k in range(10, -1, -1)]
        poly(d, t, pts, col + (240,), P.dk + (255,))


def s_yinyang(d, t, P, rnd):
    stars(d, t, P, rnd, 20, 100) if P.mode == "dark" else None
    circ(d, t, 50, 46, 32, P.lt + (255,))
    d.pieslice([t.p(50 - 32, 46 - 32 * t.w / t.h), t.p(50 + 32, 46 + 32 * t.w / t.h)], 270, 90, fill=P.dk + (255,))
    circ(d, t, 50, 46 - 16 * t.w / t.h, 16, P.dk + (255,)) if False else None
    ell(d, t, 50, 46 - 16 * t.w / t.h * 1.0 / (t.w / t.h) * (t.w / t.h) * .5, 16, 16 * t.w / t.h * .5 * 2 / 2, None)
    circ(d, t, 50, 46 - 16 * t.w / t.h, 16, P.lt + (255,)); circ(d, t, 50, 46 + 16 * t.w / t.h, 16, P.dk + (255,))
    circ(d, t, 50, 46 - 16 * t.w / t.h, 4.5, P.dk + (255,)); circ(d, t, 50, 46 + 16 * t.w / t.h, 4.5, P.lt + (255,))
    circ(d, t, 50, 46, 32, None, P.ac + (255,), 3)


def s_bamboo(d, t, P, rnd):
    clouds(d, t, rnd, 2); sun(d, t, P, 76, 20, 7)
    for i in range(6):
        u = 14 + i * 14 + rnd.uniform(-2, 2)
        rect(d, t, u, 0, u + 3.2, 100, (P.dk if i % 2 == 0 else P.mid) + (255,))
        for v in range(8, 100, 17):
            rect(d, t, u - .6, v, u + 3.8, v + 1.4, P.lt + (200,))
        for k in range(3):
            v = rnd.uniform(20, 80)
            poly(d, t, [(u + 3, v), (u + 14, v - 5), (u + 3, v + 1.6)], P.ac + (255,)); poly(d, t, [(u, v + 6), (u - 12, v + 1), (u, v + 7.6)], P.ac + (255,))


def s_star8(d, t, P, rnd):
    for r, a in ((46, 0), (46, 45), (34, 22.5), (34, 67.5), (22, 0), (22, 45)):
        pts = rot([(50 - r * .7, 46 - r * .7 * t.w / t.h), (50 + r * .7, 46 - r * .7 * t.w / t.h), (50 + r * .7, 46 + r * .7 * t.w / t.h), (50 - r * .7, 46 + r * .7 * t.w / t.h)], 50, 46, a)
        col = (P.ac, P.lt, P.mid)[int(a / 22.5) % 3]
        d.polygon([(x / 100 * t.w, y / 100 * t.h) for x, y in pts], outline=col + (255,), fill=col + (40,), width=3 * S)
    circ(d, t, 50, 46, 6, P.ac + (255,))


def s_openbook(d, t, P, rnd):
    for k in range(13):
        a = math.radians(-80 + k * 160 / 12)
        poly(d, t, [(50, 56), (50 + 80 * math.sin(a - .05), 56 - 80 * math.cos(a)), (50 + 80 * math.sin(a + .05), 56 - 80 * math.cos(a))], P.ac + (55,))
    poly(d, t, [(50, 78), (14, 70), (14, 40), (50, 48)], P.lt + (255,), P.dk + (255,)); poly(d, t, [(50, 78), (86, 70), (86, 40), (50, 48)], P.lt + (235,), P.dk + (255,))
    for k in range(5):
        line(d, t, [(20, 48 + k * 4.4), (46, 55 + k * 4.4)], P.mid + (255,), 1.1); line(d, t, [(54, 55 + k * 4.4), (80, 48 + k * 4.4)], P.mid + (255,), 1.1)
    circ(d, t, 50, 30, 5, P.lt + (255,))


def s_scales(d, t, P, rnd):
    sun(d, t, P, 50, 36, 22)
    rect(d, t, 48.5, 18, 51.5, 88, P.dk); rect(d, t, 36, 86, 64, 90, P.dk); rect(d, t, 14, 22, 86, 25, P.dk); circ(d, t, 50, 20, 3.4, P.ac + (255,))
    for cu in (18, 82):
        line(d, t, [(cu, 25), (cu - 10, 56)], P.dk + (255,), 1); line(d, t, [(cu, 25), (cu + 10, 56)], P.dk + (255,), 1)
        poly(d, t, [(cu - 13, 56), (cu + 13, 56), (cu + 8, 64), (cu - 8, 64)], P.dk)


def s_kawung(d, t, P, rnd):
    t_bg = P.dk if P.mode == "dark" else P.mid
    for r in range(-1, 8):
        for c in range(-1, 6):
            cx, cy = c * 22 + (11 if r % 2 else 0), r * 14
            for dx, dy, col in ((0, -6, P.ac), (6, 0, P.lt), (0, 6, P.ac), (-6, 0, P.lt)):
                ell(d, t, cx + dx, cy + dy, 6.2, 4.2, col + (150,), P.lt + (230,), 1)
            circ(d, t, cx, cy, 1.4, P.lt + (255,))


def s_parang(d, t, P, rnd):
    for k in range(-6, 14):
        pts = [(-20 + k * 16 + 40 * i / 20, 100 - i * 6 + 5 * math.sin(i * .9)) for i in range(21)]
        pts2 = [(x + 6, y) for x, y in reversed(pts)]
        poly(d, t, pts + pts2, (P.ac if k % 2 == 0 else P.lt) + (170,), P.dk + (255,))
    for k in range(-3, 10):
        circ(d, t, k * 15, 6 + (k % 3) * 30, 3, P.dk + (230,))


def s_candi(d, t, P, rnd):
    sun(d, t, P, 50, 26, 16)
    for k in range(5):
        rect(d, t, 10 + k * 3, 84 - k * 9, 90 - k * 3, 90 - k * 9, (P.dk if k % 2 == 0 else P.mid) + (255,))
    for k in range(3):
        for u in (30 + k * 20, 40 + k * 10):
            pass
    for u in (28, 36, 44, 56, 64, 72):
        ell(d, t, u, 52, 3.6, 5, P.dk + (255,)); rect(d, t, u - 3.4, 52, u + 3.4, 58, P.dk)
    ell(d, t, 50, 40, 8, 11, P.dk + (255,)); poly(d, t, [(48, 30), (50, 20), (52, 30)], P.dk)
    for u in (28, 44, 56, 72):
        for v in (62, 70, 78):
            rect(d, t, u - 1, v, u + 1, v + 4, P.ac + (230,))


def s_gunungan(d, t, P, rnd):
    stars(d, t, P, rnd, 18, 100) if P.mode == "dark" else None
    pts = [(50, 6), (58, 22), (66, 30), (72, 44), (82, 58), (86, 78), (76, 94), (50, 98), (24, 94), (14, 78), (18, 58), (28, 44), (34, 30), (42, 22)]
    poly(d, t, pts, P.mid + (255,), P.ac + (255,))
    poly(d, t, [(50, 28), (66, 52), (66, 90), (34, 90), (34, 52)], P.dk + (255,)); poly(d, t, [(50, 40), (60, 56), (60, 88), (40, 88), (40, 56)], P.ac + (255,))
    for k in range(6):
        line(d, t, [(50, 8 + k * 6), (50 + 10 + k * 3, 24 + k * 8)], P.lt + (200,), 1)
    circ(d, t, 50, 70, 6, P.dk + (255,))


def s_perahu(d, t, P, rnd):
    sun(d, t, P, 24, 26, 10); clouds(d, t, rnd, 3)
    poly(d, t, [(24, 62), (78, 62), (70, 74), (32, 74)], P.dk); poly(d, t, [(78, 62), (88, 52), (80, 62)], P.dk)
    rect(d, t, 50, 20, 51.5, 62, P.dk)
    poly(d, t, [(52, 22), (80, 60), (52, 60)], P.lt + (255,), P.dk + (255,)); poly(d, t, [(49, 28), (30, 60), (49, 60)], P.ac + (255,), P.dk + (255,))
    waves(d, t, rnd, 70, 5, [P.mid + (230,), P.dk + (240,)])


def s_ulos(d, t, P, rnd):
    cols = [P.ac, P.lt, P.mid, P.dk]
    for i in range(9):
        v0 = i * 11.5
        poly(d, t, [(0, v0), (100, v0), (100, v0 + 11.5), (0, v0 + 11.5)], cols[i % 4] + (255,))
        pts = [(k * 6.25, v0 + 1.2 + (5 if k % 2 else 0)) for k in range(17)]
        line(d, t, pts, cols[(i + 2) % 4] + (255,), 1.8)
        for k in range(0, 17, 2):
            poly(d, t, [(k * 6.25, v0 + 9), (k * 6.25 + 3, v0 + 5), (k * 6.25 + 6, v0 + 9)], cols[(i + 1) % 4] + (230,))


def s_rainbow(d, t, P, rnd):
    clouds(d, t, rnd, 5, (255, 255, 255, 230), 8, 50)
    cols = [(255, 70, 70), (255, 160, 50), (255, 225, 60), (90, 200, 100), (70, 150, 255), (150, 100, 230)]
    for i, c in enumerate(cols):
        circ(d, t, 50, 78, 44 - i * 4.2, None, c + (255,), 4)
    sun(d, t, P, 86, 12, 5)
    for i, (u, v) in enumerate(((16, 18), (84, 40), (26, 46))):
        col = cols[(i * 2) % 6]
        ell(d, t, u, v, 5, 6.5, col + (255,)); line(d, t, [(u, v + 6.5), (u + 1, v + 20)], P.dk + (255,), 1)
    hills(d, t, rnd, 90, 3, (90, 190, 100, 255))



def s_weather(d, t, P, rnd):
    sun(d, t, P, 78, 18, 9)
    for u, v, r in ((36, 40, 14), (52, 34, 17), (66, 42, 13), (46, 46, 15), (58, 48, 12)):
        circ(d, t, u, v, r, (255, 255, 255, 245))
    poly(d, t, [(48, 52), (42, 68), (50, 68), (44, 88), (60, 62), (52, 62), (58, 52)], P.ac + (255,))
    for _ in range(26):
        u, v = rnd.uniform(24, 76), rnd.uniform(56, 92)
        line(d, t, [(u, v), (u - 1.6, v + 5)], P.lt + (220,), 1.4)


def s_dino(d, t, P, rnd):
    sun(d, t, P, 78, 18, 8); hills(d, t, rnd, 82, 3, P.mid + (255,))
    ell(d, t, 52, 62, 22, 11, P.dk + (255,))
    poly(d, t, [(36, 56), (28, 22), (36, 20), (46, 52)], P.dk + (255,)); ell(d, t, 26, 20, 6, 4, P.dk + (255,))
    poly(d, t, [(70, 58), (96, 74), (70, 68)], P.dk + (255,))
    for u in (38, 46, 58, 66):
        rect(d, t, u, 66, u + 4, 88, P.dk + (255,))
    circ(d, t, 24, 19, .9, P.lt + (255,))
    for _ in range(5):
        poly(d, t, [(rnd.uniform(40, 66), 52), (rnd.uniform(40, 66) + 2, 47), (rnd.uniform(40, 66) + 4, 52)], P.ac + (255,))


def s_flag(d, t, P, rnd):
    stars(d, t, P, rnd, 24, 60) if P.mode == "dark" else clouds(d, t, rnd, 3)
    hills(d, t, rnd, 80, 4, P.mid + (255,))
    rect(d, t, 28, 14, 30, 88, P.dk + (255,)); circ(d, t, 29, 12, 2.2, P.ac + (255,))
    pts_top = [(30 + k * 5, 18 + 2.6 * math.sin(k * .9)) for k in range(0, 15)]
    poly(d, t, pts_top + [(x, y + 16) for x, y in reversed(pts_top)], (220, 40, 40, 255))
    pts_b = [(30 + k * 5, 34 + 2.6 * math.sin(k * .9)) for k in range(0, 15)]
    poly(d, t, pts_b + [(x, y + 16) for x, y in reversed(pts_b)], (250, 250, 250, 255))
    for a in (-24, 24):
        pts = rot([(78, 40), (80, 40), (80, 94), (79, 98), (78, 94)], 79, 70, a)
        d.polygon([(x / 100 * t.w, y / 100 * t.h) for x, y in pts], fill=P.dk + (255,))


def s_burst(d, t, P, rnd, text="WOW!"):
    for u in range(0, 100, 5):
        for v in range(0, 100, 5):
            circ(d, t, u + (2.5 if (v // 5) % 2 else 0), v, 1.4 * (1 - v / 130), P.lt + (70,))
    pts = []
    for k in range(32):
        a = k * math.pi / 16
        r = 38 if k % 2 == 0 else 24
        pts.append((50 + r * math.cos(a), 44 + r * math.sin(a) * t.w / t.h))
    poly(d, t, pts, P.ac + (255,), P.dk + (255,))
    glyph(d, t, text, 50, 44, 46, P.dk + (255,), "sans")


def s_bars(d, t, P, rnd):
    for i, h in enumerate((22, 34, 28, 48, 60, 78)):
        rect(d, t, 10 + i * 14, 88 - h, 20 + i * 14, 88, (P.lt if i % 2 else P.ac) + (255,), 1)
    line(d, t, [(10, 70), (30, 52), (48, 60), (66, 34), (90, 12)], P.lt + (255,), 3)
    poly(d, t, [(90, 12), (80, 14), (88, 22)], P.lt + (255,)); rect(d, t, 6, 88, 94, 90, P.lt + (200,))


def s_coins(d, t, P, rnd):
    for u, n in ((24, 3), (44, 6), (64, 4), (80, 2)):
        for k in range(n):
            v = 84 - k * 5.2
            ell(d, t, u, v, 9, 3.2, P.ac + (255,), P.dk + (255,), 1); rect(d, t, u - 9, v - 5.2, u + 9, v, P.ac + (255,)); ell(d, t, u, v - 5.2, 9, 3.2, P.lt + (255,), P.dk + (255,), 1)
    glyph(d, t, "$", 52, 22, 70, P.lt + (255,), "serif")


def s_diamond(d, t, P, rnd):
    for r in (46, 34):
        circ(d, t, 50, 46, r, P.lt + (20,))
    top = [(26, 36), (74, 36), (50, 36)]
    poly(d, t, [(26, 36), (38, 22), (62, 22), (74, 36)], P.lt + (255,), P.dk + (255,)); poly(d, t, [(26, 36), (74, 36), (50, 78)], P.ac + (255,), P.dk + (255,))
    for pts in ([(38, 22), (44, 36), (50, 22)], [(62, 22), (56, 36), (50, 22)], [(44, 36), (50, 78), (56, 36)]):
        poly(d, t, pts, P.lt + (150,), P.dk + (255,))
    for _ in range(14):
        u, v = rnd.uniform(8, 92), rnd.uniform(8, 90); line(d, t, [(u - 2, v), (u + 2, v)], P.lt + (230,), 1); line(d, t, [(u, v - 2), (u, v + 2)], P.lt + (230,), 1)


def s_factory(d, t, P, rnd):
    clouds(d, t, rnd, 3, P.mid + (90,), 4, 30)
    for u in (22, 40, 58):
        rect(d, t, u, 40, u + 7, 80, P.dk)
        for k in range(3):
            circ(d, t, u + 3.5 + k * 3, 34 - k * 9, 4 + k * 1.5, P.mid + (150,))
    rect(d, t, 10, 62, 90, 90, P.dk)
    for k in range(5):
        poly(d, t, [(10 + k * 16, 62), (10 + k * 16, 52), (26 + k * 16, 62)], P.dk)
    for u in range(16, 86, 11):
        rect(d, t, u, 70, u + 6, 78, P.ac + (230,))
    gear(d, t, 82, 36, 9, 8, P.ac + (255,), P.top + (255,))


def s_portrait(d, t, P, rnd, var="man"):
    ell(d, t, 50, 46, 38, 40, P.lt + (60,), P.ac + (255,), 3)
    circ(d, t, 50, 33, 11, P.dk + (255,)); poly(d, t, [(20, 82), (24, 62), (36, 54), (50, 60), (64, 54), (76, 62), (80, 82)], P.dk + (255,))
    if var == "man":
        poly(d, t, [(36, 28), (50, 14), (64, 28), (60, 24), (40, 24)], P.dk + (255,))
    for cu, cv in ((8, 6), (92, 6), (8, 86), (92, 86)):
        circ(d, t, cu, cv, 2.4, P.ac + (255,))
    for k in range(10):
        a = k * math.pi / 5
        circ(d, t, 50 + 40 * math.cos(a), 46 + 42 * math.sin(a) * t.w / t.h * .96, 1.2, P.ac + (255,))


def s_abstract(d, t, P, rnd):
    for _ in range(14):
        circ(d, t, rnd.uniform(0, 100), rnd.uniform(0, 100), rnd.uniform(6, 28), (rnd.choice((P.ac, P.lt, P.mid, P.dk))) + (rnd.randint(60, 150),))


def s_math(d, t, P, rnd, text="+−×÷π√"):
    syms = list(text)
    for i, ch in enumerate(syms):
        u, v = 22 + (i % 3) * 28, 24 + (i // 3) * 34
        circ(d, t, u, v, 12.5, (P.ac if (i + i // 3) % 2 == 0 else P.lt) + (255,))
        glyph(d, t, ch, u, v, 40, P.dk + (255,), "serif")


# ============================================================ PEMILIHAN ADEGAN
RULES = [  # (kata kunci pada judul+deskripsi, adegan, varian)
    (("moby",), "ship", "whale"), (("twenty thousand",), "ship", "sub"),
    (("treasure island", "gulliver", "voyage of the beagle", "huckleberry", "monte cristo", "around the world", "perahu", "heart of darkness"), "ship", "ship"),
    (("dracula", "hikayat amir", "vampir"), "castle", "castle"), (("frankenstein",), "castle", "lightning"),
    (("jane eyre", "wuthering", "hound", "baskerville"), "castle", "manor"), (("jekyll", "dorian"), "skyline", "london"),
    (("oliver twist", "great expectations", "tale of two cities", "david copperfield", "pepys", "sherlock", "scarlet", "sign of the four"), "skyline", "london"),
    (("crime and punishment", "brothers karamazov", "anna karenina", "war and peace"), "skyline", "domes"),
    (("heidi", "call of the wild", "beyond good", "zarathustra", "mountain"), "mountains", "sun"),
    (("jungle", "kipling", "rimba"), "forest", "jungle"), (("wind in the willows", "robin", "forest"), "forest", "pine"),
    (("pride and prejudice", "emma", "persuasion", "tess", "secret garden", "anne of green", "little women", "little princess", "boenga roos"), "flowers", "garden"),
    (("time machine",), "space", "clock"), (("war of the worlds", "invisible man"), "space", "tripod"), (("princess of mars",), "space", "mars"),
    (("railway", "train"), "train", None), (("alice", "through the looking"), "cards", "alice"), (("looking-glass",), "cards", "chess"),
    (("wizard of oz",), "oz", None), (("peter pan",), "moonship", None), (("fairy", "grimm", "andersen", "pinocchio", "cinderella"), "fairy", None),
    (("musketeers", "art of war", "peloponnesian", "gallic", "grant", "caesar"), "swords", "swords"), (("don quixote",), "swords", "windmill"),
    (("christmas",), "lantern", None), (("histories", "twelve caesars", "republic", "symposium", "phaedo", "apology", "nicomachean", "ethics", "analects", "polit"), "temple", "laurel"),
    (("marco polo", "travels", "compass", "voyage"), "compass", None), (("ips", "sosial", "geografi"), "globe", None),
    (("relativity", "atom", "physics", "fisika", "feynman", "newtonian"), "atom", None), (("opticks",), "prism", None), (("candle",), "candle", None),
    (("dialogues concerning", "astronomy", "galileo"), "telescope", None), (("origin of species", "descent of man", "biology", "biologi", "microbiology", "concepts of biology"), "dna", "cell"),
    (("anatomy", "physiology"), "heart", None), (("chemistry", "kimia", "organic"), "hex", None), (("calculus", "calculus made easy"), "graph", "curve"), (("statistics", "stats"), "graph", "bell"),
    (("elements (euclid)",), "temple", "greek"), (("neural", "deep learning"), "network", "neural"), (("beej", "network"), "network", "net"),
    (("data structures", "algorithms", "open data"), "tree", None), (("operating systems", "gears", "scientific management", "factory"), "gears", None),
    (("lotus", "dhammapada"), "lotus", None), (("tao te ching",), "yinyang", None), (("analects", "konfusius"), "bamboo", None),
    (("koran", "quran"), "star8", None), (("bible", "imitation of christ", "confessions", "pensées"), "openbook", None),
    (("utilitarianism", "on liberty", "leviathan", "utopia"), "scales", None), (("kawung",), "kawung", None),
    (("parang",), "parang", None), (("candi", "pararaton", "negarakertagama", "sutasoma", "arjunawiwaha", "majapahit", "babad"), "candi", None),
    (("serat", "wedhatama", "kalatidha", "centhini", "gunungan"), "gunungan", None), (("syair perahu", "tuhfat", "bustanus"), "perahu", None),
    (("azab", "ulos"), "ulos", None), (("communist manifesto", "factory"), "factory", None), (("acres of diamonds",), "diamond", None),
    (("wealth of nations", "rich dad", "economics"), "coins", None), (("up from slavery", "souls of black", "slave"), "mountains", "sun"),
    (("komik", "comic"), "burst", None), (("matematika asyik",), "burst", None), (("terminal", "command line", "linux", "missing semester", "shell"), "terminal", None),
    (("self-help", "ladder"), "bars", None), (("rainbow", "laskar pelangi"), "rainbow", None),
]
RULES = [
    (("memoirs of u. s. grant", "grant"), "portrait", "man"), (("gallic",), "temple", "laurel"),
    (("filosofi teras",), "temple", "laurel"), (("sapiens",), "compass", None), (("the prince",), "cards", "chess"),
    (("franklin", "douglass", "story of my life"), "portrait", "man"), (("dunia sophie",), "openbook", None),
    (("sherlock", "study in scarlet", "sign of the four"), "magnifier", None), (("dorian gray",), "portrait", "man"),
    (("jekyll",), "skyline", "london"), (("oliver twist",), "skyline", "plain"), (("great expectations",), "ship", "ship"),
    (("david copperfield", "tess of", "emma"), "flowers", "garden"), (("tale of two cities",), "skyline", "domes"),
    (("crime and punishment",), "scales", None), (("brothers karamazov", "anne of green"), "forest", "pine"),
    (("les mis",), "candle", None), (("anna karenina",), "train", None), (("war and peace",), "swords", "swords"),
    (("little women", "christmas carol"), "lantern", None), (("black beauty", "call of the wild"), "mountains", "sun"),
    (("middlemarch",), "forest", "pine"), (("metamorphosis",), "skyline", "plain"),
    (("tubuh manusia",), "heart", None), (("dinosaurus",), "dino", None), (("cuaca",), "weather", None), (("pahlawan",), "flag", None),
    (("matematika asyik",), "math", None), (("tata surya",), "space", "planet"), (("ensiklopedia sains",), "globe", None),
    (("cerita rakyat",), "fairy", None), (("bahasa inggris seru",), "burst", None), (("ekosistem",), "ship", "whale"),
] + RULES
POOLS = {
    "Novel Gratis": ["mountains", "flowers", "skyline", "forest", "castle", "ship", "abstract"],
    "Sastra Indonesia Klasik": ["kawung", "parang", "candi", "gunungan", "perahu", "ulos"],
    "Sains & Teknologi": ["atom", "telescope", "dna", "hex", "graph", "prism"],
    "Pemrograman & Komputer": ["terminal", "symbol", "tree", "network", "gears", "symbol"],
    "Sejarah & Biografi": ["temple", "compass", "portrait", "skyline", "swords", "globe"],
    "Bisnis & Pengembangan Diri": ["bars", "coins", "gears", "diamond", "factory"],
    "Agama & Filsafat": ["openbook", "lotus", "star8", "scales", "mountains", "bamboo", "yinyang"],
    "Anak-anak & Komik Edukasi": ["rainbow", "fairy", "flowers", "moonship", "forest", "rainbow"],
}
SYMBOLS = {"python": ("🐍", None), "javascript": ("JS", 90), "java ": ("{ }", 110), "rust": ("&", 130), "haskell": ("λ", 150),
           "sicp": ("λ", 150), "structure and interpretation": ("λ", 150), "how to design": ("λ", 150), "html": ("</>", 90),
           "django": ("dj", 110), "interpreters": ("{ }", 110), "crafting": ("{ }", 110), "git": ("git", 100), "web": ("</>", 90)}
SCENES = {"ship": s_ship, "castle": s_castle, "mountains": s_mountains, "skyline": s_skyline, "forest": s_forest, "flowers": s_flowers,
          "space": s_space, "train": s_train, "cards": s_cards, "oz": s_oz, "moonship": s_moonship, "fairy": s_fairy, "magnifier": s_magnifier,
          "swords": s_swords, "lantern": s_lantern, "temple": s_temple, "compass": s_compass, "globe": s_globe, "atom": s_atom, "prism": s_prism,
          "candle": s_candle, "telescope": s_telescope, "dna": s_dna, "hex": s_hex, "graph": s_graph, "heart": s_heart, "terminal": s_terminal,
          "symbol": s_symbol, "tree": s_tree, "network": s_network, "gears": s_gears, "lotus": s_lotus, "yinyang": s_yinyang, "bamboo": s_bamboo,
          "star8": s_star8, "openbook": s_openbook, "scales": s_scales, "kawung": s_kawung, "parang": s_parang, "candi": s_candi,
          "gunungan": s_gunungan, "perahu": s_perahu, "ulos": s_ulos, "rainbow": s_rainbow, "burst": s_burst, "bars": s_bars, "coins": s_coins,
          "weather": s_weather, "dino": s_dino, "flag": s_flag, "math": s_math, "diamond": s_diamond, "factory": s_factory, "portrait": s_portrait, "abstract": s_abstract}
_counter = {}


def choose_scene(b):
    text = (b["title"] + " " + b.get("description", "")).lower()
    title = b["title"].lower()
    PROG = {"automate": ("gears", {}), "python for everybody": ("network", {"var": "net"}), "a byte of python": ("terminal", {}),
            "dive into python": ("tree", {}), "the python tutorial": ("openbook", {}), "pro git": ("network", {"var": "net"})}
    if b["cat"] == "Pemrograman & Komputer":
        for k, v in PROG.items():
            if k in title:
                return v
        for k, (g, sz) in SYMBOLS.items():
            if k in title:
                return "symbol", {"text": g if g != "🐍" else "Py", "size": sz or 110}
    for kws, scene, var in RULES:
        if any(k in title for k in kws):
            return scene, ({"var": var} if var else {})
    for kws, scene, var in RULES:
        if any(k in text for k in kws if len(k) > 5):
            return scene, ({"var": var} if var else {})
    pool = POOLS.get(b["cat"], ["abstract"])
    i = _counter.get(b["cat"], 0)
    _counter[b["cat"]] = i + 1
    scene = pool[i % len(pool)]
    if scene == "symbol":
        return "symbol", {"text": ["{ }", "</>", ">_", "λ", "01", "#!"][i % 6], "size": 110}
    return scene, {}


# =============================================================== TATA LETAK
def art_image(w, h, P, scene, kw, rnd):
    top, bot = P.top, P.bot
    mask = Image.linear_gradient("L").resize((w, h))
    img = Image.composite(Image.new("RGB", (w, h), bot), Image.new("RGB", (w, h), top), mask).convert("RGBA")
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    SCENES[scene](ImageDraw.Draw(layer, "RGBA"), T(w, h), P, rnd, **kw)
    return Image.alpha_composite(img, layer)


def wrap(d, text, fnt, width):
    lines, cur = [], ""
    for word in text.split():
        test = (cur + " " + word).strip()
        if d.textlength(test, font=fnt) <= width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    return lines + [cur] if cur else lines


def fit(d, text, kind, width, max_h, size, min_size=22, spacing=1.12):
    while True:
        f = font(kind, size * S)
        lines = wrap(d, text, f, width)
        if (len(lines) * size * S * spacing <= max_h and all(d.textlength(l, font=f) <= width for l in lines)) or size <= min_size:
            return f, lines, size
        size -= 2


def draw_block(d, lines, f, x, y, size, fill, align="left", width=0, spacing=1.12):
    for ln in lines:
        xx = x if align == "left" else x + (width - d.textlength(ln, font=f)) / 2
        d.text((xx, y), ln, font=f, fill=fill)
        y += size * S * spacing
    return y


def paste_masked(base, art, pos, shape):
    mask = Image.new("L", art.size, 0)
    md = ImageDraw.Draw(mask)
    w, h = art.size
    if shape == "arch":
        md.rounded_rectangle([0, 0, w, h], radius=w // 2 - 2, fill=255)
        md.rectangle([0, h // 2, w, h], fill=255)
    elif shape == "circle":
        md.ellipse([0, 0, w - 1, h - 1], fill=255)
    elif shape == "round":
        md.rounded_rectangle([0, 0, w - 1, h - 1], radius=24 * S, fill=255)
    else:
        md.rectangle([0, 0, w, h], fill=255)
    base.paste(art, pos, mask)


def render(b, scene, kw, P, layout, rnd, tkind):
    img = Image.new("RGBA", (W, H), P.paper + (255,))
    d = ImageDraw.Draw(img, "RGBA")
    title, author = b["title"], b["author"] if len(b["author"]) < 34 else b["author"][:32] + "…"
    cat = b["cat"].split(" ")[0].upper()
    m = 38 * S
    sub = P.sub + (255,)
    if layout == "bottom":
        ah = int(H * .62)
        paste_masked(img, art_image(W, ah, P, scene, kw, rnd), (0, 0), "rect")
        d.rectangle([0, ah, W, H], fill=P.paper + (255,)); d.rectangle([0, ah, W, ah + 7 * S], fill=P.ac + (255,))
        f, lines, sz = fit(d, title, tkind, W - 2 * m, H - ah - 120 * S, 40)
        y = draw_block(d, lines, f, m, ah + 26 * S, sz, P.ink + (255,))
        d.text((m, H - 52 * S), author, font=font("italic", 17 * S), fill=sub)
    elif layout == "band":
        paste_masked(img, art_image(W, H, P, scene, kw, rnd), (0, 0), "rect")
        bh = int(H * .26)
        by = int(H * .60)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.rectangle([0, by, W, by + bh], fill=P.paper + (232,)); od.rectangle([0, by, W, by + 4 * S], fill=P.ac + (255,)); od.rectangle([0, by + bh - 4 * S, W, by + bh], fill=P.ac + (255,))
        od.rectangle([0, int(H * .88), W, H], fill=P.paper + (225,))
        img = Image.alpha_composite(img, ov); d = ImageDraw.Draw(img, "RGBA")
        f, lines, sz = fit(d, title, tkind, W - 2 * m, bh - 36 * S, 38)
        th = len(lines) * sz * S * 1.12
        draw_block(d, lines, f, m, by + (bh - th) / 2, sz, P.ink + (255,), "center", W - 2 * m)
        d.text((W / 2, H - 38 * S), author, font=font("italic", 17 * S), fill=sub, anchor="mm")
    elif layout == "top":
        f, lines, sz = fit(d, title, tkind, W - 2 * m, int(H * .22), 38)
        y = draw_block(d, lines, f, m, 40 * S, sz, P.ink + (255,), "center", W - 2 * m)
        d.rectangle([W / 2 - 30 * S, y + 4 * S, W / 2 + 30 * S, y + 7 * S], fill=P.ac + (255,))
        top = int(y + 22 * S); ah = H - top - 70 * S
        paste_masked(img, art_image(W - 2 * 40 * S, ah, P, scene, kw, rnd), (40 * S, top), "round")
        d.text((W / 2, H - 36 * S), author, font=font("italic", 18 * S), fill=sub, anchor="mm")
    elif layout == "arch":
        d.rectangle([14 * S, 14 * S, W - 14 * S, H - 14 * S], outline=P.ac + (255,), width=2 * S); d.rectangle([22 * S, 22 * S, W - 22 * S, H - 22 * S], outline=P.ac + (140,), width=1 * S)
        aw, ah = int(W * .70), int(H * .50)
        paste_masked(img, art_image(aw, ah, P, scene, kw, rnd), ((W - aw) // 2, 52 * S), "arch")
        f, lines, sz = fit(d, title, tkind, W - 2 * m - 10 * S, int(H * .22), 34)
        y = draw_block(d, lines, f, m + 5 * S, 52 * S + ah + 24 * S, sz, P.ink + (255,), "center", W - 2 * m - 10 * S)
        d.text((W / 2, H - 52 * S), author, font=font("italic", 17 * S), fill=sub, anchor="mm")
    else:  # circle
        r = int(W * .40)
        d.ellipse([W / 2 - r - 8 * S, 44 * S - 8 * S, W / 2 + r + 8 * S, 44 * S + 2 * r + 8 * S], outline=P.ac + (255,), width=3 * S)
        paste_masked(img, art_image(2 * r, 2 * r, P, scene, kw, rnd), (int(W / 2 - r), 44 * S), "circle")
        yy = 44 * S + 2 * r + 30 * S
        f, lines, sz = fit(d, title, tkind, W - 2 * m, H - yy - 90 * S, 34)
        draw_block(d, lines, f, m, yy, sz, P.ink + (255,), "center", W - 2 * m)
        d.text((W / 2, H - 42 * S), author, font=font("italic", 17 * S), fill=sub, anchor="mm")
    if layout in ("bottom", "band"):
        d.text((W - 24 * S, 22 * S), cat, font=font("light", 12 * S), fill=P.lt + (200,), anchor="ra")
    # punggung buku + tekstur kertas
    sp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sp)
    for i in range(18 * S):
        sd.line([(i, 0), (i, H)], fill=(0, 0, 0, int(90 * (1 - i / (18 * S)))))
    sd.line([(20 * S, 0), (20 * S, H)], fill=(255, 255, 255, 40), width=S)
    img = Image.alpha_composite(img, sp)
    return img.convert("RGB").resize((W // S, H // S), Image.LANCZOS)


# ============================================================ BUKU PELAJARAN
JENJANG = {"SD": (.09, .55, "dark"), "SMP": (.50, .10, "dark"), "SMA": (.72, .12, "dark")}
MAPEL = {"Matematika": ("math", "+−×÷π√"), "Bahasa Indonesia": ("text", "Aa"), "IPAS": ("globe", None), "Ilmu Pengetahuan Alam": ("atom", None),
         "Ilmu Pengetahuan Sosial": ("globe", None), "Bahasa Inggris": ("text", "ABC"), "Informatika": ("terminal", None), "Fisika": ("atom", None),
         "Kimia": ("hex", None), "Biologi": ("dna", None)}


def render_textbook(b, idx):
    m = re.search(r"(SD|SMP|SMA) Kelas (\d+)", b["title"])
    jenjang, kelas = m.group(1), m.group(2)
    mapel = next((k for k in MAPEL if b["title"].startswith(k)), "Matematika")
    kind, txt = MAPEL[mapel]
    h, ah, mode = JENJANG[jenjang]
    mode = "dark" if int(kelas) % 2 else "light"        # kelas ganjil gelap, genap terang
    h = (h + (int(kelas) % 7) * .06 + (len(b['title']) % 5) * .02) % 1
    P = Pal(h, ah, mode, idx)
    rnd = random.Random(slugify(b["title"]))
    img = Image.new("RGBA", (W, H), P.paper + (255,)); d = ImageDraw.Draw(img, "RGBA")
    d.rectangle([0, 0, W, int(H * .13)], fill=P.ac + (255,))
    d.text((m := 32 * S, 26 * S), "BUKU SEKOLAH ELEKTRONIK", font=font("sansc", 13 * S), fill=P.dk + (255,))
    d.text((m, 50 * S), f"{jenjang} · KURIKULUM MERDEKA", font=font("light", 12 * S), fill=P.dk + (255,))
    # lencana kelas
    cx, cy, r = W - 70 * S, int(H * .13), 46 * S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=P.paper + (255,), outline=P.ac + (255,), width=5 * S)
    d.text((cx, cy - 8 * S), kelas, font=font("serif", 46 * S), fill=P.ink + (255,), anchor="mm"); d.text((cx, cy + 26 * S), "KELAS", font=font("sans", 11 * S), fill=P.sub + (255,), anchor="mm")
    # ikon
    ay, ah_ = int(H * .24), int(H * .34)
    art = Image.new("RGBA", (W - 2 * m, ah_), (0, 0, 0, 0)); ad = ImageDraw.Draw(art, "RGBA"); t = T(*art.size)
    kn = int(kelas)
    rad = (22, 70, 130)[kn % 3] * S                    # bentuk bingkai ikon bergantian
    ad.rounded_rectangle([0, 0, art.size[0] - 1, art.size[1] - 1], radius=rad, fill=P.top + (255,))
    for _ in range(10):  # hiasan latar unik per kelas
        circ(ad, t, rnd.uniform(0, 100), rnd.uniform(0, 100), rnd.uniform(3, 12), (P.lt if rnd.random() < .5 else P.ac) + (50,))
    if kind == "math":
        allsym = "+−×÷π√∑%∞≠≤∫"
        pick = "".join(allsym[(kn * 2 + i) % len(allsym)] for i in range(6))
        s_math(ad, t, P, rnd, pick)
    elif kind == "text":
        txt = ("Aa Bb Cc Dd Ee Ff Gg Hh Ii Jj Kk Ll".split() if mapel == "Bahasa Indonesia" else ["ABC", "Hi!", "Yes", "Go!", "Why?", "OK", "Hello", "Fun", "Zoo", "Cat", "Sun", "Joy"])[(kn + len(b["title"])) % 12]
        circ(ad, t, 50, 46, 34, P.ac + (255,)); glyph(ad, t, txt, 50, 46, 78 if len(txt) < 3 else (56 if len(txt) < 5 else 42), P.dk + (255,), "serif")
        poly(ad, t, [(30, 74), (40, 66), (44, 78)], P.ac + (255,))
        glyph(ad, t, "“", 80, 20, 70, P.lt + (255,), "serif")
    else:
        SCENES[kind](ad, t, P, rnd)
    clip = Image.new("L", art.size, 0); ImageDraw.Draw(clip).rounded_rectangle([0, 0, art.size[0] - 1, art.size[1] - 1], radius=rad, fill=255)
    art.putalpha(Image.composite(art.getchannel("A"), Image.new("L", art.size, 0), clip))
    img.alpha_composite(art, (m, ay)); d = ImageDraw.Draw(img, "RGBA")
    ty = ay + ah_ + 22 * S
    f, lines, sz = fit(d, mapel.upper() if len(mapel) < 18 else mapel, "serif", W - 2 * m, int(H * .13), 34)
    ty = draw_block(d, lines, f, m, ty, sz, P.ink + (255,))
    d.rectangle([m, ty + 4 * S, m + 60 * S, ty + 8 * S], fill=P.ac + (255,))
    grades = {"SD": range(1, 7), "SMP": range(7, 10), "SMA": range(10, 13)}[jenjang]
    bw, gap = 38 * S, 8 * S
    gx, gy = m, H - 100 * S
    d.text((gx, gy - 22 * S), "TINGKAT KELAS", font=font("sans", 10 * S), fill=P.sub + (255,))
    for g_ in grades:
        on = g_ == kn
        d.rounded_rectangle([gx, gy, gx + bw, gy + 30 * S], radius=8 * S, fill=(P.ac if on else P.mid) + (255 if on else 120,))
        d.text((gx + bw / 2, gy + 15 * S), str(g_), font=font("sans", 16 * S), fill=(P.dk if on else P.sub) + (255,), anchor="mm")
        gx += bw + gap
    d.text((m, H - 56 * S), "Kemendikbudristek", font=font("italic", 16 * S), fill=P.sub + (255,))
    d.text((m, H - 36 * S), "Tim Penulis · Buku Teks Utama", font=font("light", 12 * S), fill=P.sub + (255,))
    sp = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sp)
    for i in range(18 * S):
        sd.line([(i, 0), (i, H)], fill=(0, 0, 0, int(90 * (1 - i / (18 * S)))))
    img = Image.alpha_composite(img, sp)
    return img.convert("RGB").resize((W // S, H // S), Image.LANCZOS), ("textbook", kind, jenjang, kelas, mapel)


# ================================================================== UTAMA
LAYOUTS = ["bottom", "band", "top", "arch", "circle"]
TFONTS = {"Novel Gratis": ["serif", "serifc"], "Sastra Indonesia Klasik": ["serif", "serifc"], "Sejarah & Biografi": ["serif", "serifc"],
          "Agama & Filsafat": ["serif", "serifc"], "Sains & Teknologi": ["sans", "sansc"], "Pemrograman & Komputer": ["mono", "sansc"],
          "Bisnis & Pengembangan Diri": ["sans", "sansc"], "Anak-anak & Komik Edukasi": ["sans", "sans"]}


def build_all():
    """Pilih (tata letak, palet) untuk tiap buku: buku dengan ilustrasi sama dipaksa beda tata letak & warna,
    dan palet disebar merata ke seluruh koleksi."""
    results, scene_used, pal_count = {}, {}, {i: 0 for i in range(len(PAL_DEF))}
    for idx, b in enumerate(BOOKS):
        slug = slugify(b["title"])
        if b["cat"] == "Buku Pelajaran" and re.search(r"(SD|SMP|SMA) Kelas \d+", b["title"]):
            results[slug] = render_textbook(b, idx)
            continue
        rnd = random.Random(slug)
        scene, kw = choose_scene(b)
        skey = scene
        dark_only = scene in ("castle", "space", "moonship", "lantern", "atom", "prism", "telescope", "network", "terminal", "symbol", "tree", "gunungan", "candle")
        best, best_score = None, 1e9
        for layout in LAYOUTS:
            for pi, (h, ah, mode) in enumerate(PAL_DEF):
                if dark_only and mode == "light":
                    continue
                score = rnd.random() * 2 + pal_count[pi] * 3
                for (ul, upi) in scene_used.get(skey, []):
                    if ul == layout:
                        score += 100                      # tata letak sama pada ilustrasi sama
                    hd = abs(PAL_DEF[upi][0] - h)
                    hd = min(hd, 1 - hd)
                    if upi == pi:
                        score += 200                      # palet sama
                    elif hd < .10 and PAL_DEF[upi][2] == mode:
                        score += 60                       # warna terlalu berdekatan
                if score < best_score:
                    best, best_score = (layout, pi), score
        layout, pi = best
        scene_used.setdefault(skey, []).append(best)
        pal_count[pi] += 1
        h, ah, mode = PAL_DEF[pi]
        P = Pal(h, ah, mode, pi)
        tk = rnd.choice(TFONTS.get(b["cat"], ["serif"]))
        results[slug] = (render(b, scene, kw, P, layout, rnd, tk), (scene, layout, pi))
    return results


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    res = build_all()
    for slug, (img, _) in res.items():
        img.save(os.path.join(OUT, slug + ".png"), optimize=True)
    print(f"{len(res)} sampul unik dibuat di {OUT}")
