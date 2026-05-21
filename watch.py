#!/usr/bin/env python3
"""
Auto-rebuild + push watcher
รันทิ้งไว้บน Mac → rebuild ทุก 5 นาที หรือเมื่อ file เปลี่ยน → git push → GitHub Pages อัพเดท
"""

import time, subprocess, os, hashlib
from pathlib import Path

ROOT    = Path(__file__).parent
TRANS   = Path.home() / "Documents/Norms-Corp/Social-Norms/03-Knowledge/transcripts"
DRAFTS  = Path.home() / "Documents/Norms-Corp/Social-Norms/02-Content/content_pipeline/drafts"
BUILD   = ROOT / "build.py"
INDEX   = ROOT / "index.html"
INTERVAL = 900  # วินาที (15 นาที · ลด git noise · pull-to-refresh ทดแทน manual)

def run(cmd, **kw):
    return subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, **kw)

def fingerprint():
    """Hash ของทุก file ที่ monitor — ถ้าเปลี่ยนต้อง rebuild"""
    h = hashlib.md5()
    for folder in [TRANS, DRAFTS]:
        if folder.exists():
            for f in sorted(folder.rglob("*.txt")) + sorted(folder.rglob("*.json")):
                h.update(f.name.encode())
                h.update(str(f.stat().st_mtime).encode())
    return h.hexdigest()

def rebuild():
    r = run(["python3", str(BUILD)])
    if r.returncode != 0:
        print(f"[ERROR] build failed:\n{r.stderr}")
        return False
    print("[✓] Built index.html")
    return True

def push(msg):
    run(["git", "add", "index.html"])
    r = run(["git", "commit", "-m", msg])
    if "nothing to commit" in r.stdout + r.stderr:
        print("[~] No changes to push")
        return
    r2 = run(["git", "push"])
    if r2.returncode == 0:
        print(f"[✓] Pushed: {msg}")
    else:
        print(f"[ERROR] push failed: {r2.stderr}")

def stamp():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def main():
    print(f"[Watcher] started — rebuild every {INTERVAL//60} min or on file change")
    print(f"[Watcher] monitoring: {TRANS}, {DRAFTS}")

    last_fp   = ""
    last_push = 0

    while True:
        try:
            fp = fingerprint()
            now = time.time()
            changed = fp != last_fp
            due     = (now - last_push) >= INTERVAL

            if changed or due:
                reason = "file changed" if changed else "scheduled"
                print(f"\n[{stamp()}] Rebuilding ({reason})...")
                if rebuild():
                    push(f"auto: {stamp()} ({reason})")
                    last_fp   = fingerprint()
                    last_push = now
        except KeyboardInterrupt:
            print("\n[Watcher] stopped")
            break
        except Exception as e:
            print(f"[ERROR] {e}")

        time.sleep(30)

if __name__ == "__main__":
    main()
