import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Category, Product
from services.catalog import service


@pytest.mark.asyncio
async def test_list_products(db_session: AsyncSession, sample_products):
    result = await service.list_products(db_session, page=1, per_page=10)
    assert result["total"] == 3
    assert len(result["items"]) == 3
    assert result["page"] == 1


@pytest.mark.asyncio
async def test_list_products_pagination(db_session: AsyncSession, sample_products):
    result = await service.list_products(db_session, page=1, per_page=2)
    assert result["total"] == 3
    assert len(result["items"]) == 2
    assert result["pages"] == 2


@pytest.mark.asyncio
async def test_list_products_by_category(db_session: AsyncSession, sample_products, sample_category):
    result = await service.list_products(db_session, page=1, per_page=10, category_id=sample_category.id)
    assert result["total"] == 3
    assert all(p.category_id == sample_category.id for p in result["items"])


@pytest.mark.asyncio
async def test_get_product(db_session: AsyncSession, sample_products):
    product = await service.get_product(db_session, sample_products[0].id)
    assert product is not None
    assert product.name == "Test Product 1"


@pytest.mark.asyncio
async def test_get_product_not_found(db_session: AsyncSession):
    product = await service.get_product(db_session, 99999)
    assert product is None


@pytest.mark.asyncio
async def test_list_categories(db_session: AsyncSession, sample_category):
    categories = await service.list_categories(db_session)
    assert len(categories) >= 1
    assert any(c.name == "Electronics" for c in categories)
