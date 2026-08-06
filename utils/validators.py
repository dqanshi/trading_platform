import re
from typing import Tuple, Optional
from utils.constants import TransactionType, OrderType, ProductType


class DataValidator:
    """
    Input validation utility for API payloads, symbols, and parameters.
    """

    @staticmethod
    def validate_trading_symbol(symbol: str) -> bool:
        if not symbol or not isinstance(symbol, str):
            return False
        pattern = r"^[A-Z0-9\-\_]{2,20}$"
        return bool(re.match(pattern, symbol.upper()))

    @staticmethod
    def validate_order_params(
        symbol: str,
        quantity: int,
        price: Optional[float],
        order_type: str,
        transaction_type: str,
        product: str
    ) -> Tuple[bool, str]:

        if not DataValidator.validate_trading_symbol(symbol):
            return False, f"Invalid symbol format: {symbol}"

        if quantity <= 0:
            return False, "Quantity must be greater than zero."

        if transaction_type.upper() not in [t.value for t in TransactionType]:
            return False, f"Invalid transaction type: {transaction_type}"

        if order_type.upper() not in [o.value for o in OrderType]:
            return False, f"Invalid order type: {order_type}"

        if product.upper() not in [p.value for p in ProductType]:
            return False, f"Invalid product type: {product}"

        if order_type.upper() in ["LIMIT", "SL"] and (price is None or price <= 0):
            return False, f"Price must be specified for {order_type} orders."

        return True, "Valid"
