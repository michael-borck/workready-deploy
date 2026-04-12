#!/usr/bin/env bash
# ============================================================
# WorkReady Simulation — single-machine installer
#
# This script is the single source of truth for "how does WorkReady
# run on a machine." It works identically when:
#   1. Piped from curl on a bare-metal VPS / VM
#   2. RUN inside a Dockerfile during docker build
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/.../install.sh | bash
#   # or
#   ./install.sh
#
# Environment variables (all optional):
#   WORKREADY_DIR    — install root (default: /opt/workready)
#   GITHUB_ORG       — GitHub org/user to clone from (default: michael-borck)
#   SKIP_DEPS        — set to 1 to skip system dependency installation
#   SKIP_CLONE       — set to 1 if repos are already in $WORKREADY_DIR
# ============================================================

set -euo pipefail

WORKREADY_DIR="${WORKREADY_DIR:-/opt/workready}"
GITHUB_ORG="${GITHUB_ORG:-michael-borck}"
SKIP_DEPS="${SKIP_DEPS:-0}"
SKIP_CLONE="${SKIP_CLONE:-0}"

# The 9 repos that make up the simulation
COMPANY_SITES=(
    ironvale-resources
    nexuspoint-systems
    horizon-foundation
    southern-cross-financial
    metro-council-wa
    meridian-advisory
)
PLATFORM_REPOS=(
    workready-api
    workready-portal
    workready-jobs
)
ALL_REPOS=("${COMPANY_SITES[@]}" "${PLATFORM_REPOS[@]}")

# Colours for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${CYAN}[workready]${NC} $*"; }
ok()    { echo -e "${GREEN}[workready]${NC} ✓ $*"; }
warn()  { echo -e "${YELLOW}[workready]${NC} ⚠ $*"; }
fail()  { echo -e "${RED}[workready]${NC} ✗ $*" >&2; exit 1; }

# ============================================================
# 1. System dependencies
# ============================================================

install_caddy() {
    if command -v caddy &>/dev/null; then
        ok "Caddy already installed: $(caddy version 2>/dev/null || echo 'unknown')"
        return
    fi

    info "Installing Caddy..."
    local arch
    arch="$(uname -m)"
    case "$arch" in
        x86_64)  arch="amd64" ;;
        aarch64|arm64) arch="arm64" ;;
        *) fail "Unsupported architecture: $arch" ;;
    esac

    local os
    os="$(uname -s | tr '[:upper:]' '[:lower:]')"

    curl -fsSL "https://caddyserver.com/api/download?os=${os}&arch=${arch}" \
        -o /usr/local/bin/caddy
    chmod +x /usr/local/bin/caddy
    ok "Caddy installed: $(caddy version 2>/dev/null || echo 'ok')"
}

install_uv() {
    if command -v uv &>/dev/null; then
        ok "uv already installed: $(uv --version 2>/dev/null || echo 'unknown')"
        return
    fi

    info "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    # Make uv available in the current shell
    export PATH="$HOME/.local/bin:$PATH"
    ok "uv installed: $(uv --version 2>/dev/null || echo 'ok')"
}

install_system_deps() {
    if [ "$SKIP_DEPS" = "1" ]; then
        info "Skipping system dependency installation (SKIP_DEPS=1)"
        return
    fi

    info "Checking system dependencies..."

    # Git
    if ! command -v git &>/dev/null; then
        if command -v apt-get &>/dev/null; then
            apt-get update -qq && apt-get install -y -qq --no-install-recommends git ca-certificates curl
        elif command -v brew &>/dev/null; then
            brew install git
        else
            fail "git is required but not installed, and no package manager found"
        fi
    fi
    ok "git: $(git --version)"

    # Python 3.11+
    if ! command -v python3 &>/dev/null; then
        fail "Python 3 is required but not found. Install Python 3.11+ first."
    fi
    ok "python3: $(python3 --version)"

    install_caddy
    install_uv
}

# ============================================================
# 2. Clone or update repos
# ============================================================

fetch_repos() {
    if [ "$SKIP_CLONE" = "1" ]; then
        info "Skipping clone (SKIP_CLONE=1) — assuming repos are in $WORKREADY_DIR"
        return
    fi

    mkdir -p "$WORKREADY_DIR"
    info "Fetching ${#ALL_REPOS[@]} repos into $WORKREADY_DIR..."

    for repo in "${ALL_REPOS[@]}"; do
        local target="$WORKREADY_DIR/$repo"
        if [ -d "$target/.git" ]; then
            info "  Updating $repo..."
            git -C "$target" pull --ff-only --quiet 2>/dev/null || warn "  Could not fast-forward $repo — skipping"
        else
            info "  Cloning $repo..."
            git clone --depth 1 --quiet \
                "https://github.com/$GITHUB_ORG/$repo.git" "$target"
        fi
    done
    ok "All repos fetched"
}

