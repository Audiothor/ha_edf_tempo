"""EDF Tempo integration for Home Assistant."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import DOMAIN, COORDINATOR
from .coordinator import EDFTempoCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "binary_sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up EDF Tempo from a config entry."""
    coordinator = EDFTempoCoordinator(hass)

    await coordinator.async_config_entry_first_refresh()

    if coordinator.last_exception:
        raise ConfigEntryNotReady from coordinator.last_exception

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {COORDINATOR: coordinator}

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Re-fetch when options are changed (tariff updates)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update (tariff change)."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload EDF Tempo config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: EDFTempoCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
        if coordinator._session and not coordinator._session.closed:
            await coordinator._session.close()
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok
