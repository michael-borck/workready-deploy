"""Local publishing console. No credentials or mutations are exposed to previews."""
from __future__ import annotations

import hashlib
import ast
import json
import os
import secrets
import shlex
import subprocess
import time
from datetime import datetime, timezone
from contextlib import contextmanager
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse

import httpx
import yaml
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

HERE = Path(__file__).resolve().parent
ROOT = Path(os.environ.get('WORKREADY_HOME', str(HERE.parents[1]))).resolve()
BOOTSTRAP_TOKEN = os.environ.get('CONSOLE_TOKEN') or secrets.token_urlsafe(32)
API_BASE = os.environ.get('WORKREADY_API_BASE', 'https://workready-api.eduserver.au').rstrip('/')
VPS_ALIAS = os.environ.get('WORKREADY_VPS', 'vps')
VPS_DIR = os.environ.get('WORKREADY_VPS_DIR', 'homelab/workready')
COMPANIES = ['nexuspoint-systems', 'ironvale-resources', 'meridian-advisory',
             'metro-council-wa', 'southern-cross-financial', 'horizon-foundation']
REPOS = ['workready-api'] + COMPANIES + ['workready-jobs', 'workready-primer', 'workready-portal', 'workready-deploy']
SESSIONS: dict = {}
PLANS: dict = {}
OPERATIONS = Lock()
LOGIN_ATTEMPTS: dict = {}
app = FastAPI(title='WorkReady local console', docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost'])


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@app.middleware('http')
async def boundary(request: Request, call_next):
    host = request.headers.get('host', '')
    if host.split(':')[0] not in ('localhost', '127.0.0.1'):
        return JSONResponse({'detail': 'Invalid Host'}, status_code=400)
    mutable = request.method not in ('GET', 'HEAD', 'OPTIONS')
    if mutable and request.headers.get('origin') != f'{request.url.scheme}://{host}':
        return JSONResponse({'detail': 'Cross-origin operation refused'}, status_code=403)
    # These endpoints are public only to support the local login screen.
    public = request.url.path in ('/', '/api/login')
    session = SESSIONS.get(digest(request.cookies.get('wr_console', '')))
    if not public:
        if not session or session['expires'] < time.monotonic():
            return JSONResponse({'detail': 'Please unlock the local console'}, status_code=401)
        if mutable and not secrets.compare_digest(request.headers.get('x-console-csrf', ''), session['csrf']):
            return JSONResponse({'detail': 'Invalid request token'}, status_code=403)
        request.state.session = session
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; frame-ancestors 'none'; form-action 'self'"
    return response


@contextmanager
def operation():
    if not OPERATIONS.acquire(blocking=False):
        raise HTTPException(409, 'A build or publish is already running')
    try:
        yield
    finally:
        OPERATIONS.release()


def safe_path(relative: str) -> Path:
    path = (ROOT / relative).resolve()
    if not path.is_relative_to(ROOT):
        raise HTTPException(400, 'Path escapes the workspace')
    return path


def editable() -> list[dict]:
    files = []
    for company in COMPANIES:
        files.append({'path': f'workready-api/jobs/{company}.json', 'group': company + ' · runtime jobs, hours, tasks and personas'})
        files.append({'path': f'{company}/brief.yaml', 'group': company + ' · website profile'})
        for kind in ('employees', 'jobs', 'docs'):
            for path in sorted((ROOT / company / 'content' / kind).rglob('*.md')):
                if not path.name.startswith('._'):
                    files.append({'path': str(path.relative_to(ROOT)), 'group': company + ' · website ' + kind})
    files.extend([{'path': 'workready-portal/config.js', 'group': 'Portal copy'},
                  {'path': 'workready-deploy/pacing.json', 'group': 'Runtime pacing preset; redeploy API to apply'},
                  {'path': 'workready-primer/workready.ink', 'group': 'Primer story'}])
    return files


def run(command: list[str], cwd: Path | None = None, timeout: int = 600) -> str:
    try:
        result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise HTTPException(504, 'Command timed out. Inspect the operation before retrying.')
    output = result.stdout + result.stderr
    if result.returncode:
        raise HTTPException(409, output[-6000:] or 'Command failed')
    return output


def git(repo: str, *args) -> str:
    return run(['git', '-c', 'core.fileMode=false', *args], safe_path(repo), timeout=300)


def status(repo: str) -> dict:
    if not safe_path(repo).is_dir():
        return {'repo': repo, 'exists': False}
    dirty = git(repo, 'status', '--porcelain')
    branch = git(repo, 'branch', '--show-current').strip()
    upstream = run(['git', 'rev-parse', '--verify', 'origin/main'], safe_path(repo)).strip()
    ahead = git(repo, 'rev-list', '--count', upstream + '..HEAD').strip()
    return {'repo': repo, 'exists': True, 'dirty': bool(dirty), 'changes': dirty,
            'branch': branch, 'ahead': int(ahead), 'head': git(repo, 'rev-parse', 'HEAD').strip()}


@app.get('/')
def index():
    return FileResponse(HERE / 'static/index.html')


@app.post('/api/login')
def login(request: Request, payload: dict):
    key = request.client.host if request.client else 'local'
    now = time.monotonic()
    attempts = [t for t in LOGIN_ATTEMPTS.get(key, []) if t > now - 60]
    if len(attempts) >= 10:
        raise HTTPException(429, 'Please wait a minute', headers={'Retry-After': '60'})
    LOGIN_ATTEMPTS[key] = attempts + [now]
    if not secrets.compare_digest(str(payload.get('token', '')), BOOTSTRAP_TOKEN):
        raise HTTPException(401, 'Incorrect local console key')
    session_id = secrets.token_urlsafe(32)
    csrf = secrets.token_urlsafe(24)
    SESSIONS[digest(session_id)] = {'csrf': csrf, 'expires': now + 28800, 'admin_token': None}
    for sid in list(SESSIONS):
        if SESSIONS[sid]['expires'] < now:
            del SESSIONS[sid]
    response = JSONResponse({'csrf': csrf})
    response.set_cookie('wr_console', session_id, httponly=True, samesite='strict', max_age=28800)
    return response


@app.get('/api/session')
def session(request: Request):
    return {'csrf': request.state.session['csrf'], 'api_base': API_BASE}


@app.post('/api/logout')
def logout(request: Request):
    SESSIONS.pop(digest(request.cookies.get('wr_console', '')), None)
    response = JSONResponse({'status': 'locked'})
    response.delete_cookie('wr_console')
    return response


@app.get('/admin')
def admin():
    return FileResponse(HERE / 'static/admin.html')


@app.post('/api/admin/connect')
def connect_admin(request: Request, payload: dict):
    token = str(payload.get('token', ''))
    with httpx.Client(timeout=15) as client:
        response = client.get(API_BASE + '/api/v1/admin/health', headers={'Authorization': 'Bearer ' + token})
    if response.status_code != 200:
        raise HTTPException(401, 'Admin credential was not accepted')
    request.state.session['admin_token'] = token
    return {'connected': True}


@app.api_route('/api/admin/{path:path}', methods=['GET', 'POST', 'DELETE'])
async def proxy_admin(path: str, request: Request):
    if not path or any(part in ('.', '..') for part in path.split('/')) or '\\' in path:
        raise HTTPException(400, 'Invalid admin path')
    token = request.state.session.get('admin_token')
    if not token:
        raise HTTPException(401, 'Connect an admin credential first')
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.request(request.method, API_BASE + '/api/v1/admin/' + path,
            params=list(request.query_params.multi_items()), content=await request.body(),
            headers={'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    return Response(response.content, status_code=response.status_code, media_type='application/json')


@app.get('/api/files')
def files():
    return {'files': editable()}


@app.get('/api/file')
def read_file(path: str):
    if path not in {f['path'] for f in editable()}:
        raise HTTPException(400, 'File is not editable')
    return {'path': path, 'content': safe_path(path).read_text()}


@app.post('/api/file')
def save_file(payload: dict):
    path, content = payload.get('path', ''), payload.get('content', '')
    if path not in {f['path'] for f in editable()} or not isinstance(content, str) or len(content) > 1000000:
        raise HTTPException(400, 'Invalid file or content')
    try:
        if path == 'workready-deploy/pacing.json':
            validate_pacing(json.loads(content))
        elif path.endswith('.json'):
            data = json.loads(content)
            if not isinstance(data, dict) or not all(k in data for k in ('company_slug', 'jobs')):
                raise ValueError('Job export needs company_slug and jobs')
        if path.endswith('.yaml'):
            if not isinstance(yaml.safe_load(content), dict):
                raise ValueError('Company profile must be a mapping')
    except (ValueError, yaml.YAMLError) as error:
        raise HTTPException(400, str(error))
    with operation():
        safe_path(path).write_text(content)
    return {'saved': path}


@app.get('/api/status')
def repo_status():
    return {'repos': [status(repo) for repo in REPOS]}


def build_for(paths: list[str]) -> tuple[list[str], str]:
    generated, logs, scopes = [], [], set()
    for path in paths:
        if path.startswith('workready-api/jobs/'):
            company = Path(path).stem
            if company not in COMPANIES:
                raise HTTPException(400, 'Unknown company')
            scopes.add(company)
            target = safe_path(company + '/jobs.json')
            target.write_text(safe_path(path).read_text())
            # Company-root exports are build inputs; include them when tracked.
            if git(company, 'ls-files', 'jobs.json').strip():
                generated.append(company + '/jobs.json')
        elif path.split('/')[0] in COMPANIES:
            scopes.add(path.split('/')[0])
        elif path.startswith('workready-primer/'):
            scopes.add('primer')
        elif path == 'workready-portal/config.js':
            logs.append(run(['node', '--check', 'config.js'], ROOT / 'workready-portal'))
    for scope in sorted(scopes):
        if scope == 'primer':
            logs.append(run(['bash', 'build.sh'], ROOT / 'workready-primer'))
            generated += ['workready-primer/workready.ink.json', 'workready-primer/lib/ink.js']
        else:
            logs.append(run(['uv', 'run', '--quiet', '--with', 'pyyaml', '--with', 'jinja2', '--with', 'markdown', 'python3', 'site/build.py'], ROOT / scope))
            generated += [str(p.relative_to(ROOT)) for p in (ROOT / scope / 'dist').rglob('*') if p.is_file() and not p.name.startswith('._')]
            # Include deleted tracked build output too.
            generated += [scope + '/' + p for p in git(scope, 'ls-files', 'dist').splitlines()]
    return sorted(set(paths + generated)), '\n'.join(logs)


def fingerprint(paths: list[str], repos: list[str]) -> str:
    h = hashlib.sha256()
    for repo in repos:
        h.update(git(repo, 'rev-parse', 'HEAD').encode())
    for name in sorted(paths):
        p = safe_path(name)
        h.update(name.encode())
        h.update(p.read_bytes() if p.is_file() else b'DELETED')
    return h.hexdigest()


@app.post('/api/plan')
def plan(request: Request, payload: dict):
    paths = sorted(set(payload.get('paths', [])))
    if not paths or any(path not in {f['path'] for f in editable()} for path in paths):
        raise HTTPException(400, 'Select editable files to publish')
    with operation():
        # Do not overwrite manual edits to build products, or commit staged work.
        for repo in REPOS:
            if git(repo, 'diff', '--cached', '--name-only').strip():
                raise HTTPException(409, f'{repo} has staged changes. Resolve those outside the console.')
        scopes = {Path(p).stem if p.startswith('workready-api/jobs/') else p.split('/')[0] for p in paths}
        for repo in scopes & set(COMPANIES):
            if git(repo, 'status', '--porcelain', '--', 'dist').strip():
                raise HTTPException(409, f'{repo}/dist has local changes. Review them before rebuilding.')
        outputs, logs = build_for(paths)
        repos = [r for r in REPOS if any(p.startswith(r + '/') for p in outputs)]
        diffs = []
        for repo in repos:
            local = [p[len(repo) + 1:] for p in outputs if p.startswith(repo + '/')]
            diffs.append(git(repo, 'diff', '--', *local))
        plan_id = secrets.token_urlsafe(24)
        if len(PLANS) > 100:
            PLANS.clear()
        PLANS[plan_id] = {'paths': outputs, 'repos': repos, 'stamp': fingerprint(outputs, repos),
                          'owner': request.state.session['csrf'], 'expires': time.monotonic() + 1800}
        return {'id': plan_id, 'paths': outputs, 'repos': repos, 'diff': '\n'.join(diffs), 'log': logs,
                'api_rebuild_needed': any(p.startswith('workready-api/') for p in outputs)}


@app.post('/api/deploy/site')
def deploy_site(request: Request, payload: dict):
    selected = PLANS.get(payload.get('plan', ''))
    if not selected or selected['owner'] != request.state.session['csrf'] or selected['expires'] < time.monotonic():
        raise HTTPException(409, 'Build a fresh deployment plan')
    with operation():
        if fingerprint(selected['paths'], selected['repos']) != selected['stamp']:
            raise HTTPException(409, 'Files changed since the plan. Build a fresh plan.')
        logs = []
        for repo in selected['repos']:
            if git(repo, 'diff', '--cached', '--name-only').strip() or git(repo, 'branch', '--show-current').strip() != 'main':
                raise HTTPException(409, f'{repo}: expected main with no staged work')
        for repo in selected['repos']:
            local = [p[len(repo) + 1:] for p in selected['paths'] if p.startswith(repo + '/')]
            logs.append(git(repo, 'add', '--', *local))
            if git(repo, 'diff', '--cached', '--name-only').strip():
                logs.append(git(repo, 'commit', '-m', str(payload.get('message') or 'Update simulation content')))
            # Push even if the tree is clean, to retry a previous failed push.
            logs.append(git(repo, 'push', 'origin', 'main'))
        PLANS.pop(payload['plan'], None)
        return {'log': '\n'.join(logs), 'pushed': selected['repos']}


@app.post('/api/retry-push')
def retry_push(payload: dict):
    repo = payload.get('repo')
    if repo not in REPOS:
        raise HTTPException(400, 'Unknown repo')
    with operation():
        return {'log': git(repo, 'push', 'origin', 'main')}


@app.post('/api/deploy/api')
def deploy_api(payload: dict):
    pacing = validate_pacing(json.loads((ROOT / 'workready-deploy/pacing.json').read_text()))
    directory = VPS_DIR.removeprefix('~/')
    if directory.startswith('/') or '..' in directory.split('/'):
        raise HTTPException(400, 'VPS directory must be relative to the SSH user home')
    compose = 'docker compose -f docker-compose.yml -f workready-deploy/compose.privacy.yml -f compose.pacing.yml'
    if payload.get('dry_run'):
        return {'log': f'Build published content in GitHub Actions, then ssh {VPS_ALIAS}: docker pull release image; {compose} up -d --no-build --force-recreate', 'dry_run': True}
    with operation():
        image, build_log = build_published_image()
        overlay = json.dumps({'services': {'workready-api': {'image': image, 'environment': pacing}}})
        remote = ('cd "$HOME"/' + shlex.quote(directory) + ' && '
                  'git -C workready-deploy pull --ff-only && '
                  'printf %s ' + shlex.quote(overlay) + ' > compose.pacing.yml && '
                  'docker image tag "$(docker inspect --format \'{{.Image}}\' workready-api)" workready:rollback && '
                  'docker pull ' + shlex.quote(image) + ' && '
                  'export WORKREADY_TRUSTED_PROXY_IPS="$(docker inspect --format \'{{(index .NetworkSettings.Networks "caddy_default").IPAddress}}\' caddy)" && '
                  + compose + ' up -d --no-build --force-recreate')
        output = run(['ssh', '-o', 'BatchMode=yes', VPS_ALIAS, remote], timeout=1800)
        # Check HTTP + JSON, not a substring in the Docker build log.
        for _ in range(12):
            try:
                response = httpx.get(API_BASE + '/health', timeout=5)
                if response.status_code == 200 and response.json().get('status') == 'ok':
                    return {'ok': True, 'log': build_log + '\n' + output, 'image': image}
            except (httpx.HTTPError, ValueError):
                pass
            time.sleep(2)
        raise HTTPException(502, 'Health check failed. Previous image retained as workready:rollback; inspect before rollback.')


def build_published_image() -> tuple[str, str]:
    """Build on GitHub, where the image's external dependencies are reachable."""
    repository = 'michael-borck/workready-deploy'
    since = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    run(['gh', 'workflow', 'run', 'build.yml', '--repo', repository, '--ref', 'main'])
    for _ in range(30):
        runs = json.loads(run(['gh', 'run', 'list', '--repo', repository, '--workflow', 'build.yml',
                              '--event', 'workflow_dispatch', '--limit', '5',
                              '--json', 'databaseId,createdAt,headSha']))
        fresh = [r for r in runs if r['createdAt'] >= since]
        if fresh:
            selected = min(fresh, key=lambda r: r['createdAt'])
            log = run(['gh', 'run', 'watch', str(selected['databaseId']), '--repo', repository, '--exit-status'], timeout=1800)
            return 'ghcr.io/michael-borck/workready:' + selected['headSha'][:7], log
        time.sleep(2)
    raise HTTPException(504, 'GitHub did not report the new image-build run. Check Actions before retrying.')


def validate_pacing(data: dict) -> dict:
    if not isinstance(data, dict):
        raise ValueError('Pacing must be a JSON object')
    allowed = {'SIMULATION_PRESET', 'TASK_DEADLINE_DAYS', 'TASK_NEXT_TASK_DELAY_MINUTES',
               'TASK_FEEDBACK_DELAY_MINUTES', 'RESUME_FEEDBACK_DELAY_MINUTES',
               'INTERVIEW_FEEDBACK_DELAY_MINUTES', 'LUNCHROOM_INVITE_LEAD_HOURS'}
    if set(data) - allowed or data.get('SIMULATION_PRESET', 'custom') not in ('custom', 'workshop', 'semester'):
        raise ValueError('Unknown pacing option')
    for key, value in data.items():
        if key != 'SIMULATION_PRESET' and (not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 86400):
            raise ValueError('Timing values must be nonnegative integers no greater than 86400')
    # Read the API's literal preset table without executing application code.
    tree = ast.parse((ROOT / 'workready-api/workready_api/scheduling.py').read_text())
    presets = next(ast.literal_eval(node.value) for node in tree.body
                   if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'PRESETS' for t in node.targets))
    merged = {**presets[data.get('SIMULATION_PRESET', 'custom')], **data}
    return {k: str(v).lower() if isinstance(v, bool) else str(v) for k, v in merged.items()}


# Run on localhost:7789, separately from the privileged 127.0.0.1:7788 UI.
preview_app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
preview_app.add_middleware(TrustedHostMiddleware, allowed_hosts=['localhost'])


@preview_app.middleware('http')
async def isolate_preview(request: Request, call_next):
    if request.method not in ('GET', 'HEAD'):
        return Response(status_code=405)
    response = await call_next(request)
    company = request.url.path.strip('/').split('/')[0]
    if company in COMPANIES:
        response.set_cookie('wr_preview_company', company, samesite='strict')
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-src 'none'; form-action 'none'; base-uri 'self'"
    response.headers['Referrer-Policy'] = 'no-referrer'
    return response


for company in COMPANIES:
    if (ROOT / company / 'dist').is_dir():
        preview_app.mount('/' + company, StaticFiles(directory=ROOT / company / 'dist', html=True))


@preview_app.get('/{path:path}')
def preview_asset(path: str, request: Request):
    """Resolve the existing company sites' root-relative links on the preview host."""
    company = request.cookies.get('wr_preview_company')
    if company not in COMPANIES:
        raise HTTPException(404, 'Open a company preview first')
    root = (ROOT / company / 'dist').resolve()
    target = (root / path).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        raise HTTPException(404, 'Preview file not found')
    return FileResponse(target)
