import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # Zoho SMTP
    ZOHO_EMAIL = os.getenv("ZOHO_EMAIL")
    ZOHO_PASSWORD = os.getenv("ZOHO_PASSWORD")
    ZOHO_SMTP_HOST = os.getenv("ZOHO_SMTP_HOST", "smtp.zoho.in")
    ZOHO_SMTP_PORT = int(os.getenv("ZOHO_SMTP_PORT", 587))

    # Email settings
    SENDER_NAME = os.getenv("SENDER_NAME", "Talent Acquisition Team")
    EMAIL_SUBJECT = os.getenv(
        "EMAIL_SUBJECT",
        "Congratulations! You've Been Shortlisted for Round II – AI Engineering Challenge | Horrazon AI",
    )

    # Offer email settings
    OFFER_EMAIL_SUBJECT = os.getenv(
        "OFFER_EMAIL_SUBJECT",
        "Congratulations! Internship Offer – AI Engineer Intern (LLM & Agentic AI) | Horrazon Intelligence Private Limited",
    )

    # CC/BCC — comma-separated email addresses (optional)
    CC_EMAILS = [e.strip() for e in os.getenv("CC_EMAILS", "").split(",") if e.strip()]
    BCC_EMAILS = [
        e.strip() for e in os.getenv("BCC_EMAILS", "").split(",") if e.strip()
    ]

    # Paths
    RESUMES_DIR = "./Resumes"
    ATTACHMENTS_DIR = "./attachments"
    OUTPUT_CSV = "./extracted_emails.csv"
    TEMPLATE_FILE = "./template.html"
    OFFER_TEMPLATE_FILE = "./template_offer.html"

    # Rate limiting — 2 minutes between emails to avoid spam
    SEND_DELAY = int(os.getenv("SEND_DELAY", 120))
