#!/bin/bash

# 1. Update and install Nginx + Certbot
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx

# 2. Define Domain (Change this to your actual domain)
DOMAIN="thaiedit.com"

# 3. Create Nginx Configuration
NGINX_CONF="/etc/nginx/sites-available/thaiedit"

sudo bash -c "cat > $NGINX_CONF" <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;

    # Increase upload size for PDFs and Images
    client_max_body_size 50M;

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
echo "✅ Nginx Reverse Proxy Setup Complete!"
echo "--------------------------------------------------------"
echo "STEP 6 (Manual): To activate SSL (HTTPS), run the following command:"
echo "sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo "--------------------------------------------------------"
