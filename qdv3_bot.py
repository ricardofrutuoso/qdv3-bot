#!/usr/bin/env python3
"""
QDV3 Alert Bot — Ricardo Frutuoso
Le emails do TradingView via Gmail e envia alertas para Telegram
"""

import imaplib
import email
import time
import json
import urllib.request
from datetime import datetime

# ── CONFIGURAÇÃO ─────────────────────────────────────────────
TELEGRAM_TOKEN = "8681454728:AAGMaYXHn2UNIJ_XCdozvGgG-vROT8qxQ34"
CHAT_ID        = "8797381859"
GMAIL_USER     = "qdv3alerts@gmail.com"
GMAIL_PASS     = "xlrlntrdxzutyzlb"
CHECK_INTERVAL = 60  # segundos entre verificações

# ── TELEGRAM ─────────────────────────────────────────────────
def send_telegram(message: str):
    url  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = json.dumps({
        "chat_id"   : CHAT_ID,
        "text"      : message,
        "parse_mode": "HTML"
    }).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

# ── FORMATAR MENSAGEM ─────────────────────────────────────────
def format_alert(subject: str, body: str) -> str:
    now = datetime.now().strftime("%d/%m/%Y %H:%M")

    icons = {
        "BUY_9"       : "🟢", "SELL_9"      : "🟠",
        "BUY_13"      : "🔵", "SELL_13"     : "🔴",
        "TRADE_UPPER" : "⬆️", "TRADE_LOWER" : "⬇️",
        "TREND_UPPER" : "🚨", "TREND_LOWER" : "💚",
        "TAIL_UPPER"  : "⚠️", "TAIL_LOWER"  : "🎯",
    }
    labels = {
        "BUY_9"       : "Exaustão Compra (9)",
        "SELL_9"      : "Exaustão Venda (9)",
        "BUY_13"      : "Exaustão Compra (13) ✅",
        "SELL_13"     : "Exaustão Venda (13) ✅",
        "TRADE_UPPER" : "Preço acima Trade Upper",
        "TRADE_LOWER" : "Preço abaixo Trade Lower",
        "TREND_UPPER" : "Preço acima Trend Upper",
        "TREND_LOWER" : "Preço abaixo Trend Lower",
        "TAIL_UPPER"  : "Preço acima Tail — extremo",
        "TAIL_LOWER"  : "Preço abaixo Tail — extremo",
    }

    # Tentar fazer parse de JSON no body
    try:
        payload = json.loads(body.strip())
        signal  = payload.get("signal",  "SINAL")
        ticker  = payload.get("ticker",  "N/A")
        price   = payload.get("price",   "N/A")
        tf      = payload.get("tf",      "1D")
    except Exception:
        # Se não for JSON, usa o subject e body directamente
        return (
            f"📊 <b>QDV3 Alerta</b>\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📌 <b>Assunto:</b> {subject}\n"
            f"📝 <b>Mensagem:</b> {body[:200]}\n"
            f"🕐 <b>Hora:</b> {now}\n"
            f"━━━━━━━━━━━━━━━\n"
            f"<i>Decisão é tua — analisa antes de executar.</i>"
        )

    icon  = icons.get(signal,  "📊")
    label = labels.get(signal, signal)

    return (
        f"{icon} <b>QDV3 — {ticker}</b>\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📌 <b>Sinal:</b> {label}\n"
        f"💰 <b>Preço:</b> {price}\n"
        f"⏱ <b>Timeframe:</b> {tf}\n"
        f"🕐 <b>Hora:</b> {now}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"<i>Decisão é tua — analisa antes de executar.</i>"
    )

# ── LER EMAILS ───────────────────────────────────────────────
def check_emails():
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com")
        mail.login(GMAIL_USER, GMAIL_PASS)
        mail.select("inbox")

        # Procurar emails não lidos do TradingView
        _, msgs = mail.search(None, '(UNSEEN FROM "noreply@tradingview.com")')

        for num in msgs[0].split():
            _, data = mail.fetch(num, "(RFC822)")
            msg = email.message_from_bytes(data[0][1])

            subject = msg.get("Subject", "Sem assunto")
            body    = ""

            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True).decode("utf-8", errors="ignore")
                        break
            else:
                body = msg.get_payload(decode=True).decode("utf-8", errors="ignore")

            # Marcar como lido
            mail.store(num, "+FLAGS", "\\Seen")

            # Enviar para Telegram
            message = format_alert(subject, body.strip())
            send_telegram(message)
            print(f"Alert sent: {subject}")

        mail.logout()

    except Exception as e:
        print(f"Email error: {e}")

# ── MAIN ─────────────────────────────────────────────────────
if __name__ == "__main__":
    print("QDV3 Bot iniciado — a verificar emails...")
    send_telegram(
        "🤖 <b>QDV3 Bot iniciado</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "A monitorizar alertas do TradingView via Gmail.\n"
        f"📧 {GMAIL_USER}\n"
        "Verificação a cada 60 segundos."
    )
    while True:
        check_emails()
        time.sleep(CHECK_INTERVAL)
