"""Select platform for RFID Medication Reminder."""
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_REMINDER_NAME, CONF_ENABLED
from . import _process_rfid_scan, get_known_tags

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    selects = []
    for i, reminder in enumerate(coordinator["reminders"]):
        selects.append(ReminderActionSelect(coordinator, entry, i, reminder))
    selects.append(RFIDTagClearSelect(coordinator, entry))
    async_add_entities(selects, True)

class ReminderActionSelect(SelectEntity):
    """Select for reminder actions (no snooze)."""

    def __init__(self, coordinator, entry, index, reminder):
        self._coordinator = coordinator
        self._entry = entry
        self._index = index
        self._reminder = reminder
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_action_{index}"
        self._attr_name = f"{reminder[CONF_REMINDER_NAME]} Action"
        self._attr_options = ["Edit", "Delete", "Test", "Enable/Disable", "Add Condition"]
        self._attr_current_option = None
        self._attr_icon = "mdi:dots-vertical"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    async def async_select_option(self, option: str) -> None:
        name = self._reminder[CONF_REMINDER_NAME]
        if option == "Edit":
            self.hass.bus.async_fire(f"{DOMAIN}_show_edit_form", {"reminder_name": name})
        elif option == "Delete":
            self.hass.bus.async_fire(f"{DOMAIN}_confirm_delete", {"reminder_name": name})
        elif option == "Test":
            self.hass.bus.async_fire(f"{DOMAIN}_test_reminder", {"reminder_name": name})
        elif option == "Enable/Disable":
            reminders = self._coordinator["reminders"]
            for r in reminders:
                if r[CONF_REMINDER_NAME] == name:
                    r[CONF_ENABLED] = not r.get(CONF_ENABLED, True)
                    break
            await self._coordinator["store"].async_save({"reminders": reminders})
            self.hass.bus.async_fire(f"{DOMAIN}_reminders_updated", {})
        elif option == "Add Condition":
            self.hass.bus.async_fire(f"{DOMAIN}_show_condition_form", {"reminder_name": name})
        self._attr_current_option = None
        self.async_write_ha_state()

class RFIDTagClearSelect(SelectEntity):
    """Select to pick a tag to clear all reminders for that tag."""

    def __init__(self, coordinator, entry):
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_tag_clear"
        self._attr_name = "Clear by RFID Tag"
        self._attr_icon = "mdi:rfid"
        self._attr_options = []
        self._attr_current_option = None
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    async def async_select_option(self, option: str) -> None:
        await _process_rfid_scan(self.hass, self._entry, option)
        self._attr_current_option = None
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        tags = self._coordinator.get("known_tags", set())
        self._attr_options = sorted(tags)
        self.async_write_ha_state()
