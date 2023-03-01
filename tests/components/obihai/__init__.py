"""Tests for the Obihai Integration."""

from unittest.mock import patch

from homeassistant.components.obihai.const import DOMAIN
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry

USER_INPUT = {
    CONF_HOST: "10.10.10.30",
    CONF_PASSWORD: "admin",
    CONF_USERNAME: "admin",
}


async def async_mock_existing_entry(hass: HomeAssistant) -> MockConfigEntry:
    """Provide a configured (MockConfig) entry."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data=USER_INPUT,
    )
    entry.add_to_hass(hass)

    with patch("homeassistant.components.obihai.PLATFORMS", []):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry
