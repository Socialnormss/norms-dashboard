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
    hours_done = round(total_done * AVG_HOURS_PER_EP, 1)
    hours_remaining = round(total_remaining * AVG_HOURS_PER_EP, 1)
    hours_total = round(total_target * AVG_HOURS_PER_EP, 1)
    overall_pct = round(total_done / total_target * 100) if total_target else 0

    # ETA assuming 8h/day compute (overnight + bg)
    HOURS_PER_DAY = 8
    days_remaining = round(hours_remaining / HOURS_PER_DAY)
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

def collect_git_repos():
    """Multi-repo status"""
    repos = [
        ("dashboard",          NC/"IT/dashboard"),
        ("norms-website",      NC/"IT/social-norms-website"),
        ("dog-feeder",         HOME/"dog-feeder"),
        ("bell-app",           NC/"Bell/app"),
        ("bell-hero",          NC/"Bell/Hero"),
    ]
    out = []
    for name, path in repos:
        if not (path/".git").exists(): continue
        try:
            pending = int(subprocess.run(["git","-C",str(path),"status","-s"],
                          capture_output=True, text=True, timeout=2).stdout.strip().count("\n") + (1 if subprocess.run(["git","-C",str(path),"status","-s"], capture_output=True, text=True, timeout=2).stdout.strip() else 0))
            last = subprocess.run(["git","-C",str(path),"log","-1","--format=%ct"],
                          capture_output=True, text=True, timeout=2).stdout.strip()
            last_msg = subprocess.run(["git","-C",str(path),"log","-1","--format=%s"],
                          capture_output=True, text=True, timeout=2).stdout.strip()[:60]
            out.append({
                "name": name,
                "pending": pending,
                "last": get_relative_time(int(last)) if last else "—",
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
        "original": len(all_files) - len(new_files),
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
    {"id":"dog-feeder","icon":"🐕","title":"Dog Feeder v3","tier":"P2","status":"phase1","progress":60,
     "subtitle":"Soft Cozy redesign","tag":"app",
     "details":["v2.1 live · skip-meal","Round 2 mockup ผ่าน","4 Magnific sheets dictated","Awaiting CSS+HTML from Pro"],
     "next":"Pro assets → Max integrate"},
    {"id":"hero-bell","icon":"🦸","title":"Hero (Bell)","tier":"P2","status":"phase1","progress":85,
     "subtitle":"Claude Project · BD Manager AI","tag":"client",
     "details":["Deployed @ liewsk129","7 knowledge files","Test 9/10 passed","V2 vision: brief→deliverable"],
     "next":"V2 design 2026-05-20"},
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
        {"text":"Pro Hero visual implementation","due":"this week","tag":"website","emoji":"🎨"},
        {"text":"Dog Feeder v3 CSS+HTML integrate","due":"this week","tag":"app","emoji":"🐕"},
    ],
    "soon":[
        {"text":"Phase 3 production: rename + 5 new chapters","due":"after sign-off","tag":"book","emoji":"📚"},
        {"text":"File rename: B1_C11 NES_Synthesis · B1_C13 Liquidity_Complex","due":"after sign-off","tag":"book","emoji":"📝"},
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
    ts_thai = NOW.strftime("อัพเดท %d %b %y · %H:%M")
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
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
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
  --bg:#050505;--base:#0A0A0B;--surface:#121214;--raised:#18181C;--overlay:#222227;
  --amber:#D47A2A;--amber-2:#E0944A;--amber-glow:rgba(212,122,42,.45);
  --cyan:#00D4FF;--cyan-glow:rgba(0,212,255,.4);
  --magenta:#FF2E97;--magenta-glow:rgba(255,46,151,.4);
  --green:#00F593;--green-glow:rgba(0,245,147,.4);
  --red:#FF3B5C;--red-glow:rgba(255,59,92,.45);
  --yellow:#FFC53D;--purple:#A855F7;
  --text:#F5F2EE;--t2:#9F9B95;--muted:#5E5A55;
  --border:rgba(255,255,255,.06);
  --border-glow:rgba(255,255,255,.1);
  --r:16px;--r-sm:10px;
  --sb:env(safe-area-inset-bottom);
}}
*{{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent}}
@keyframes pulse-glow{{0%,100%{{opacity:.5;transform:scale(.9)}}50%{{opacity:1;transform:scale(1.1)}}}}
@keyframes pulse-dot{{0%,100%{{opacity:1}}50%{{opacity:.3}}}}
@keyframes gradient-shift{{0%,100%{{background-position:0% 50%}}50%{{background-position:100% 50%}}}}
@keyframes shimmer{{0%{{background-position:-200% 0}}100%{{background-position:200% 0}}}}
@keyframes ring-rotate{{from{{transform:rotate(0deg)}}to{{transform:rotate(360deg)}}}}
@keyframes blink-warn{{0%,50%{{box-shadow:0 0 0 0 var(--red-glow)}}51%,100%{{box-shadow:0 0 0 8px rgba(255,59,92,0)}}}}

html,body{{height:100%;background:var(--bg);color:var(--text);
  font-family:-apple-system,"SF Pro Display","Helvetica Neue",Sarabun,sans-serif;
  font-size:14px;line-height:1.4;overflow-x:hidden}}
body{{background:radial-gradient(ellipse at top,rgba(212,122,42,.05),transparent 50%),
                radial-gradient(ellipse at bottom right,rgba(0,212,255,.04),transparent 60%),
                var(--bg);min-height:100vh}}

/* ── TOPBAR ────────────────────────────────────────────────────── */
.topbar{{position:sticky;top:0;z-index:50;
  background:rgba(10,10,11,.85);backdrop-filter:blur(20px) saturate(180%);
  -webkit-backdrop-filter:blur(20px) saturate(180%);
  border-bottom:1px solid var(--border);padding:12px 16px}}
.topbar-row{{display:flex;align-items:center;gap:14px;max-width:1400px;margin:0 auto}}
.logo{{font-weight:900;font-size:14px;letter-spacing:.05em;
  background:linear-gradient(90deg,var(--amber),var(--amber-2),var(--cyan));
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
  background-size:200% auto;animation:gradient-shift 6s ease infinite}}
.logo-pulse{{display:inline-block;width:7px;height:7px;border-radius:50%;
  background:var(--green);box-shadow:0 0 12px var(--green-glow);
  animation:pulse-glow 2s infinite;margin-right:6px;vertical-align:middle}}
.update-ts{{font-size:10px;color:var(--t2);font-weight:500;letter-spacing:.02em}}
.h-stats{{margin-left:auto;display:flex;gap:18px;align-items:center}}
.h-stat{{display:flex;flex-direction:column;align-items:flex-end;line-height:1}}
.h-stat-n{{font-size:18px;font-weight:800;font-feature-settings:"tnum"}}
.h-stat-l{{font-size:9px;color:var(--muted);font-weight:700;letter-spacing:.08em;
  text-transform:uppercase;margin-top:3px}}

/* ── LAYOUT ────────────────────────────────────────────────────── */
.app{{max-width:1400px;margin:0 auto;padding:16px;padding-bottom:calc(120px + var(--sb))}}
.grid{{display:grid;gap:14px}}
.grid-2{{grid-template-columns:repeat(2,1fr)}}
.grid-3{{grid-template-columns:repeat(3,1fr)}}
.grid-4{{grid-template-columns:repeat(4,1fr)}}
@media (max-width:760px){{.grid-3,.grid-4{{grid-template-columns:repeat(2,1fr)}}}}
@media (max-width:480px){{.grid-2,.grid-3,.grid-4{{grid-template-columns:1fr}}}}

/* ── RE-TRANSCRIBE MISSION ────────────────────────────────────── */
.mission-box{{position:relative;border-radius:var(--r);overflow:hidden;
  background:linear-gradient(135deg,#0a1a2a 0%,#1a0a2a 100%);
  border:1px solid rgba(0,212,255,.3);
  padding:20px 22px;margin-bottom:18px;
  box-shadow:0 0 50px rgba(0,212,255,.15),inset 0 1px 0 rgba(255,255,255,.04)}}
.mission-box::before{{content:"";position:absolute;inset:0;
  background:radial-gradient(circle at 0% 100%,rgba(168,85,247,.15),transparent 60%);
  pointer-events:none}}
.mission-box::after{{content:"";position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,var(--cyan),var(--magenta),transparent);
  animation:shimmer 5s linear infinite;background-size:200% 100%}}
