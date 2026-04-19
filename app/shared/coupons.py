from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models import Coupon


async def find_active_coupon(db: AsyncSession, code: str) -> Coupon | None:
    result = await db.execute(
        select(Coupon).where(Coupon.code == code.upper(), Coupon.is_active)
    )
    return result.scalars().first()


def _is_coupon_valid(coupon: Coupon, cart_total: float) -> tuple[bool, str]:
    if coupon.valid_until is not None:
        now = datetime.now(timezone.utc)
        if coupon.valid_until < now:
            return False, "Coupon has expired"

    if coupon.max_uses is not None and coupon.times_used >= coupon.max_uses:
        return False, "Coupon usage limit reached"

    if cart_total < float(coupon.min_order_amount):
        return False, f"Minimum order amount is ${float(coupon.min_order_amount):.2f}"

    return True, ""


def calculate_discount(coupon: Coupon, cart_total: float) -> float:
    if coupon.discount_type == "percent":
        discount = cart_total * (float(coupon.discount_value) / 100.0)
    else:
        discount = float(coupon.discount_value)

    return min(round(discount, 2), cart_total)


async def validate_and_calculate(
    db: AsyncSession, code: str, cart_total: float
) -> dict:
    coupon = await find_active_coupon(db, code)
    if not coupon:
        return {
            "valid": False,
            "code": None,
            "discount_amount": 0.0,
            "new_total": round(cart_total, 2),
            "message": "Invalid coupon code",
        }

    ok, reason = _is_coupon_valid(coupon, cart_total)
    if not ok:
        return {
            "valid": False,
            "code": coupon.code,
            "discount_amount": 0.0,
            "new_total": round(cart_total, 2),
            "message": reason,
        }

    discount = calculate_discount(coupon, cart_total)
    return {
        "valid": True,
        "code": coupon.code,
        "discount_amount": discount,
        "new_total": round(cart_total - discount, 2),
        "message": "Coupon applied",
    }
