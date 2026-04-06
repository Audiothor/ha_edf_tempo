"""Sensors for EDF Tempo integration."""
from __future__ import annotations

import logging
from datetime import datetime

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN, COORDINATOR,
    CONF_PRIX_BLEU_HC, CONF_PRIX_BLEU_HP,
    CONF_PRIX_BLANC_HC, CONF_PRIX_BLANC_HP,
    CONF_PRIX_ROUGE_HC, CONF_PRIX_ROUGE_HP,
    DEFAULT_PRIX_BLEU_HC, DEFAULT_PRIX_BLEU_HP,
    DEFAULT_PRIX_BLANC_HC, DEFAULT_PRIX_BLANC_HP,
    DEFAULT_PRIX_ROUGE_HC, DEFAULT_PRIX_ROUGE_HP,
)
from .coordinator import EDFTempoCoordinator

_LOGGER = logging.getLogger(__name__)

COLOR_ICONS = {
    "BLEU": "mdi:circle",
    "BLANC": "mdi:circle-outline",
    "ROUGE": "mdi:circle",
    "INCONNU": "mdi:help-circle-outline",
}
COLOR_ENTITY_PICTURES = {
    "BLEU": "🔵",
    "BLANC": "⚪",
    "ROUGE": "🔴",
    "INCONNU": "❓",
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EDFTempoCoordinator = hass.data[DOMAIN][entry.entry_id][COORDINATOR]

    entities = [
        CouleurAujourdhuiSensor(coordinator, entry),
        CouleurDemainSensor(coordinator, entry),
        HeureCreuseSensor(coordinator, entry),
        TarifActuelSensor(coordinator, entry),
        JoursBleuRestantsSensor(coordinator, entry),
        JoursBlancRestantsSensor(coordinator, entry),
        JoursRougeRestantsSensor(coordinator, entry),
        NbBleusSaisonSensor(coordinator, entry),
        NbBlancsSaisonSensor(coordinator, entry),
        NbRougesSaisonSensor(coordinator, entry),
    ]
    async_add_entities(entities)


def _get_tarif(entry: ConfigEntry, couleur: str, hc: bool) -> float:
    """Return tariff in €/kWh for given color and HC/HP."""
    opts = {**entry.data, **entry.options}
    key_hc = {
        "BLEU": CONF_PRIX_BLEU_HC,
        "BLANC": CONF_PRIX_BLANC_HC,
        "ROUGE": CONF_PRIX_ROUGE_HC,
    }.get(couleur)
    key_hp = {
        "BLEU": CONF_PRIX_BLEU_HP,
        "BLANC": CONF_PRIX_BLANC_HP,
        "ROUGE": CONF_PRIX_ROUGE_HP,
    }.get(couleur)
    default_hc = {
        "BLEU": DEFAULT_PRIX_BLEU_HC,
        "BLANC": DEFAULT_PRIX_BLANC_HC,
        "ROUGE": DEFAULT_PRIX_ROUGE_HC,
    }.get(couleur, 0.0)
    default_hp = {
        "BLEU": DEFAULT_PRIX_BLEU_HP,
        "BLANC": DEFAULT_PRIX_BLANC_HP,
        "ROUGE": DEFAULT_PRIX_ROUGE_HP,
    }.get(couleur, 0.0)

    if hc and key_hc:
        return opts.get(key_hc, default_hc)
    if not hc and key_hp:
        return opts.get(key_hp, default_hp)
    return 0.0


class EDFTempoBaseSensor(CoordinatorEntity, SensorEntity):
    """Base class for EDF Tempo sensors."""

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
            "entry_type": "service",
        }


class CouleurAujourdhuiSensor(EDFTempoBaseSensor):
    """Couleur du jour."""

    _attr_unique_id = "edf_tempo_couleur_aujourd_hui"
    _attr_name = "Couleur Aujourd'hui"
    _attr_icon = "mdi:calendar-today"

    @property
    def native_value(self):
        return self.coordinator.data.get("couleur_aujourd_hui", "INCONNU")

    @property
    def extra_state_attributes(self):
        couleur = self.native_value
        return {
            "emoji": COLOR_ENTITY_PICTURES.get(couleur, "❓"),
            "saison": self.coordinator.data.get("saison"),
            "last_update": self.coordinator.data.get("last_update"),
        }

    @property
    def icon(self):
        return COLOR_ICONS.get(self.native_value, "mdi:help-circle-outline")


class CouleurDemainSensor(EDFTempoBaseSensor):
    """Couleur du lendemain."""

    _attr_unique_id = "edf_tempo_couleur_demain"
    _attr_name = "Couleur Demain"
    _attr_icon = "mdi:calendar-arrow-right"

    @property
    def native_value(self):
        return self.coordinator.data.get("couleur_demain", "INCONNU")

    @property
    def extra_state_attributes(self):
        couleur = self.native_value
        return {
            "emoji": COLOR_ENTITY_PICTURES.get(couleur, "❓"),
            "disponible_apres": "10h30",
        }

    @property
    def icon(self):
        return COLOR_ICONS.get(self.native_value, "mdi:help-circle-outline")


