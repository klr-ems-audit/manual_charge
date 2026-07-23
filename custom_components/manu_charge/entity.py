"""Klasa bazowa encji — grupuje wszystko pod jednym urządzeniem."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity import Entity, async_generate_entity_id

from .const import DOMAIN, MANUFACTURER, NAME, VERSION
from .controller import ManuChargeController


class ManuChargeEntity(Entity):
    """Wspólna baza encji modułu.

    Identyfikator encji jest narzucany jawnie (prefiks domeny + klucz),
    aby był IDENTYCZNY niezależnie od języka interfejsu użytkownika.
    Bez tego HA zbudowałby entity_id z przetłumaczonej nazwy, co uniemożliwia
    dostarczenie z modułem gotowej karty dashboardu.
    """

    _attr_has_entity_name = True
    _attr_should_poll = False

    # Nadpisywane w każdej platformie, np. "switch.{}"
    _entity_id_format: str | None = None

    def __init__(self, controller: ManuChargeController, key: str) -> None:
        """Inicjalizacja encji."""
        self._controller = controller
        self._key = key
        self._attr_unique_id = f"{controller.entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, controller.entry.entry_id)},
            name=NAME,
            manufacturer=MANUFACTURER,
            model="Deye battery charge control",
            sw_version=VERSION,
        )

        if self._entity_id_format:
            self.entity_id = async_generate_entity_id(
                self._entity_id_format,
                f"{DOMAIN}_{key}",
                hass=controller.hass,
            )

    async def async_added_to_hass(self) -> None:
        """Podpięcie do powiadomień kontrolera."""
        await super().async_added_to_hass()
        self.async_on_remove(
            self._controller.register_listener(self.async_write_ha_state)
        )
