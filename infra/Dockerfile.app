FROM node:22.14.0-alpine AS base
WORKDIR /app
RUN apk add --no-cache libc6-compat && \
    addgroup -S appgroup && adduser -S appuser -G appgroup
USER appuser

FROM base AS dev
WORKDIR /app
EXPOSE 3000
CMD ["npm", "run", "dev"]
