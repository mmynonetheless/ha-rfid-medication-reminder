"""Sensor platform for RFID Medication Reminder."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ATTR_REMINDERS,
    ATTR_ACTIVE_REMINDERS,
    ATTR_TOTAL_REMINDERS,
    ICON_REMINDER,
    ICON_ACTIVE,
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = [
        RFIDReminderStatusSensor(coordinator, entry),
        RFIDReminderListSensor(coordinator, entry),
        RFIDTagListSensor(coordinator, entry),
    ]
    for i, reminder in enumerate(coordinator["reminders"]):
        sensors.append(IndividualReminderSensor(coordinator, entry, i, reminder))
    async_add_entities(sensors, True)

class RFIDReminderStatusSensor(CoordinatorEntity, SensorEntity):
    """Main status sensor showing number of active reminders."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_status"
        self._attr_name = "RFID Reminder Status"
        self._attr_icon = ICON_REMINDER
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    @property
    def native_value(self):
        active = sum(1 for r in self._coordinator["reminders"] if r.get("active"))
        return active

    @property
    def extra_state_attributes(self):
        reminders = self._coordinator["reminders"]
        return {
            ATTR_ACTIVE_REMINDERS: sum(1 for r in reminders if r.get("active")),
            ATTR_TOTAL_REMINDERS: len(reminders),
            "reminder_names": [r.get("reminder_name") for r in reminders],
        }

class RFIDReminderListSensor(CoordinatorEntity, SensorEntity):
    """Sensor that lists all reminders with their conditions."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_list"
        self._attr_name = "RFID Reminder List"
        self._attr_icon = "mdi:format-list-bulleted"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    @property
    def native_value(self):
        return len(self._coordinator["reminders"])

    @property
    def extra_state_attributes(self):
        reminders = self._coordinator["reminders"]
        reminder_list = []
        for r in reminders:
            copy = r.copy()
            if copy.get("conditions"):
                copy["has_conditions"] = True
                copy["condition_count"] = len(copy["conditions"])
            reminder_list.append(copy)
        return {ATTR_REMINDERS: reminder_list}

class RFIDTagListSensor(CoordinatorEntity, SensorEntity):
    """Sensor that lists all known RFID tags."""

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_tag_list"
        self._attr_name = "RFID Tag List"
        self._attr_icon = "mdi:rfid"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    @property
    def native_value(self):
        return len(self._coordinator.get("known_tags", set()))

    @property
    def extra_state_attributes(self):
        tags = list(self._coordinator.get("known_tags", set()))
        return {"tags": tags, "tag_count": len(tags)}

class IndividualReminderSensor(CoordinatorEntity, SensorEntity):
    """Sensor for an individual reminder with condition status."""

    def __init__(self, coordinator, entry, index, reminder):
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._index = index
        self._reminder = reminder
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_reminder_{index}"
        self._attr_name = reminder.get("reminder_name", "Unknown")
        self._attr_icon = ICON_ACTIVE if reminder.get("active") else ICON_REMINDER
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    @property
    def native_value(self):
        return "active" if self._reminder.get("active") else "inactive"

    @property
    def extra_state_attributes(self):
        copy = self._reminder.copy()
        conditions = copy.get("conditions", [])
        if conditions:
            copy["condition_count"] = len(conditions)
            copy["condition_type"] = copy.get("condition_type", "all")
            summaries = []
            for cond in conditions:
                parts = []
                if cond.get("time_window"):
                    parts.append(f"Time: {cond.get('time_start','00:00')}-{cond.get('time_end','23:59')}")
                if cond.get("weekdays"):
                    parts.append(f"Days: {', '.join(cond['weekdays'])}")
                for ec in cond.get("entity_conditions", []):
                    parts.append(f"Entity: {ec.get('condition_entity')} {ec.get('condition_operator')} {ec.get('condition_state', ec.get('condition_value'))}")
                summaries.append(" | ".join(parts))
            copy["condition_summaries"] = summaries
        return copy
