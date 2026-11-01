"""Build hooks/sprite.ts for the som-the-office-cat mod from a character file.

Usage: python3 tools/build_sprite.py [--character characters/som.json] [--debug <dir>]
  Writes ../hooks/sprite.ts (128x128 pixel SVG body + per-pose SMIL overlays).
  --character names the character file (picture, eyes, paws, overlay offsets);
    see "Make your own character" in the README. Defaults to Som.
  --debug also writes one static SVG per pose (animations frozen visible) for checking placement.
"""
import json
import os
import re
import sys

from PIL import Image

N = 128
COLORS = 48
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CHARACTER = (sys.argv[sys.argv.index('--character') + 1] if '--character' in sys.argv
             else os.path.join(ROOT, 'characters', 'som.json'))
CFG = json.load(open(CHARACTER))
IMAGE = os.path.join(ROOT, CFG['image'])
EYES = CFG['eyes']
SKIN, INK, LENS = EYES['skin'], EYES['ink'], EYES['lens']
EYE_XS = (EYES['left'][0], EYES['right'][0])
EYE_Y = EYES['left'][1]  # both eyes share a row
OFFSETS = CFG.get('offsets', {})


def shift(svg, part):
    """An overlay part moved by the character's offset for it (none for Som)."""
    dx, dy = OFFSETS.get(part, (0, 0))
    return svg if (dx, dy) == (0, 0) else f'<g transform="translate({dx} {dy})">{svg}</g>'


def picture():
    return Image.open(IMAGE).convert('RGBA').resize((N, N), Image.BOX)


def base_paths():
    im = picture()
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
    # One element per line: the file is data, and reads as such.
    return '\n'.join(
        f'<path fill=""#{pal[3*c]:02x}{pal[3*c+1]:02x}{pal[3*c+2]:02x}" d="{"".join(d)}"/>'
        for c, d in paths.items()
    )


def blink_anim(dur='4.5s'):
    return (f'<animate attributeName="opacity" values="0;1;0" keyTimes="0;0.94;0.98" '
            f'dur="{dur}" calcMode="discrete" repeatCount="indefinite"/>')


def flash(dur, begin='0s', values='1;0'):
    return (f'<animate attributeName="opacity" values="{values}" dur="{dur}" begin="{begin}" '
            f'calcMode="discrete" repeatCount="indefinite"/>')


# Eye boxes in the 128 grid (inside the lenses), 8 wide and 7 tall from each
# eye's top-left in the character file (Som: x55-62 and x74-81, y35-41).
CLOSED = (''.join(f'<rect x="{x}" y="{EYE_Y}" width="8" height="6" fill="{SKIN}"/>' for x in EYE_XS)
          + ''.join(f'<rect x="{x + 1}" y="{EYE_Y + 3}" width="6" height="1" fill="{INK}"/>' for x in EYE_XS))
HAPPY = (''.join(f'<rect x="{x}" y="{EYE_Y}" width="8" height="6" fill="{SKIN}"/>' for x in EYE_XS)
         + f'<path fill="{INK}" d="'
         + ''.join(f'M{x + 1} {EYE_Y + 4}h1v-1h1v-1h2v1h1v1h1v1h-1v-1h-1v-1h-2v1h-1v1h-1z' for x in EYE_XS) + '"/>')
STEAM = shift('<g fill="#c9ced6" opacity="0.9">'
              '<rect x="8" y="80" width="2" height="2"/><rect x="10" y="77" width="2" height="2"/>'
              '<rect x="8" y="74" width="2" height="2"/><rect x="12" y="81" width="1" height="1"/>'
              '<animateTransform attributeName="transform" type="translate" values="0 0;1 -1;0 -2;-1 -1" '
              'dur="1.6s" calcMode="discrete" repeatCount="indefinite"/></g>', 'steam')

# Drawn above every pose, so blinking also covers redrawn eyes (think).
COMMON = f'{STEAM}<g opacity="0">{CLOSED}{blink_anim()}</g>'


def sparkle(x, y, begin):
    return (f'<g fill="#f4c430" opacity="1"><rect x="{x}" y="{y-2}" width="1" height="5"/>'
            f'<rect x="{x-2}" y="{y}" width="5" height="1"/>{flash("0.8s", begin)}</g>')


def key(x, y, begin):
    return f'<rect x="{x}" y="{y}" width="3" height="1" fill="#acdbf5" opacity="0">{flash("0.6s", begin, "0;1")}</rect>'


