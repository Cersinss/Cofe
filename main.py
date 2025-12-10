from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Optional, Tuple


@dataclass(frozen=True)
class CoffeeOrder:
    base: str
    size: str
    milk: str
    syrups: Tuple[str, ...]
    sugar: int
    iced: bool
    price: float
    description: str
    extra_shots: int

    def __str__(self) -> str:
        if self.description:
            return self.description
        return f"{self.size} {self.base} ({self.price:.2f})"


class CoffeeOrderBuilder:
    """
    Строитель заказа кофе. Поддерживает пошаговую сборку с валидацией:
    - обязательны base и size;
    - лимиты: сахар 0..5, сиропов до 4 уникальных, шотов 0..3;
    - доплаты и множители задаются класс-атрибутами;
    - build возвращает неизменяемый CoffeeOrder, билдер можно переиспользовать.
    """

    BASE_PRICES = {
        "espresso": 200.0,
        "americano": 250.0,
        "latte": 300.0,
        "cappuccino": 320.0,
    }

    SIZE_MULTIPLIERS = {"small": 1.0, "medium": 1.2, "large": 1.4}
    MILK_SURCHARGES = {"none": 0.0, "whole": 30.0, "skim": 30.0, "oat": 60.0, "soy": 50.0}
    SYRUP_PRICE = 40.0
    SHOT_PRICE = 70.0
    ICED_RATE = 0.2  # 20% надбавка к базовой стоимости

    MAX_SYRUPS = 4
    MAX_SUGAR = 5
    MAX_SHOTS = 3

    DEFAULT_MILK = "none"

    def __init__(self) -> None:
        self._base: Optional[str] = None
        self._size: Optional[str] = None
        self._milk: str = self.DEFAULT_MILK
        self._syrups: List[str] = []
        self._sugar: int = 0
        self._iced: bool = False
        self._shots: int = 0

    # Fluent setters
    def set_base(self, base: str) -> "CoffeeOrderBuilder":
        if base not in self.BASE_PRICES:
            raise ValueError(f"Недопустимая база: {base}")
        self._base = base
        return self

    def set_size(self, size: str) -> "CoffeeOrderBuilder":
        if size not in self.SIZE_MULTIPLIERS:
            raise ValueError(f"Недопустимый размер: {size}")
        self._size = size
        return self

    def set_milk(self, milk: str) -> "CoffeeOrderBuilder":
        if milk not in self.MILK_SURCHARGES:
            raise ValueError(f"Недопустимое молоко: {milk}")
        self._milk = milk
        return self

    def add_syrup(self, name: str) -> "CoffeeOrderBuilder":
        if name not in self._syrups:
            if len(self._syrups) >= self.MAX_SYRUPS:
                raise ValueError("Превышен лимит сиропов")
            self._syrups.append(name)
        return self

    def set_sugar(self, teaspoons: int) -> "CoffeeOrderBuilder":
        if not 0 <= teaspoons <= self.MAX_SUGAR:
            raise ValueError("Сахар должен быть в диапазоне 0..5")
        self._sugar = teaspoons
        return self

    def add_shot(self, count: int = 1) -> "CoffeeOrderBuilder":
        if count < 0:
            raise ValueError("Количество шотов не может быть отрицательным")
        new_total = self._shots + count
        if new_total > self.MAX_SHOTS:
            raise ValueError("Превышен лимит шотов")
        self._shots = new_total
        return self

    def set_iced(self, iced: bool = True) -> "CoffeeOrderBuilder":
        self._iced = iced
        return self

    def clear_extras(self) -> "CoffeeOrderBuilder":
        self._milk = self.DEFAULT_MILK
        self._syrups = []
        self._sugar = 0
        self._shots = 0
        self._iced = False
        return self

    # Build helpers
    def _calc_price(self) -> float:
        assert self._base is not None
        assert self._size is not None

        base_cost = self.BASE_PRICES[self._base] * self.SIZE_MULTIPLIERS[self._size]
        milk_cost = self.MILK_SURCHARGES[self._milk]
        syrup_cost = len(self._syrups) * self.SYRUP_PRICE
        shots_cost = self._shots * self.SHOT_PRICE

        subtotal = base_cost + milk_cost + syrup_cost + shots_cost
        if self._iced:
            subtotal += base_cost * self.ICED_RATE
        return round(subtotal, 2)

    def _build_description(self) -> str:
        assert self._base is not None
        assert self._size is not None

        parts: List[str] = [f"{self._size} {self._base}"]
        if self._milk != self.DEFAULT_MILK:
            parts.append(f"with {self._milk} milk")
        if self._syrups:
            parts.append("+" + ",".join(self._syrups) + " syrup")
        if self._iced:
            parts.append("(iced)")
        if self._sugar:
            parts.append(f"{self._sugar} tsp sugar")
        if self._shots:
            parts.append(f"+{self._shots} extra shot(s)")
        return " ".join(parts)

    def build(self) -> CoffeeOrder:
        if self._base is None:
            raise ValueError("base обязателен")
        if self._size is None:
            raise ValueError("size обязателен")

        syrups_tuple = tuple(self._syrups)
        price = self._calc_price()
        description = self._build_description()

        return CoffeeOrder(
            base=self._base,
            size=self._size,
            milk=self._milk,
            syrups=syrups_tuple,
            sugar=self._sugar,
            iced=self._iced,
            price=price,
            description=description,
            extra_shots=self._shots,
        )


