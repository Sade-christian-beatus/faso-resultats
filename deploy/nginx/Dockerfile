# Production web server: static pages + reverse proxy to the API + HTTPS.
# Built from the repository root: docker compose -f docker-compose.prod.yml build web
FROM nginx:alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY deploy/nginx/snippets/ /etc/nginx/snippets/
COPY deploy/nginx/templates/ /etc/nginx/templates/
COPY frontend/public/ /usr/share/nginx/html/
