FROM node:20-alpine
WORKDIR /usr/src/app
COPY package.json package-lock.json* ./
RUN npm ci || npm i
COPY . .
EXPOSE 8080
CMD ["npm","run","dev"]
