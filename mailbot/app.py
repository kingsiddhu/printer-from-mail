from imapclient import IMAPClient
import email
import requests
import subprocess
import time
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("APP_PASSWORD")
CONVERTER_URL = os.getenv("CONVERTER_URL", "http://converter:5000/convert")
PRINTER = os.getenv("PRINTER", "Canon_G2020_series")
FILES_DIR = os.getenv("FILES_DIR", "./files")

Path(FILES_DIR).mkdir(parents=True, exist_ok=True)


def convert_to_pdf(path):
    filename = os.path.basename(path)

    with open(path, "rb") as f:
        resp = requests.post(CONVERTER_URL, files={"file": (filename, f)}, timeout=120)

    if resp.status_code != 200:
        raise RuntimeError(f"Conversion failed ({resp.status_code}): {resp.text}")

    out_path = str(Path(path).with_suffix(".pdf"))
    with open(out_path, "wb") as f:
        f.write(resp.content)

    return out_path


def print_file(path):
    print("Printing:", path)
    subprocess.run(["lp", "-d", PRINTER, path], check=True)
    print("Printed successfully")


def process_unseen(client):
    messages = client.search(["UNSEEN"])
    
    for uid in messages:
        raw = client.fetch(uid, ["RFC822"])[uid][b"RFC822"]
        msg = email.message_from_bytes(raw)

        sender = msg["From"]
        print("From:", sender)

        for part in msg.walk():
            filename = part.get_filename()
            if not filename:
                continue
            
            ext = Path(filename).suffix.lower()
            if ext not in (".pdf", ".doc", ".docx"):
                continue
                
            path = os.path.join(FILES_DIR, filename)
            with open(path, "wb") as f:
                f.write(part.get_payload(decode=True))

            print("Received:", path)

            if ext in (".doc", ".docx"):
                print("Converting Word document...")
                path = convert_to_pdf(path)

            print_file(path)
        
        client.add_flags(uid, ["\\Seen"])


def watch_mailbox():
    """Long-lived connection using IMAP IDLE: blocks until Gmail pushes a
    notification instead of polling. Falls back to a periodic wake-up
    (IDLE_TIMEOUT) as a safety net in case a notification gets missed."""
    IDLE_TIMEOUT = 300  # seconds; just a heartbeat, not a poll interval

    with IMAPClient("imap.gmail.com", ssl=True) as client:
        client.login(EMAIL, PASSWORD)
        client.select_folder("INBOX")

        process_unseen(client) 
        
        while True:
            client.idle()
            try:
                client.idle_check(timeout=IDLE_TIMEOUT)
            finally:
                client.idle_done()

            process_unseen(client)


if __name__ == "__main__":
    backoff = 5
    max_backoff = 300

    while True:
        try:
            watch_mailbox()
        except Exception as e:
            print("Connection lost, reconnecting:", e)
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)
        else:
            backoff = 5