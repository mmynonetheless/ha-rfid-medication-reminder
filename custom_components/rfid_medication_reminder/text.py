"""Text platform for RFID Medication Reminder."""
from homeassistant.components.text import TextEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_REMINDER_NAME, CONF_CUSTOM_MESSAGE, CONF_RFID_TAG

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up text entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    texts = []

    # Create text entities for each reminder's message and RFID tag
    reminders = coordinator["reminders"]
    for i, reminder in enumerate(reminders):
        texts.append(ReminderMessageText(coordinator, entry, i, reminder))
        texts.append(ReminderRFIDText(coordinator, entry, i, reminder))

    async_add_entities(texts, True)

class ReminderMessageText(TextEntity):
    """Text entity for reminder message."""

    def __init__(self, coordinator, entry, index, reminder):
        """Initialize the text."""
        self._coordinator = coordinator
        self._entry = entry
        self._index = index
        self._reminder = reminder
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_message_{index}"
        self._attr_name = f"{reminder[CONF_REMINDER_NAME]} Message"
        self._attr_native_value = reminder.get(CONF_CUSTOM_MESSAGE, "")
        self._attr_icon = "mdi:message-text"
        self._attr_mode = "text"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    async def async_set_value(self, value: str) -> None:
        """Update the current value."""
        reminders = self._coordinator["reminders"]
        for i, r in enumerate(reminders):
            if i == self._index:
                r[CONF_CUSTOM_MESSAGE] = value
                break
        await self._coordinator["store"].async_save({"reminders": reminders})
        self._attr_native_value = value
        self.async_write_ha_state()

class ReminderRFIDText(TextEntity):
    """Text entity for reminder RFID tag."""

    def __init__(self, coordinator, entry, index, reminder):
        """Initialize the text."""
        self._coordinator = coordinator
        self._entry = entry
        self._index = index
        self._reminder = reminder
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_rfid_{index}"
        self._attr_name = f"{reminder[CONF_REMINDER_NAME]} RFID Tag"
        self._attr_native_value = reminder.get(CONF_RFID_TAG, "")
        self._attr_icon = "mdi:rfid"
        self._attr_mode = "text"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    async def async_set_value(self, value: str) -> None:
        """Update the current value."""
        reminders = self._coordinator["reminders"]
        for i, r in enumerate(reminders):
            if i == self._index:
                r[CONF_RFID_TAG] = value
                break
        await self._coordinator["store"].async_save({"reminders": reminders})
        self._attr_native_value = value
        self.async_write_ha_state()
