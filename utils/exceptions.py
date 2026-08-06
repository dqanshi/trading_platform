class TradingPlatformException(Exception):
    """Base exception for all trading platform errors."""
    pass


class BrokerAuthenticationError(TradingPlatformException):
    """Raised when authentication with the broker fails."""
    pass


class OrderExecutionError(TradingPlatformException):
    """Raised when an order placement or modification fails."""
    pass


class RiskLimitExceededError(TradingPlatformException):
    """Raised when an action violates risk management policies."""
    pass


class StrategyExecutionError(TradingPlatformException):
    """Raised when an error occurs during strategy calculation or execution."""
    pass


class MarketDataError(TradingPlatformException):
    """Raised when market data or WebSocket streaming fails."""
    pass


class InsufficientFundsError(TradingPlatformException):
    """Raised when account margin or balance is insufficient for trade."""
    pass
