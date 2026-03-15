"""Number platform for RFID Medication Reminder."""
from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, CONF_REMINDER_NAME, CONF_VOLUME, CONF_INTERVAL_HOURS

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    numbers = []

    # Create number entities for each reminder's volume and interval
    reminders = coordinator["reminders"]
    for i, reminder in enumerate(reminders):
        numbers.append(ReminderVolumeNumber(coordinator, entry, i, reminder))
        numbers.append(ReminderIntervalNumber(coordinator, entry, i, reminder))

    async_add_entities(numbers, True)

class ReminderVolumeNumber(NumberEntity):
    """Number entity for reminder volume."""

    def __init__(self, coordinator, entry, index, reminder):
        """Initialize the number."""
        self._coordinator = coordinator
        self._entry = entry
        self._index = index
        self._reminder = reminder
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_volume_{index}"
        self._attr_name = f"{reminder[CONF_REMINDER_NAME]} Volume"
        self._attr_native_min_value = 0.1
        self._attr_native_max_value = 1.0
        self._attr_native_step = 0.1
        self._attr_native_value = reminder.get(CONF_VOLUME, 0.7)
        self._attr_icon = "mdi:volume-high"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        reminders = self._coordinator["reminders"]
        for i, r in enumerate(reminders):
            if i == self._index:
                r[CONF_VOLUME] = value
                break
        await self._coordinator["store"].async_save({"reminders": reminders})
        self._attr_native_value = value
        self.async_write_ha_state()

class ReminderIntervalNumber(NumberEntity):
    """Number entity for reminder interval."""

    def __init__(self, coordinator, entry, index, reminder):
        """Initialize the number."""
        self._coordinator = coordinator
        self._entry = entry
        self._index = index
        self._reminder = reminder
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_interval_{index}"
        self._attr_name = f"{reminder[CONF_REMINDER_NAME]} Interval"
        self._attr_native_min_value = 0.5
        self._attr_native_max_value = 24.0
        self._attr_native_step = 0.5
        self._attr_native_value = reminder.get(CONF_INTERVAL_HOURS, 4.0)
        self._attr_icon = "mdi:timer"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    async def async_set_native_value(self, value: float) -> None:
        """Update the current value."""
        reminders = self._coordinator["reminders"]
        for i, r in enumerate(reminders):
            if i == self._index:
                r[CONF_INTERVAL_HOURS] = value
                break
        await self._coordinator["store"].async_save({"reminders": reminders})
        self._attr_native_value = value
        self.async_write_ha_state()
