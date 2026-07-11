"""
Day 26 report builder service.
Builds report payloads from PMS source-of-truth tables.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.models import Charge, Guest, Reservation, Room, RoomType


def _enum_value(value: Any) -> str:
    if value is None:
        return ""
    return str(value.value) if hasattr(value, "value") else str(value)


def _f(value: Any) -> float:
    return float(value or 0)


class ReportBuilderService:
    TEMPLATE_CATALOG: dict[str, dict[str, str]] = {
        "revenue_summary": {
            "category": "revenue",
            "name": "Revenue Summary",
            "description": "Revenue totals and averages.",
        },
        "revenue_daily_trend": {
            "category": "revenue",
            "name": "Revenue Daily Trend",
            "description": "Revenue by day.",
        },
        "revenue_by_source": {
            "category": "revenue",
            "name": "Revenue by Source",
            "description": "Revenue by booking source.",
        },
        "revenue_by_room_type": {
            "category": "revenue",
            "name": "Revenue by Room Type",
            "description": "Revenue by room type.",
        },
        "revenue_by_charge_type": {
            "category": "revenue",
            "name": "Revenue by Charge Type",
            "description": "Revenue by charge type.",
        },
        "occupancy_summary": {
            "category": "occupancy",
            "name": "Occupancy Summary",
            "description": "Occupancy summary KPIs.",
        },
        "occupancy_daily_trend": {
            "category": "occupancy",
            "name": "Occupancy Daily Trend",
            "description": "Occupancy by day.",
        },
        "occupancy_by_room_type": {
            "category": "occupancy",
            "name": "Occupancy by Room Type",
            "description": "Room nights by room type.",
        },
        "occupancy_weekday_pattern": {
            "category": "occupancy",
            "name": "Occupancy Weekday Pattern",
            "description": "Average occupancy by weekday.",
        },
        "guest_acquisition": {
            "category": "guest",
            "name": "Guest Acquisition",
            "description": "New and active guest metrics.",
        },
        "guest_retention": {
            "category": "guest",
            "name": "Guest Retention",
            "description": "Repeat-guest metrics.",
        },
        "guest_geography": {
            "category": "guest",
            "name": "Guest Geography",
            "description": "Country mix of guests.",
        },
        "guest_lead_time": {
            "category": "guest",
            "name": "Guest Lead Time",
            "description": "Lead-time distribution.",
        },
        "reservation_status_mix": {
            "category": "reservation",
            "name": "Reservation Status Mix",
            "description": "Reservation counts by status.",
        },
        "reservation_pickup": {
            "category": "reservation",
            "name": "Reservation Pickup",
            "description": "Bookings created by day.",
        },
        "cancellation_analysis": {
            "category": "reservation",
            "name": "Cancellation Analysis",
            "description": "Cancellation rate and counts.",
        },
        "no_show_analysis": {
            "category": "reservation",
            "name": "No Show Analysis",
            "description": "No-show rate and counts.",
        },
        "checkin_checkout_flow": {
            "category": "operations",
            "name": "Check-in/Check-out Flow",
            "description": "Daily check-in and check-out flow.",
        },
        "housekeeping_workload": {
            "category": "operations",
            "name": "Housekeeping Workload",
            "description": "Turnover workload estimate.",
        },
        "stay_duration_distribution": {
            "category": "operations",
            "name": "Stay Duration Distribution",
            "description": "Distribution of stay lengths.",
        },
        "outstanding_balance": {
            "category": "financial",
            "name": "Outstanding Balance",
            "description": "Open receivables and pending charges.",
        },
        "payment_collection": {
            "category": "financial",
            "name": "Payment Collection",
            "description": "Collected amounts by method.",
        },
    }

    def __init__(self, db: Session):
        self.db = db
        self._pd, self._np = self._try_data_stack()

    @staticmethod
    def _try_data_stack():
        try:
            import pandas as pd  # type: ignore
            import numpy as np  # type: ignore

            return pd, np
        except Exception:
            return None, None

    def list_templates(self) -> list[dict[str, str]]:
        templates = []
        for template_id, meta in self.TEMPLATE_CATALOG.items():
            templates.append(
                {
                    "template_id": template_id,
                    "category": meta["category"],
                    "name": meta["name"],
                    "description": meta["description"],
                }
            )
        return sorted(templates, key=lambda x: (x["category"], x["name"]))

    def get_template_metadata(self, template_id: str) -> dict[str, str]:
        meta = self.TEMPLATE_CATALOG.get(template_id)
        if meta is None:
            raise ValueError(f"Unknown report template: {template_id}")
        return {
            "template_id": template_id,
            "category": meta["category"],
            "name": meta["name"],
            "description": meta["description"],
        }

    def generate_template_report(
        self, template_id: str, property_id: int, start_date: date, end_date: date
    ) -> dict[str, Any]:
        if template_id not in self.TEMPLATE_CATALOG:
            raise ValueError(f"Unknown report template: {template_id}")

        if template_id == "revenue_summary":
            body = self._revenue_summary(property_id, start_date, end_date)
        elif template_id == "revenue_daily_trend":
            body = self._revenue_daily(property_id, start_date, end_date)
        elif template_id in {"revenue_by_source", "revenue_by_room_type"}:
            key = "source" if template_id == "revenue_by_source" else "room_type_name"
            label = "source" if template_id == "revenue_by_source" else "room_type"
            body = self._revenue_grouped(property_id, start_date, end_date, key, label)
        elif template_id == "revenue_by_charge_type":
            body = self._charge_revenue_grouped(property_id, start_date, end_date)
        elif template_id in {"occupancy_summary", "occupancy_daily_trend"}:
            body = self._occupancy(
                property_id,
                start_date,
                end_date,
                with_daily=(template_id == "occupancy_daily_trend"),
            )
        elif template_id in {"occupancy_by_room_type", "occupancy_weekday_pattern"}:
            body = self._occupancy_breakdowns(property_id, start_date, end_date)
        elif template_id in {
            "guest_acquisition",
            "guest_retention",
            "guest_geography",
            "guest_lead_time",
        }:
            body = self._guest_reports(property_id, start_date, end_date)
        elif template_id in {
            "reservation_status_mix",
            "reservation_pickup",
            "cancellation_analysis",
            "no_show_analysis",
        }:
            body = self._reservation_reports(property_id, start_date, end_date)
        elif template_id in {"checkin_checkout_flow", "housekeeping_workload"}:
            body = self._operations_reports(property_id, start_date, end_date)
        elif template_id == "stay_duration_distribution":
            body = self._stay_duration_distribution(property_id, start_date, end_date)
        elif template_id in {"outstanding_balance", "payment_collection"}:
            body = self._financial_reports(property_id, start_date, end_date)
        else:
            body = {"summary": {}}

        body["template"] = self.get_template_metadata(template_id)
        body["period"] = {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }
        body["generated_at"] = datetime.now(timezone.utc).isoformat()
        body["engine"] = {
            "pandas_enabled": self._pd is not None,
            "numpy_enabled": self._np is not None,
        }
        return body

    def _reservations(
        self, property_id: int, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        rows = (
            self.db.query(
                Reservation.id.label("reservation_id"),
                Reservation.guest_id,
                Reservation.status,
                Reservation.source,
                Reservation.check_in_date,
                Reservation.check_out_date,
                Reservation.created_at,
                Reservation.number_of_nights,
                Reservation.total_amount,
                RoomType.name.label("room_type_name"),
            )
            .outerjoin(RoomType, RoomType.id == Reservation.room_type_id)
            .filter(
                Reservation.property_id == property_id,
                Reservation.check_out_date > start_date,
                Reservation.check_in_date <= end_date,
            )
            .all()
        )
        return [
            {
                "reservation_id": row.reservation_id,
                "guest_id": row.guest_id,
                "status": _enum_value(row.status).lower(),
                "source": _enum_value(row.source).lower() or "unknown",
                "check_in_date": row.check_in_date,
                "check_out_date": row.check_out_date,
                "created_at": row.created_at,
                "booking_date": row.created_at.date() if row.created_at else None,
                "number_of_nights": row.number_of_nights or 0,
                "total_amount": _f(row.total_amount),
                "room_type_name": row.room_type_name or "Unassigned",
            }
            for row in rows
        ]

    def _charges(
        self, property_id: int, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        rows = (
            self.db.query(
                Charge.id.label("charge_id"),
                Charge.charge_type,
                Charge.status,
                Charge.amount,
                Charge.total_amount,
                Charge.charge_date,
                Charge.payment_method,
            )
            .filter(
                Charge.property_id == property_id,
                Charge.charge_date.isnot(None),
                Charge.charge_date >= start_date,
                Charge.charge_date <= end_date,
            )
            .all()
        )
        items = []
        for row in rows:
            charge_date = row.charge_date
            total = row.total_amount if row.total_amount is not None else row.amount
            items.append(
                {
                    "charge_id": row.charge_id,
                    "charge_type": _enum_value(row.charge_type).lower() or "other",
                    "status": _enum_value(row.status).lower(),
                    "total_amount": _f(total),
                    "charge_date": charge_date,
                    "payment_method": (row.payment_method or "unknown").lower(),
                }
            )
        return items

    def _daily_occupancy(
        self, property_id: int, start_date: date, end_date: date
    ) -> list[dict[str, Any]]:
        total_rooms = (
            self.db.query(func.count(Room.id))
            .filter(Room.property_id == property_id, Room.is_active.is_(True))
            .scalar()
        ) or 0
        total_rooms = int(total_rooms or 1)
        rows = self._reservations(property_id, start_date, end_date)
        inactive = {"cancelled", "noshow", "no_show"}
        days = []
        cursor = start_date
        while cursor <= end_date:
            occupied = 0
            for row in rows:
                if row["status"] in inactive:
                    continue
                if row["check_in_date"] <= cursor < row["check_out_date"]:
                    occupied += 1
            days.append(
                {
                    "date": cursor.isoformat(),
                    "occupied_rooms": occupied,
                    "available_rooms": max(total_rooms - occupied, 0),
                    "occupancy_rate": round((occupied / total_rooms) * 100, 2),
                }
            )
            cursor += timedelta(days=1)
        return days

    def _revenue_summary(
        self, property_id: int, start_date: date, end_date: date
    ) -> dict[str, Any]:
        charges = [
            c
            for c in self._charges(property_id, start_date, end_date)
            if c["status"] not in {"voided", "disputed", "refunded"}
        ]
        reservations = self._reservations(property_id, start_date, end_date)
        total = round(sum(c["total_amount"] for c in charges), 2)
        booked = round(sum(r["total_amount"] for r in reservations), 2)
        days = max((end_date - start_date).days + 1, 1)
        return {
            "summary": {
                "recognized_revenue": total,
                "booked_revenue": booked,
                "avg_daily_revenue": round(total / days, 2),
                "avg_booking_value": round(booked / max(len(reservations), 1), 2),
                "charges_count": len(charges),
            }
        }

    def _revenue_daily(
        self, property_id: int, start_date: date, end_date: date
    ) -> dict[str, Any]:
        charges = [
            c
            for c in self._charges(property_id, start_date, end_date)
            if c["status"] not in {"voided", "disputed", "refunded"}
        ]
        totals = defaultdict(float)
        for charge in charges:
            if charge["charge_date"] is not None:
                totals[charge["charge_date"].isoformat()] += charge["total_amount"]
        daily = []
        cursor = start_date
        while cursor <= end_date:
            key = cursor.isoformat()
            daily.append({"date": key, "revenue": round(totals.get(key, 0.0), 2)})
            cursor += timedelta(days=1)
        return {"daily": daily}

    def _revenue_grouped(
        self, property_id: int, start_date: date, end_date: date, key: str, label: str
    ) -> dict[str, Any]:
        grouped = defaultdict(float)
        for row in self._reservations(property_id, start_date, end_date):
            if row["status"] != "cancelled":
                grouped[row[key]] += row["total_amount"]
        data = [
            {label: name, "revenue": round(value, 2)} for name, value in grouped.items()
        ]
        data.sort(key=lambda item: item["revenue"], reverse=True)
        return {"items": data}

    def _charge_revenue_grouped(
        self, property_id: int, start_date: date, end_date: date
    ) -> dict[str, Any]:
        grouped = defaultdict(float)
        for charge in self._charges(property_id, start_date, end_date):
            if charge["status"] not in {"voided", "disputed", "refunded"}:
                grouped[charge["charge_type"]] += charge["total_amount"]
        items = [{"charge_type": k, "revenue": round(v, 2)} for k, v in grouped.items()]
        items.sort(key=lambda x: x["revenue"], reverse=True)
        return {"items": items}

    def _occupancy(
        self, property_id: int, start_date: date, end_date: date, with_daily: bool
    ) -> dict[str, Any]:
        daily = self._daily_occupancy(property_id, start_date, end_date)
        rates = [item["occupancy_rate"] for item in daily]
        payload = {
            "summary": {
                "avg_occupancy_rate": round(sum(rates) / max(len(rates), 1), 2),
                "max_occupancy_rate": round(max(rates) if rates else 0.0, 2),
                "min_occupancy_rate": round(min(rates) if rates else 0.0, 2),
                "occupied_room_nights": sum(item["occupied_rooms"] for item in daily),
            }
        }
        if with_daily:
            payload["daily"] = daily
        return payload

    def _occupancy_breakdowns(
        self, property_id: int, start_date: date, end_date: date
    ) -> dict[str, Any]:
        by_room_type = defaultdict(int)
        for row in self._reservations(property_id, start_date, end_date):
            if row["status"] not in {"cancelled", "noshow", "no_show"}:
                by_room_type[row["room_type_name"]] += max(row["number_of_nights"], 0)
        weekday = defaultdict(list)
        for row in self._daily_occupancy(property_id, start_date, end_date):
            dow = datetime.fromisoformat(row["date"]).weekday()
            weekday[dow].append(row["occupancy_rate"])
        weekday_labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        weekday_data = [
            {
                "weekday": weekday_labels[i],
                "avg_occupancy_rate": round(
                    sum(weekday[i]) / max(len(weekday[i]), 1), 2
                ),
            }
            for i in range(7)
        ]
        room_data = [
            {"room_type": k, "room_nights": v} for k, v in by_room_type.items()
        ]
        room_data.sort(key=lambda x: x["room_nights"], reverse=True)
        return {"by_room_type": room_data, "weekday_pattern": weekday_data}

    def _guest_reports(
        self, property_id: int, start_date: date, end_date: date
    ) -> dict[str, Any]:
        reservations = self._reservations(property_id, start_date, end_date)
        guest_counts = Counter(
            r["guest_id"] for r in reservations if r["guest_id"] is not None
        )
        repeat_guests = sum(1 for _, n in guest_counts.items() if n > 1)
        new_guests = (
            self.db.query(func.count(Guest.id))
            .join(Reservation, Reservation.guest_id == Guest.id)
            .filter(
                Reservation.property_id == property_id,
                Guest.created_at.isnot(None),
                func.date(Guest.created_at) >= start_date,
                func.date(Guest.created_at) <= end_date,
            )
            .scalar()
        ) or 0
        geography_rows = (
            self.db.query(Guest.country)
            .join(Reservation, Reservation.guest_id == Guest.id)
            .filter(
                Reservation.property_id == property_id,
                Reservation.check_out_date > start_date,
                Reservation.check_in_date <= end_date,
            )
            .all()
        )
        countries = Counter(
            (row.country or "Unknown").upper() for row in geography_rows
        )
        lead_times = []
        for row in reservations:
            if row["booking_date"] and row["check_in_date"]:
                delta = (row["check_in_date"] - row["booking_date"]).days
                if delta >= 0:
                    lead_times.append(delta)
        return {
            "summary": {
                "new_guests": int(new_guests),
                "active_guests": len(guest_counts),
                "repeat_guests": repeat_guests,
                "retention_rate_percent": round(
                    (repeat_guests / max(len(guest_counts), 1)) * 100, 2
                ),
                "avg_lead_time_days": round(
                    sum(lead_times) / max(len(lead_times), 1), 2
                ),
            },
            "by_country": [
                {"country": c, "guests": n} for c, n in countries.most_common()
            ],
        }

    def _reservation_reports(
        self, property_id: int, start_date: date, end_date: date
    ) -> dict[str, Any]:
        reservations = self._reservations(property_id, start_date, end_date)
        status_mix = Counter(r["status"] for r in reservations)
        pickup = defaultdict(int)
        for row in reservations:
            if row["booking_date"] is not None:
                pickup[row["booking_date"].isoformat()] += 1
        cancelled = status_mix.get("cancelled", 0)
        no_show = status_mix.get("noshow", 0) + status_mix.get("no_show", 0)
        total = len(reservations)
        return {
            "status_mix": [{"status": k, "count": v} for k, v in status_mix.items()],
            "daily_pickup": [
                {"date": k, "bookings": v} for k, v in sorted(pickup.items())
            ],
            "summary": {
                "total_reservations": total,
                "cancelled_reservations": cancelled,
                "no_show_reservations": no_show,
                "cancellation_rate_percent": round(
                    (cancelled / max(total, 1)) * 100, 2
                ),
                "no_show_rate_percent": round((no_show / max(total, 1)) * 100, 2),
            },
        }

    def _operations_reports(
        self, property_id: int, start_date: date, end_date: date
    ) -> dict[str, Any]:
        rows = self._reservations(property_id, start_date, end_date)
        check_ins = Counter()
        check_outs = Counter()
        for row in rows:
            if row["check_in_date"] and start_date <= row["check_in_date"] <= end_date:
                check_ins[row["check_in_date"].isoformat()] += 1
            if (
                row["check_out_date"]
                and start_date <= row["check_out_date"] <= end_date
            ):
                check_outs[row["check_out_date"].isoformat()] += 1
        flow = []
        cursor = start_date
        while cursor <= end_date:
            key = cursor.isoformat()
            departures = check_outs.get(key, 0)
            flow.append(
                {
                    "date": key,
                    "check_ins": check_ins.get(key, 0),
                    "check_outs": departures,
                    "recommended_staff_units": max(
                        1, departures // 3 + (1 if departures % 3 else 0)
                    ),
                }
            )
            cursor += timedelta(days=1)
        return {"daily_flow": flow}

    def _stay_duration_distribution(
        self, property_id: int, start_date: date, end_date: date
    ) -> dict[str, Any]:
        bins = {"1_night": 0, "2_3_nights": 0, "4_7_nights": 0, "8_plus_nights": 0}
        for row in self._reservations(property_id, start_date, end_date):
            n = max(row["number_of_nights"], 0)
            if n <= 1:
                bins["1_night"] += 1
            elif n <= 3:
                bins["2_3_nights"] += 1
            elif n <= 7:
                bins["4_7_nights"] += 1
            else:
                bins["8_plus_nights"] += 1
        return {
            "distribution": [{"bucket": k, "reservations": v} for k, v in bins.items()]
        }

    def _financial_reports(
        self, property_id: int, start_date: date, end_date: date
    ) -> dict[str, Any]:
        charges = self._charges(property_id, start_date, end_date)
        open_charges = [
            c for c in charges if c["status"] in {"pending", "posted", "disputed"}
        ]
        paid = [c for c in charges if c["status"] == "paid"]
        by_method = defaultdict(float)
        for charge in paid:
            by_method[charge["payment_method"]] += charge["total_amount"]
        method_items = [
            {"payment_method": k, "amount": round(v, 2)} for k, v in by_method.items()
        ]
        method_items.sort(key=lambda x: x["amount"], reverse=True)
        return {
            "summary": {
                "open_charge_count": len(open_charges),
                "outstanding_amount": round(
                    sum(c["total_amount"] for c in open_charges), 2
                ),
                "collected_amount": round(sum(c["total_amount"] for c in paid), 2),
            },
            "by_payment_method": method_items,
        }
