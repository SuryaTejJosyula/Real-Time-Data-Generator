"""
Retail industry generators — 6 use cases.
"""

import random
import uuid
from datetime import datetime, timezone

from faker import Faker

from core.generators.base import BaseGenerator, UseCase

_fake = Faker()


# ── 1 · POS Transactions ──────────────────────────────────────────────────────

class POSTransactionGenerator(BaseGenerator):
    CATEGORIES = ["Electronics", "Clothing", "Grocery", "Home & Garden", "Sports", "Toys", "Beauty"]
    PAYMENT    = ["Credit Card", "Debit Card", "Cash", "Mobile Pay", "Gift Card"]

    def generate(self) -> dict:
        qty = random.randint(1, 8)
        price = round(random.uniform(2.50, 299.99), 2)
        return {
            "transaction_id": str(uuid.uuid4()),
            "timestamp":      datetime.now(timezone.utc).isoformat(),
            "store_id":       f"STORE-{random.randint(1, 500):04d}",
            "terminal_id":    f"POS-{random.randint(1, 20):02d}",
            "customer_id":    f"CUST-{random.randint(1, 100000):07d}",
            "item_count":     qty,
            "unit_price":     price,
            "total_amount":   round(qty * price, 2),
            "category":       random.choice(self.CATEGORIES),
            "payment_method": random.choice(self.PAYMENT),
            "cashier_id":     f"EMP-{random.randint(1, 200):04d}",
        }


# ── 2 · Inventory Changes ─────────────────────────────────────────────────────

class InventoryChangeGenerator(BaseGenerator):
    ACTIONS = ["RESTOCK", "SALE", "RETURN", "SHRINKAGE", "TRANSFER_IN", "TRANSFER_OUT"]

    def generate(self) -> dict:
        return {
            "event_id":   str(uuid.uuid4()),
            "timestamp":  datetime.now(timezone.utc).isoformat(),
            "sku":        f"SKU-{random.randint(10000, 99999)}",
            "product":    _fake.catch_phrase(),
            "store_id":   f"STORE-{random.randint(1, 500):04d}",
            "action":     random.choice(self.ACTIONS),
            "quantity":   random.randint(1, 500),
            "stock_after": random.randint(0, 2000),
            "warehouse":  f"WH-{random.randint(1, 20):02d}",
        }


# ── 3 · Customer Footfall ─────────────────────────────────────────────────────

class FootfallGenerator(BaseGenerator):
    ZONES = ["Entrance", "Electronics", "Checkout", "Cafe", "Clothing", "Exit"]

    def generate(self) -> dict:
        return {
            "sensor_id":   f"SENSOR-{random.randint(1, 100):03d}",
            "timestamp":   datetime.now(timezone.utc).isoformat(),
            "store_id":    f"STORE-{random.randint(1, 200):04d}",
            "zone":        random.choice(self.ZONES),
            "count_in":    random.randint(0, 15),
            "count_out":   random.randint(0, 15),
            "current_occupancy": random.randint(10, 800),
            "dwell_time_sec": random.randint(30, 900),
        }


# ── 4 · Cart Abandonment ──────────────────────────────────────────────────────

class CartAbandonmentGenerator(BaseGenerator):
    PAGES = ["product_page", "cart", "checkout", "payment", "shipping"]

    def generate(self) -> dict:
        items = random.randint(1, 10)
        return {
            "session_id":      str(uuid.uuid4()),
            "timestamp":       datetime.now(timezone.utc).isoformat(),
            "customer_id":     f"CUST-{random.randint(1, 100000):07d}",
            "cart_value":      round(random.uniform(5.0, 599.99), 2),
            "items_in_cart":   items,
            "last_page":       random.choice(self.PAGES),
            "session_duration_sec": random.randint(30, 1800),
            "device":          random.choice(["Mobile", "Desktop", "Tablet"]),
            "utm_source":      random.choice(["direct", "google", "email", "social"]),
        }


