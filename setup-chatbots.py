#!/usr/bin/env python3
"""
WorkReady — AnythingLLM Chatbot Setup

Creates one "hiring desk" chatbot per company in AnythingLLM. Each
workspace gets a system prompt built from the company's brief.yaml
and open job listings, plus RAG documents uploaded for deeper context.

These are the public-facing chatbots embedded on each company's
careers/contact page. They know about the company and its roles but
NOT about individual student conversations (that's the email system).

Usage:
    python3 setup-chatbots.py                    # create all 6
    python3 setup-chatbots.py ironvale-resources # just one company
    python3 setup-chatbots.py --list             # show existing workspaces
    python3 setup-chatbots.py --update-prompts   # update prompts only

Environment:
    ANYTHINGLLM_API_KEY — required (checks env, then .env file)
    ANYTHINGLLM_BASE_URL — default: https://chat.eduserver.au/api/v1

The embed UUIDs are printed at the end — paste them into each company's
site templates to wire up the chat widget.
"""

import json
import os
import sys
import time
import yaml
import requests
from pathlib import Path
from datetime import datetime


# ============================================================================
# Configuration
# ============================================================================

def load_env_file():
    """Load .env file if it exists (don't override existing env vars)."""
    for env_path in [Path(".env"), Path(__file__).parent / ".env"]:
        if env_path.is_file():
            for line in env_path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key not in os.environ:
                    os.environ[key] = value


load_env_file()

API_KEY = os.environ.get("ANYTHINGLLM_API_KEY", "")
BASE_URL = os.environ.get("ANYTHINGLLM_BASE_URL", "https://chat.eduserver.au/api/v1")

if not API_KEY:
    print("ERROR: ANYTHINGLLM_API_KEY not set in environment or .env file")
    sys.exit(1)

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json",
}

# Where to find company data — try the loco-ensyo directory structure
SITES_DIR = Path(os.environ.get("SITES_DIR", str(Path(__file__).parent.parent)))

COMPANIES = {
    "ironvale-resources": {
        "name": "IronVale Resources",
        "domain": "ironvaleresources.eduserver.au",
        "workspace_name": "workready-ironvale-hiring",
    },
    "nexuspoint-systems": {
        "name": "NexusPoint Systems",
        "domain": "nexuspointsystems.eduserver.au",
        "workspace_name": "workready-nexuspoint-hiring",
    },
    "horizon-foundation": {
        "name": "Horizon Foundation",
        "domain": "horizonfoundation.eduserver.au",
        "workspace_name": "workready-horizon-hiring",
    },
    "southern-cross-financial": {
        "name": "Southern Cross Financial",
        "domain": "southerncrossfinancial.eduserver.au",
        "workspace_name": "workready-southern-cross-hiring",
    },
    "metro-council-wa": {
        "name": "Metro Council WA",
        "domain": "metrocouncilwa.eduserver.au",
        "workspace_name": "workready-metro-hiring",
    },
    "meridian-advisory": {
        "name": "Meridian Advisory",
        "domain": "meridianadvisory.eduserver.au",
        "workspace_name": "workready-meridian-hiring",
    },
}

# Domains allowed to embed the chat widget
EMBED_ALLOWLIST = [
    "localhost",
    "*.eduserver.au",
]


# ============================================================================
# Helpers
# ============================================================================

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def ok(msg):
    print(f"  ✓ {msg}")

def fail(msg):
    print(f"  ✗ {msg}")

def api_get(endpoint):
    r = requests.get(f"{BASE_URL}{endpoint}", headers=HEADERS)
    r.raise_for_status()
    return r.json()

def api_post(endpoint, data):
    r = requests.post(f"{BASE_URL}{endpoint}", headers=HEADERS, json=data)
    try:
        return r.json()
    except Exception:
        return {"error": f"HTTP {r.status_code}: {r.text[:200]}"}

def api_upload(endpoint, filepath):
    h = {"Authorization": f"Bearer {API_KEY}"}
    with open(filepath, "rb") as f:
        r = requests.post(f"{BASE_URL}{endpoint}", headers=h, files={"file": f})
    return r.json()


# ============================================================================
# Data loading
# ============================================================================

