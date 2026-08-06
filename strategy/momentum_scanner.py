from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import pandas as pd
from broker.kite_client import KiteClient
from config.logging_config import get_logger

logger = get_logger("strategy")


class MomentumCandidate:
    def __init__(
        self,
        symbol: str,
        instrument_token: int,
        ltp: float,
        price_change_pct: float,
        volume: int,
        momentum_score: float
    ):
        self.symbol = symbol
        self.instrument_token = instrument_token
        self.ltp = ltp
        self.price_change_pct = price_change_pct
        self.volume = volume
        self.momentum_score = momentum_score


class HighMomentumScanner:
    """
    Scanner service that evaluates market quotes and candle data to identify
    high momentum stock candidates based on price acceleration and volume spikes.
    """

    def __init__(self, kite_client: KiteClient, watchlist: Dict[str, int]):
        self.kite_client = kite_client
        self.watchlist = watchlist

    def scan(self, top_n: int = 5) -> List[MomentumCandidate]:
        if not self.watchlist:
            return []

        formatted_instruments = [f"NSE:{sym}" for sym in self.watchlist.keys()]

        try:
            quotes = self.kite_client.get_quote(formatted_instruments)
        except Exception as e:
            logger.error(f"Failed to fetch quotes during momentum scan: {str(e)}")
            return []

        candidates: List[MomentumCandidate] = []

        for symbol, token in self.watchlist.items():
            quote_key = f"NSE:{symbol}"
            if quote_key not in quotes:
                continue

            q = quotes[quote_key]
            ltp = q.get("last_price", 0.0)
            net_change = q.get("net_change", 0.0)
            ohlc = q.get("ohlc", {})
            close_prev = ohlc.get("close", 0.0)
            volume = q.get("volume", 0)

            if close_prev <= 0:
                continue

            pct_change = ((ltp - close_prev) / close_prev) * 100.0
            momentum_score = pct_change * (volume / 100000.0)

            if pct_change >= 1.5:  # Minimum 1.5% intraday surge threshold
                candidates.append(
                    MomentumCandidate(
                        symbol=symbol,
                        instrument_token=token,
                        ltp=ltp,
                        price_change_pct=pct_change,
                        volume=volume,
                        momentum_score=momentum_score
                    )
                )

        sorted_candidates = sorted(candidates, key=lambda x: x.momentum_score, reverse=True)
        top_candidates = sorted_candidates[:top_n]

        logger.info(
            f"Momentum scan completed. Identified {len(top_candidates)} top momentum candidates."
        )
        return top_candidates
