import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from config.config import settings
from config.logging_config import get_logger

logger = get_logger("system")


class NotificationService:
    """
    Multi-channel notification engine supporting Telegram Bot alerts,
    Discord Webhooks, and SMTP Email dispatching.
    """

    def __init__(self):
        self.telegram_bot_token: Optional[str] = getattr(settings, "TELEGRAM_BOT_TOKEN", None)
        self.telegram_chat_id: Optional[str] = getattr(settings, "TELEGRAM_CHAT_ID", None)
        self.discord_webhook_url: Optional[str] = getattr(settings, "DISCORD_WEBHOOK_URL", None)
        self.smtp_host: Optional[str] = getattr(settings, "SMTP_HOST", None)
        self.smtp_port: int = int(getattr(settings, "SMTP_PORT", 587))
        self.smtp_user: Optional[str] = getattr(settings, "SMTP_USER", None)
        self.smtp_pass: Optional[str] = getattr(settings, "SMTP_PASS", None)

    def send_telegram(self, message: str) -> bool:
        if not self.telegram_bot_token or not self.telegram_chat_id:
            return False

        url = f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            res = requests.post(url, json=payload, timeout=5)
            return res.status_code == 200
        except Exception as e:
            logger.error(f"Telegram notification dispatch failed: {str(e)}")
            return False

    def send_discord(self, message: str, title: str = "QuantTerminal Alert") -> bool:
        if not self.discord_webhook_url:
            return False

        payload = {
            "embeds": [{
                "title": title,
                "description": message,
                "color": 3447003
            }]
        }
        try:
            res = requests.post(self.discord_webhook_url, json=payload, timeout=5)
            return res.status_code in (200, 204)
        except Exception as e:
            logger.error(f"Discord webhook dispatch failed: {str(e)}")
            return False

    def send_email(self, subject: str, body: str, recipient: str) -> bool:
        if not self.smtp_host or not self.smtp_user or not self.smtp_pass:
            return False

        try:
            msg = MIMEMultipart()
            msg["From"] = self.smtp_user
            msg["To"] = recipient
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "html"))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
            return True
        except Exception as e:
            logger.error(f"Email dispatch failed: {str(e)}")
            return False

    def notify_trade(self, symbol: str, action: str, qty: int, price: float, order_id: str) -> None:
        msg = (
            f"🚨 *TRADE EXECUTED*\n"
            f"• *Symbol*: {symbol}\n"
            f"• *Action*: {action}\n"
            f"• *Quantity*: {qty}\n"
            f"• *Price*: ₹{price:.2f}\n"
            f"• *Order ID*: `{order_id}`"
        )
        self.send_telegram(msg)
        self.send_discord(msg, title="Trade Execution Notice")


notifier = NotificationService()