def load_company_data(slug: str) -> dict:
    """Load brief.yaml and jobs.json for a company."""
    company_dir = SITES_DIR / slug

    # Brief
    brief = {}
    brief_path = company_dir / "brief.yaml"
    if brief_path.is_file():
        brief = yaml.safe_load(brief_path.read_text(encoding="utf-8")) or {}

    # Jobs
    jobs = []
    jobs_path = company_dir / "jobs.json"
    if jobs_path.is_file():
        jobs_data = json.loads(jobs_path.read_text(encoding="utf-8"))
        jobs = jobs_data.get("jobs", [])

    return {"brief": brief, "jobs": jobs}


def build_system_prompt(slug: str, data: dict) -> str:
    """Build the hiring desk system prompt from company data."""
    brief = data["brief"]
    jobs = data["jobs"]
    company = brief.get("company", {})
    profile = company.get("profile", {})
    scenario = company.get("scenario", {})
    company_name = company.get("name", slug.replace("-", " ").title())

    # Build job listing summary
    job_lines = []
    for j in jobs:
        title = j.get("title", "")
        dept = j.get("department", "")
        emp_type = j.get("employment_type", "")
        reports_to = j.get("reports_to", "")
        brief_desc = j.get("brief", "")
        job_lines.append(
            f"- {title} ({dept}, {emp_type})"
            + (f" — reports to {reports_to}" if reports_to else "")
            + (f"\n  {brief_desc}" if brief_desc else "")
        )

    jobs_text = "\n".join(job_lines) if job_lines else "No current openings listed."

    # Key facts
    facts = profile.get("key_facts", [])
    facts_text = "\n".join(f"- {f}" for f in facts) if facts else ""

    # Services
    services = profile.get("services", [])
    services_text = "\n".join(f"- {s}" for s in services) if services else ""

    # Business hours
    bh = company.get("business_hours", {})
    bh_text = ""
    if bh:
        bh_text = f"Business hours: {bh.get('start', 9)}:00–{bh.get('end', 17)}:00, {bh.get('description', 'weekdays')}"

    prompt = f"""You are the hiring desk assistant at {company_name}.

You help prospective applicants learn about the company and its open roles. You are friendly, professional, and knowledgeable about the organisation. You answer questions about:
- The company, its culture, and what it does
- Open positions and what they involve
- The application and hiring process
- General questions about working here

You do NOT:
- Make promises about hiring outcomes
- Share confidential or internal information
- Discuss specific applicant details or application statuses
- Pretend to be a specific named employee

If someone asks about their application status, direct them to check their WorkReady portal inbox or email the company's careers address.

Keep responses concise (2-3 paragraphs max) and helpful. Use a warm but professional tone that matches {company_name}'s culture.

=== COMPANY PROFILE ===

{company_name}
{company.get('tagline', '')}
Location: {company.get('location', 'Perth, Western Australia')}
Founded: {profile.get('founded', '')}
Employees: {profile.get('employees', '')}
Structure: {profile.get('structure', '')}
{bh_text}

{profile.get('description', '')}

Key Facts:
{facts_text}

What We Do:
{services_text}

=== CURRENT SITUATION ===

{scenario.get('name', '')}
{scenario.get('description', '')}

=== OPEN POSITIONS ===

{jobs_text}

=== HIRING PROCESS ===

Our standard process:
1. Submit your CV and a cover letter via the careers page or by emailing careers@{COMPANIES[slug]['domain'].replace('.eduserver.au', '')}.com.au
2. If shortlisted, you'll be invited to an interview with the hiring manager
3. Decisions are communicated within one week of interviews

For questions about specific roles, feel free to ask here or contact the hiring manager listed on the role description.
"""
    return prompt.strip()


def build_rag_document(slug: str, data: dict) -> str:
    """Build a single RAG document combining company profile + jobs."""
    brief = data["brief"]
    jobs = data["jobs"]
    company = brief.get("company", {})
    profile = company.get("profile", {})

    sections = [
        f"# {company.get('name', slug)} — Company Information",
        "",
        f"## About",
        profile.get("description", ""),
        "",
    ]

    # Employees
    employees = brief.get("employees", [])
    if employees:
        sections.append("## Key People")
        for emp in employees:
            name = emp.get("name", "")
            role = emp.get("role", "")
            bg = emp.get("customisation", {}).get("background", "")
            sections.append(f"### {name} — {role}")
            if bg:
                sections.append(bg.strip())
            sections.append("")

    # Documents
    docs = brief.get("documents", [])
    if docs:
        sections.append("## Internal Documents Available")
        for doc in docs:
            sections.append(f"- {doc.get('title', '')}: {doc.get('brief', '')}")
        sections.append("")

    # Jobs
    if jobs:
        sections.append("## Open Positions")
        for j in jobs:
            sections.append(f"### {j.get('title', '')}")
            sections.append(f"Department: {j.get('department', '')}")
            sections.append(f"Type: {j.get('employment_type', '')}")
            sections.append(f"Reports to: {j.get('reports_to', '')}")
            sections.append(j.get("brief", ""))
            if j.get("description"):
                sections.append("")
                sections.append(j["description"][:2000])
            sections.append("")

    return "\n".join(sections)


