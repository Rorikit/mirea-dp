FROM node:24-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS runtime
RUN sed -i 's#/run/nginx.pid#/tmp/nginx.pid#' /etc/nginx/nginx.conf \
    && chown -R nginx:nginx /var/cache/nginx /var/run /etc/nginx/conf.d /usr/share/nginx/html
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
USER nginx
EXPOSE 8080
HEALTHCHECK --interval=10s --timeout=3s --retries=5 CMD wget -q -O - http://127.0.0.1:8080/ >/dev/null || exit 1
ENTRYPOINT []
CMD ["nginx", "-g", "daemon off;"]
