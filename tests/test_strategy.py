import pytest
from unittest.mock import MagicMock
from datetime import time
from strategy.orb_strategy import ORBStrategy, ORBInstrumentState
from database.models import TransactionType


def test_orb_range_building():
    mock_db = MagicMock()
    mock_kite = MagicMock()
    mock_order_mgr = MagicMock()
    mock_risk_mgr = MagicMock()
    mock_pos_mgr = MagicMock()

    watchlist = {"RELIANCE": 738561}
    strategy = ORBStrategy(
        db=mock_db,
        kite_client=mock_kite,
        order_manager=mock_order_mgr,
        risk_manager=mock_risk_mgr,
        position_manager=mock_pos_mgr,
        watchlist=watchlist,
        range_start_time="00:00",
        range_end_time="23:59"
    )
    strategy.start()

    ticks = [{
        "tradingsymbol": "RELIANCE",
        "last_price": 2510.0
    }, {
        "tradingsymbol": "RELIANCE",
        "last_price": 2490.0
    }]

    strategy.on_tick(ticks)

    state = strategy.instruments["RELIANCE"]
    assert state.orb_high == 2510.0
    assert state.orb_low == 2490.0


def test_orb_breakout_execution():
    mock_db = MagicMock()
    mock_kite = MagicMock()
    mock_order_mgr = MagicMock()
    mock_risk_mgr = MagicMock()
    mock_pos_mgr = MagicMock()

    mock_risk_mgr.validate_order.return_value = (True, "Order passed risk validation")

    watchlist = {"RELIANCE": 738561}
    strategy = ORBStrategy(
        db=mock_db,
        kite_client=mock_kite,
        order_manager=mock_order_mgr,
        risk_manager=mock_risk_mgr,
        position_manager=mock_pos_mgr,
        watchlist=watchlist,
        range_start_time="00:00",
        range_end_time="00:01"
    )
    strategy.start()

    state = strategy.instruments["RELIANCE"]
    state.orb_high = 2500.0
    state.orb_low = 2400.0
    state.range_established = True

    breakout_tick = [{
        "tradingsymbol": "RELIANCE",
        "last_price": 2505.0
    }]

    strategy.on_tick(breakout_tick)

    assert state.traded_today is True
    mock_order_mgr.execute_order.assert_called_once()
