import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.checkout import service


def _make_mock_redis_with_cart(cart_items):
    """Create mock Redis pre-loaded with cart data."""
    cart = {"items": cart_items, "updated_at": "2026-04-14T10:00:00"}
    stored = {"data": json.dumps(cart)}

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
async def test_checkout_empty_cart(db_session):
    r = _make_mock_redis_with_cart([])
    with pytest.raises(ValueError, match="Cart is empty"):
        await service.process_checkout(db_session, r, "user-1", "test@test.com")


@pytest.mark.asyncio
async def test_checkout_success(db_session, sample_products):
    cart_items = [{
        "product_id": sample_products[0].id,
        "name": sample_products[0].name,
        "price": float(sample_products[0].price),
        "quantity": 2,
    }]
    r = _make_mock_redis_with_cart(cart_items)

    # process_checkout no longer publishes to SQS itself — it returns the
    # message for the router to schedule as a BackgroundTask. So no mock_sqs
    # patching is needed here. Just unpack the (response, sqs_message) tuple.
    response, sqs_message = await service.process_checkout(db_session, r, "user-1", "test@test.com")

    assert response["order_id"] is not None
    assert response["status"] == "confirmed"
    assert response["total_amount"] == 20.00  # 10.00 * 2
    assert sqs_message["order_id"] == response["order_id"]
    assert sqs_message["customer_email"] == "test@test.com"
    assert len(sqs_message["items"]) == 1


@pytest.mark.asyncio
async def test_checkout_insufficient_stock(db_session, sample_products):
    cart_items = [{
        "product_id": sample_products[0].id,
        "name": sample_products[0].name,
        "price": float(sample_products[0].price),
        "quantity": 999,
    }]
    r = _make_mock_redis_with_cart(cart_items)

    with pytest.raises(ValueError, match="only .* units in stock"):
        await service.process_checkout(db_session, r, "user-1", "test@test.com")


@pytest.mark.asyncio
async def test_list_orders_empty(db_session):
    result = await service.list_orders(db_session, "nonexistent-user")
    assert result["items"] == []
    assert result["total"] == 0


@pytest.mark.asyncio
async def test_list_orders_after_checkout(db_session, sample_products):
    cart_items = [{
        "product_id": sample_products[0].id,
        "name": sample_products[0].name,
        "price": float(sample_products[0].price),
        "quantity": 1,
    }]
    r = _make_mock_redis_with_cart(cart_items)

    await service.process_checkout(db_session, r, "order-user", "order@test.com")

    result = await service.list_orders(db_session, "order-user")
    assert result["total"] >= 1


@pytest.mark.asyncio
async def test_get_order_not_found(db_session):
    order = await service.get_order(db_session, "nonexistent-user", 99999)
    assert order is None


def test_publish_invoice_message_calls_sqs_when_configured():
    msg = {"order_id": 42, "customer_email": "x@y.com"}
    fake_sqs = MagicMock()
    with patch.object(service.settings, "sqs_queue_url", "https://sqs.fake/q"), \
         patch.object(service, "_get_sqs", return_value=fake_sqs):
        service.publish_invoice_message(msg)
    fake_sqs.send_message.assert_called_once()
    kwargs = fake_sqs.send_message.call_args.kwargs
    assert kwargs["QueueUrl"] == "https://sqs.fake/q"
    assert json.loads(kwargs["MessageBody"]) == msg


def test_publish_invoice_message_logs_in_dev_when_unconfigured():
    msg = {"order_id": 99}
    with patch.object(service.settings, "sqs_queue_url", ""), \
         patch.object(service.settings, "environment", "dev"):
        service.publish_invoice_message(msg)  # must not raise


def test_publish_invoice_message_raises_in_prod_when_unconfigured():
    msg = {"order_id": 100}
    with patch.object(service.settings, "sqs_queue_url", ""), \
         patch.object(service.settings, "environment", "prod"):
        with pytest.raises(RuntimeError, match="SQS_QUEUE_URL empty in prod"):
            service.publish_invoice_message(msg)
