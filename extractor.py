"""
Extractor — Extracts candidate name and email from PDF/DOCX resumes, saves to CSV.
"""

import csv
import re
from pathlib import Path

from PyPDF2 import PdfReader
from docx import Document

from config import Config

EMAIL_REGEX = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,4}")

EXCLUDED_DOMAINS = {"example.com", "email.com", "domain.com", "yourmail.com"}

# Words that are NOT names — common resume headers/sections
NOT_NAMES = {
    "resume",
    "cv",
    "curriculum",
    "vitae",
    "objective",
    "summary",
    "career",
    "education",
    "experience",
    "skills",
    "contact",
    "profile",
    "about",
    "personal",
    "details",
    "information",
    "projects",
    "certifications",
    "achievements",
    "references",
    "declaration",
    "hobbies",
    "interests",
    "languages",
    "strengths",
    "intern",
    "internship",
    "engineer",
    "developer",
    "analyst",
}


def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    try:
        reader = PdfReader(file_path)
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content + "\n"
    except Exception as e:
        print(f"  [!] Error reading PDF: {e}")
    return text


def extract_text_from_docx(file_path: str) -> str:
    text = ""
    try:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    text += cell.text + "\n"
    except Exception as e:
        print(f"  [!] Error reading DOCX: {e}")
    return text


def _is_valid_name(text: str) -> bool:
    """Check if text looks like a human name."""
    words = text.strip().split()
    if not (2 <= len(words) <= 5):
        return False
    # All words should be alphabetic
    if not all(w.isalpha() for w in words):
        return False
    # No word should be a common resume header
    if any(w.lower() in NOT_NAMES for w in words):
        return False
    # No word should be a location/institution keyword
    location_words = {
        "india",
        "maharashtra",
        "karnataka",
        "gujarat",
        "pune",
        "mumbai",
        "delhi",
        "bangalore",
        "hyderabad",
        "chennai",
        "kolkata",
        "ahmedabad",
        "university",
        "college",
        "institute",
        "school",
        "academy",
        "adani",
        "github",
        "linkedin",
        "http",
        "www",
        "com",
        "org",
        "net",
        "btech",
        "mtech",
        "bachelor",
        "master",
        "science",
        "computer",
        "engineering",
        "technology",
        "diploma",
        "degree",
        "pursuing",
    }
    if any(w.lower() in location_words for w in words):
        return False
    # Each word should be reasonably short (names rarely > 12 chars)
    if any(len(w) > 14 for w in words):
        return False
    return True


