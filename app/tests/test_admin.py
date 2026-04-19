import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from services.admin import service


@pytest.mark.asyncio
async def test_dashboard_stats(db_session: AsyncSession, sample_products):
    stats = await service.get_dashboard_stats(db_session)
    assert stats["total_products"] == 3
    assert stats["total_orders"] == 0
    assert stats["total_revenue"] == 0
    assert isinstance(stats["recent_orders"], list)


@pytest.mark.asyncio
async def test_list_products_admin(db_session: AsyncSession, sample_products):
    result = await service.list_products_admin(db_session)
    assert result["total"] == 3
    assert len(result["items"]) == 3


@pytest.mark.asyncio
async def test_list_products_admin_search(db_session: AsyncSession, sample_products):
    result = await service.list_products_admin(db_session, search="Product 1")
    assert result["total"] >= 1
    assert any("Product 1" in p.name for p in result["items"])


@pytest.mark.asyncio
async def test_create_product(db_session: AsyncSession, sample_category):
    data = {
        "name": "New Admin Product",
        "description": "Created via admin",
        "price": 25.99,
        "category_id": sample_category.id,
        "stock_quantity": 100,
    }
    product = await service.create_product(db_session, data)
    assert product.id is not None
    assert product.name == "New Admin Product"
    assert float(product.price) == 25.99


@pytest.mark.asyncio
async def test_update_product(db_session: AsyncSession, sample_products):
    updated = await service.update_product(db_session, sample_products[0].id, {"name": "Updated Name"})
    assert updated is not None
    assert updated.name == "Updated Name"


@pytest.mark.asyncio
async def test_deactivate_product(db_session: AsyncSession, sample_products):
    success = await service.deactivate_product(db_session, sample_products[0].id)
    assert success is True


@pytest.mark.asyncio
async def test_update_order_status_invalid(db_session: AsyncSession):
    with pytest.raises(ValueError, match="Invalid status"):
        await service.update_order_status(db_session, 1, "invalid_status")


# ── Batch E: admin compliance fixes ──

@pytest.mark.asyncio
async def test_revenue_excludes_cancelled_orders(db_session: AsyncSession, sample_products):
    """Batch E: total_revenue must not count cancelled orders."""
    from shared.models import Customer, Order
    customer = Customer(cognito_sub="cust-1", email="a@x.com")
    db_session.add(customer)
    await db_session.flush()
    db_session.add_all([
        Order(customer_id=customer.id, total_amount=100, status="confirmed"),
        Order(customer_id=customer.id, total_amount=50, status="cancelled"),
        Order(customer_id=customer.id, total_amount=25, status="delivered"),
    ])
    await db_session.commit()
    stats = await service.get_dashboard_stats(db_session)
    assert float(stats["total_revenue"]) == 125.0
    assert stats["total_orders"] == 3


@pytest.mark.asyncio
async def test_active_count_requires_stock(db_session: AsyncSession, sample_category):
    """Batch E: 'Active Products' = is_active AND stock_quantity > 0."""
    from shared.models import Product
    db_session.add_all([
        Product(name="A", price=10, category_id=sample_category.id, is_active=True, stock_quantity=5),
        Product(name="B", price=10, category_id=sample_category.id, is_active=True, stock_quantity=0),
        Product(name="C", price=10, category_id=sample_category.id, is_active=False, stock_quantity=5),
    ])
    await db_session.commit()
    stats = await service.get_dashboard_stats(db_session)
    assert stats["total_products"] == 1


@pytest.mark.asyncio
async def test_get_product_direct_lookup(db_session: AsyncSession, sample_products):
    """Batch E: edit-product flow now uses direct lookup, not paginated scan."""
    target_id = sample_products[2].id
    found = await service.get_product(db_session, target_id)
    assert found is not None
    assert found.id == target_id
    missing = await service.get_product(db_session, 99999)
    assert missing is None
