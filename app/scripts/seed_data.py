"""Seed database with sample categories, products, reviews, promotions, and testimonials."""

import asyncio
import os
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from shared.models import (
    Category,
    Coupon,
    Product,
    Promotion,
    Review,
    Testimonial,
)

DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://shopcloud:localdev@localhost:5432/shopcloud"
)

# Media lives in frontend/media/ which deploy-frontend.sh syncs to S3.
# CloudFront serves these paths as /media/... in production.
MEDIA_BASE = "/media"


def m(*parts: str) -> str:
    return "/".join([MEDIA_BASE, *parts])


CATEGORIES = [
    {
        "name": "Electronics",
        "description": "Smartphones, laptops, gadgets and accessories",
    },
    {"name": "Clothing", "description": "Men's and women's fashion apparel"},
    {
        "name": "Home & Kitchen",
        "description": "Furniture, appliances and home essentials",
    },
    {
        "name": "Sports & Outdoors",
        "description": "Athletic gear, camping and fitness equipment",
    },
    {"name": "Books", "description": "Fiction, non-fiction, textbooks and more"},
    {
        "name": "Beauty & Health",
        "description": "Skincare, supplements and personal care",
    },
]


def _images_for(slug: str) -> list[str]:
    return [
        m("products", f"{slug}-1.svg"),
        m("products", f"{slug}-2.svg"),
        m("products", f"{slug}-3.svg"),
        m("products", f"{slug}-4.svg"),
    ]


