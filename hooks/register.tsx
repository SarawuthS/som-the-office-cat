import { atom, read, update } from 'claude-code'
import type { EngineInterface, PluginOptions, Register } from 'claude-code'
import type { ContextStats, MonthlySpend, Pose } from '../types'
import { alarm, base, isWorking, overlay, working } from './sprite'
import { type Lang, TEXT, type Words } from './text'

const PANE = 'som-the-office-cat'
const DONE_MS = 8000
const WATCH_MS = 2000
// A main turn with no event for this long is treated as gone (no turn.complete came).
const STALE_MS = 10 * 60 * 1000
// What the cat is doing, driven by this session's turn and tool events.
const pose = atom({ plugin: 'som-the-office-cat', key: 'pose' } as const, 'idle' as Pose, {
  shape: 'pose-1',
})

// The main turn in progress ('' when none) and when the pose last changed.
const turn = atom({ plugin: 'som-the-office-cat', key: 'turn' } as const, '', { shape: 'turn-1' })
const since = atom({ plugin: 'som-the-office-cat', key: 'since' } as const, 0, { shape: 'since-1' })

// The person's choices from the plugin's settings (`userConfig` in
// plugin.json); `register` reads them again on every reload.
const settings = (o: PluginOptions) => {
  const num = (k: string, d: number) => (typeof o[k] === 'number' ? (o[k] as number) : d)
  const flag = (k: string) => o[k] !== false
  const lang: Lang = o.language === 'th' ? 'th' : 'en'
  return {
    lang,
    warnAt: num('warnAt', 70),
    alarmAt: num('alarmAt', 85),
    catAlarm: flag('catAlarm'),
    categories: flag('showCategories'),
    limits: flag('showUsageLimits'),
    cost: flag('showSessionCost'),
    spend: flag('showMonthlySpend'),
  }
}
let cfg = settings({})
let words: Words = TEXT.en

const setPose = async ($: EngineInterface, p: Pose) => {
  await update($, pose, () => p)
  await update($, since, () => Date.now())
}

// The context window by category, as the app's Context panel shows it. Counted
// with the local estimate (`summary`: no API request, no model tokens) when a
// main turn ends and at session start, and kept in state so drawing reads it.
const context = atom({ plugin: 'som-the-office-cat', key: 'context' } as const, null as ContextStats | null, {
  shape: 'context-4',
})

async function countContext($: EngineInterface, afterTurn: boolean) {
  const t0 = Date.now()
  const { context: c, rateLimits, cost } = await $.session.usage({ breakdown: 'summary' })
  const b = c.breakdown
  if (b === undefined) return
  const rows = b.categories.flatMap(r => (r.kind === 'deferred' || r.tokens <= 0 ? [] : [{ name: r.name, color: r.color, tokens: r.tokens, kind: r.kind }]))
  const order = { used: 0, buffer: 1, free: 2 }
  rows.sort((a, z) => order[a.kind] - order[z.kind] || z.tokens - a.tokens)
  const ms = Date.now() - t0
  const prev = await read($, context)
  // Only a finished turn moves the delta; a reload's recount keeps the last one.
  const delta = afterTurn && prev !== null ? b.totalTokens - prev.tokens : prev?.delta
  const limits = rateLimits.map(l => ({ kind: l.kind, percent: l.percentUsed, resetsAt: l.resetsAt }))
  const compactAt = b.isAutoCompactEnabled ? b.autoCompactThreshold : undefined
  // A failed or empty answer keeps the last figure rather than blanking the row.
  // Turned off in settings, the endpoint is not asked at all.
  const spend = cfg.spend ? ((await fetchSpend($).catch(() => undefined)) ?? prev?.spend) : undefined
  await update($, context, () => ({
    percent: b.percentage, tokens: b.totalTokens, window: b.rawMaxTokens, rows, ms, compactAt, delta, limits, costUsd: cost?.usd, spend,
  }))
}