# ============================================================================
# Workspace operations
# ============================================================================

def list_workspaces():
    """List existing AnythingLLM workspaces."""
    result = api_get("/workspaces")
    workspaces = result.get("workspaces", [])
    log(f"Found {len(workspaces)} workspaces")
    for ws in workspaces:
        name = ws.get("name", "?")
        slug = ws.get("slug", "?")
        print(f"  {slug} — {name}")
    return workspaces


def create_or_update_workspace(slug: str, company_info: dict, data: dict) -> dict:
    """Create or update a workspace for a company."""
    ws_name = company_info["workspace_name"]
    prompt = build_system_prompt(slug, data)

    # Check if workspace already exists
    try:
        existing = api_get(f"/workspace/{ws_name}")
        ws = existing.get("workspace")
        if ws:
            # Update existing
            log(f"Updating existing workspace: {ws_name}")
            result = api_post(f"/workspace/{ws_name}/update", {
                "openAiPrompt": prompt,
                "openAiTemp": 0.7,
                "openAiHistory": 20,
            })
            return result.get("workspace", {})
    except Exception:
        pass

    # Create new
    log(f"Creating workspace: {ws_name}")
    result = api_post("/workspace/new", {
        "name": ws_name,
        "openAiPrompt": prompt,
        "openAiTemp": 0.7,
        "openAiHistory": 20,
        "chatMode": "query",
        "similarityThreshold": 0,
        "topN": 8,
    })

    ws = result.get("workspace", {})
    if ws.get("slug"):
        ok(f"Created workspace: {ws['slug']}")
    else:
        fail(f"Failed to create workspace: {result}")

    return ws


def create_embed(ws_slug: str, company_info: dict) -> str | None:
    """Create an embed widget for a workspace. Returns the embed UUID."""
    domain = company_info["domain"]

    log(f"Creating embed for {ws_slug}")
    result = api_post(f"/workspace/{ws_slug}/embed/new", {
        "chat_mode": "query",
        "allowlist_domains": EMBED_ALLOWLIST,
    })

    # Try alternative endpoint if that fails
    if not result.get("embed"):
        result = api_post("/embed/new", {
            "workspaceSlug": ws_slug,
            "chat_mode": "query",
            "allowlist_domains": EMBED_ALLOWLIST,
        })

    embed = result.get("embed", {})
    uuid = embed.get("uuid", "")

    if uuid:
        ok(f"Embed UUID: {uuid}")
        return uuid
    else:
        fail(f"Embed creation failed: {result}")
        return None


def upload_rag_document(ws_slug: str, slug: str, data: dict):
    """Build and upload a RAG document to a workspace."""
    # Write the RAG doc to a temp file
    content = build_rag_document(slug, data)
    tmp_path = Path(f"/tmp/workready-rag-{slug}.md")
    tmp_path.write_text(content, encoding="utf-8")

    log(f"Uploading RAG document for {slug} ({len(content)} chars)")

    try:
        result = api_upload("/document/upload", str(tmp_path))
        if result.get("success"):
            docs = result.get("documents", [])
            if docs:
                docpath = docs[0].get("location", "")
                ok(f"Uploaded: {docpath}")

                # Assign to workspace
                embed_result = api_post(f"/workspace/{ws_slug}/update-embeddings", {
                    "adds": [docpath],
                    "deletes": [],
                })
                if embed_result.get("workspace"):
                    ok("Assigned to workspace")
                else:
                    fail(f"Assignment failed: {embed_result}")
            else:
                fail("No document path returned")
        else:
            fail(f"Upload failed: {result}")
    except Exception as e:
        fail(f"Error: {e}")
    finally:
        tmp_path.unlink(missing_ok=True)


