import azure.functions as func
import logging
import json
import os
from urllib.parse import urlparse, unquote
from mistralai import Mistral

app = func.FunctionApp()

@app.queue_trigger(arg_name="azqueue", queue_name="documento-nuevo",
                   connection="cuentatesis_STORAGE")
def OCR_trigger(azqueue: func.QueueMessage):

    # 1) Read message from queue
    msg = azqueue.get_body().decode('utf-8')
    data = json.loads(msg)

    blob_url = data.get("blobUrl")
    if not blob_url:
        logging.error("❌ No blobUrl found in the queue message")
        return
    
    logging.info(f"📥 Received blob URL: {blob_url}")

    # 2) Prepare document info
    parsed = urlparse(blob_url)
    filename = unquote(os.path.basename(parsed.path))
    
    logging.info(f"📄 Document name: {filename}")

    # 3) Call Mistral OCR API
    try:
        api_key = os.environ["MISTRAL_API_KEY"]
        client = Mistral(api_key=api_key)

        logging.info("⚙️ Processing OCR with Mistral...")

        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": blob_url
            },
            include_image_base64=False
        )

        logging.info("✅ OCR process completed")

        # Extract text blocks
        extracted_text = "\n".join([item.text for item in ocr_response.output.text_blocks])
        logging.info(f"📑 Extracted text:\n{extracted_text[:500]}...")  # print partial

    except Exception as e:
        logging.error(f"❌ OCR failed: {e}")
        return

    # TODO: You can now save extracted text to Blob, DB, another queue, etc.
    logging.info("🎯 OCR finished successfully")
