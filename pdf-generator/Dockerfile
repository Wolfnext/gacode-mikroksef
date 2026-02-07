FROM node:22-alpine AS builder

WORKDIR /app

RUN apk add --no-cache git && corepack enable && corepack prepare pnpm@latest --activate

COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --frozen-lockfile || pnpm install

# Build the CIRFMF library (GitHub source has no pre-built dist)
# Then copy built files to package root (package.json references ./ksef-fe-invoice-converter.js)
RUN cd node_modules/@akmf/ksef-fe-invoice-converter \
    && npm install \
    && npm run build \
    && cp -r dist/* .

COPY tsconfig.json ./
COPY src/ ./src/

RUN pnpm run build

# Production stage
FROM node:22-alpine

WORKDIR /app

ENV NODE_ENV=production

# Copy everything from builder (includes built library in node_modules)
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules/ ./node_modules/
COPY --from=builder /app/dist/ ./dist/

EXPOSE 3001

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://127.0.0.1:3001/health || exit 1

CMD ["node", "dist/server.js"]
