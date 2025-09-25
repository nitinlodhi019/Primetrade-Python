#!/usr/bin/env python3
"""
trading_bot.py - Binance Futures Testnet Trading Bot (USDT-M)

Features:
- MARKET, LIMIT, STOP order support
- Logging to console + rotating file
- Reads API keys from `.env` or environment variables
- Optional CLI override for keys
"""

import argparse
import os
import time
import hmac
import hashlib
import logging
import requests
from urllib.parse import urlencode
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load API keys from .env (highest priority: CLI > .env > OS env)
load_dotenv()

# Testnet base URL
TESTNET_BASE = "https://testnet.binancefuture.com"

# --------- Logging Setup ---------
logger = logging.getLogger("TradingBot")
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    "%Y-%m-%d %H:%M:%S",
)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
logger.addHandler(ch)

# Rotating file handler
fh = RotatingFileHandler("trading_bot.log", maxBytes=2_000_000, backupCount=5)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logger.addHandler(fh)


# --------- Binance Futures REST Client ---------
class BinanceFuturesREST:
    def __init__(self, api_key: str, api_secret: str, base_url: str = TESTNET_BASE):
        self.api_key = api_key
        self.api_secret = api_secret.encode("utf-8")
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.session.headers.update({"X-MBX-APIKEY": self.api_key})

    def _sign(self, params: dict) -> str:
        query = urlencode(params, doseq=True)
        return hmac.new(self.api_secret, query.encode("utf-8"), hashlib.sha256).hexdigest()

    def _request(self, method: str, path: str, params: dict = None, signed: bool = False):
        url = f"{self.base_url}{path}"
        params = params or {}
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["signature"] = self._sign(params)

        try:
            logger.debug("REQUEST %s %s params=%s", method, url, params)
            if method.upper() == "GET":
                r = self.session.get(url, params=params, timeout=10)
            else:
                r = self.session.post(url, params=params, timeout=10)
            logger.debug("RESPONSE %s: %s", r.status_code, r.text)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            logger.exception("HTTP request failed: %s", e)
            raise

    def place_order(self, **params):
        """Generic order placement"""
        return self._request("POST", "/fapi/v1/order", params=params, signed=True)

    def get_order(self, symbol: str, orderId: int):
        return self._request("GET", "/fapi/v1/order", params={"symbol": symbol.upper(), "orderId": orderId}, signed=True)


# --------- Bot Wrapper ---------
class TradingBot:
    def __init__(self, api_key: str, api_secret: str, base_url: str = TESTNET_BASE):
        self.client = BinanceFuturesREST(api_key, api_secret, base_url)
        logger.info("TradingBot initialized (base_url=%s)", base_url)

    def place_market_order(self, symbol: str, side: str, quantity: float):
        return self.client.place_order(symbol=symbol.upper(), side=side.upper(), type="MARKET", quantity=quantity)

    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float, tif: str = "GTC"):
        return self.client.place_order(symbol=symbol.upper(), side=side.upper(),
                                       type="LIMIT", quantity=quantity, price=price, timeInForce=tif)

    def place_stop_order(self, symbol: str, side: str, quantity: float, stop_price: float, limit_price: float, tif: str = "GTC"):
        return self.client.place_order(symbol=symbol.upper(), side=side.upper(),
                                       type="STOP", quantity=quantity, stopPrice=stop_price,
                                       price=limit_price, timeInForce=tif)


# --------- CLI ---------
def parse_args():
    p = argparse.ArgumentParser(description="Binance Futures Testnet Trading Bot")
    p.add_argument("--api-key", help="API key (or set in .env)")
    p.add_argument("--api-secret", help="API secret (or set in .env)")
    p.add_argument("--base-url", default=TESTNET_BASE, help="Base URL (default=testnet)")
    p.add_argument("--symbol", required=True, help="Symbol e.g. BTCUSDT")
    p.add_argument("--side", required=True, choices=["BUY", "SELL"], help="Order side")
    p.add_argument("--type", required=True, choices=["MARKET", "LIMIT", "STOP"], help="Order type")
    p.add_argument("--quantity", type=float, required=True, help="Order quantity")
    p.add_argument("--price", type=float, help="Price (LIMIT/STOP)")
    p.add_argument("--stop-price", type=float, help="Stop trigger price (STOP only)")
    p.add_argument("--time-in-force", choices=["GTC", "IOC", "FOK"], default="GTC")
    return p.parse_args()


def main():
    args = parse_args()

    # Load keys (priority: CLI > .env > OS env)
    api_key = args.api_key or os.getenv("BINANCE_API_KEY")
    api_secret = args.api_secret or os.getenv("BINANCE_API_SECRET")

    if not api_key or not api_secret:
        logger.error("API key and secret must be provided (CLI or .env).")
        return

    bot = TradingBot(api_key, api_secret, base_url=args.base_url)

    try:
        if args.type == "MARKET":
            result = bot.place_market_order(args.symbol, args.side, args.quantity)
        elif args.type == "LIMIT":
            if not args.price:
                logger.error("LIMIT order requires --price")
                return
            result = bot.place_limit_order(args.symbol, args.side, args.quantity, args.price, args.time_in_force)
        elif args.type == "STOP":
            if not args.stop_price or not args.price:
                logger.error("STOP order requires --stop-price and --price")
                return
            result = bot.place_stop_order(args.symbol, args.side, args.quantity, args.stop_price, args.price, args.time_in_force)
        else:
            logger.error("Unsupported order type: %s", args.type)
            return

        print("\n----- ORDER RESULT -----")
        print(result)

        if isinstance(result, dict) and result.get("orderId"):
            status = bot.client.get_order(args.symbol, result["orderId"])
            print("Order Status:", status.get("status"))

    except Exception as e:
        logger.error("Order failed: %s", e)


if __name__ == "__main__":
    main()
