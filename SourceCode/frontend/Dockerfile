FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_SOP_DETECTOR_ENABLED=false
ARG VITE_SOP_DETECTOR_URL=/sop-detector
ENV VITE_SOP_DETECTOR_ENABLED=$VITE_SOP_DETECTOR_ENABLED
ENV VITE_SOP_DETECTOR_URL=$VITE_SOP_DETECTOR_URL
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY <<'EOF' /etc/nginx/conf.d/default.conf
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    # Proxy API calls to backend — no hardcoded IP needed
    location /api/ {
        proxy_pass         http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header   Host              $host;
        proxy_set_header   X-Real-IP         $remote_addr;
        proxy_set_header   X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_read_timeout 300s;
    }

    # SPA fallback
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
