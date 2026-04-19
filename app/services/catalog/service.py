import math
from datetime import datetime, timezone

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from shared.models import Category, Product, Promotion, Review, Testimonial


_SORT_OPTIONS = {
    "newest": Product.created_at.desc(),
    "oldest": Product.created_at.asc(),
    "price_asc": Product.price.asc(),
    "price_desc": Product.price.desc(),
    "name_asc": Product.name.asc(),
    "name_desc": Product.name.desc(),
}


async def list_products(
    db: AsyncSession,
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    sort: str = "newest",
    page: int = 1,
    per_page: int = 20,
) -> dict:
    filters = [Product.is_active == True]
    if category_id:
        filters.append(Product.category_id == category_id)
    if min_price is not None:
        filters.append(Product.price >= min_price)
    if max_price is not None:
        filters.append(Product.price <= max_price)

    query = select(Product).where(*filters).options(joinedload(Product.category))

    count_query = select(func.count()).select_from(
        select(Product.id).where(*filters).subquery()
    )
    total = (await db.execute(count_query)).scalar() or 0

    order_clause = _SORT_OPTIONS.get(sort, _SORT_OPTIONS["newest"])
    query = query.order_by(order_clause).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    products = result.unique().scalars().all()

    return {
        "items": products,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page > 0 else 0,
    }


async def get_product(db: AsyncSession, product_id: int) -> Product | None:
    query = (
        select(Product)
        .where(Product.id == product_id, Product.is_active == True)
        .options(joinedload(Product.category))
    )
    result = await db.execute(query)
    return result.unique().scalars().first()


async def search_products(
    db: AsyncSession,
    query_text: str,
    category_id: int | None = None,
    min_price: float | None = None,
    max_price: float | None = None,
    page: int = 1,
    per_page: int = 20,
) -> dict:
    ts_query = func.plainto_tsquery("english", query_text)

    filters = [Product.is_active == True, Product.search_vector.op("@@")(ts_query)]
    if category_id:
        filters.append(Product.category_id == category_id)
    if min_price is not None:
        filters.append(Product.price >= min_price)
    if max_price is not None:
        filters.append(Product.price <= max_price)

    search_query = (
        select(Product)
        .where(*filters)
        .options(joinedload(Product.category))
        .order_by(func.ts_rank(Product.search_vector, ts_query).desc())
    )

    count_query = select(func.count()).select_from(
        select(Product.id).where(*filters).subquery()
    )
    total = (await db.execute(count_query)).scalar() or 0

    search_query = search_query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(search_query)
    products = result.unique().scalars().all()

    return {
        "items": products,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if per_page > 0 else 0,
    }


async def get_price_range(db: AsyncSession) -> dict:
    result = await db.execute(
        select(
            func.coalesce(func.min(Product.price), 0),
            func.coalesce(func.max(Product.price), 0),
        ).where(Product.is_active == True)
    )
    row = result.first()
    return {"min": float(row[0]), "max": float(row[1])}


async def list_categories(db: AsyncSession) -> list[Category]:
    result = await db.execute(select(Category).order_by(Category.name))
    return result.scalars().all()


async def list_best_sellers(db: AsyncSession, limit: int = 8) -> list[Product]:
    query = (
        select(Product)
        .where(Product.is_active == True)
        .options(joinedload(Product.category))
        .order_by(Product.sales_count.desc(), Product.avg_rating.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.unique().scalars().all()


async def list_new_arrivals(db: AsyncSession, limit: int = 8) -> list[Product]:
    query = (
        select(Product)
        .where(Product.is_active == True)
        .options(joinedload(Product.category))
        .order_by(Product.created_at.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.unique().scalars().all()


async def list_related(db: AsyncSession, product_id: int, limit: int = 4) -> list[Product]:
    base = await db.execute(
        select(Product.category_id).where(Product.id == product_id)
    )
    category_id = base.scalar()
    if category_id is None:
        return []
    query = (
        select(Product)
        .where(
            Product.is_active == True,
            Product.category_id == category_id,
            Product.id != product_id,
        )
        .options(joinedload(Product.category))
        .order_by(Product.sales_count.desc())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.unique().scalars().all()


async def get_product_reviews(
    db: AsyncSession, product_id: int, limit: int = 20
) -> dict:
    avg_row = await db.execute(
        select(
            func.coalesce(func.avg(Review.rating), 0),
            func.count(Review.id),
        ).where(Review.product_id == product_id)
    )
    avg, total = avg_row.first()

    breakdown_rows = await db.execute(
        select(Review.rating, func.count(Review.id))
        .where(Review.product_id == product_id)
        .group_by(Review.rating)
    )
    breakdown = {r: 0 for r in range(1, 6)}
    for rating, count in breakdown_rows.all():
        breakdown[rating] = count

    reviews_query = (
        select(Review)
        .where(Review.product_id == product_id)
        .order_by(Review.created_at.desc())
        .limit(limit)
    )
    reviews = (await db.execute(reviews_query)).scalars().all()

    return {
        "avg_rating": float(avg or 0),
        "review_count": int(total or 0),
        "rating_breakdown": breakdown,
        "reviews": reviews,
    }


async def create_review(
    db: AsyncSession,
    product_id: int,
    author_name: str,
    rating: int,
    title: str | None,
    body: str | None,
    customer_id: int | None = None,
    verified_purchase: bool = False,
) -> Review:
    review = Review(
        product_id=product_id,
        customer_id=customer_id,
        author_name=author_name or "Customer",
        rating=rating,
        title=title,
        body=body,
        verified_purchase=verified_purchase,
    )
    db.add(review)
    await db.flush()

    agg = await db.execute(
        select(
            func.coalesce(func.avg(Review.rating), 0),
            func.count(Review.id),
        ).where(Review.product_id == product_id)
    )
    avg, count = agg.first()
    product = (
        await db.execute(select(Product).where(Product.id == product_id))
    ).scalar_one()
    product.avg_rating = round(float(avg or 0), 2)
    product.review_count = int(count or 0)

    await db.commit()
    await db.refresh(review)
    return review


async def list_promotions(db: AsyncSession, slot: str | None = None) -> list[Promotion]:
    now = datetime.now(timezone.utc)
    filters = [Promotion.is_active == True]
    if slot:
        filters.append(Promotion.slot == slot)
    query = (
        select(Promotion)
        .where(
            *filters,
            (Promotion.starts_at == None) | (Promotion.starts_at <= now),
            (Promotion.ends_at == None) | (Promotion.ends_at >= now),
        )
        .order_by(Promotion.sort_order.asc(), Promotion.id.asc())
    )
    result = await db.execute(query)
    return result.scalars().all()


async def list_testimonials(db: AsyncSession, limit: int = 6) -> list[Testimonial]:
    query = (
        select(Testimonial)
        .where(Testimonial.is_active == True)
        .order_by(Testimonial.sort_order.asc(), Testimonial.id.asc())
        .limit(limit)
    )
    result = await db.execute(query)
    return result.scalars().all()
