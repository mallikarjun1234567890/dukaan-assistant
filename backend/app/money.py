"""Decimal-safe money helpers using integer paise (1 INR = 100 paise)."""

from decimal import ROUND_HALF_UP, Decimal

PAISE_PER_RUPEE = Decimal("100")
RUPEE_QUANTUM = Decimal("0.01")


def rupees_to_paise(amount: Decimal | int | float | str) -> int:
    value = Decimal(str(amount))
    if value < 0:
        raise ValueError("Monetary amounts cannot be negative")
    paise = (value * PAISE_PER_RUPEE).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(paise)


def paise_to_rupees(paise: int) -> Decimal:
    return (Decimal(paise) / PAISE_PER_RUPEE).quantize(RUPEE_QUANTUM)


def format_inr(paise: int) -> str:
    rupees = paise_to_rupees(paise)
    return f"₹{rupees:,.2f}"
