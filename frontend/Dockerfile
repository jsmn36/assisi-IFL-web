# syntax=docker/dockerfile:1.7
# Multi-stage Dockerfile for the React + Vite frontend.
#
# Stage 1 (builder) installs node_modules and runs `npm run build`.
# Stage 2 serves the static dist/ via nginx.
#
# Build:    docker build -f frontend/Dockerfile -t pms-frontend ./frontend
# Run:      docker run -p 8080:80 pms-frontend
#
# At build time, set VITE_API_URL via:
#   docker build --build-arg VITE_API_URL=https://api.example.com/api/v1 ...
# Vite inlines env vars at build time, so the image is environment-specific
# unless you use a runtime-templated nginx config.

# ---- Stage 1: builder ------------------------------------------------------
FROM node:20-alpine AS builder

WORKDIR /build

# Install deps with the lockfile for reproducibility.
COPY package.json package-lock.json ./
RUN --mount=type=cache,target=/root/.npm \
    npm ci --no-audit --no-fund

# Copy source after deps so dep changes don't bust the source layer cache.
COPY . ./

# VITE_* env vars are baked in at build time.
ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# ---- Stage 2: runtime (nginx) ----------------------------------------------
FROM nginx:1.27-alpine AS runtime

# Strip default config and ship our own.
RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/default.conf

# SPA assets.
COPY --from=builder /build/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://127.0.0.1/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
