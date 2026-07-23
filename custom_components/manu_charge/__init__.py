"""KLR EMS — Manual Charge."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, PLATFORMS
from .controller import ManuChargeController

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Konfiguracja wpisu."""
    controller = ManuChargeController(hass, entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = controller

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await controller.async_setup()

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Usunięcie wpisu."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Przeładowanie po zmianie opcji."""
    await hass.config_entries.async_reload(entry.entry_id)
