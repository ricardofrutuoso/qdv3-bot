#!/usr/bin/env python3
"""
QDV3 Alert Bot — Ricardo Frutuoso
Recebe webhooks do TradingView e envia alertas para Telegram
"""

import os
import json
import hmac
import hashlib
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# ── CONFIGURAÇÃO ─────────────────────────────────────────────
TELEGRAM_TOKEN  = "8681454728:AAGMaYXHn2UNIJ_XCdozvGgG-vROT8qxQ34"
CHAT_ID         = "8797381859"
WEBHOOK_SECRET  = "qdv3_frutuoso_2025"  # coloca este valor no TradingView também
PORT            = 8080

# ── TELEGRAM ─────────────────────────────────────────────────
import urllib.request

def send_telegram(message: str):
    url  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    data = json.dumps({
        "chat_id"    : CHAT_ID,
        "text"       : message,
        "parse_mode" : "HTML"
    }).encode("utf-8")
    req  = urllib.request.Request(url, data=data,
                                  headers={"Content-Type": "application/json"})
    try:
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        print(f"Telegram error: {e}")

# ── FORMATAR MENSAGEM ─────────────────────────────────────────
def format_alert(payload: dict) -> str:
    signal  = payload.get("signal",  "SINAL")
    ticker  = payload.get("ticker",  "N/A")
    price   = payload.get("price",   "N/A")
    tf      = payload.get("tf",      "1D")
    now     = datetime.now().strftime("%d/%m/%Y %H:%M")

    icons = {
        "BUY_9"   : "🟢",
        "SELL_9"  : "🟠",
        "BUY_13"  : "🔵",
        "SELL_13" : "🔴",
        "TRADE_UPPER" : "⬆️",
        "TRADE_LOWER" : "⬇️",
        "TREND_UPPER" : "🚨",
        "TREND_LOWER" : "💚",
        "TAIL_UPPER"  : "⚠️",
        "TAIL_LOWER"  : "🎯",
    }
    labels = {
        "BUY_9"   : "Exaustão Compra (9)",
        "SELL_9"  : "Exaustão Venda (9)",
        "BUY_13"  : "Exaustão Compra (13) ✅",
        "SELL_13" : "Exaustão Venda (13) ✅",
        "TRADE_UPPER" : "Preço acima Trade Upper",
        "TRADE_LOWER" : "Preço abaixo Trade Lower",
        "TREND_UPPER" : "Preço acima Trend Upper",
        "TREND_LOWER" : "Preço abaixo Trend Lower",
        "TAIL_UPPER"  : "Preço acima Tail — extremo",
        "TAIL_LOWER"  : "Preço abaixo Tail — extremo",
    }

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

# ── SERVIDOR WEBHOOK ─────────────────────────────────────────
class WebhookHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        # Health check — confirma que o servidor está vivo
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"QDV3 Bot online")
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        length  = int(self.headers.get("Content-Length", 0))
        body    = self.rfile.read(length)

        # Verificar secret
        secret_header = self.headers.get("X-QDV3-Secret", "")
        if secret_header != WEBHOOK_SECRET:
            self.send_response(403)
            self.end_headers()
            print(f"Unauthorized request from {self.client_address}")
            return

        try:
            payload = json.loads(body.decode("utf-8"))
            msg     = format_alert(payload)
            send_telegram(msg)
            print(f"Alert sent: {payload.get('signal')} on {payload.get('ticker')}")
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
        except Exception as e:
            print(f"Error processing webhook: {e}")
            self.send_response(500)
            self.end_headers()

    def log_message(self, format, *args):
        # Log limpo
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {args[0]} {args[1]}")


# ── MAIN ─────────────────────────────────────────────────────
if __name__ == "__main__":
    send_telegram(
        "🤖 <b>QDV3 Bot iniciado</b>\n"
        "━━━━━━━━━━━━━━━\n"
        "Sistema de alertas activo.\n"
        "Aguardando sinais do TradingView..."
    )
    print(f"QDV3 Bot running on port {PORT}")
    server = HTTPServer(("0.0.0.0", PORT), WebhookHandler)
    server.serve_forever()
