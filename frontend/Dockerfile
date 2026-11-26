FROM node:22-bookworm-slim
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build && chown -R node:node /app
USER node
EXPOSE 3000
CMD ["npm", "start", "--", "-H", "0.0.0.0"]
