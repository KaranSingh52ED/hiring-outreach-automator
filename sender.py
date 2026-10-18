"""
Sender — Reads CSV, sends personalized emails via Zoho SMTP with proper anti-spam headers.
Sends one email every ~2 minutes to avoid spam detection.
Supports CC/BCC recipients and multiple email templates (shortlist / offer).
"""

import csv
import mimetypes
import random
import smtplib
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr, formatdate, make_msgid
from pathlib import Path

from jinja2 import Template

from config import Config


def load_contacts() -> list[dict]:
    """Load contacts from extracted CSV."""
    csv_path = Path(Config.OUTPUT_CSV)
    if not csv_path.exists():
        print(f"[!] CSV not found: {Config.OUTPUT_CSV}")
        print("    Run 'python main.py extract' first.")
        return []

    contacts = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("email"):
                contacts.append({"name": row["name"], "email": row["email"]})
    return contacts


def load_template(template_path: str | None = None) -> Template:
    """Load the HTML email template from the given path."""
    path = Path(template_path or Config.TEMPLATE_FILE)
    if not path.exists():
        print(f"[!] Template not found: {path}")
        return Template("<p>Hi {{ name }},</p>")
    return Template(path.read_text())


def get_attachments() -> list[Path]:
    """Get all files from the attachments directory."""
    attach_dir = Path(Config.ATTACHMENTS_DIR)
    if not attach_dir.exists():
        return []
    return [f for f in sorted(attach_dir.iterdir()) if f.is_file()]


def build_email(
    to_name: str,
    to_email: str,
    template: Template,
    attachments: list[Path],
    subject: str | None = None,
    cc_emails: list[str] | None = None,
    bcc_emails: list[str] | None = None,
) -> MIMEMultipart:
    """Build a MIME email with proper anti-spam headers, CC/BCC support."""
    msg = MIMEMultipart("mixed")

    # Anti-spam headers
    msg["From"] = formataddr((Config.SENDER_NAME, Config.ZOHO_EMAIL))
    msg["To"] = formataddr((to_name, to_email))
    msg["Subject"] = subject or Config.EMAIL_SUBJECT
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=Config.ZOHO_EMAIL.split("@")[1])
    msg["Reply-To"] = Config.ZOHO_EMAIL
    msg["X-Mailer"] = "Horrazon-Mailer/1.0"

    # CC header (visible to recipients)
    if cc_emails:
        msg["Cc"] = ", ".join(cc_emails)

    # BCC is NOT added as a header (by design — it stays hidden)
    # but we include BCC recipients in the SMTP envelope (sendmail recipients list)

    # Render personalized HTML
    html_body = template.render(name=to_name)
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Attach files
    for file_path in attachments:
        mime_type, _ = mimetypes.guess_type(str(file_path))
        mime_type = mime_type or "application/octet-stream"
        main_type, sub_type = mime_type.split("/", 1)

        with open(file_path, "rb") as f:
            part = MIMEBase(main_type, sub_type)
            part.set_payload(f.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition", f'attachment; filename="{file_path.name}"'
            )
            msg.attach(part)

    return msg


def _get_all_recipients(
    to_email: str,
    cc_emails: list[str] | None = None,
    bcc_emails: list[str] | None = None,
) -> list[str]:
    """Build the full recipient list for SMTP envelope (To + CC + BCC)."""
    recipients = [to_email]
    if cc_emails:
        recipients.extend(cc_emails)
    if bcc_emails:
        recipients.extend(bcc_emails)
    return recipients


def _connect_smtp():
    """Connect and authenticate to Zoho SMTP. Returns the server or None on failure."""
    try:
        server = smtplib.SMTP(Config.ZOHO_SMTP_HOST, Config.ZOHO_SMTP_PORT)
        server.ehlo()
        server.starttls()
        server.ehlo()
        server.login(Config.ZOHO_EMAIL, Config.ZOHO_PASSWORD)
        print("[✓] Connected to Zoho SMTP\n")
        return server
    except Exception as e:
        print(f"[✗] SMTP connection failed: {e}")
        return None


def _send_emails(
    contacts: list[dict],
    template_path: str,
    subject: str,
    cc_emails: list[str] | None = None,
    bcc_emails: list[str] | None = None,
):
    """Core send loop — used by both send_all() and send_offer()."""
    if not contacts:
        return

    template = load_template(template_path)
    attachments = get_attachments()

    print(f"[*] Contacts: {len(contacts)}")
    print(f"[*] Template: {template_path}")
    print(f"[*] Subject: {subject}")
    print(f"[*] Attachments: {len(attachments)} file(s)")
    if attachments:
        for a in attachments:
            print(f"      → {a.name}")
    if cc_emails:
        print(f"[*] CC: {', '.join(cc_emails)}")
    if bcc_emails:
        print(f"[*] BCC: {', '.join(bcc_emails)}")
    print(f"[*] Delay: random 90–120s between emails")
    print(f"[*] Estimated time: ~{(len(contacts) - 1) * 105 // 60} min\n")

    server = _connect_smtp()
    if not server:
        return

    sent, failed = 0, 0

    for i, contact in enumerate(contacts, 1):
        name, email = contact["name"], contact["email"]
        print(f"  [{i}/{len(contacts)}] → {name} <{email}>", end=" ... ")

        try:
            msg = build_email(
                to_name=name,
                to_email=email,
                template=template,
                attachments=attachments,
                subject=subject,
                cc_emails=cc_emails,
                bcc_emails=bcc_emails,
            )
            all_recipients = _get_all_recipients(email, cc_emails, bcc_emails)
            server.sendmail(Config.ZOHO_EMAIL, all_recipients, msg.as_string())
            sent += 1
            print("✓ Sent")
        except Exception as e:
            failed += 1
            print(f"✗ Failed ({e})")

        # Random delay between 90-120 seconds (skip after last)
        if i < len(contacts):
            delay = random.randint(90, 120)
            print(f"      ⏳ Waiting {delay}s before next...")
            time.sleep(delay)

    try:
        server.quit()
    except Exception:
        pass

    print(f"\n{'─' * 50}")
    print(f"[✓] Complete — Sent: {sent} | Failed: {failed}")


def send_all():
    """Send personalized shortlist emails to all contacts (original behavior)."""
    contacts = load_contacts()
    _send_emails(
        contacts=contacts,
        template_path=Config.TEMPLATE_FILE,
        subject=Config.EMAIL_SUBJECT,
        cc_emails=Config.CC_EMAILS or None,
        bcc_emails=Config.BCC_EMAILS or None,
    )


def send_offer():
    """Send congratulations/offer emails to all contacts with CC/BCC support."""
    contacts = load_contacts()
    _send_emails(
        contacts=contacts,
        template_path=Config.OFFER_TEMPLATE_FILE,
        subject=Config.OFFER_EMAIL_SUBJECT,
        cc_emails=Config.CC_EMAILS or None,
        bcc_emails=Config.BCC_EMAILS or None,
    )


if __name__ == "__main__":
    send_all()
