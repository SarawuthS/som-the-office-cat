# Som the office cat

A Claude Code mod: a pane beside the chat where Som, a pixel office cat in glasses, acts out what Claude is doing, with your session's context statistics underneath.

## What it shows

- **Som's poses** follow the session: `think` (thought bubble), `read` (magnifier, for Read/Grep/Glob/WebFetch/WebSearch), `edit` (keys and code light up, for Edit/Write), `bash` (terminal on the tablet), `done` (happy eyes and sparkles for 8 s after a turn ends), then `idle`. While working Som looks at the monitor, types and moves the mouse. Som blinks and the coffee steams in every pose.
- **Context:** % of the window used, tokens / window, a bar that stretches with the pane (each category in its colour, the autocompact buffer, free space), tokens added by the last turn, distance to auto-compact, and one row per category. The header turns amber at 70 % and red at 85 %.
- **Usage limits** (subscription accounts): 5-hour and 7-day % with reset times. Hidden when your account reports none.

The figures are a local estimate (no API request, no model tokens), refreshed at session start and whenever a turn ends. The mod reads nothing but the session's own usage figures and sends nothing anywhere.

The picture needs the Claude desktop app (or another surface that draws SVG); in a terminal the pane shows the statistics only.

## Install

At the prompt of a Claude Code terminal session:

```
/plugin install som-the-office-cat --marketplace SarawuthS/som-the-office-cat
```

Answer `y` to add the marketplace, then pick a scope (user scope loads it in every session). From a shell:

```
claude plugin install som-the-office-cat --marketplace SarawuthS/som-the-office-cat
```

In the desktop app, where `/plugin` does not run: click **+** next to the prompt box, then **Plugins**, **Add marketplace** with `SarawuthS/som-the-office-cat`, then **Add plugin**.

The pane opens when a session starts; if it does not, type `/som-the-office-cat`.

## Develop

- `hooks/register.tsx` — hooks, state and the pane. `types/index.d.ts` — the state contract.
- `hooks/sprite.ts` — generated SVG layers. Regenerate from `assets/office-cat.png` with `python3 tools/build_sprite.py [--debug <dir>]` (needs Pillow); change the overlays in the script, not `sprite.ts`.
- `hooks/pane.test.tsx` — mounts the pane on every surface with seeded statistics.

```
claude plugin validate .
claude plugin test .
```

Run a working copy with `claude --plugin-dir <this folder>`.

Notes from building it, in case you change the pane: Box sizes are character cells, not pixels; the pane accepts only whole-number `%` widths and `flexGrow` up to 10000, and one refused prop drops the whole pane; keep the total SVG markup small (about 110k characters draws, 430k did not); changing an interactive `Svg`'s `source` reloads its frame and flickers, so every pose stays mounted and only `display` changes; layers must centre in the same row or they drift apart.
