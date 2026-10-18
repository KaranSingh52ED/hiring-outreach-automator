# 📧 Email Extractor & Sender — Horrazon

Extract candidate names + emails from bulk resumes (PDF/DOCX) → CSV, then send personalized emails via Zoho SMTP with a 2-minute gap between each to avoid spam.

## Setup

```bash
source venv/bin/activate
cp .env.example .env       # Add your Zoho credentials
pip install -r requirements.txt
```

## Usage

```bash
# Step 1: Drop resumes into ./Resumes/ folder

# Step 2: Extract emails to CSV
python main.py extract

# Step 3: (Optional) Add attachments to ./attachments/

# Step 4: Send emails
python main.py send
```

## Project Structure

```
Email_Extractor/
├── main.py              # CLI (extract / send)
├── config.py            # Configuration from .env
├── extractor.py         # Extracts name + email → CSV
├── sender.py            # Sends via Zoho SMTP, 2-min delay
├── template.html        # Email template with signature
├── Resumes/             # Drop PDF/DOCX here
├── attachments/         # Files to attach to emails
├── extracted_emails.csv # Generated after extraction
├── .env                 # Your credentials
└── requirements.txt
```

## How it works

1. **Extract** — Parses every PDF/DOCX in `./Resumes/`, pulls the candidate's name (first line) and email, deduplicates, saves to `extracted_emails.csv`
2. **Send** — Reads the CSV, renders a personalized HTML email (with your Horrazon signature), attaches any files from `./attachments/`, sends one-by-one with a 2-minute gap via Zoho SMTP TLS

## Anti-spam measures

- Proper `From`, `To`, `Reply-To`, `Date`, `Message-ID` headers
- One email at a time (no bulk blast)
- 2-minute delay between sends
- TLS encrypted connection
- Personalized `To:` header with recipient name
