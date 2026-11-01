export type ContextRow = { name: string; color: string; tokens: number; kind: 'used' | 'free' | 'buffer' }
export type UsageLimit = { kind: string; percent: number; resetsAt?: string }
export type ContextStats = {
  percent: number
  tokens: number
  window: number
  rows: ContextRow[]
  ms: number
  // Tokens at which auto-compaction runs; absent when it is off.
  compactAt?: number
  // Change in context tokens over the last main turn; absent until one ends.
  delta?: number
  limits: UsageLimit[]
  // US dollars this session has cost so far; absent where the host keeps no ledger.
  costUsd?: number
  // This month's extra-usage spend against its cap; absent when the account reports none.
  spend?: MonthlySpend
}
export type MonthlySpend = { used: number; limit: number; percent: number; currency: string }
export type Pose = 'idle' | 'think' | 'read' | 'edit' | 'bash' | 'done'

declare module 'claude-code' {
  interface PluginState {
    'som-the-office-cat': { pose: Shaped<Pose>; turn: Shaped<string>; since: Shaped<number>; context: Shaped<ContextStats | null> }
  }
}
