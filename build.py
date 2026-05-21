#!/usr/bin/env python3
"""
Norms Mission Control — Dashboard v2
Operations cockpit · tracks every dimension of the empire
"""

import json, os, datetime, subprocess, re
from pathlib import Path

# ─── PATHS ──────────────────────────────────────────────────────────
HOME      = Path.home()
NC        = HOME / "Documents/Norms-Corp"
VAULT     = HOME / "Documents/Obsidian Vault/Social Norms"
KV        = NC / "Knowledge"
TRANS     = KV / "transcripts"
TRANS_ACC = KV / "transcripts_accurate"
MEMORY    = HOME / ".claude/projects/-Users-liew/memory"
DRIVE     = Path("/Volumes/SocialNorms")
FB_SRC    = DRIVE / "SocialNorms PV Course/FacebookLive"
DRAFTS    = KV / "content_drafts"
OUT       = Path(__file__).parent / "index.html"

# ─── DEADLINES ──────────────────────────────────────────────────────
NPC_DEADLINE = datetime.date(2026, 7, 19)
TODAY        = datetime.date.today()
NOW          = datetime.datetime.now()

# ─── HELPERS ────────────────────────────────────────────────────────
def count_files(path, pattern="*"):
    if not path.exists(): return 0
    return len(list(path.glob(pattern)))

def count_txt(path):
    return count_files(path, "*.txt")

def count_txt_multi(*paths):
    return sum(count_txt(p) for p in paths)

def count_mp4(path):
    if not path.exists(): return 0
    return sum(1 for ext in ("*.mp4", "*.mov", "*.m4v")
               for f in path.glob(ext) if not f.name.startswith("._"))

def get_size_human(bytes_):
    for unit in ['B','KB','MB','GB']:
        if bytes_ < 1024: return f"{bytes_:.1f}{unit}"
        bytes_ /= 1024
    return f"{bytes_:.1f}TB"

def get_relative_time(timestamp):
    """epoch → 'X min ago'"""
    delta = datetime.datetime.now().timestamp() - timestamp
    if delta < 60: return f"{int(delta)}s ago"
    if delta < 3600: return f"{int(delta/60)}m ago"
    if delta < 86400: return f"{int(delta/3600)}h ago"
    return f"{int(delta/86400)}d ago"

# ─── DATA COLLECTORS ────────────────────────────────────────────────

def collect_pipeline():
    """Transcription + book stages"""
    nmspc_done = count_txt_multi(TRANS/"nmspc2026", TRANS/"nmspc2026_misc", TRANS/"nmspc2026_plan")
    accurate_done = count_txt(TRANS_ACC/"npc_gen1")
    return {
        "accurate":  {"done": accurate_done, "total": 25,  "label": "Accurate Batch", "icon": "🔥", "priority": True},
        "npc_gen1":  {"done": count_txt(TRANS/"npc_gen1"),      "total": 168, "label": "NPC Gen1 turbo", "icon": "🎙️"},
        "npc_gen2":  {"done": count_txt(TRANS/"npc_gen2"),      "total": 145, "label": "NPC Gen2",       "icon": "🎙️"},
        "nmspc":     {"done": nmspc_done,                       "total": max(nmspc_done, 62), "label": "NMSPC 2026", "icon": "🎙️"},
        "facebook":  {"done": count_txt(TRANS/"facebook_live"), "total": count_mp4(FB_SRC) or 234, "label": "Facebook Live", "icon": "📺"},
    }

def collect_running():
    """ps aux for background jobs"""
    try:
        out = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=3).stdout
    except Exception:
        return []
    jobs = []
    for line in out.splitlines():
        if "transcribe.py" in line and "grep" not in line:
            m = re.search(r"--file\s+(\S+(?:\s\S+)*?)(?:\s--|$)", line)
            file_target = m.group(1) if m else "unknown"
            jobs.append({"type": "transcribe", "label": f"Accurate · {file_target[:40]}", "icon": "🎤"})
    return jobs

MUST_READ_FILES = [
    # ── Working docs (current state) ────────────────────────────
    {"id":"status",        "cat":"working", "icon":"📊", "title":"STATUS · current state",        "path": VAULT/"STATUS.md",                                                       "tier":"P1"},
    {"id":"phase2",        "cat":"working", "icon":"🥇", "title":"Phase 2 Architecture",          "path": VAULT/"05-Projects/Norms-Book/Phase2-Architecture.md",                  "tier":"P1"},
    {"id":"worklog-book",  "cat":"working", "icon":"📝", "title":"Norms Book · WORKLOG",          "path": VAULT/"05-Projects/Norms-Book/WORKLOG.md",                              "tier":"P2"},
    {"id":"handoff-book",  "cat":"working", "icon":"🤝", "title":"Norms Book · Handoff",          "path": VAULT/"05-Projects/Norms-Book/Handoff.md",                              "tier":"P3"},
    {"id":"handoff-sync",  "cat":"working", "icon":"🔄", "title":"Pro↔Max · HANDOFF",             "path": NC/"SYNC/HANDOFF.md",                                                   "tier":"P2"},
    {"id":"worklog-dog",   "cat":"working", "icon":"🐕", "title":"Dog Feeder · WORKLOG (v4 plan)","path": VAULT/"05-Projects/Dog-Feeder/WORKLOG.md",                              "tier":"P2"},
    {"id":"hero-v2-setup", "cat":"working", "icon":"🦸", "title":"Hero V2 · SETUP (Drive integ.)", "path": NC/"Bell/Hero/v2/SETUP.md",                                             "tier":"P2"},

    # ── Book content (NPC course material) ──────────────────────
    {"id":"phase1-km",     "cat":"book",    "icon":"📘", "title":"Phase 1 Knowledge Map",         "path": VAULT/"05-Projects/Norms-Book/Phase1-Knowledge-Map.md",                 "tier":"P2"},
    {"id":"ch-3pillar",    "cat":"book",    "icon":"🆕", "title":"Ch 1.0 · 3-Pillar Preview",     "path": KV/"Norms-Book/npc_gen1/chapters/NEW_B1_C00_3-Pillar_Preview.md",       "tier":"NEW"},
    {"id":"ch-psy1",       "cat":"book",    "icon":"🆕", "title":"Ch 5.1 · Psy1 Intro (Day 1)",   "path": KV/"Norms-Book/npc_gen1/chapters/NEW_B5_C01_Psy1_Intro.md",             "tier":"NEW"},
    {"id":"ch-closing",    "cat":"book",    "icon":"🆕", "title":"Ch 6.20 · Market is a Game",    "path": KV/"Norms-Book/npc_gen1/chapters/NEW_B6_C20_Market_is_a_Game.md",       "tier":"NEW"},
    {"id":"ch-structure",  "cat":"book",    "icon":"🆕", "title":"Ch 3.7 · Structure 1-8",        "path": KV/"Norms-Book/npc_gen1/chapters/NEW_B3_C07_Structure_1-8_Framework.md","tier":"NEW"},
    {"id":"ch-nes-wf",     "cat":"book",    "icon":"🆕", "title":"Ch 4.5 · NES Workflow",         "path": KV/"Norms-Book/npc_gen1/chapters/NEW_B4_C05_NES_Workflow.md",           "tier":"NEW"},
    {"id":"ch-review",     "cat":"book",    "icon":"🆕", "title":"Ch 6.19 · Review System",       "path": KV/"Norms-Book/npc_gen1/chapters/NEW_B6_C19_Review_System.md",          "tier":"NEW"},
    {"id":"ch-nes-syn",    "cat":"book",    "icon":"📕", "title":"Ch 4.1 · NES Synthesis (reshape)","path": KV/"Norms-Book/npc_gen1/chapters/B1_C11_Normie_System.md",          "tier":"BOOK"},
    {"id":"ch-phase-b",    "cat":"book",    "icon":"📕", "title":"Ch 2.5 · Phase B (reshape)",    "path": KV/"Norms-Book/npc_gen1/chapters/B1_C18_Phase_B.md",                    "tier":"BOOK"},
    {"id":"ch-carry",      "cat":"book",    "icon":"📕", "title":"Ch 4.4 · Carry & Focus (reshape)","path": KV/"Norms-Book/npc_gen1/chapters/B3_C14_Carry_คืออะไร.md",         "tier":"BOOK"},
    {"id":"ch-liquidity",  "cat":"book",    "icon":"📕", "title":"Ch 3.6 · Liquidity Complex",    "path": KV/"Norms-Book/npc_gen1/chapters/B1_C13_Liquidity_4_มิติ.md",          "tier":"BOOK"},

    # ── Website content (NPC landing) ───────────────────────────
    {"id":"npc-website",   "cat":"web",     "icon":"🌐", "title":"NPC Website Content Draft",     "path": VAULT/"05-Projects/NPC/Website-Content-Draft.md",                       "tier":"WEB"},
    {"id":"brand-ci",      "cat":"web",     "icon":"🎨", "title":"Brand CI · identity",           "path": VAULT/"00-Brand/Brand_CI.md",                                           "tier":"WEB"},
    {"id":"chart-ci",      "cat":"web",     "icon":"📈", "title":"Chart CI · diagram standard",   "path": VAULT/"00-Brand/CHART-CI.md",                                           "tier":"WEB"},
    {"id":"mascot",        "cat":"web",     "icon":"🦊", "title":"Mascot reference",              "path": VAULT/"00-Brand/MASCOT-REF.md",                                         "tier":"WEB"},
    {"id":"master-plan",   "cat":"web",     "icon":"🗺️", "title":"Master Plan · brand strategy",   "path": VAULT/"00-Brand/MASTER_PLAN.md",                                        "tier":"WEB"},

    # ── Audit & reference ───────────────────────────────────────
    {"id":"audit",         "cat":"audit",   "icon":"🔍", "title":"NPC Master Audit",              "path": VAULT/"05-Projects/Norms-Book/NPC-Master-Audit-2026-05-19.md",          "tier":"P3"},
    {"id":"evidence",      "cat":"audit",   "icon":"📑", "title":"Evidence Pack",                 "path": VAULT/"05-Projects/Norms-Book/Evidence-Pack-2026-05-19.md",             "tier":"P3"},
    {"id":"lexicon",       "cat":"audit",   "icon":"📚", "title":"Canonical Lexicon",             "path": VAULT/"05-Projects/Norms-Book/Canonical-Lexicon-2026-05-19.md",         "tier":"P3"},

    # ── NPC Gen2 Lesson Notes (EP 5-9 · 2026-05-21) ────────────
    {"id":"npc-g2-index",  "cat":"lessons", "icon":"📚", "title":"NPC Gen2 EP 5-9 · INDEX",       "path": KV/"npc_gen2_lessons_ep5-9/INDEX.md",                                   "tier":"P1"},
    {"id":"npc-g2-ep05",   "cat":"lessons", "icon":"🎙️", "title":"EP 5 · Markets Discount as Trap · Quad Dance", "path": KV/"npc_gen2_lessons_ep5-9/EP-05.md",                  "tier":"P2"},
    {"id":"npc-g2-ep06",   "cat":"lessons", "icon":"🎙️", "title":"EP 6 · Top Down · Multiple TF · Flow",        "path": KV/"npc_gen2_lessons_ep5-9/EP-06.md",                  "tier":"P2"},
    {"id":"npc-g2-ep07",   "cat":"lessons", "icon":"🎙️", "title":"EP 7 · POI = Liquidity · นอก Flow ไม่เทรด",   "path": KV/"npc_gen2_lessons_ep5-9/EP-07.md",                  "tier":"P2"},
    {"id":"npc-g2-ep08",   "cat":"lessons", "icon":"🎙️", "title":"EP 8 · Flip (SRF) · ครึ่งแท่ง 50% · Mother Bar","path": KV/"npc_gen2_lessons_ep5-9/EP-08.md",                  "tier":"P2"},
    {"id":"npc-g2-ep09",   "cat":"lessons", "icon":"🎙️", "title":"EP 9 · TP 1,000 · Fibo 1.618 · Part-1 Recap",  "path": KV/"npc_gen2_lessons_ep5-9/EP-09.md",                  "tier":"P2"},

    # ── Norms Book Compliance Report (2026-05-21) ──────────────
    {"id":"compliance-2026-05-21", "cat":"book", "icon":"🔍", "title":"Compliance Report · Ch 6/12/13/14", "path": KV/"Norms-Book/atoms/chapters/_COMPLIANCE-REPORT-2026-05-21.md", "tier":"P1"},
    {"id":"summary-deck-2026-05-21", "cat":"book", "icon":"📖", "title":"Chapter Summary Deck · 18 chapters (mobile spot-check)", "path": KV/"Norms-Book/atoms/chapters/_SUMMARY-DECK-2026-05-21.md", "tier":"P1"},
    {"id":"edits-applied-2026-05-21", "cat":"book", "icon":"🛠️", "title":"Edits Applied · Ch 14/13/6 (6 brand edits)", "path": KV/"Norms-Book/atoms/chapters/_EDITS-APPLIED-2026-05-21.md", "tier":"P1"},
]

