"""Config flow for EDF Tempo integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    DOMAIN,
    CONF_PRIX_BLEU_HC, CONF_PRIX_BLEU_HP,
    CONF_PRIX_BLANC_HC, CONF_PRIX_BLANC_HP,
    CONF_PRIX_ROUGE_HC, CONF_PRIX_ROUGE_HP,
    DEFAULT_PRIX_BLEU_HC, DEFAULT_PRIX_BLEU_HP,
    DEFAULT_PRIX_BLANC_HC, DEFAULT_PRIX_BLANC_HP,
    DEFAULT_PRIX_ROUGE_HC, DEFAULT_PRIX_ROUGE_HP,
)

TARIF_SCHEMA = {
    vol.Required(CONF_PRIX_BLEU_HC, default=DEFAULT_PRIX_BLEU_HC): vol.Coerce(float),
    vol.Required(CONF_PRIX_BLEU_HP, default=DEFAULT_PRIX_BLEU_HP): vol.Coerce(float),
    vol.Required(CONF_PRIX_BLANC_HC, default=DEFAULT_PRIX_BLANC_HC): vol.Coerce(float),
    vol.Required(CONF_PRIX_BLANC_HP, default=DEFAULT_PRIX_BLANC_HP): vol.Coerce(float),
    vol.Required(CONF_PRIX_ROUGE_HC, default=DEFAULT_PRIX_ROUGE_HC): vol.Coerce(float),
    vol.Required(CONF_PRIX_ROUGE_HP, default=DEFAULT_PRIX_ROUGE_HP): vol.Coerce(float),
}


class EDFTempoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle the initial configuration flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")

        if user_input is not None:
            return self.async_create_entry(title="EDF Tempo", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(TARIF_SCHEMA),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return EDFTempoOptionsFlow(config_entry)


class EDFTempoOptionsFlow(config_entries.OptionsFlow):
    """Handle options (update tariffs)."""

    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current = {**self.config_entry.data, **self.config_entry.options}

        schema = vol.Schema({
            vol.Required(CONF_PRIX_BLEU_HC, default=current.get(CONF_PRIX_BLEU_HC, DEFAULT_PRIX_BLEU_HC)): vol.Coerce(float),
            vol.Required(CONF_PRIX_BLEU_HP, default=current.get(CONF_PRIX_BLEU_HP, DEFAULT_PRIX_BLEU_HP)): vol.Coerce(float),
            vol.Required(CONF_PRIX_BLANC_HC, default=current.get(CONF_PRIX_BLANC_HC, DEFAULT_PRIX_BLANC_HC)): vol.Coerce(float),
            vol.Required(CONF_PRIX_BLANC_HP, default=current.get(CONF_PRIX_BLANC_HP, DEFAULT_PRIX_BLANC_HP)): vol.Coerce(float),
            vol.Required(CONF_PRIX_ROUGE_HC, default=current.get(CONF_PRIX_ROUGE_HC, DEFAULT_PRIX_ROUGE_HC)): vol.Coerce(float),
            vol.Required(CONF_PRIX_ROUGE_HP, default=current.get(CONF_PRIX_ROUGE_HP, DEFAULT_PRIX_ROUGE_HP)): vol.Coerce(float),
        })

        return self.async_show_form(step_id="init", data_schema=schema)
