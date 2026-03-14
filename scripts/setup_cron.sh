#!/bin/bash

# 1. Define the renewal command (Run as root)
RENEW_CMD="0 0 * * * /usr/bin/certbot renew --quiet --deploy-hook 'systemctl reload nginx' >> /var/log/certbot-renewal.log 2>&1"

# 2. Add to crontab
# This should be run with sudo to add to root's crontab
(sudo crontab -l 2>/dev/null | grep -v "certbot renew"; echo "$RENEW_CMD") | sudo crontab -

echo "✅ SSL Auto-renewal Cronjob installed in Root Crontab!"
echo "The system will check for expiry every day at 00:00."
echo "Logs will be available at /var/log/certbot-renewal.log"

# 3. Verify the installation
echo "Current Root Crontab:"
sudo crontab -l
