"""Render assets/demo.gif: Som going through every pose, as the pane draws it.

Usage: python3 tools/make_demo_gif.py
Needs Pillow and Playwright with a Chromium (or Chrome) browser. Each pose is
the pane's own layers (base, working, overlay) with their SMIL animation
stepped frame by frame, so the GIF shows the real blinking, typing and steam.
"""
import io
import os
import sys

from PIL import Image, ImageDraw, ImageFont
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(__file__))
import build_sprite as b  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, 'assets', 'demo.gif')
SIZE = 256          # cat picture, pixels
STEP = 0.1          # seconds between frames
SECONDS = {'idle': 2.0, 'think': 2.0, 'read': 2.0, 'edit': 2.0, 'bash': 2.0, 'delegate': 2.0, 'alarm': 2.0, 'done': 2.5}
LABELS = {
    'idle': 'idle', 'think': 'thinking', 'read': 'reading files', 'edit': 'editing code',
    'bash': 'running a command', 'delegate': 'subagent at work',
    'alarm': 'context nearly full!', 'done': 'done!',
}
BG = (246, 243, 238)
INK = (60, 52, 46)


def svg(pose):
    if pose == 'alarm':  # the alarm layer over a working pose, as the pane stacks it
        return svg('edit').replace('</svg>', b.ALARM + '</svg>')
    body = b.base_paths() + ((b.look_right() + b.hands()) if pose in b.WORKING_POSES else '') + b.POSES[pose] + b.COMMON
    return (f'<svg id="s" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {b.N} {b.N}" width="{SIZE}" height="{SIZE}" '
            f'shape-rendering="crispEdges">{body}</svg>')


def font(px):
    for f in ('/System/Library/Fonts/Menlo.ttc', '/System/Library/Fonts/SFNSMono.ttf', 'DejaVuSansMono.ttf'):
        try:
            return ImageFont.truetype(f, px)
        except OSError:
            pass
    return ImageFont.load_default()


def main():
    frames = []
    label_font = font(16)
    with sync_playwright() as p:
        try:
            browser = p.chromium.launch()
        except Exception:
            browser = p.chromium.launch(channel='chrome')
        page = browser.new_page(viewport={'width': SIZE, 'height': SIZE})
        for pose, secs in SECONDS.items():
            page.set_content(f'<body style="margin:0;background:rgb{BG}">{svg(pose)}</body>')
            page.evaluate('document.getElementById("s").pauseAnimations()')
            for i in range(round(secs / STEP)):
                page.evaluate(f'document.getElementById("s").setCurrentTime({i * STEP})')
                cat = Image.open(io.BytesIO(page.screenshot())).convert('RGB')
                frame = Image.new('RGB', (SIZE, SIZE + 32), BG)
                frame.paste(cat, (0, 0))
                d = ImageDraw.Draw(frame)
                w = d.textlength(LABELS[pose], font=label_font)
                d.text(((SIZE - w) / 2, SIZE + 6), LABELS[pose], fill=INK, font=label_font)
                frames.append(frame)
        browser.close()
    pal = [f.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE) for f in frames]
    pal[0].save(OUT, save_all=True, append_images=pal[1:], duration=int(STEP * 1000), loop=0, optimize=True)
    print('wrote', OUT, len(frames), 'frames', os.path.getsize(OUT), 'bytes')


if __name__ == '__main__':
    main()