// The month's extra-usage spend from the account's usage endpoint, through the
// host (the credential never reaches the mod). Undefined when it answers
// nothing usable (no first-party login, not enabled, a changed shape).
async function fetchSpend($: EngineInterface): Promise<MonthlySpend | undefined> {
  const a = await $.session.authorize()
  if (a === null) return undefined
  const r = await $.http.fetch('https://api.anthropic.com/api/oauth/usage', {
    auth: a.handle,
    headers: { 'anthropic-beta': 'oauth-2025-04-20' },
  })
  if (!r.ok) return undefined
  const s = (JSON.parse(r.text) as { spend?: SpendBody | null }).spend
  if (!s || !s.enabled || !s.used || !s.limit) return undefined
  return {
    used: s.used.amount_minor / 10 ** s.used.exponent,
    limit: s.limit.amount_minor / 10 ** s.limit.exponent,
    percent: s.percent,
    currency: s.used.currency,
  }
}
type SpendBody = {
  enabled: boolean
  percent: number
  used?: { amount_minor: number; currency: string; exponent: number }
  limit?: { amount_minor: number; exponent: number }
}

const fmt = (n: number) =>
  n >= 1_000_000 ? `${+(n / 1_000_000).toFixed(1)}M` : n >= 1000 ? `${+(n / 1000).toFixed(1)}k` : `${n}`

const permille = (n: number, of: number) => Math.min(1000, Math.round((1000 * n) / of))

// The context bar: used categories, then the autocompact buffer beside them
// on the left (the user's call: it is held, not free), then free space. A
// one-cell mark at the compact point drew as a thick block that read as data.
const barSegments = (ctx: ContextStats) =>
  [...ctx.rows.filter(r => r.kind === 'used'), ...ctx.rows.filter(r => r.kind === 'buffer'), ...ctx.rows.filter(r => r.kind === 'free')]
    .map(r => ({ color: r.kind === 'buffer' ? 'subtle' : r.kind === 'free' ? 'inactive' : r.color, grow: permille(r.tokens, ctx.window) }))
    .filter(g => g.grow > 0)

// Reset time in local time: `15:00` today, `Mon 15:00` later.
const resetLabel = (iso: string | undefined) => {
  if (iso === undefined) return ''
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return ''
  const hm = `${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`
  const sameDay = d.toDateString() === new Date().toDateString()
  return sameDay ? hm : `${words.days[d.getDay()]} ${hm}`
}

// Header colour: amber from `warnAt` %, red from `alarmAt` % (70 and 85 unless
// set), of the window or a limit.
const level = (percent: number) => (percent >= cfg.alarmAt ? 'error' : percent >= cfg.warnAt ? 'warning' : undefined)

// At most one decimal: the usage endpoint can answer 1.8823.
const pct = (percent: number) => `${+percent.toFixed(1)}%`

const SYMBOLS: Record<string, string> = { USD: '$', EUR: '€', GBP: '£', JPY: '¥', THB: '฿' }
const money = (n: number, currency: string) => `${SYMBOLS[currency] ?? `${currency} `}${n.toFixed(2)}`

const NAME_CHARS = 20
const short = (name: string) => (name.length > NAME_CHARS ? `${name.slice(0, NAME_CHARS - 1)}…` : name)

const POSES: Pose[] = ['idle', 'think', 'read', 'edit', 'bash', 'delegate', 'done']
const OVERLAYS = Object.fromEntries(POSES.map(p => [p, overlay(p)])) as Record<Pose, string>

const toolPose = (tool: string): Pose => {
  if (tool === 'Read' || tool === 'Grep' || tool === 'Glob' || tool === 'WebFetch' || tool === 'WebSearch') return 'read'
  if (tool === 'Edit' || tool === 'Write' || tool === 'NotebookEdit') return 'edit'
  if (tool === 'Bash') return 'bash'
  if (tool === 'Agent' || tool === 'Task') return 'delegate'
  return 'think'
}

