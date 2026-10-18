#!/usr/bin/env python3
"""
Email Extractor & Sender — Horrazon Intelligence Pvt. Ltd.

Usage:
    python main.py extract   Extract names + emails from resumes → CSV
    python main.py send      Send personalized shortlist emails to all contacts in CSV
    python main.py offer     Send congratulations/offer emails to all contacts in CSV
"""

import sys

from config import Config


def banner():
    print("""
╔══════════════════════════════════════════════════╗
║   📧  Horrazon Email Extractor & Sender  v1.1    ║
║   ────────────────────────────────────────────   ║
║   extract → CSV → send/offer (2-min intervals)   ║
╚══════════════════════════════════════════════════╝
""")


def cmd_extract():
    from extractor import run_extraction

    print("[EXTRACT] Scanning resumes...\n")
    run_extraction()


def cmd_send():
    from sender import send_all

    print("[SEND] Starting shortlist email dispatch...\n")
    send_all()


def cmd_offer():
    from sender import send_offer

    print("[OFFER] Starting congratulations/offer email dispatch...\n")
    send_offer()


def main():
    banner()

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python main.py extract   →  Extract emails from ./Resumes/ to CSV")
        print(
            "  python main.py send      →  Send shortlist emails to all contacts in CSV"
        )
        print(
            "  python main.py offer     →  Send offer/congratulations emails (with CC/BCC)"
        )
        print()
        print(f"  Resumes folder:    {Config.RESUMES_DIR}")
        print(f"  Output CSV:        {Config.OUTPUT_CSV}")
        print(f"  Template (send):   {Config.TEMPLATE_FILE}")
        print(f"  Template (offer):  {Config.OFFER_TEMPLATE_FILE}")
        print(f"  Attachments:       {Config.ATTACHMENTS_DIR}")
        print(f"  Send delay:        {Config.SEND_DELAY}s (~2 min)")
        if Config.CC_EMAILS:
            print(f"  CC:                {', '.join(Config.CC_EMAILS)}")
        if Config.BCC_EMAILS:
            print(f"  BCC:               {', '.join(Config.BCC_EMAILS)}")
        return

    command = sys.argv[1].lower()

    if command == "extract":
        cmd_extract()
    elif command == "send":
        cmd_send()
    elif command == "offer":
        cmd_offer()
    else:
        print(f"[!] Unknown command: {command}")
        print("    Use 'extract', 'send', or 'offer'")


if __name__ == "__main__":
    main()