def pixels():
    """The base picture as RGB tuples, None where transparent: [y][x]."""
    im = picture()
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
    return '\n'.join(out) + '\n'


FUR = (CFG.get('paws') or {}).get('fur', {'min_red': 140, 'red_minus_blue': 50})


def warm(c):
    """A fur-coloured pixel (the paws), by the character file's thresholds."""
    return c is not None and c[0] > FUR['min_red'] and c[0] - c[2] > FUR['red_minus_blue']


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
# Som's left box is the paw only: moving the forearm smeared the sleeve and the
# sticky note. A character file with no "paws" keeps its hands still.
PAWS = CFG.get('paws')


def mouse_pred(c):
    return c is not None and not warm(c) and c[2] >= c[0] - 10


def hands():
    if not PAWS:
        return ''
    px = pixels()
    paw_r = mask(px, PAWS['keyboard'], warm)
    hand_l = mask(px, PAWS['mouse_paw'], warm) | mask(px, PAWS['mouse'], mouse_pred)
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


def look_right(dx=EYES.get('look', 2)):
    """Both eyes redrawn dx px to the right inside their lens boxes, so the cat looks at the monitor."""
    if not dx:
        return ''
    im = picture()
    q = im.convert('RGB').quantize(COLORS, method=Image.MEDIANCUT, dither=Image.NONE).convert('RGB')
    lens = tuple(int(LENS[i:i + 2], 16) for i in (1, 3, 5))
    out = []
    for x0 in EYE_XS:
        x1 = x0 + 7
        for y in range(EYE_Y, EYE_Y + 7):
            row = [q.getpixel((x, y)) for x in range(x0, x1 + 1)]
            for i, c in enumerate([lens] * dx + row[:-dx]):
                out.append(f'<rect x="{x0 + i}" y="{y}" width="1" height="1" fill="#{c[0]:02x}{c[1]:02x}{c[2]:02x}"/>')
    return '\n'.join(out) + '\n'


POSES = {
    'idle': '',
    'think': shift(
        '<g fill="#ffffff" stroke="#2e3245" stroke-width="1">'
        '<circle cx="41" cy="30" r="1.5"/><circle cx="35" cy="23" r="2.5"/>'
        '<ellipse cx="20" cy="12" rx="15" ry="9"/></g>'
        + ''.join(f'<rect x="{x}" y="11" width="3" height="3" fill="#2e3245" opacity="0">'
                  f'{flash("1.5s", b, "0;1;1")}</rect>'
                  for x, b in ((11, '0s'), (18, '0.5s'), (25, '1s'))), 'bubble'
    ),
    'read': shift(
        '<g><circle cx="100" cy="28" r="7" fill="#acdbf5" fill-opacity="0.55" stroke="#494f5e" stroke-width="2"/>'
        '<rect x="97" y="24" width="2" height="2" fill="#ffffff"/>'
        '<path d="M105 33l7 7" stroke="#844820" stroke-width="3"/>'
        '<animateTransform attributeName="transform" type="translate" values="0 0;-3 2;0 3;3 2" '
        'dur="1.6s" calcMode="discrete" repeatCount="indefinite"/></g>', 'magnifier'
    ),
    'edit': (
        shift(''.join(key(x, y, b) for x, y, b in ((70, 97, '0s'), (78, 99, '0.15s'), (86, 97, '0.3s'), (94, 99, '0.45s'))), 'keys')
        + shift('<g>' + ''.join(
            f'<rect x="42" y="{y}" width="{w}" height="1" fill="{c}">'
            f'<animate attributeName="width" values="0;{w};{w}" dur="2s" begin="{b}" calcMode="discrete" '
            f'repeatCount="indefinite"/></rect>'
            for y, w, c, b in ((119, 20, '#2d5fd1', '0s'), (121, 32, '#c8323a', '0.3s'),
                               (123, 26, '#3f8f4a', '0.6s'), (125, 14, '#2d5fd1', '0.9s'))) + '</g>', 'screen')
    ),
    'bash': (
        shift('<rect x="38" y="117" width="58" height="11" fill="#14324a"/>'
              '<path fill="#8fe39b" d="M41 119h1v1h1v1h1v1h-1v1h-1v1h-1v-1h1v-1h1v-1h-1v-1h-1z"/>'
              '<rect x="47" y="123" width="4" height="1" fill="#8fe39b">' + flash('0.8s') + '</rect>', 'screen')
        + shift('<rect x="113" y="90" width="3" height="2" fill="#8fe39b">' + flash('0.5s') + '</rect>', 'led')
    ),
    'done': HAPPY + shift(sparkle(40, 14, '0s') + sparkle(100, 10, '0.2s') + sparkle(108, 40, '0.4s') + sparkle(30, 44, '0.6s'), 'sparkles'),
    # A subagent is working: a paper plane flies off with the job.
    'delegate': shift(
        '<g><path d="M0 0L11 4L0 8L3 4Z" fill="#ffffff" stroke="#2e3245" stroke-width="1"/>'
        '<path d="M3 4h8" stroke="#9aa3b5" stroke-width="1"/>'
        '<animateTransform attributeName="transform" type="translate" values="6 14;12 11;18 9;24 8;30 9" '
        'dur="1.5s" calcMode="discrete" repeatCount="indefinite"/></g>'
        + ''.join(f'<rect x="{x}" y="22" width="2" height="1" fill="#9aa3b5" opacity="0">{flash("1.5s", b, "0;1;1;0")}</rect>'
                  for x, b in ((4, '0s'), (9, '0.3s'), (14, '0.6s'))), 'plane'
    ),
}

