# ============================================================
# WorkReady Simulation — all-in-one container
#
# The Dockerfile treats the container as a standalone machine
# and runs the same install.sh script used for bare-metal
# deployment. Zero drift between the two paths.
#
# Build:
#   docker build -t workready .
#
# Run:
#   docker run -d \
#     --name workready \
#     -p 80:80 -p 443:443 \
#     -v ./data:/opt/workready/data \
#     --env-file domains.env \
#     --env-file .env \
#     workready
# ============================================================

FROM python:3.13-slim

# System deps that install.sh needs
RUN apt-get update -qq && \
    apt-get install -y -qq --no-install-recommends \
        git ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

# Copy deploy scripts into the image
COPY install.sh start.sh Caddyfile domains.env.example /tmp/deploy/

# Run the installer — same script, same result as bare metal.
# SKIP_DEPS=0 so it installs Caddy and uv inside the image.
RUN chmod +x /tmp/deploy/install.sh /tmp/deploy/start.sh && \
    /tmp/deploy/install.sh

# The install script writes start.sh and Caddyfile into /opt/workready
RUN chmod +x /opt/workready/start.sh

# Expose HTTP (80) and HTTPS (443, for Caddy auto-TLS if desired)
EXPOSE 80 443

# Data volume for SQLite persistence
VOLUME /opt/workready/data

# Runtime
WORKDIR /opt/workready
CMD ["/opt/workready/start.sh"]