CATEGORIES = [
    {"id":"working", "icon":"🏠", "label":"งานปัจจุบัน"},
    {"id":"book",    "icon":"📚", "label":"หนังสือ NPC"},
    {"id":"lessons", "icon":"🎙️", "label":"NPC Gen2 EP 5-9"},
    {"id":"web",     "icon":"🌐", "label":"เว็บไซต์"},
    {"id":"audit",   "icon":"🔍", "label":"Audit"},
]

def collect_must_read():
    """Embed must-read files inline · accessible on mobile"""
    out = []
    for spec in MUST_READ_FILES:
        path = spec["path"]
        if not path.exists():
            continue
        try:
            content = path.read_text(encoding="utf-8")
            stat = path.stat()
            mtime_ago = get_relative_time(stat.st_mtime)
            out.append({
                "id": spec["id"],
                "cat": spec.get("cat", "working"),
                "icon": spec["icon"],
                "title": spec["title"],
                "tier": spec["tier"],
                "content": content,
                "size": len(content),
                "lines": content.count("\n") + 1,
                "mtime_ago": mtime_ago,
                "path_short": str(path).replace(str(HOME), "~"),
            })
        except Exception:
            pass
    return out

def collect_retranscribe_mission():
    """Full re-transcribe mission — accurate model across all sources"""
    # Source totals (accurate target = all 4 corpora)
    sources = [
        {"key":"npc_gen1",  "label":"NPC Gen1 (lectures)",   "path": TRANS_ACC/"npc_gen1",  "total": 168, "icon":"📘"},
        {"key":"npc_gen2",  "label":"NPC Gen2 (lectures)",   "path": TRANS_ACC/"npc_gen2",  "total": 145, "icon":"📙"},
        {"key":"nmspc",     "label":"NMSPC 2026",            "path": TRANS_ACC/"nmspc2026", "total": 62,  "icon":"📕"},
        {"key":"fblive",    "label":"Facebook Live archive", "path": TRANS_ACC/"facebook_live", "total": 234, "icon":"📺"},
    ]
    total_target = sum(s["total"] for s in sources)
    total_done = 0
    AVG_HOURS_PER_EP = 1.5  # accurate model lecture average
    for s in sources:
        done = count_txt(s["path"])
        s["done"] = done
        s["remaining"] = s["total"] - done
        s["pct"] = round(done / s["total"] * 100) if s["total"] else 0
        total_done += done
        del s["path"]  # don't serialize Path

    total_remaining = total_target - total_done

    # Read real avg min/EP from accurate_queue.py log (single source of truth)
    real_avg_min = None
    queue_log = Path("/tmp/accurate_queue.log")
    if queue_log.exists():
        try:
            for line in reversed(queue_log.read_text().splitlines()):
                m = re.search(r"avg\s+([\d.]+)\s*min", line)
                if m:
                    real_avg_min = float(m.group(1))
                    break
        except Exception:
            pass

    # Count live parallel transcribe workers (transcribe.py with --accurate)
    try:
        ps_out = subprocess.run(
            ["pgrep", "-f", "transcribe.py.*--accurate"],
            capture_output=True, text=True, timeout=3
        ).stdout
        live_workers = max(1, len([p for p in ps_out.split() if p.strip()]))
    except Exception:
        live_workers = 2

    if real_avg_min:
        AVG_HOURS_PER_EP = round(real_avg_min / 60, 2)

    hours_done = round(total_done * AVG_HOURS_PER_EP, 1)
    hours_remaining = round(total_remaining * AVG_HOURS_PER_EP, 1)
    hours_total = round(total_target * AVG_HOURS_PER_EP, 1)
    overall_pct = round(total_done / total_target * 100) if total_target else 0

    # ETA from real throughput: 24h/day × live_workers
    HOURS_PER_DAY = 24
    daily_capacity = HOURS_PER_DAY * live_workers
    days_remaining = max(1, round(hours_remaining / daily_capacity)) if hours_remaining else 0
    eta_date = (TODAY + datetime.timedelta(days=days_remaining)).isoformat() if days_remaining else TODAY.isoformat()

    return {
        "sources": sources,
        "total_target": total_target,
        "total_done": total_done,
        "total_remaining": total_remaining,
        "overall_pct": overall_pct,
        "hours_done": hours_done,
        "hours_remaining": hours_remaining,
        "hours_total": hours_total,
        "days_remaining": days_remaining,
        "eta_date": eta_date,
        "avg_h_per_ep": AVG_HOURS_PER_EP,
        "live_workers": live_workers,
    }

def collect_claude_sessions():
    """Live Claude Code sessions with token usage"""
    sessions_dir = HOME / ".claude/sessions"
    projects_dir = HOME / ".claude/projects"
    now_ms = NOW.timestamp() * 1000
    sessions = []
    if not sessions_dir.exists(): return sessions
    for sf in sorted(sessions_dir.glob("*.json"), key=lambda f: f.stat().st_mtime, reverse=True):
        try:
            data = json.loads(sf.read_text())
            pid = data.get("pid")
            session_id = data.get("sessionId", "")
            cwd = data.get("cwd", "")
            started_ms = data.get("startedAt", 0)
            r = subprocess.run(["ps", "-p", str(pid), "-o", "pid="], capture_output=True, text=True)
            is_alive = bool(r.stdout.strip())
            runtime_min = int((now_ms - started_ms) / 60000) if started_ms else 0
            tokens = {"in": 0, "out": 0, "cache": 0, "latest_cache": 0, "msgs": 0, "pct": 0}
            name = ""
            for proj_subdir in projects_dir.iterdir():
                if not proj_subdir.is_dir(): continue
                jsonl_path = proj_subdir / f"{session_id}.jsonl"
                if jsonl_path.exists():
                    try:
                        lines = jsonl_path.read_text(encoding="utf-8", errors="ignore").splitlines()
                        latest = 0
                        for line in lines:
                            try:
                                d = json.loads(line)
                                if d.get("type") == "assistant" and isinstance(d.get("message"), dict):
                                    u = d["message"].get("usage", {})
                                    tokens["in"] += u.get("input_tokens", 0)
                                    tokens["out"] += u.get("output_tokens", 0)
                                    cr = u.get("cache_read_input_tokens", 0)
                                    tokens["cache"] += cr
                                    if cr > latest: latest = cr
                                    tokens["msgs"] += 1
                                if not name and d.get("type") == "user":
                                    msg = d.get("message", {}); content = msg.get("content", "")
                                    if isinstance(content, list):
                                        for block in content:
                                            if isinstance(block, dict) and block.get("type") == "text":
                                                content = block.get("text", ""); break
                                    if isinstance(content, str):
                                        text = content.strip()
                                        if text and not text.startswith("<") and "caveat" not in text.lower():
                                            name = text.splitlines()[0].strip()[:60]
                            except Exception: pass
                        tokens["latest_cache"] = latest
                        tokens["pct"] = min(100, round(latest / 2000))  # 200k context
                    except Exception: pass
                    break
            sessions.append({
                "pid": pid, "session_id": session_id[:8], "cwd": Path(cwd).name if cwd else "",
                "name": name or "untitled", "alive": is_alive, "runtime_min": runtime_min,
                "tokens": tokens, "warn": tokens["pct"] > 75
            })
        except Exception: pass
    return sessions[:6]

REPOS = [
    ("dashboard",     NC/"IT/dashboard"),
    ("norms-website", NC/"IT/social-norms-website"),
    ("dog-feeder",    HOME/"dog-feeder"),
    ("bell-app",      NC/"Bell/app"),
    ("bell-hero",     NC/"Bell/Hero"),
]

def _git(path, *args):
    return subprocess.run(["git","-C",str(path),*args], capture_output=True, text=True, timeout=2).stdout

def collect_git_repos():
    """Multi-repo status · one subprocess per stat (was 4 per repo)"""
    out = []
    for name, path in REPOS:
        if not (path/".git").exists(): continue
        try:
            pending = len(_git(path, "status", "--porcelain").splitlines())
            log = _git(path, "log", "-1", "--format=%ct%n%s").splitlines()
            last_ts  = log[0].strip() if log else ""
            last_msg = (log[1] if len(log) > 1 else "")[:60]
            out.append({
                "name": name,
                "pending": pending,
                "last": get_relative_time(int(last_ts)) if last_ts else "—",
                "msg": last_msg,
                "status": "warn" if pending > 5 else ("dirty" if pending > 0 else "clean")
            })
        except Exception: pass
    return out

def collect_chapters():
    """Norms Book chapter inventory"""
    ch_dir = KV/"Norms-Book/npc_gen1/chapters"
    if not ch_dir.exists(): return {"total": 0, "new": 0, "edited_today": 0}
    all_files = list(ch_dir.glob("*.md"))
    new_files = [f for f in all_files if f.name.startswith("NEW_")]
    today_ts = datetime.datetime.combine(TODAY, datetime.time(0)).timestamp()
    edited_today = sum(1 for f in all_files if f.stat().st_mtime > today_ts)
    return {
        "total": len(all_files),
        "new": len(new_files),
        "edited_today": edited_today,
        "new_files": [f.name for f in sorted(new_files)],
    }

def collect_memory():
    """Memory inventory"""
    if not MEMORY.exists(): return {"total": 0, "by_type": {}}
    files = [f for f in MEMORY.glob("*.md") if f.name != "MEMORY.md"]
    by_type = {"user": 0, "feedback": 0, "project": 0, "reference": 0, "other": 0}
    for f in files:
        try:
            text = f.read_text(encoding="utf-8")[:500]
            m = re.search(r"type:\s*(\w+)", text)
            t = m.group(1) if m else "other"
            if t in by_type: by_type[t] += 1
            else: by_type["other"] += 1
        except Exception: pass
    return {"total": len(files), "by_type": by_type}

def collect_vault_stats():
    """Vault file counts per top folder"""
    if not VAULT.exists(): return []
    stats = []
    for folder in sorted(VAULT.iterdir()):
        if folder.is_dir() and not folder.name.startswith("."):
            count = sum(1 for _ in folder.rglob("*.md"))
            stats.append({"name": folder.name, "count": count})
    return stats

def collect_system_health():
    """Disk · drive · backup"""
    try:
        df = subprocess.run(["df","-h",str(HOME)], capture_output=True, text=True, timeout=2).stdout
        line = df.splitlines()[-1].split()
        disk = {"used": line[2], "total": line[1], "pct": int(line[4].rstrip("%"))}
    except Exception:
        disk = {"used": "?", "total": "?", "pct": 0}
    return {
        "disk": disk,
        "drive_mounted": DRIVE.exists(),
        "vault_exists": VAULT.exists(),
    }

def collect_phase_progress():
    """Norms Book Phase 0-4 visual progress"""
    return [
        {"phase": 0, "label": "Strategy Lock", "status": "done", "pct": 100, "note": "Tier 0-3 · NMSPC sunset · NES locked"},
        {"phase": 1, "label": "Knowledge Map", "status": "done", "pct": 100, "note": "12 EP sample · 7 B-decisions"},
        {"phase": 2, "label": "Architecture", "status": "active", "pct": 70, "note": "v1 draft · awaiting C1-C10"},
        {"phase": 3, "label": "Production", "status": "active", "pct": 35, "note": "Mechanical pass + 6 new chapters"},
        {"phase": 4, "label": "Launch", "status": "pending", "pct": 0, "note": "Legal · screening · pre-launch QA"},
    ]

# ─── PROJECTS DATA ──────────────────────────────────────────────────

