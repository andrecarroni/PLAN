# syntax=docker/dockerfile:1
FROM node:24-bookworm-slim AS ui
WORKDIR /build
COPY frontend/package*.json ./
RUN --mount=type=secret,id=proxy_ca \
    if [ -f /run/secrets/proxy_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/proxy_ca; fi; \
    npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 FRONTEND_DIST=/app/frontend/dist LOGO_PATH=/app/frontend/dist/logo.png
WORKDIR /app/backend
COPY backend/requirements.lock .
RUN --mount=type=secret,id=ca_bundle \
    if [ -f /run/secrets/ca_bundle ]; then export PIP_CERT=/run/secrets/ca_bundle; fi; \
    pip install --no-cache-dir -r requirements.lock
COPY backend/ ./
COPY --from=ui /build/dist /app/frontend/dist
RUN useradd --uid 10001 --create-home p4 && chown -R p4:p4 /app
USER p4
EXPOSE 8000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--no-proxy-headers"]
