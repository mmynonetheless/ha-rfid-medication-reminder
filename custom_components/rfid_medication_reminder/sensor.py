from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.entity import DeviceInfo
from .const import DOMAIN

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        ActiveReminderSensor(coordinator, entry),
        KnownTagsSensor(coordinator, entry),
    ])

class ActiveReminderSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_active"
        self._attr_name = "Active Reminders"
        self._attr_icon = "mdi:bell-ring"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Reminder",
            manufacturer="Community",
        )

    @property
    def native_value(self):
        return sum(1 for r in self._coordinator["reminders"] if r.get("active"))

    @property
    def extra_state_attributes(self):
        return {
            "reminders": [r for r in self._coordinator["reminders"] if r.get("active")]
        }

class KnownTagsSensor(SensorEntity):
    def __init__(self, coordinator, entry):
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_known_tags_count"
        self._attr_name = "Known RFID Tags"
        self._attr_icon = "mdi:tag-multiple"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Reminder",
        )

    @property
    def native_value(self):
        return len(self._coordinator.get("known_tags", set()))

    @property
    def extra_state_attributes(self):
        return {"tags": sorted(self._coordinator.get("known_tags", set()))}