# ============================================================================
# Main
# ============================================================================

def setup_company(slug: str):
    """Full setup for one company: workspace + embed + RAG doc."""
    company_info = COMPANIES.get(slug)
    if not company_info:
        fail(f"Unknown company: {slug}")
        return None

    print(f"\n{'=' * 60}")
    log(f"Setting up {company_info['name']} ({slug})")
    print(f"{'=' * 60}")

    # Load data
    data = load_company_data(slug)
    if not data["brief"]:
        fail(f"No brief.yaml found for {slug} in {SITES_DIR / slug}")
        return None

    # Create/update workspace
    ws = create_or_update_workspace(slug, company_info, data)
    ws_slug = ws.get("slug", company_info["workspace_name"])

    # Create embed (only for new workspaces)
    embed_uuid = create_embed(ws_slug, company_info)

    # Upload RAG document
    upload_rag_document(ws_slug, slug, data)

    return {
        "company": company_info["name"],
        "workspace_slug": ws_slug,
        "embed_uuid": embed_uuid,
        "domain": company_info["domain"],
    }


def main():
    args = sys.argv[1:]

    log("WorkReady — AnythingLLM Chatbot Setup")
    print(f"Target: {BASE_URL}")
    print(f"Sites:  {SITES_DIR}")
    print()

    if "--dry-run" in args:
        log("Dry run — generating prompts without calling AnythingLLM")
        targets = [a for a in args if a != "--dry-run"] or list(COMPANIES.keys())
        for slug in targets:
            if slug not in COMPANIES:
                continue
            data = load_company_data(slug)
            if not data["brief"]:
                fail(f"No brief.yaml for {slug}")
                continue
            prompt = build_system_prompt(slug, data)
            rag = build_rag_document(slug, data)
            print(f"\n{'=' * 60}")
            print(f"{COMPANIES[slug]['name']} ({slug})")
            print(f"{'=' * 60}")
            print(f"System prompt: {len(prompt)} chars (~{len(prompt)//4} tokens)")
            print(f"RAG document:  {len(rag)} chars (~{len(rag)//4} tokens)")
            print(f"Jobs: {len(data['jobs'])}")
            print(f"Employees: {len(data['brief'].get('employees', []))}")
            print(f"\n--- Prompt preview (first 600 chars) ---")
            print(prompt[:600])
            print("...")
        return

    # Check connectivity (skip for dry-run which already returned)
    try:
        api_get("/auth")
        ok("Connected to AnythingLLM")
    except Exception as e:
        fail(f"Cannot connect to AnythingLLM: {e}")
        sys.exit(1)

    if "--list" in args:
        list_workspaces()
        return

    if "--update-prompts" in args:
        log("Updating prompts only")
        for slug in COMPANIES:
            data = load_company_data(slug)
            if data["brief"]:
                ws_name = COMPANIES[slug]["workspace_name"]
                prompt = build_system_prompt(slug, data)
                result = api_post(f"/workspace/{ws_name}/update", {
                    "openAiPrompt": prompt,
                })
                if result.get("workspace"):
                    ok(f"{COMPANIES[slug]['name']}")
                else:
                    fail(f"{COMPANIES[slug]['name']}: {result}")
        return

    # Specific company or all
    targets = args if args else list(COMPANIES.keys())
    results = []

    for slug in targets:
        result = setup_company(slug)
        if result:
            results.append(result)
        time.sleep(1)  # rate limit courtesy

    # Summary
    if results:
        print(f"\n{'=' * 60}")
        log("EMBED UUIDS — paste into company site templates")
        print(f"{'=' * 60}")
        for r in results:
            print(f"  {r['company']}")
            print(f"    workspace: {r['workspace_slug']}")
            print(f"    domain:    {r['domain']}")
            print(f"    embed:     {r['embed_uuid'] or '(already exists — check AnythingLLM UI)'}")
            print()

        print("To embed on a company site, add this script tag:")
        print()
        print('  <script')
        print('    data-embed-id="YOUR_UUID_HERE"')
        print('    data-base-api-url="https://chat.eduserver.au/api/embed"')
        print('    src="https://chat.eduserver.au/embed/anythingllm-chat-widget.min.js">')
        print('  </script>')

    log("Done!")


if __name__ == "__main__":
    main()
