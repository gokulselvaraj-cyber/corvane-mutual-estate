FROM node:20-alpine
WORKDIR /app
COPY package.json ./
RUN npm install --omit=dev
COPY dist ./dist
COPY src/templates ./dist/templates
USER node
EXPOSE 8070
CMD ["node", "dist/index.js"]
