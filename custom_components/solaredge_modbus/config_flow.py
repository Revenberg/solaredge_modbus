"""s0 5 channels."""
from __future__ import annotations
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries, exceptions
from homeassistant.core import HomeAssistant

#from homeassistant.const import CONF_ACCESS_TOKEN, CONF_NAME, CONF_PATH, CONF_URL, CONF_TYPE,
from homeassistant.const import CONF_DEVICE
#,    CONF_DEVICE_ID,    CONF_DEVICES, CONF_HOST, CONF_PORT
from .const import DOMAIN, CONF_MANUAL_PATH  # pylint:disable=unused-import
from .hub import Hub
import serial
import os

_LOGGER = logging.getLogger(__name__)

# This is the schema that used to display the UI to the user. This simple
# schema has a single required host field, but it could include a number of fields
# such as username, password etc. See other components in the HA core code for
# further examples.
# Note the input displayed to the user will be translated. See the
# translations/<lang>.json file and strings.json. See here for further information:
# https://developers.home-assistant.io/docs/config_entries_config_flow_handler/#translations
# At the time of writing I found the translations created by the scaffold didn't
# quite work as documented and always gave me the "Lokalise key references" string
# (in square brackets), rather than the actual translated value. I did not attempt to
# figure this out or look further into it.
DATA_SCHEMA = vol.Schema({("host"): str})

def get_serial_by_id(dev_path: str) -> str:
    """Return a /dev/serial/by-id match for given device if available."""
    by_id = "/dev/serial/by-id"
    if not os.path.isdir(by_id):
        return dev_path

    for path in (entry.path for entry in os.scandir(by_id) if entry.is_symlink()):
        if os.path.realpath(path) == dev_path:
            return path
    return dev_path

async def validate_input_title(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input allows us to connect.

    Data has the keys from DATA_SCHEMA with values provided by the user.
    """
    # Validate the data can be used to set up a connection.

    # This is a simple example to show an error in the UI for a short hostname
    # The exceptions are defined at the end of this file, and are used in the
    # `async_step_user` method below.
    if len(data["host"]) < 3:
        raise InvalidHost

    return {"title": data["host"]}

async def validate_input_device(hass: HomeAssistant, data: dict) -> dict[str, Any]:
    """Validate the user input device to connect."""
    if len(data[CONF_DEVICE ]) < 3:
        raise InvalidHost

#    hub = Hub(hass, data["title"], data[ CONF_DEVICE ])
    # The dummy hub provides a `test_connection` method to ensure it's working
    # as expected
#    result = await hub.connection()
#    if not result:
        # If there is an error, raise an exception to notify HA that there was a
        # problem. The UI will also show there was a problem
#        raise CannotConnect

    # If your PyPI package is not built with async, pass your methods
    # to the executor:
    # await hass.async_add_executor_job(
    #     your_validate_func, data["username"], data["password"]
    # )

    # If you cannot connect:
    # throw CannotConnect
    # If the authentication is wrong:
    # InvalidAuth

    # Return info that you want to store in the config entry.
    # "Title" is what is displayed to the user for this hub device
    # It is stored internally in HA as part of the device config.
    # See `async_step_user` below for how this is used
    return {"title": data["title"], "device": data[ CONF_DEVICE ]}


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Hello World."""

    VERSION = 1
    # Pick one of the available connection classes in homeassistant/config_entries.py
    # This tells HA if it should be asking for updates, or it'll be notified of updates
    # automatically. This example uses PUSH, as the dummy hub will notify HA of
    # changes.
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_PUSH

    #data: Optional[Dict[str, Any]]

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        # This goes through the steps to take the user through the setup process.
        # Using this it is possible to update the UI and prompt for additional
        # information. This example provides a single form (built from `DATA_SCHEMA`),
        # and when that has some validated input, it calls `async_create_entry` to
        # actually create the HA config entry. Note the "title" value is returned by
        # `validate_input` above.
        errors = {}
        if user_input is not None:
            try:
                self.data = await validate_input_title(self.hass, user_input )
                return await self.async_step_setup_serial()

#                return self.async_create_entry(title=info["title"], data=user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidHost:
                # The error string is set here, and should be translated.
                # This example does not currently cover translations, see the
                # comments on `DATA_SCHEMA` for further details.
                # Set the error on the `host` field, not the entire form.
                errors["host"] = "cannot_connect"
            except Exception:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"

        # If there is no user input or there were errors, show the form again, including any errors that were found with the input.
        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )


    async def async_step_setup_serial(
        self, user_input: dict[str, Any] | None = None
    ):# -> data_entry_flow.FlowResult:
        """Step when setting up serial configuration."""
        errors: dict[str, str] = {}
        _LOGGER.debug( user_input )
        if user_input is not None:
          if user_input[CONF_DEVICE] is not None:
            _LOGGER.debug( "!!!!!!!!!!!!!!!!!" )
            _LOGGER.debug( user_input )
