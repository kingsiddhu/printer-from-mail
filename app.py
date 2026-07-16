from imapclient import IMAPClient
import email
import subprocess
import time
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("APP_PASSWORD")


def convert_to_pdf(path):
    output_dir = os.path.dirname(path)

    subprocess.run([
        "libreoffice",
        "--headless",
        "--convert-to",
        "pdf",
        "--outdir",
        output_dir,
        path
    ], check=True)

    return str(Path(path).with_suffix(".pdf"))

def check_mail():

    with IMAPClient("imap.gmail.com", ssl=True) as client:
        client.login(EMAIL, PASSWORD)

        client.select_folder("INBOX")

        messages = client.search([
            "UNSEEN"
        ])

        for uid in messages:
            raw = client.fetch(uid, ["RFC822"])[uid][b"RFC822"]

            msg = email.message_from_bytes(raw)
            #print(msg.as_string())
            sender = msg["From"]
            print("From:", sender)
            
            for part in msg.walk():

                filename = part.get_filename()

                if not filename:
                    continue

                ext = Path(filename).suffix.lower()
                print(ext)


                if ext in [".pdf", ".doc", ".docx"]:

                    path = "./files/" + filename

                    with open(path, "wb") as f:
                        f.write(part.get_payload(decode=True))

                    print("Received:", path)

                    if ext in [".doc", ".docx"]:
                        print("Converting Word document...")
                        path = convert_to_pdf(path)

                    print("Printing:", path)
                    print_file(path)

            client.add_flags(uid, ["\\Seen"])

def print_file(path):
    print("Printing:", path)
    printer = "Canon_G2020_series"

    subprocess.run(
        ["lp", "-d", printer, path],
        check=True
    )

    print("Printed successfully")
while True:
    check_mail()
    print("...")
    time.sleep(15)