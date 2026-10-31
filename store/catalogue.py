"""Demo catalogue data (no Django imports so scripts can reuse it)."""

# (name, price, stock, description, fallback emoji, online photo id)
CATALOGUE = {
    "Coffee & Tea": [
        ("Suffolk Blend Coffee Beans 500g", 8.99, 120, "Medium roast, notes of chocolate and hazelnut.", "☕", "photo-1559056199-641a0ac8b55e"),
        ("Single Origin Ethiopian 250g", 7.49, 80, "Bright, floral and fruity light roast.", "🫘", "photo-1447933601403-0c6688de566e"),
        ("English Breakfast Tea (80 bags)", 4.25, 200, "Classic strong black tea.", "🍵", "photo-1564890369478-c89ca6d9cde9"),
        ("Matcha Green Tea Powder 100g", 12.50, 60, "Ceremonial-grade Japanese matcha.", "🌿", "photo-1515823064-d6e0c04616a7"),
    ],
    "Kitchen": [
        ("Ceramic Pour-Over Dripper", 18.00, 40, "Hand-finished dripper for a clean cup.", "🫗", "photo-1495474472287-4d71bcdd2085"),
        ("Cast Iron Skillet 26cm", 34.99, 25, "Pre-seasoned, oven and hob safe.", "🍳", "photo-1584990347449-a5d9f800a783"),
        ("Bamboo Chopping Board", 14.50, 70, "Sustainable bamboo, juice groove.", "🔪", "photo-1594137898440-8ba7ccd5cb4a"),
        ("Stainless Steel Kettle 1.7L", 29.00, 35, "Rapid boil, auto shut-off.", "🫖", "photo-1594213114663-d94db9b17125"),
    ],
    "Home & Living": [
        ("Soy Wax Candle - Cedar & Sea Salt", 11.99, 90, "Hand-poured, 40 hour burn time.", "🕯️", "photo-1602874801007-bd458bb1b8b6"),
        ("Linen Cushion Cover 45x45", 15.00, 55, "Stonewashed European linen.", "🛋️", "photo-1584100936595-c0654b55a2e6"),
        ("Ceramic Plant Pot - Medium", 13.75, 65, "Matte glaze with drainage tray.", "🪴", "photo-1485955900006-10f4d324d411"),
        ("Wool Throw Blanket", 49.00, 20, "Soft merino blend, 130x170cm.", "🧶", "photo-1580301762395-21ce84d00bc6"),
    ],
}

CATEGORY_COLOURS = {
    "Coffee & Tea": ("#92400e", "#f59e0b"),
    "Kitchen": ("#1e3a8a", "#60a5fa"),
    "Home & Living": ("#065f46", "#34d399"),
}
