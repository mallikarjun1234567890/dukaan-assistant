from app.services.inventory_service import (
    inventory_value_paise,
    is_low_stock,
    stock_status,
    suggested_reorder_quantity,
)


class FakeProduct:
    def __init__(self, qty, cost):
        self.stock_quantity = qty
        self.purchase_cost_paise = cost


def test_low_stock_at_threshold():
    assert is_low_stock(8, 8) is True
    assert is_low_stock(9, 8) is False
    assert stock_status(0, 5) == "out"
    assert stock_status(2, 5) == "low"
    assert stock_status(10, 5) == "healthy"


def test_suggested_quantity_is_twice_minimum_minus_current():
    assert suggested_reorder_quantity(2, 8) == 14
    assert suggested_reorder_quantity(16, 8) == 0
    assert suggested_reorder_quantity(0, 5) == 10


def test_inventory_value_uses_purchase_cost():
    products = [FakeProduct(2, 12000), FakeProduct(3, 1000)]
    assert inventory_value_paise(products) == 27000
