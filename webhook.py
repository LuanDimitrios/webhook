import os
import logging
from flask import Flask, request, jsonify

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

@app.route("/webhook/mercadopago", methods=["POST"])
def mercadopago_webhook():
    logger.info("=== WEBHOOK RECEBIDO (MÍNIMO) ===")
    logger.info(f"Headers: {dict(request.headers)}")
    logger.info(f"Body: {request.get_data(as_text=True)}")
    return jsonify({"status": "ok"}), 200

@app.route("/", methods=["GET"])
def health():
    return "Webhook OK", 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    logger.info(f"Iniciando webhook na porta {port}")
    app.run(host="0.0.0.0", port=port)
