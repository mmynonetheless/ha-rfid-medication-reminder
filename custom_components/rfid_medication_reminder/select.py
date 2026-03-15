from homeassistant.components.select import SelectEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.core import callback
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        KnownTagsSelect(coordinator, entry),
        ClearTagSelect(coordinator, entry),
    ])

class KnownTagsSelect(SelectEntity):
    def __init__(self, coordinator, entry):
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_known_tags_select"
        self._attr_name = "Known RFID Tags"
        self._attr_icon = "mdi:tag-multiple"
        self._attr_options = []
        self._attr_current_option = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Reminder",
        )

    @callback
    def _handle_coordinator_update(self):
        tags = self._coordinator.get("known_tags", set())
        self._attr_options = sorted(tags)
        if self._attr_current_option not in self._attr_options:
            self._attr_current_option = None
        self.async_write_ha_state()

    async def async_select_option(self, option: str):
        self._attr_current_option = option
        self.async_write_ha_state()

class ClearTagSelect(SelectEntity):
    def __init__(self, coordinator, entry):
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_clear_tag"
        self._attr_name = "Clear by RFID Tag"
        self._attr_icon = "mdi:rfid"
        self._attr_options = []
        self._attr_current_option = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Reminder",
        )

    @callback
    def _handle_coordinator_update(self):
        tags = self._coordinator.get("known_tags", set())
        self._attr_options = sorted(tags)
        self.async_write_ha_state()

    async def async_select_option(self, option: str):
        from . import _process_scan
        await _process_scan(self.hass, self._entry, option)
        self._attr_current_option = None
        self.async_write_ha_state()
