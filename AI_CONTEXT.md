# Context for AI Assistant - Home Assistant Integration: EDF Tempo

## Project Purpose
Intégration personnalisée Home Assistant pour gérer le contrat EDF Tempo. Elle interroge l'API `api-couleur-tempo.fr` pour récupérer les couleurs du jour, du lendemain, la période tarifaire (HC/HP) en temps réel, le tarif applicable et l'estimation des jours restants dans la saison.

## Architecture & Design Patterns
- **Domaine:** `edf_tempo`
- **Pattern Principal:** `DataUpdateCoordinator` (nommé `EDFTempoCoordinator`) agit comme source unique de vérité.
- **Update Frequency:** `SCAN_INTERVAL_MINUTES` = 30 minutes (cloud_polling).
- **Base Classes:** - `EDFTempoBaseSensor` hérite de `CoordinatorEntity` et `SensorEntity`.
  - `EDFTempoBaseBinary` hérite de `CoordinatorEntity` et `BinarySensorEntity`.
- **Options / Configuration:** Géré via `ConfigFlow` (`config_flow.py`) permettant à l'utilisateur d'outrepasser les prix par défaut (ex: `prix_bleu_hc`).

## Data Schema (`coordinator.data`)
Le dictionnaire mis à jour toutes les 30 minutes contient les clés suivantes :
- `couleur_aujourd_hui` (str) : "BLEU", "BLANC", "ROUGE" ou "INCONNU".
- `couleur_demain` (str) : "BLEU", "BLANC", "ROUGE" ou "INCONNU".
- `en_heure_creuse` (bool) : `True` si Heure Creuse (22h-6h), `False` si Heure Pleine.
- `tarif_kwh` (float) : Tarif actuel renvoyé par l'endpoint `/now`.
- `lib_tarif` (str) : Libellé du tarif actuel (ex: "Bleu-HC").
- `jours_rouges_restants`, `jours_blancs_restants`, `jours_bleus_restants` (int) : Jours restants calculés par approximation sur la saison en cours.
- `nb_bleus_saison`, `nb_blancs_saison`, `nb_rouges_saison` (None) : Non disponible via cette API (endpoints singuliers).
- `saison` (str) : Période Tempo en cours (ex: "2025-2026").
- `last_update` (str) : Timestamp ISO de la dernière mise à jour.

## File Mapping
- `manifest.json` : Définit l'intégration (`domain`: "edf_tempo", `config_flow`: true).
- `const.py` : Constantes (endpoints API, clés de configuration `CONF_PRIX_*`, prix par défaut, plages horaires).
- `__init__.py` : Point d'entrée. Initialise le `EDFTempoCoordinator`, propage les données aux plateformes et gère l'écouteur de mise à jour des options tarifaires (`_async_update_listener`).
- `config_flow.py` : `EDFTempoConfigFlow` et `EDFTempoOptionsFlow` pour la gestion des tarifs personnalisés dans l'UI.
- `coordinator.py` : `EDFTempoCoordinator` gère la session `aiohttp` et les appels API (`/today`, `/tomorrow`, `/now`). Contient la logique métier d'estimation des jours restants (`_compute_jours_restants`).
- `sensor.py` : Entités de type Sensor (Couleurs, Période Tarifaire, Tarifs actuels, Jours restants). Gère la logique de fallback tarifaire si l'API `/now` ne renvoie pas de prix.
- `binary_sensor.py` : Entités de type Binary Sensor (Heure Creuse, Jours spécifiques, Demain Rouge pour les alertes).

## Business Rules (EDF Tempo Spécificités)
1. **Saison Tempo** : Du 1er septembre au 31 août de l'année suivante.
2. **Heures Creuses (HC)** : De 22h00 à 06h00 (`HC_START` et `HC_END`).
3. **Publication du lendemain** : La `couleur_demain` est généralement publiée vers 10h30. Avant, elle vaut "INCONNU".
4. **Quotas Fixes** : Une saison complète comprend 22 jours Rouges, 40 jours Blancs, et environ 300 jours Bleus.

## Coding Standards & Règles pour l'IA
- Les nouvelles entités **doivent** hériter de `EDFTempoBaseSensor` ou `EDFTempoBaseBinary` et utiliser `self.coordinator.data.get("cle")` pour lire leur état.
- Ne **jamais** utiliser de méthode `async_update` dans les classes d'entités, car le cycle de vie est géré par le coordinateur.
- Lors de l'ajout d'une nouvelle option tarifaire, mettre à jour `const.py`, le schéma dans `config_flow.py`, la logique de secours dans `sensor.py` (`_get_tarif`) et `translations/fr.json`.
- Respecter le formatage des `_attr_unique_id` en utilisant le préfixe `edf_tempo_`.