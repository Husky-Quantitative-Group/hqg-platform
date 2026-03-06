# Nginx Setup

The school of business reverse proxy forwards requests from our platform domain to our server.

This Nginx config forwards HTTP/HTTPS traffic to the `hqg-platform` container for service routing.

**Config location:** `/etc/nginx/sites-enabled/default`

```nginx
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8080;
    }
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name _;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8080;
    }
}
```

**Notes:**
- TLS certificates are managed via [Let's Encrypt](https://letsencrypt.org/). Replace `your-domain.com` with your actual domain.
- Both HTTP and HTTPS traffic proxy to the `hqg-platform` container on port `8080`.