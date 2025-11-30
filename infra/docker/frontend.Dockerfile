###############################################
# 1. Base Builder Image
###############################################
FROM node:20-alpine AS builder

WORKDIR /app

# Install OS packages needed for build
RUN apk add --no-cache libc6-compat

# Copy ONLY package files first for caching
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy frontend source
COPY frontend/ ./

# Build Next.js (creates .next/)
RUN npm run build


###############################################
# 2. Production Runtime Image
###############################################
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Install only production deps
COPY frontend/package.json ./
COPY --from=builder /app/node_modules ./node_modules

# Copy built assets
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Next.js server requires this
COPY --from=builder /app/next.config.mjs ./

# Expose port
EXPOSE 3000

# Healthcheck (optional)
HEALTHCHECK --interval=30s --timeout=5s --retries=3 CMD \
  wget -qO- http://localhost:3000 || exit 1

# Start the Next.js server
CMD ["npm", "start"]
