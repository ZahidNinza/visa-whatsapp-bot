import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from google.oauth2 import service_account
from googleapiclient.discovery import build

# ===================== CONFIG =====================
FOLDER_ID = "10wywy_btpezgQMadex40mIehu-1I-bDo"

# ✅ yaha apni JSON file ka exact naam rakho
SERVICE_ACCOUNT_FILE = "visa-whatsapp-bot-1c44f4d4505f.json"
# ==================================================

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

app = Flask(__name__)

# ---- Google Drive client ----
credentials = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE,
    scopes=SCOPES
)

drive_service = build("drive", "v3", credentials=credentials)


def find_pdf_in_folder(passport_number: str):
    """
    Given passport number like P1234567, search inside folder for matching PDF.
    """
    passport_number = passport_number.strip()

    query = (
        f"'{FOLDER_ID}' in parents and "
        f"mimeType='application/pdf' and "
        f"name contains '{passport_number}' and "
        "trashed = false"
    )

    results = drive_service.files().list(
        q=query,
        fields="files(id, name)",
        pageSize=1
    ).execute()

    files = results.get("files", [])
    return files[0] if files else None


@app.route("/whatsapp", methods=["POST"])
def whatsapp_webhook():
    incoming_msg = (request.form.get("Body") or "").strip()

    resp = MessagingResponse()
    msg = resp.message()

    if not incoming_msg:
        msg.body("❌ Message blank hai. Passport number bhejo, jaise: P1234567")
        return str(resp)

    pdf = find_pdf_in_folder(incoming_msg)

    if pdf:
        file_id = pdf["id"]
        file_name = pdf["name"]

        # ✅ Direct download link
        download_url = f"https://drive.google.com/uc?id={file_id}&export=download"

        msg.body(f"✅ Visa found: {file_name}")
        msg.media(download_url)
    else:
        msg.body("❌ Visa PDF nahi mila. Passport number dobara check karo (example: P1234567).")

    return str(resp)


if __name__ == "__main__":
    # Local run
    app.run(host="0.0.0.0", port=5000, debug=True)
