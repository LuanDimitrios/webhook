import os
import logging
import threading
import requests
from flask import Flask, request, jsonify
from subscription import criar_assinatura

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
MERCADOPAGO_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")

def processar_pagamento(payment_id):
    """Processa o pagamento em segundo plano (não bloqueia o webhook)"""
    try:
        # Consulta o pagamento na API do Mercado Pago
        url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
        headers = {"Authorization": f"Bearer {MERCADOPAGO_TOKEN}"}
        resp = requests.get(url, headers=headers, timeout=10)
        
        if resp.status_code != 200:
            logger.error(f"Erro ao consultar pagamento {payment_id}: {resp.status_code}")
            return
        
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
    except Exception as e:
        logger.error(f"Erro no processamento: {e}")

@app.route("/webhook/mercadopago", methods=["POST"])
def mercadopago_webhook():
    # Responde IMEDIATAMENTE para evitar 502
    event = request.json
    logger.info(f"Webhook recebido: {event.get('action')}")
    
    # Extrai o payment_id
    payment_id = None
    if event.get("type") == "payment":
        payment_id = event.get("data", {}).get("id")
    elif event.get("action") == "payment.updated":
        payment_id = event.get("data", {}).get("id")
    
    if payment_id:
        # Processa em segundo plano
        threading.Thread(target=processar_pagamento, args=(payment_id,)).start()
    else:
        logger.warning("Nenhum payment_id encontrado")
    
    return jsonify({"status": "ok"}), 200

@app.route("/", methods=["GET"])
def health():
    return "Webhook OK", 200

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