PROJECTS = [
    {"id":"norms-book","icon":"🥇","title":"Norms Book + Website","tier":"P1","status":"phase1","progress":55,
     "subtitle":"NPC course flagship · ฿50K","tag":"book",
     "details":["17/17 Q sign-off complete","Phase 2 v1 · 53 NPC + 4 T1 + 4 T3","Phase 3 mechanical pass + 6 new chapters","842 lines new content","Awaiting หลิว sign-off C1-C10"],
     "next":"หลิว review → Phase 3 production","deadline":"2026-07-19"},
    {"id":"npc-website","icon":"🌐","title":"NPC Website","tier":"P1","status":"phase1","progress":35,
     "subtitle":"Apple-premium landing","tag":"website",
     "details":["Content A1-A10 locked","Visual direction notes","Hero copy locked","6-block curriculum visible","Awaiting Pro Hero cinematic"],
     "next":"Pro visual session","deadline":"2026-07-19"},
    {"id":"dog-feeder","icon":"🐕","title":"Dog Feeder v3 → v4 rebuild","tier":"P2","status":"blocked","progress":50,
     "subtitle":"Paused · cozy-reference blueprint","tag":"app",
     "details":["v3.3 deployed 0ecf375 แต่ off-spec","Authority: handoff/cozy-reference.html (792 lines)","34 PNG assets installed","Pending: topbar avatar · light-btn · tabs"],
     "next":"Full v4 rebuild ตาม blueprint (2-3h)"},
    {"id":"hero-bell","icon":"🦸","title":"Hero V1 + V2 (Bell)","tier":"P2","status":"phase1","progress":95,
     "subtitle":"V1 deployed · V2 awaiting Drive","tag":"client",
     "details":["V1 live @ liewsk129 (Claude Project)","V2 pipeline ครบ · E2E tested","launchd + watch.py + template ready","รอเบล share Drive + Desktop install"],
     "next":"Drive folder + Desktop install"},
    {"id":"bell-app","icon":"🔔","title":"Bell Web App V1","tier":"DONE","status":"done","progress":100,
     "subtitle":"Fallback · socialnormss.github.io/bell-app","tag":"client",
     "details":["Shipped 2026-05-19","Live · used as fallback","Repo: github.com/Socialnormss/bell-app"],"next":"—"},
    {"id":"transcription","icon":"🎙️","title":"Transcription Stack","tier":"P3","status":"running","progress":0,
     "subtitle":"Accurate batch · ETA ~2d","tag":"pipeline",
     "details":[],"next":"Background batch"},
    {"id":"migration","icon":"🚀","title":"Migration → Max","tier":"DONE","status":"done","progress":100,
     "subtitle":"socialnorms.t@gmail.com","tag":"infra",
     "details":["APIFY · Firebase · Backup ✅","Two-instance setup live"],"next":"—"},
    {"id":"norms-corp","icon":"🏢","title":"Norms Corp Infra","tier":"P3","status":"phase1","progress":50,
     "subtitle":"9 departments · ownership","tag":"infra",
     "details":["SYNC system live","Memory v2","Phase 2 orchestrator backlog"],"next":"Phase 2 orchestrator"},
    {"id":"digital-twin","icon":"🤖","title":"Digital Twin","tier":"BLOCKED","status":"blocked","progress":5,
     "subtitle":"AI ที่สอนแบบหลิว","tag":"future",
     "details":["50 golden notes pending","ThinkAloud Pass 2 not run","Config ready"],"next":"After transcript done"},
    {"id":"aa","icon":"⚡","title":"AnotherAi","tier":"P3","status":"research","progress":35,
     "subtitle":"NotebookLM bulk upload","tag":"knowledge",
     "details":["APIFY ready","NotebookLM MCP login","NPC transcripts pending upload"],"next":"Manual NotebookLM upload"},
    {"id":"wyckoff-norms","icon":"📈","title":"Wyckoff Norms","tier":"BACKLOG","status":"research","progress":40,
     "subtitle":"3D cinematic visual","tag":"brand",
     "details":["wyckoff.html live","CREATIVE-BRIEF.md ready"],"next":"3D/cinematic exploration"},
]

TODOS = {
    "urgent":[
        {"text":"หลิว review Phase 2 doc → sign-off C1-C10","due":"ASAP","tag":"book","emoji":"🥇"},
        {"text":"หลิว review 6 NEW chapters (Norms-Corp/.../NEW_*.md)","due":"ASAP","tag":"book","emoji":"📕"},
        {"text":"Dog Feeder v4 rebuild (cozy-reference blueprint · 2-3h)","due":"next session","tag":"app","emoji":"🐕"},
        {"text":"Hero V2: Drive folder share + Desktop install + launchd load","due":"รอเบล","tag":"client","emoji":"🦸"},
    ],
    "soon":[
        {"text":"Phase 3 production round 2: rewrite per locked decisions","due":"after sign-off","tag":"book","emoji":"📚"},
        {"text":"File rename: B1_C11 NES_Synthesis · B1_C13 Liquidity_Complex","due":"after sign-off","tag":"book","emoji":"📝"},
        {"text":"Tier 1 packaging: Prop Firm Challenge (4 chapters ready)","due":"after sign-off","tag":"book","emoji":"📦"},
        {"text":"Pro Hero visual session — NPC Website cinematic","due":"parallel · ไม่ block","tag":"website","emoji":"🎨"},
        {"text":"Eightcap June brief · World Cup + event","due":"June","tag":"sponsor","emoji":"📰"},
        {"text":"NotebookLM bulk upload NPC transcripts (manual)","due":"this week","tag":"knowledge","emoji":"📒"},
    ],
    "backlog":[
        {"text":"Wyckoff Norms 3D / cinematic visual","due":"ongoing","tag":"brand","emoji":"📈"},
        {"text":"AI Vocab (125 fields)","due":"after Book","tag":"book","emoji":"📒"},
        {"text":"Tickmill / FocusTrade sponsor","due":"TBD","tag":"sponsor","emoji":"💼"},
        {"text":"NPC Gen2 + NMSPC + FBLive books","due":"after transcript","tag":"book","emoji":"📚"},
        {"text":"Digital Twin: ThinkAloud Pass 2","due":"after transcript","tag":"knowledge","emoji":"🤖"},
        {"text":"Norms Corp Phase 2 orchestrator","due":"next month","tag":"infra","emoji":"🏢"},
    ],
}

# ─── BUILD ──────────────────────────────────────────────────────────

def build():
    ts = NOW.strftime("%Y-%m-%dT%H:%M:%S")
    ts_thai = NOW.strftime("%d %b %y · %H:%M")
    days_left = (NPC_DEADLINE - TODAY).days

    pipeline = collect_pipeline()
    running = collect_running()
    sessions = collect_claude_sessions()
    git_repos = collect_git_repos()
    chapters = collect_chapters()
    memory = collect_memory()
    vault = collect_vault_stats()
    system = collect_system_health()
    phases = collect_phase_progress()
    mission = collect_retranscribe_mission()
    must_read = collect_must_read()

    # Pipeline-derived values
    pipe_total_done = sum(v["done"] for v in pipeline.values())
    pipe_total_max = sum(v["total"] for v in pipeline.values())
    pipe_pct = round(pipe_total_done / pipe_total_max * 100) if pipe_total_max else 0
    accurate_pct = round(pipeline["accurate"]["done"] / pipeline["accurate"]["total"] * 100)

    alive_count = sum(1 for s in sessions if s["alive"])
    git_dirty = sum(1 for r in git_repos if r["status"] != "clean")

    # Update transcription project details
    for p in PROJECTS:
        if p["id"] == "transcription":
            p["progress"] = accurate_pct
            p["details"] = [
                f"🔥 Accurate: {pipeline['accurate']['done']}/{pipeline['accurate']['total']} EP ({accurate_pct}%)",
                f"Gen1 turbo: {pipeline['npc_gen1']['done']}/{pipeline['npc_gen1']['total']}",
                f"Gen2: {pipeline['npc_gen2']['done']}/{pipeline['npc_gen2']['total']}",
                f"NMSPC: {pipeline['nmspc']['done']}/{pipeline['nmspc']['total']}",
                f"FB Live: {pipeline['facebook']['done']}/{pipeline['facebook']['total']}",
            ]

    deadline_color = "var(--red)" if days_left <= 14 else "var(--amber)" if days_left <= 30 else "var(--green)"
    deadline_glow = "var(--red-glow)" if days_left <= 14 else "var(--amber-glow)" if days_left <= 30 else "var(--green-glow)"

    # ─── JSON payload (compact) ──────────────────────────────────────
    payload = {
        "ts": ts,
        "days_left": days_left,
        "pipeline": pipeline,
        "running": running,
        "sessions": sessions,
        "git_repos": git_repos,
        "chapters": chapters,
        "memory": memory,
        "vault": vault,
        "system": system,
        "phases": phases,
        "mission": mission,
        "must_read": must_read,
        "categories": CATEGORIES,
        "projects": PROJECTS,
        "todos": TODOS,
        "stats": {
            "alive": alive_count,
            "git_dirty": git_dirty,
            "pipe_pct": pipe_pct,
            "accurate_pct": accurate_pct,
            "chapters_total": chapters["total"],
            "chapters_new": chapters["new"],
            "memory_total": memory["total"],
        },
    }

    html = HTML_TEMPLATE.format(
        ts=ts, ts_thai=ts_thai, days_left=days_left,
        deadline_color=deadline_color, deadline_glow=deadline_glow,
        alive_count=alive_count, git_dirty=git_dirty,
        accurate_pct=accurate_pct, accurate_done=pipeline['accurate']['done'],
        chapters_new=chapters['new'], chapters_total=chapters['total'],
        memory_total=memory['total'],
        disk_pct=system['disk']['pct'], disk_used=system['disk']['used'],
        drive_ok="✓" if system['drive_mounted'] else "✗",
        drive_color="var(--green)" if system['drive_mounted'] else "var(--red)",
        payload_json=json.dumps(payload, ensure_ascii=False),
    )
    return html

# ─── HTML TEMPLATE (large · use {{ }} for literal braces) ───────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no,viewport-fit=cover">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black">
<meta name="apple-mobile-web-app-title" content="Norms Mission Control">
<meta name="theme-color" content="#050505">
<meta name="build-time" content="{ts}">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<title>Norms · Mission Control</title>
<link rel="manifest" href="manifest.json">
<style>
:root{{
  /* Brand CI · Wyckoff Norms ─────────────────────────────── */
  --bg:#0A0A0B;--base:#101011;--surface:#161618;--raised:#1C1C1F;--overlay:#252528;
  --amber:#C07840;--amber-2:#E0944A;--amber-soft:#8B5E36;
  --amber-glow:rgba(192,120,64,.4);
  --slate:#5A5F6E;--slate-light:#7C8294;
  --text:#F0EDE8;--t2:#A8A49E;--muted:#615D58;
  --border:rgba(240,237,232,.06);
  --border-glow:rgba(192,120,64,.25);
  /* Status indicators only (small dots/badges · not card backgrounds) */
  --green:#3BCC8B;--green-glow:rgba(59,204,139,.4);
  --red:#E15461;--red-glow:rgba(225,84,97,.4);
  --yellow:#E8B547;
  --r:16px;--r-sm:10px;
  --sb:env(safe-area-inset-bottom);
}}
*{{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}}
@keyframes pulse-glow{{0%,100%{{opacity:.5;transform:scale(.9)}}50%{{opacity:1;transform:scale(1.1)}}}}
@keyframes pulse-dot{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
@keyframes shimmer{{0%{{background-position:-200% 0}}100%{{background-position:200% 0}}}}

html,body{{height:100%;background:var(--bg);color:var(--text);
  font-family:-apple-system,"SF Pro Display","Helvetica Neue",Sarabun,sans-serif;
  font-size:15px;line-height:1.45;overflow-x:hidden;
  scrollbar-width:none;-ms-overflow-style:none;
  -webkit-text-size-adjust:100%;text-size-adjust:100%}}
html::-webkit-scrollbar,body::-webkit-scrollbar,*::-webkit-scrollbar{{width:0;height:0;display:none}}
body{{background:radial-gradient(ellipse at top,rgba(192,120,64,.04),transparent 55%),
                var(--bg);min-height:100vh}}

/* ── TOPBAR ────────────────────────────────────────────────────── */
.topbar{{position:sticky;top:0;z-index:50;
  background:rgba(10,10,11,.96);backdrop-filter:blur(24px) saturate(180%);
  -webkit-backdrop-filter:blur(24px) saturate(180%);
  border-bottom:1px solid var(--border);padding:10px 16px}}
.topbar-row{{display:flex;align-items:center;gap:10px;max-width:1400px;margin:0 auto;flex-wrap:nowrap}}
.logo{{font-weight:900;font-size:13px;letter-spacing:.04em;white-space:nowrap;
  color:var(--amber-2);flex-shrink:0}}
.logo-pulse{{display:inline-block;width:7px;height:7px;border-radius:50%;
  background:var(--green);box-shadow:0 0 10px var(--green-glow);
  animation:pulse-glow 2s infinite;margin-right:6px;vertical-align:middle}}
.update-ts{{margin-left:auto;font-size:11px;color:var(--t2);font-weight:600;
  letter-spacing:.02em;font-feature-settings:"tnum";white-space:nowrap;flex-shrink:0}}
.h-stats{{display:flex;gap:14px;align-items:center;flex-shrink:0;margin-left:8px}}
.h-stat{{display:flex;flex-direction:column;align-items:flex-end;line-height:1}}
.h-stat-n{{font-size:15px;font-weight:800;font-feature-settings:"tnum";color:var(--text)}}
.h-stat-l{{font-size:8px;color:var(--muted);font-weight:700;letter-spacing:.08em;
  text-transform:uppercase;margin-top:3px}}
@media (max-width:540px){{.h-stats{{display:none}}}}

/* ── LAYOUT ────────────────────────────────────────────────────── */
.app{{max-width:1400px;margin:0 auto;padding:16px;padding-bottom:calc(150px + var(--sb))}}
.panel{{display:none;animation:fadein .25s ease}}
.panel.active{{display:block}}
@keyframes fadein{{from{{opacity:0;transform:translateY(6px)}}to{{opacity:1;transform:translateY(0)}}}}
.grid{{display:grid;gap:14px}}
.grid-2{{grid-template-columns:repeat(2,1fr)}}
.grid-3{{grid-template-columns:repeat(3,1fr)}}
.grid-4{{grid-template-columns:repeat(4,1fr)}}
@media (max-width:760px){{.grid-3,.grid-4{{grid-template-columns:repeat(2,1fr)}}}}
@media (max-width:480px){{.grid-2,.grid-3,.grid-4{{grid-template-columns:1fr}}}}

/* ── RE-TRANSCRIBE MISSION ────────────────────────────────────── */
.mission-box{{position:relative;border-radius:var(--r);overflow:hidden;
  background:linear-gradient(135deg,#181208 0%,#101011 100%);
  border:1px solid var(--border-glow);
  padding:20px 22px;margin-bottom:18px;
  box-shadow:0 0 30px var(--amber-glow),inset 0 1px 0 rgba(255,255,255,.03)}}
.mission-box::after{{content:"";position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--amber),transparent);
  animation:shimmer 5s linear infinite;background-size:200% 100%}}
