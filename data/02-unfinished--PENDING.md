---
type: index
status: active
date: 2026-05-22
tags: [inbox, approvals, status]
---

# PENDING — สิ่งที่หลิวต้อง approve / decide / test

> Single inbox · Norms maintain (append เมื่อ ship · remove เมื่อหลิว action) · หลิวเช็คตอนเช้า/start session
>
> **Priority:** 🔥 P0 (block ≥3 things) · ⚡ P1 (block 1-2) · ◽ P2 (single · nice-to-have)
> **Aging:** 🟢 < 1d · 🟡 1-3d · 🟠 3-7d · 🔴 > 7d
> **Effort:** ⚡ < 5min · ⏱️ 5-15min · ⏰ 15-30min · 🕰️ > 30min
> **Decay:** item > 30d → Norms ถาม "ยังจะรอไหม" → ถ้าไม่ = sunset (ย้ายไป STATUS Paused/Sunset)

---

## 🔥 P0 — blocking ≥3 things

| Aging | Item | Effort | Where | Why |
|------|------|------|------|------|
| 🟠 ~3d | **FDA grant** (Privacy → Full Disk Access · `/bin/bash` พอ · python inherit · +Terminal.app optional) | ⚡ | System Settings | ATS auto-recovery · ATS = 80% โปรเจค depend · verify 2026-05-27: plist+keep_running เรียก python ผ่าน bash → grant /bin/bash พอ (Homebrew python3 = คำแนะนำเก่า ผิด) · `[[feedback-launchd-tcc]]` |
| 🟢 today | **Multi-Platform A5 · Epidemic Sound ฿500/mo subscribe** (เงิน · เหลือ decision เดียวจาก 3 Y/N · Plan A resolve อีก 2: A4 mascot defer Week 3 · E2 = podcast follows≥60/IG≥180/saves≥5/DM≥3) → Y/N | ⚡ | `[[PLAN-A-vs-B-OVERNIGHT-2026-05-22]]` §A.5 | block Week 3 EP1 launch (intro/outro music) · ✅ Plan A · Podcast-first locked 2026-05-27 |

---

## ⚡ P1 — blocking 1-2