PRODUCTS = [
    {
        "slug": "headphones",
        "name": "Wireless Bluetooth Headphones",
        "description": "Noise-cancelling over-ear headphones with 30-hour battery life and premium memory-foam cushions.",
        "price": 79.99,
        "category": "Electronics",
        "stock_quantity": 150,
        "sales_count": 420,
        "attributes": {
            "color": "Black",
            "brand": "SoundMax",
            "wireless": True,
            "battery_hours": 30,
        },
    },
    {
        "slug": "charger",
        "name": "USB-C Fast Charger",
        "description": "65W GaN charger compatible with laptops and phones. Dual-port, foldable prongs, travel-ready.",
        "price": 34.99,
        "category": "Electronics",
        "stock_quantity": 300,
        "sales_count": 880,
        "attributes": {"wattage": 65, "ports": 2, "type": "GaN"},
    },
    {
        "slug": "keyboard",
        "name": "Mechanical Keyboard RGB",
        "description": "RGB backlit mechanical keyboard with hot-swappable Cherry MX switches and aluminum frame.",
        "price": 129.99,
        "category": "Electronics",
        "stock_quantity": 80,
        "sales_count": 210,
        "attributes": {
            "switch_type": "Cherry MX Blue",
            "layout": "Full-size",
            "backlit": "RGB",
        },
    },
    {
        "slug": "ssd",
        "name": "Portable SSD 1TB",
        "description": "USB 3.2 portable solid state drive with read speeds up to 1050MB/s. Shock-resistant aluminum shell.",
        "price": 89.99,
        "category": "Electronics",
        "stock_quantity": 200,
        "sales_count": 540,
        "attributes": {
            "capacity": "1TB",
            "interface": "USB 3.2",
            "read_speed": "1050MB/s",
        },
    },
    {
        "slug": "smartwatch",
        "name": "Smart Watch Pro",
        "description": "Fitness tracker with heart-rate monitor, GPS, and 7-day battery. Swim-proof, syncs to iOS/Android.",
        "price": 199.99,
        "category": "Electronics",
        "stock_quantity": 60,
        "sales_count": 330,
        "attributes": {"color": "Silver", "battery_days": 7, "waterproof": "5ATM"},
    },
    {
        "slug": "tshirt",
        "name": "Classic Cotton T-Shirt",
        "description": "100% organic cotton crew-neck t-shirt, pre-shrunk, tagless neck, available in 6 colors.",
        "price": 24.99,
        "category": "Clothing",
        "stock_quantity": 500,
        "sales_count": 1240,
        "attributes": {
            "gender": "women",
            "color": "White",
            "size": "M",
            "material": "100% Organic Cotton",
        },
    },
    {
        "slug": "jeans",
        "name": "Slim Fit Denim Jeans",
        "description": "Stretch denim jeans with modern slim fit. Reinforced pockets, button fly, sustainable wash.",
        "price": 59.99,
        "category": "Clothing",
        "stock_quantity": 250,
        "sales_count": 670,
        "attributes": {
            "gender": "men",
            "color": "Dark Blue",
            "size": "32",
            "material": "98% Cotton, 2% Elastane",
        },
    },
    {
        "slug": "jacket",
        "name": "Lightweight Running Jacket",
        "description": "Water-resistant windbreaker with reflective details and packable hood. Perfect for morning runs.",
        "price": 74.99,
        "category": "Clothing",
        "stock_quantity": 120,
        "sales_count": 290,
        "attributes": {
            "gender": "men",
            "color": "Navy",
            "size": "L",
            "material": "Nylon",
            "waterproof": True,
        },
    },
    {
        "slug": "sweater",
        "name": "Wool Blend Sweater",
        "description": "Cozy merino wool-blend crew-neck sweater. Pilling-resistant yarn, ribbed hem and cuffs.",
        "price": 89.99,
        "category": "Clothing",
        "stock_quantity": 90,
        "sales_count": 180,
        "attributes": {
            "gender": "women",
            "color": "Charcoal",
            "size": "M",
            "material": "70% Merino Wool, 30% Nylon",
        },
    },
    {
        "slug": "waterbottle",
        "name": "Stainless Steel Water Bottle",
        "description": "Double-wall vacuum-insulated 750ml bottle. Keeps drinks cold 24h, hot 12h. Leak-proof lid.",
        "price": 29.99,
        "category": "Home & Kitchen",
        "stock_quantity": 400,
        "sales_count": 1560,
        "attributes": {
            "capacity": "750ml",
            "material": "Stainless Steel",
            "insulated": True,
        },
    },
    {
        "slug": "cookware",
        "name": "Non-Stick Cookware Set",
        "description": "10-piece ceramic non-stick cookware set with tempered-glass lids. Oven-safe to 500°F.",
        "price": 149.99,
        "category": "Home & Kitchen",
        "stock_quantity": 45,
        "sales_count": 95,
        "attributes": {
            "pieces": 10,
            "material": "Ceramic Non-Stick",
            "dishwasher_safe": True,
        },
    },
    {
        "slug": "lamp",
        "name": "LED Desk Lamp",
        "description": "Dimmable LED desk lamp with USB charging port and 5 color modes. Touch controls, memory function.",
        "price": 44.99,
        "category": "Home & Kitchen",
        "stock_quantity": 180,
        "sales_count": 410,
        "attributes": {"modes": 5, "usb_port": True, "brightness_levels": 10},
    },
    {
        "slug": "cuttingboard",
        "name": "Bamboo Cutting Board Set",
        "description": "Set of 3 organic bamboo cutting boards in different sizes. Juice grooves, non-slip feet.",
        "price": 34.99,
        "category": "Home & Kitchen",
        "stock_quantity": 220,
        "sales_count": 370,
        "attributes": {"pieces": 3, "material": "Organic Bamboo"},
    },
    {
        "slug": "yogamat",
        "name": "Yoga Mat Premium",
        "description": "6mm thick non-slip yoga mat with carrying strap. Eco-friendly TPE, double-sided texture.",
        "price": 39.99,
        "category": "Sports & Outdoors",
        "stock_quantity": 300,
        "sales_count": 720,
        "attributes": {"thickness": "6mm", "material": "TPE", "length": "183cm"},
    },
    {
        "slug": "dumbbells",
        "name": "Adjustable Dumbbell Set",
        "description": "Pair of adjustable dumbbells, 5-25 lbs each. Dial-a-weight mechanism saves space.",
        "price": 179.99,
        "category": "Sports & Outdoors",
        "stock_quantity": 35,
        "sales_count": 110,
        "attributes": {"weight_range": "5-25 lbs", "adjustable": True, "pair": True},
    },
    {
        "slug": "backpack",
        "name": "Camping Backpack 50L",
        "description": "Waterproof hiking backpack with rain cover, hip belt, and hydration sleeve. Lightweight 1.2kg.",
        "price": 99.99,
        "category": "Sports & Outdoors",
        "stock_quantity": 70,
        "sales_count": 200,
        "attributes": {"capacity": "50L", "waterproof": True, "weight": "1.2kg"},
    },
    {
        "slug": "bands",
        "name": "Resistance Bands Set",
        "description": "Set of 5 latex resistance bands with different tension levels. Door anchor, handles, carry bag.",
        "price": 19.99,
        "category": "Sports & Outdoors",
        "stock_quantity": 450,
        "sales_count": 960,
        "attributes": {"pieces": 5, "material": "Natural Latex"},
    },
    {
        "slug": "cleancode",
        "name": "Clean Code",
        "description": "A Handbook of Agile Software Craftsmanship by Robert C. Martin. Signed first printing.",
        "price": 37.99,
        "category": "Books",
        "stock_quantity": 100,
        "sales_count": 340,
        "attributes": {
            "author": "Robert C. Martin",
            "pages": 464,
            "format": "Paperback",
        },
    },
    {
        "slug": "ddia",
        "name": "Designing Data-Intensive Applications",
        "description": "The Big Ideas Behind Reliable, Scalable, and Maintainable Systems by Martin Kleppmann.",
        "price": 44.99,
        "category": "Books",
        "stock_quantity": 85,
        "sales_count": 260,
        "attributes": {
            "author": "Martin Kleppmann",
            "pages": 616,
            "format": "Paperback",
        },
    },
    {
        "slug": "pragmatic",
        "name": "The Pragmatic Programmer",
        "description": "Your Journey to Mastery, 20th Anniversary Edition. Hardcover with ribbon bookmark.",
        "price": 49.99,
        "category": "Books",
        "stock_quantity": 120,
        "sales_count": 280,
        "attributes": {
            "author": "David Thomas, Andrew Hunt",
            "pages": 352,
            "format": "Hardcover",
        },
    },
    {
        "slug": "vitaminc",
        "name": "Vitamin C Serum",
        "description": "20% Vitamin C face serum with hyaluronic acid and vitamin E. Cruelty-free, 30ml.",
        "price": 24.99,
        "category": "Beauty & Health",
        "stock_quantity": 350,
        "sales_count": 820,
        "attributes": {"volume": "30ml", "concentration": "20%"},
    },
    {
        "slug": "greentea",
        "name": "Organic Green Tea",
        "description": "100 premium organic green tea bags, individually wrapped for freshness. Fair-trade certified.",
        "price": 18.99,
        "category": "Beauty & Health",
        "stock_quantity": 500,
        "sales_count": 1420,
        "attributes": {"count": 100, "type": "Green Tea", "organic": True},
    },
    {
        "slug": "protein",
        "name": "Protein Powder Vanilla",
        "description": "Whey protein isolate, 2lb tub, 30 servings. 25g protein, 2g carbs, natural vanilla.",
        "price": 39.99,
        "category": "Beauty & Health",
        "stock_quantity": 160,
        "sales_count": 490,
        "attributes": {"weight": "2lb", "servings": 30, "protein_per_serving": "25g"},
    },
]


