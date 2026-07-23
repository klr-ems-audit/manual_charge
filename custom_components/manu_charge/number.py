"""Encje liczbowe Manual Charge."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, EntityCategory, UnitOfElectricCurrent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DOMAIN
from .controller import ManuChargeController
from .entity import ManuChargeEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Utworzenie encji liczbowych."""
    controller: ManuChargeController = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ManuChargeSoc(controller, "range1_soc"),
            ManuChargeSoc(controller, "range2_soc"),
            ManuChargeCurrent(controller, "preset_current"),
            ManuChargeCurrent(controller, "saved_current", diagnostic=True),
        ]
    )


class ManuChargeNumberBase(ManuChargeEntity, NumberEntity, RestoreEntity):
    """Baza encji liczbowej z odtwarzaniem wartości."""
    _entity_id_format = "number.{}"

    _attr_mode = NumberMode.BOX

    @property
    def native_value(self) -> float:
        """Bieżąca wartość."""
        return getattr(self._controller.state, self._key)

    async def async_added_to_hass(self) -> None:
        """Odtworzenie wartości."""
        await super().async_added_to_hass()
        last = await self.async_get_last_state()
        if last is not None:
            try:
                setattr(self._controller.state, self._key, float(last.state))
                self.async_write_ha_state()
            except (TypeError, ValueError):
                pass

    async def async_set_native_value(self, value: float) -> None:
        """Zapis nowej wartości."""
        setattr(self._controller.state, self._key, value)
        self.async_write_ha_state()
        self._controller.notify_listeners()
        self._controller.async_request_apply()


class ManuChargeSoc(ManuChargeNumberBase):
    """Próg SOC dla zakresu."""

    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:battery-charging"


class ManuChargeCurrent(ManuChargeNumberBase):
    """Wartość prądu ładowania."""

    _attr_native_min_value = 0
    _attr_native_step = 1
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_icon = "mdi:current-dc"

    def __init__(
        self,
        controller: ManuChargeController,
        key: str,
        diagnostic: bool = False,
    ) -> None:
        """Inicjalizacja."""
        super().__init__(controller, key)
        if diagnostic:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_max_value(self) -> float:
        """Limit odczytany z encji falownika."""
        return self._controller.max_current
