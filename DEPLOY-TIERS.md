# WorkReady Deployment Tiers

Three deployment tiers, each building on the previous. The simulation
works at every tier — each step adds capability, nothing breaks if
you stop early.

## Tier 1 — Demo (zero config)

```bash
docker compose up -d
# Open http://localhost
```

**What works:**
- Portal, seek.jobs, all 6 company sites — served via path-based routing
  on a single port, no DNS needed
- Builtin keyword chatbot on career pages (no AnythingLLM)
- Apply forms on company sites and seek.jobs Quick Apply
- In-app email (compose, reply, bounce, sent box)
- Interview system with stub LLM (canned responses)
- Resume assessment with stub LLM (deterministic pass/fail)
- Full state machine (NOT_APPLIED → APPLIED → HIRED → COMPLETED)
- Admin page for testing

**Requires:** Docker. Nothing else.

**Audience:** "Let me see what this is" — lecturers evaluating WorkReady,
students in a tutorial, quick demos.

**Pre-built image:** YES — ships on GHCR with builtin chatbots and stub LLM.

## Tier 2 — Standard (add real LLM)

```bash
docker compose up -d
# Edit .env:
#   LLM_PROVIDER=anthropic
#   ANTHROPIC_API_KEY=sk-ant-...
docker compose restart
```

**What it adds over Demo:**
- Real LLM-powered resume assessment (genuine feedback on student CVs)
- Real LLM-powered interviews (character-voiced, ~10 turns)
- Real LLM-powered email replies (Karen remembers the conversation)
- Thread-aware context stuffing with summarisation guardrail

**Requires:** Docker + an LLM API key (Anthropic, OpenRouter, or Ollama).

**Audience:** "Running this for my class" — the main use case.

**Pre-built image:** YES — same GHCR image as Demo, just add the API key.

## Tier 3 — Full (add AnythingLLM + custom domains)

```bash
# 1. Set up AnythingLLM somewhere (chat.example.com)
# 2. Configure
cp domains.env.example domains.env   # 9 custom domains
echo "ANYTHINGLLM_API_KEY=..." >> .env

# 3. Create chatbot workspaces
python3 setup-chatbots.py

# 4. Build with everything baked in
docker compose build && docker compose up -d
```

**What it adds over Standard:**
- AnythingLLM-powered chatbots on career pages (RAG over company docs)
- Custom domains (ironvaleresources.example.com, etc.)
- Auto-TLS via Caddy/Let's Encrypt
- Each company site feels like a real employer at its own URL

**Requires:** Docker + LLM API key + AnythingLLM instance + 9 DNS records.

**Audience:** "Production deployment for 1000+ students" — the full experience.

**Pre-built image:** NO — requires local build because AnythingLLM embed
UUIDs are baked into the site templates at build time.

---

## Implementation TODO

### For Demo tier (path-based standalone mode):
- [ ] Convert all template paths from absolute to relative + add `<base href="{{ base_url }}">`
- [ ] Update all 6 `build.py` scripts to accept `BASE_URL` env var (default `/`)
- [ ] Add standalone Caddyfile mode (path-based routing when no domains.env)
- [ ] Update portal `config.js` to auto-detect standalone mode
- [ ] Update seek.jobs `config.js` to auto-detect standalone mode
- [ ] Build the builtin keyword chatbot (`chatbot-builtin.js`)
- [ ] Update `install.sh` to pass `BASE_URL` during site builds
- [ ] Update `docker-compose.yml` for standalone defaults

### For Full tier (AnythingLLM integration):
- [ ] Update `setup-chatbots.py` to write `chatbot-embeds.json`
- [ ] Update `build.py` scripts to read chatbot config at build time
- [ ] Add `chatbot-loader.js` or conditional template rendering
- [ ] Add `<base href>` to all templates (shared with Demo tier)

### Builtin keyword chatbot:
- [ ] `chatbot-builtin.js` — small chat bubble, bottom-right corner
- [ ] FAQ list compiled from company job data at build time
- [ ] Handles: "what roles are open?", "tell me about the company",
  "how do I apply?", "what's the salary?", catch-all with email pointer
- [ ] ~100 lines JS, no external dependencies, works offline
