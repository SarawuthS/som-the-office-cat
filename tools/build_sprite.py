"""Build hooks/sprite.ts for the som-the-office-cat mod from assets/office-cat.png.

Usage: python3 tools/build_sprite.py [--debug <dir>]
  Writes ../hooks/sprite.ts (128x128 pixel SVG body + per-pose SMIL overlays).
  --debug also writes one static SVG per pose (animations frozen visible) for checking placement.
"""
import os
import re
import sys

from PIL import Image

N = 128
COLORS = 48
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def base_paths():
    im = Image.open(os.path.join(ROOT, 'assets', 'office-cat.png')).convert('RGBA').resize((N, N), Image.BOX)
    q = im.convert('RGB').quantize(COLORS, method=Image.MEDIANCUT, dither=Image.NONE)
    pal, px, al = q.getpalette(), q.load(), im.getchannel('A').load()
    paths = {}
    for y in range(N):
        x = 0
        while x < N:
            c = px[x, y] if al[x, y] >= 128 else None
            w = 1
            while x + w < N and (px[x + w, y] if al[x + w, y] >= 128 else None) == c:
                w += 1
            if c is not None:
                paths.setdefault(c, []).append(f'M{x} {y}h{w}v1h-{w}z')
            x += w
    return ''.join(
        f'<path fill="#{pal[3*c]:02x}{pal[3*c+1]:02x}{pal[3*c+2]:02x}" d="{"".join(d)}"/>'
        for c, d in paths.items()
    )


def blink_anim(dur='4.5s'):
    return (f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;0.94;0.98" '
            f'dur="{dur}" calcMode="discrete" repeatCount="indefinite"/>')


def flash(dur, begin='0s', values='1;0'):
    return (f'<animate attributeName="opacity" values="{values}" dur="{dur}" begin="{begin}" '
            f'calcMode="discrete" repeatCount="indefinite"/>')


# Eye boxes in the 128 grid (inside the lenses): left x55-62, right x74-81, y35-41.
CLOSED = ('<rect x="55" y="35" width="8" height="6" fill="#f0bf82"/>'
          '<rect x="74" y="35" width="8" height="6" fill="#f0bf82"/>'
          '<rect x="56" y="38" width="6" height="1" fill="#2b2325"/>'
          '<rect x="75" y="38" width="6" height="1" fill="#2b2325"/>')
HAPPY = ('<rect x="55" y="35" width="8" height="6" fill="#f0bf82"/>'
         '<rect x="74" y="35" width="8" height="6" fill="#f0bf82"/>'
         '<path fill="#2b2325" d="M56 39h1v-1h1v-1h2v1h1v1h1v1h-1v-1h-1v-1h-2v1h-1v1h-1z'
         'M75 39h1v-1h1v-1h2v1h1v1h1v1h-1v-1h-1v-1h-2v1h-1v1h-1z"/>')
STEAM = ('<g fill="#c9ced6" opacity="0.9">'
         '<rect x="8" y="80" width="2" height="2"/><rect x="10" y="77" width="2" height="2"/>'
         '<rect x="8" y="74" width="2" height="2"/><rect x="12" y="81" width="1" height="1"/>'
         '<animateTransform attributeName="transform" type="translate" values="0 0;1 -1;0 -2;-1 -1" '
         'dur="1.6s" calcMode="discrete" repeatCount="indefinite"/></g>')

# Drawn above every pose, so blinking also covers redrawn eyes (think).
COMMON = f'{STEAM}<g opacity="0">{CLOSED}{blink_anim()}</g>'


def sparkle(x, y, begin):
    return (f'<g fill="#f4c430" opacity="1"><rect x="{x}" y="{y-2}" width="1" height="5"/>'
            f'<rect x="{x-2}" y="{y}" width="5" height="1"/>{flash("0.8s", begin)}</g>')


def key(x, y, begin):
    return f'<rect x="{x}" y="{y}" width="3" height="1" fill="#acdbf5" opacity="0">{flash("0.6s", begin, "0;1")}</rect>'


def pixels():
    """The base picture as RGB tuples, None where transparent: [y][x]."""
    im = Image.open(os.path.join(ROOT, 'assets', 'office-cat.png')).convert('RGBA').resize((N, N), Image.BOX)
    q = im.convert('RGB').quantize(COLORS, method=Image.MEDIANCUT, dither=Image.NONE).convert('RGB')
    a = im.getchannel('A')
    return [[q.getpixel((x, y)) if a.getpixel((x, y)) >= 128 else None for x in range(N)] for y in range(N)]


def rle(cells):
    """{(x, y): rgb} -> one rect per run of same colour along a row."""
    out = []
    for y in sorted({y for _, y in cells}):
        xs = sorted(x for x, yy in cells if yy == y)
        i = 0
        while i < len(xs):
            x, c, w = xs[i], cells[(xs[i], y)], 1
            while i + w < len(xs) and xs[i + w] == x + w and cells[(x + w, y)] == c:
                w += 1
            out.append(f'<rect x="{x}" y="{y}" width="{w}" height="1" fill="#{c[0]:02x}{c[1]:02x}{c[2]:02x}"/>')
            i += w
    return ''.join(out)


