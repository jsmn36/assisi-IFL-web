from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    UniqueConstraint,
    CheckConstraint,
    Index,
    Boolean,
    BigInteger,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime, timezone
from decimal import Decimal
from app.database import Base
from app.analytics_database import AnalyticsBase


# =========================
# OPERATIONAL MODELS (OLTP)
# Uses: Base from app.database
# =========================


# -------------------------
# DAILY METRICS (Operational)
# -------------------------
class DailyMetrics(Base):
    __tablename__ = "daily_metrics"

    __table_args__ = (
        UniqueConstraint("property_id", "business_date", name="uq_property_date"),
        Index("idx_property_date", "property_id", "business_date"),
    )

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    business_date = Column(Date, nullable=False)

    # Occupancy
    total_rooms = Column(Integer, nullable=False, default=0)
    occupied_rooms = Column(Integer, nullable=False, default=0)
    available_rooms = Column(Integer, nullable=False, default=0)
    out_of_order_rooms = Column(Integer, nullable=False, default=0)
    occupancy_rate = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))

    # Revenue (in cents)
    room_revenue = Column(Integer, nullable=False, default=0)
    food_beverage_revenue = Column(Integer, nullable=False, default=0)
    other_revenue = Column(Integer, nullable=False, default=0)
    total_revenue = Column(Integer, nullable=False, default=0)

    # ADR / RevPAR
    adr = Column(Integer, nullable=True)
    revpar = Column(Integer, nullable=True)

    # Guests
    arrivals = Column(Integer, nullable=False, default=0)
    departures = Column(Integer, nullable=False, default=0)
    stayovers = Column(Integer, nullable=False, default=0)
    no_shows = Column(Integer, nullable=False, default=0)

    # Reservations
    reservations_made = Column(Integer, nullable=False, default=0)
    reservations_cancelled = Column(Integer, nullable=False, default=0)

    # Housekeeping
    rooms_cleaned = Column(Integer, nullable=False, default=0)
    rooms_inspected = Column(Integer, nullable=False, default=0)

    # Metadata
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    property = relationship("Property", backref="daily_metrics")

    def __repr__(self):
        return f"<DailyMetrics {self.business_date}: {self.occupancy_rate}%"


# -------------------------
# MONTHLY METRICS (Operational)
# -------------------------
class MonthlyMetrics(Base):
    __tablename__ = "monthly_metrics"

    __table_args__ = (
        UniqueConstraint("property_id", "year", "month", name="uq_property_month"),
        CheckConstraint("month >= 1 AND month <= 12", name="check_month_valid"),
    )

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)

    # Occupancy
    avg_occupancy_rate = Column(Numeric(5, 2), nullable=False, default=Decimal("0.00"))
    total_room_nights_sold = Column(Integer, nullable=False, default=0)
    total_room_nights_available = Column(Integer, nullable=False, default=0)

    # Revenue
    total_room_revenue = Column(Integer, nullable=False, default=0)
    total_food_beverage_revenue = Column(Integer, nullable=False, default=0)
    total_other_revenue = Column(Integer, nullable=False, default=0)
    total_revenue = Column(Integer, nullable=False, default=0)

    # Averages
    avg_adr = Column(Integer, nullable=True)
    avg_revpar = Column(Integer, nullable=True)

    # Guests
    total_arrivals = Column(Integer, nullable=False, default=0)
    total_departures = Column(Integer, nullable=False, default=0)
    total_no_shows = Column(Integer, nullable=False, default=0)

    # Reservations
    total_reservations = Column(Integer, nullable=False, default=0)
    total_cancellations = Column(Integer, nullable=False, default=0)
    cancellation_rate = Column(Numeric(5, 2), nullable=True)

    # Metadata
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    property = relationship("Property", backref="monthly_metrics")

    def __repr__(self):
        return (
            f"<MonthlyMetrics {self.year}-{self.month:02d}: {self.avg_occupancy_rate}%"
        )


# -------------------------
# PERFORMANCE KPI
# -------------------------
class PerformanceKPI(Base):
    __tablename__ = "performance_kpis"

    __table_args__ = (Index("idx_property_kpi_period", "property_id", "period_type"),)

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)

    # KPI info
    kpi_name = Column(String(100), nullable=False)
    kpi_category = Column(String(50), nullable=False)

    # Values
    current_value = Column(Numeric(10, 2), nullable=False)
    target_value = Column(Numeric(10, 2), nullable=True)
    previous_value = Column(Numeric(10, 2), nullable=True)

    # Period
    period_type = Column(String(20), nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)

    # Status
    status = Column(String(20), nullable=False)
    variance_percent = Column(Numeric(5, 2), nullable=True)

    # Metadata
    calculated_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    # Relationships
    property = relationship("Property", backref="performance_kpis")

    def __repr__(self):
        return f"<PerformanceKPI {self.kpi_name}: {self.current_value}>"


