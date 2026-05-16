import os
import logging
import requests
from flask import Flask, request, jsonify
from subscription import criar_assinatura

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

MERCADOPAGO_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")

@app.route("/webhook/mercadopago", methods=["POST"])
def mercadopago_webhook():
    logger.info("=== Webhook recebido ===")
    logger.info(f"Headers: {dict(request.headers)}")
    raw_data = request.get_data(as_text=True)
    logger.info(f"Body: {raw_data}")

    try:
        event = request.json
    except Exception as e:
        logger.error(f"JSON inválido: {e}")
        return jsonify({"error": "invalid json"}), 400

    # Extrai payment_id (para pagamentos comuns ou assinaturas)
    payment_id = None
    if event.get("type") == "payment":
        payment_id = event.get("data", {}).get("id")
    elif event.get("action") == "payment.updated":
        payment_id = event.get("data", {}).get("id")

    if not payment_id:
        logger.info("Evento sem payment_id - ignorado")
        return jsonify({"status": "ignored"}), 200

    # Consulta detalhes do pagamento
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {"Authorization": f"Bearer {MERCADOPAGO_TOKEN}"}
    try:
        resp = requests.get(url, headers=headers, timeout=10)
    except Exception as e:
        logger.error(f"Erro ao consultar API do MP: {e}")
        return jsonify({"error": "api error"}), 500

    if resp.status_code != 200:
        logger.error(f"Erro MP: {resp.status_code} - {resp.text}")
        return jsonify({"error": "payment not found"}), 404

    data = resp.json()
    status = data.get("status")
    if status == "approved":
        external_ref = data.get("external_reference")
        if external_ref and external_ref.startswith("user_"):
            user_id = int(external_ref.split("_")[1])
            criar_assinatura(user_id, duracao_dias=30, payment_id=payment_id)
            logger.info(f"✅ Assinatura ativada para user {user_id}")
        else:
            logger.warning(f"external_reference inválido: {external_ref}")
    else:
        logger.info(f"Pagamento {payment_id} status: {status}")

    return jsonify({"status": "ok"}), 200

@app.route("/", methods=["GET"])
def health():
    return "Webhook rodando", 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port)