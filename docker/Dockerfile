# ── Semantic Cache Engine Demo Image ─────────────────────────────────────────
#
# Multi-stage build:
#   Stage 1 (builder) — Cython-compiles core IP modules to .so extensions
#   Stage 2 (runtime) — clean image with no readable source for core modules
#
# Usage:
#   docker build -t ghcr.io/leangridlabs/semantic-cache-engine-demo:latest .
#   docker run -it ghcr.io/leangridlabs/semantic-cache-engine-demo:latest
# ─────────────────────────────────────────────────────────────────────────────

# ─── Stage 1: Cython compiler ────────────────────────────────────────────────
FROM python:3.11-slim AS builder

ARG RELEASE_VERSION=0.1.0

# gcc + libc6-dev required for Cython; Python.h is already at
# /usr/local/include/python3.11/ in the python:3.11-slim base image.
RUN apt-get update \
 && apt-get install -y --no-install-recommends gcc libc6-dev \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "Cython>=3.0"

WORKDIR /build
COPY wheels/ /build/wheels/
COPY cython_build/ /build/cython_build/

RUN python /build/cython_build/build.py \
      /build/wheels/semantic_cache_engine-${RELEASE_VERSION}-py3-none-any.whl \
      /build/dist

# ─── Stage 2: runtime ────────────────────────────────────────────────────────
FROM python:3.11-slim

ARG  RELEASE_VERSION=0.1.0
ENV  RELEASE_VERSION=${RELEASE_VERSION}

# ── system dependencies ───────────────────────────────────────────────────────
RUN apt-get update \
 && apt-get install -y --no-install-recommends git \
 && rm -rf /var/lib/apt/lists/*

# ── install runtime dependencies via the original wheel, then replace ─────────
# pip resolves and installs all Requires-Dist from the wheel metadata.
# We then remove the plain-Python package and overlay the Cython-compiled one.
COPY wheels/ /tmp/wheels/
RUN pip install --no-cache-dir /tmp/wheels/semantic_cache_engine-${RELEASE_VERSION}-py3-none-any.whl \
 && rm -rf /tmp/wheels \
 && rm -rf /usr/local/lib/python3.11/site-packages/semantic_cache_engine/

# ── install compiled package from builder ─────────────────────────────────────
COPY --from=builder /build/dist/semantic_cache_engine/ \
                    /usr/local/lib/python3.11/site-packages/semantic_cache_engine/

# ── clone Flask 3.0.3 into both workspace slots ───────────────────────────────
RUN git clone --depth 1 --branch 3.0.3 \
      https://github.com/pallets/flask.git \
      /workspace/session-a/flask \
 && git clone --depth 1 --branch 3.0.3 \
      https://github.com/pallets/flask.git \
      /workspace/session-b/flask

# ── copy demo script ──────────────────────────────────────────────────────────
COPY demo/ /app/demo/

# ── activate bundle encryption ────────────────────────────────────────────────
ENV SEMANTIC_BUNDLE_ENCRYPT=true

# ── working directory ─────────────────────────────────────────────────────────
WORKDIR /workspace

# ── entrypoint ────────────────────────────────────────────────────────────────
ENTRYPOINT ["python", "/app/demo/demo.py"]
