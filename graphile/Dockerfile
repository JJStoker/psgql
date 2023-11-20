FROM node:21.2.0-bookworm-slim

WORKDIR /data/app/

COPY package.json ./
COPY yarn.lock ./

RUN yarn install

COPY . .

EXPOSE 3000

CMD [ "node", "server.js" ]
