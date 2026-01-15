
# ================================
#          ASSETS BUILDER
# ================================

FROM node:22-alpine AS assets-builder

WORKDIR /app

COPY package.json package-lock.json .
RUN npm ci && npm cache clean --force

COPY postcss.config.js tsconfig.json eslint.config.js .
COPY scripts ./scripts
COPY ./src/app/frontend/assets ./src/app/frontend/assets
COPY ./src/app/frontend/templates ./src/app/frontend/templates

RUN npm run build:all && rm -rf node_modules

# ================================
#           MAIN BUILDER
# ================================

FROM python:3.12-alpine

LABEL version="1.0"
LABEL description="Simple infrastructure status page"

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    rm requirements.txt

COPY --chmod=755 entrypoint.sh .

COPY --chown=appuser:appgroup src/ .

COPY --from=assets-builder --chown=appuser:appgroup \
    /app/src/app/frontend/static/ ./app/frontend/static/

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://127.0.0.1:5000/health || exit 1

ENTRYPOINT ["./entrypoint.sh"]