def warm(c):
    return c is not None and c[0] > 140 and c[0] - c[2] > 50


def mask(px, box, pred):
    """Pixels in box matching pred, plus the dark outline pixels touching them."""
    x0, y0, x1, y1 = box
    m = {(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1) if pred(px[y][x])}
    ring = set()
    for x, y in m:
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            c = px[ny][nx]
            if x0 <= nx <= x1 and y0 <= ny <= y1 and (nx, ny) not in m and c is not None and sum(c) < 200:
                ring.add((nx, ny))
    return m | ring


def uncovered(px, m, dx, dy):
    """What shows where mask m was once it moves by (dx, dy): each pixel left
    bare is filled from the first pixel beyond the mask, looking against the
    motion. Bare pixels with only transparency beyond are left alone."""
    cells = {}
    for x, y in m:
        if (x - dx, y - dy) in m:
            continue
        sx, sy = x, y
        while (sx, sy) in m:
            sx, sy = sx - dx, sy - dy
        c = px[sy][sx]
        if c is not None:
            cells[(x, y)] = c
    return cells


def moved(px, m, dx, dy):
    """Mask m drawn shifted by (dx, dy) over its uncovered fill (for previews)."""
    cells = uncovered(px, m, dx, dy)
    cells.update({(x + dx, y + dy): px[y][x] for x, y in m})
    return cells


# Hands while thinking: right paw taps the keyboard, left paw slides the mouse.
RIGHT_PAW = (86, 80, 108, 97)
LEFT_PAW = (50, 90, 70, 106)  # paw only: moving the forearm smeared the sleeve and the sticky note
MOUSE = (48, 98, 72, 112)


def mouse_pred(c):
    return c is not None and not warm(c) and c[2] >= c[0] - 10


def hands():
    px = pixels()
    paw_r = mask(px, RIGHT_PAW, warm)
    hand_l = mask(px, LEFT_PAW, warm) | mask(px, MOUSE, mouse_pred)
    # One copy of each moving part, stepped by a discrete translate; under it,
    # the fill for each offset shows only while that offset does.
    show = lambda cells, values, dur: (f'<g opacity="0">{rle(cells)}<animate attributeName="opacity" '
                                       f'values="{values}" dur="{dur}" calcMode="discrete" repeatCount="indefinite"/></g>')
    step = lambda m, values, dur: (f'<g>{rle({c: px[c[1]][c[0]] for c in m})}<animateTransform attributeName="transform" '
                                   f'type="translate" values="{values}" dur="{dur}" calcMode="discrete" repeatCount="indefinite"/></g>')
    return (show(uncovered(px, paw_r, 0, -1), '0;1', '0.5s') + step(paw_r, '0 0;0 -1', '0.5s')
            + show(uncovered(px, hand_l, 1, 0), '0;1;0;1', '1.6s')
            + show(uncovered(px, hand_l, 2, 0), '0;0;1;0', '1.6s')
            + step(hand_l, '0 0;1 0;2 0;1 0', '1.6s'))


def look_right(dx=2):
    """Both eyes redrawn dx px to the right inside their lens boxes, so the cat looks at the monitor."""
    im = Image.open(os.path.join(ROOT, 'assets', 'office-cat.png')).convert('RGBA').resize((N, N), Image.BOX)
    q = im.convert('RGB').quantize(COLORS, method=Image.MEDIANCUT, dither=Image.NONE).convert('RGB')
    out = []
    for x0, x1 in ((55, 62), (74, 81)):
        for y in range(35, 42):
            row = [q.getpixel((x, y)) for x in range(x0, x1 + 1)]
            for i, c in enumerate([(0xfa, 0xd7, 0xa4)] * dx + row[:-dx]):
                out.append(f'<rect x="{x0 + i}" y="{y}" width="1" height="1" fill="#{c[0]:02x}{c[1]:02x}{c[2]:02x}"/>')
    return ''.join(out)


