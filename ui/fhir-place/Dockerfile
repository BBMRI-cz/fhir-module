# Build stage
FROM node:20-alpine AS builder

# Install dependencies needed for native modules
RUN apk add --no-cache g++ libc6-compat make python3

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install all dependencies (including devDependencies for build)
RUN npm ci && npm cache clean --force

# Copy source code
COPY . .

# Generate database schema and build the application
RUN npm run db:generate && \
    mkdir -p /app/data && \
    npm run db:migrate && \
    npm run db:init && \
    npm run build

# Production stage
FROM node:20-alpine AS runner

WORKDIR /app

# Install tsx for TypeScript execution
RUN npm install -g tsx

# Create a non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nextjs -u 1001

# Copy necessary files from builder stage
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static

# Copy package.json for runtime dependencies
COPY --from=builder /app/package.json ./package.json

# Copy database migration files and scripts
COPY --from=builder /app/drizzle ./drizzle
COPY --from=builder /app/src/scripts ./src/scripts
COPY --from=builder /app/src/lib ./src/lib

# Copy startup script
COPY start.sh /app/start.sh

# Create data directory and set permissions
RUN mkdir -p /app/data && \
    chown -R nextjs:nodejs /app && \
    chmod +x /app/start.sh
USER nextjs

# Expose port
EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Start the application with database initialization
CMD ["/app/start.sh"] 