.mission-head{{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:14px;flex-wrap:wrap;position:relative;z-index:1}}
.mission-title-wrap{{flex:1;min-width:200px}}
.mission-eyebrow{{font-size:10px;font-weight:800;letter-spacing:.15em;text-transform:uppercase;
  color:var(--cyan);margin-bottom:4px}}
.mission-title{{font-size:20px;font-weight:800;letter-spacing:-.01em}}
.mission-sub{{font-size:12px;color:var(--t2);margin-top:2px}}
.mission-eta{{text-align:right;flex-shrink:0}}
.mission-eta-n{{font-size:32px;font-weight:900;line-height:1;letter-spacing:-.02em;
  background:linear-gradient(135deg,var(--cyan),var(--magenta));
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
  font-feature-settings:"tnum"}}
.mission-eta-l{{font-size:10px;color:var(--t2);font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin-top:3px}}
.mission-eta-date{{font-size:11px;color:var(--cyan);font-weight:700;margin-top:4px;font-feature-settings:"tnum"}}

/* mega progress bar */
.mission-mega-bar{{height:14px;background:rgba(255,255,255,.04);border-radius:7px;overflow:hidden;
  position:relative;margin-bottom:12px;border:1px solid rgba(255,255,255,.06)}}
.mission-mega-fill{{height:100%;border-radius:7px;position:relative;overflow:hidden;
  background:linear-gradient(90deg,var(--cyan),var(--magenta));
  box-shadow:0 0 12px var(--cyan-glow);
  transition:width 1.2s cubic-bezier(.2,.8,.2,1)}}
.mission-mega-fill::after{{content:"";position:absolute;inset:0;
  background:linear-gradient(90deg,transparent,rgba(255,255,255,.3),transparent);
  background-size:200% 100%;animation:shimmer 2s linear infinite}}
.mission-mega-pct{{position:absolute;top:50%;transform:translateY(-50%);left:50%;translate:-50% -50%;
  font-size:10px;font-weight:800;color:#000;mix-blend-mode:overlay;font-feature-settings:"tnum"}}

/* mission stats grid */
.mission-stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;margin-bottom:14px}}
@media (max-width:640px){{.mission-stats{{grid-template-columns:repeat(2,1fr)}}}}
.ms{{padding:10px 12px;background:rgba(255,255,255,.03);border-radius:8px;
  border:1px solid rgba(255,255,255,.05)}}
.ms-n{{font-size:18px;font-weight:800;line-height:1;font-feature-settings:"tnum"}}
.ms-l{{font-size:9px;color:var(--t2);font-weight:600;text-transform:uppercase;letter-spacing:.05em;margin-top:4px}}

/* per-source breakdown */
.mission-src-grid{{display:grid;grid-template-columns:repeat(2,1fr);gap:8px}}
@media (max-width:520px){{.mission-src-grid{{grid-template-columns:1fr}}}}
.msrc{{background:rgba(255,255,255,.025);border:1px solid rgba(255,255,255,.05);
  border-radius:8px;padding:10px 12px}}
