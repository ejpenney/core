"""Test the Obihai config flow."""
from unittest.mock import AsyncMock, patch

import pytest

from homeassistant import config_entries
from homeassistant.components.obihai.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import CONF_HOST, CONF_USERNAME, USER_INPUT, async_mock_existing_entry

VALIDATE_AUTH_PATCH = "homeassistant.components.obihai.config_flow.validate_auth"

pytestmark = pytest.mark.usefixtures("mock_setup_entry")


async def test_user_form(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test we get the user initiated form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    with patch("pyobihai.PyObihai.check_account"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["title"] == "10.10.10.30"
    assert result["data"] == {**USER_INPUT}

    assert len(mock_setup_entry.mock_calls) == 1


async def test_auth_failure(hass: HomeAssistant) -> None:
    """Test we get the authentication error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(VALIDATE_AUTH_PATCH, return_value=False):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"]["base"] == "cannot_connect"


async def test_yaml_import(hass: HomeAssistant) -> None:
    """Test we get the YAML imported."""
    with patch(VALIDATE_AUTH_PATCH, return_value=True):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert "errors" not in result


async def test_yaml_import_fail(hass: HomeAssistant) -> None:
    """Test the YAML import fails."""
    with patch(VALIDATE_AUTH_PATCH, return_value=False):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_IMPORT},
            data=USER_INPUT,
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "cannot_connect"
    assert "errors" not in result


async def test_options_flow(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test updating options."""
    entry = await async_mock_existing_entry(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    with patch("pyobihai.PyObihai.check_account"):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={
                CONF_HOST: USER_INPUT[CONF_HOST],
                CONF_USERNAME: "changed_username",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"][CONF_USERNAME] == "changed_username"


async def test_options_flow_already_configured(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test updating options to an existing entry fails."""
    blocking_entry = await async_mock_existing_entry(hass)
    await hass.config_entries.options.async_init(blocking_entry.entry_id)

    second_entry = await async_mock_existing_entry(hass)
    result = await hass.config_entries.options.async_init(second_entry.entry_id)

    with patch("pyobihai.PyObihai.check_account"):
        final_result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: USER_INPUT[CONF_HOST]},
        )
        await hass.async_block_till_done()

    assert final_result["type"] == FlowResultType.FORM
    assert final_result["errors"][CONF_HOST] == "already_configured"


async def test_options_flow_cannot_connect(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """Test updating options to an entry with bad creds fails."""
    entry = await async_mock_existing_entry(hass)
    result = await hass.config_entries.options.async_init(entry.entry_id)

    with patch("pyobihai.PyObihai.check_account"), patch(
        VALIDATE_AUTH_PATCH, return_value=False
    ):
        result = await hass.config_entries.options.async_configure(
            result["flow_id"],
            user_input={CONF_HOST: "changed_host"},
        )
        await hass.async_block_till_done()

    assert result["type"] == FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"