REVIEW_POOL = {
    5: [
        (
            "Exceeded expectations",
            "Easily the best purchase I've made this year. Shipping was fast and quality is outstanding.",
        ),
        (
            "Worth every penny",
            "Packaging was beautiful, build quality feels premium, and it performs exactly as described.",
        ),
        (
            "Highly recommend",
            "I was hesitant at first but I'm so glad I bought it. Already recommending to friends.",
        ),
        (
            "Perfect",
            "Works flawlessly. Instructions were clear and setup took under five minutes.",
        ),
        (
            "Five-star experience",
            "From ordering to unboxing, everything was seamless. I'll definitely shop here again.",
        ),
    ],
    4: [
        (
            "Really good",
            "Very happy with this. Only docking a star because the color is slightly different from the photos.",
        ),
        (
            "Solid choice",
            "Does exactly what it says. Build could be slightly more premium but the value is there.",
        ),
        (
            "Great value",
            "Honest review: good product, fair price, fast delivery. Nothing to complain about.",
        ),
    ],
    3: [
        (
            "Decent for the price",
            "It's okay. Does the job but don't expect luxury at this price point.",
        ),
        (
            "Mixed feelings",
            "Works as advertised but I had to contact support once. They resolved it quickly.",
        ),
    ],
}


AUTHOR_POOL = [
    ("Alex Rivera", True),
    ("Priya Shah", True),
    ("Jordan Park", False),
    ("Sofia Martinez", True),
    ("Noah Chen", True),
    ("Emma Wright", False),
    ("Liam O'Brien", True),
    ("Maya Patel", True),
    ("Diego Fernandez", False),
    ("Zara Khan", True),
    ("Oliver Tanaka", True),
    ("Aisha Bakr", False),
    ("Ethan Kowalski", True),
    ("Mia Nakamura", True),
    ("Samir Haddad", True),
]


def _make_reviews(product_idx: int) -> list[dict]:
    random.seed(1000 + product_idx)
    count = random.randint(3, 6)
    out = []
    for _ in range(count):
        rating = random.choices([5, 4, 3], weights=[65, 28, 7])[0]
        title, body = random.choice(REVIEW_POOL[rating])
        author, verified = random.choice(AUTHOR_POOL)
        out.append(
            {
                "author_name": author,
                "rating": rating,
                "title": title,
                "body": body,
                "verified_purchase": verified,
            }
        )
    return out


