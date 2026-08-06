from typing import Dict, Any, List, Optional
from config.config import settings
from utils.exceptions import BrokerAuthenticationError, OrderExecutionError
from config.logging_config import get_logger

logger = get_logger("broker")


class KiteClient:
    """
    Wrapper around KiteConnect REST API client.
    Handles login, quote fetching, order routing, and historical data fetching.
    """

    def __init__(self):
        self.api_key = settings.KITE_API_KEY
        self.api_secret = settings.KITE_API_SECRET
        self.access_token = settings.KITE_ACCESS_TOKEN
        self.client = None
        self._initialize()

    def _initialize(self):
        try:
            from kiteconnect import KiteConnect
            self.client = KiteConnect(api_key=self.api_key)
            if self.access_token:
                self.client.set_access_token(self.access_token)
        except ImportError:
            logger.warning("kiteconnect package not installed. Running in mock mode.")
            self.client = None

    def generate_session(self, request_token: str) -> str:
        if not self.client:
            raise BrokerAuthenticationError("KiteConnect client not initialized.")
        try:
            data = self.client.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data["access_token"]
            self.client.set_access_token(self.access_token)
            return self.access_token
        except Exception as e:
            logger.error(f"Failed to generate Kite session: {str(e)}")
            raise BrokerAuthenticationError(f"Session generation failed: {str(e)}")

    def place_order(
        self,
        variety: str,
        exchange: str,
        tradingsymbol: str,
        transaction_type: str,
        quantity: int,
        product: str,
        order_type: str,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None
    ) -> str:
        if not self.client:
            logger.info(f"MOCK ORDER: {transaction_type} {quantity} {tradingsymbol} @ {price}")
            return f"MOCK_ORDER_{tradingsymbol}_12345"

        try:
            order_id = self.client.place_order(
                variety=variety,
                exchange=exchange,
                tradingsymbol=tradingsymbol,
                transaction_type=transaction_type,
                quantity=quantity,
                product=product,
                order_type=order_type,
                price=price,
                trigger_price=trigger_price
            )
            return str(order_id)
        except Exception as e:
            logger.error(f"Kite order placement exception: {str(e)}")
            raise OrderExecutionError(f"Order failed on Kite: {str(e)}")

    def cancel_order(self, variety: str, order_id: str) -> bool:
        if not self.client:
            return True
        try:
            self.client.cancel_order(variety=variety, order_id=order_id)
            return True
        except Exception as e:
            logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            return False

    def get_historical_data(
        self,
        instrument_token: int,
        from_date: str,
        to_date: str,
        interval: str
    ) -> List[Dict[str, Any]]:
        if not self.client:
            return []
        try:
            return self.client.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
        except Exception as e:
            logger.error(f"Failed to fetch historical data for token {instrument_token}: {str(e)}")
            return []