# --------------------- Примитивные проверки ---------------------
if __name__ == "__main__":
    builder = CoffeeOrderBuilder()
    order_basic = (
        builder.set_base("espresso")
        .set_size("medium")
        .set_milk("oat")
        .add_syrup("vanilla")
        .add_syrup("caramel")
        .set_sugar(2)
        .add_shot()
        .set_iced(True)
        .build()
    )
    assert isinstance(order_basic, CoffeeOrder)
    assert order_basic.price > 0
    assert "vanilla" in order_basic.syrups
    assert order_basic.iced is True
    assert order_basic.extra_shots == 1

    # Переиспользование билдера
    order_second = builder.set_milk("soy").add_syrup("hazelnut").add_shot().build()
    assert order_second is not order_basic
    assert order_second.price != order_basic.price
    assert order_basic.milk == "oat"
    assert order_basic.extra_shots == 1
    assert order_second.extra_shots == 2

    # Валидации обязательных полей
    try:
        CoffeeOrderBuilder().set_size("small").build()
    except ValueError:
        pass
    else:
        raise AssertionError("Отсутствие base не вызвало ошибку")

    try:
        CoffeeOrderBuilder().set_base("latte").build()
    except ValueError:
        pass
    else:
        raise AssertionError("Отсутствие size не вызвало ошибку")

    # Лимиты
    try:
        CoffeeOrderBuilder().set_base("latte").set_size("small").set_sugar(6)
    except ValueError:
        pass
    else:
        raise AssertionError("Превышение лимита сахара не проверено")

    try:
        (
            CoffeeOrderBuilder()
            .set_base("latte")
            .set_size("small")
            .add_shot(4)
            .build()
        )
    except ValueError:
        pass
    else:
        raise AssertionError("Превышение лимита шотов не проверено")

    # Дубликат сиропа
    order_dup = (
        CoffeeOrderBuilder()
        .set_base("americano")
        .set_size("large")
        .add_syrup("vanilla")
        .add_syrup("vanilla")
        .build()
    )
    assert order_dup.syrups == ("vanilla",)

    # Надбавка за лед
    iced_price = (
        CoffeeOrderBuilder()
        .set_base("espresso")
        .set_size("small")
        .set_iced(True)
        .build()
        .price
    )
    hot_price = CoffeeOrderBuilder().set_base("espresso").set_size("small").build().price
    assert iced_price > hot_price

    print("All basic checks passed.")