.mission-head{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px;flex-wrap:wrap;position:relative;z-index:1}}
.mission-title-wrap{{flex:1;min-width:200px}}
.mission-eyebrow{{font-size:10px;font-weight:800;letter-spacing:.15em;text-transform:uppercase;
  color:var(--amber-2);margin-bottom:4px}}
.mission-title{{font-size:18px;font-weight:800;letter-spacing:-.01em;color:var(--text)}}
.mission-sub{{font-size:12px;color:var(--t2);margin-top:2px;line-height:1.4}}
.mission-eta{{text-align:right;flex-shrink:0}}
.mission-eta-n{{font-size:30px;font-weight:900;line-height:1;letter-spacing:-.02em;
  color:var(--amber-2);font-feature-settings:"tnum"}}
.mission-eta-l{{font-size:9px;color:var(--t2);font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin-top:3px}}
.mission-eta-date{{font-size:10px;color:var(--amber);font-weight:700;margin-top:4px;font-feature-settings:"tnum"}}

/* mega progress bar */
.mission-mega-bar{{height:12px;background:rgba(255,255,255,.04);border-radius:6px;overflow:hidden;
  position:relative;margin-bottom:12px;border:1px solid var(--border)}}
.mission-mega-fill{{height:100%;border-radius:6px;position:relative;overflow:hidden;
  background:linear-gradient(90deg,var(--amber),var(--amber-2));
  box-shadow:0 0 10px var(--amber-glow);
  transition:width 1.2s cubic-bezier(.2,.8,.2,1)}}
.mission-mega-fill::after{{content:"";position:absolute;inset:0;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.25),transparent);
  background-size:200% 100%;animation:shimmer 2.5s linear infinite}}
.mission-mega-pct{{position:absolute;top:50%;left:50%;translate:-50% -50%;
  font-size:10px;font-weight:800;color:var(--text);font-feature-settings:"tnum";
  text-shadow:0 0 4px rgba(0,0,0,.8)}}

/* mission stats grid */
.mission-stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:14px}}
@media (max-width:640px){{.mission-stats{{grid-template-columns:repeat(2,1fr)}}}}
.ms{{padding:10px 12px;background:rgba(255,255,255,.025);border-radius:8px;
  border:1px solid var(--border)}}
.ms-n{{font-size:18px;font-weight:800;line-height:1;font-feature-settings:"tnum";color:var(--text)}}
.ms-l{{font-size:9px;color:var(--t2);font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-top:4px}}

/* per-source breakdown */
.mission-src-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}}
@media (max-width:520px){{.mission-src-grid{{grid-template-columns:1fr}}}}
.msrc{{background:rgba(255,255,255,.02);border:1px solid var(--border);
  border-radius:8px;padding:10px 12px;min-width:0}}
.msrc-h{{display:flex;align-items:center;gap:6px;margin-bottom:6px}}
.msrc-icon{{font-size:14px;flex-shrink:0}}
.msrc-l{{font-size:11px;font-weight:700;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text)}}
.msrc-pct{{font-size:10px;font-weight:800;color:var(--amber-2);font-feature-settings:"tnum";flex-shrink:0}}
.msrc-nums{{font-size:10px;color:var(--muted);margin-bottom:6px;font-feature-settings:"tnum"}}
.msrc-bar{{height:4px;background:rgba(255,255,255,.04);border-radius:2px;overflow:hidden}}
.msrc-fill{{height:100%;background:linear-gradient(90deg,var(--amber),var(--amber-2));
  transition:width 1s cubic-bezier(.2,.8,.2,1);border-radius:2px}}
.msrc-fill.done{{background:var(--green);box-shadow:0 0 5px var(--green-glow)}}

/* ── HERO COUNTDOWN ───────────────────────────────────────────── */
.hero-mission{{position:relative;border-radius:var(--r);overflow:hidden;
  background:linear-gradient(135deg,#1a1108 0%,#101011 100%);
  border:1px solid var(--border-glow);
  padding:22px 22px;margin-bottom:18px;
  box-shadow:0 0 40px var(--amber-glow),inset 0 1px 0 rgba(255,255,255,.03)}}
.hero-mission::before{{content:"";position:absolute;inset:0;
  background:radial-gradient(circle at 80% 50%,var(--amber-glow),transparent 55%);
  opacity:.3;pointer-events:none}}
.hero-mission::after{{content:"";position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--amber),transparent);
  animation:shimmer 5s linear infinite;background-size:200% 100%}}
.hero-row{{display:flex;align-items:center;gap:20px;position:relative;z-index:1;flex-wrap:wrap}}
.hero-count{{font-size:80px;font-weight:900;line-height:.9;letter-spacing:-.04em;
  font-feature-settings:"tnum";color:{deadline_color};
  text-shadow:0 0 24px {deadline_glow}}}
.hero-text{{flex:1;min-width:200px}}
.hero-eyebrow{{font-size:10px;font-weight:800;letter-spacing:.15em;text-transform:uppercase;
  color:var(--amber-2);margin-bottom:6px}}
.hero-title{{font-size:22px;font-weight:800;letter-spacing:-.01em;margin-bottom:4px;color:var(--text)}}
.hero-sub{{font-size:12.5px;color:var(--t2);margin-bottom:10px;line-height:1.4}}
.hero-phase-strip{{display:flex;gap:4px;margin-top:8px}}
.phase-pill{{flex:1;height:5px;border-radius:3px;background:var(--surface);overflow:hidden;position:relative}}
.phase-pill .fill{{position:absolute;inset:0;border-radius:3px;
  transition:transform .8s cubic-bezier(.2,.8,.2,1)}}
.phase-pill.done .fill{{background:var(--green);box-shadow:0 0 6px var(--green-glow)}}
.phase-pill.active .fill{{background:linear-gradient(90deg,var(--amber),var(--amber-2));
  box-shadow:0 0 8px var(--amber-glow)}}
.phase-pill.pending{{opacity:.2}}

/* ── KPI CARDS · brand-only palette ───────────────────────────── */
.kpi-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:18px}}
@media (max-width:760px){{.kpi-row{{grid-template-columns:repeat(2,1fr)}}}}
.kpi{{position:relative;border:1px solid var(--border);border-radius:var(--r);
  padding:14px 14px 12px;overflow:hidden;background:var(--raised);
  transition:transform .15s,border-color .2s}}
.kpi:hover{{transform:translateY(-2px);border-color:var(--border-glow)}}
.kpi::before{{content:"";position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--amber),var(--amber-2))}}
.kpi.k-done::before{{background:var(--green);opacity:.7}}
.kpi-l{{font-size:10px;font-weight:700;color:var(--t2);letter-spacing:.1em;
  text-transform:uppercase;margin-bottom:8px}}
.kpi-n{{font-size:34px;font-weight:900;line-height:1;letter-spacing:-.02em;
  font-feature-settings:"tnum";margin-bottom:4px;color:var(--amber-2)}}
.kpi.k-done .kpi-n{{color:var(--green)}}
.kpi.k-text .kpi-n{{color:var(--text)}}
.kpi-sub{{font-size:11px;color:var(--muted);font-weight:500}}

/* ── SECTION HEADER ───────────────────────────────────────────── */
.section-h{{display:flex;align-items:center;gap:10px;margin:24px 0 12px}}
.section-h-l{{font-size:10px;font-weight:800;letter-spacing:.15em;text-transform:uppercase;
  color:var(--amber)}}
.section-h-line{{flex:1;height:1px;background:linear-gradient(90deg,var(--amber),transparent)}}
.section-h-icon{{font-size:14px}}

/* ── CARD BASE ────────────────────────────────────────────────── */
.card{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r);
  padding:14px;position:relative;overflow:hidden}}
.card-h{{display:flex;align-items:flex-start;gap:10px;margin-bottom:10px}}
.card-icon{{font-size:18px;flex-shrink:0}}
.card-title{{font-size:13px;font-weight:700;line-height:1.3;margin-bottom:2px}}
.card-sub{{font-size:10px;color:var(--t2);font-weight:500}}
.card-tier{{font-size:9px;font-weight:800;letter-spacing:.08em;padding:2px 6px;
  border-radius:4px;background:var(--surface);color:var(--t2);flex-shrink:0;margin-left:auto}}
.card-tier.p1{{background:rgba(192,120,64,.2);color:var(--amber-2)}}
.card-tier.p2{{background:rgba(192,120,64,.12);color:var(--amber)}}
.card-tier.p3{{background:rgba(168,164,158,.12);color:var(--t2)}}
.card-tier.done{{background:rgba(59,204,139,.15);color:var(--green)}}
.card-tier.blocked{{background:rgba(225,84,97,.15);color:var(--red)}}
.card-tier.backlog{{background:rgba(168,164,158,.1);color:var(--muted)}}

/* progress bar */
.pbar{{height:6px;background:var(--surface);border-radius:3px;overflow:hidden;position:relative}}
.pbar-fill{{height:100%;border-radius:3px;transition:width 1s cubic-bezier(.2,.8,.2,1);
  background:linear-gradient(90deg,var(--amber),var(--amber-2))}}
.pbar-fill.done{{background:var(--green);box-shadow:0 0 6px var(--green-glow)}}
.pbar-fill.warn{{background:var(--red);box-shadow:0 0 6px var(--red-glow)}}
.pbar-fill.active{{background:linear-gradient(90deg,var(--amber),var(--amber-2));
  box-shadow:0 0 6px var(--amber-glow)}}

/* ── PROJECT GRID ─────────────────────────────────────────────── */
.proj-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}}
.proj{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r);
  padding:16px;position:relative;overflow:hidden;cursor:pointer;transition:all .2s}}
.proj:hover{{border-color:var(--border-glow);transform:translateY(-2px);
  box-shadow:0 8px 24px rgba(0,0,0,.4)}}
.proj::before{{content:"";position:absolute;top:0;left:0;bottom:0;width:3px;
  background:var(--surface);transition:background .3s}}
.proj.s-done::before{{background:var(--green);box-shadow:0 0 6px var(--green-glow)}}
.proj.s-phase1::before{{background:linear-gradient(180deg,var(--amber),var(--amber-2));
  box-shadow:0 0 6px var(--amber-glow)}}
.proj.s-running::before{{background:var(--amber-2);
  box-shadow:0 0 6px var(--amber-glow);animation:pulse-dot 2s infinite}}
.proj.s-blocked::before{{background:var(--red)}}
.proj.s-research::before{{background:var(--slate-light)}}
.proj-h{{display:flex;gap:10px;margin-bottom:10px;align-items:flex-start}}
.proj-icon{{font-size:22px;flex-shrink:0}}
.proj-title{{font-size:14px;font-weight:800;line-height:1.3;letter-spacing:-.01em}}
.proj-sub{{font-size:10px;color:var(--t2);margin-top:2px}}
.proj-details{{margin-top:10px;padding-top:10px;border-top:1px solid var(--border)}}
.proj-details li{{list-style:none;font-size:11px;color:var(--t2);
  padding:3px 0;line-height:1.4}}
.proj-next{{margin-top:8px;font-size:11px;color:var(--amber-2);font-weight:600;line-height:1.3}}
.proj-progress-row{{display:flex;align-items:center;gap:8px;margin-top:8px}}
.proj-pct{{font-size:11px;font-weight:700;color:var(--t2);
  font-feature-settings:"tnum";min-width:32px}}

