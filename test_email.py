"""
Quick test script for the email notification feature.
Sends a test email through the local debug SMTP server.

Usage:
  1. In one terminal:  python -m aiosmtpd -n -l localhost:1025
  2. In another terminal: python test_email.py
"""
import os
import sys
import asyncio
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

# Setup Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
os.environ['DJANGO_EMAIL_HOST'] = 'smtp.gmail.com'
os.environ['DJANGO_EMAIL_PORT'] = '587'
os.environ['DJANGO_EMAIL_USE_TLS'] = 'True'
os.environ['DJANGO_EMAIL_HOST_USER'] = 'gabrieljohnrg01@gmail.com'  # Your sender email
# os.environ['DJANGO_EMAIL_HOST_PASSWORD'] = 'your-app-password' # We'll prompt for this below

import django
django.setup()

from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import aiosmtplib


async def send_test():
    # --- Test 1: Approved email ---
    context = {
        'deliverable_name': 'Business Model Canvas',
        'startup_name': 'TechVenture PH',
        'milestone_name': 'Milestone 1 - Ideation',
        'admin_name': 'Admin User',
        'status_label': 'Approved',
        'comment': 'Great work on the business model! Everything looks solid.',
        'action': 'done',
        'readiness_levels': [
            {'name': 'TRL', 'self_level': 'Level 3', 'admin_level': 'Level 4'},
            {'name': 'CRL', 'self_level': 'Level 3', 'admin_level': 'Level 3'},
            {'name': 'BRL', 'self_level': 'Level 4', 'admin_level': 'Level 5'},
            {'name': 'FRL', 'self_level': 'Level 2', 'admin_level': 'Level 2'},
        ],
    }
    html = render_to_string('emails/deliverable_approved.html', context)
    plain = strip_tags(html)

    msg = MIMEMultipart("alternative")
    msg["From"] = "Icebox Incubator <noreply@incubator.com>"
    msg["To"] = "gabrieljohnrg01@gmail.com"  # Sending to yourself for the test
    msg["Subject"] = "✅ Deliverable Approved: Business Model Canvas"
    msg.attach(MIMEText(plain, "plain"))
    msg.attach(MIMEText(html, "html"))

    password = os.environ.get('DJANGO_EMAIL_HOST_PASSWORD')
    await aiosmtplib.send(
        msg, 
        hostname="smtp.gmail.com", 
        port=587, 
        start_tls=True,
        username="gabrieljohnrg01@gmail.com",
        password=password
    )
    print("[OK] Approved email sent!")

    # --- Test 2: Revision email ---
    context['status_label'] = 'Revision Requested'
    context['comment'] = 'Please update the revenue projections section with Q2 data.'
    context['action'] = 'revision'
    html = render_to_string('emails/deliverable_revision.html', context)
    plain = strip_tags(html)

    msg2 = MIMEMultipart("alternative")
    msg2["From"] = "Icebox Incubator <noreply@incubator.com>"
    msg2["To"] = "gabrieljohnrg01@gmail.com"  # Sending to yourself for the test
    msg2["Subject"] = "🔄 Revision Requested: Business Model Canvas"
    msg2.attach(MIMEText(plain, "plain"))
    msg2.attach(MIMEText(html, "html"))

    await aiosmtplib.send(
        msg2, 
        hostname="smtp.gmail.com", 
        port=587, 
        start_tls=True,
        username="gabrieljohnrg01@gmail.com",
        password=password
    )
    print("[OK] Revision email sent!")

    print("\nBoth test emails sent successfully! Check your inbox (gabrieljohnrg01@gmail.com).")


if __name__ == '__main__':
    # Load the .env file you just created!
    from dotenv import load_dotenv
    load_dotenv()
    
    password = os.environ.get('DJANGO_EMAIL_HOST_PASSWORD')
    if not password:
        print("Error: Could not find DJANGO_EMAIL_HOST_PASSWORD in your .env file!")
    else:
        # Remove spaces just in case
        os.environ['DJANGO_EMAIL_HOST_PASSWORD'] = password.replace(" ", "")
        asyncio.run(send_test())
