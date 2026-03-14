#!/bin/bash

# 1. Update and install Nginx + Certbot
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx

# 2. Define Domain
DOMAIN="thaiedit.com"

# 3. Create Nginx Configuration
NGINX_CONF="/etc/nginx/sites-available/thaiedit"

sudo bash -c "cat > $NGINX_CONF" <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # Redirect all HTTP traffic to HTTPS
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name $DOMAIN www.$DOMAIN;

    # Increase upload size for PDFs and Images
    client_max_body_size 50M;

    # MIME types
    include /etc/nginx/mime.types;

    # SSL Certificate Paths (Managed by Certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    # Modern SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers HIGH:!aNULL:!MD5;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Cloudflare specific: Get the real user IP
        proxy_set_header CF-Connecting-IP \$http_cf_connecting_ip;
    }

    # Static files caching
    location /static/ {
        alias /home/ubuntu/servicehub-suite/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
}
EOF

# 4. Enable configuration and restart Nginx
sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t && sudo systemctl restart nginx

# 5. Open Firewall ports
sudo ufw allow 'Nginx Full'

echo "--------------------------------------------------------"
echo "✅ Nginx Reverse Proxy with HTTPS Redirect Setup Complete!"
echo "--------------------------------------------------------"
echo "NOTE: If you haven't run Certbot yet, the Nginx restart might fail."
echo "Run: sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo "--------------------------------------------------------"
