FROM node:22-alpine

WORKDIR /app

RUN apk add --no-cache docker-cli

COPY package*.json ./

RUN npm ci

COPY . .

CMD ["npx", "cdk", "--version"]