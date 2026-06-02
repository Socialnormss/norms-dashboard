# Knowledge Pipeline — Master Status

อัปเดต: 2026-05-19 | อ่านไฟล์นี้แทนการ scan folders
> ⚠️ **STALE** — ค้างตั้งแต่ 05-19 · live progress จริง (atomize waves) ดู `SYNC/MAX-LOG.md` · reconcile ตอน pipeline session ถัดไป (Norms System Map เฟส A · 2026-05-31)

---

## ⚠️ Model Strategy Change (2026-05-19)

กำลัง **re-transcribe ทุก source ด้วย accurate model** (whisper-large-v3-mlx)
- Reason: turbo (whisper-large-v3-turbo) ที่ใช้ทำของเก่า — risk "หมู→ไก่" concept error · foundation Tier 2 ฿50K ต้องแข็ง
- Strategy: side-by-side · turbo เก็บที่ `transcripts/` · accurate ใหม่ที่ `transcripts_accurate/`
- Priority: NPC Gen1 → Gen2 → NMSPC → FBLive
- Cost: ~100 ชม Mac background · $0 (local MLX)
- Command: `cd ~/Documents/Norms-Corp/Knowledge/pipeline && python3 transcribe.py --accurate --output-dir ~/Documents/Norms-Corp/Knowledge/transcripts_accurate <folder>`
- Flags: `--accurate` · `--fast` · `--output-dir <path>` · `--limit N` (test mode)

---

## Video Sources (External Drive: /Volumes/SocialNorms/)

### Turbo (legacy · เก็บไว้เป็น baseline diff)

| Source | Videos บน Drive | Transcribed (turbo) | ThinkAloud | Golden |
|--------|----------------|---------------------|------------|--------|
| NPC Gen1 | 172 | ✅ 167/172 | 0 | 0/50 |
| NPC Gen2 | 145 | ✅ 145/145 | 0 | 0 |
| NMSPC 2026 | ~60 | ✅ 30 done | 0 | 0 |
| Facebook Live | 234 | 🟡 58/234 | 0 | 0 |
| NPC Gen3 | มีใน drive | ❌ 0 | 0 | 0 |

### Accurate (re-transcribe ใหม่ · `transcripts_accurate/`)

**Update 2026-05-24 00:55:** Counts re-verified from filesystem · Tier 0 พลิกดีขึ้นมาก
**⚠️ Pipeline crash (00:00-00:43):** launchd queue เข้า Metal-reentrancy state · 178 files ❌ ต่อเนื่อง · Norms ทำ stop+diagnose+fix (2026-05-24)

**Priority logic:** Tier 0 (core ทุก source) → Tier 1 (supplementary) · ตาม `CORE_PATTERNS` ใน `accurate_queue.py`

| Source | Total | Done (txt) | Core done | Core pending | Supp pending |
|--------|------:|-----:|----------:|-------------:|-------------:|
| NPC Gen1 | 172 | 143 | **54/54 ✅** | **0** | 25 |
| NPC Gen2 | 145 | 27 | 26/61 | **35** | 83 |
| NMSPC 2026 | 62 | 7 | 3/30 | **27** | 28 |
| Facebook Live | 227 | 0 | — | 0 | 226 |
| **Queue total** | — | — | — | **62 (Tier 0)** | **362 (Tier 1)** |

> 🟧 **Priority insert 2026-05-27:** FB Live `เงินอยู่ตรงไหน.mp4` + `สอนหาLIQUIDITY - เงินอยู่ตรงไหน.mp4` — transcribe คู่ขนาน ATS หลัก (ไม่มี Metal contention) นอกคิวปกติ · feeds Liquidity track free lesson · → atom-LIQ-NNN (namespace แยก) · DONE marker + merge plan ที่ `Norms-Book/atoms/tracks/liquidity-money/_MANIFEST.md` · ดู `[[project-liquidity-money-insert]]`