def _name_from_text(text: str) -> str:
    """Strategy 1: Extract name from the first few lines of resume text."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]

    for line in lines[:10]:
        # Skip lines with email, phone, URL, special chars
        if EMAIL_REGEX.search(line):
            continue
        if re.search(
            r"[\d]{4,}|http|www\.|@|\||\+91|phone|mobile|github|linkedin",
            line,
            re.IGNORECASE,
        ):
            continue
        # Skip very long lines (likely paragraphs or addresses)
        if len(line) > 35:
            continue

        # Clean the line — remove non-alpha chars
        clean = re.sub(r"[^a-zA-Z\s]", "", line).strip()
        # Remove extra spaces
        clean = re.sub(r"\s+", " ", clean)

        if _is_valid_name(clean):
            return clean.title()

    return ""


def _name_from_filename(filename: str) -> str:
    """Strategy 2: Derive name from the filename."""
    name = Path(filename).stem

    # Remove common prefixes/suffixes
    name = re.sub(r"(?i)^resume[s]?[-_\s]*", "", name)
    name = re.sub(r"(?i)[-_\s]*(resume|cv)[-_\s]*$", "", name)
    name = re.sub(r"(?i)[-_\s]*(ai|aiml|ml|intern|engineer)[-_\s]*", " ", name)
    name = re.sub(r"(?i)[-_\s]*(pdf|doc|docx)[-_\s]*", " ", name)

    # Replace separators with spaces, but preserve single-letter initials
    # First, protect initials like "S.S" → mark them
    name = re.sub(r"\b([A-Z])\.([A-Z])\b", r"\1_INIT_\2", name)
    name = re.sub(r"[_\-\.]+", " ", name)
    name = name.replace("_INIT_", " ")
    # Remove stray numbers
    name = re.sub(r"\d+", " ", name)
    name = re.sub(r"\s+", " ", name).strip()

    if not name:
        return ""

    # Handle all-UPPERCASE: keep as one word (e.g., "VENNELA" stays "Vennela")
    # For mixed case: split camelCase "AfshanSaniaA" → "Afshan Sania A"
    if not name.isupper() and not name.islower():
        name = re.sub(r"([a-z])([A-Z])", r"\1 \2", name)
        name = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", name)

    # Capitalize each word properly
    words = name.split()
    cleaned_words = []
    for w in words:
        if w.lower() in NOT_NAMES:
            continue
        # Skip very short fragments (likely junk from splitting)
        if len(w) == 1:
            cleaned_words.append(w.upper())
        elif len(w) == 2 and w.isupper():
            # Likely initials like "HN", "SS" → "H N" or keep as-is
            cleaned_words.append(w.upper())
        else:
            cleaned_words.append(w.capitalize())

    if cleaned_words:
        return " ".join(cleaned_words)
    return ""


def _name_from_email(email: str) -> str:
    """Strategy 3: Derive name from email local part as last resort."""
    local = email.split("@")[0]

    # Remove common prefixes/suffixes
    local = re.sub(r"(?i)^(its|the|im|hey|mr|ms|dr)", "", local)
    # Remove numbers
    local = re.sub(r"\d+", "", local)
    # Replace dots/underscores with spaces
    local = re.sub(r"[._\-]+", " ", local).strip()

    if not local:
        return ""

    # Split camelCase
    local = re.sub(r"([a-z])([A-Z])", r"\1 \2", local)

    words = local.split()
    # Filter short garbage
    words = [w.capitalize() for w in words if len(w) >= 2]

    if words:
        return " ".join(words)
    return ""


def extract_name(text: str, filename: str, email: str) -> str:
    """
    Extract candidate name using 3 strategies in priority order:
    1. From resume text (first lines) — most reliable if valid
    2. From filename — good fallback for "ResumeFirstnameLastname.pdf" format
    3. From email address — last resort
    """
    # Strategy 1: From text content
    name_from_text = _name_from_text(text)

    # Strategy 2: From filename
    name_from_file = _name_from_filename(filename)

    # Strategy 3: From email
    name_from_mail = _name_from_email(email)

    # Pick the best one
    # Text-based name is best if it has 2+ proper words
    if name_from_text and len(name_from_text.split()) >= 2:
        # But if any word is just 2 chars (likely bad initial parse), prefer filename
        words = name_from_text.split()
        has_suspicious_word = any(len(w) == 2 and w != w.upper() for w in words)
        if not has_suspicious_word:
            return name_from_text
        # If filename also has 2+ words, use it instead
        if name_from_file and len(name_from_file.split()) >= 2:
            return name_from_file
        return name_from_text

    # Filename-based name if it has 2+ words
    if name_from_file and len(name_from_file.split()) >= 2:
        return name_from_file

    # Text with single word is still better than email-derived
    if name_from_text and len(name_from_text) >= 3:
        return name_from_text

    # Filename single word
    if name_from_file and len(name_from_file) >= 3:
        return name_from_file

    # Email-derived as last resort
    if name_from_mail and len(name_from_mail) >= 3:
        return name_from_mail

    return "Candidate"


def extract_email(text: str) -> str:
    """Extract the first valid email from text, cleaning PDF URL artifacts."""
    matches = EMAIL_REGEX.findall(text)
    for email in matches:
        email = email.lower().strip(".")
        domain = email.split("@")[1]
        if domain in EXCLUDED_DOMAINS:
            continue

        # Clean PDF hyperlink artifacts — emails from redirect URLs
        # often have "pe" prefix stuck to them
        local_part = email.split("@")[0]

        if local_part.startswith("pe") and len(local_part) > 4:
            cleaned = local_part[2:]
            if cleaned and cleaned[0].isalpha():
                # Don't strip from real "pe" names
                real_pe_names = {
                    "peter",
                    "pedro",
                    "penny",
                    "pearl",
                    "perry",
                    "peggy",
                    "percy",
                }
                if not any(local_part.startswith(n) for n in real_pe_names):
                    email = cleaned + "@" + domain

        # Handle "3a" prefix (URL encoding artifacts)
        local_part = email.split("@")[0]
        if local_part.startswith("3a"):
            email = local_part[2:] + "@" + domain

        # Validate: proper format, TLD must be 2-4 chars (.com, .in, .org, .info)
        if re.match(r"^[a-z0-9][a-z0-9._%+\-]*@[a-z0-9.\-]+\.[a-z]{2,4}$", email):
            # Extra check: reject if domain looks corrupted (e.g. gmail.comp, gmail.compri)
            domain = email.split("@")[1]
            known_domains = {
                "gmail.com",
                "yahoo.com",
                "hotmail.com",
                "outlook.com",
                "zoho.com",
                "zoho.in",
                "protonmail.com",
                "icloud.com",
                "rediffmail.com",
                "ymail.com",
                "live.com",
                "mail.com",
            }
            # If it's a known provider, the domain must match exactly
            provider = domain.split(".")[0]  # e.g. "gmail"
            if provider in (
                "gmail",
                "yahoo",
                "hotmail",
                "outlook",
                "zoho",
                "protonmail",
            ):
                if domain not in known_domains:
                    continue  # Corrupted domain like gmail.comp
            return email

    return ""


def run_extraction() -> list[dict]:
    """Scan all resumes, extract name + email, save to CSV."""
    resumes_path = Path(Config.RESUMES_DIR)
    if not resumes_path.exists():
        print(f"[!] Resumes folder not found: {Config.RESUMES_DIR}")
        return []

    supported = {".pdf", ".docx", ".doc"}
    files = sorted(f for f in resumes_path.iterdir() if f.suffix.lower() in supported)

    if not files:
        print(f"[!] No PDF/DOCX files found in {Config.RESUMES_DIR}/")
        return []

    print(f"[*] Found {len(files)} resume(s)\n")
    results = []

    for file in files:
        ext = file.suffix.lower()
        print(f"  Processing: {file.name}", end=" → ")

        if ext == ".pdf":
            text = extract_text_from_pdf(str(file))
        else:
            text = extract_text_from_docx(str(file))

        email = extract_email(text)
        if not email:
            print("No email found, skipping")
            continue

        name = extract_name(text, file.name, email)
        # Clean extra whitespace
        name = re.sub(r"\s+", " ", name).strip()

        results.append({"name": name, "email": email})
        print(f"{name} <{email}>")

    # Deduplicate by email
    seen = set()
    unique = []
    for r in results:
        if r["email"] not in seen:
            seen.add(r["email"])
            unique.append(r)

    # Save to CSV
    csv_path = Path(Config.OUTPUT_CSV)
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "email"])
        writer.writeheader()
        writer.writerows(unique)

    print(f"\n[✓] Extracted {len(unique)} unique contact(s)")
    print(f"[✓] Saved to: {csv_path}")
    return unique


if __name__ == "__main__":
    run_extraction()
