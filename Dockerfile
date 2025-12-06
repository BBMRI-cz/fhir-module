# ============================================
# Node.js Build Stage
# ============================================
FROM node:20-alpine AS node-builder

RUN apk add --no-cache g++ libc6-compat make python3

WORKDIR /app

COPY ui/fhir-place/package*.json ./
RUN npm ci && npm cache clean --force

COPY ui/fhir-place/. .

RUN npm run db:generate && \
    mkdir -p /app/data && \
    npm run build

# ============================================
# Final Combined Stage
# ============================================
FROM node:20-alpine

# Install Python, bash, and supervisor
RUN apk add --no-cache bash curl py3-pip python3 supervisor && \
    addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001 && \
    npm install -g tsx

# ============================================
# Setup Python App
# ============================================
ENV APP_DIR="/opt/fhir-module"

WORKDIR $APP_DIR

COPY --chown=1001:1001 requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn --break-system-packages

COPY --chown=1001:1001 . .

# ============================================
# Setup Node.js App
# ============================================
WORKDIR /app

COPY --from=node-builder --chown=1001:1001 /app/public ./public
COPY --from=node-builder --chown=1001:1001 /app/.next/standalone ./
COPY --from=node-builder --chown=1001:1001 /app/.next/static ./.next/static
COPY --from=node-builder --chown=1001:1001 /app/drizzle ./drizzle

# ============================================
# Create log directory and config snapshots
# ============================================
RUN mkdir -p /var/log/fhir-module && \
    mkdir -p /var/log/supervisor && \
    mkdir -p /app/data && \
    mkdir -p /opt/config-snapshots && \
    mkdir -p /tmp/prometheus_multiproc && \
    chown -R 1001:1001 /var/log/fhir-module /app /opt/config-snapshots /opt/fhir-module && \
    chown -R 1001:1001 /var/log/supervisor && \
    chown -R 1001:1001 /tmp/prometheus_multiproc && \
    chmod 775 /opt/config-snapshots


COPY --chown=1001:1001 supervisord.conf /etc/supervisor/conf.d/supervisord.conf
COPY --chown=1001:1001 --chmod=755 startup.sh /usr/local/bin/startup.sh

# ============================================
# Runtime
# ============================================
EXPOSE 3000 5000 8080

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

WORKDIR $APP_DIR

CMD ["/usr/local/bin/startup.sh"]