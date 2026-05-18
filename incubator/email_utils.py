"""
Email notification utilities for the Incubator system.
Uses aiosmtplib for lightweight SMTP email delivery.
Sends emails to incubatees when admins approve or request revision on deliverables.
"""
import asyncio
import logging
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

import aiosmtplib
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings

logger = logging.getLogger(__name__)


async def _send_email_async(subject, plain_body, html_body, recipients):
    """
    Send an email via aiosmtplib using SMTP settings from Django settings.
    """
    msg = MIMEMultipart("alternative")
    msg["From"] = settings.DEFAULT_FROM_EMAIL
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    await aiosmtplib.send(
        msg,
        hostname=settings.EMAIL_HOST,
        port=settings.EMAIL_PORT,
        username=settings.EMAIL_HOST_USER or None,
        password=settings.EMAIL_HOST_PASSWORD or None,
        start_tls=settings.EMAIL_USE_TLS,
    )


def send_deliverable_status_email(deliverable, action, admin_user, comment=None):
    """
    Send an email notification to all startup members when an admin
    approves or requests revision on a deliverable.

    Args:
        deliverable: The Deliverable instance
        action: 'done' (approved) or 'revision' (revision requested)
        admin_user: The admin User who performed the action
        comment: Optional comment text from the admin
    """
    # Skip if SMTP is not configured (no host user set)
    if not settings.EMAIL_HOST_USER:
        logger.info("Email sending skipped — EMAIL_HOST_USER not configured.")
        return

    startup = deliverable.milestone.startup
    milestone = deliverable.milestone

    # Collect all incubatee recipients (members + owner)
    recipients = set()
    for member in startup.members.all():
        # Ensure we only add users who are incubatees
        if member.email and member.role == 'incubatee':
            recipients.add(member.email)
            
    if startup.owner and startup.owner.email and startup.owner.role == 'incubatee':
        recipients.add(startup.owner.email)

    # Explicitly remove the admin who is taking the action (just in case)
    if admin_user and admin_user.email in recipients:
        recipients.remove(admin_user.email)

    if not recipients:
        logger.warning(
            f"No email recipients found for startup '{startup.name}' "
            f"deliverable '{deliverable.name}'"
        )
        return

    # Determine email subject and template based on action
    if action == 'done':
        subject = f"✅ Deliverable Approved: {deliverable.name}"
        template_name = 'emails/deliverable_approved.html'
        status_label = 'Approved'
    elif action == 'revision':
        subject = f"🔄 Revision Requested: {deliverable.name}"
        template_name = 'emails/deliverable_revision.html'
        status_label = 'Revision Requested'
    else:
        logger.error(f"Unknown action: {action}")
        return

    milestone_label = milestone.title or f"Milestone {milestone.milestone_progress}"

    # Gather readiness level verdicts
    readiness_levels = []
    for rl in deliverable.readiness_levels.all():
        if rl.admin_level or rl.incubatee_level:
            readiness_levels.append({
                'name': rl.name,
                'admin_level': rl.admin_level,
                'self_level': rl.incubatee_level,
            })

    context = {
        'deliverable_name': deliverable.name,
        'startup_name': startup.name,
        'milestone_name': milestone_label,
        'admin_name': admin_user.get_full_name() or admin_user.username,
        'status_label': status_label,
        'comment': comment,
        'action': action,
        'readiness_levels': readiness_levels,
    }

    try:
        html_message = render_to_string(template_name, context)
        plain_message = strip_tags(html_message)

        asyncio.run(
            _send_email_async(subject, plain_message, html_message, list(recipients))
        )
        logger.info(
            f"Email sent to {recipients} for deliverable '{deliverable.name}' "
            f"({status_label})"
        )
    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
