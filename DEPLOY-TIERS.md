# Deployment recipes and their status

[Project home](README.md) · [Operations](docs/operations.md) · [Configuration](docs/configuration.md)

The original three-tier document mixed proposed features with working deployment instructions. Its [archived proposal](docs/archive/deployment-tiers-proposal.md) remains available for history. This page describes the 0.3.0 baseline reviewed on 14 September 2026.

## Current deployment

GitHub Pages serves the static sites. The VPS runs the `workready-api` service behind shared Caddy, with SQLite and attachments on a durable volume. Routine updates pull the GitHub-built public `ghcr.io/michael-borck/workready` image and recreate the API service. Follow [operations](docs/operations.md#update-the-existing-vps).

## Alternative all-in-one recipe

The root `docker-compose.yml` starts a service named `workready` with bundled Caddy and static sites. It binds ports 80/443 and uses virtual-host configuration. Domain settings, client API URLs, CSP and CORS need to match the chosen deployment.

This recipe is not the active shared-VPS Compose project. Do not run it on ports already owned by shared Caddy. The old promise that `docker compose up -d` provides a complete path-routed localhost demo was not implemented.

## Optional model and hiring-desk configuration

- `LLM_PROVIDER=stub` is the main API's deliberate no-model mode. Select and configure Ollama, Anthropic or OpenRouter for model-backed replies.
- Changed Compose environment settings require container recreation. A plain `docker compose restart` does not apply them.
- AnythingLLM hiring desks use a separate service and build-time embed configuration. They are not controlled by the API provider setting and are excluded from sensitive application/staff pages.
- The proposed builtin keyword chatbot and automatic path-mode frontend configuration do not exist in this baseline.

There is no verified capacity tier for 1,000 or more students. Test the chosen API/model/proxy setup against the intended cohort. See [architecture](docs/architecture.md#limits-and-extension-points) and [privacy](docs/privacy.md).
