"""Select platform for RFID Medication Reminder."""
from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_REMINDER_NAME, CONF_ENABLED

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up select entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    selects = []

    # Create a select for each reminder to choose actions (no snooze)
    reminders = coordinator["reminders"]
    for i, reminder in enumerate(reminders):
        selects.append(ReminderActionSelect(coordinator, entry, i, reminder))

    async_add_entities(selects, True)

class ReminderActionSelect(SelectEntity):
    """Select for reminder actions (no snooze)."""

    def __init__(self, coordinator, entry, index, reminder):
        """Initialize the select."""
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
        """Handle option selection."""
        reminder_name = self._reminder[CONF_REMINDER_NAME]
        
        if option == "Edit":
            self.hass.bus.async_fire(f"{DOMAIN}_show_edit_form", {
                "reminder_name": reminder_name
            })
        elif option == "Delete":
            self.hass.bus.async_fire(f"{DOMAIN}_confirm_delete", {
                "reminder_name": reminder_name
            })
        elif option == "Test":
            # Force trigger the reminder regardless of conditions
            self.hass.bus.async_fire(f"{DOMAIN}_test_reminder", {
                "reminder_name": reminder_name
            })
        elif option == "Enable/Disable":
            # Toggle enabled state
            reminders = self._coordinator["reminders"]
            for r in reminders:
                if r[CONF_REMINDER_NAME] == reminder_name:
                    r[CONF_ENABLED] = not r.get(CONF_ENABLED, True)
                    break
            await self._coordinator["store"].async_save({"reminders": reminders})
            self.hass.bus.async_fire(f"{DOMAIN}_reminders_updated", {})
        elif option == "Add Condition":
            self.hass.bus.async_fire(f"{DOMAIN}_show_condition_form", {
                "reminder_name": reminder_name
            })

        self._attr_current_option = None
        self.async_write_ha_state()
