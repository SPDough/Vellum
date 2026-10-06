# =============================================================================
# Otomeshon Frontend Dockerfile - Vite Multi-Stage Production Build
# =============================================================================
#
# This Dockerfile creates a production-ready container for the Otomeshon
# frontend (Vite + React + MUI SPA). It uses a multi-stage build approach to
# optimize image size, security, and performance while supporting both
# development and production workflows.
#
# Build Stages:
# 1. Base: Common dependencies and system setup
# 2. Development: Hot-reload development environment (Vite dev server)
# 3. Build: Vite static production build
# 4. Production: Minimal runtime environment serving the static build
#
# Usage:
#   Development: docker build --target development -t otomeshon-frontend:dev .
#   Production:  docker build --target production -t otomeshon-frontend:prod .
# =============================================================================

FROM node:20-alpine as base

WORKDIR /app

RUN apk add --no-cache curl bash git

# =============================================================================
# DEVELOPMENT STAGE - Optimized for development workflow
# =============================================================================
FROM base as development

COPY package*.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# =============================================================================
# BUILD STAGE - Vite application compilation
# =============================================================================
FROM base as build

COPY package*.json ./
RUN npm ci

COPY . .

RUN npm run build

# =============================================================================
# PRODUCTION STAGE - Minimal static-serving runtime
# =============================================================================
FROM node:20-alpine as production

WORKDIR /app

RUN apk add --no-cache curl && npm install -g serve

COPY --from=build /app/dist ./dist

RUN addgroup -g 1001 -S vite && \
    adduser -S vite -u 1001 && \
    chown -R vite:vite /app

USER vite

HEALTHCHECK --interval=30s \
    --timeout=30s \
    --start-period=5s \
    --retries=3 \
    CMD curl -f http://localhost:3000/ || exit 1

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
