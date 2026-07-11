"""Cost-per-dish analysis.

Joins POS menu items to inventory recipes (via the soft
``RecipeIngredient.pos_menu_item_id``) and computes the live food cost,
margin, and category for each dish. POS and Inventory live in separate
DBs, so this service takes both sessions and does the join in Python.

Margin band heuristic:
- gross_margin_pct < 50  -> "low"
- 50 .. 65               -> "medium"
- > 65                   -> "high"
"""
from __future__ import annotations

from decimal import Decimal
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from app.inventory.models import InventoryItem, RecipeIngredient
from app.pos.models import MenuItem


def _band(margin_pct: float) -> str:
    if margin_pct < 50:
        return "low"
    if margin_pct <= 65:
        return "medium"
    return "high"


class CostPerDishService:
    def __init__(self, pos_db: Session, inventory_db: Session):
        self.pos = pos_db
        self.inv = inventory_db

    def _recipes_by_menu_item(self) -> Dict[int, List[Tuple[RecipeIngredient, InventoryItem]]]:
        recipes = self.inv.query(RecipeIngredient).all()
        item_ids = {r.inventory_item_id for r in recipes}
        items = (
            self.inv.query(InventoryItem)
            .filter(InventoryItem.id.in_(list(item_ids) or [-1]))
            .all()
        )
        item_map = {i.id: i for i in items}
        out: Dict[int, List[Tuple[RecipeIngredient, InventoryItem]]] = {}
        for r in recipes:
            inv_item = item_map.get(r.inventory_item_id)
            if not inv_item:
                continue
            out.setdefault(r.pos_menu_item_id, []).append((r, inv_item))
        return out

    def compute(
        self,
        menu_item_ids: Optional[List[int]] = None,
        category_id: Optional[int] = None,
    ) -> List[dict]:
        q = self.pos.query(MenuItem)
        if menu_item_ids:
            q = q.filter(MenuItem.id.in_(menu_item_ids))
        if category_id:
            q = q.filter(MenuItem.category_id == category_id)
        dishes = q.all()
        recipes = self._recipes_by_menu_item()

        rows: List[dict] = []
        for d in dishes:
            recipe = recipes.get(d.id, [])
            total_cost = Decimal("0")
            cost_breakdown: List[dict] = []
            for r, inv_item in recipe:
                line_cost = Decimal(r.quantity) * Decimal(inv_item.unit_cost or 0)
                total_cost += line_cost
                cost_breakdown.append(
                    {
                        "inventory_item_id": inv_item.id,
                        "sku": inv_item.sku,
                        "name": inv_item.name,
                        "quantity": float(r.quantity),
                        "unit_cost": float(inv_item.unit_cost or 0),
                        "line_cost": float(line_cost),
                    }
                )
            price = Decimal(d.price or 0)
            cost_pct = float(total_cost / price * 100) if price > 0 else 0.0
            margin_pct = 100.0 - cost_pct if price > 0 else 0.0
            rows.append(
                {
                    "menu_item_id": d.id,
                    "name": d.name,
                    "category_id": d.category_id,
                    "price": float(price),
                    "food_cost": float(total_cost),
                    "cost_pct": cost_pct,
                    "gross_margin": float(price - total_cost),
                    "gross_margin_pct": margin_pct,
                    "margin_band": _band(margin_pct),
                    "ingredients": cost_breakdown,
                    "has_recipe": len(recipe) > 0,
                }
            )
        rows.sort(key=lambda r: r["gross_margin_pct"], reverse=True)
        return rows

    def summary_by_category(self) -> List[dict]:
        rows = self.compute()
        by_cat: Dict[int, dict] = {}
        for r in rows:
            cat = by_cat.setdefault(
                r["category_id"],
                {
                    "category_id": r["category_id"],
                    "dishes": 0,
                    "avg_margin_pct": 0.0,
                    "low_margin_dishes": 0,
                },
            )
            cat["dishes"] += 1
            cat["avg_margin_pct"] += r["gross_margin_pct"]
            if r["margin_band"] == "low":
                cat["low_margin_dishes"] += 1
        for cat in by_cat.values():
            if cat["dishes"]:
                cat["avg_margin_pct"] /= cat["dishes"]
        return list(by_cat.values())