def _avg(ratings: list[int]) -> float:
    return round(sum(ratings) / len(ratings), 2) if ratings else 0.0


HERO_SLIDES = [
    {
        "slot": "hero",
        "sort_order": 1,
        "accent_color": "#1F3A5F",
        "headline": "Shop Smarter. Live Better.",
        "subheadline": "Curated collections across six categories. Free shipping on orders over $50.",
        "cta_text": "Shop Now",
        "cta_url": "index.html#products",
        "image_path": m("hero", "slide-1.svg"),
    },
    {
        "slot": "hero",
        "sort_order": 2,
        "accent_color": "#5F84A2",
        "headline": "New Arrivals Are Here",
        "subheadline": "Discover the latest drops from our most-loved brands. Updated weekly.",
        "cta_text": "See What's New",
        "cta_url": "index.html?filter=new#products",
        "image_path": m("hero", "slide-2.svg"),
    },
    {
        "slot": "hero",
        "sort_order": 3,
        "accent_color": "#F4A261",
        "headline": "Members Save 10% Sitewide",
        "subheadline": "Sign in and use code SAVE10 at checkout. Minimum $20 order.",
        "cta_text": "Apply SAVE10",
        "cta_url": "cart.html",
        "image_path": m("hero", "slide-3.svg"),
    },
]


def _flash_end() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=48)


FLASH_BANNER = {
    "slot": "flash",
    "sort_order": 1,
    "accent_color": "#B91C1C",
    "headline": "48-Hour Flash Sale",
    "subheadline": "Up to 25% off select best-sellers.",
    "cta_text": "Shop the sale",
    "cta_url": "index.html?filter=best-sellers#products",
    "image_path": None,
    "ends_at": _flash_end(),
}


COUPONS = [
    {
        "code": "SAVE10",
        "description": "10% off sitewide. Minimum $20.",
        "discount_type": "percent",
        "discount_value": 10,
        "min_order_amount": 20,
        "max_uses": None,
        "is_active": True,
    },
    {
        "code": "WELCOME5",
        "description": "$5 off your first order. Minimum $25.",
        "discount_type": "fixed",
        "discount_value": 5,
        "min_order_amount": 25,
        "max_uses": None,
        "is_active": True,
    },
]


TESTIMONIALS = [
    {
        "author_name": "Sarah M.",
        "author_title": "Verified Buyer",
        "avatar_initials": "SM",
        "rating": 5,
        "quote": "Love the selection and how fast everything ships. My go-to store for thoughtful gifts.",
        "sort_order": 1,
    },
    {
        "author_name": "David K.",
        "author_title": "Member since 2024",
        "avatar_initials": "DK",
        "rating": 5,
        "quote": "Checkout is smooth and the coupons actually work. Returns were painless too.",
        "sort_order": 2,
    },
    {
        "author_name": "Jenna L.",
        "author_title": "Verified Buyer",
        "avatar_initials": "JL",
        "rating": 4,
        "quote": "Packaging is beautiful and orders have always arrived ahead of the estimated delivery date.",
        "sort_order": 3,
    },
]


async def seed():
    engine = create_async_engine(DATABASE_URL)
    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        result = await session.execute(select(Category))
        if result.scalars().first():
            print("Database already seeded. Skipping.")
            await engine.dispose()
            return

        category_map = {}
        for cat_data in CATEGORIES:
            cat = Category(**cat_data)
            session.add(cat)
            await session.flush()
            category_map[cat_data["name"]] = cat.id

        for idx, prod_data in enumerate(PRODUCTS):
            slug = prod_data.pop("slug")
            cat_name = prod_data.pop("category")
            images = _images_for(slug)
            reviews_data = _make_reviews(idx)
            ratings = [r["rating"] for r in reviews_data]

            product = Product(
                category_id=category_map[cat_name],
                image_url=images[0],
                images=images,
                avg_rating=_avg(ratings),
                review_count=len(reviews_data),
                **prod_data,
            )
            session.add(product)
            await session.flush()

            for r in reviews_data:
                session.add(Review(product_id=product.id, **r))

        for slide in HERO_SLIDES:
            session.add(Promotion(**slide))
        session.add(Promotion(**FLASH_BANNER))

        for c in COUPONS:
            session.add(Coupon(**c))

        for t in TESTIMONIALS:
            session.add(Testimonial(**t))

        await session.commit()
        print(
            f"Seeded {len(CATEGORIES)} categories, {len(PRODUCTS)} products, "
            f"{len(HERO_SLIDES) + 1} promotions, {len(TESTIMONIALS)} testimonials."
        )

    await engine.dispose()


def main():
    asyncio.run(seed())


if __name__ == "__main__":
    main()
