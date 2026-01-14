
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


ENTRYPOINT ["./entrypoint.sh"]
