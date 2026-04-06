"""Binary sensors for EDF Tempo integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorEntity, BinarySensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, COORDINATOR
from .coordinator import EDFTempoCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EDFTempoCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]
    async_add_entities([
        HeureCreuseBinarySensor(coordinator, entry),
        JourRougeBinarySensor(coordinator, entry),
        JourBlancBinarySensor(coordinator, entry),
        JourBleuBinarySensor(coordinator, entry),
        DemainRougeBinarySensor(coordinator, entry),
    ])


class EDFTempoBaseBinary(CoordinatorEntity, BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: EDFTempoCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, "edf_tempo")},
            "name": "EDF Tempo",
            "manufacturer": "EDF",
            "model": "Option Tempo",
        }


class HeureCreuseBinarySensor(EDFTempoBaseBinary):
    """True si on est actuellement en Heures Creuses."""

    _attr_unique_id = "edf_tempo_binary_heure_creuse"
    _attr_name = "Heure Creuse"
    _attr_icon = "mdi:moon-waning-crescent"

    @property
    def is_on(self):
        return self.coordinator.data.get("en_heure_creuse", False)

    @property
    def extra_state_attributes(self):
        return {"plage": "22h00 – 06h00"}


class JourRougeBinarySensor(EDFTempoBaseBinary):
    """True si aujourd'hui est un jour rouge."""

    _attr_unique_id = "edf_tempo_binary_jour_rouge"
    _attr_name = "Jour Rouge"
    _attr_icon = "mdi:alert-circle"

    @property
    def is_on(self):
        return self.coordinator.data.get("couleur_aujourd_hui") == "ROUGE"


class JourBlancBinarySensor(EDFTempoBaseBinary):
    """True si aujourd'hui est un jour blanc."""

    _attr_unique_id = "edf_tempo_binary_jour_blanc"
    _attr_name = "Jour Blanc"
    _attr_icon = "mdi:circle-outline"

    @property
    def is_on(self):
        return self.coordinator.data.get("couleur_aujourd_hui") == "BLANC"


class JourBleuBinarySensor(EDFTempoBaseBinary):
    """True si aujourd'hui est un jour bleu."""

    _attr_unique_id = "edf_tempo_binary_jour_bleu"
    _attr_name = "Jour Bleu"
    _attr_icon = "mdi:circle"

    @property
    def is_on(self):
        return self.coordinator.data.get("couleur_aujourd_hui") == "BLEU"


class DemainRougeBinarySensor(EDFTempoBaseBinary):
    """True si demain est un jour rouge (alerte anticipation)."""

    _attr_unique_id = "edf_tempo_binary_demain_rouge"
    _attr_name = "Demain Rouge"
    _attr_icon = "mdi:alert-circle-outline"

    @property
    def is_on(self):
        return self.coordinator.data.get("couleur_demain") == "ROUGE"

    @property
    def extra_state_attributes(self):
        return {
            "couleur_demain": self.coordinator.data.get("couleur_demain"),
            "note": "Couleur connue à partir de 10h30",
        }
