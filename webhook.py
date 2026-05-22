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
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")  # necessário para notificar o usuário

def enviar_mensagem_telegram(user_id, texto):
    """Envia uma mensagem para o usuário no Telegram"""
    if not TELEGRAM_TOKEN:
        logger.warning("TELEGRAM_TOKEN não configurado")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": user_id,
        "text": texto,
        "parse_mode": "Markdown"
    }
    try:
        resp = requests.post(url, json=payload, timeout=5)
        if resp.status_code != 200:
            logger.error(f"Erro ao enviar mensagem para {user_id}: {resp.text}")
    except Exception as e:
        logger.error(f"Falha ao enviar mensagem: {e}")

def processar_pagamento(payment_id):
    """Processa o pagamento em background (não bloqueia o webhook)"""
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
        logger.info(f"Status do pagamento {payment_id}: {status}")

        if status == "approved":
            external_ref = data.get("external_reference")
            if external_ref and external_ref.startswith("user_"):
                user_id = int(external_ref.split("_")[1])
                logger.info(f"✅ Ativando assinatura para user {user_id}")
                if criar_assinatura(user_id, duracao_dias=30, payment_id=payment_id):
                    logger.info(f"✅ Assinatura ativada para user {user_id}")
                    # Notifica o usuário
                    enviar_mensagem_telegram(
                        user_id,
                        "🎉 *Pagamento confirmado!*\n\n"
                        "Seu acesso ao bot foi liberado por 30 dias.\n"
                        "Use /start para começar a usar todas as funcionalidades."
                    )
                else:
                    logger.error(f"❌ Falha ao ativar assinatura para user {user_id}")
            else:
                logger.warning(f"external_reference inválido: {external_ref}")
        else:
            logger.info(f"Pagamento {payment_id} não aprovado. Status: {status}")
    except Exception as e:
        logger.error(f"Erro no processamento: {e}")

@app.route("/webhook/mercadopago", methods=["POST"])
def mercadopago_webhook():
    # Responde IMEDIATAMENTE para evitar 502
    event = request.json
    logger.info(f"Webhook recebido: {event.get('action') or event.get('type')}")

    # Extrai o payment_id
    payment_id = None
    if event.get("type") == "payment":
        payment_id = event.get("data", {}).get("id")
    elif event.get("action") == "payment.updated":
        payment_id = event.get("data", {}).get("id")
    elif event.get("id"):
        payment_id = event.get("id")

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