/* ── PIPELINE TRACKER ─────────────────────────────────────────── */
.pipe-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px}}
.pipe{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r-sm);
  padding:12px;position:relative}}
.pipe.priority{{border-color:rgba(212,122,42,.4);
  background:linear-gradient(135deg,rgba(212,122,42,.08),var(--raised) 60%);
  box-shadow:0 0 20px rgba(212,122,42,.1)}}
.pipe-h{{display:flex;align-items:center;gap:8px;margin-bottom:8px}}
.pipe-icon{{font-size:14px}}
.pipe-l{{font-size:11px;font-weight:700;color:var(--t2);letter-spacing:.04em}}
.pipe-nums{{display:flex;align-items:baseline;gap:4px;margin-bottom:6px}}
.pipe-done{{font-size:22px;font-weight:900;line-height:1;font-feature-settings:"tnum"}}
.pipe.priority .pipe-done{{color:var(--amber-2);text-shadow:0 0 12px var(--amber-glow)}}
.pipe-sep{{color:var(--muted);font-size:14px}}
.pipe-total{{font-size:13px;color:var(--t2);font-feature-settings:"tnum"}}
.pipe-pct{{margin-left:auto;font-size:10px;font-weight:800;padding:2px 6px;border-radius:4px}}
.pipe-pct.done{{background:rgba(0,245,147,.12);color:var(--green)}}
.pipe-pct.active{{background:rgba(192,120,64,.12);color:var(--amber-2)}}
.pipe-pct.zero{{background:var(--surface);color:var(--muted)}}
.pipe-done-group{{margin-top:12px;background:var(--surface);border:1px solid var(--border);
  border-radius:var(--r-sm);overflow:hidden}}
.pipe-done-head{{display:flex;align-items:center;gap:8px;padding:10px 14px;cursor:pointer;
  user-select:none;font-size:11px;font-weight:700;color:var(--t2);letter-spacing:.04em}}
.pipe-done-head:hover{{background:rgba(255,255,255,.02)}}
.pipe-done-count{{background:rgba(0,245,147,.12);color:var(--green);
  padding:2px 7px;border-radius:4px;font-size:10px;font-weight:800}}
.pipe-done-chev{{margin-left:auto;color:var(--muted);transition:transform .25s}}
.pipe-done-group.open .pipe-done-chev{{transform:rotate(90deg);color:var(--green)}}
.pipe-done-body{{display:none;padding:0 14px 12px;border-top:1px solid var(--border)}}
.pipe-done-group.open .pipe-done-body{{display:block}}
.pipe-done-item{{display:flex;align-items:center;gap:8px;padding:8px 0;font-size:11px;
  border-bottom:1px solid rgba(255,255,255,.04)}}
.pipe-done-item:last-child{{border-bottom:none}}
.pipe-done-item-l{{color:var(--t2);flex:1}}
.pipe-done-item-n{{color:var(--green);font-weight:800;font-feature-settings:"tnum"}}

/* ── RUNNING / LIVE ───────────────────────────────────────────── */
.running-row{{display:flex;align-items:center;gap:10px;padding:10px 12px 10px 26px;
  background:var(--surface);border-radius:var(--r-sm);margin-bottom:6px;
  border-left:3px solid var(--green);position:relative}}
.running-row::before{{content:"";position:absolute;left:10px;top:50%;width:6px;height:6px;
  border-radius:50%;background:var(--green);transform:translateY(-50%);
  box-shadow:0 0 8px var(--green-glow);animation:pulse-dot 1.5s infinite}}
.running-icon{{font-size:14px}}
.running-text{{flex:1;font-size:12px;font-weight:600}}
.running-sub{{font-size:10px;color:var(--muted)}}

/* ── CLAUDE SESSIONS ──────────────────────────────────────────── */
.cl-card{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r-sm);
  padding:12px;position:relative;min-width:0;overflow:hidden}}
.cl-card.warn{{border-color:rgba(225,84,97,.3);background:linear-gradient(135deg,rgba(225,84,97,.04),var(--raised) 50%)}}
.cl-head{{display:flex;align-items:center;gap:8px;margin-bottom:8px;min-width:0}}
.cl-name{{font-size:12px;font-weight:700;flex:1;min-width:0;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--text)}}
.cl-badge{{font-size:9px;font-weight:800;padding:2px 6px;border-radius:4px;letter-spacing:.05em;flex-shrink:0}}
.cl-badge.live{{background:rgba(59,204,139,.15);color:var(--green)}}
.cl-badge.off{{background:rgba(97,93,88,.2);color:var(--muted)}}
.cl-bell{{background:transparent;border:1px solid var(--border);border-radius:6px;
  width:28px;height:24px;font-size:12px;cursor:pointer;color:var(--t2);
  display:flex;align-items:center;justify-content:center;flex-shrink:0;
  transition:all .15s;padding:0;line-height:1}}
.cl-bell:hover{{border-color:var(--amber-2);color:var(--amber-2);background:rgba(192,120,64,.08)}}
.cl-bell:active{{transform:scale(.92)}}
.cl-bell.sent{{border-color:var(--green);color:var(--green);background:rgba(59,204,139,.12)}}
.cl-bell.error{{border-color:var(--red);color:var(--red);background:rgba(225,84,97,.12)}}
.cl-meta{{font-size:9px;color:var(--muted);margin-bottom:8px;
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.cl-tokens{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:6px;margin-top:6px}}
.cl-tok{{text-align:center;padding:6px 4px;background:var(--surface);border-radius:6px;min-width:0;overflow:hidden}}
.cl-tok-n{{font-size:13px;font-weight:800;font-feature-settings:"tnum";color:var(--amber-2);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.cl-tok-l{{font-size:9px;color:var(--muted)}}

/* ── TODOS ────────────────────────────────────────────────────── */
.todo-section{{margin-bottom:16px}}
.todo-h{{display:flex;align-items:center;gap:8px;margin-bottom:8px}}
.todo-tag-l{{font-size:10px;font-weight:800;letter-spacing:.1em;text-transform:uppercase;padding:3px 8px;border-radius:4px}}
.todo-tag-l.urgent{{background:rgba(255,59,92,.15);color:var(--red)}}
.todo-tag-l.soon{{background:rgba(212,122,42,.15);color:var(--amber-2)}}
.todo-tag-l.backlog{{background:rgba(94,90,85,.15);color:var(--t2)}}
.todo-count{{font-size:11px;color:var(--muted);font-feature-settings:"tnum"}}
.todo-item{{display:flex;align-items:flex-start;gap:10px;padding:10px 12px;
  background:var(--raised);border-radius:var(--r-sm);margin-bottom:6px;
  border:1px solid var(--border);transition:all .15s}}
.todo-item:hover{{border-color:var(--border-glow)}}
.todo-emoji{{font-size:16px;flex-shrink:0}}
.todo-body{{flex:1}}
.todo-text{{font-size:12px;font-weight:500;line-height:1.4}}
.todo-meta{{display:flex;gap:8px;margin-top:4px;font-size:10px}}
.todo-due{{color:var(--amber-2);font-weight:600}}
.todo-tag-i{{color:var(--muted);font-weight:500}}
.todo-chk{{width:20px;height:20px;border-radius:50%;border:1.5px solid var(--muted);
  flex-shrink:0;cursor:pointer;display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:800;transition:all .15s}}
.todo-chk.on{{background:var(--green);border-color:var(--green);color:#000;
  box-shadow:0 0 12px var(--green-glow)}}
.todo-item.done .todo-text{{text-decoration:line-through;color:var(--muted)}}

/* ── GIT / SYSTEM ─────────────────────────────────────────────── */
.mini-card{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r-sm);
  padding:10px 12px;display:flex;align-items:center;gap:10px;min-width:0;overflow:hidden}}
.mini-icon{{font-size:14px;flex-shrink:0}}
.mini-body{{flex:1;min-width:0;overflow:hidden}}
.mini-l{{font-size:12px;font-weight:700;line-height:1.3;color:var(--text);
  overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.mini-s{{font-size:10px;color:var(--muted);margin-top:1px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.mini-badge{{font-size:9px;font-weight:800;padding:3px 6px;border-radius:4px;letter-spacing:.04em;flex-shrink:0;white-space:nowrap}}
.mini-badge.clean{{background:rgba(59,204,139,.12);color:var(--green)}}
.mini-badge.dirty{{background:rgba(192,120,64,.15);color:var(--amber-2)}}
.mini-badge.warn{{background:rgba(225,84,97,.12);color:var(--red)}}

/* ── VAULT / MEMORY STATS ─────────────────────────────────────── */
.stat-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px}}
.stat-tile{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r-sm);
  padding:12px;text-align:left}}
.stat-tile-n{{font-size:20px;font-weight:900;line-height:1;font-feature-settings:"tnum"}}
.stat-tile-l{{font-size:10px;color:var(--t2);margin-top:4px;font-weight:600}}

/* ── MODAL ────────────────────────────────────────────────────── */
.modal-bg{{position:fixed;inset:0;background:rgba(0,0,0,.7);backdrop-filter:blur(8px);
  display:none;z-index:200;align-items:center;justify-content:center;padding:20px}}
.modal-bg.open{{display:flex}}
.modal{{background:var(--base);border:1px solid var(--border-glow);border-radius:var(--r);
  padding:24px;max-width:520px;width:100%;max-height:80vh;overflow-y:auto;
  box-shadow:0 20px 60px rgba(0,0,0,.8)}}
.modal-close{{position:absolute;top:16px;right:16px;width:30px;height:30px;
  display:flex;align-items:center;justify-content:center;background:var(--surface);
  border-radius:50%;cursor:pointer;font-size:18px;line-height:1;border:none;color:var(--text)}}

/* ── BOTTOM NAV (Mission control bar) ─────────────────────────── */
.bnav{{position:fixed;bottom:calc(var(--sb) + 14px);left:50%;transform:translateX(-50%);
  background:rgba(28,28,31,.97);border:1px solid rgba(240,237,232,.1);
  border-radius:64px;padding:8px 10px;display:flex;gap:4px;
  backdrop-filter:blur(24px) saturate(180%);-webkit-backdrop-filter:blur(24px) saturate(180%);
  box-shadow:0 16px 40px rgba(0,0,0,.6),0 0 0 1px rgba(0,0,0,.4);z-index:100}}
.nb{{display:flex;flex-direction:column;align-items:center;gap:4px;padding:10px 18px;
  border:none;background:none;color:var(--text);font-size:11px;font-weight:700;
  cursor:pointer;border-radius:48px;letter-spacing:.02em;transition:all .2s;white-space:nowrap;
  opacity:.55;min-width:62px}}
.nb .ic{{font-size:22px;line-height:1;transition:transform .2s}}
.nb:hover{{opacity:.85}}
.nb.on{{background:linear-gradient(135deg,rgba(192,120,64,.28),rgba(192,120,64,.12));
  color:var(--amber-2);opacity:1;
  box-shadow:inset 0 0 0 1px rgba(192,120,64,.35),0 4px 12px rgba(192,120,64,.2)}}
.nb.on .ic{{transform:scale(1.05)}}
@media (max-width:520px){{
  .nb{{padding:9px 14px;min-width:54px;font-size:10px}}
  .nb .ic{{font-size:20px}}
}}

/* ── READ PANEL · sub-tabs ───────────────────────────────────── */
.read-tabs{{display:flex;gap:6px;overflow-x:auto;padding:2px 0 4px;margin:0;
  scrollbar-width:none;-webkit-overflow-scrolling:touch}}
.read-tabs::-webkit-scrollbar{{display:none}}
.read-tab{{display:flex;align-items:center;gap:6px;padding:8px 14px;
  background:var(--raised);border:1px solid var(--border);border-radius:50px;
  color:var(--t2);font-size:12px;font-weight:700;cursor:pointer;white-space:nowrap;
  transition:all .15s;flex-shrink:0}}
.read-tab:hover{{border-color:var(--border-glow)}}
.read-tab.on{{background:linear-gradient(135deg,rgba(192,120,64,.2),rgba(192,120,64,.08));
  border-color:rgba(192,120,64,.4);color:var(--amber-2)}}
.read-tab-ic{{font-size:14px}}
.read-tab-count{{font-size:9px;opacity:.7;font-weight:600}}

/* ── READ PANEL ────────────────────────────────────────────────── */
/* Sticky composite: search + tabs in one solid container.
   No backdrop-filter — solid bg already opaque + filter causes iOS Safari
   sticky layer bug where text bleeds through when scrolled. */
.read-sticky{{position:sticky;top:40px;z-index:40;
  background:var(--bg);
  margin:-16px -16px 14px;padding:12px 16px 6px;
  border-bottom:1px solid var(--border);
  box-shadow:0 -40px 0 var(--bg)}}
.read-search{{margin:0 0 10px}}
.read-search input{{width:100%;background:var(--raised);border:1px solid var(--border);
  border-radius:50px;padding:11px 16px;color:var(--text);font-size:14px;font-family:inherit;
  outline:none;transition:border-color .2s}}
.read-search input:focus{{border-color:var(--amber-2)}}
.read-list{{display:flex;flex-direction:column;gap:8px}}
.read-card{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r-sm);
  overflow:hidden;transition:border-color .2s}}
