"""Button platform for RFID Medication Reminder."""
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, ICON_REMINDER, CONF_REMINDER_NAME

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    buttons = [AddReminderButton(coordinator, entry)]

    # Add a "Set Tag from Known" button for each reminder
    for i, reminder in enumerate(coordinator["reminders"]):
        buttons.append(SetReminderTagButton(coordinator, entry, i, reminder))

    async_add_entities(buttons, True)


class AddReminderButton(ButtonEntity):
    """Button to add a new reminder."""

    def __init__(self, coordinator, entry):
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_add_reminder"
        self._attr_name = "Add New Reminder"
        self._attr_icon = ICON_REMINDER
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    async def async_press(self) -> None:
        self.hass.bus.async_fire(f"{DOMAIN}_show_add_form", {})


class SetReminderTagButton(ButtonEntity):
    """Button to set this reminder's RFID tag to the currently selected known tag."""

    def __init__(self, coordinator, entry, index, reminder):
        self._coordinator = coordinator
        self._entry = entry
        self._index = index
        self._reminder = reminder
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_set_tag_{index}"
        self._attr_name = f"{reminder[CONF_REMINDER_NAME]} - Set Tag from Known"
        self._attr_icon = "mdi:tag-arrow-right"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    async def async_press(self) -> None:
        """Get selected tag from KnownTagsSelect and apply to this reminder."""
        # Find the known tags select entity
        known_tags_entity_id = f"select.{DOMAIN}_{self._entry.entry_id}_known_tags"
        known_state = self.hass.states.get(known_tags_entity_id)
        if not known_state or not known_state.state:
            # No tag selected – maybe fire a notification
            self.hass.bus.async_fire(f"{DOMAIN}_no_tag_selected", {})
            return

        selected_tag = known_state.state

        # Update this reminder's RFID tag
        reminders = self._coordinator["reminders"]
        for r in reminders:
            if r[CONF_REMINDER_NAME] == self._reminder[CONF_REMINDER_NAME]:
                r["rfid_tag"] = selected_tag
                break

        await self._coordinator["store"].async_save({"reminders": reminders})
        self.hass.bus.async_fire(f"{DOMAIN}_reminders_updated", {})
