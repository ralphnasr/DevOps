from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from shared.database import get_db
from shared.schemas import (
    CategoryOut,
    ProductList,
    ProductOut,
    PromotionOut,
    ReviewCreate,
    ReviewOut,
    ReviewSummary,
    TestimonialOut,
)

from . import service

router = APIRouter(prefix="/api/products", tags=["catalog"])
storefront_router = APIRouter(prefix="/api", tags=["storefront"])

SORT_VALUES = "newest|oldest|price_asc|price_desc|name_asc|name_desc"


@router.get("", response_model=ProductList)
async def list_products(
    category_id: int | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    sort: str = Query(default="newest", pattern=f"^({SORT_VALUES})$"),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_products(
        db,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        sort=sort,
        page=page,
        per_page=per_page,
    )


@router.get("/search", response_model=ProductList)
async def search_products(
    q: str = Query(min_length=1),
    category_id: int | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    page: int = Query(default=1, ge=1),
    per_page: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    return await service.search_products(
        db,
        query_text=q,
        category_id=category_id,
        min_price=min_price,
        max_price=max_price,
        page=page,
        per_page=per_page,
    )


@router.get("/categories", response_model=list[CategoryOut])
async def list_categories(db: AsyncSession = Depends(get_db)):
    return await service.list_categories(db)


@router.get("/price-range")
async def price_range(db: AsyncSession = Depends(get_db)):
    return await service.get_price_range(db)


@router.get("/best-sellers", response_model=list[ProductOut])
async def best_sellers(
    limit: int = Query(default=8, ge=1, le=24), db: AsyncSession = Depends(get_db)
):
    return await service.list_best_sellers(db, limit=limit)


@router.get("/new-arrivals", response_model=list[ProductOut])
async def new_arrivals(
    limit: int = Query(default=8, ge=1, le=24), db: AsyncSession = Depends(get_db)
):
    return await service.list_new_arrivals(db, limit=limit)


@router.get("/{product_id}", response_model=ProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    product = await service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.get("/{product_id}/related", response_model=list[ProductOut])
async def related_products(
    product_id: int,
    limit: int = Query(default=4, ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_related(db, product_id, limit=limit)


@router.get("/{product_id}/reviews", response_model=ReviewSummary)
async def product_reviews(
    product_id: int,
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    product = await service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return await service.get_product_reviews(db, product_id, limit=limit)


@router.post("/{product_id}/reviews", response_model=ReviewOut, status_code=201)
async def submit_review(
    product_id: int,
    payload: ReviewCreate,
    db: AsyncSession = Depends(get_db),
):
    product = await service.get_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    author = (payload.author_name or "").strip() or "Customer"
    return await service.create_review(
        db,
        product_id=product_id,
        author_name=author,
        rating=payload.rating,
        title=payload.title,
        body=payload.body,
    )


@storefront_router.get("/promotions", response_model=list[PromotionOut])
async def active_promotions(
    slot: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_promotions(db, slot=slot)


@storefront_router.get("/testimonials", response_model=list[TestimonialOut])
async def testimonials(
    limit: int = Query(default=6, ge=1, le=24),
    db: AsyncSession = Depends(get_db),
):
    return await service.list_testimonials(db, limit=limit)
