import csv
import io
import requests
from typing import Dict, Any, List, Optional
from config.logging_config import get_logger

logger = get_logger("system")


class InstrumentManager:
    """
    Handles downloading, parsing, caching, and searching Zerodha Kite instrument master files.
    """

    INSTRUMENTS_URL = "https://api.kite.trade/instruments"

    def __init__(self):
        self._instruments_cache: Dict[str, Dict[str, Any]] = {}
        self._token_map: Dict[int, Dict[str, Any]] = {}

    def fetch_and_load_instruments(self) -> int:
        try:
            response = requests.get(self.INSTRUMENTS_URL, timeout=15)
            response.raise_for_status()

            csv_data = csv.DictReader(io.StringIO(response.text))
            self._instruments_cache.clear()
            self._token_map.clear()

            count = 0
            for row in csv_data:
                token = int(row["instrument_token"])
                symbol = row["tradingsymbol"]
                exchange = row["exchange"]
                key = f"{exchange}:{symbol}"

                item = {
                    "instrument_token": token,
                    "exchange_token": row.get("exchange_token"),
                    "tradingsymbol": symbol,
                    "name": row.get("name"),
                    "last_price": float(row.get("last_price", 0.0)),
                    "expiry": row.get("expiry"),
                    "strike": float(row.get("strike", 0.0)),
                    "tick_size": float(row.get("tick_size", 0.05)),
                    "lot_size": int(row.get("lot_size", 1)),
                    "instrument_type": row.get("instrument_type"),
                    "segment": row.get("segment"),
                    "exchange": exchange
                }

                self._instruments_cache[key] = item
                self._token_map[token] = item
                count += 1

            logger.info(f"Loaded {count} instruments into memory cache.")
            return count

        except Exception as e:
            logger.error(f"Failed to fetch instrument master: {str(e)}")
            return 0

    def get_token(self, exchange: str, symbol: str) -> Optional[int]:
        key = f"{exchange}:{symbol}"
        inst = self._instruments_cache.get(key)
        return inst["instrument_token"] if inst else None

    def search_instruments(self, query: str, exchange: Optional[str] = "NSE") -> List[Dict[str, Any]]:
        query_upper = query.upper()
        results = []
        for key, inst in self._instruments_cache.items():
            if exchange and inst["exchange"] != exchange:
                continue
            if query_upper in inst["tradingsymbol"]:
                results.append(inst)
                if len(results) >= 50:
                    break
        return results
