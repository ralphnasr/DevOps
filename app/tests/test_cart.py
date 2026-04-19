import json
from unittest.mock import AsyncMock

import pytest

from services.cart import service


def _make_mock_redis(cart_data=None):
    """Create a mock Redis that simulates cart storage."""
    stored = {"data": json.dumps(cart_data) if cart_data else None}

    r = AsyncMock()

    async def mock_get(key):
        return stored["data"]

    async def mock_set(key, value, ex=None):
        stored["data"] = value
        return True

    async def mock_delete(key):
        stored["data"] = None
        return True

    r.get = mock_get
    r.set = mock_set
    r.delete = mock_delete
    return r


@pytest.mark.asyncio
async def test_get_empty_cart():
    r = _make_mock_redis()
    cart = await service.get_user_cart(r, "user-1")
    assert cart["items"] == []


@pytest.mark.asyncio
async def test_add_item(db_session, sample_products):
    r = _make_mock_redis()
    cart = await service.add_item(r, db_session, "user-1", sample_products[0].id, 2)
    assert len(cart["items"]) == 1
    assert cart["items"][0]["product_id"] == sample_products[0].id
    assert cart["items"][0]["quantity"] == 2


@pytest.mark.asyncio
async def test_add_item_duplicate_increases_quantity(db_session, sample_products):
    r = _make_mock_redis()
    await service.add_item(r, db_session, "user-1", sample_products[0].id, 1)
    cart = await service.add_item(r, db_session, "user-1", sample_products[0].id, 3)
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 4


@pytest.mark.asyncio
async def test_add_item_invalid_product(db_session):
    r = _make_mock_redis()
    with pytest.raises(ValueError, match="not found"):
        await service.add_item(r, db_session, "user-1", 99999, 1)


@pytest.mark.asyncio
async def test_update_item_quantity(db_session, sample_products):
    r = _make_mock_redis()
    await service.add_item(r, db_session, "user-1", sample_products[0].id, 2)
    cart = await service.update_item(r, db_session, "user-1", sample_products[0].id, 5)
    assert cart["items"][0]["quantity"] == 5


@pytest.mark.asyncio
async def test_update_item_zero_removes(db_session, sample_products):
    r = _make_mock_redis()
    await service.add_item(r, db_session, "user-1", sample_products[0].id, 2)
    cart = await service.update_item(r, db_session, "user-1", sample_products[0].id, 0)
    assert len(cart["items"]) == 0


@pytest.mark.asyncio
async def test_remove_item(db_session, sample_products):
    r = _make_mock_redis()
    await service.add_item(r, db_session, "user-1", sample_products[0].id, 2)
    cart = await service.remove_item(r, "user-1", sample_products[0].id)
    assert len(cart["items"]) == 0


@pytest.mark.asyncio
async def test_add_item_blocks_when_out_of_stock(db_session, sample_products):
    """Batch E: server-side guard rejects add when stock_quantity <= 0."""
    sample_products[0].stock_quantity = 0
    await db_session.flush()
    r = _make_mock_redis()
    with pytest.raises(ValueError, match="out of stock"):
        await service.add_item(r, db_session, "user-1", sample_products[0].id, 1)


@pytest.mark.asyncio
async def test_add_item_blocks_when_qty_exceeds_stock(db_session, sample_products):
    """Batch E: cannot add more than current stock_quantity."""
    sample_products[0].stock_quantity = 3
    await db_session.flush()
    r = _make_mock_redis()
    with pytest.raises(ValueError, match="Only 3"):
        await service.add_item(r, db_session, "user-1", sample_products[0].id, 5)


@pytest.mark.asyncio
async def test_update_item_blocks_when_qty_exceeds_stock(db_session, sample_products):
    """Batch E: PUT /items/{id} re-validates against stock."""
    sample_products[0].stock_quantity = 4
    await db_session.flush()
    r = _make_mock_redis()
    await service.add_item(r, db_session, "user-1", sample_products[0].id, 1)
    with pytest.raises(ValueError, match="Only 4"):
        await service.update_item(r, db_session, "user-1", sample_products[0].id, 99)
