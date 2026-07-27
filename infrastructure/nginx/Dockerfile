FROM nginx:1.27-alpine
RUN chown -R nginx:nginx /var/cache/nginx /var/run /etc/nginx/conf.d
USER nginx
EXPOSE 8080 8443
ENTRYPOINT []
CMD ["nginx", "-g", "daemon off;"]
