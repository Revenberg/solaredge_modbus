"""The SolarEdge Modbus Integration."""
import asyncio
import logging
from datetime import timedelta
from typing import Any

import async_timeout
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_HOST,
    CONF_NAME,
    CONF_PORT,
    CONF_SCAN_INTERVAL,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, ConfDefaultFlag, ConfDefaultInt
from .const import ConfName, RetrySettings, DATA_ENERGY_METER
from .hub import DataUpdateFailed, HubInitFailed, SolarEdgeModbusMultiHub

from homeassistant.components.utility_meter import (
        CONF_METER,
#    CONF_SOURCE_SENSOR,
    CONF_TARIFF,
    CONF_TARIFF_ENTITY,
    CONF_TARIFFS,
    DATA_TARIFF_SENSORS,
    DATA_UTILITY,
    DOMAIN as UM_DOMAIN,
#    METER_CONFIG_SCHEMA,
)
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers import discovery
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.select import DOMAIN as SELECT_DOMAIN

_LOGGER = logging.getLogger(__name__)
_LOGGER.setLevel(logging.DEBUG)

PLATFORMS: list[str] = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an Energy Meter."""
    hass.data[DATA_ENERGY_METER] = {}

    _LOGGER.debug("test 1201")
    _LOGGER.debug("test")
    _LOGGER.debug("test")
    _LOGGER.debug("test")
    _LOGGER.debug(entry)
    _LOGGER.debug(DOMAIN)

    if DOMAIN not in entry:
        _LOGGER.debug("not in entry")
        return True

    _LOGGER.debug(entry[DOMAIN].items())
    for meter, conf in entry[DOMAIN].items():
        _LOGGER.debug("Setup %s.%s", DOMAIN, meter)

        # create the select entity
        select_entity = await setup_utility_meter_select(hass, entry, meter, conf)

        # Create the utility_meters for the energy
        um_conf = conf.copy()
        await setup_utility_meter_sensors(hass, entry,
                                          meter, um_conf, select_entity)






    entry_updates: dict[str, Any] = {}
    if CONF_SCAN_INTERVAL in entry.data:
        data = {**entry.data}
        entry_updates["data"] = data
        entry_updates["options"] = {
            **entry.options,
            CONF_SCAN_INTERVAL: data.pop(CONF_SCAN_INTERVAL),
        }
    if entry_updates:
        hass.config_entries.async_update_entry(entry, **entry_updates)

    solaredge_hub = SolarEdgeModbusMultiHub(
        hass,
        entry.data[CONF_NAME],
        entry.data[CONF_HOST],
        entry.data[CONF_PORT],
#        entry.data.get(ConfName.NUMBER_INVERTERS, ConfDefaultInt.NUMBER_INVERTERS),
#        entry.data.get(ConfName.DEVICE_ID, ConfDefaultInt.DEVICE_ID),
        entry.options.get(ConfName.DETECT_METERS, bool(ConfDefaultFlag.DETECT_METERS)),
        entry.options.get(
            ConfName.DETECT_BATTERIES, bool(ConfDefaultFlag.DETECT_BATTERIES)
        ),
        entry.options.get(
            ConfName.KEEP_MODBUS_OPEN, bool(ConfDefaultFlag.KEEP_MODBUS_OPEN)
        ),
        entry.options.get(
            ConfName.ADV_PWR_CONTROL, bool(ConfDefaultFlag.ADV_PWR_CONTROL)
        ),
        entry.options.get(
            ConfName.ADV_STORAGE_CONTROL, bool(ConfDefaultFlag.ADV_STORAGE_CONTROL)
        ),
        entry.options.get(
            ConfName.ADV_SITE_LIMIT_CONTROL,
            bool(ConfDefaultFlag.ADV_SITE_LIMIT_CONTROL),
        ),
        entry.options.get(
            ConfName.ALLOW_BATTERY_ENERGY_RESET,
            bool(ConfDefaultFlag.ALLOW_BATTERY_ENERGY_RESET),
        ),
        entry.options.get(ConfName.SLEEP_AFTER_WRITE, ConfDefaultInt.SLEEP_AFTER_WRITE),
        entry.options.get(
            ConfName.BATTERY_RATING_ADJUST, ConfDefaultInt.BATTERY_RATING_ADJUST
        ),
    )

    coordinator = SolarEdgeCoordinator(
        hass,
        solaredge_hub,
        entry.options.get(CONF_SCAN_INTERVAL, ConfDefaultInt.SCAN_INTERVAL),
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "hub": solaredge_hub,
        "coordinator": coordinator,
    }

    await coordinator.async_config_entry_first_refresh()

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    solaredge_hub = hass.data[DOMAIN][entry.entry_id]["hub"]
    await solaredge_hub.shutdown()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle an options update."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    """Remove a config entry from a device."""
    solaredge_hub = hass.data[DOMAIN][config_entry.entry_id]["hub"]

    known_devices = []

    for inverter in solaredge_hub.inverters:
        inverter_device_ids = {
            dev_id[1]
            for dev_id in inverter.device_info["identifiers"]
            if dev_id[0] == DOMAIN
        }
        for dev_id in inverter_device_ids:
            known_devices.append(dev_id)

    for meter in solaredge_hub.meters:
        meter_device_ids = {
            dev_id[1]
            for dev_id in meter.device_info["identifiers"]
            if dev_id[0] == DOMAIN
        }
        for dev_id in meter_device_ids:
            known_devices.append(dev_id)

    for battery in solaredge_hub.batteries:
        battery_device_ids = {
            dev_id[1]
            for dev_id in battery.device_info["identifiers"]
            if dev_id[0] == DOMAIN
        }
        for dev_id in battery_device_ids:
            known_devices.append(dev_id)

    this_device_ids = {
        dev_id[1] for dev_id in device_entry.identifiers if dev_id[0] == DOMAIN
    }

    for device_id in this_device_ids:
        if device_id in known_devices:
            _LOGGER.error(f"Failed to remove device entry: device {device_id} in use")
            return False

    return True


class SolarEdgeCoordinator(DataUpdateCoordinator):
    def __init__(
        self, hass: HomeAssistant, hub: SolarEdgeModbusMultiHub, scan_interval: int
    ):
        super().__init__(
            hass,
            _LOGGER,
            name="SolarEdge Coordinator",
            update_interval=timedelta(seconds=scan_interval),
        )
        self._hub = hub

        if scan_interval < 10 and not self._hub.keep_modbus_open:
            _LOGGER.warning("Polling frequency < 10, requiring keep modbus open.")
            self._hub.keep_modbus_open = True

    async def _async_update_data(self):
        try:
            async with async_timeout.timeout(self._hub.coordinator_timeout):
                return await self._refresh_modbus_data_with_retry(
                    ex_type=DataUpdateFailed,
                    limit=RetrySettings.Limit,
                    wait_ms=RetrySettings.Time,
                    wait_ratio=RetrySettings.Ratio,
                )

        except HubInitFailed as e:
            raise UpdateFailed(f"{e}")

        except DataUpdateFailed as e:
            raise UpdateFailed(f"{e}")

    async def _refresh_modbus_data_with_retry(
        self,
        ex_type=Exception,
        limit=0,
        wait_ms=100,
        wait_ratio=2,
    ):
        """
        Retry refresh until no exception occurs or retries exhaust
        :param ex_type: retry only if exception is subclass of this type
        :param limit: maximum number of invocation attempts
        :param wait_ms: initial wait time after each attempt in milliseconds.
        :param wait_ratio: increase wait by multiplying by this after each try.
        :return: result of first successful invocation
        :raises: last invocation exception if attempts exhausted
                 or exception is not an instance of ex_type
        """
        attempt = 1
        while True:
            try:
                return await self._hub.async_refresh_modbus_data()
            except Exception as ex:
                if not isinstance(ex, ex_type):
                    raise ex
                if 0 < limit <= attempt:
                    _LOGGER.debug(f"No more data refresh attempts (maximum {limit})")
                    raise ex

                _LOGGER.debug(f"Failed data refresh attempt #{attempt}", exc_info=ex)

                attempt += 1
                _LOGGER.debug(
                    f"Waiting {wait_ms} ms before data refresh attempt #{attempt}"
                )
                await asyncio.sleep(wait_ms / 1000)
                wait_ms *= wait_ratio

async def setup_utility_meter_select(
    hass: HomeAssistant,
    config: ConfigType,
    meter: str,
    conf: dict,
) -> str:
    """Create the select for utility_meters."""
    # Only create the select if multiple tariffs are created
    if not conf.get(CONF_TARIFFS):
        _LOGGER.debug("Setup %s.%s: skip utility_meter select entity", DOMAIN, meter)
        return ""

    _LOGGER.debug("Setup %s.%s: create utility_meter select entity", DOMAIN, meter)
    # create tariff selection
    hass.async_create_task(
        discovery.async_load_platform(
            hass,
            SELECT_DOMAIN,
            UM_DOMAIN,
            {CONF_METER: meter, CONF_TARIFFS: conf[CONF_TARIFFS]},
            config,
        ),
    )

    # create the select entity ID the same way utility_meter does
    return f"{SELECT_DOMAIN}.{meter}"


async def setup_utility_meter_sensors(
    hass: HomeAssistant,
    config: ConfigType,
    meter: str,
    conf: dict,
    select_entity: str,
):
    """Create the utility_meter sensors linked to the select entity."""
    # use of copy of the conf to keep data of energy & cost separate
    hass.data[DATA_UTILITY][meter] = conf.copy()
    hass.data[DATA_UTILITY][meter][DATA_TARIFF_SENSORS] = []

    if not conf.get(CONF_TARIFFS):
        _LOGGER.debug(
            "Setup %s.%s: create a single utility_meter sensor",
            DOMAIN,
            meter,
        )
        # only one entity is required
        hass.async_create_task(
            discovery.async_load_platform(
                hass,
                SENSOR_DOMAIN,
                UM_DOMAIN,
                {meter: {CONF_METER: meter}},
                config,
            ),
        )
    else:
        # Indicate the select entity for the tariff selection
        hass.data[DATA_UTILITY][meter][CONF_TARIFF_ENTITY] = select_entity

        # add one meter for each tariff for energy
        tariff_confs = {}
        for tariff in conf[CONF_TARIFFS]:
            name = f"{meter} {tariff}"
            tariff_confs[name] = {
                CONF_METER: meter,
                CONF_TARIFF: tariff,
            }

        _LOGGER.debug(
            "Setup %s.%s: create utility_meter sensors for tariffs %s",
            DOMAIN,
            meter,
            conf[CONF_TARIFFS],
        )
        hass.async_create_task(
            discovery.async_load_platform(
                hass,
                SENSOR_DOMAIN,
                UM_DOMAIN,
                tariff_confs,
                config,
            ),
        )
