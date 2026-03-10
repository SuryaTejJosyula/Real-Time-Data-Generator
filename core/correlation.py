"""
Shared ID pools for cross-use-case correlation within each industry.

Generator files import these pools so events from different use cases in the
same industry share consistent entity identifiers, enabling JOIN operations and
holistic dashboards in Fabric / downstream systems.

Correlation keys by industry
─────────────────────────────
RETAIL
  customer_id  →  POS ↔ Cart ↔ Loyalty
  store_id     →  POS ↔ Inventory ↔ Footfall ↔ Loyalty ↔ Price
  sku          →  Inventory ↔ Price

HEALTHCARE
  patient_id   →  Vitals ↔ ER ↔ Medication ↔ Lab ↔ DeviceAlert ↔ Appointment
  device_id    →  Vitals ↔ DeviceAlert  (unified prefix DEV-)
  doctor_id    →  ER (attending_id) ↔ Medication (prescriber_id) ↔ Appointment (doctor_id)

FINANCE
  account_id   →  Trades ↔ Fraud ↔ ATM
  customer_id  →  Loans ↔ Cards
  card_last4   →  Cards ↔ ATM

MANUFACTURING
  machine_id   →  Sensors ↔ Energy ↔ Maintenance
  line_id      →  Sensors ↔ Defects ↔ Throughput
  plant        →  All 6 use cases
  batch_id     →  Defects ↔ Materials

TRANSPORTATION
  vehicle_id   →  GPS ↔ Driver ↔ Fuel
  driver_id    →  GPS ↔ Driver
  shipment_id  →  Package ↔ Cargo

ENERGY
  meter_id     →  SmartMeter (pool)
  grid_id      →  GridLoad ↔ Outage
  region       →  GridLoad ↔ Renewable ↔ Pipeline ↔ Outage ↔ Forecast
  account_id   →  SmartMeter (pool)

TELECOM
  cell_id      →  CDR ↔ DataUsage ↔ SMS
  subscriber_id→  DataUsage ↔ Churn
  node_id      →  Traffic ↔ Faults

SMART_CITY
  city         →  All 6 use cases
  district     →  Traffic ↔ Air ↔ Waste ↔ Environment ↔ Transit ↔ Parking

IT
  host         →  Security ↔ System
  username     →  Security (user) ↔ Audit (actor_id)
  internal_ip  →  Audit (ip_address) ↔ Security (dest_ip)
  session_id   →  Audit ↔ Security
"""

# ── RETAIL ───────────────────────────────────────────────────────────────────

RETAIL = {
    "customer_ids": [f"CUST-{i:07d}" for i in range(1, 501)],       # 500 customers
    "store_ids":    [f"STORE-{i:04d}" for i in range(1, 51)],        # 50 stores
    "skus":         [f"SKU-{i:05d}" for i in range(10001, 12001)],   # 2 000 SKUs
}

# ── HEALTHCARE ───────────────────────────────────────────────────────────────

HEALTHCARE = {
    "patient_ids": [f"PT-{i:06d}" for i in range(100001, 100501)],   # 500 patients
    "device_ids":  [f"DEV-{i:04d}" for i in range(1, 201)],          # 200 devices
    "doctor_ids":  [f"DR-{i:03d}" for i in range(1, 101)],           # 100 doctors
}

# ── FINANCE ──────────────────────────────────────────────────────────────────

FINANCE = {
    "account_ids":  [f"ACC-{i:08d}" for i in range(1, 10001)],       # 10 000 accounts
    "customer_ids": [f"CUST-{i:08d}" for i in range(1, 10001)],      # 10 000 customers
    "card_last4s":  [f"{i:04d}" for i in range(1000, 1300)],          # 300 card numbers
}

# ── MANUFACTURING ─────────────────────────────────────────────────────────────

MANUFACTURING = {
    "machine_ids": [f"MACH-{i:04d}" for i in range(1, 201)],         # 200 machines
    "line_ids":    [f"LINE-{i:02d}" for i in range(1, 21)],           # 20 lines
    "plants":      [f"PLANT-{i:02d}" for i in range(1, 6)],           # 5 plants
    "batch_ids":   [f"BATCH-{i:06d}" for i in range(100001, 100501)], # 500 batches
}

# ── TRANSPORTATION ────────────────────────────────────────────────────────────

TRANSPORTATION = {
    "vehicle_ids":  [f"VEH-{i:05d}" for i in range(1, 501)],         # 500 vehicles
    "driver_ids":   [f"DRV-{i:05d}" for i in range(1, 201)],         # 200 drivers
    "shipment_ids": [f"SHP-{i:06d}" for i in range(100001, 100301)],  # 300 shipments
}

# ── ENERGY ───────────────────────────────────────────────────────────────────

ENERGY = {
    "meter_ids":   [f"MTR-{i:07d}" for i in range(1, 201)],          # 200 meters
    "grid_ids":    [f"GRID-{i:03d}" for i in range(1, 31)],           # 30 grids
    "regions":     ["North", "South", "East", "West", "Central"],
    "account_ids": [f"ACC-{i:08d}" for i in range(1, 5001)],          # 5 000 accounts
}

# ── TELECOM ──────────────────────────────────────────────────────────────────

TELECOM = {
    "cell_ids":       [f"CELL-{i:05d}" for i in range(1, 5001)],     # 5 000 cells
    "subscriber_ids": [f"SUB-{i:09d}" for i in range(1, 1001)],      # 1 000 subscribers
    "node_ids":       [f"NODE-{i:05d}" for i in range(1, 201)],       # 200 nodes
}

# ── SMART CITY ───────────────────────────────────────────────────────────────

SMART_CITY = {
    "cities":    ["Chicago", "London", "Singapore", "Dubai",
                  "Berlin", "Tokyo", "Sydney", "Toronto"],
    "districts": ["Downtown", "Midtown", "Suburbs", "Industrial",
                  "Airport", "Port", "University"],
}

# ── IT / INFORMATION TECHNOLOGY ──────────────────────────────────────────────

IT = {
    "hosts":        [f"srv-{i:03d}.corp.local" for i in range(1, 51)],   # 50 servers
    "usernames":    [f"user{i:03d}" for i in range(1, 101)],              # 100 users
    "actor_ids":    [f"USR-{i:04d}" for i in range(1001, 1101)],          # 100 audit actors
    "internal_ips": [f"10.0.{i // 100}.{i % 100 + 1}" for i in range(100)],  # /16 subnet
    "session_ids":  [f"SES-{i:06d}" for i in range(1, 501)],              # 500 sessions
}
