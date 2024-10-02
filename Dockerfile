# Etapa de build
FROM node:18-alpine AS builder
WORKDIR /app

COPY package.json yarn.lock ./
RUN yarn install --frozen-lockfile

COPY . .
RUN yarn build

# Etapa de produção
FROM node:18-alpine AS runner
WORKDIR /app

COPY --from=builder /app ./

CMD ["yarn", "start"]