export const register: Register = (on, options) => {
  cfg = settings(options)
  words = TEXT[cfg.lang]

  on('session.start', async ($, e, next) => {
    await $.command.register({
      name: 'som-the-office-cat',
      description: 'Show Som, the office cat, in a pane',
    })
    void countContext($, false).catch(() => {})
    void $.ui.open({ id: PANE, title: words.title }).catch(() => {})
    // Watchdog: back to idle once no main turn is running and `done` has been
    // shown long enough. Survives reloads (a `clock.after` from an old module
    // does not), and catches a turn.start whose turn.complete never comes.
    $.clock.every(WATCH_MS, () => {
      void (async () => {
        const t = await $.clock.now()
        const active = await read($, turn)
        const p = await read($, pose)
        if (active !== '' && t - (await read($, since)) > STALE_MS) {
          await update($, turn, () => '')
        } else if (active !== '') return
        if (p === 'idle') return
        if (p !== 'done' || t - (await read($, since)) >= DONE_MS) {
          await update($, pose, () => 'idle')
        }
      })().catch(() => {})
    })
    return next(e)
  })

  on('command.run', { command: 'som-the-office-cat' }, async $ => {
    await $.ui.open({ id: PANE, title: words.title })
    return { text: words.opened }
  })

  on('turn.start', async ($, e, next) => {
    if (e.agentId === undefined) {
      await update($, turn, () => e.turnId).catch(() => {})
      await setPose($, 'think').catch(() => {})
    }
    return next(e)
  })

  on('tool.call', async ($, e, next) => {
    if (e.agentId !== undefined) return next(e)
    // Never let the animation get in the way of the tool call itself.
    await setPose($, toolPose(e.tool)).catch(() => {})
    try {
      return await next(e)
    } finally {
      if ((await read($, turn).catch(() => '')) !== '') {
        await setPose($, 'think').catch(() => {})
      }
    }
  })

  on('turn.complete', async ($, e, next) => {
    if (e.agentId === undefined) {
      await update($, turn, () => '').catch(() => {})
      await setPose($, 'done').catch(() => {})
      void countContext($, true).catch(() => {})
    }
    return next(e)
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const els = $.ui.resolve(e)
    const { Box, Text } = els
    const Svg = 'Svg' in els ? els.Svg : undefined
    const now = await read($, pose)
    const ctx = await read($, context)
    // Context nearly full (or compaction due): the alarm layer goes on top.
    const alarmed = cfg.catAlarm && ctx !== null
      && (ctx.percent >= cfg.alarmAt || (ctx.compactAt !== undefined && ctx.tokens >= ctx.compactAt))

    return (
      <Box flexDirection="column">
        {Svg !== undefined && (
          // One centring row holds every layer: the base in the flow (so the
          // stack takes its height; an empty Box or a blank picture took none in
          // the desktop pane) and the overlays absolute over it, spanning the
          // same row. Overlays spanning an outer box instead sat ~28 px to the
          // right of the base on desktop. Box sizes are character cells, not
          // pixels: a `width={192}` box is far wider than the pane.
          <Box position="relative" flexDirection="row" justifyContent="center">
            <Svg source={base} alt="Office cat at a desk" width={192} height={192} isInteractive />
            {/* Only the small moving layer per pose changes; every overlay stays
                mounted and only the shown one is displayed: swapping a frame's
                source reloads it, which flickers. Six full pictures (~430k
                chars) did not draw. */}
            {[
              { key: 'working', source: working, alt: 'Office cat working', shown: isWorking(now) },
              ...POSES.map(p => ({ key: p, source: OVERLAYS[p], alt: `Office cat: ${p}`, shown: p === now })),
              { key: 'alarm', source: alarm, alt: 'Office cat: context nearly full', shown: alarmed },
            ].map(l => (
              <Box key={`layer-${l.key}`} position="absolute" top={0} left={0} right={0} flexDirection="row" justifyContent="center"
                display={l.shown ? 'flex' : 'none'}>
                <Svg source={l.source} alt={l.alt} width={192} height={192} isInteractive />
              </Box>
            ))}
          </Box>
        )}
        {ctx !== null && (
          <Box flexDirection="column" marginTop={1} paddingX={1}>
            <Box flexDirection="row" justifyContent="space-between">
              <Text bold color={level(ctx.percent)}>
                {words.contextUsed(pct(ctx.percent))}
              </Text>
              <Text dimColor>
                {fmt(ctx.tokens)} / {fmt(ctx.window)}
              </Text>
            </Box>
            {/* The bar stretches with the pane: each segment grows from zero
                width by its share of the window in per-mille (whole numbers;
                the Pane takes flexGrow up to 10000, so raw token counts fail). Boxes sized in fractional
                percent were refused by the Pane, which then dropped the whole
                tree; fixed-length block characters wrapped or left a gap. */}
            <Box flexDirection="row" width="100%" height={1} marginY={1}>
              {/* One flat list of segments: wrapped in a fragment, the free
                  space took no width on desktop and the used part filled the bar. */}
              {barSegments(ctx).map(g => (
                <Box width={0} height={1} flexGrow={g.grow} backgroundColor={g.color} />
              ))}
            </Box>
            <Box flexDirection="row" justifyContent="space-between">
              <Text size="footnote" dimColor>
                {ctx.delta === undefined ? '' : words.lastTurn(`${ctx.delta >= 0 ? '+' : '−'}${fmt(Math.abs(ctx.delta))}`)}
              </Text>
              <Text size="footnote" color={ctx.compactAt !== undefined && ctx.compactAt - ctx.tokens < 50_000 ? 'warning' : undefined}
                dimColor={!(ctx.compactAt !== undefined && ctx.compactAt - ctx.tokens < 50_000)}>
                {ctx.compactAt === undefined
                  ? words.compactOff
                  : ctx.compactAt > ctx.tokens
                    ? words.toCompact(fmt(ctx.compactAt - ctx.tokens))
                    : words.compactDue}
              </Text>
            </Box>
            {cfg.categories && <Box flexDirection="column">
              {ctx.rows.map(r => (
                <Box flexDirection="row" justifyContent="space-between">
                  <Text size="footnote" dimColor={r.kind !== 'used'}>
                    <Text color={r.color}>■</Text> {short(r.name)}
                  </Text>
                  <Text size="footnote" tabular dimColor>
                    {fmt(r.tokens).padStart(6)} {((100 * r.tokens) / ctx.window).toFixed(1).padStart(5)}%
                  </Text>
                </Box>
              ))}
            </Box>}
            {cfg.limits && ctx.limits.length > 0 && (
              <Box flexDirection="column" marginTop={1}>
                <Text bold>{words.usageLimits}</Text>
                {ctx.limits.map(l => (
                  <Box flexDirection="column" marginTop={1}>
                    <Box flexDirection="row" justifyContent="space-between">
                      <Text size="footnote" color={level(l.percent)}>
                        {words.limitNames[l.kind] ?? l.kind} {pct(l.percent)}
                      </Text>
                      <Text size="footnote" dimColor>
                        {l.resetsAt === undefined ? '' : words.resets(resetLabel(l.resetsAt))}
                      </Text>
                    </Box>
                    <Box flexDirection="row" width="100%" height={1}>
                      <Box width={0} height={1} flexGrow={Math.max(0, Math.min(1000, Math.round(l.percent * 10)))}
                        backgroundColor={level(l.percent) ?? 'suggestion'} />
                      <Box width={0} height={1} flexGrow={Math.max(0, 1000 - Math.round(l.percent * 10))} backgroundColor="inactive" />
                    </Box>
                  </Box>
                ))}
              </Box>
            )}
            {cfg.cost && ctx.costUsd !== undefined && (
              <Box flexDirection="column" marginTop={1}>
                <Box flexDirection="row" justifyContent="space-between">
                  <Text bold>{words.sessionCost}</Text>
                  <Text>{money(ctx.costUsd, 'USD')}</Text>
                </Box>
                {/* The figure is priced at API list prices (as `/cost` totals
                    it); on a plan with usage windows that is not the bill. */}
                {ctx.limits.length > 0 && (
                  <Text size="footnote" dimColor>
                    {words.apiPrices}
                  </Text>
                )}
              </Box>
            )}
            {cfg.spend && ctx.spend !== undefined && (
              <Box flexDirection="column" marginTop={1}>
                <Box flexDirection="row" justifyContent="space-between">
                  <Text bold color={level(ctx.spend.percent)}>{words.monthlySpend}</Text>
                  <Text>
                    {money(ctx.spend.used, ctx.spend.currency)} / {money(ctx.spend.limit, ctx.spend.currency)} ({pct(ctx.spend.percent)})
                  </Text>
                </Box>
                <Box flexDirection="row" width="100%" height={1} marginTop={1}>
                  <Box width={0} height={1} flexGrow={Math.max(0, Math.min(1000, Math.round(ctx.spend.percent * 10)))}
                    backgroundColor={level(ctx.spend.percent) ?? 'suggestion'} />
                  <Box width={0} height={1} flexGrow={Math.max(0, 1000 - Math.round(ctx.spend.percent * 10))} backgroundColor="inactive" />
                </Box>
              </Box>
            )}
            <Text size="caption" dimColor>
              {words.caption}
            </Text>
          </Box>
        )}
        {Svg === undefined && <Text dimColor>{words.desktopOnly(now)}</Text>}
      </Box>
    )
  })
}