.read-card.open{{border-color:var(--border-glow)}}
.read-head{{display:flex;align-items:center;gap:10px;padding:12px 14px;cursor:pointer;
  user-select:none}}
.read-icon{{font-size:18px;flex-shrink:0}}
.read-body{{flex:1;min-width:0}}
.read-title{{font-size:13px;font-weight:700;line-height:1.3}}
.read-meta{{font-size:10px;color:var(--muted);margin-top:2px;font-feature-settings:"tnum"}}
.read-tier{{font-size:9px;font-weight:800;padding:3px 7px;border-radius:4px;letter-spacing:.06em;flex-shrink:0}}
.read-tier.p1{{background:rgba(192,120,64,.22);color:var(--amber-2)}}
.read-tier.p2{{background:rgba(192,120,64,.12);color:var(--amber)}}
.read-tier.p3{{background:rgba(168,164,158,.1);color:var(--t2)}}
.read-tier.new{{background:rgba(59,204,139,.15);color:var(--green)}}
.read-tier.book{{background:rgba(192,120,64,.18);color:var(--amber-2)}}
.read-tier.web{{background:rgba(124,140,148,.15);color:var(--slate-light)}}
.read-chevron{{color:var(--muted);transition:transform .25s;font-size:14px;flex-shrink:0}}
.read-card.open .read-chevron{{transform:rotate(90deg);color:var(--amber-2)}}
.read-content{{display:none;padding:0 14px 14px;border-top:1px solid var(--border);
  font-size:13px;line-height:1.6;color:var(--t2);max-height:65vh;overflow-y:auto;
  word-break:break-word;overflow-wrap:break-word}}
.read-card.open .read-content{{display:block}}
.read-content h1,.read-content h2,.read-content h3{{color:var(--text);margin:14px 0 8px;font-weight:800;letter-spacing:-.01em}}
.read-content h1{{font-size:17px}}.read-content h2{{font-size:14px;color:var(--amber-2)}}
.read-content h3{{font-size:13px;color:var(--amber)}}
.read-content p{{margin:8px 0;color:var(--t2)}}
.read-content ul,.read-content ol{{margin:8px 0;padding-left:20px}}
.read-content li{{margin:3px 0}}
.read-content code{{background:var(--surface);padding:1px 5px;border-radius:4px;
  font-family:"SF Mono",Menlo,monospace;font-size:11px;color:var(--amber-2);
  word-break:break-all}}
.read-content pre{{background:var(--surface);padding:10px;border-radius:6px;
  font-size:10.5px;line-height:1.5;margin:8px 0;border:1px solid var(--border);
  white-space:pre-wrap;word-break:break-word;overflow-x:auto}}
.read-content pre code{{background:none;padding:0;color:var(--text);word-break:normal}}
.read-content blockquote{{border-left:3px solid var(--amber);padding:6px 12px;margin:8px 0;
  background:rgba(192,120,64,.05);color:var(--t2);font-style:italic}}
/* Tables · constrained · scroll inside */
.read-content table{{width:100%;border-collapse:collapse;margin:8px 0;font-size:11px;
  table-layout:fixed;word-break:break-word}}
.read-content th,.read-content td{{padding:6px 8px;border:1px solid var(--border);text-align:left;
  vertical-align:top;overflow-wrap:break-word}}
.read-content th{{background:var(--surface);color:var(--amber-2);font-weight:700;font-size:10px}}
.read-content td{{font-size:11px}}
.read-content a{{color:var(--amber-2);text-decoration:none;border-bottom:1px dotted var(--amber)}}
.read-content .wlink{{color:var(--amber-2);background:rgba(192,120,64,.08);padding:0 4px;border-radius:3px;font-size:.94em}}
.read-content hr{{border:none;border-top:1px solid var(--border);margin:14px 0}}
.read-content strong{{color:var(--text)}}
.read-content img{{max-width:100%;height:auto}}

/* must-read shortcuts (overview panel) */
.shortcut-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(140px,1fr));gap:8px}}
.shortcut{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r-sm);
  padding:10px 12px;cursor:pointer;text-align:left;transition:all .15s;position:relative;overflow:hidden}}
.shortcut:hover{{border-color:var(--border-glow);transform:translateY(-1px)}}
.shortcut::before{{content:"";position:absolute;top:0;left:0;right:0;height:2px;
  background:linear-gradient(90deg,var(--amber),var(--amber-2));opacity:.7}}
.shortcut-icon{{font-size:18px;margin-bottom:4px}}
.shortcut-l{{font-size:11px;font-weight:700;line-height:1.3}}
.shortcut-s{{font-size:9px;color:var(--muted);margin-top:2px}}

/* update banner */
.upd{{position:fixed;top:60px;left:50%;transform:translateX(-50%);
  background:linear-gradient(135deg,var(--amber),var(--amber-2));color:#000;
  padding:8px 16px;border-radius:50px;font-size:12px;font-weight:800;
  display:none;z-index:90;cursor:pointer;box-shadow:0 4px 20px var(--amber-glow)}}
.upd.show{{display:block}}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-row">
    <div class="logo"><span class="logo-pulse"></span>NORMS · MISSION CONTROL</div>
    <div class="h-stats">
      <div class="h-stat"><span class="h-stat-n" style="color:var(--green)">{alive_count}</span><span class="h-stat-l">Live</span></div>
      <div class="h-stat"><span class="h-stat-n">{accurate_done}/25</span><span class="h-stat-l">Acc.</span></div>
      <div class="h-stat"><span class="h-stat-n">{chapters_new}</span><span class="h-stat-l">New</span></div>
      <div class="h-stat"><span class="h-stat-n" style="color:{drive_color}">{drive_ok}</span><span class="h-stat-l">Drive</span></div>
    </div>
    <span class="update-ts">{ts_thai}</span>
  </div>
</div>

<div class="upd" id="upd-banner" onclick="location.reload()">↻ New build · refresh</div>

<div class="app">

  <!-- ═══ HOME PANEL ═══════════════════════════════════════════════ -->
  <div class="panel active" id="p-home">
    <!-- Hero countdown -->
    <div class="hero-mission">
      <div class="hero-row">
        <div class="hero-count">{days_left}</div>
        <div class="hero-text">
          <div class="hero-eyebrow">🥇 NPC Mission · Norms Book + Website</div>
          <div class="hero-title">Days until launch</div>
          <div class="hero-sub">2026-07-19 · Phase 2 sign-off pending · Phase 3 production active</div>
          <div class="hero-phase-strip" id="phase-strip"></div>
        </div>
      </div>
    </div>

    <!-- KPI cards -->
    <div class="kpi-row">
      <div class="kpi">
        <div class="kpi-l">Accurate Batch</div>
        <div class="kpi-n">{accurate_pct}%</div>
        <div class="kpi-sub">{accurate_done}/25 EP · bg</div>
      </div>
      <div class="kpi k-text">
        <div class="kpi-l">Chapters · New</div>
        <div class="kpi-n">{chapters_new}/{chapters_total}</div>
        <div class="kpi-sub">drafted Phase 3</div>
      </div>
      <div class="kpi k-text">
        <div class="kpi-l">Memory</div>
        <div class="kpi-n">{memory_total}</div>
        <div class="kpi-sub">items active</div>
      </div>
      <div class="kpi k-done">
        <div class="kpi-l">Disk</div>
        <div class="kpi-n">{disk_pct}%</div>
        <div class="kpi-sub">{disk_used} used</div>
      </div>
    </div>

    <!-- Live now -->
    <div class="section-h"><span class="section-h-icon">⚡</span><span class="section-h-l">Live now</span><div class="section-h-line"></div></div>
    <div id="live-running"></div>

    <!-- Must-read shortcuts -->
    <div class="section-h"><span class="section-h-icon">📖</span><span class="section-h-l">Quick read · จากที่ไหนก็ได้</span><div class="section-h-line"></div></div>
    <div class="shortcut-grid" id="shortcut-grid"></div>
  </div>

  <!-- ═══ PROJECTS PANEL ════════════════════════════════════════════ -->
  <div class="panel" id="p-projects">
    <div class="section-h"><span class="section-h-icon">🚀</span><span class="section-h-l">Projects · priority order</span><div class="section-h-line"></div></div>
    <div class="proj-grid" id="proj-grid"></div>

    <div class="section-h"><span class="section-h-icon">📋</span><span class="section-h-l">Action items</span><div class="section-h-line"></div></div>
    <div id="todo-list"></div>
  </div>

  <!-- ═══ PIPELINE PANEL ════════════════════════════════════════════ -->
  <div class="panel" id="p-pipeline">
    <div class="section-h"><span class="section-h-icon">🎤</span><span class="section-h-l">Re-transcribe mission · accurate model</span><div class="section-h-line"></div></div>
    <div class="mission-box" id="mission-box"></div>

    <div class="section-h"><span class="section-h-icon">🎙️</span><span class="section-h-l">Transcription pipeline</span><div class="section-h-line"></div></div>
    <div class="pipe-grid" id="pipe-grid"></div>

    <div class="section-h"><span class="section-h-icon">📦</span><span class="section-h-l">Git repos · {git_dirty} dirty</span><div class="section-h-line"></div></div>
    <div class="grid grid-2" id="git-grid"></div>
  </div>

  <!-- ═══ SYSTEM PANEL ══════════════════════════════════════════════ -->
  <div class="panel" id="p-system">
    <div class="section-h"><span class="section-h-icon">⚙️</span><span class="section-h-l">Claude sessions</span><div class="section-h-line"></div></div>
    <div class="grid grid-2" id="cl-grid"></div>

    <div class="section-h"><span class="section-h-icon">🗂️</span><span class="section-h-l">Knowledge base</span><div class="section-h-line"></div></div>
    <div class="stat-grid" id="vault-grid"></div>
  </div>

  <!-- ═══ READ PANEL ════════════════════════════════════════════════ -->
  <div class="panel" id="p-read">
    <div class="read-sticky">
      <div class="read-search">
        <input type="text" id="read-search-input" placeholder="🔍 ค้นหาในไฟล์ทั้งหมด..." autocomplete="off">
      </div>
      <div class="read-tabs" id="read-tabs"></div>
    </div>
    <div class="read-list" id="read-list"></div>
  </div>

</div>

<!-- Bottom nav bar -->
<nav class="bnav">
  <button class="nb on" data-panel="p-home"><span class="ic">🏠</span><span>Home</span></button>
  <button class="nb" data-panel="p-projects"><span class="ic">🚀</span><span>Projects</span></button>
  <button class="nb" data-panel="p-pipeline"><span class="ic">🎤</span><span>Pipeline</span></button>
  <button class="nb" data-panel="p-system"><span class="ic">⚙️</span><span>System</span></button>
  <button class="nb" data-panel="p-read"><span class="ic">📖</span><span>Read</span></button>
</nav>

<!-- ── MODAL ────────────────────────────────────────────────── -->
<div class="modal-bg" id="modal-bg" onclick="if(event.target===this)closeModal()">
  <div class="modal" id="modal-content"></div>
</div>

<script>
const D = {payload_json};
const BUILD_TIME = D.ts;
const NTFY_TOPIC = 'norms-mc-5d1a901f06cf';
const NTFY_URL = `https://ntfy.sh/${{NTFY_TOPIC}}`;

async function notifyRetire(btn){{
  const pid  = btn.dataset.pid;
  const name = btn.dataset.name;
  const pct  = btn.dataset.pct;
  const orig = btn.textContent;
  btn.disabled = true;
  btn.textContent = '⏳';
  try {{
    const res = await fetch(NTFY_URL, {{
      method: 'POST',
      headers: {{
        'Title': `Norms · session ใกล้เต็ม (${{pct}}%)`,
        'Tags': 'warning,bell',
        'Priority': '4'
      }},
      body: `${{name}} · PID ${{pid}} · ขึ้น session ใหม่`
    }});
    if (!res.ok) throw new Error(res.status);
    btn.textContent = '✓';
    btn.classList.add('sent');
    setTimeout(() => {{ btn.textContent = orig; btn.classList.remove('sent'); btn.disabled = false; }}, 4000);
  }} catch (e) {{
    btn.textContent = '✗';
    btn.classList.add('error');
    setTimeout(() => {{ btn.textContent = orig; btn.classList.remove('error'); btn.disabled = false; }}, 4000);
  }}
}}

