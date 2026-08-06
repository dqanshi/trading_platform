import pytest
from unittest.mock import MagicMock
from sqlalchemy.orm import Session
from engine.risk_manager import RiskManager
from broker.kite_client import KiteClient


@pytest.fixture
def mock_db():
    return MagicMock(spec=Session)


@pytest.fixture
def mock_kite():
    client = MagicMock(spec=KiteClient)
    client.get_quote.return_value = {
        "NSE:RELIANCE": {
            "last_price": 2500.0,
            "ohlc": {"close": 2480.0}
        }
    }
    return client


def test_risk_manager_order_validation_success(mock_db, mock_kite):
    rm = RiskManager(db=mock_db, kite_client=mock_kite)
    rm.max_order_value = 50000.0
    
    is_valid, reason = rm.validate_order(
        symbol="RELIANCE",
        quantity=10,
        price=2500.0,
        transaction_type="BUY"
    )
    
    assert is_valid is True
    assert reason == "Order passed risk validation"


def test_risk_manager_max_order_value_exceeded(mock_db, mock_kite):
    rm = RiskManager(db=mock_db, kite_client=mock_kite)
    rm.max_order_value = 10000.0
    
    is_valid, reason = rm.validate_order(
        symbol="RELIANCE",
        quantity=10,
        price=2500.0,
        transaction_type="BUY"
    )
    
    assert is_valid is False
    assert "exceeds maximum allowed limit" in reason


def test_risk_manager_max_failures_kill_switch(mock_db, mock_kite):
    rm = RiskManager(db=mock_db, kite_client=mock_kite)
    rm.max_consecutive_failures = 3
    
    rm.register_failure()
    rm.register_failure()
    rm.register_failure()
    
    is_valid, reason = rm.validate_order(
        symbol="RELIANCE",
        quantity=1,
        price=2500.0,
        transaction_type="BUY"
    )
    
    assert is_valid is False
    assert "Kill switch active" in reason
