class QuantTerminalException(Exception):
    """Base exception class for QuantTerminal engine."""
    pass


class BrokerAuthenticationError(QuantTerminalException):
    """Raised when broker authentication or token exchange fails."""
    pass


class OrderExecutionError(QuantTerminalException):
    """Raised when an order placement, modification, or cancellation fails."""
    pass


class RiskViolationError(QuantTerminalException):
    """Raised when trade order breaches risk limits."""
    pass
