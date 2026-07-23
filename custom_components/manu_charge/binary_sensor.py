"""Sensor stanu blokady."""

from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .controller import ManuChargeController
from .entity import ManuChargeEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Utworzenie sensora."""
    controller: ManuChargeController = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ManuChargeBlockingSensor(controller, "blocking_active")])


class ManuChargeBlockingSensor(ManuChargeEntity, BinarySensorEntity):
    """Czy blokada ładowania jest aktywna."""
    _entity_id_format = "binary_sensor.{}"

    @property
    def is_on(self) -> bool:
        """Stan blokady."""
        return self._controller.blocking

    @property
    def icon(self) -> str:
        """Ikona zależna od stanu."""
        return "mdi:battery-off" if self.is_on else "mdi:battery-charging"
