"""Constants for EDF Tempo integration."""

DOMAIN = "edf_tempo"
CONF_PRIX_BLEU_HC = "prix_bleu_hc"
CONF_PRIX_BLEU_HP = "prix_bleu_hp"
CONF_PRIX_BLANC_HC = "prix_blanc_hc"
CONF_PRIX_BLANC_HP = "prix_blanc_hp"
CONF_PRIX_ROUGE_HC = "prix_rouge_hc"
CONF_PRIX_ROUGE_HP = "prix_rouge_hp"

# Tarifs réglementés EDF Tempo au 1er février 2026 (€/kWh TTC)
DEFAULT_PRIX_BLEU_HC  = 0.1325
DEFAULT_PRIX_BLEU_HP  = 0.1612
DEFAULT_PRIX_BLANC_HC = 0.1499
DEFAULT_PRIX_BLANC_HP = 0.1871
DEFAULT_PRIX_ROUGE_HC = 0.1575
DEFAULT_PRIX_ROUGE_HP = 0.7060

# ----------------------------------------------------------------
# Endpoints vérifiés de https://www.api-couleur-tempo.fr/api
# Réponse /today + /tomorrow :
#   {"dateJour":"2026-04-06","codeJour":1,"periode":"2025-2026","libCouleur":"Bleu"}
#     codeJour : 1=Bleu, 2=Blanc, 3=Rouge
# Réponse /now :
#   {"codeCouleur":1,"codeHoraire":2,"tarifKwh":0.1325,"libTarif":"Bleu-HC"}
#     codeHoraire : 1=HP, 2=HC
# Réponse archive (?periode=YYYY-YYYY) :
#   liste de {"dateJour":"...","codeJour":1,"periode":"...","libCouleur":"Bleu"}
# ----------------------------------------------------------------
API_BASE_URL = "https://www.api-couleur-tempo.fr/api"
API_TODAY    = f"{API_BASE_URL}/jourTempo/today"      # singulier
API_TOMORROW = f"{API_BASE_URL}/jourTempo/tomorrow"   # singulier
API_NOW      = f"{API_BASE_URL}/now"                  # tarif + HC/HP temps réel
API_ARCHIVE  = f"{API_BASE_URL}/jourTempo"            # singulier + ?periode=YYYY-YYYY
API_STATS    = f"{API_BASE_URL}/stats"                # consommé et restant

# Couleurs
COULEUR_BLEU     = "BLEU"
COULEUR_BLANC    = "BLANC"
COULEUR_ROUGE    = "ROUGE"
COULEUR_INCONNUE = "INCONNU"

# Plages horaires HC : 22h00 -> 06h00
HC_START = 22
HC_END   = 6

# Scan interval
SCAN_INTERVAL_MINUTES = 30

# Coordinator key
COORDINATOR = "coordinator"