# ── 5 · Loyalty Points Events ─────────────────────────────────────────────────

class LoyaltyPointsGenerator(BaseGenerator):
    EVENTS = ["EARN", "REDEEM", "EXPIRE", "BONUS", "TIER_UPGRADE"]
    TIERS  = ["Bronze", "Silver", "Gold", "Platinum"]

    def generate(self) -> dict:
        event = random.choice(self.EVENTS)
        pts   = random.randint(5, 5000)
        return {
            "event_id":     str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "customer_id":  f"CUST-{random.randint(1, 100000):07d}",
            "event_type":   event,
            "points":       pts if event in ("EARN", "BONUS") else -pts,
            "balance_after": random.randint(0, 50000),
            "tier":         random.choice(self.TIERS),
            "store_id":     f"STORE-{random.randint(1, 500):04d}",
        }


# ── 6 · Price Change Events ───────────────────────────────────────────────────

class PriceChangeGenerator(BaseGenerator):
    REASONS = ["Markdown", "Competitor Match", "Seasonal", "Clearance", "Promo", "Regular"]

    def generate(self) -> dict:
        old_p = round(random.uniform(5.0, 499.99), 2)
        ch    = round(random.uniform(-0.40, 0.20), 3)
        return {
            "event_id":     str(uuid.uuid4()),
            "timestamp":    datetime.now(timezone.utc).isoformat(),
            "sku":          f"SKU-{random.randint(10000, 99999)}",
            "category":     random.choice(POSTransactionGenerator.CATEGORIES),
            "old_price":    old_p,
            "new_price":    round(old_p * (1 + ch), 2),
            "change_pct":   round(ch * 100, 1),
            "reason":       random.choice(self.REASONS),
            "effective_date": datetime.now(timezone.utc).date().isoformat(),
            "store_id":     f"STORE-{random.randint(1, 500):04d}",
        }


# ── USE_CASES registry ────────────────────────────────────────────────────────

USE_CASES = [
    UseCase(
        id="retail_pos",
        title="POS Transactions",
        description="Live point-of-sale transaction events from retail stores including item details, payment method, and cashier.",
        schema_preview='{ "transaction_id", "store_id", "total_amount", "category", "payment_method" }',
        generator_class=POSTransactionGenerator,
    ),
    UseCase(
        id="retail_inventory",
        title="Inventory Changes",
        description="Real-time stock movement events including restocks, sales deductions, returns, and transfers.",
        schema_preview='{ "sku", "store_id", "action", "quantity", "stock_after" }',
        generator_class=InventoryChangeGenerator,
    ),
    UseCase(
        id="retail_footfall",
        title="Customer Footfall",
        description="In-store sensor counts tracking how many customers enter/exit each zone and current occupancy.",
        schema_preview='{ "sensor_id", "zone", "count_in", "count_out", "current_occupancy" }',
        generator_class=FootfallGenerator,
    ),
    UseCase(
        id="retail_cart",
        title="Cart Abandonment",
        description="E-commerce session events where customers leave without completing checkout, with cart value and last page.",
        schema_preview='{ "session_id", "cart_value", "items_in_cart", "last_page", "device" }',
        generator_class=CartAbandonmentGenerator,
    ),
    UseCase(
        id="retail_loyalty",
        title="Loyalty Points Events",
        description="Customer loyalty programme events — earn, redeem, expire, bonus, and tier upgrades.",
        schema_preview='{ "customer_id", "event_type", "points", "balance_after", "tier" }',
        generator_class=LoyaltyPointsGenerator,
    ),
    UseCase(
        id="retail_price",
        title="Price Change Events",
        description="Automated price adjustment events with reason codes, old vs new price, and effective dates.",
        schema_preview='{ "sku", "old_price", "new_price", "change_pct", "reason" }',
        generator_class=PriceChangeGenerator,
    ),
]
