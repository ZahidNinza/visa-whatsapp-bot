import os
import json
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse

from google.oauth2 import service_account
from googleapiclient.discovery import build

# ===================== CONFIG =====================
FOLDER_ID = "10wywy_btpezgQMadex40mIehu-1I-bDo"
# ==================================================

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

app = Flask(__name__)

# ---- Google Drive client (from ENV JSON) ----
# Render environment variable: GOOGLE_SERVICE_ACCOUNT_JSON
service_account_info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])

credentials = service_account.Credentials.from_service_account_info(
    service_account_info,
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
    # Local run only (Render will use gunicorn)
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
