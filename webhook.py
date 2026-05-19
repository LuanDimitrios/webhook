# webhook.py
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
    
    try:
        raw_data = request.get_data(as_text=True)
        logger.info(f"Body: {raw_data}")
        event = request.json
        logger.info(f"Event: {event}")
    except Exception as e:
        logger.error(f"Erro ao parsear JSON: {e}")
        return jsonify({"error": "invalid json"}), 400

    # Extrai payment_id
    payment_id = None
    if event.get("type") == "payment":
        payment_id = event.get("data", {}).get("id")
    elif event.get("action") == "payment.updated":
        payment_id = event.get("data", {}).get("id")
    elif event.get("id"):
        payment_id = event.get("id")

    if not payment_id:
        logger.info("Evento sem payment_id - ignorado")
        return jsonify({"status": "ignored"}), 200

    # Consulta detalhes do pagamento
    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {"Authorization": f"Bearer {MERCADOPAGO_TOKEN}"}
    
    try:
        resp = requests.get(url, headers=headers, timeout=10)
        logger.info(f"Resposta MP: {resp.status_code}")
        
        if resp.status_code != 200:
            logger.error(f"Erro MP: {resp.status_code} - {resp.text}")
            return jsonify({"error": "payment not found"}), 404
        
        data = resp.json()
        status = data.get("status")
        logger.info(f"Status do pagamento: {status}")
        
        if status == "approved":
            external_ref = data.get("external_reference")
            logger.info(f"external_reference: {external_ref}")
            
            if external_ref and external_ref.startswith("user_"):
                user_id = int(external_ref.split("_")[1])
                logger.info(f"✅ Ativando assinatura para user {user_id}")
                
                if criar_assinatura(user_id, duracao_dias=30, payment_id=payment_id):
                    logger.info(f"✅ Assinatura ativada com sucesso para user {user_id}")
                else:
                    logger.error(f"❌ Falha ao ativar assinatura para user {user_id}")
            else:
                logger.warning(f"external_reference inválido: {external_ref}")
        else:
            logger.info(f"Pagamento não aprovado. Status: {status}")
            
    except Exception as e:
        logger.error(f"Erro ao consultar API do MP: {e}")
        return jsonify({"error": "api error"}), 500

    return jsonify({"status": "ok"}), 200

@app.route("/", methods=["GET"])
def health():
    return "Webhook rodando", 200

@app.route("/teste", methods=["GET"])
def teste():
    """Endpoint para testar se o webhook está funcionando"""
    return jsonify({"status": "ok", "message": "Webhook está rodando!"})

if __name__ == "__main__":
    # Railway define a variável PORT - use ela!
    port = int(os.getenv("PORT", 8080))
    logger.info(f"🚀 Webhook iniciando na porta {port}")
    app.run(host="0.0.0.0", port=port)
