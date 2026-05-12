# Icebox Production Deployment Guide

This guide outlines the steps required to deploy the Icebox Django application to a production server (such as an Ubuntu VPS on DigitalOcean, AWS EC2, or Linode) using **Gunicorn** and **Nginx**.

## Prerequisites
- A Linux Server (Ubuntu 22.04 or Debian 12 recommended)
- A domain name pointing to your server's IP address (optional but recommended for SSL)
- Python 3.10+ installed on the server

---

## 1. Initial Server Setup & Dependencies

First, update your server and install the necessary system dependencies:

```bash
sudo apt update
sudo apt install python3-pip python3-venv nginx -y
```

## 2. Clone the Application

Transfer your code to the server or clone it via Git into a designated directory (e.g., `/var/www/icebox`).

```bash
sudo mkdir -p /var/www/icebox
sudo chown -R $USER:$USER /var/www/icebox
# Clone your repository here
```

## 3. Set Up the Virtual Environment

Navigate to your project directory and create a virtual environment:

```bash
cd /var/www/icebox
python3 -m venv venv
source venv/bin/activate
```

Install the required Python packages, ensuring you include Gunicorn:

```bash
pip install -r requirements.txt
pip install gunicorn
```

## 4. Environment Variables

Because we configured `settings.py` for production, you must set your environment variables. Create a `.env` file or export these in your server environment:

```bash
export DJANGO_SECRET_KEY='your-very-long-and-secure-random-secret-key-here'
export DJANGO_DEBUG='False'
export DJANGO_ALLOWED_HOSTS='yourdomain.com,www.yourdomain.com,your_server_ip'
export DJANGO_CSRF_TRUSTED_ORIGINS='https://yourdomain.com'
```

## 5. Prepare the Database and Static Files

Run the migrations to prepare the database and collect all static files into the `staticfiles` directory so Nginx can serve them:

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

*(Optional)* Run your seed script to populate default data:
```bash
python seed_templates.py
```

## 6. Configure Gunicorn

Gunicorn acts as the application server that runs your Python code. We will create a `systemd` service file so that Gunicorn runs continuously and restarts automatically if the server reboots.

Create the service file:
```bash
sudo nano /etc/systemd/system/gunicorn.service
```

Add the following configuration (adjusting the paths and user if necessary):

```ini
[Unit]
Description=gunicorn daemon for Icebox
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/icebox
Environment="DJANGO_SECRET_KEY=your-secure-key"
Environment="DJANGO_DEBUG=False"
Environment="DJANGO_ALLOWED_HOSTS=yourdomain.com"
Environment="DJANGO_CSRF_TRUSTED_ORIGINS=https://yourdomain.com"
ExecStart=/var/www/icebox/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/icebox/icebox.sock config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Start and enable the Gunicorn service:
```bash
sudo systemctl start gunicorn
sudo systemctl enable gunicorn
```

## 7. Configure Nginx

Nginx will act as the reverse proxy, passing web traffic to Gunicorn, and directly serving your static and media files.

Create a new Nginx configuration block:
```bash
sudo nano /etc/nginx/sites-available/icebox
```

Add the following configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com your_server_ip;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    # Serve static files directly
    location /static/ {
        root /var/www/icebox;
    }

    # Serve media/uploaded files directly
    location /media/ {
        root /var/www/icebox;
    }

    # Pass all other requests to Gunicorn
    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/icebox/icebox.sock;
    }
}
```

Enable the configuration and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/icebox /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

## 8. Secure with SSL (Let's Encrypt)

If you are using a domain name, secure the application with HTTPS using Certbot:

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot will automatically modify your Nginx configuration to handle SSL and set up auto-renewal.

## 9. Final Checks

1. **Permissions**: Ensure your `/var/www/icebox/media` folder has correct permissions so the server can save uploaded files:
   ```bash
   sudo chown -R www-data:www-data /var/www/icebox/media
   sudo chmod -R 755 /var/www/icebox/media
   ```
2. Navigate to your domain or server IP in the browser. The Icebox application should load securely!
