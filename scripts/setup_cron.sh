#!/bin/bash

# 1. Define the renewal command
# --quiet means it only outputs if there is an error
# --deploy-hook restarts nginx only if a new certificate was actually obtained
RENEW_CMD="0 0 * * * /usr/bin/certbot renew --quiet --deploy-hook 'systemctl reload nginx' >> /var/log/certbot-renewal.log 2>&1"

# 2. Add to crontab if not already there
(crontab -l 2>/dev/null | grep -v "certbot renew"; echo "$RENEW_CMD") | crontab -

echo "✅ SSL Auto-renewal Cronjob installed!"
echo "The system will check for expiry every day at 00:00."
echo "Logs will be available at /var/log/certbot-renewal.log"

# 3. Verify the installation
echo "Current Crontab:"
crontab -l
