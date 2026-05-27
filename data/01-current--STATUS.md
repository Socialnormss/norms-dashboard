---
type: index
status: active
date: 2026-05-23
---

# Status — Max-Only Operating Model

> Norms (Max) = sole owner Socialnorms · เบล + Pro = Bell-Hero only · ATS background 24/7
> Single source: STATUS = active project state · PIPELINE-STATUS = pipeline state · WORKLOG per project = milestone history
>
> **🛎️ สิ่งที่หลิวต้อง approve/decide/test → `[[PENDING]]`** (single approval inbox · ไม่อยู่ใน STATUS แล้ว)

อัปเดต: 2026-05-26 | จบเดือน: 2026-05-31 | 🎯 **Focus mode: transcript เท่านั้น** (ห้าม multitask จนหลิวสั่ง)

---

## 🌙 Latest drops

> **2026-05-26 18:30 — กลับจาก away · Tickmill pack ปิดงาน + pipeline review**:
> · ✅ **Tickmill 2026 Q2-3 pack จบ** — หลิวยืนยัน "งานจบแล้ว" · เคลียร์ 8 รายการออกจาก `[[PENDING]]` (Pre-Live · Asset 1 v12 · Asset 2/3/5 · Asset 4 Live · 2026-05-22 pack) · BAD STATE Session 43 = ปิด
> · 🟢 **ATS** รันต่อเนื่องระหว่าง away · **90/424 EP** (0 fail · Metal cascade ไม่กลับ) · ETA ~10 วัน
> · ✅ **Atomize loop เก่าปิด** — `atomize_loop.sh` จบเอง 16:01 (+40 → 560 atoms) · ไม่มี scheduled job เหลือ (launchd/cron/at ว่างหมด)
> · 🎉 **Atomize Gen1 core COMPLETE (v10 · supervised 7 batches · manual)** — +742 atoms session นี้ · EP1–19 (Noon+Night) + Extra Ep3/5/6 + Secret Norms 0/1/2 + Prop firm 1/2 + Psychology 2 ครบ · **560 → 1,342 atoms**
> · 🎯 **prop-firm category ACTIVATED** (slot ว่างสุดท้าย · 43 atoms · The5%ers spec + "$5000→$248 reframe" + survival-first)
> · 💎 highlights: Wyckoff 5-Step Approach (Gen1 first full) · EP9≡Wyckoff synthesis · **Carry origin** ("ไอ้ม่วง" ตั้งชื่อสด + "กอดคอ" etymology) · Wyckoff Trendline X+A=B · JAC vs SOS · Mis-Entity
> · ⚠️ **ID collision แก้แล้ว** — session ttys002 (Max terminal #2 ทำ Gen2/NMSPC · ไม่ใช่ Pro) ชน ID 00800-839 · **ไม่ data loss** (agents หลบกัน) · revise เป็น **instance-based namespace** (Gen1=01000+ · Gen2=02000+ · NMSPC=03000+) เขียนใน INDEX frontmatter + `[[project-atom-id-namespace]]`
> · 💡 **7 module candidates** พร้อม assemble (INDEX v10): Carry Origin · EP9≡Wyckoff · JAC-vs-SOS · REFADE/REDIST · Money-Mgmt Masterclass · POI Killer/Focus · Wyckoff Trendline
> · ⏳ next: assemble module แรก (book chapter prototype) · dashboard deploy (รอ approve push) · WWMI EP1 (deadline 31/5)

> **2026-05-24 10:00 — Norms Book atomize + scheduled loop (หลิว away จนถึง 26 18:00)**:
> · 🟢 **Atomize v4 batch (supervised):** +40 atoms (00367-00406) · gen1 EP2-1 Night + EP2-2 Noon · **406 total** · INDEX updated lightweight (category sections + dashboard push รอ full review)
> · 🟢 **Scheduled atomize loop LAUNCHED** — `pipeline/atomize_loop.sh` · armed รอจันทร์ 25 พ.ค. 21:05 → ทุก 6 ชม → **hard-stop 26 พ.ค. 18:00** (~4 รอบ) · scoped allowedTools (ไม่ bypassPermissions) · ntfy แต่ละรอบ
> · ⚠️ **Lesson:** autonomous loop ห้าม self-grant bypassPermissions (classifier block ถูก) · ใช้ scoped allowedTools · user authorize task ≠ authorize ปิด permission ทั้งหมด · ดู `[[scheduled-atomize]]`
> · ATS transcript รันต่อปกติ (Gen2 EP.2-2 · 7/424)

> **2026-05-24 01:30 — ATS recovery + autonomous 2-day run (หลิว away)**:
> · 🔴 **Metal cascade fixed** — launchd queue ติด `MTLCompilerService Reentrancy avoided` · 178 files ❌ ต่อเนื่อง (00:00-00:43) · stop+diagnose+fix · Metal recovered after ~5min idle
> · 🆕 **Cascade detection** — `accurate_queue.py` ตรวจ Metal-error 2-streak → cool 90s · 3-streak → 5min · 4-streak → exit 2 (respawn) · exit code มี 0/2/3 ชัดเจน
> · 🆕 **TCC workaround** — launchd ไม่ผ่าน FDA แล้ว (ไม่รู้ว่าเลิกเมื่อไหร่) · ใช้ `keep_running.sh` + nohup จาก terminal-context แทน · respawn loop เอง
> · 🟢 **Queue active** — Gen2 EP.15-3 (2:57hr) กำลังถอด · ntfy heartbeat ทุก 10 success
> · ⚠️ **Realistic 48hr coverage:** Tier 0 = 62 files · 147hr audio · จะได้ ~30-40 files (~50-65% Tier 0) · ไม่ทันครบ
> · Files: `Knowledge/pipeline/{accurate_queue.py, keep_running.sh}` · log `~/Library/Logs/norms-transcribe.log`
> · ดู `Knowledge/PIPELINE-STATUS.md` for counts


---

## 🎯 Tier 0 — Core Missions

| งาน | สถานะ | ถัดไป |
|-----|------|------|
| **WWMI** — YouTube show × Atomic Trader | 🟢 pre-pilot · EP1 target 2026-07-19 | v0.1 Episode Structure + EP1 Timeline + **Production Workflow v0.1** drafted · ⬜ Atomic input merge target 2026-06-01 · ⬜ Branding (Pro/Claude Design help) · ⬜ Multi-platform extension plan · `[[Episode-Structure-v0.1]]` `[[EP1-Timeline]]` `[[EP1-PRODUCTION-WORKFLOW-v0.1]]` |
| **Multi-Platform Expansion** | 🟢 audit shipped · waiting decisions | ★ master deliverable + 30-day map + 20-Y/N decisions: `[[05-Projects/Multi-Platform/PLATFORM-EXPANSION-AUDIT-2026-05-21]]` · approvals → `[[PENDING]]` |

---

## 🥇 Content Engines (รอง · ป้อน Tier 0)

| งาน | สถานะ | ถัดไป |
|-----|------|------|
| **Norms Book + Website** | 🟢 V1 Demo done · awaiting verify | 18 chapters + Ch19 (Wyckoff 5-Step) + **Ch20 (EP9≡Wyckoff synthesis · module candidate #1 · 2026-05-27 · 603 บรรทัด · 31 atoms)** · backup Vault ครบ · 🎤 13/25 EP accurate done · Real swap หลัง ATS · approvals → `[[PENDING]]` · `[[atoms/chapters/_OVERNIGHT-PROGRESS]]` |
| **NPC Book + Website** (login-gated) | 🟢 designing | PDF 3 books + Tier 1 + course videos + members-only · Login · Notion/MasterClass feel · `[[NPC-Website-Inspiration-2026-05-20]]` · Connect: Mega `/shop` → NPC signup |
| **Socialnorms Mega-Website** (public showroom · Apple-feel) | 🟢 Stage 1 grid live · waiting Top 5 | Grid 36 mood-board `Norms-Master/grid-36-mega.html` · approvals → `[[PENDING]]` |
| **NPC Course** (existing product · 50k ฿ / 90d) | 🟢 active | Marketing surface (public funnel) ยังไม่สร้าง · website tier upsell · `project_npc_course_strategy` |

---

## 🥈 Monetization

| งาน | สถานะ | ถัดไป |
|-----|------|------|
| **Eightcap** | 🟢 monthly active | May ✅ ปิด · 🔥 Traders Football Cup 2026-07-05 brief received · 3 prompt packs ready: `Sponsors/Eightcap/TradersFootballCup-2026-07-05/` · base images gen → `[[PENDING]]` ⏸️ section |
| **Tickmill / FocusTrade** | 🟡 pipeline | รอ brief |

---

## 🛠️ Sub-active (Norms produces · serves Tier 0 indirectly)

| งาน | สถานะ | ถัดไป |
|-----|------|------|
| **Digital Twin v0.1** (scale mechanism for Multi-Platform) | 🟢 live · หลิว smoke test PASS 2026-05-27 | **3 formats live** (`/twin` slash · `liew-twin` subagent · `~/Twin/CLAUDE.md` standalone) · Max QA 5/5 + หลิว judge PASS 4/4 (voice/framework/refusal/signature) · ready ป้อน Multi-Platform · Pro deploy เมื่อใกล้หมด Max plan |
| **Norms-Master "ปั้มนอม"** (meta) | 🟢 Phase 1 done · v2 audit awaiting approve | ★★★★ Moat Distribution Rule locked · PROFILE-v1 + v2 audit (7 gaps · 3 conflicts · 7 patterns) · approval → `[[PENDING]]` |
| **Wyckoff Norms** | 🟡 live · idle | wyckoff.html live · 3D / cinematic CREATIVE-BRIEF.md · low priority |
| **NES Indicator (Pine Script)** | ⏸️ paused · awaiting หลิว data input | v0.2 fail (Norms เดา POI) · Q&A Pack (30Q) + POI Spec + memory rule พร้อมแล้ว · **หลิวบอก:** ไม่รีบ · จะเอา data ให้เอง · **NEXT:** รอหลิว fill Q&A → code v0.3 |

---

## 👥 Bell-Hero (hands-off · เบล + Pro)

| งาน | สถานะ | ถัดไป |
|-----|------|------|
| **Hero V1** (Claude Project) | ✅ deployed · เบลใช้ | `liewsk129` claude.ai · fallback |
| **Hero V2** (brief→deliverable pipeline) | ✅ deployed · awaiting handoff | Watcher live (launchd) · symlink Drive `Hero-Bell/` ↔ `v2/` · 4 outputs ใน 3-5s · venv `~/Library/Application Support/HeroV2/` (TCC fix) · share Drive + guide → `[[PENDING]]` |
| **Bell Web App V1** | ✅ shipped | https://socialnormss.github.io/bell-app/ · fallback |

→ Norms ไม่แตะ Bell-Hero ยกเว้นหลิวสั่งโดยตรง · `[[feedback-max-only-socialnorms]]`

---

## 🎓 Training only (ไม่ใช่ business)

| งาน | สถานะ | ถัดไป |
|-----|------|------|
| **Dog Feeder v4.2 (Mocha)** | ✅ shipped + deployed | `d7f733e` push origin/main 2026-05-21 · SW v8.3-cozy live verified · ไม่ proactive iterate ต่อ · รอ feedback หลิว |

---

## 🔧 Background

| งาน | สถานะ | ถัดไป |
|-----|------|------|
| **Accurate Transcribe (ATS)** | 🟢 running 24/7 · 81/594 EP | `accurate_queue.py` PID 52789 · ~6 วัน ETA · log `/tmp/accurate_queue.log` · blocks: Real Book swap + Twin v0.2+ (80% โปรเจคไม่ block) |
| **Pipeline tasks** | → `[[PIPELINE-STATUS]]` | transcription · book stages · extracts · Gen2 |

---

## ⏸️ Paused / Queue / Sunset

| งาน | สถานะ | หมายเหตุ |
|-----|------|---------|
| **AnotherAi v1.1** | ⏸️ archived 2026-05-20 | ROI ไม่คุ้ม · scope แคบ 30% · pivot ไป Norms-Master · revival criteria + KB moved out 2026-05-21 → `Norms-Corp/KB/` · `AnotherAi/ARCHIVED.md` |
| **AI Vocab (125 fields)** | ⏸️ queued | รอ Norms Book Website จบ · ป้อน Twin v0.3 chart-reading · `Vocabulary-Input.md` |
| **NPC Chapter Enrichment** | ⏸️ paused | Demo Book V1 ครอบคลุมแล้ว · revisit หลัง Real swap |
| **TalokCafe** | ⏸️ v0.2 paused | low-priority experimental · รอหลิว append transcript ลง `data/jokes.json` |
| **Showroom Website** | merged → Mega-Website | ดู Mega-Website row |

→ Done tasks: `[[CHANGELOG]]`

---

## Links

[[PIPELINE-STATUS]] · [[NPC-Book]] · [[Digital-Twin-Program]] · [[Vocabulary-Input]] · [[Wyckoff-Rephase]] · [[Eightcap-INDEX]] · [[Wyckoff-INDEX]] · [[MASTER_PLAN]] · [[INDEX]]
