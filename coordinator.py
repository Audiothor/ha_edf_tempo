"""DataUpdateCoordinator for EDF Tempo."""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, date

import aiohttp

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    API_TODAY, API_TOMORROW, API_NOW, API_STATS,
    SCAN_INTERVAL_MINUTES,
    COULEUR_INCONNUE,
)

_LOGGER = logging.getLogger(__name__)

# codeJour : 1=Bleu, 2=Blanc, 3=Rouge
CODE_COULEUR = {1: "BLEU", 2: "BLANC", 3: "ROUGE"}
# codeHoraire : 1=HP, 2=HC
CODE_HORAIRE = {1: False, 2: True}  # True = heure creuse


def _current_saison() -> str:
    """Return current Tempo season like '2025-2026'. Season: Sep 1 → Aug 31."""
    today = date.today()
    if today.month >= 9:
        return f"{today.year}-{today.year + 1}"
    return f"{today.year - 1}-{today.year}"


def _parse_color_from_code(code) -> str:
    """Convert codeJour integer (1/2/3) to color string."""
    if isinstance(code, int):
        return CODE_COULEUR.get(code, COULEUR_INCONNUE)
    if isinstance(code, str):
        mapping = {
            "BLEU": "BLEU", "BLANC": "BLANC", "ROUGE": "ROUGE",
            "TEMPO_BLEU": "BLEU", "TEMPO_BLANC": "BLANC", "TEMPO_ROUGE": "ROUGE",
            "1": "BLEU", "2": "BLANC", "3": "ROUGE",
        }
        return mapping.get(code.upper(), COULEUR_INCONNUE)
    return COULEUR_INCONNUE


class EDFTempoCoordinator(DataUpdateCoordinator):
    """Fetches all EDF Tempo data from api-couleur-tempo.fr."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=SCAN_INTERVAL_MINUTES),
        )
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def _fetch(self, url: str) -> dict | list:
        session = await self._get_session()
        try:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=15),
                headers={"Accept": "application/json"},
            ) as resp:
                resp.raise_for_status()
                return await resp.json(content_type=None)
        except aiohttp.ClientResponseError as err:
            raise UpdateFailed(
                f"Erreur API EDF Tempo ({url}): {err.status}, message='{err.message}', url='{url}'"
            ) from err
        except aiohttp.ClientError as err:
            raise UpdateFailed(f"Erreur API EDF Tempo ({url}): {err}") from err

    async def _async_update_data(self) -> dict:
        """Main update: fetch today, tomorrow, now and stats."""
        try:
            today_data    = await self._fetch(API_TODAY)
            tomorrow_data = await self._fetch(API_TOMORROW)
            now_data      = await self._fetch(API_NOW)
            stats_data    = await self._fetch(API_STATS)
        except UpdateFailed:
            raise
        except Exception as err:
            raise UpdateFailed(f"Erreur inattendue: {err}") from err

        # /api/jourTempo/today → {"dateJour":"2026-04-06","codeJour":1,"periode":"2025-2026","libCouleur":"Bleu"}
        couleur_aujourd_hui = _parse_color_from_code(today_data.get("codeJour"))
        saison = today_data.get("periode", _current_saison())

        # /api/jourTempo/tomorrow → même structure
        couleur_demain = _parse_color_from_code(tomorrow_data.get("codeJour"))

        # /api/now → {"applicableIn":0,"codeCouleur":1,"codeHoraire":1,"tarifKwh":0.1612,"libTarif":"Bleu-HP"}
        # codeHoraire : 1=HP, 2=HC
        en_heure_creuse = CODE_HORAIRE.get(now_data.get("codeHoraire"), self._is_heure_creuse())
        tarif_kwh       = now_data.get("tarifKwh")
        lib_tarif       = now_data.get("libTarif", "")

        # Jours restants et quotas de la saison fournis par /api/stats
        jours_rouges_restants = stats_data.get("joursRougesRestants")
        jours_blancs_restants = stats_data.get("joursBlancsRestants")
        jours_bleus_restants  = stats_data.get("joursBleusRestants")

        nb_bleus_saison = (stats_data.get("joursBleusConsommes", 0) + jours_bleus_restants) if jours_bleus_restants is not None else None
        nb_blancs_saison = (stats_data.get("joursBlancsConsommes", 0) + jours_blancs_restants) if jours_blancs_restants is not None else None
        nb_rouges_saison = (stats_data.get("joursRougesConsommes", 0) + jours_rouges_restants) if jours_rouges_restants is not None else None

        return {
            "couleur_aujourd_hui": couleur_aujourd_hui,
            "couleur_demain": couleur_demain,
            "en_heure_creuse": en_heure_creuse,
            "tarif_kwh": tarif_kwh,
            "lib_tarif": lib_tarif,
            "jours_rouges_restants": jours_rouges_restants,
            "jours_blancs_restants": jours_blancs_restants,
            "jours_bleus_restants": jours_bleus_restants,
            "nb_bleus_saison": nb_bleus_saison,
            "nb_blancs_saison": nb_blancs_saison,
            "nb_rouges_saison": nb_rouges_saison,
            "saison": saison,
            "last_update": datetime.now().isoformat(),
        }

    # deleted _compute_jours_restants local calculation

    @staticmethod
    def _is_heure_creuse() -> bool:
        """Fallback: True if 22h00–06h00 Paris time."""
        h = datetime.now().hour
        return h >= 22 or h < 6
