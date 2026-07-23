"""Stałe modułu Manual Charge."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "manu_charge"
NAME: Final = "Manual Charge"
VERSION: Final = "0.1.0"
MANUFACTURER: Final = "KLR EMS"

PLATFORMS: Final[list[str]] = ["binary_sensor", "number", "switch", "time"]

CONF_CHARGE_CURRENT_ENTITY: Final = "charge_current_entity"
CONF_BATTERY_SOC_ENTITY: Final = "battery_soc_entity"
CONF_NOTIFICATIONS: Final = "notifications"

RECONCILE_INTERVAL: Final = timedelta(minutes=1)
STARTUP_DELAY: Final = 90
INVERTER_ONLINE_DELAY: Final = 15

DEFAULT_PRESET_CURRENT: Final = 200.0
FALLBACK_MAX_CURRENT: Final = 350.0

EVENT_BLOCKING_CHANGED: Final = f"{DOMAIN}_blocking_changed"
NOTIFICATION_ID: Final = f"{DOMAIN}_block"