// ─── RE-TRANSCRIBE MISSION ───────────────────────────────────
function renderMission(){{
  const m = D.mission;
  const el = document.getElementById('mission-box');
  el.innerHTML = `
    <div class="mission-head">
      <div class="mission-title-wrap">
        <div class="mission-eyebrow">🎤 Full Re-transcribe · accurate (Whisper Large v3)</div>
        <div class="mission-title">${{m.total_done}} / ${{m.total_target}} EP transcribed</div>
        <div class="mission-sub">${{m.hours_done}}h done · ${{m.hours_remaining}}h remaining · ~${{m.avg_h_per_ep}}h/EP avg</div>
      </div>
      <div class="mission-eta">
        <div class="mission-eta-n">${{m.days_remaining}}</div>
        <div class="mission-eta-l">days @ 24/7 · ${{m.live_workers}}x live</div>
        <div class="mission-eta-date">ETA ${{m.eta_date}}</div>
      </div>
    </div>
    <div class="mission-mega-bar">
      <div class="mission-mega-fill" style="width:${{m.overall_pct}}%"></div>
      <div class="mission-mega-pct">${{m.overall_pct}}%</div>
    </div>
    <div class="mission-stats">
      <div class="ms"><div class="ms-n" style="color:var(--slate-light)">${{m.total_target}}</div><div class="ms-l">Total EPs</div></div>
      <div class="ms"><div class="ms-n" style="color:var(--green)">${{m.total_done}}</div><div class="ms-l">Done</div></div>
      <div class="ms"><div class="ms-n" style="color:var(--amber-2)">${{m.total_remaining}}</div><div class="ms-l">Remaining</div></div>
      <div class="ms"><div class="ms-n" style="color:var(--amber-soft)">${{m.hours_total}}h</div><div class="ms-l">Total est.</div></div>
    </div>
    <div class="mission-src-grid">
      ${{m.sources.map(s => `
        <div class="msrc">
          <div class="msrc-h">
            <span class="msrc-icon">${{s.icon}}</span>
            <span class="msrc-l">${{s.label}}</span>
            <span class="msrc-pct">${{s.pct}}%</span>
          </div>
          <div class="msrc-nums">${{s.done}} / ${{s.total}} EP · ${{s.remaining}} remaining</div>
          <div class="msrc-bar"><div class="msrc-fill ${{s.pct === 100 ? 'done' : ''}}" style="width:${{s.pct}}%"></div></div>
        </div>
      `).join('')}}
    </div>
  `;
}}

// ─── PHASE STRIP ─────────────────────────────────────────────
function renderPhases(){{
  const el = document.getElementById('phase-strip');
  el.innerHTML = D.phases.map(p =>
    `<div class="phase-pill ${{p.status}}" title="P${{p.phase}} ${{p.label}} · ${{p.note}}">
       <div class="fill" style="width:${{p.pct}}%"></div>
     </div>`).join('');
}}

// ─── LIVE RUNNING ────────────────────────────────────────────
function renderLive(){{
  const el = document.getElementById('live-running');
  const items = [];
  D.running.forEach(r => {{
    items.push(`<div class="running-row">
      <span class="running-icon">${{r.icon}}</span>
      <div style="flex:1"><div class="running-text">${{r.label}}</div>
      <div class="running-sub">background process · transcribe.py</div></div>
    </div>`);
  }});
  // accurate batch as live item if not 100%
  const acc = D.pipeline.accurate;
  if (acc.done < acc.total && D.running.length === 0) {{
    items.push(`<div class="running-row" style="border-left-color:var(--amber)">
      <span class="running-icon">🎤</span>
      <div style="flex:1"><div class="running-text">Accurate batch · ${{acc.done}}/${{acc.total}} EP</div>
      <div class="running-sub">~${{Math.round((acc.total-acc.done)/2)}}h remaining · ETA ${{Math.ceil((acc.total-acc.done)*1.5)}}h</div></div>
    </div>`);
  }}
  if (D.sessions.filter(s => s.alive).length) {{
    items.push(`<div class="running-row" style="border-left-color:var(--amber-2)">
      <span class="running-icon">⚡</span>
      <div style="flex:1"><div class="running-text">${{D.sessions.filter(s=>s.alive).length}} Claude session(s) live</div>
      <div class="running-sub">see Claude panel below</div></div>
    </div>`);
  }}
  el.innerHTML = items.join('') || '<div style="color:var(--muted);font-size:12px;text-align:center;padding:20px">No background work</div>';
}}

// ─── PROJECTS ───────────────────────────────────────────────
function renderProjects(){{
  const el = document.getElementById('proj-grid');
  el.innerHTML = D.projects.map(p => {{
    const tierCls = p.tier.toLowerCase().replace('done','done').replace('blocked','blocked').replace('backlog','backlog');
    const pCls = p.progress === 100 ? 'done' : (p.status === 'running' ? 'active' : '');
    return `<div class="proj s-${{p.status}}" onclick="openProj('${{p.id}}')">
      <div class="proj-h">
        <div class="proj-icon">${{p.icon}}</div>
        <div style="flex:1;min-width:0">
          <div class="proj-title">${{p.title}}</div>
          <div class="proj-sub">${{p.subtitle}}</div>
        </div>
        <div class="card-tier ${{tierCls}}">${{p.tier}}</div>
      </div>
      <div class="proj-progress-row">
        <div class="pbar" style="flex:1"><div class="pbar-fill ${{pCls}}" style="width:${{p.progress}}%"></div></div>
        <div class="proj-pct">${{p.progress}}%</div>
      </div>
      <div class="proj-next">→ ${{p.next}}</div>
    </div>`;
  }}).join('');
}}

function openProj(id){{
  const p = D.projects.find(x => x.id === id);
  if (!p) return;
  document.getElementById('modal-content').innerHTML = `
    <button class="modal-close" onclick="closeModal()">×</button>
    <div style="font-size:28px;margin-bottom:6px">${{p.icon}}</div>
    <div style="font-size:20px;font-weight:800;margin-bottom:2px">${{p.title}}</div>
    <div style="font-size:12px;color:var(--t2);margin-bottom:16px">${{p.subtitle}}</div>
    <div class="pbar" style="margin-bottom:6px"><div class="pbar-fill ${{p.progress===100?'done':''}}" style="width:${{p.progress}}%"></div></div>
    <div style="font-size:11px;color:var(--t2);margin-bottom:18px">Progress · ${{p.progress}}%</div>
    <div style="font-size:11px;font-weight:800;color:var(--amber);letter-spacing:.1em;text-transform:uppercase;margin-bottom:8px">Details</div>
    <ul style="list-style:none;padding:0;margin:0 0 16px">${{p.details.map(d => `<li style="padding:4px 0;font-size:13px;color:var(--t2)">• ${{d}}</li>`).join('')}}</ul>
    <div style="background:var(--surface);padding:12px;border-radius:10px;border-left:3px solid var(--amber)">
      <div style="font-size:10px;font-weight:800;color:var(--amber);letter-spacing:.08em;text-transform:uppercase;margin-bottom:4px">Next step</div>
      <div style="font-size:13px;font-weight:600">${{p.next}}</div>
    </div>
  `;
  document.getElementById('modal-bg').classList.add('open');
}}
function closeModal(){{ document.getElementById('modal-bg').classList.remove('open'); }}

// ─── PIPELINE ────────────────────────────────────────────────
function renderPipeline(){{
  const el = document.getElementById('pipe-grid');
  const entries = Object.entries(D.pipeline).map(([k, v]) => {{
    const pct = Math.round(v.done / v.total * 100) || 0;
    return [k, v, pct];
  }});
  const active = entries.filter(([,,pct]) => pct < 100);
  const done = entries.filter(([,,pct]) => pct === 100);

  const renderCard = ([k, v, pct]) => {{
    const cls = pct === 100 ? 'done' : pct > 0 ? 'active' : 'zero';
    return `<div class="pipe ${{v.priority ? 'priority' : ''}}">
      <div class="pipe-h"><span class="pipe-icon">${{v.icon}}</span><span class="pipe-l">${{v.label}}</span></div>
      <div class="pipe-nums">
        <span class="pipe-done">${{v.done}}</span>
        <span class="pipe-sep">/</span>
        <span class="pipe-total">${{v.total}}</span>
        <span class="pipe-pct ${{cls}}">${{pct}}%</span>
      </div>
      <div class="pbar"><div class="pbar-fill ${{cls}}" style="width:${{pct}}%"></div></div>
    </div>`;
  }};

  let html = active.map(renderCard).join('');
  if (done.length) {{
    html += `<div class="pipe-done-group" style="grid-column:1/-1" onclick="this.classList.toggle('open')">
      <div class="pipe-done-head">
        <span>✅</span><span>Completed</span>
        <span class="pipe-done-count">${{done.length}}</span>
        <span class="pipe-done-chev">›</span>
      </div>
      <div class="pipe-done-body">
        ${{done.map(([k, v]) => `
          <div class="pipe-done-item">
            <span>${{v.icon}}</span>
            <span class="pipe-done-item-l">${{v.label}}</span>
            <span class="pipe-done-item-n">${{v.done}} / ${{v.total}}</span>
          </div>
        `).join('')}}
      </div>
    </div>`;
  }}
  el.innerHTML = html;
}}

// ─── CLAUDE ─────────────────────────────────────────────────
function renderClaude(){{
  const el = document.getElementById('cl-grid');
  if (!D.sessions.length) {{
    el.innerHTML = '<div style="color:var(--muted);font-size:12px;padding:20px;text-align:center;grid-column:1/-1">No active sessions</div>';
    return;
  }}
  const ik = n => n >= 1000 ? (n/1000).toFixed(1) + 'k' : String(n);
  el.innerHTML = D.sessions.map(s => {{
    const pct = s.tokens.pct;
    const bc = pct > 75 ? 'var(--red)' : pct > 50 ? 'var(--yellow)' : 'var(--green)';
    return `<div class="cl-card ${{s.warn ? 'warn' : ''}}">
      <div class="cl-head">
        <span style="font-size:14px">${{s.alive ? '⚡' : '○'}}</span>
        <div class="cl-name">${{s.name || s.cwd}}</div>
        <button class="cl-bell" data-pid="${{s.pid}}" data-name="${{(s.name || s.cwd).replace(/"/g,'&quot;')}}" data-pct="${{pct}}" onclick="notifyRetire(this)" title="แจ้งเตือนให้ขึ้น session ใหม่">🔔</button>
        <span class="cl-badge ${{s.alive ? 'live' : 'off'}}">${{s.alive ? 'LIVE' : 'OFF'}}</span>
      </div>
      <div class="cl-meta">PID ${{s.pid}} · ${{s.runtime_min}}m · #${{s.session_id}} · ${{s.cwd}}</div>
      <div style="display:flex;align-items:center;gap:6px;font-size:10px;color:var(--muted);margin-bottom:4px">
        <span>Context ${{pct}}%</span><span style="margin-left:auto">${{ik(s.tokens.latest_cache)}} / 200k</span>
      </div>
      <div class="pbar"><div class="pbar-fill" style="width:${{pct}}%;background:${{bc}}"></div></div>
      <div class="cl-tokens">
        <div class="cl-tok"><div class="cl-tok-n" style="color:var(--slate-light)">${{ik(s.tokens.in)}}</div><div class="cl-tok-l">Input</div></div>
        <div class="cl-tok"><div class="cl-tok-n" style="color:var(--amber-2)">${{ik(s.tokens.out)}}</div><div class="cl-tok-l">Output</div></div>
        <div class="cl-tok"><div class="cl-tok-n" style="color:var(--text)">${{s.tokens.msgs}}</div><div class="cl-tok-l">Msgs</div></div>
      </div>
    </div>`;
  }}).join('');
}}

// ─── TODOS ──────────────────────────────────────────────────
const TODO_KEY = 'norms-mc-todo-done';
function getTodoState(){{ return JSON.parse(localStorage.getItem(TODO_KEY) || '{{}}'); }}
function setTodoState(id, v){{
  const s = getTodoState(); s[id] = v;
  localStorage.setItem(TODO_KEY, JSON.stringify(s));
}}
function renderTodos(){{
  const el = document.getElementById('todo-list');
  const done = getTodoState();
  el.innerHTML = ['urgent','soon','backlog'].map(group => {{
    const items = D.todos[group] || [];
    const groupItems = items.map((t,i) => {{
      const id = `${{group}}-${{i}}`;
      const ck = !!done[id];
      return `<div class="todo-item ${{ck ? 'done' : ''}}">
        <div class="todo-chk ${{ck ? 'on' : ''}}" onclick="toggleTodo('${{id}}', this)">${{ck ? '✓' : ''}}</div>
        <span class="todo-emoji">${{t.emoji}}</span>
        <div class="todo-body">
          <div class="todo-text">${{t.text}}</div>
          <div class="todo-meta">
            <span class="todo-due">📅 ${{t.due}}</span>
            <span class="todo-tag-i">#${{t.tag}}</span>
          </div>
        </div>
      </div>`;
    }}).join('');
    return `<div class="todo-section">
      <div class="todo-h">
        <span class="todo-tag-l ${{group}}">${{group}}</span>
        <span class="todo-count">${{items.length}}</span>
      </div>
      ${{groupItems}}
    </div>`;
  }}).join('');
}}
function toggleTodo(id, el){{
  const v = !getTodoState()[id];
  setTodoState(id, v);
  el.classList.toggle('on', v);
  el.textContent = v ? '✓' : '';
  el.closest('.todo-item').classList.toggle('done', v);
}}

