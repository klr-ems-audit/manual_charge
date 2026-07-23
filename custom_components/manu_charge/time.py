"""Encje czasu — granice zakresów."""

from __future__ import annotations

from datetime import time as dt_time

from homeassistant.components.time import TimeEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .controller import ManuChargeController
from .entity import ManuChargeEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Utworzenie encji czasu."""
    controller: ManuChargeController = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ManuChargeTime(controller, "range1_on"),
            ManuChargeTime(controller, "range1_off"),
            ManuChargeTime(controller, "range2_on"),
            ManuChargeTime(controller, "range2_off"),
        ]
    )


class ManuChargeTime(ManuChargeEntity, TimeEntity, RestoreEntity):
    """Godzina graniczna zakresu."""
    _entity_id_format = "time.{}"

    _attr_icon = "mdi:clock-outline"

    @property
    def native_value(self) -> dt_time:
        """Ustawiona godzina."""
        return getattr(self._controller.state, self._key)

    async def async_added_to_hass(self) -> None:
        """Odtworzenie godziny."""
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None:
            try:
                parts = [int(p) for p in last.state.split(":")]
                while len(parts) < 3:
                    parts.append(0)
                setattr(
                    self._controller.state,
                    self._key,
                    dt_time(parts[0], parts[1], parts[2]),
                )
                self.async_write_ha_state()
            except (TypeError, ValueError):
                pass

    async def async_set_value(self, value: dt_time) -> None:
        """Zapis nowej godziny."""
        setattr(self._controller.state, self._key, value)
        self.async_write_ha_state()
        self._controller.notify_listeners()
        self._controller.async_request_apply()
