#!/bin/bash

# 1. Update and install dependencies
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv git

# 2. Setup project directory (adjust path if needed)
PROJECT_DIR="/home/ubuntu/servicehub-suite"
if [ ! -d "$PROJECT_DIR" ]; then
    git clone https://github.com/kcommerce/servicehub-suite.git $PROJECT_DIR
fi

cd $PROJECT_DIR

# 3. Setup Virtual Environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Create Systemd Service File
SERVICE_FILE="/etc/systemd/system/thaiedit.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOF
[Unit]
Description=ThaiEdit Pro FastAPI Service
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# 5. Start and Enable Service
sudo systemctl daemon-reload
sudo systemctl enable thaiedit
sudo systemctl start thaiedit

echo "✅ Server Setup Complete! Service is running."
sudo systemctl status thaiedit --no-pager
