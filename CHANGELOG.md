# Changelog

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
