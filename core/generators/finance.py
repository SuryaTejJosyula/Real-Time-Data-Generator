"""
Finance & Banking industry generators — 6 use cases.
"""

import random
import uuid
from datetime import datetime, timezone

from faker import Faker

from core.generators.base import BaseGenerator, UseCase

_fake = Faker()

_CURRENCIES = ["USD", "EUR", "GBP", "JPY", "CHF", "AUD", "CAD", "CNY", "INR", "BRL"]
_EXCHANGES  = ["NYSE", "NASDAQ", "LSE", "TSE", "HKEX", "BSE", "ASX", "NSE", "Euronext"]


# ── 1 · Stock Trades ──────────────────────────────────────────────────────────

class StockTradeGenerator(BaseGenerator):
    SIDES  = ["BUY", "SELL"]
    TYPES  = ["MARKET", "LIMIT", "STOP", "STOP_LIMIT", "TRAILING_STOP"]
    STATUS = ["FILLED", "PARTIAL", "PENDING", "CANCELLED", "REJECTED"]
    TICKERS = ["AAPL", "MSFT", "AMZN", "GOOGL", "TSLA", "META", "NVDA", "JPM",
               "BAC", "GS", "MS", "V", "MA", "PFE", "JNJ", "XOM"]

    def generate(self) -> dict:
        qty   = random.randint(1, 5000)
        price = round(random.uniform(5.0, 900.0), 2)
        return {
            "trade_id":   str(uuid.uuid4()),
            "timestamp":  datetime.now(timezone.utc).isoformat(),
            "ticker":     random.choice(self.TICKERS),
            "exchange":   random.choice(_EXCHANGES),
            "side":       random.choice(self.SIDES),
            "order_type": random.choice(self.TYPES),
            "quantity":   qty,
            "price":      price,
            "value":      round(qty * price, 2),
            "status":     random.choice(self.STATUS),
            "trader_id":  f"TRD-{random.randint(1, 10000):06d}",
            "account_id": f"ACC-{random.randint(1, 100000):08d}",
        }


# ── 2 · Card Transactions ─────────────────────────────────────────────────────

class CardTransactionGenerator(BaseGenerator):
    CARD_TYPES = ["Visa", "Mastercard", "Amex", "Discover"]
    MCC_CODES  = {
        "Grocery": 5411, "Gas": 5541, "Restaurant": 5812, "Retail": 5999,
        "Travel": 4511, "Entertainment": 7999, "Healthcare": 8099
    }

    def generate(self) -> dict:
        mcc_cat  = random.choice(list(self.MCC_CODES.keys()))
        approved = random.random() > 0.03
        return {
            "txn_id":       str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "card_type":    random.choice(self.CARD_TYPES),
            "card_last4":   f"{random.randint(1000, 9999)}",
            "merchant":     _fake.company(),
            "merchant_city": _fake.city(),
            "merchant_country": _fake.country_code(),
            "mcc":          self.MCC_CODES[mcc_cat],
            "mcc_category": mcc_cat,
            "amount":       round(random.uniform(1.0, 4999.99), 2),
            "currency":     random.choice(_CURRENCIES),
            "approved":     approved,
            "decline_code": None if approved else random.choice(["NSF", "STOLEN", "EXPIRED", "FRAUD"]),
        }


# ── 3 · Fraud Events ──────────────────────────────────────────────────────────

class FraudEventGenerator(BaseGenerator):
    TYPES   = ["Velocity_Check", "Geo_Anomaly", "Device_Mismatch", "Amount_Spike",
               "After_Hours", "Black_List_Match", "CNP_Suspicious", "Account_Takeover"]
    ACTIONS = ["BLOCK", "FLAG_REVIEW", "CHALLENGE_3DS", "ALLOW_WITH_FLAG", "ESCALATE"]

    def generate(self) -> dict:
        score = round(random.uniform(0.0, 1.0), 4)
        return {
            "alert_id":     str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "account_id":   f"ACC-{random.randint(1, 100000):08d}",
            "fraud_type":   random.choice(self.TYPES),
            "risk_score":   score,
            "threshold":    0.75,
            "action_taken": random.choice(self.ACTIONS) if score > 0.60 else "NONE",
            "txn_amount":   round(random.uniform(50.0, 9999.99), 2),
            "channel":      random.choice(["Mobile", "Web", "ATM", "POS", "Wire"]),
            "ip_address":   _fake.ipv4(),
            "device_id":    str(uuid.uuid4())[:8],
        }


# ── 4 · FX Currency Rates ─────────────────────────────────────────────────────