// ─── GIT REPOS ──────────────────────────────────────────────
function renderGit(){{
  const el = document.getElementById('git-grid');
  el.innerHTML = D.git_repos.map(r => {{
    const cls = r.status === 'clean' ? 'clean' : r.status === 'warn' ? 'warn' : 'dirty';
    const badge = r.pending > 0 ? `${{r.pending}} pending` : 'clean';
    return `<div class="mini-card">
      <span class="mini-icon">📦</span>
      <div class="mini-body">
        <div class="mini-l">${{r.name}}</div>
        <div class="mini-s">${{r.msg}} · ${{r.last}}</div>
      </div>
      <span class="mini-badge ${{cls}}">${{badge}}</span>
    </div>`;
  }}).join('');
}}

// ─── VAULT / MEMORY ─────────────────────────────────────────
function renderVault(){{
  const el = document.getElementById('vault-grid');
  const tiles = [];
  tiles.push(`<div class="stat-tile"><div class="stat-tile-n" style="color:var(--amber-2)">${{D.memory.total}}</div><div class="stat-tile-l">Memory items</div></div>`);
  const mbt = D.memory.by_type;
  if (mbt.feedback) tiles.push(`<div class="stat-tile"><div class="stat-tile-n" style="color:var(--amber-soft)">${{mbt.feedback}}</div><div class="stat-tile-l">Feedback</div></div>`);
  if (mbt.project) tiles.push(`<div class="stat-tile"><div class="stat-tile-n" style="color:var(--slate-light)">${{mbt.project}}</div><div class="stat-tile-l">Project mem</div></div>`);
  if (mbt.user) tiles.push(`<div class="stat-tile"><div class="stat-tile-n" style="color:var(--green)">${{mbt.user}}</div><div class="stat-tile-l">User mem</div></div>`);
  tiles.push(`<div class="stat-tile"><div class="stat-tile-n" style="color:var(--text)">${{D.chapters.total}}</div><div class="stat-tile-l">NPC chapters</div></div>`);
  tiles.push(`<div class="stat-tile"><div class="stat-tile-n" style="color:var(--green)">${{D.chapters.new}}</div><div class="stat-tile-l">New (Phase 3)</div></div>`);
  tiles.push(`<div class="stat-tile"><div class="stat-tile-n" style="color:var(--amber-2)">${{D.chapters.edited_today}}</div><div class="stat-tile-l">Edited today</div></div>`);
  // top vault folders
  const top = D.vault.filter(v => v.count > 50).slice(0, 4);
  top.forEach(v => {{
    tiles.push(`<div class="stat-tile"><div class="stat-tile-n">${{v.count}}</div><div class="stat-tile-l">${{v.name}}</div></div>`);
  }});
  el.innerHTML = tiles.join('');
}}

// ─── MARKDOWN → HTML (lightweight) ──────────────────────────
function md2html(md){{
  // Escape HTML
  let h = md.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  // Code blocks (fenced)
  h = h.replace(/```([a-z]*)\\n([\\s\\S]*?)```/g, (m,lang,code) => `<pre><code>${{code}}</code></pre>`);
  // Tables (basic GFM)
  h = h.replace(/((?:^\\|[^\\n]+\\|\\n)+)/gm, table => {{
    const rows = table.trim().split('\\n');
    if(rows.length < 2) return table;
    const head = rows[0].split('|').slice(1,-1).map(c => `<th>${{c.trim()}}</th>`).join('');
    const body = rows.slice(2).map(r => '<tr>' + r.split('|').slice(1,-1).map(c => `<td>${{c.trim()}}</td>`).join('') + '</tr>').join('');
    return `<table><thead><tr>${{head}}</tr></thead><tbody>${{body}}</tbody></table>`;
  }});
  // Headings
  h = h.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  h = h.replace(/^## (.+)$/gm, '<h2>$1</h2>');
  h = h.replace(/^# (.+)$/gm, '<h1>$1</h1>');
  // Blockquote
  h = h.replace(/^&gt; (.+)$/gm, '<blockquote>$1</blockquote>');
  // Horizontal rule
  h = h.replace(/^---$/gm, '<hr>');
  // Bold + italic
  h = h.replace(/\\*\\*([^*]+)\\*\\*/g, '<strong>$1</strong>');
  // Inline code
  h = h.replace(/`([^`]+)`/g, '<code>$1</code>');
  // Wiki-links [[foo]] · render as styled span (not <a> without href)
  h = h.replace(/\\[\\[([^\\]]+)\\]\\]/g, '<span class="wlink">$1</span>');
  // Links [text](url)
  h = h.replace(/\\[([^\\]]+)\\]\\(([^)]+)\\)/g, '<a href="$2">$1</a>');
  // Lists
  h = h.replace(/^(?:- |\\* )(.+)$/gm, '<li>$1</li>');
  h = h.replace(/(<li>[\\s\\S]*?<\\/li>(?:\\n<li>[\\s\\S]*?<\\/li>)*)/g, '<ul>$1</ul>');
  // Paragraphs (double newline)
  h = h.split(/\\n\\n+/).map(p => {{
    p = p.trim();
    if (!p) return '';
    if (p.startsWith('<')) return p;
    return '<p>' + p.replace(/\\n/g, '<br>') + '</p>';
  }}).join('\\n');
  return h;
}}

// ─── READ PANEL ─────────────────────────────────────────────
let readSearchQuery = '';
let readActiveCat = 'working';

function renderReadTabs(){{
  const el = document.getElementById('read-tabs');
  // Add "All" tab + each category
  const allCount = D.must_read.length;
  const tabs = [{{ id: 'all', icon: '📂', label: 'ทั้งหมด' }}].concat(D.categories);
  el.innerHTML = tabs.map(c => {{
    const count = c.id === 'all' ? allCount : D.must_read.filter(f => f.cat === c.id).length;
    const cls = c.id === readActiveCat ? 'on' : '';
    return `<button class="read-tab ${{cls}}" data-cat="${{c.id}}">
      <span class="read-tab-ic">${{c.icon}}</span>
      <span>${{c.label}}</span>
      <span class="read-tab-count">${{count}}</span>
    </button>`;
  }}).join('');
  el.querySelectorAll('.read-tab').forEach(btn => {{
    btn.addEventListener('click', () => {{
      readActiveCat = btn.dataset.cat;
      renderReadTabs();
      renderRead();
    }});
  }});
}}

// Pre-lowercase title+content once (search runs on every keystroke)
D.must_read.forEach(f => {{ f._title_lc = f.title.toLowerCase(); f._content_lc = f.content.toLowerCase(); }});

function renderRead(){{
  const list = document.getElementById('read-list');
  const q = readSearchQuery.toLowerCase().trim();
  const filtered = D.must_read.filter(f => {{
    if (readActiveCat !== 'all' && f.cat !== readActiveCat) return false;
    if (q && !f._title_lc.includes(q) && !f._content_lc.includes(q)) return false;
    return true;
  }});
  list.innerHTML = filtered.map(f => {{
    const sizeKb = (f.size / 1024).toFixed(1);
    return `<div class="read-card" id="rc-${{f.id}}">
      <div class="read-head" onclick="toggleRead('${{f.id}}')">
        <span class="read-icon">${{f.icon}}</span>
        <div class="read-body">
          <div class="read-title">${{f.title}}</div>
          <div class="read-meta">${{f.lines}} lines · ${{sizeKb}}KB · updated ${{f.mtime_ago}}</div>
        </div>
        <span class="read-tier ${{f.tier.toLowerCase()}}">${{f.tier}}</span>
        <span class="read-chevron">›</span>
      </div>
      <div class="read-content" id="rcc-${{f.id}}"></div>
    </div>`;
  }}).join('') || '<div style="text-align:center;color:var(--muted);padding:30px;font-size:13px">ไม่พบไฟล์ที่ตรงกับ "' + q + '"</div>';
}}
function toggleRead(id){{
  const card = document.getElementById('rc-' + id);
  const content = document.getElementById('rcc-' + id);
  const isOpen = card.classList.contains('open');
  if (isOpen) {{
    card.classList.remove('open');
  }} else {{
    if (!content.dataset.rendered) {{
      const file = D.must_read.find(f => f.id === id);
      content.innerHTML = md2html(file.content);
      content.dataset.rendered = '1';
    }}
    card.classList.add('open');
  }}
}}

// ─── SHORTCUTS (Home panel) ─────────────────────────────────
function renderShortcuts(){{
  const el = document.getElementById('shortcut-grid');
  // Top 8 most important
  const priority = ['status','phase2','phase1-km','worklog-book','handoff-sync','npc-website','ch-3pillar','ch-psy1'];
  const items = priority.map(id => D.must_read.find(f => f.id === id)).filter(Boolean);
  el.innerHTML = items.map(f => `
    <div class="shortcut" onclick="jumpToFile('${{f.id}}','${{f.cat}}')">
      <div class="shortcut-icon">${{f.icon}}</div>
      <div class="shortcut-l">${{f.title}}</div>
      <div class="shortcut-s">${{f.mtime_ago}}</div>
    </div>
  `).join('');
}}

function jumpToFile(id, cat){{
  switchPanel('p-read');
  readActiveCat = cat || 'all';
  renderReadTabs();
  renderRead();
  setTimeout(() => toggleRead(id), 120);
}}

// ─── TAB SWITCHING ──────────────────────────────────────────
function switchPanel(targetId){{
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.nb').forEach(b => b.classList.remove('on'));
  document.getElementById(targetId).classList.add('active');
  document.querySelector(`.nb[data-panel="${{targetId}}"]`).classList.add('on');
  window.scrollTo({{ top: 0, behavior: 'smooth' }});
}}
document.querySelectorAll('.nb').forEach(btn => {{
  btn.addEventListener('click', () => switchPanel(btn.dataset.panel));
}});

// ─── AUTO-REFRESH check (debounced · single in-flight) ───────
let updateInFlight = false, lastReturnCheck = 0;
function checkUpdate(autoReload){{
  if (updateInFlight) return;
  updateInFlight = true;
  fetch(location.href + '?_=' + Date.now(), {{cache: 'no-store'}})
    .then(r => r.text()).then(html => {{
      const m = html.match(/content="(\\d{{4}}-\\d{{2}}-\\d{{2}}T[^"]+)"/);
      if (m && m[1] !== BUILD_TIME) {{
        if (autoReload) location.reload();
        else document.getElementById('upd-banner').classList.add('show');
      }}
    }}).catch(() => {{}}).finally(() => {{ updateInFlight = false; }});
}}
setInterval(() => checkUpdate(false), 60000);
// On tab return: auto-reload if stale · throttle 5s between checks (prevent alt-tab spam)
function onReturn(){{
  const now = Date.now();
  if (now - lastReturnCheck < 5000) return;
  lastReturnCheck = now;
  checkUpdate(true);
}}
document.addEventListener('visibilitychange', () => {{ if (!document.hidden) onReturn(); }});
window.addEventListener('focus', onReturn);

// ─── INIT ───────────────────────────────────────────────────
renderPhases();
renderMission();
renderLive();
renderShortcuts();
renderReadTabs();
renderRead();
// Search bar listener (debounced 150ms · 24+ files × content.toLowerCase is expensive on every keystroke)
let searchDebounce;
const searchInput = document.getElementById('read-search-input');
if (searchInput) searchInput.addEventListener('input', e => {{
  clearTimeout(searchDebounce);
  const v = e.target.value;
  searchDebounce = setTimeout(() => {{ readSearchQuery = v; renderRead(); }}, 150);
}});
renderProjects();
renderPipeline();
renderClaude();
renderTodos();
renderGit();
renderVault();
</script>
</body>
</html>"""


if __name__ == "__main__":
    print("Building Norms Mission Control...")
    html = build()
    OUT.write_text(html, encoding="utf-8")
    print(f"✓ index.html · {len(html):,} bytes · {(NPC_DEADLINE - TODAY).days} days to NPC launch")
