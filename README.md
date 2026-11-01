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

---

# ส้ม แมวออฟฟิศ (ภาษาไทย)

mod สำหรับ Claude Code: pane ข้างแชทที่มี "ส้ม" แมวออฟฟิศพิกเซลใส่แว่น ขยับท่าตามสิ่งที่ Claude กำลังทำ และแสดงสถิติ context ของ session ไว้ด้านล่าง

## สิ่งที่แสดง

- **ท่าของส้ม** เปลี่ยนตาม session: `think` (ฟองความคิด), `read` (แว่นขยาย เมื่อใช้ Read/Grep/Glob/WebFetch/WebSearch), `edit` (คีย์บอร์ดกับโค้ดสว่างขึ้น เมื่อใช้ Edit/Write), `bash` (จอ terminal บนแท็บเล็ต), `done` (ยิ้มตาปิดพร้อมประกายดาว 8 วินาทีหลังจบ turn) แล้วกลับเป็น `idle` ระหว่างทำงานส้มจะมองจอ พิมพ์คีย์บอร์ด และเลื่อนเมาส์ ทุกท่าส้มกะพริบตาและมีไอลอยจากแก้วกาแฟ
- **Context:** % ที่ใช้ไปของ context, จำนวน token เทียบทั้งหมด, แถบที่ยืดตามความกว้างของ pane (แต่ละหมวดตามสี, autocompact buffer, พื้นที่ว่าง), token ที่เพิ่มในรอบล่าสุด, ระยะที่เหลือก่อน auto-compact และตารางแยกตามหมวด หัวข้อเปลี่ยนเป็นสีเหลืองที่ 70% และสีแดงที่ 85%
- **Usage limits** (บัญชีแบบ subscription): % ที่ใช้ไปของรอบ 5 ชั่วโมงและ 7 วัน พร้อมเวลารีเซ็ต ถ้าบัญชีไม่มีข้อมูลนี้ส่วนนี้จะถูกซ่อน

ตัวเลขเป็นค่าประมาณที่คำนวณในเครื่อง (ไม่เรียก API และไม่ใช้ token ของโมเดล) อัปเดตตอนเริ่ม session และทุกครั้งที่ turn จบ mod อ่านเฉพาะสถิติการใช้งานของ session เอง และไม่ส่งข้อมูลไปที่ไหน

ภาพแมวต้องใช้แอป Claude Desktop (หรือ surface อื่นที่วาด SVG ได้) ใน terminal จะเห็นเฉพาะสถิติ

## ติดตั้ง

ในช่องพิมพ์ของ Claude Code แบบ terminal:

```
/plugin install som-the-office-cat --marketplace SarawuthS/som-the-office-cat
```

ตอบ `y` เพื่อเพิ่ม marketplace แล้วเลือก scope (user scope จะโหลดในทุก session) หรือจาก shell:

```
claude plugin install som-the-office-cat --marketplace SarawuthS/som-the-office-cat
```

ในแอป Desktop ซึ่งใช้ `/plugin` ไม่ได้: กด **+** ข้างช่องพิมพ์ → **Plugins** → **Add marketplace** ใส่ `SarawuthS/som-the-office-cat` → **Add plugin**

pane จะเปิดเองเมื่อเริ่ม session ถ้าไม่เปิด ให้พิมพ์ `/som-the-office-cat`

## พัฒนาต่อ

- `hooks/register.tsx`: hook, state และการวาด pane ส่วน `types/index.d.ts` คือ contract ของ state
- `hooks/sprite.ts`: ชั้นภาพ SVG ที่สร้างอัตโนมัติ สร้างใหม่จาก `assets/office-cat.png` ด้วย `python3 tools/build_sprite.py [--debug <dir>]` (ต้องมี Pillow) ถ้าจะแก้ท่า ให้แก้ในสคริปต์ ไม่ใช่ใน `sprite.ts`
- `hooks/pane.test.tsx`: วาด pane บนทุก surface ด้วยสถิติจำลอง

```
claude plugin validate .
claude plugin test .
```

รันสำเนาที่กำลังแก้ด้วย `claude --plugin-dir <โฟลเดอร์นี้>`

ข้อควรรู้ถ้าจะแก้ pane: ขนาดของ Box นับเป็นช่องตัวอักษร ไม่ใช่ pixel; pane รับความกว้างแบบ `%` เฉพาะจำนวนเต็ม และ `flexGrow` ไม่เกิน 10000 ถ้ามี prop ใดถูกปฏิเสธ pane จะไม่วาดทั้งหมด; ขนาด SVG รวมควรเล็ก (ราว 110k ตัวอักษรวาดได้ แต่ 430k ไม่ได้); การเปลี่ยน `source` ของ `Svg` แบบ interactive ทำให้ frame โหลดใหม่และกะพริบ จึงวาดทุกท่าค้างไว้แล้วสลับแค่ `display`; ทุกชั้นภาพต้องจัดกึ่งกลางในแถวเดียวกัน ไม่อย่างนั้นจะเหลื่อมกัน