POSES = {
    'idle': '',
    'think': (
        '<g fill="#ffffff" stroke="#2e3245" stroke-width="1">'
        '<circle cx="41" cy="30" r="1.5"/><circle cx="35" cy="23" r="2.5"/>'
        '<ellipse cx="20" cy="12" rx="15" ry="9"/></g>'
        + ''.join(f'<rect x="{x}" y="11" width="3" height="3" fill="#2e3245" opacity="0">'
                  f'{flash("1.5s", b, "0;1;1")}</rect>'
                  for x, b in ((11, '0s'), (18, '0.5s'), (25, '1s')))
    ),
    'read': (
        '<g><circle cx="100" cy="28" r="7" fill="#acdbf5" fill-opacity="0.55" stroke="#494f5e" stroke-width="2"/>'
        '<rect x="97" y="24" width="2" height="2" fill="#ffffff"/>'
        '<path d="M105 33l7 7" stroke="#844820" stroke-width="3"/>'
        '<animateTransform attributeName="transform" type="translate" values="0 0;-3 2;0 3;3 2" '
        'dur="1.6s" calcMode="discrete" repeatCount="indefinite"/></g>'
    ),
    'edit': (
        ''.join(key(x, y, b) for x, y, b in ((70, 97, '0s'), (78, 99, '0.15s'), (86, 97, '0.3s'), (94, 99, '0.45s')))
        + '<g>' + ''.join(
            f'<rect x="42" y="{y}" width="{w}" height="1" fill="{c}">'
            f'<animate attributeName="width" values="0;{w};{w}" dur="2s" begin="{b}" calcMode="discrete" '
            f'repeatCount="indefinite"/></rect>'
            for y, w, c, b in ((119, 20, '#2d5fd1', '0s'), (121, 32, '#c8323a', '0.3s'),
                               (123, 26, '#3f8f4a', '0.6s'), (125, 14, '#2d5fd1', '0.9s'))) + '</g>'
    ),
    'bash': (
        '<rect x="38" y="117" width="58" height="11" fill="#14324a"/>'
        '<path fill="#8fe39b" d="M41 119h1v1h1v1h1v1h-1v1h-1v1h-1v-1h1v-1h1v-1h-1v-1h-1z"/>'
        '<rect x="47" y="123" width="4" height="1" fill="#8fe39b">' + flash('0.8s') + '</rect>'
        '<rect x="113" y="90" width="3" height="2" fill="#8fe39b">' + flash('0.5s') + '</rect>'
    ),
    'done': HAPPY + sparkle(40, 14, '0s') + sparkle(100, 10, '0.2s') + sparkle(108, 40, '0.4s') + sparkle(30, 44, '0.6s'),
}


# While working (think/read/edit/bash) the cat looks at the monitor and its
# hands move. One shared layer, under each pose's overlay, so the pane carries
# it once (~38k chars) instead of once per pose.
WORKING_POSES = ('think', 'read', 'edit', 'bash')


def main():
    base = base_paths()
    working = look_right() + hands()
    out = os.path.join(ROOT, 'hooks', 'sprite.ts')
    esc = lambda s: s.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
    lines = [
        '// Generated by tools/build_sprite.py from assets/office-cat.png; do not edit by hand.',
        "import type { Pose } from '../types'",
        f'const BASE = `{esc(base)}`',
        f'const COMMON = `{esc(COMMON)}`',
        f'const WORKING = `{esc(working)}`',
        'const POSES: Record<Pose, string> = {',
        *[f'  {k}: `{esc(v)}`,' for k, v in POSES.items()],
        '}',
        f'const OPEN = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {N} {N}" shape-rendering="crispEdges">`',
        '// The still picture, drawn once as an image.',
        'export const base = `${OPEN}${BASE}</svg>`',
        '// What moves for a pose, on a transparent canvas laid over the base.',
        'export const overlay = (pose: Pose) => `${OPEN}${POSES[pose]}${COMMON}</svg>`',
        '// Eyes on the monitor and moving hands, shown under the overlay while working.',
        'export const working = `${OPEN}${WORKING}</svg>`',
        f"export const isWorking = (pose: Pose) => {' || '.join(f'pose === {chr(39)}{p}{chr(39)}' for p in WORKING_POSES)}",
        '// Base and overlay in one picture (previews).',
        'export const sprite = (pose: Pose) =>',
        '  `${OPEN}${BASE}${isWorking(pose) ? WORKING : \'\'}${POSES[pose]}${COMMON}</svg>`',
        '',
    ]
    open(out, 'w').write('\n'.join(lines))
    wrap = lambda body: (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {N} {N}" '
                         f'shape-rendering="crispEdges">{body}</svg>')
    full = lambda k: base + (working if k in WORKING_POSES else '') + POSES[k] + COMMON
    sizes = {'base': len(wrap(base)), 'working': len(wrap(working)), **{k: len(wrap(v + COMMON)) for k, v in POSES.items()}}
    print('wrote', out, 'pane total chars', sum(sizes.values()), sizes)
    if '--debug' in sys.argv:
        d = sys.argv[sys.argv.index('--debug') + 1]
        os.makedirs(d, exist_ok=True)
        for k in POSES:
            s = wrap(full(k))
            s = re.sub(r'<animate[^>]*/>', '', s).replace('opacity="0"', 'opacity="1"')
            s = s.replace('<svg ', '<svg width="512" height="512" ', 1)
            open(os.path.join(d, f'pose-{k}.svg'), 'w').write(s)


if __name__ == '__main__':
    main()
