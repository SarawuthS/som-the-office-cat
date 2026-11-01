# Changelog

## 0.3.0 — 2026-11-01

- **Settings** (`userConfig`): pane language, amber/red thresholds, the cat's alarm, and which sections show. Turning Monthly spend off stops the usage endpoint being asked.
- **Thai** pane text (`language: th`).
- **New poses:** `delegate` (a paper plane while a subagent works) and an alarm layer (wide eyes, sweat drop, red !) once context passes `alarmAt` or auto-compact is due.
- **Your own character:** `tools/build_sprite.py --character <file>` reads the picture, eyes, paws and overlay offsets from a JSON file; Som's is `characters/som.json`. README has the steps.
- Demo GIF shows the new poses.

## 0.2.1 — 2026-11-01

- Percentages show at most one decimal; Monthly spend uses the account's currency symbol.
- Session cost says, on subscription plans, that it is priced at API rates and not billed.
- `tsconfig.json`, `.gitignore`, a CI check (`validate` and `test` on every push) and a Troubleshooting section in the README.

## 0.2.0 — 2026-11-01

- **Session cost:** what the session has cost so far, in US dollars.
- **Monthly spend:** this month's extra-usage spend against its cap, for accounts that have extra usage (e.g. Team or Enterprise, which have no 5-hour/7-day windows). Read from Claude's usage endpoint through Claude Code's sign-in; hidden when the account reports none.
- README (English and Thai) says which figures come from that endpoint.

## 0.1.0 — 2026-11-01

- First release: Som, a pixel office cat, in a pane beside the chat, with poses for think, read, edit, bash and done.
- Context statistics under the cat: % used, a bar by category, tokens added last turn, distance to auto-compact, and 5-hour/7-day usage limits on subscription accounts.