# =========================
# ANALYTICS MODELS (OLAP/Data Warehouse)
# Uses: AnalyticsBase from app.analytics_database
# =========================


# -------------------------
# FACT RESERVATIONS
# -------------------------
class FactReservations(AnalyticsBase):
    __tablename__ = "fact_reservations"

    reservation_id = Column(Integer, primary_key=True)
    property_id = Column(Integer, nullable=False)
    property_name = Column(String(200))
    guest_id = Column(Integer)
    guest_country = Column(String(2))
    guest_loyalty_tier = Column(String(50))
    room_type_id = Column(Integer)
    room_type_name = Column(String(100))
    channel = Column(String(50))

    booking_date = Column(Date, nullable=False)
    check_in_date = Column(Date, nullable=False)
    check_out_date = Column(Date, nullable=False)

    nights = Column(Integer, nullable=False)
    guests_count = Column(Integer, nullable=False, default=1)
    room_revenue = Column(Numeric(10, 2))
    total_revenue = Column(Numeric(10, 2))
    lead_time_days = Column(Integer)

    status = Column(String(50))

    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_check_in_date", "check_in_date"),
        Index("idx_booking_date", "booking_date"),
        Index("idx_property", "property_id"),
        Index("idx_channel", "channel"),
        Index("idx_status", "status"),
    )


# -------------------------
# FACT STAYS
# -------------------------
class FactStays(AnalyticsBase):
    __tablename__ = "fact_stays"

    stay_id = Column(Integer, primary_key=True)
    reservation_id = Column(Integer)
    room_id = Column(Integer)
    room_number = Column(String(20))

    property_id = Column(Integer, nullable=False)
    guest_id = Column(Integer)
    room_type_id = Column(Integer)
    room_type_name = Column(String(100))

    check_in_date = Column(Date, nullable=False)
    check_in_time = Column(
        String(20)
    )  # Storing TIME as string for sqlite compatibility
    check_out_date = Column(Date, nullable=False)
    check_out_time = Column(String(20))

    nights_actual = Column(Integer)
    room_revenue = Column(Numeric(10, 2))
    food_revenue = Column(Numeric(10, 2))
    beverage_revenue = Column(Numeric(10, 2))
    spa_revenue = Column(Numeric(10, 2))
    other_revenue = Column(Numeric(10, 2))
    total_revenue = Column(Numeric(10, 2))

    status = Column(String(50))

    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_stay_check_in_date", "check_in_date"),
        Index("idx_stay_check_out_date", "check_out_date"),
        Index("idx_stay_room", "room_id"),
        Index("idx_stay_property", "property_id"),
    )


# -------------------------
# FACT CHARGES
# -------------------------
class FactCharges(AnalyticsBase):
    __tablename__ = "fact_charges"

    charge_id = Column(BigInteger, primary_key=True)
    stay_id = Column(Integer)
    reservation_id = Column(Integer)

    property_id = Column(Integer, nullable=False)
    charge_type = Column(String(50))
    department = Column(String(50))

    amount = Column(Numeric(10, 2), nullable=False)
    quantity = Column(Integer)
    unit_price = Column(Numeric(10, 2))

    posted_date = Column(Date, nullable=False)
    description = Column(String(500))

    created_at = Column(DateTime, nullable=False)

    __table_args__ = (
        Index("idx_charge_posted_date", "posted_date"),
        Index("idx_charge_stay", "stay_id"),
        Index("idx_charge_type", "charge_type"),
        Index("idx_charge_property", "property_id"),
    )


# -------------------------
# ETL SYNC LOG
# -------------------------
class EtlSyncLog(AnalyticsBase):
    __tablename__ = "etl_sync_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    table_name = Column(String(100))
    last_sync_at = Column(DateTime)
    records_extracted = Column(Integer)
    records_transformed = Column(Integer)
    records_loaded = Column(Integer)
    duration_seconds = Column(Numeric(10, 2))
    status = Column(String(50))
    error_message = Column(String)
    created_at = Column(DateTime, default=func.now())


