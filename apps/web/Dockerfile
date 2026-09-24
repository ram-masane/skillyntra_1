FROM node:20-alpine

WORKDIR /app
COPY apps/web/package*.json ./
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
RUN npm ci
COPY apps/web ./
RUN npm run build
EXPOSE 3000
CMD ["npm", "run", "start", "--", "-p", "3000"]
