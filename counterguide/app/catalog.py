"""Schema and the SAMPLE catalog for the CounterGuide demo.

These products are demo assumptions, not AnyCompany's real catalog. The four
categories (electronics, cell phones, hobby equipment, batteries) are facts
from the problem statement.
"""

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS products (
    sku         TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    category    TEXT NOT NULL,
    description TEXT NOT NULL,
    price       NUMERIC(10,2) NOT NULL,
    stock       INTEGER NOT NULL DEFAULT 0,
    tags        TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS request_log (
    id          BIGSERIAL PRIMARY KEY,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    request_id  TEXT NOT NULL,
    path        TEXT NOT NULL,
    status      INTEGER NOT NULL,
    tier        TEXT NOT NULL,
    latency_ms  INTEGER NOT NULL,
    detail      TEXT NOT NULL DEFAULT '',
    simulated   BOOLEAN NOT NULL DEFAULT false
);
CREATE INDEX IF NOT EXISTS request_log_created_at ON request_log (created_at DESC);
"""

# (sku, name, category, description, price, stock, tags)
CATALOG_ROWS = [
    # Hobby equipment
    ("HB-RC-TRUCK1", "Trailblazer 1:18 Beginner RC Truck Kit", "hobby equipment",
     "Ready-to-run beginner RC truck. Uses one 7.2V NiMH stick pack with a Tamiya-style connector. Battery and charger sold separately.",
     89.99, 14, "rc,beginner,kit,7.2v,nimh"),
    ("HB-RC-BUGGY2", "Dustrunner 1:16 Beginner RC Buggy", "hobby equipment",
     "Beginner off-road buggy. Uses one 7.2V NiMH stick pack with a Tamiya-style connector. Battery and charger sold separately.",
     99.99, 9, "rc,beginner,kit,7.2v,nimh"),
    ("HB-RC-LIPO-ADV", "Velocity 1:10 Advanced RC Car (LiPo)", "hobby equipment",
     "Advanced RC car for experienced drivers. Requires a 2S 7.4V LiPo pack and a LiPo balance charger. Not a beginner kit.",
     219.99, 4, "rc,advanced,lipo,2s"),
    ("HB-TX-AAPACK", "RC Transmitter (takes 4x AA)", "hobby equipment",
     "Replacement handheld transmitter for the beginner trucks. Powered by four AA cells in the transmitter only.",
     24.99, 11, "rc,transmitter,aa"),
    # Batteries
    ("BT-NIMH-72", "7.2V 3000mAh NiMH Stick Pack (Tamiya)", "batteries",
     "Approved drive battery for beginner RC trucks and buggies. Matches the Tamiya-style connector.",
     29.99, 32, "nimh,7.2v,rc,drive-battery"),
    ("BT-LIPO-2S", "7.4V 2S 5000mAh LiPo Pack (hard case)", "batteries",
     "LiPo drive pack for advanced RC cars. Requires a LiPo balance charger and a LiPo-safe charging bag.",
     54.99, 12, "lipo,2s,7.4v,rc,drive-battery"),
    ("BT-AA-ALK8", "AA Alkaline Cells, 8-pack (loose)", "batteries",
     "Loose single-use AA cells for remotes, transmitters, flashlights and small electronics.",
     8.99, 120, "aa,alkaline,loose"),
    ("BT-AA-NIMH4", "AA Rechargeable NiMH Cells, 4-pack (loose)", "batteries",
     "Loose rechargeable AA cells for transmitters and household devices.",
     14.99, 40, "aa,nimh,loose,rechargeable"),
    ("BT-CHG-NIMH", "Smart NiMH Peak-Detect Charger", "batteries",
     "Charger for 6-8.4V NiMH stick packs with a Tamiya-style connector. Stops automatically when the pack is full.",
     34.99, 18, "charger,nimh,rc"),
    ("BT-CHG-LIPO", "LiPo Balance Charger 2S-4S", "batteries",
     "Balance charger for 2S-4S LiPo packs. Use with a LiPo-safe charging bag.",
     59.99, 7, "charger,lipo,balance"),
    ("BT-BAG-LIPO", "LiPo-Safe Charging Bag", "batteries",
     "Fire-resistant bag for charging and storing LiPo packs.",
     12.99, 25, "lipo,safety,bag"),
    # Cell phones
    ("CP-PHONE-A15", "Nova A15 Smartphone 128GB", "cell phones",
     "Unlocked smartphone with a 5000mAh built-in battery and USB-C fast charging.",
     249.99, 20, "phone,usb-c"),
    ("CP-CHG-USBC20", "20W USB-C Wall Charger", "cell phones",
     "Certified 20W USB-C power adapter for phones and small electronics.",
     19.99, 60, "charger,usb-c,phone"),
    ("CP-CASE-A15", "Rugged Case for Nova A15", "cell phones",
     "Drop-resistant case for the Nova A15.",
     17.99, 35, "case,phone"),
    # Electronics
    ("EL-BTSPK-01", "Pocket Bluetooth Speaker", "electronics",
     "Portable speaker with a built-in rechargeable battery and USB-C charging.",
     39.99, 22, "speaker,bluetooth,usb-c"),
    ("EL-PWRBNK-10K", "10,000mAh Power Bank", "electronics",
     "USB-C power bank for phones and small electronics. Airline carry-on friendly (under 100Wh).",
     29.99, 30, "power-bank,usb-c"),
]