class FXRateGenerator(BaseGenerator):
    PAIRS = ["EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF", "AUD/USD",
             "USD/CAD", "NZD/USD", "EUR/GBP", "USD/CNY", "USD/INR"]

    def generate(self) -> dict:
        mid   = round(random.uniform(0.60, 160.0), 5)
        spread = round(random.uniform(0.00010, 0.00050), 5)
        return {
            "tick_id":   str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "pair":      random.choice(self.PAIRS),
            "bid":       round(mid - spread, 5),
            "ask":       round(mid + spread, 5),
            "mid":       mid,
            "spread":    round(spread * 2, 5),
            "provider":  random.choice(["Bloomberg", "Reuters", "IG", "Oanda", "XE"]),
            "volume_24h": random.randint(1_000_000, 5_000_000_000),
        }


# ── 5 · Loan Applications ─────────────────────────────────────────────────────

class LoanApplicationGenerator(BaseGenerator):
    TYPES    = ["Personal", "Mortgage", "Auto", "Business", "Student", "HELOC"]
    STATUSES = ["SUBMITTED", "UNDER_REVIEW", "APPROVED", "CONDITIONAL", "DECLINED", "WITHDRAWN"]

    def generate(self) -> dict:
        amount = round(random.uniform(1000, 1_000_000), 2)
        return {
            "app_id":       str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "customer_id":  f"CUST-{random.randint(1, 1_000_000):08d}",
            "loan_type":    random.choice(self.TYPES),
            "amount":       amount,
            "term_months":  random.choice([12, 24, 36, 48, 60, 120, 180, 240, 360]),
            "interest_rate": round(random.uniform(2.5, 24.9), 2),
            "credit_score": random.randint(300, 850),
            "dti_ratio":    round(random.uniform(0.05, 0.65), 3),
            "status":       random.choice(self.STATUSES),
            "branch_id":    f"BR-{random.randint(1, 300):04d}",
        }


# ── 6 · ATM Withdrawals ───────────────────────────────────────────────────────

class ATMWithdrawalGenerator(BaseGenerator):
    STATUSES = ["SUCCESS", "DECLINED", "TIMEOUT", "CARD_RETAINED", "INSUFFICIENT_FUNDS"]

    def generate(self) -> dict:
        return {
            "txn_id":      str(uuid.uuid4()),
            "timestamp":   datetime.now(timezone.utc).isoformat(),
            "atm_id":      f"ATM-{random.randint(1, 5000):05d}",
            "atm_city":    _fake.city(),
            "account_id":  f"ACC-{random.randint(1, 100000):08d}",
            "card_last4":  f"{random.randint(1000, 9999)}",
            "amount":      random.choice([20, 40, 60, 80, 100, 200, 300, 500]),
            "currency":    "USD",
            "balance_after": round(random.uniform(0, 50000), 2),
            "status":      random.choice(self.STATUSES),
            "network":     random.choice(["Visa", "Mastercard", "Cirrus", "Plus"]),
        }


# ── USE_CASES registry ────────────────────────────────────────────────────────

USE_CASES = [
    UseCase(
        id="fin_trades",
        title="Stock Trades",
        description="High-frequency equity trade events with ticker, price, quantity, order type, and fill status.",
        schema_preview='{ "ticker", "side", "quantity", "price", "value", "status" }',
        generator_class=StockTradeGenerator,
    ),
    UseCase(
        id="fin_cards",
        title="Card Transactions",
        description="Real-time card payment events including merchant, MCC category, amount, currency, and approval.",
        schema_preview='{ "card_type", "merchant", "amount", "currency", "approved" }',
        generator_class=CardTransactionGenerator,
    ),
    UseCase(
        id="fin_fraud",
        title="Fraud Detection Events",
        description="ML-scored fraud alerts with risk score, fraud type, action taken, channel, and device fingerprint.",
        schema_preview='{ "fraud_type", "risk_score", "action_taken", "txn_amount", "channel" }',
        generator_class=FraudEventGenerator,
    ),
    UseCase(
        id="fin_fx",
        title="FX Currency Rates",
        description="Foreign exchange tick data across major pairs — bid, ask, mid, spread from multiple providers.",
        schema_preview='{ "pair", "bid", "ask", "mid", "spread", "provider" }',
        generator_class=FXRateGenerator,
    ),
    UseCase(
        id="fin_loans",
        title="Loan Applications",
        description="Loan application lifecycle events with type, amount, credit score, DTI, and approval status.",
        schema_preview='{ "loan_type", "amount", "credit_score", "dti_ratio", "status" }',
        generator_class=LoanApplicationGenerator,
    ),
    UseCase(
        id="fin_atm",
        title="ATM Withdrawals",
        description="ATM transaction events including location, withdrawal amount, balance, and decline reasons.",
        schema_preview='{ "atm_id", "atm_city", "amount", "balance_after", "status" }',
        generator_class=ATMWithdrawalGenerator,
    ),
]