class HeureCreuseSensor(EDFTempoBaseSensor):
    """Indique si on est en heure creuse ou pleine."""

    _attr_unique_id = "edf_tempo_heure_creuse"
    _attr_name = "Période Tarifaire"
    _attr_icon = "mdi:clock-outline"

    @property
    def native_value(self):
        hc = self.coordinator.data.get("en_heure_creuse", False)
        return "Heures Creuses" if hc else "Heures Pleines"

    @property
    def extra_state_attributes(self):
        return {
            "en_heure_creuse": self.coordinator.data.get("en_heure_creuse", False),
            "plage_hc": "22h00 – 06h00",
            "plage_hp": "06h00 – 22h00",
        }


class TarifActuelSensor(EDFTempoBaseSensor):
    """Tarif actuel en €/kWh — valeur temps réel fournie par /api/now."""

    _attr_unique_id = "edf_tempo_tarif_actuel"
    _attr_name = "Tarif Actuel"
    _attr_native_unit_of_measurement = "€/kWh"
    _attr_icon = "mdi:currency-eur"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        # Priorité : tarif temps réel de l'API, sinon calcul local
        data = self.coordinator.data
        tarif_api = data.get("tarif_kwh")
        if tarif_api is not None:
            return round(tarif_api, 4)
        couleur = data.get("couleur_aujourd_hui", "INCONNU")
        hc = data.get("en_heure_creuse", False)
        if couleur == "INCONNU":
            return None
        return round(_get_tarif(self._entry, couleur, hc), 4)

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data
        opts = {**self._entry.data, **self._entry.options}
        return {
            "couleur": data.get("couleur_aujourd_hui"),
            "periode": "HC" if data.get("en_heure_creuse") else "HP",
            "lib_tarif": data.get("lib_tarif", ""),
            "source": "api/now (temps réel)",
            "tarifs_bleu_hc": opts.get(CONF_PRIX_BLEU_HC, DEFAULT_PRIX_BLEU_HC),
            "tarifs_bleu_hp": opts.get(CONF_PRIX_BLEU_HP, DEFAULT_PRIX_BLEU_HP),
            "tarifs_blanc_hc": opts.get(CONF_PRIX_BLANC_HC, DEFAULT_PRIX_BLANC_HC),
            "tarifs_blanc_hp": opts.get(CONF_PRIX_BLANC_HP, DEFAULT_PRIX_BLANC_HP),
            "tarifs_rouge_hc": opts.get(CONF_PRIX_ROUGE_HC, DEFAULT_PRIX_ROUGE_HC),
            "tarifs_rouge_hp": opts.get(CONF_PRIX_ROUGE_HP, DEFAULT_PRIX_ROUGE_HP),
        }


class JoursBleuRestantsSensor(EDFTempoBaseSensor):
    _attr_unique_id = "edf_tempo_jours_bleu_restants"
    _attr_name = "Jours Bleus Restants"
    _attr_icon = "mdi:calendar-minus"
    _attr_native_unit_of_measurement = "jours"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        v = self.coordinator.data.get("jours_bleus_restants", -1)
        return v if v >= 0 else None


class JoursBlancRestantsSensor(EDFTempoBaseSensor):
    _attr_unique_id = "edf_tempo_jours_blanc_restants"
    _attr_name = "Jours Blancs Restants"
    _attr_icon = "mdi:calendar-blank-outline"
    _attr_native_unit_of_measurement = "jours"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        v = self.coordinator.data.get("jours_blancs_restants", -1)
        return v if v >= 0 else None


class JoursRougeRestantsSensor(EDFTempoBaseSensor):
    _attr_unique_id = "edf_tempo_jours_rouge_restants"
    _attr_name = "Jours Rouges Restants"
    _attr_icon = "mdi:calendar-alert"
    _attr_native_unit_of_measurement = "jours"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        v = self.coordinator.data.get("jours_rouges_restants", -1)
        return v if v >= 0 else None


class NbBleusSaisonSensor(EDFTempoBaseSensor):
    _attr_unique_id = "edf_tempo_nb_bleus_saison"
    _attr_name = "Jours Bleus (saison)"
    _attr_icon = "mdi:counter"
    _attr_native_unit_of_measurement = "jours"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self.coordinator.data.get("nb_bleus_saison")

    @property
    def available(self):
        return self.coordinator.data.get("nb_bleus_saison") is not None


class NbBlancsSaisonSensor(EDFTempoBaseSensor):
    _attr_unique_id = "edf_tempo_nb_blancs_saison"
    _attr_name = "Jours Blancs (saison)"
    _attr_icon = "mdi:counter"
    _attr_native_unit_of_measurement = "jours"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self.coordinator.data.get("nb_blancs_saison")

    @property
    def available(self):
        return self.coordinator.data.get("nb_blancs_saison") is not None


class NbRougesSaisonSensor(EDFTempoBaseSensor):
    _attr_unique_id = "edf_tempo_nb_rouges_saison"
    _attr_name = "Jours Rouges (saison)"
    _attr_icon = "mdi:counter"
    _attr_native_unit_of_measurement = "jours"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def native_value(self):
        return self.coordinator.data.get("nb_rouges_saison")

    @property
    def available(self):
        return self.coordinator.data.get("nb_rouges_saison") is not None