.msrc-h{{display:flex;align-items:center;gap:6px;margin-bottom:6px}}
.msrc-icon{{font-size:14px}}
.msrc-l{{font-size:11px;font-weight:700;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.msrc-pct{{font-size:10px;font-weight:800;color:var(--cyan);font-feature-settings:"tnum"}}
.msrc-nums{{font-size:10px;color:var(--muted);margin-bottom:6px;font-feature-settings:"tnum"}}
.msrc-bar{{height:5px;background:rgba(255,255,255,.05);border-radius:3px;overflow:hidden}}
.msrc-fill{{height:100%;background:linear-gradient(90deg,var(--cyan),var(--magenta));
  transition:width 1s cubic-bezier(.2,.8,.2,1);border-radius:3px}}
.msrc-fill.done{{background:linear-gradient(90deg,var(--green),#7CFFE0);box-shadow:0 0 6px var(--green-glow)}}

/* ── HERO COUNTDOWN ───────────────────────────────────────────── */
.hero-mission{{position:relative;border-radius:var(--r);overflow:hidden;
  background:linear-gradient(135deg,#1a0e00 0%,#0e0a1a 100%);
  border:1px solid {deadline_color};
  padding:24px 24px 24px 28px;margin-bottom:18px;
  box-shadow:0 0 60px {deadline_glow},inset 0 1px 0 rgba(255,255,255,.04)}}
.hero-mission::before{{content:"";position:absolute;inset:0;
  background:radial-gradient(circle at 80% 50%,{deadline_glow},transparent 50%);
  opacity:.4;pointer-events:none}}
.hero-mission::after{{content:"";position:absolute;top:0;left:0;right:0;height:1px;
  background:linear-gradient(90deg,transparent,{deadline_color},transparent);
  animation:shimmer 4s linear infinite;background-size:200% 100%}}
.hero-row{{display:flex;align-items:center;gap:24px;position:relative;z-index:1;flex-wrap:wrap}}
.hero-count{{font-size:88px;font-weight:900;line-height:.9;letter-spacing:-.04em;
  font-feature-settings:"tnum";
  background:linear-gradient(180deg,{deadline_color},{deadline_color}99);
  -webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;
  text-shadow:0 0 30px {deadline_glow}}}
.hero-text{{flex:1;min-width:200px}}
.hero-eyebrow{{font-size:10px;font-weight:800;letter-spacing:.15em;text-transform:uppercase;
  color:var(--amber);margin-bottom:6px}}
.hero-title{{font-size:22px;font-weight:800;letter-spacing:-.01em;margin-bottom:4px}}
.hero-sub{{font-size:13px;color:var(--t2);margin-bottom:10px}}
.hero-phase-strip{{display:flex;gap:4px;margin-top:8px}}
.phase-pill{{flex:1;height:6px;border-radius:3px;background:var(--surface);overflow:hidden;position:relative}}
.phase-pill .fill{{position:absolute;inset:0;border-radius:3px;
  transition:transform .8s cubic-bezier(.2,.8,.2,1)}}
.phase-pill.done .fill{{background:linear-gradient(90deg,var(--green),var(--cyan));
  box-shadow:0 0 10px var(--green-glow)}}
.phase-pill.active .fill{{background:linear-gradient(90deg,var(--amber),var(--amber-2));
  box-shadow:0 0 10px var(--amber-glow)}}
.phase-pill.pending{{opacity:.3}}

/* ── HERO KPI CARDS ───────────────────────────────────────────── */
.kpi-row{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:18px}}
@media (max-width:760px){{.kpi-row{{grid-template-columns:repeat(2,1fr)}}}}
.kpi{{position:relative;border:1px solid var(--border);border-radius:var(--r);
  padding:14px 14px 12px;overflow:hidden;background:var(--raised);
  transition:transform .15s,border-color .2s}}
.kpi:hover{{transform:translateY(-2px);border-color:var(--border-glow)}}
.kpi::before{{content:"";position:absolute;top:0;left:0;right:0;height:2px}}
.kpi.k-amber::before{{background:linear-gradient(90deg,var(--amber),var(--amber-2))}}
.kpi.k-cyan::before{{background:linear-gradient(90deg,var(--cyan),#7CECFF)}}
.kpi.k-magenta::before{{background:linear-gradient(90deg,var(--magenta),#FF7AC8)}}
.kpi.k-green::before{{background:linear-gradient(90deg,var(--green),#7CFFE0)}}
.kpi-l{{font-size:10px;font-weight:700;color:var(--t2);letter-spacing:.1em;
  text-transform:uppercase;margin-bottom:8px}}
.kpi-n{{font-size:36px;font-weight:900;line-height:1;letter-spacing:-.02em;
  font-feature-settings:"tnum";margin-bottom:4px}}
.kpi.k-amber .kpi-n{{color:var(--amber-2)}}
.kpi.k-cyan .kpi-n{{color:var(--cyan)}}
.kpi.k-magenta .kpi-n{{color:var(--magenta)}}
.kpi.k-green .kpi-n{{color:var(--green)}}
.kpi-sub{{font-size:11px;color:var(--muted);font-weight:500}}
.kpi-spark{{position:absolute;bottom:0;left:0;right:0;height:32px;opacity:.5}}

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
.card-tier.p1{{background:rgba(255,46,151,.15);color:var(--magenta)}}
.card-tier.p2{{background:rgba(212,122,42,.15);color:var(--amber-2)}}
.card-tier.p3{{background:rgba(0,212,255,.15);color:var(--cyan)}}
.card-tier.done{{background:rgba(0,245,147,.15);color:var(--green)}}
.card-tier.blocked{{background:rgba(255,59,92,.15);color:var(--red)}}
.card-tier.backlog{{background:rgba(168,85,247,.15);color:var(--purple)}}

/* progress ring */
.ring{{position:relative;width:48px;height:48px;flex-shrink:0}}
.ring svg{{width:100%;height:100%;transform:rotate(-90deg)}}
.ring-track{{stroke:var(--surface);stroke-width:4;fill:none}}
.ring-fill{{stroke-width:4;fill:none;stroke-linecap:round;transition:stroke-dashoffset 1s}}
.ring-n{{position:absolute;inset:0;display:flex;align-items:center;justify-content:center;
  font-size:11px;font-weight:800;font-feature-settings:"tnum"}}

/* progress bar */
.pbar{{height:6px;background:var(--surface);border-radius:3px;overflow:hidden;position:relative}}
.pbar-fill{{height:100%;border-radius:3px;transition:width 1s cubic-bezier(.2,.8,.2,1);
  background:linear-gradient(90deg,var(--amber),var(--amber-2))}}
.pbar-fill.done{{background:linear-gradient(90deg,var(--green),#7CFFE0);box-shadow:0 0 8px var(--green-glow)}}
.pbar-fill.warn{{background:linear-gradient(90deg,var(--red),#FF7C92)}}
.pbar-fill.active{{background:linear-gradient(90deg,var(--cyan),#7CECFF);box-shadow:0 0 8px var(--cyan-glow)}}

/* ── PROJECT GRID ─────────────────────────────────────────────── */
.proj-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}}
.proj{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r);
  padding:16px;position:relative;overflow:hidden;cursor:pointer;transition:all .2s}}
.proj:hover{{border-color:var(--border-glow);transform:translateY(-2px);
  box-shadow:0 8px 24px rgba(0,0,0,.4)}}
.proj::before{{content:"";position:absolute;top:0;left:0;bottom:0;width:3px;
  background:var(--surface);transition:background .3s}}
.proj.s-done::before{{background:linear-gradient(180deg,var(--green),#7CFFE0);
  box-shadow:0 0 8px var(--green-glow)}}
.proj.s-phase1::before{{background:linear-gradient(180deg,var(--amber),var(--amber-2));
  box-shadow:0 0 8px var(--amber-glow)}}
.proj.s-running::before{{background:linear-gradient(180deg,var(--cyan),#7CECFF);
  box-shadow:0 0 8px var(--cyan-glow);animation:pulse-dot 2s infinite}}
.proj.s-blocked::before{{background:linear-gradient(180deg,var(--red),#FF7C92)}}
.proj.s-research::before{{background:linear-gradient(180deg,var(--purple),#C8A8FF)}}
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
.pipe-pct.active{{background:rgba(0,212,255,.12);color:var(--cyan)}}
.pipe-pct.zero{{background:var(--surface);color:var(--muted)}}

/* ── RUNNING / LIVE ───────────────────────────────────────────── */
.running-row{{display:flex;align-items:center;gap:10px;padding:10px 12px;
  background:var(--surface);border-radius:var(--r-sm);margin-bottom:6px;
  border-left:3px solid var(--green);position:relative}}
.running-row::before{{content:"";position:absolute;left:-2px;top:50%;width:6px;height:6px;
  border-radius:50%;background:var(--green);transform:translateY(-50%);
  box-shadow:0 0 8px var(--green-glow);animation:pulse-dot 1.5s infinite}}
.running-icon{{font-size:14px}}
.running-text{{flex:1;font-size:12px;font-weight:600}}
.running-sub{{font-size:10px;color:var(--muted)}}

/* ── CLAUDE SESSIONS ──────────────────────────────────────────── */
.cl-card{{background:var(--raised);border:1px solid var(--border);border-radius:var(--r-sm);
  padding:12px;position:relative}}
.cl-card.warn{{border-color:rgba(255,59,92,.3);background:linear-gradient(135deg,rgba(255,59,92,.05),var(--raised) 50%)}}
.cl-head{{display:flex;align-items:center;gap:8px;margin-bottom:8px}}
.cl-name{{font-size:12px;font-weight:700;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.cl-badge{{font-size:9px;font-weight:800;padding:2px 6px;border-radius:4px;letter-spacing:.05em}}
.cl-badge.live{{background:rgba(0,245,147,.15);color:var(--green)}}
.cl-badge.off{{background:rgba(94,90,85,.2);color:var(--muted)}}
.cl-meta{{font-size:9px;color:var(--muted);margin-bottom:8px}}
.cl-tokens{{display:grid;grid-template-columns:repeat(3,1fr);gap:6px;margin-top:6px}}
.cl-tok{{text-align:center;padding:6px 4px;background:var(--surface);border-radius:6px}}
.cl-tok-n{{font-size:13px;font-weight:800;font-feature-settings:"tnum"}}
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
  padding:10px 12px;display:flex;align-items:center;gap:10px}}
.mini-icon{{font-size:14px;flex-shrink:0}}
.mini-body{{flex:1;min-width:0}}
.mini-l{{font-size:11px;font-weight:700;line-height:1.3}}
.mini-s{{font-size:10px;color:var(--muted);margin-top:1px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.mini-badge{{font-size:9px;font-weight:800;padding:3px 6px;border-radius:4px;letter-spacing:.04em;flex-shrink:0}}
.mini-badge.clean{{background:rgba(0,245,147,.12);color:var(--green)}}
.mini-badge.dirty{{background:rgba(212,122,42,.12);color:var(--amber-2)}}
.mini-badge.warn{{background:rgba(255,59,92,.12);color:var(--red)}}

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

/* ── FOOTER (Mission control bar) ─────────────────────────────── */
.footer-bar{{position:fixed;bottom:calc(var(--sb) + 12px);left:50%;transform:translateX(-50%);
  background:rgba(18,18,20,.95);border:1px solid var(--border-glow);
  border-radius:50px;padding:6px 8px;display:flex;gap:2px;
  backdrop-filter:blur(20px);box-shadow:0 12px 36px rgba(0,0,0,.7);z-index:100}}
.fb-btn{{display:flex;flex-direction:column;align-items:center;gap:2px;padding:8px 14px;
  border:none;background:none;color:var(--muted);font-size:9px;font-weight:700;
  cursor:pointer;border-radius:40px;letter-spacing:.04em;transition:all .2s}}
.fb-btn .ic{{font-size:18px;line-height:1}}
.fb-btn.on{{background:linear-gradient(135deg,rgba(212,122,42,.2),rgba(255,46,151,.1));color:#fff}}

/* update banner */
.upd{{position:fixed;top:60px;left:50%;transform:translateX(-50%);
  background:linear-gradient(135deg,var(--cyan),var(--magenta));color:#000;
  padding:8px 16px;border-radius:50px;font-size:12px;font-weight:800;
  display:none;z-index:90;cursor:pointer;box-shadow:0 4px 20px var(--cyan-glow)}}
.upd.show{{display:block}}
</style>
</head>
<body>

<div class="topbar">
  <div class="topbar-row">
    <div class="logo"><span class="logo-pulse"></span>NORMS · MISSION CONTROL</div>
    <span class="update-ts">{ts_thai}</span>
    <div class="h-stats">
      <div class="h-stat"><span class="h-stat-n" style="color:var(--green)">{alive_count}</span><span class="h-stat-l">Live</span></div>
      <div class="h-stat"><span class="h-stat-n" style="color:var(--amber-2)">{accurate_done}/25</span><span class="h-stat-l">Acc.</span></div>
      <div class="h-stat"><span class="h-stat-n" style="color:var(--cyan)">{chapters_new}</span><span class="h-stat-l">New Ch.</span></div>
      <div class="h-stat"><span class="h-stat-n" style="color:{drive_color}">{drive_ok}</span><span class="h-stat-l">Drive</span></div>
    </div>
  </div>
</div>

<div class="upd" id="upd-banner" onclick="location.reload()">↻ New build · refresh</div>

<div class="app">

  <!-- ── HERO MISSION ──────────────────────────────────────── -->
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

  <!-- ── KPI ROW ────────────────────────────────────────────── -->
  <div class="kpi-row">
    <div class="kpi k-amber">
      <div class="kpi-l">Accurate Batch</div>
      <div class="kpi-n">{accurate_pct}%</div>
      <div class="kpi-sub">{accurate_done}/25 EP · background</div>
    </div>
    <div class="kpi k-cyan">
      <div class="kpi-l">Chapters · New</div>
      <div class="kpi-n">{chapters_new}/{chapters_total}</div>
      <div class="kpi-sub">drafted Phase 3</div>
    </div>
    <div class="kpi k-magenta">
      <div class="kpi-l">Memory</div>
      <div class="kpi-n">{memory_total}</div>
      <div class="kpi-sub">items active</div>
    </div>
    <div class="kpi k-green">
      <div class="kpi-l">Disk</div>
      <div class="kpi-n">{disk_pct}%</div>
      <div class="kpi-sub">{disk_used} used</div>
    </div>
  </div>

  <!-- ── RE-TRANSCRIBE MISSION ──────────────────────────────── -->
  <div class="section-h"><span class="section-h-icon">🎤</span><span class="section-h-l">Re-transcribe mission · accurate model</span><div class="section-h-line"></div></div>
  <div class="mission-box" id="mission-box"></div>

  <!-- ── LIVE NOW ───────────────────────────────────────────── -->
  <div class="section-h"><span class="section-h-icon">⚡</span><span class="section-h-l">Live now</span><div class="section-h-line"></div></div>
  <div id="live-running"></div>

  <!-- ── PROJECTS ───────────────────────────────────────────── -->
  <div class="section-h"><span class="section-h-icon">🚀</span><span class="section-h-l">Projects · priority order</span><div class="section-h-line"></div></div>
  <div class="proj-grid" id="proj-grid"></div>

  <!-- ── PIPELINE TRACKER ───────────────────────────────────── -->
  <div class="section-h"><span class="section-h-icon">🎙️</span><span class="section-h-l">Transcription pipeline</span><div class="section-h-line"></div></div>
  <div class="pipe-grid" id="pipe-grid"></div>

  <!-- ── CLAUDE SESSIONS ────────────────────────────────────── -->
  <div class="section-h"><span class="section-h-icon">⚙️</span><span class="section-h-l">Claude sessions</span><div class="section-h-line"></div></div>
  <div class="grid grid-2" id="cl-grid"></div>

  <!-- ── TODOS ──────────────────────────────────────────────── -->
  <div class="section-h"><span class="section-h-icon">📋</span><span class="section-h-l">Action items</span><div class="section-h-line"></div></div>
  <div id="todo-list"></div>

  <!-- ── GIT REPOS ──────────────────────────────────────────── -->
  <div class="section-h"><span class="section-h-icon">📦</span><span class="section-h-l">Git repos · {git_dirty} dirty</span><div class="section-h-line"></div></div>
  <div class="grid grid-2" id="git-grid"></div>

  <!-- ── VAULT + MEMORY ─────────────────────────────────────── -->
  <div class="section-h"><span class="section-h-icon">🗂️</span><span class="section-h-l">Knowledge base</span><div class="section-h-line"></div></div>
  <div class="stat-grid" id="vault-grid"></div>

</div>

<!-- ── MODAL ────────────────────────────────────────────────── -->
<div class="modal-bg" id="modal-bg" onclick="if(event.target===this)closeModal()">
  <div class="modal" id="modal-content"></div>
</div>

<script>
const D = {payload_json};
const BUILD_TIME = D.ts;

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
        <div class="mission-eta-l">days @ 8h/day</div>
        <div class="mission-eta-date">ETA ${{m.eta_date}}</div>
      </div>
    </div>
    <div class="mission-mega-bar">
      <div class="mission-mega-fill" style="width:${{m.overall_pct}}%"></div>
      <div class="mission-mega-pct">${{m.overall_pct}}%</div>
    </div>
    <div class="mission-stats">
      <div class="ms"><div class="ms-n" style="color:var(--cyan)">${{m.total_target}}</div><div class="ms-l">Total EPs</div></div>
      <div class="ms"><div class="ms-n" style="color:var(--green)">${{m.total_done}}</div><div class="ms-l">Done</div></div>
      <div class="ms"><div class="ms-n" style="color:var(--amber-2)">${{m.total_remaining}}</div><div class="ms-l">Remaining</div></div>
      <div class="ms"><div class="ms-n" style="color:var(--magenta)">${{m.hours_total}}h</div><div class="ms-l">Total est.</div></div>
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
    items.push(`<div class="running-row" style="border-left-color:var(--cyan)">
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
  el.innerHTML = Object.entries(D.pipeline).map(([k, v]) => {{
    const pct = Math.round(v.done / v.total * 100) || 0;
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
  }}).join('');
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
        <span class="cl-badge ${{s.alive ? 'live' : 'off'}}">${{s.alive ? 'LIVE' : 'OFF'}}</span>
      </div>
      <div class="cl-meta">PID ${{s.pid}} · ${{s.runtime_min}}m · #${{s.session_id}} · ${{s.cwd}}</div>
      <div style="display:flex;align-items:center;gap:6px;font-size:10px;color:var(--muted);margin-bottom:4px">
        <span>Context ${{pct}}%</span><span style="margin-left:auto">${{ik(s.tokens.latest_cache)}} / 200k</span>
      </div>
      <div class="pbar"><div class="pbar-fill" style="width:${{pct}}%;background:${{bc}}"></div></div>
      <div class="cl-tokens">
        <div class="cl-tok"><div class="cl-tok-n" style="color:var(--cyan)">${{ik(s.tokens.in)}}</div><div class="cl-tok-l">Input</div></div>
        <div class="cl-tok"><div class="cl-tok-n" style="color:var(--amber-2)">${{ik(s.tokens.out)}}</div><div class="cl-tok-l">Output</div></div>
        <div class="cl-tok"><div class="cl-tok-n" style="color:var(--purple)">${{s.tokens.msgs}}</div><div class="cl-tok-l">Msgs</div></div>
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
  if (mbt.feedback) tiles.push(`<div class="stat-tile"><div class="stat-tile-n" style="color:var(--magenta)">${{mbt.feedback}}</div><div class="stat-tile-l">Feedback</div></div>`);
  if (mbt.project) tiles.push(`<div class="stat-tile"><div class="stat-tile-n" style="color:var(--cyan)">${{mbt.project}}</div><div class="stat-tile-l">Project mem</div></div>`);
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

// ─── AUTO-REFRESH check ─────────────────────────────────────
function checkUpdate(){{
  fetch(location.href + '?_=' + Date.now(), {{cache: 'no-store'}})
    .then(r => r.text()).then(html => {{
      const m = html.match(/content="(\\d{{4}}-\\d{{2}}-\\d{{2}}T[^"]+)"/);
      if (m && m[1] !== BUILD_TIME) document.getElementById('upd-banner').classList.add('show');
    }}).catch(() => {{}});
}}
setInterval(checkUpdate, 60000);

// ─── INIT ───────────────────────────────────────────────────
renderPhases();
renderMission();
renderLive();
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
