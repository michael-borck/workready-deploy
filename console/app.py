"""WorkReady Console — local content editor + deploy runner.

Run from this directory:

    uv run --with fastapi --with uvicorn uvicorn app:app --port 7788

Then open http://127.0.0.1:7788

Binds to loopback only: reachable on your machine, not the network.
Optional shared token: set CONSOLE_TOKEN and append ?token=... to URLs.

What it can do:
  - Edit per-company content (brief.yaml, jobs.json, personas, job ads),
    portal config.js (sign-in journey steps), and the primer story.
  - Rebuild the affected static sites and preview them locally.
  - Deploy site content: commit + push changed repos (GitHub Pages
    redeploys automatically).
  - Deploy API: rebuild the VPS container over SSH (no-cache — the image
    clones the repos at build time) and verify health.

What it deliberately does NOT do:
  - Code changes, database edits, or anything admin.html already covers
    (students, codes, force-state, journey reports — at /admin here).
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse

CONSOLE_DIR = Path(__file__).resolve().parent
# console/ -> workready-deploy/ -> <workspace root with the sibling repos>
ROOT = Path(os.environ.get("WORKREADY_HOME", str(CONSOLE_DIR.parents[1])))
VPS_ALIAS = os.environ.get("WORKREADY_VPS", "vps")
VPS_DIR = os.environ.get("WORKREADY_VPS_DIR", "~/homelab/workready")
CONSOLE_TOKEN = os.environ.get("CONSOLE_TOKEN", "")

COMPANIES = [
    "nexuspoint-systems", "ironvale-resources", "meridian-advisory",
    "metro-council-wa", "southern-cross-financial", "horizon-foundation",
]
REPOS = COMPANIES + [
    "workready-portal", "workready-jobs", "workready-primer",
    "workready-api", "workready-deploy",
]

app = FastAPI(title="WorkReady Console", docs=None, redoc=None)


# ------------------------------------------------------------------ helpers

def _check_token(request: Request) -> None:
    if not CONSOLE_TOKEN:
        return
    if (request.query_params.get("token") != CONSOLE_TOKEN
            and request.headers.get("X-Console-Token") != CONSOLE_TOKEN):
        raise HTTPException(status_code=401, detail="Bad console token")


def _repo_path(rel: str) -> Path:
    """Resolve a repo-relative path inside the workspace — no escapes."""
    p = (ROOT / rel).resolve()
    if not str(p).startswith(str(ROOT.resolve())):
        raise HTTPException(status_code=400, detail="Path escapes workspace")
    return p


def _run(cmd: list[str], cwd: Path | None = None, timeout: int = 600) -> str:
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    out = (r.stdout or "") + (r.stderr or "")
    if r.returncode != 0:
        raise RuntimeError(f"exit {r.returncode}: {out.strip()[:2000]}")
    return out


def _editable_files() -> list[dict]:
    files: list[dict] = []
    for c in COMPANIES:
        files.append({"group": f"{c}", "path": f"{c}/brief.yaml"})
        files.append({"group": f"{c}", "path": f"{c}/jobs.json"})
        emp = ROOT / c / "content" / "employees"
        if emp.is_dir():
            for md in sorted(emp.glob("*.md")):
                if md.name.startswith("._") or "-prompt" in md.name:
                    continue
                files.append({"group": f"{c} · personas", "path": f"{c}/content/employees/{md.name}"})
        jobs = ROOT / c / "content" / "jobs"
        if jobs.is_dir():
            for md in sorted(jobs.glob("*.md")):
                if md.name.startswith("._"):
                    continue
                files.append({"group": f"{c} · job ads", "path": f"{c}/content/jobs/{md.name}"})
    files.append({"group": "portal", "path": "workready-portal/config.js"})
    files.append({"group": "primer", "path": "workready-primer/workready.ink"})
    allowed = {f["path"] for f in files}
    return files, allowed


def _repo_status(rel: str) -> dict:
    d = _repo_path(rel)
    if not (d / ".git").exists():
        return {"repo": rel, "exists": False}
    dirty = subprocess.run(
        ["git", "-c", "core.fileMode=false", "status", "--porcelain"],
        cwd=d, capture_output=True, text=True).stdout.strip()
    branch = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=d, capture_output=True, text=True).stdout.strip()
    last = subprocess.run(
        ["git", "log", "--oneline", "-1"],
        cwd=d, capture_output=True, text=True).stdout.strip()
    return {"repo": rel, "exists": True, "branch": branch,
            "dirty": bool(dirty), "changes": dirty[:1500], "last": last}


# ------------------------------------------------------------------ routes

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    _check_token(request)
    return FileResponse(CONSOLE_DIR / "static" / "index.html")


@app.get("/admin", response_class=HTMLResponse)
def admin(request: Request):
    _check_token(request)
    return FileResponse(CONSOLE_DIR / "static" / "admin.html")


@app.get("/api/files")
def files(request: Request):
    _check_token(request)
    files, _ = _editable_files()
    return {"root": str(ROOT), "files": files}


@app.get("/api/file")
def read_file(request: Request, path: str):
    _check_token(request)
    _, allowed = _editable_files()
    if path not in allowed:
        raise HTTPException(status_code=400, detail="File is not editable")
    f = _repo_path(path)
    if not f.is_file():
        raise HTTPException(status_code=404, detail="Not found")
    return {"path": path, "content": f.read_text(errors="replace")}


@app.post("/api/file")
def write_file(request: Request, payload: dict):
    _check_token(request)
    path = payload.get("path", "")
    _, allowed = _editable_files()
    if path not in allowed:
        raise HTTPException(status_code=400, detail="File is not editable")
    f = _repo_path(path)
    f.write_text(payload.get("content", ""), encoding="utf-8")
    return {"saved": path, "bytes": len(payload.get("content", ""))}


@app.get("/api/status")
def status(request: Request):
    _check_token(request)
    return {"repos": [_repo_status(r) for r in REPOS]}


@app.post("/api/build/{scope}")
def build(scope: str, request: Request):
    """Rebuild static output for a scope: a company slug, jobs, primer, or all."""
    _check_token(request)
    log: list[str] = []
    scopes = [scope] if scope != "all" else COMPANIES + ["jobs", "primer"]
    for s in scopes:
        if s in COMPANIES:
            d = _repo_path(s)
            log.append(f"$ build {s}")
            log.append(_run(
                ["uv", "run", "--quiet", "--with", "pyyaml", "--with", "jinja2",
                 "--with", "markdown", "python3", "site/build.py"], cwd=d))
        elif s == "jobs":
            d = _repo_path("workready-jobs")
            log.append("$ build jobs")
            log.append(_run(["python3", "build.py"], cwd=d))
        elif s == "primer":
            d = _repo_path("workready-primer")
            log.append("$ build primer")
            log.append(_run(["./build.sh"], cwd=d, timeout=900))
        else:
            raise HTTPException(status_code=400, detail=f"Unknown scope {scope}")
    return {"log": "\n".join(log)}


@app.post("/api/deploy/site")
def deploy_site(request: Request, payload: dict | None = None):
    """Commit (all dirty repos) + push. Pages redeploys automatically."""
    _check_token(request)
    message = (payload or {}).get("message") or "Content update via WorkReady Console"
    log: list[str] = []
    pushed = []
    for rel in REPOS:
        d = _repo_path(rel)
        st = _repo_status(rel)
        if not st.get("dirty"):
            continue
        log.append(f"$ {rel}: committing changes")
        _run(["git", "add", "-A"], cwd=d)
        _run(["git", "commit", "-m", message], cwd=d)
        log.append(_run(["git", "push", "origin", "main"], cwd=d, timeout=300))
        pushed.append(rel)
    if not pushed:
        log.append("Nothing to deploy — working trees clean.")
    log.append(f"Pushed: {', '.join(pushed) if pushed else '(none)'}")
    log.append("GitHub Pages redeploys changed sites automatically (~1 min).")
    return {"pushed": pushed, "log": "\n".join(log)}


@app.post("/api/deploy/api")
def deploy_api(request: Request, payload: dict | None = None):
    """Rebuild + recreate the API container on the VPS, then health-check.

    --no-cache is required: the image clones the repos in a build layer,
    so a cached rebuild would ship stale code.
    """
    _check_token(request)
    dry = bool((payload or {}).get("dry_run"))
    remote = (f"cd {VPS_DIR} && docker compose build --no-cache && "
              "docker compose up -d --force-recreate && sleep 8 && "
              "docker exec workready-api curl -s http://localhost:8000/health")
    if dry:
        return {"log": f"[dry-run] ssh {VPS_ALIAS} '{remote}'"}
    log = [f"$ ssh {VPS_ALIAS} (rebuild + recreate, ~3-5 min)"]
    out = _run(["ssh", VPS_ALIAS, remote], timeout=1800)
    log.append(out)
    ok = '"status":"ok"' in out or '"status": "ok"' in out
    log.append("HEALTH: " + ("OK" if ok else "FAILED — check docker logs workready-api"))
    return {"ok": ok, "log": "\n".join(log)}


@app.get("/api/deploy/preview-note")
def preview_note(request: Request):
    _check_token(request)
    return {"note": "Preview rebuilt sites locally before deploying: "
                    + ", ".join(f"/preview/{c}/" for c in COMPANIES)}


# local previews of built output
for _c in COMPANIES:
    _dist = ROOT / _c / "dist"
    if _dist.is_dir():
        from fastapi.staticfiles import StaticFiles
        app.mount(f"/preview/{_c}", StaticFiles(directory=str(_dist), html=True), name=f"prev-{_c}")

_jobs_dist = ROOT / "workready-jobs" / "dist"
if _jobs_dist.is_dir():
    from fastapi.staticfiles import StaticFiles
    app.mount("/preview/jobs", StaticFiles(directory=str(_jobs_dist), html=True), name="prev-jobs")
