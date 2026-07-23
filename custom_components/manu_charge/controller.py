"""Logika sterująca prądem ładowania magazynu."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import time as dt_time
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    ATTR_ENTITY_ID,
    EVENT_HOMEASSISTANT_STARTED,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_state_change_event,
    async_track_time_interval,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_BATTERY_SOC_ENTITY,
    CONF_CHARGE_CURRENT_ENTITY,
    CONF_NOTIFICATIONS,
    DEFAULT_PRESET_CURRENT,
    EVENT_BLOCKING_CHANGED,
    FALLBACK_MAX_CURRENT,
    INVERTER_ONLINE_DELAY,
    NOTIFICATION_ID,
    RECONCILE_INTERVAL,
    STARTUP_DELAY,
)

_LOGGER = logging.getLogger(__name__)

_INVALID = (STATE_UNAVAILABLE, STATE_UNKNOWN, None, "")


def in_window(now: dt_time, start: dt_time, end: dt_time) -> bool:
    """Czy czas mieści się w oknie. Obsługuje przejście przez północ.

    UWAGA: start == koniec traktujemy jako okno ZAMKNIETE (odstepstwo od
    wersji YAML, w ktorej taki przypadek dawal okno zawsze aktywne).
    """
    if start == end:
        return False
    if start < end:
        return start <= now < end
    return now >= start or now < end


@dataclass
class ManuChargeState:
    """Stan operacyjny modułu — odtwarzany po restarcie."""

    master_switch: bool = False
    force_now: bool = False
    range1_enable: bool = False
    range2_enable: bool = False
    range1_on: dt_time = dt_time(0, 0)
    range1_off: dt_time = dt_time(0, 0)
    range2_on: dt_time = dt_time(0, 0)
    range2_off: dt_time = dt_time(0, 0)
    range1_soc: float = 0.0
    range2_soc: float = 0.0
    saved_current: float = 0.0
    preset_current: float = DEFAULT_PRESET_CURRENT


class ManuChargeController:
    """Jedno źródło prawdy docelowego prądu ładowania."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Inicjalizacja kontrolera."""
        self.hass = hass
        self.entry = entry
        self.state = ManuChargeState()
        self._listeners: list[Callable[[], None]] = []
        self._lock = asyncio.Lock()
        self._last_blocking: bool | None = None

        merged = {**entry.data, **entry.options}
        self._charge_entity: str = merged[CONF_CHARGE_CURRENT_ENTITY]
        self._soc_entity: str = merged[CONF_BATTERY_SOC_ENTITY]
        self._notifications: bool = merged.get(CONF_NOTIFICATIONS, False)

    # -- rejestracja encji ------------------------------------------------

    @callback
    def register_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Rejestruje encję do odświeżania. Zwraca funkcję wyrejestrowującą."""
        self._listeners.append(listener)

        @callback
        def _remove() -> None:
            if listener in self._listeners:
                self._listeners.remove(listener)

        return _remove

    @callback
    def async_request_apply(self) -> None:
        """Zleca uzgodnienie w tle — NIE blokuje interfejsu."""
        self.hass.async_create_task(self.async_apply())

    @callback
    def notify_listeners(self) -> None:
        """Odświeża wszystkie encje modułu."""
        for listener in self._listeners:
            listener()

    # -- odczyt encji zewnętrznych ----------------------------------------

    def _read_float(self, entity_id: str, default: float) -> float:
        """Bezpieczny odczyt wartości liczbowej encji."""
        state = self.hass.states.get(entity_id)
        if state is None or state.state in _INVALID:
            return default
        try:
            return float(state.state)
        except (TypeError, ValueError):
            return default

    @property
    def max_current(self) -> float:
        """Górny limit prądu odczytany z encji falownika."""
        state = self.hass.states.get(self._charge_entity)
        if state is not None:
            raw = state.attributes.get("max")
            try:
                if raw is not None:
                    return float(raw)
            except (TypeError, ValueError):
                pass
        return FALLBACK_MAX_CURRENT

    # -- logika blokady ---------------------------------------------------

    @property
    def blocking(self) -> bool:
        """Czy blokada ładowania jest aktywna."""
        s = self.state
        if s.force_now:
            return True
        if not s.master_switch:
            return False

        now = dt_util.now().time()
        soc = self._read_float(self._soc_entity, 0.0)

        r1 = (
            s.range1_enable
            and in_window(now, s.range1_on, s.range1_off)
            and soc > s.range1_soc
        )
        r2 = (
            s.range2_enable
            and in_window(now, s.range2_on, s.range2_off)
            and soc > s.range2_soc
        )
        return r1 or r2

    # -- pętla uzgadniająca -----------------------------------------------

    async def async_apply(self, *_: Any) -> None:
        """Uzgadnia prąd falownika ze stanem docelowym. Idempotentne."""
        async with self._lock:
            blocking = self.blocking
            current = self._read_float(self._charge_entity, -1.0)

            if current < 0:
                _LOGGER.debug("Falownik niedostępny — cykl pominięty")
                self.notify_listeners()
                return

            saved = self.state.saved_current
            preset = self.state.preset_current
            target = 0.0 if blocking else (saved if saved > 0 else preset)

            if blocking and current > 0:
                # Wejście w blokadę: zapamiętaj prąd PRZED wyzerowaniem
                self.state.saved_current = current
                await self._async_set_current(0.0)
                await self._async_announce(True, current, 0.0)
            elif current != target:
                await self._async_set_current(target)
                await self._async_announce(blocking, current, target)

            self._last_blocking = blocking
            self.notify_listeners()

    async def _async_set_current(self, value: float) -> None:
        """Ustawia prąd ładowania na falowniku."""
        _LOGGER.debug("Ustawiam %s = %s A", self._charge_entity, int(value))
        try:
            await self.hass.services.async_call(
                "number",
                "set_value",
                {ATTR_ENTITY_ID: self._charge_entity, "value": int(value)},
                blocking=True,
            )
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Nie udalo sie ustawic %s", self._charge_entity)

    async def _async_announce(
        self, blocking: bool, previous: float, target: float
    ) -> None:
        """Emituje zdarzenie i opcjonalne powiadomienie."""
        self.hass.bus.async_fire(
            EVENT_BLOCKING_CHANGED,
            {
                "entry_id": self.entry.entry_id,
                "blocking": blocking,
                "previous_current": previous,
                "target_current": target,
            },
        )

        if not self._notifications:
            return
        if blocking:
            title = "manu_charge: blokada aktywna"
            message = f"Prąd ładowania zablokowany (0 A). Zapisano: {previous} A"
        else:
            title = "manu_charge: ładowanie przywrócone"
            message = f"Prąd ładowania przywrócony: {int(target)} A"

        await self.hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": title,
                "message": message,
                "notification_id": NOTIFICATION_ID,
            },
            blocking=False,
        )

    # -- cykl życia -------------------------------------------------------

    async def async_setup(self) -> None:
        """Uruchamia wyzwalacze uzgadniania."""
        entry = self.entry

        entry.async_on_unload(
            async_track_time_interval(
                self.hass, self.async_apply, RECONCILE_INTERVAL
            )
        )
        entry.async_on_unload(
            async_track_state_change_event(
                self.hass, [self._charge_entity], self._async_charge_changed
            )
        )
        entry.async_on_unload(
            async_track_state_change_event(
                self.hass, [self._soc_entity], self._async_soc_changed
            )
        )

        if self.hass.is_running:
            async_call_later(self.hass, INVERTER_ONLINE_DELAY, self.async_apply)
        else:
            entry.async_on_unload(
                self.hass.bus.async_listen_once(
                    EVENT_HOMEASSISTANT_STARTED, self._async_ha_started
                )
            )

    @callback
    def _async_ha_started(self, _event: Event) -> None:
        """Po starcie HA — uzgodnienie z opóźnieniem stabilizacyjnym."""
        async_call_later(self.hass, STARTUP_DELAY, self.async_apply)

    @callback
    def _async_charge_changed(self, event: Event) -> None:
        """Powrót falownika online — uzgodnienie po chwili stabilizacji."""
        old = event.data.get("old_state")
        new = event.data.get("new_state")
        if new is None or new.state in _INVALID:
            return
        if old is None or old.state in _INVALID:
            async_call_later(self.hass, INVERTER_ONLINE_DELAY, self.async_apply)

    @callback
    def _async_soc_changed(self, _event: Event) -> None:
        """Zmiana SOC może zmienić warunek blokady."""
        self.hass.async_create_task(self.async_apply())
