# RAGNAR Ω OMNI v33.0 — production image (full stack, SPOF-filtered)
# Layer 1: builder (compile deps, discarded) · Layer 2: runtime (non-root, minimal)
FROM python:3.12-slim AS builder
WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir --prefix=/opt/deps ".[api]"

FROM python:3.12-slim AS runtime
LABEL org.opencontainers.image.title="ragnar-omni" \
      org.opencontainers.image.description="Asymmetric, zero-trust, game-theoretic legal defense engine" \
      org.opencontainers.image.licenses="MIT"

# non-root, no shell for the app user
RUN useradd --system --uid 900 --no-create-home --shell /usr/sbin/nologin ragnar
COPY --from=builder /opt/deps /usr/local
WORKDIR /app
USER ragnar

# Secrets are injected at runtime (env), NEVER baked: fail-closed by design.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status==200 else 1)"

CMD ["uvicorn", "ragnar.api:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