**Excluded (ไม่ทำเลย · หลิว-confirmed 2026-05-21):**
- Pre-EP Gen1 (4 ไฟล์ · Pre1-1, Pre1-2, Pre2-1, Pre2-2 — Screen Recording ก่อน course เริ่ม · ไม่มีเนื้อหา)
- Pattern: `EXCLUDE_PATTERNS` ใน `accurate_queue.py` · ครอบ gen2 ด้วยถ้ามี Pre

**Known SKIP (defer · ไม่เร่ง · หลิว-confirmed 2026-05-28):**
- `npc_gen2/Plan 1.8.2025.mp4` (267 MB · Tier 1 supplementary · `.SKIP` marker = ffmpeg timeout 2026-05-24 Metal cascade)
- ผลกระทบ: Gen2 = 144/145 (99%) · ไม่กระทบ Norms Book (ใช้ `Gen2 EP.*` Tier 0)
- Retry: ลบ `.SKIP` + split ไฟล์ครึ่งทาง ตอนคิวว่าง · ปล่อยไว้ตอนนี้

**⚠️ Lesson learned:** เดิม `build_queue()` ใช้ alphabetical sort → DATE-only/BT/CPI (supp) มาก่อน EP* (core) → เผา 89 ชม. กับ supplementary
**แก้แล้ว 2026-05-21:** `CORE_PATTERNS` per source + 2-tier queue · core ทุก source ก่อน supp ทุก source

**Auto-recovery (2026-05-21):** `com.socialnorms.transcribe` launchd ฟื้นแล้ว · KeepAlive=true · ThrottleInterval=300s
- Wrapper: `~/Library/Application Support/Norms/run_accurate_queue.sh` (TCC-safe path)
- Lock: `pgrep -f accurate_queue.py` กัน double-run
- Log: `~/Library/Logs/norms-transcribe.log`
- **⚠️ ต้อง grant FDA** ที่ System Settings → Privacy & Security → Full Disk Access: `/bin/bash` + `/usr/bin/python3`

**Auto-recovery (2026-05-21):** `com.socialnorms.transcribe` launchd ฟื้นแล้ว · KeepAlive=true · ThrottleInterval=300s
- Wrapper: `~/Library/Application Support/Norms/run_accurate_queue.sh` (TCC-safe path)
- Lock: `pgrep -f accurate_queue.py` กัน double-run
- Log: `~/Library/Logs/norms-transcribe.log`
- **⚠️ ต้อง grant FDA** ที่ System Settings → Privacy & Security → Full Disk Access: `/bin/bash` + `/usr/bin/python3`

> อัปเดต column นี้ทุกครั้งที่รัน transcribe หรือ ThinkAloud

---

## Transcript Indices (auto · heuristic · turbo-based · 2026-05-19)

| Source | Index file | Total | Score 5 | Score 4 |
|--------|-----------|-------|---------|---------|
| NPC Gen1 (hand-curated) | `transcripts/NPC-TRANSCRIPT-INDEX.md` | ~110 EP + Live | manual | manual |
| NPC Gen2 | `transcripts/NPC-GEN2-INDEX.md` | 145 | 21 | 34 |
| NMSPC main | `transcripts/NMSPC-INDEX.md` | 30 | 1 | 14 |
| NMSPC misc | `transcripts/NMSPC-MISC-INDEX.md` | 12 | 2 | 2 |
| NMSPC plan | `transcripts/NMSPC-PLAN-INDEX.md` | 20 | 3 | 7 |
| Facebook Live | `transcripts/FBLIVE-INDEX.md` | 222 | 23 | 28 |

**Heuristic:** Score by tech term density in first 5k chars (Wyckoff/SMC/NES variants/Thai equivalents). ⚠️ Approximate — Phase 1 reading จะ refine.
**Tool:** `python3 /tmp/transcript_indexer.py <input_dir> <output_md> [title]` · ใช้ regenerate ได้ทุกเมื่อ

