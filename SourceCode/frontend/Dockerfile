FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
ARG VITE_API_BASE_URL=http://localhost:8000/api/v1
ARG VITE_API_KEY=
# The SOP detector (SOP-detector/) is off unless VITE_SOP_DETECTOR_ENABLED=true;
# VITE_SOP_DETECTOR_URL is where it answers when switched on
ARG VITE_SOP_DETECTOR_ENABLED=false
ARG VITE_SOP_DETECTOR_URL=/sop-detector
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_API_KEY=$VITE_API_KEY
ENV VITE_SOP_DETECTOR_ENABLED=$VITE_SOP_DETECTOR_ENABLED
ENV VITE_SOP_DETECTOR_URL=$VITE_SOP_DETECTOR_URL
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY <<'EOF' /etc/nginx/conf.d/default.conf
server {
    listen 5173;
    root /usr/share/nginx/html;
    index index.html;
    location / {
        try_files $uri $uri/ /index.html;
    }
}
EOF
EXPOSE 5173
CMD ["nginx", "-g", "daemon off;"]