# ============================================================
# 3. Build company sites
# ============================================================

build_sites() {
    info "Building ${#COMPANY_SITES[@]} company sites..."

    # Ensure uv is on PATH (may have been installed to ~/.local/bin)
    export PATH="$HOME/.local/bin:$PATH"

    for site in "${COMPANY_SITES[@]}"; do
        local build_script="$WORKREADY_DIR/$site/site/build.py"
        if [ -x "$build_script" ]; then
            info "  Building $site..."
            (cd "$WORKREADY_DIR/$site" && "$build_script") || warn "  Build failed for $site"
        elif [ -f "$build_script" ]; then
            info "  Building $site (via uv run)..."
            (cd "$WORKREADY_DIR/$site" && uv run --quiet --with pyyaml --with jinja2 --with markdown python3 site/build.py) || warn "  Build failed for $site"
        else
            warn "  No build script found for $site — using existing dist/ if present"
        fi
    done

    # Build seek.jobs
    local seek_build="$WORKREADY_DIR/workready-jobs/build.py"
    if [ -f "$seek_build" ]; then
        info "  Building workready-jobs..."
        (cd "$WORKREADY_DIR/workready-jobs" && python3 build.py)
    fi

    ok "All sites built"
}

# ============================================================
# 4. Install API dependencies
# ============================================================

install_api_deps() {
    info "Installing workready-api dependencies..."
    export PATH="$HOME/.local/bin:$PATH"

    local api_dir="$WORKREADY_DIR/workready-api"
    if [ -f "$api_dir/pyproject.toml" ]; then
        (cd "$api_dir" && uv sync --frozen --quiet 2>/dev/null || uv sync --quiet)
        ok "API dependencies installed"
    else
        warn "No pyproject.toml found in workready-api — skipping"
    fi
}

# ============================================================
# 5. Write runtime config
# ============================================================

write_config() {
    info "Writing runtime configuration..."

    # Copy start script
    local deploy_dir
    deploy_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

    cp "$deploy_dir/start.sh" "$WORKREADY_DIR/start.sh" 2>/dev/null || true
    chmod +x "$WORKREADY_DIR/start.sh" 2>/dev/null || true

    cp "$deploy_dir/Caddyfile" "$WORKREADY_DIR/Caddyfile" 2>/dev/null || true

    # Create .env if it doesn't exist
    if [ ! -f "$WORKREADY_DIR/.env" ]; then
        if [ -f "$WORKREADY_DIR/workready-api/.env.example" ]; then
            cp "$WORKREADY_DIR/workready-api/.env.example" "$WORKREADY_DIR/.env"
            info "  Created .env from .env.example — edit it with your API keys"
        fi
    fi

    # Create domains.env if it doesn't exist
    if [ ! -f "$WORKREADY_DIR/domains.env" ]; then
        if [ -f "$deploy_dir/domains.env.example" ]; then
            cp "$deploy_dir/domains.env.example" "$WORKREADY_DIR/domains.env"
            info "  Created domains.env — edit it with your domain names"
        fi
    fi

    # Create data directory for SQLite
    mkdir -p "$WORKREADY_DIR/data"

    ok "Configuration written to $WORKREADY_DIR"
}

# ============================================================
# Main
# ============================================================

main() {
    echo ""
    echo "  ╔══════════════════════════════════════════════╗"
    echo "  ║  WorkReady Simulation Installer              ║"
    echo "  ║  9 repos · 6 company sites · 1 machine      ║"
    echo "  ╚══════════════════════════════════════════════╝"
    echo ""

    mkdir -p "$WORKREADY_DIR"

    install_system_deps
    fetch_repos
    build_sites
    install_api_deps
    write_config

    echo ""
    ok "Installation complete!"
    echo ""
    info "Next steps:"
    echo "  1. Edit $WORKREADY_DIR/domains.env with your domain names"
    echo "  2. Edit $WORKREADY_DIR/.env with your API keys (LLM provider, admin token)"
    echo "  3. Point your 9 DNS records at this machine's IP"
    echo "  4. Start the simulation:"
    echo ""
    echo "     $WORKREADY_DIR/start.sh"
    echo ""
    echo "  Or with Docker:"
    echo ""
    echo "     docker compose up -d"
    echo ""
}

main "$@"