---

## Norms Book — Progress

| เล่ม | Source | Extracts | Chapters | Output |
|------|--------|----------|---------|--------|
| NPC Gen1 — เล่ม 1 "อ่านตลาดให้ขาด" | Gen1 Core EP | 167/168 ✅ | 22/22 ✅ | ⏳ Stage 4 PDF |
| NPC Gen1 — เล่ม 2 "ตลาดบอกอะไร" | Gen1 Live | 167/168 ✅ | 18/18 ✅ | ⏳ Stage 4 PDF |
| NPC Gen1 — เล่ม 3 "Trader ที่ใช่" | Gen1 Extra | 167/168 ✅ | 18/18 ✅ | ⏳ Stage 4 PDF |
| NPC Gen2 | Gen2 | 37/145 🟡 | 0 | ❌ |
| NMSPC | NMSPC 2026 | 0 | 0 | ❌ รอ ThinkAloud |
| Facebook Live | Facebook Live | 0 | 0 | ❌ รอ transcript |

**Stage 4 PDF command:**
```bash
cd ~/Documents/Norms-Corp/Knowledge/pipeline
python3 stage4_pdf.py --book 1   # A5, no margins, BG ON
python3 stage4_pdf.py --book 2
python3 stage4_pdf.py --book 3
```

---

## AI Empire — Dependency Chain

```
[BLOCKED] หลิวกรอก Vocabulary (125 fields)
    └→ ThinkAloud Agent ทำงานได้
        └→ Logic Notes (target: 50 golden)
            └→ Digital Twin training
                └→ The Guardian
                    └→ Task Manager
```

**Vocabulary file:** `vocabulary/Vocabulary-Input.md` ← หลิวต้องกรอก

---

## Commands

```bash
cd ~/Documents/Norms-Corp/Knowledge/pipeline

# Transcribe (external drive ต้อง mount ก่อน)
python3 transcribe.py npc_gen2
python3 transcribe.py facebook_live

# Book pipeline
python3 book_pipeline.py status      # เช็คสถานะ
python3 book_pipeline.py stage3      # เขียนบทที่เหลือ

# Gen2 extract
python3 book_pipeline_gen2.py [EP]

# Dashboard
python3 dashboard.py                 # → http://localhost:8888
```

---

## File Locations

```
Knowledge/
├── PIPELINE-STATUS.md        ← ไฟล์นี้ (อ่านก่อนเสมอ)
├── pipeline/                 ← scripts ทั้งหมด
│   ├── transcribe.py
│   ├── book_pipeline.py
│   ├── book_pipeline_gen2.py
│   ├── stage4_pdf.py
│   └── thinkaloud_agent_prompt.md
├── vocabulary/               ← vocabulary + resolver
│   ├── _MASTER_VOCABULARY.json
│   ├── white_era_override.json
│   └── vocabulary_resolver.py
├── transcripts/              ← raw .txt files
│   ├── npc_gen1/   ✅
│   ├── npc_gen2/   ✅
│   ├── nmspc2026/  ✅
│   └── facebook_live/ 🟡
├── logic_notes/              ← ThinkAloud output
│   ├── Beginner/
│   ├── Intermediate/
│   └── Advanced/
└── Norms-Book/               ← หนังสือทั้งหมด
    ├── npc_gen1/   ← 3 เล่ม (Stage 3 ✅, Stage 4 ⏳)
    ├── npc_gen2/   ← กำลังทำ
    ├── nmspc/      ← รอ
    └── facebook_live/ ← รอ
```

> ⚠️ ห้าม scan `transcripts/npc_gen1/` หรือ `Norms-Book/npc_gen1/master_index.json` โดยตรง
> อ่าน `NPC-TRANSCRIPT-INDEX.md` หรือ `Norms-Book/npc_gen1/stage1_report.md` แทน
