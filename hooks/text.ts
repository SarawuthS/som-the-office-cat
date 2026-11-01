// The pane's words in each language the `language` setting offers. Category
// names (Messages, MCP tools, ...) come from Claude Code and stay as given.
export type Lang = 'en' | 'th'

export const TEXT = {
  en: {
    title: 'Office cat',
    opened: 'Office cat opened.',
    contextUsed: (p: string) => `Context ${p} used`,
    lastTurn: (n: string) => `${n} last turn`,
    toCompact: (n: string) => `${n} to auto-compact`,
    compactOff: 'auto-compact off',
    compactDue: 'auto-compact due',
    usageLimits: 'Usage limits',
    limitNames: { five_hour: '5-hour', seven_day: '7-day', spend_limit: 'Spend' } as Record<string, string>,
    resets: (when: string) => `resets ${when}`,
    days: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
    sessionCost: 'Session cost',
    apiPrices: 'at API prices; your plan is not billed this',
    monthlySpend: 'Monthly spend',
    caption: 'Estimated locally · updates when a turn ends',
    desktopOnly: (pose: string) => `The cat draws on the desktop app only (${pose}).`,
  },
  th: {
    title: 'แมวออฟฟิศ',
    opened: 'เปิดแมวออฟฟิศแล้ว',
    contextUsed: (p: string) => `ใช้ context ไป ${p}`,
    lastTurn: (n: string) => `${n} รอบล่าสุด`,
    toCompact: (n: string) => `อีก ${n} ถึง auto-compact`,
    compactOff: 'ปิด auto-compact',
    compactDue: 'ถึงเวลา auto-compact',
    usageLimits: 'ขีดจำกัดการใช้งาน',
    limitNames: { five_hour: '5 ชั่วโมง', seven_day: '7 วัน', spend_limit: 'วงเงิน' } as Record<string, string>,
    resets: (when: string) => `รีเซ็ต ${when}`,
    days: ['อา.', 'จ.', 'อ.', 'พ.', 'พฤ.', 'ศ.', 'ส.'],
    sessionCost: 'ค่าใช้จ่าย session',
    apiPrices: 'คิดตามราคา API ไม่ใช่ยอดที่แพ็กเกจเรียกเก็บ',
    monthlySpend: 'ยอดใช้จ่ายเดือนนี้',
    caption: 'ประมาณในเครื่อง · อัปเดตเมื่อจบแต่ละรอบ',
    desktopOnly: (pose: string) => `ภาพแมววาดได้เฉพาะในแอป Desktop (${pose})`,
  },
}

export type Words = (typeof TEXT)['en']
