import { expect, test } from 'claude-code/testing'
import { alarm, base, overlay, working } from './sprite'

const PANE = {
  plugin: 'som-the-office-cat',
  component: 'Pane',
  requestId: 'som-the-office-cat',
  props: {
    title: 'Office cat',
    isFocused: false,
    bodyColumns: 40,
    placement: 'dock',
    scroll: { offset: 0, bodyRows: 40 },
    view: {},
  },
} as const

// Shaped like a real reading (2026-11-01): tiny rows are what once printed
// as `2.5e-5%` and made the Pane refuse the whole tree.
const CONTEXT = {
  percent: 30,
  tokens: 301_641,
  window: 1_000_000,
  ms: 34,
  compactAt: 967_000,
  delta: 12_300,
  limits: [
    { kind: 'five_hour', percent: 23.5, resetsAt: '2026-11-01T08:00:00.000Z' },
    { kind: 'seven_day', percent: 88, resetsAt: '2026-11-05T02:00:00.000Z' },
  ],
  costUsd: 3.456,
  spend: { used: 12.5, limit: 100, percent: 12.4567, currency: 'USD' },
  rows: [
    { name: 'Messages', color: 'promptBorder', tokens: 217_900, kind: 'used' as const },
    { name: 'MCP tools', color: 'warning', tokens: 19_900, kind: 'used' as const },
    { name: 'MCP server instructions', color: 'inactive', tokens: 25, kind: 'used' as const },
    { name: 'Autocompact buffer', color: 'inactive', tokens: 33_000, kind: 'buffer' as const },
    { name: 'Free space', color: 'inactive', tokens: 665_400, kind: 'free' as const },
  ],
}

test('the cat and the context stats draw on every surface', async ($, on) => {
  on('state.get', (_, e) =>
    e.key === 'context' ? { value: { value: { shape: 'context-4', value: CONTEXT }, version: 1 } } : { value: { value: undefined, version: 0 } },
  )

  for (const surface of ['terminal', 'desktop', 'vscode', 'mobile'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /Context 30% used/ }))?.text).toContain('30%')
    expect((await ui.find({ type: 'Text', text: /301\.6k \/ 1M/ }))?.text).toContain('1M')
    expect((await ui.find({ type: 'Text', text: /last turn/ }))?.text).toContain('+12.3k')
    expect((await ui.find({ type: 'Text', text: /to auto-compact/ }))?.text).toContain('665.4k')
    expect((await ui.find({ type: 'Text', text: /7-day/ }))?.text).toContain('88%')
    expect((await ui.find({ type: 'Text', text: /^\$3\.46$/ }))?.text).toBe('$3.46')
    expect((await ui.find({ type: 'Text', text: /\/ \$100\.00/ }))?.text).toBe('$12.50 / $100.00 (12.5%)')
    expect((await ui.find({ type: 'Text', text: /at API prices/ }))?.text).toBeDefined()
    await ui.unmount()
  }
})

const seed = (value: unknown) => (_: unknown, e: { key: string }) =>
  e.key === 'context' ? { value: { value: { shape: 'context-4', value }, version: 1 } } : { value: { value: undefined, version: 0 } }

test('Thai text, and the sections settings turn off', { options: { language: 'th', showCategories: false, showMonthlySpend: false } }, async ($, on) => {
  on('state.get', seed(CONTEXT))
  for (const surface of ['terminal', 'desktop'] as const) {
    const ui = await $.ui.mount({ ...PANE, surface })
    expect((await ui.find({ type: 'Text', text: /ใช้ context ไป/ }))?.text).toBe('ใช้ context ไป 30%')
    expect((await ui.find({ type: 'Text', text: /7 วัน/ }))?.text).toContain('88%')
    expect((await ui.find({ type: 'Text', text: /ค่าใช้จ่าย session/ }))?.text).toBeDefined()
    expect(await ui.find({ type: 'Text', text: /Messages/ })).toBeUndefined()
    expect(await ui.find({ type: 'Text', text: /\$100\.00/ })).toBeUndefined()
    await ui.unmount()
  }
})

test('the alarm layer shows once context passes alarmAt', async ($, on) => {
  let percent = 90
  on('state.get', (_, e) => seed({ ...CONTEXT, percent })(_, e))
  for (const [p, display] of [[90, 'flex'], [30, 'none']] as const) {
    percent = p
    const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
    expect((await ui.find({ type: 'Box', key: 'layer-alarm' }))?.props.display).toBe(display)
    await ui.unmount()
  }
})

test('catAlarm off keeps the alarm hidden', { options: { catAlarm: false } }, async ($, on) => {
  on('state.get', seed({ ...CONTEXT, percent: 95 }))
  const ui = await $.ui.mount({ ...PANE, surface: 'desktop' })
  expect((await ui.find({ type: 'Box', key: 'layer-alarm' }))?.props.display).toBe('none')
  await ui.unmount()
})

test('every sprite layer has well-formed attributes', () => {
  // 0.3.2 shipped fill=""#010101": every colour was lost and the cat drew black.
  for (const svg of [base, working, alarm, ...(['idle', 'think', 'read', 'edit', 'bash', 'delegate', 'done'] as const).map(overlay)]) {
    expect(svg).not.toMatch(/=""[^\s/>]/)
    expect(svg).toMatch(/<path fill="#[0-9a-f]{6}"|<rect /)
  }
})
