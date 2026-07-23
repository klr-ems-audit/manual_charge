"""Przełączniki Manual Charge."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .controller import ManuChargeController
from .entity import ManuChargeEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Utworzenie przełączników."""
    controller: ManuChargeController = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ManuChargeSwitch(controller, "master_switch", "mdi:calendar-clock"),
            ManuChargeSwitch(controller, "range1_enable", "mdi:clock-start"),
            ManuChargeSwitch(controller, "range2_enable", "mdi:clock-start"),
            ManuChargeForceSwitch(controller, "force_now", "mdi:flash-alert"),
        ]
    )


class ManuChargeSwitch(ManuChargeEntity, SwitchEntity, RestoreEntity):
    """Przełącznik z odtwarzaniem stanu po restarcie."""
    _entity_id_format = "switch.{}"

    def __init__(
        self, controller: ManuChargeController, key: str, icon: str
    ) -> None:
        """Inicjalizacja."""
        super().__init__(controller, key)
        self._attr_icon = icon

    @property
    def is_on(self) -> bool:
        """Stan przełącznika."""
        return getattr(self._controller.state, self._key)

    async def async_added_to_hass(self) -> None:
        """Odtworzenie stanu."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_state()) is not None:
            setattr(self._controller.state, self._key, last.state == STATE_ON)
            self.async_write_ha_state()

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Włączenie."""
        setattr(self._controller.state, self._key, True)
        self.async_write_ha_state()
        self._controller.notify_listeners()
        self._controller.async_request_apply()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Wyłączenie."""
        setattr(self._controller.state, self._key, False)
        self.async_write_ha_state()
        self._controller.notify_listeners()
        self._controller.async_request_apply()


class ManuChargeForceSwitch(ManuChargeSwitch):
    """Wymuszenie blokady — celowo NIE przetrwa restartu (samorozbrojenie)."""

    async def async_added_to_hass(self) -> None:
        """Start zawsze w pozycji wyłączonej."""
        await ManuChargeEntity.async_added_to_hass(self)
        self._controller.state.force_now = False
        self.async_write_ha_state()