#            name = user_input[ CONF_NAME ]
#            _LOGGER.debug( name )
            user_selection = user_input[CONF_DEVICE]
            _LOGGER.debug( user_selection )
            if user_selection == CONF_MANUAL_PATH:
                return await self.async_step_setup_serial_manual_path()

            dev_path = await self.hass.async_add_executor_job(
                get_serial_by_id, user_selection
            )
            user_input.update( self.data )
            _LOGGER.debug( user_input )
            data = await validate_input_device(self.hass, user_input )

            Hub(self.hass, data["title"], data[ CONF_DEVICE ])
            _LOGGER.debug( data )
#            try:
#              result = await hub.connection()
              #  data = await self.async_validate_rfx(device=dev_path)
#                data: dict[str, Any] = {
#                 'title': self.data['title'],
 #           CONF_PORT: port,
#                 CONF_DEVICE: dev_path,
#            CONF_AUTOMATIC_ADD: False,
 #           CONF_DEVICES: {},
#                }
#                self.hass.data[ 'title' ] = self.data[ "title" ]
#                self.hass.data[ CONF_DEVICE] = dev_path
#                _LOGGER.debug( data )

#            except CannotConnect:
#                errors["base"] = "cannot_connect"

            if not errors:
                _LOGGER.debug( data )
                _LOGGER.debug( data['device'] )
#                devices: dict[str, dict[str, Any] | None] = {}
#                devices['port1'] = [ 'portje 1' ]
#                data['devices'] = devices
#                data[ 'title' ] = self.data[ 'title' ]
#                self.data = data
                _LOGGER.debug( "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!" )
                _LOGGER.debug( data )
                _LOGGER.debug( dev_path )

#                self.hass.data[config_entry.entry_id] = hub

                return self.async_create_entry(title=self.data[ "title" ], data=data)
        _LOGGER.debug( serial.tools.list_ports.comports )
        ports = await self.hass.async_add_executor_job(serial.tools.list_ports.comports)
        list_of_ports = {}
        for port in ports:
            _LOGGER.debug( port )
            if port.manufacturer == "Arduino LLC":
              list_of_ports[
                  port.device
              ] = f"{port} " + (
                  f" - {port.manufacturer}" if port.manufacturer else ""
              )
        list_of_ports[CONF_MANUAL_PATH] = CONF_MANUAL_PATH

        schema = vol.Schema({vol.Required(CONF_DEVICE): vol.In(list_of_ports)})
        return self.async_show_form(
#            step_id="setup_serial",
            step_id="setup_serial",
            data_schema=schema,
            errors=errors,
        )


    async def async_step_setup_serial_manual_path(
        self, user_input: dict[str, Any] | None = None
    ): # -> data_entry_flow.FlowResult:
        """Select path manually."""
        errors: dict[str, str] = {}

        if user_input is not None:
            device = user_input[CONF_DEVICE]
            try:
#                data = await self.async_validate_rfx(device=device)
                data: dict[str, Any] = {
                 'title': self.data['title'],
 #           CONF_PORT: port,
                 CONF_DEVICE: device,
#            CONF_AUTOMATIC_ADD: False,
 #           CONF_DEVICES: {},
                }
                _LOGGER.debug(data)
            except CannotConnect:
                errors["base"] = "cannot_connect"

            if not errors:
                _LOGGER.debug(data)
                return self.async_create_entry(title="", data=data)

        schema = vol.Schema({vol.Required(CONF_DEVICE): str})
        return self.async_show_form(
            step_id="setup_serial_manual_path",
            data_schema=schema,
            errors=errors,
        )

#    async def async_validate_rfx(
#        self,
#        device: str | None = None,
#    ) -> dict[str, Any]:
#        """Create data for rfxtrx entry."""
 #       success = await self.hass.async_add_executor_job(
 #           _test_transport, device
 #       )
 #       if not success:
 #           raise CannotConnect

#        data: dict[str, Any] = {
 #           CONF_HOST: host,
 #           CONF_PORT: port,
#            CONF_DEVICE: device,
#            CONF_AUTOMATIC_ADD: False,
 #           CONF_DEVICES: {},
#        }
#        return data

#def _test_transport(device: str | None) -> bool:
#    """Construct a rfx object based on config."""
#    if host is not None:
#       _LOGGER.debug(host)
#    if port is not None:
#       _LOGGER.debug(post)
#        try:
#            conn = rfxtrxmod.PyNetworkTransport((host, port))
#        except OSError:
#            return False
#        conn.close()
#    else:
#        try:
#            conn = rfxtrxmod.PySerialTransport(device)
#        except serial.serialutil.SerialException:
#            return False
#        if conn.serial is None:
#           return False

#        conn.close()

#    return True

class CannotConnect(exceptions.HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidHost(exceptions.HomeAssistantError):
    """Error to indicate there is an invalid hostname."""
