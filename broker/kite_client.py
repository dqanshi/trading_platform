from typing import Dict, Any, List, Optional
from datetime import datetime
from kiteconnect import KiteConnect
import kiteconnect.exceptions as ex
from config.config import settings
from config.logging_config import get_logger

logger = get_logger("orders")


class KiteClient:
    def __init__(self, api_key: Optional[str] = None, access_token: Optional[str] = None):
        self.api_key = api_key or settings.KITE_API_KEY
        self.api_secret = settings.KITE_API_SECRET
        self.access_token = access_token or settings.KITE_ACCESS_TOKEN
        self.kite = KiteConnect(api_key=self.api_key)
        
        if self.access_token:
            self.kite.set_access_token(self.access_token)

    def generate_session(self, request_token: str) -> Dict[str, Any]:
        try:
            data = self.kite.generate_session(request_token, api_secret=self.api_secret)
            self.access_token = data["access_token"]
            self.kite.set_access_token(self.access_token)
            logger.info("Successfully generated Kite access token")
            return data
        except ex.KiteException as e:
            logger.error(f"Kite session generation failed: {str(e)}")
            raise e

    def set_access_token(self, access_token: str) -> None:
        self.access_token = access_token
        self.kite.set_access_token(access_token)

    def is_authenticated(self) -> bool:
        if not self.access_token:
            return False
        try:
            self.kite.profile()
            return True
        except Exception as e:
            logger.warning(f"Kite authentication check failed: {str(e)}")
            return False

    def get_profile(self) -> Dict[str, Any]:
        try:
            return self.kite.profile()
        except ex.KiteException as e:
            logger.error(f"Failed to fetch profile: {str(e)}")
            raise e

    def get_margins(self) -> Dict[str, Any]:
        try:
            return self.kite.margins()
        except ex.KiteException as e:
            logger.error(f"Failed to fetch margins: {str(e)}")
            raise e

    def place_order(
        self,
        symbol: str,
        exchange: str,
        transaction_type: str,
        quantity: int,
        order_type: str,
        product: str,
        price: float = 0.0,
        trigger_price: float = 0.0,
        tag: Optional[str] = None
    ) -> str:
        try:
            order_id = self.kite.place_order(
                variety=self.kite.VARIETY_REGULAR,
                exchange=exchange,
                tradingsymbol=symbol,
                transaction_type=transaction_type,
                quantity=quantity,
                product=product,
                order_type=order_type,
                price=price if order_type in [self.kite.ORDER_TYPE_LIMIT, self.kite.ORDER_TYPE_SL] else None,
                trigger_price=trigger_price if order_type in [self.kite.ORDER_TYPE_SL, self.kite.ORDER_TYPE_SLM] else None,
                tag=tag or "algo_trade"
            )
            logger.info(f"Order placed successfully. ID: {order_id} | {transaction_type} {quantity} {symbol}")
            return str(order_id)
        except ex.KiteException as e:
            logger.error(f"Order placement failed for {symbol}: {str(e)}")
            raise e

    def modify_order(
        self,
        order_id: str,
        quantity: Optional[int] = None,
        price: Optional[float] = None,
        trigger_price: Optional[float] = None,
        order_type: Optional[str] = None
    ) -> str:
        try:
            res_id = self.kite.modify_order(
                variety=self.kite.VARIETY_REGULAR,
                order_id=order_id,
                quantity=quantity,
                price=price,
                trigger_price=trigger_price,
                order_type=order_type
            )
            logger.info(f"Order modified successfully. ID: {order_id}")
            return str(res_id)
        except ex.KiteException as e:
            logger.error(f"Order modification failed for ID {order_id}: {str(e)}")
            raise e

    def cancel_order(self, order_id: str) -> str:
        try:
            res_id = self.kite.cancel_order(
                variety=self.kite.VARIETY_REGULAR,
                order_id=order_id
            )
            logger.info(f"Order cancelled successfully. ID: {order_id}")
            return str(res_id)
        except ex.KiteException as e:
            logger.error(f"Order cancellation failed for ID {order_id}: {str(e)}")
            raise e

    def get_orders(self) -> List[Dict[str, Any]]:
        try:
            return self.kite.orders()
        except ex.KiteException as e:
            logger.error(f"Failed to fetch orders: {str(e)}")
            raise e

    def get_positions(self) -> Dict[str, Any]:
        try:
            return self.kite.positions()
        except ex.KiteException as e:
            logger.error(f"Failed to fetch positions: {str(e)}")
            raise e

    def get_quote(self, instruments: List[str]) -> Dict[str, Any]:
        try:
            return self.kite.quote(instruments)
        except ex.KiteException as e:
            logger.error(f"Failed to fetch quotes: {str(e)}")
            raise e

    def get_historical_data(
        self,
        instrument_token: int,
        from_date: datetime,
        to_date: datetime,
        interval: str
    ) -> List[Dict[str, Any]]:
        try:
            return self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval
            )
        except ex.KiteException as e:
            logger.error(f"Failed to fetch historical data for token {instrument_token}: {str(e)}")
            raise e