# Context nearly full: wide eyes, a sweat drop and a red "!", drawn above
# every pose (its eyes cover the blink and the look at the monitor).
WIDE = ''.join(f'<rect x="{x}" y="{EYE_Y}" width="8" height="7" fill="{SKIN}"/>'
               f'<rect x="{x + 1}" y="{EYE_Y}" width="6" height="6" fill="#ffffff"/>'
               f'<rect x="{x + 3}" y="{EYE_Y + 2}" width="2" height="2" fill="{INK}"/>' for x in EYE_XS)
ALARM = (WIDE
         + shift('<g fill="#7cc6f2"><rect x="46" y="40" width="1" height="1"/><rect x="45" y="41" width="3" height="3"/>'
         '<rect x="46" y="44" width="1" height="1"/>'
         '<animateTransform attributeName="transform" type="translate" values="0 0;0 1;0 2;0 3" '
         'dur="1.2s" calcMode="discrete" repeatCount="indefinite"/></g>', 'sweat')
         + shift('<g fill="#d93a3a"><rect x="96" y="1" width="3" height="7"/><rect x="96" y="9" width="3" height="2"/>'
         + flash('0.8s', '0s', '1;0.35') + '</g>', 'exclaim'))


# While working (think/read/edit/bash/delegate) the cat looks at the monitor
# and its hands move. One shared layer, under each pose's overlay, so the pane
# carries it once (~38k chars) instead of once per pose.
WORKING_POSES = ('think', 'read', 'edit', 'bash', 'delegate')


def main():
    base = base_paths()
    working = look_right() + hands()
    out = os.path.join(ROOT, 'hooks', 'sprite.ts')
    esc = lambda s: s.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
    lines = [
        f'// Generated by tools/build_sprite.py from {os.path.relpath(CHARACTER, ROOT)} ({CFG["image"]}); do not edit by hand.',
        '// Plain SVG markup in template strings: the picture as one <path> per colour,',
        '// and per-pose overlays animated with SMIL. Nothing here runs; the pane draws it.',
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
        '// Context nearly full: drawn above whatever pose is showing.',
        f'export const alarm = `${{OPEN}}{esc(ALARM)}</svg>`',
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
    sizes = {'base': len(wrap(base)), 'working': len(wrap(working)), 'alarm': len(wrap(ALARM)),
             **{k: len(wrap(v + COMMON)) for k, v in POSES.items()}}
    print('wrote', out, 'pane total chars', sum(sizes.values()), sizes)
    if '--debug' in sys.argv:
        d = sys.argv[sys.argv.index('--debug') + 1]
        os.makedirs(d, exist_ok=True)
        for k in [*POSES, 'alarm']:
            s = wrap(full('think') + ALARM) if k == 'alarm' else wrap(full(k))
            s = re.sub(r'<animate[^>]*/>', '', s).replace('opacity="0"', 'opacity="1"')
            s = s.replace('<svg ', '<svg width="512" height="512" ', 1)
            open(os.path.join(d, f'pose-{k}.svg'), 'w').write(s)


if __name__ == '__main__':
    main()