| Aging | Item | Effort | Where | Why |
|------|------|------|------|------|
| 🟠 ~2d | **Norms-Master v2 audit approve** → fresh session draft v2 | ⏱️ | `Norms-Master/PROFILE-v2-AUDIT-2026-05-21.md` | block v2 draft · 7 gaps · 3 conflicts · 7 patterns · **prework พร้อมแล้ว** (`PROFILE-v2-PREWORK-2026-05-22.md` — 17/17 decode + TOC + 5 Q's with defaults + 2 sample sections · approve = ลุย draft 100 นาที) |
| 🟠 ~2d | **Bell-Hero V2: share Drive + ส่ง guide เบล** | ⏱️ | Drive `Hero-Bell/` · `BELL-HANDOFF.md` | เบลยังใช้ V2 ไม่ได้ · V1 fallback ยังเปิดอยู่ |
| 🟠 ~3d | **Mega-Website: approve Recommended 5** (Norms pick = `V1·3D20·H2`+`V2·3D0·H1`+`V3·3D80·H1`+`V2·3D20·H2`+`V4·3D0·H3` · 100% asset-ready · 1-wk ramp) → Y/N | ⚡ < 5min | `[[MEGA-TOP5-RECOMMENDATION-OVERNIGHT-2026-05-22]]` (Norms-Master/) | block Stage 2 dev · overnight pack เสร็จ · Conservative + Bold alternatives ในไฟล์ |
| 🟡 ~1d | **4 critical book decisions** (Ch 16 ดวงดี · Ch 12 Wyckoff Institute $999 + รุ่นพี่ · Ch 5 reveal timing · voice convention global) — full recs + line refs | ⏰ | `[[V1-SPOT-CHECK-OVERNIGHT-2026-05-22]]` (§2) | block Stage 4 PDF · post-sign Norms apply edits ~3 ชม. |
| 🟢 today | **WWMI EP1 v0.2 review + ส่ง 3 Atomic messages** | ⏰ | `[[EP1-PRODUCTION-WORKFLOW-v0.2-OVERNIGHT-2026-05-22]]` §3 | hard deadline 2026-05-31 Atomic ตอบ · หลุด = EP1 release ดัน 2026-08-02 · 3 messages copy-paste พร้อมส่ง LINE (channel ownership · recording setup · ICT chart pick) |
| 🟢 today | **NPC funnel v0.1 proposal review (3 decisions inside)** | ⏰ | `[[FUNNEL-V0.1-PROPOSAL-OVERNIGHT-2026-05-22]]` (03-Courses/NPC) · mirror `Knowledge/NPC-FUNNEL-V0.1-PROPOSAL-OVERNIGHT-2026-05-22.md` | block 30-day execute path · 3 Y/N: Lead Magnet (Ch 1 PDF default) · Paid Mix (Meta Retarget default) · App Friction (Form-first default) · proposal-only ไม่แตะ course code |
| 🟢 today | **Eightcap TFC base images** (gen-in-one-sitting) | 🕰️ ~2.0–2.5 ชม. | `[[STORYBOARD-OVERNIGHT-2026-05-22]]` (`02-Content/Eightcap/2026/07-July-TradersFootballCup/`) | storyboard pre-staged · 5 frames · 15 base images · order + risk + copy พร้อม · open Magnific แล้ว paste Input Blocks · CCTV V5 reuse → D-7 → WANTED → Coupon → GOT YOU (S2 last) |
| ⏸️ corpus | **Longtoon 2 video gap** — vault case study อ้าง 2AAxQhv7644 + nnD1w2hlAdk แต่ NotebookLM มีแค่ "การเรียน AI คอร์สฟรี" 1 ตัว | ⚡ ~2 min | NotebookLM "สอนใช้งาน Ai สร้างระบบทำงาน" notebook · add 2 YouTube URL | unblock proper Longtoon-anchor synthesis · Norms ทำ corpus build รอ 2 ตัวนี้เพิ่ม |
| 🟢 today | **Rotate Discord bot token** (security · ปัจจุบัน token leak ใน chat session) | ⚡ ~2 min | Developer Portal → Reset Token · update `Norms-Corp/Discord-Bot/config/.env` → `launchctl unload+load com.norms.discord-bot.plist` | token ปัจจุบันใช้งานได้ · แต่ rotate ดีกว่า · Norms-Corp/Discord-Bot/docs/STEP-1 มี link · post-rotate test `/post_now` |

---

## ◽ P2 — single / nice-to-have

| Aging | Item | Effort | Where | Why |
|------|------|------|------|------|
| 🟡 ~1d | **Norms Book V1 spot-check** + Stage 4 PDF | 🕰️ | `Norms-Book/atoms/chapters/` (18 ch) | demo book ส่ง · verify ก่อน Compliance |
| 🟢 today | **Norms Book Ch19 review** — Wyckoff 5-Step Approach (proof: atom→chapter) | ⏱️ ~10 min | `Norms-Book/atoms/chapters/Chapter-19-V1-Wyckoff-5-Step-Approach.md` | assembled จาก 8 atom Gen1 v9 (00571/00591-00597) · review voice+accuracy → ดี = scale อีก 2 module พร้อมอยู่ (3 Laws Canonical · "Wyckoff=ตัวจบ" opener) · placement ในเล่มรอ editor (แนะนำ foundation ต้นเล่ม) |
| 🟢 today | **Norms Book Ch20 review** — EP9 ≡ Wyckoff synthesis (module candidate #1 assembled · 2026-05-27) | ⏱️ ~15 min | `Norms-Book/atoms/chapters/Chapter-20-V1-EP9-Wyckoff-Synthesis.md` (backup Vault `05-Projects/Norms-Book/`) | 603 บรรทัด · 31 atoms · 45 quotes · 9 extensions ครบ · QC PASS (voice/mapping/NPC purity). ✅ ASR clean done (ไวคอฟ สม่ำเสมอ · garble แก้ · คง slang/voice). **2 decisions รอหลิว:** (1) **Research fact-check** — Evans 1950s + Pruden 2007 quotes = best-guess paraphrase ต้อง verify ก่อน publish (2) **content verify** — "EP9=Wyckoff ที่ไม่มี PS" vs "Pos6=PS" tension · agent resolve ว่า PS ซ่อนเพราะดึงกรอบออกมา → ตรงกับ mental model หลิวไหม |
| 🟡 ~1d | **Compliance Ch 6/12/13/14** final sign + **9 READY pre-flight done** | ⏰ | Ch 6/12/13/14 = `_COMPLIANCE-Ch*.md` PASS/PASS-MINOR · Ch 1/2/4/7/8/9/11/17/18 = `Norms-Book/COMPLIANCE-PREFLIGHT-9-READY-2026-05-22.md` (8 PASS + 1 PASS-MINOR · zero FAIL · 9 บท green-light Stage 4 ทันที) | post-edit verify Ch 6/12/13/14 · 9 READY pack PDF-ready ตอนนี้ |
| 🟡 ~1d | **PNG Cutout test** (Clay vs CG comparison) — *defer until Magnific CG presets exist* | ⏰ | `Brand/Assets/Workflow/CUTOUT-TEST-BRIEF.md` + `MAGNIFIC-CG-SETUP.md` | validate `[[feedback-png-cutout-consideration]]` · blocked: ต้องมี CG presets ก่อน (Session 32 trace: เป็น nice-to-have ไม่ใช่ critical path) |
| 🟢 today | **(Optional) Disable Dataview plugin** | ⚡ ~30 sec | Settings → Community plugins → toggle off | Norms revert Dataview blocks · plugin ไม่จำเป็นอีก · keep ไว้เผื่ออนาคตก็ได้ |
| 🟢 today | **Atomize v4 ready-to-fire (post-ATS)** — approve to spawn 4 agents เมื่อ ATS wave จบ | ⚡ Y/N | `[[ATOMIZE-V4-PLAN-OVERNIGHT-2026-05-22]]` | pre-staged plan · 12 EPs · IDs 00367-00686 · ~240 atoms · pre-flight checks §2 · fire command §7 · waiting on ATS completion + หลิว approve |
| 🟢 today | **Brand asset audit review** (top 10 gaps · 4-6 Magnific presets to add) | ⏰ | `[[BRAND-ASSET-AUDIT-OVERNIGHT-2026-05-22]]` (00-Brand) · mirror `Brand/Assets/AUDIT-OVERNIGHT-2026-05-22.md` | top blocker = Logo folder ว่าง · top quick-win = `@norm-mascot-clay-cutout` preset · 30-day fill plan §8 พร้อม approve |
| 🟢 today | **Discord bot v0.2 — drag 12 channels เข้า category + ลบ test channel + test commands** | ⏱️ ~10 min | Discord UI · right-click channel → Move Channel · IDs ใน `Norms-Corp/Discord-Bot/config/groups.json` | bot running 24/7 · ไม่ block · แต่ category = clean structure · 6 BA + 6 HW channels ลอย root · old `🍖-before-after` (id 1507301250281111562) ลบทิ้ง · test `/my_thread` `/my_hw` `/hw_status` |
| 🟢 today | **Discord bot — rename HW threads** (60 threads · default "HW N · (rename ได้)") | ⏰ ~30 min | Forum `📒-hw` × 6 groups | นักเรียนเห็นชื่อ HW จริงตามที่หลิวสอน · current default = placeholder · ไม่บังคับ urgent (default ยังใช้ได้) |
| 🟢 today | **Claude-Trading Onboarding Form** setup ใน Google Forms (paste จาก draft + ใส่ LINE OpenChat URL) | ⏰ ~20-30 min | `Norms-Corp/Claude-Trading-Class/Google-Form-Onboarding.md` | FB ประกาศแล้ว · มีคนสนใจเยอะ · ต้อง funnel เข้า LINE OpenChat ก่อน Discord · form เบามาก collect data + 5 ข้อกฎกลุ่ม |

---

## ⏸️ Waiting on หลิว data input (not aging · หลิวบอกไม่รีบ)

| Item | Where | Note |
|------|------|------|
| **NES Q&A fill 30 questions** (19 P0) | `05-Projects/NES-Indicator/Q&A-INTERVIEW-PACK-v0.1.md` | block v0.3 code · หลิวบอกจะให้ data เอง · **priority ranking ready** → `NES-SPEC-CROSSREF-OVERNIGHT-2026-05-22.md` (overnight 2026-05-22) · ตอบ Q-12/26/07/13/25 ก่อน = unlock 20 claims |
| **AI Vocab 125 fields** | `Vocabulary-Input.md` | block Twin v0.3 chart-reading · queued หลัง Norms Book |
| **TalokCafe transcript** | `data/jokes.json` | low-priority experimental |

---

## How to use

- **หลิว:** เปิดไฟล์นี้ตอนเช้า/start session · 🔥 P0 ก่อน · บอก Norms "เคลียร์ X" → Norms verify + remove
- **Norms:** ทุกครั้ง ship → append ใน priority tier (re-assess priority ตาม block count) · เช้าทุกวันเลื่อน aging · เมื่อหลิว action → remove
- **Decay:** item > 30d → Norms ถาม "ยังจะรอไหม" · sunset = ย้ายไป STATUS Paused/Sunset + log

→ ดู `[[feedback-pending-inbox-discipline]]` · `[[STATUS]]` · `[[INDEX]]`