# -------------------------
# DAILY METRICS (Analytics)
# Note: Renamed table to avoid collision with operational DailyMetrics
# -------------------------
class AnalyticsDailyMetrics(AnalyticsBase):
    __tablename__ = "analytics_daily_metrics"

    metric_date = Column(Date, primary_key=True)
    property_id = Column(Integer, primary_key=True)

    total_rooms = Column(Integer, nullable=False)
    rooms_occupied = Column(Integer, nullable=False)
    rooms_available = Column(Integer, nullable=False)
    occupancy_percent = Column(Numeric(5, 2), nullable=False)

    room_revenue = Column(Numeric(10, 2), nullable=False)
    food_revenue = Column(Numeric(10, 2), nullable=False)
    beverage_revenue = Column(Numeric(10, 2), nullable=False)
    spa_revenue = Column(Numeric(10, 2), nullable=False)
    other_revenue = Column(Numeric(10, 2), nullable=False)
    total_revenue = Column(Numeric(10, 2), nullable=False)

    adr = Column(Numeric(10, 2))
    revpar = Column(Numeric(10, 2))

    reservations_created = Column(Integer, nullable=False)
    reservations_cancelled = Column(Integer, nullable=False)
    check_ins = Column(Integer, nullable=False)
    check_outs = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("idx_daily_date", "metric_date"),
        Index("idx_daily_property", "property_id"),
    )


# -------------------------
# DIMENSION: PROPERTIES
# -------------------------
class DimProperties(AnalyticsBase):
    __tablename__ = "dim_properties"

    property_id = Column(Integer, primary_key=True)
    property_name = Column(String(200), nullable=False)
    total_rooms = Column(Integer)
    address = Column(String(500))
    city = Column(String(100))
    country = Column(String(2))
    timezone = Column(String(50))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


# -------------------------
# DIMENSION: ROOM TYPES
# -------------------------
class DimRoomTypes(AnalyticsBase):
    __tablename__ = "dim_room_types"

    room_type_id = Column(Integer, primary_key=True)
    property_id = Column(Integer)
    room_type_name = Column(String(100))
    base_occupancy = Column(Integer)
    max_occupancy = Column(Integer)
    size_sqm = Column(Numeric(10, 2))
    created_at = Column(DateTime)
    updated_at = Column(DateTime)


# -------------------------
# DIMENSION: CHANNELS
# -------------------------
class DimChannels(AnalyticsBase):
    __tablename__ = "dim_channels"

    channel_id = Column(String(50), primary_key=True)
    channel_name = Column(String(100))
    channel_type = Column(String(50))
    commission_rate = Column(Numeric(5, 2))
    is_active = Column(Boolean)


# -------------------------
# WEEKLY METRICS
# -------------------------
class WeeklyMetrics(AnalyticsBase):
    __tablename__ = "weekly_metrics"

    week_start_date = Column(Date, primary_key=True)
    property_id = Column(Integer, primary_key=True)
    avg_occupancy_percent = Column(Numeric(5, 2))
    total_revenue = Column(Numeric(10, 2))
    avg_adr = Column(Numeric(10, 2))
    avg_revpar = Column(Numeric(10, 2))
    total_reservations = Column(Integer)
    total_check_ins = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# -------------------------
# MONTHLY METRICS (Analytics)
# Note: Renamed table to avoid collision with operational MonthlyMetrics
# -------------------------
class AnalyticsMonthlyMetrics(AnalyticsBase):
    __tablename__ = "analytics_monthly_metrics"

    year = Column(Integer, primary_key=True)
    month = Column(Integer, primary_key=True)
    property_id = Column(Integer, primary_key=True)
    avg_occupancy_percent = Column(Numeric(5, 2))
    total_revenue = Column(Numeric(10, 2))
    avg_adr = Column(Numeric(10, 2))
    avg_revpar = Column(Numeric(10, 2))
    total_reservations = Column(Integer)
    total_guests = Column(Integer)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# -------------------------
# ROOM TYPE PERFORMANCE
# -------------------------
class RoomTypePerformance(AnalyticsBase):
    __tablename__ = "room_type_performance"

    metric_date = Column(Date, primary_key=True)
    property_id = Column(Integer, primary_key=True)
    room_type_id = Column(Integer, primary_key=True)
    total_rooms = Column(Integer)
    rooms_occupied = Column(Integer)
    occupancy_percent = Column(Numeric(5, 2))
    revenue = Column(Numeric(10, 2))
    adr = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


# -------------------------
# CHANNEL PERFORMANCE
# -------------------------
class ChannelPerformance(AnalyticsBase):
    __tablename__ = "channel_performance"

    metric_date = Column(Date, primary_key=True)
    property_id = Column(Integer, primary_key=True)
    channel = Column(String(50), primary_key=True)
    bookings_count = Column(Integer)
    revenue = Column(Numeric(10, 2))
    avg_booking_value = Column(Numeric(10, 2))
    cancellation_rate = Column(Numeric(5, 2))
    avg_lead_time_days = Column(Numeric(5, 1))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
