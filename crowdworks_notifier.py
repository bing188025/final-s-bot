"""
CrowdWorks email notifier.
Connects to Gmail via IMAP and fetches unread notification emails from CrowdWorks.
"""

import imaplib
import email
from email.header import decode_header, make_header


def _decode_header(value: str | None) -> str:
    if not value:
        return ""
    return str(make_header(decode_header(value)))


def _extract_body(msg: email.message.Message) -> str:
    """Extract plain text body from an email message."""
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                charset = part.get_content_charset() or "utf-8"
                return part.get_payload(decode=True).decode(charset, errors="replace").strip()
    else:
        charset = msg.get_content_charset() or "utf-8"
        return msg.get_payload(decode=True).decode(charset, errors="replace").strip()
    return ""


def fetch_new_crowdworks_messages(imap_server: str, email_address: str, email_password: str) -> list[dict]:
    """
    Connect to IMAP and return unread emails from CrowdWorks.
    Each result is a dict with keys: subject, sender, date, body.
    """
    results = []
    try:
        mail = imaplib.IMAP4_SSL(imap_server, 993)
        mail.login(email_address, email_password)
        mail.select("INBOX")

        status, data = mail.search(None, 'UNSEEN FROM "crowdworks.jp"')
        if status != "OK" or not data[0]:
            mail.logout()
            return results

        for eid in data[0].split():
            status, msg_data = mail.fetch(eid, "(RFC822)")
            if status != "OK":
                continue
            msg = email.message_from_bytes(msg_data[0][1])
            results.append({
                "subject": _decode_header(msg["Subject"]),
                "sender": _decode_header(msg["From"]),
                "date": msg.get("Date", ""),
                "body": _extract_body(msg),
            })

        mail.logout()
    except Exception as e:
        print(f"[IMAP ERROR] {e}")
    return results
