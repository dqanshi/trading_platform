import requests
from config.config import settings
from config.logging_config import get_logger

logger = get_logger("notifier")


class TelegramNotifier:
    def __init__(self):
        self.bot_token = settings.TELEGRAM_BOT_TOKEN
        self.chat_id = settings.TELEGRAM_CHAT_ID

    def send_message(self, message: str) -> bool:
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram bot token or chat ID not configured.")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        try:
            response = requests.post(url, json=payload, timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {str(e)}")
            return False

    def notify_trade(self, symbol: str, transaction_type: str, quantity: int, price: float, order_id: str):
        msg = (
            f"🚨 *TRADE EXECUTED*\n"
            f"*Symbol:* `{symbol}`\n"
            f"*Action:* `{transaction_type}`\n"
            f"*Quantity:* `{quantity}`\n"
            f"*Price:* `₹{price:,.2f}`\n"
            f"*Order ID:* `{order_id}`"
        )
        self.send_message(msg)


notifier = TelegramNotifier()
