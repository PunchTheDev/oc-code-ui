FROM nginx:alpine

COPY index.html /usr/share/nginx/html/index.html
COPY data.json /usr/share/nginx/html/data.json

# Permissive CORS for GitHub API calls from the browser
RUN echo 'server { \
  listen 80; \
  root /usr/share/nginx/html; \
  index index.html; \
  location / { \
    add_header Cache-Control "no-cache, must-revalidate"; \
    add_header Access-Control-Allow-Origin "*"; \
    try_files $uri $uri/ /index.html; \
  } \
  location /data.json { \
    add_header Cache-Control "no-cache, must-revalidate"; \
  } \
}' > /etc/nginx/conf.d/default.conf
