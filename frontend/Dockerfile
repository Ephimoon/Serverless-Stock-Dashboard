ARG NODE_VERSION=22-alpine

FROM node:${NODE_VERSION} AS builder

WORKDIR /app

COPY package.json package-lock.json ./

RUN --mount=type=cache,target=/root/.npm npm ci

COPY . .

RUN npm run build

FROM node:${NODE_VERSION} AS runner

ENV NODE_ENV=production

WORKDIR /app

COPY --link --from=builder /app/dist ./dist

RUN --mount=type=cache,target=/root/.npm npm install --global serve@14.2.6

USER node

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]