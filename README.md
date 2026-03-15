# RFID Medication Reminder for Home Assistant

A powerful, customizable medication reminder system with **full UI configuration** and **conditional reminders**. No manual YAML or service calls required!

## Features

- ✅ **Full UI Configuration** - Add reminders through dropdown menus and forms
- ✅ **Multiple Independent Reminders** - Each with its own RFID tag, interval, and message
- ✅ **Conditional Reminders** - Only trigger when specific conditions are met
- ✅ **Time Windows** - Set reminders to only trigger between certain hours
- ✅ **Day-based Conditions** - Weekdays, days of month, or specific months
- ✅ **Entity State Conditions** - Trigger based on other Home Assistant entities
- ✅ **Media Player Alerts** - Looping sound on any media player
- ✅ **Phone Notifications** - Critical alerts with Find My style notifications
- ✅ **RFID Clearing** - Scan RFID tag to stop active reminders
- ✅ **Per-Reminder Controls** - Volume, interval, and message for each reminder

## Installation

### HACS Installation (Recommended)

1. Open HACS → Integrations → Custom repositories
2. Add: `https://github.com/mmynonetheless/ha-rfid-medication-reminder`
3. Category: Integration
4. Click Download
5. Restart Home Assistant

### Manual Installation

1. Download the `rfid_medication_reminder` folder
2. Copy to `custom_components/` directory
3. Restart Home Assistant

## Configuration

After installation, go to **Settings → Devices & Services → Add Integration** and search for "RFID Medication Reminder".

## Adding a Reminder

1. Go to your dashboard
2. Click the "Add New Reminder" button
3. Fill in the form:
   - **Reminder Name**: Unique name (e.g., "Morning Medication")
   - **RFID Tag**: The tag ID that will clear this reminder
   - **Interval Hours**: Hours between triggers (0.5-24)
   - **Volume**: Alert volume (0.1-1.0)
   - **Media Players**: Select which speakers to use
   - **Notification Targets**: Select phones to notify
   - **Custom Message**: The reminder message

## Adding Conditions

1. Find your reminder in the list
2. Select "Add Condition" from the action dropdown
3. Configure conditions:
   - **Time Window**: Set start and end times
   - **Weekdays**: Select which days of the week
   - **Entity Conditions**: Add conditions based on other entities

## Available Condition Operators

| Operator | Description |
|----------|-------------|
| `eq` | Equal to |
| `ne` | Not equal to |
| `gt` | Greater than |
| `lt` | Less than |
| `gte` | Greater than or equal |
| `lte` | Less than or equal |
| `in` | Value in list |
| `not_in` | Value not in list |
| `home` | Entity is home/on |
| `not_home` | Entity is not home/off |

## Events

| Event | Description | Data |
|-------|-------------|------|
| `rfid_medication_reminder_triggered` | Reminder triggered | reminder_name, rfid_tag, message |
| `rfid_medication_reminder_cleared` | Reminder cleared | rfid_tag, cleared_reminders |
| `rfid_medication_reminder_rfid_scanned` | RFID tag scanned | rfid_tag, cleared_reminders |
| `rfid_medication_reminder_condition_met` | Conditions met | reminder_name |
| `rfid_medication_reminder_condition_not_met` | Conditions not met | reminder_name |



## Example Configurations

### Medication Reminder (8 hours)
```yaml
reminder_name: "Medication"
rfid_tag: "1234567890"
interval_hours: 8
volume: 0.8
media_players: '["media_player.bedroom"]'
notification_targets: '["device_tracker.my_phone"]'
custom_message: "Time for evening medication"
```

### Hydration Reminder (2 hours)

```yaml
reminder_name: "Hydration"
rfid_tag: "0987654321"
interval_hours: 2
volume: 0.5
media_players: '["media_player.kitchen"]'
notification_targets: '["device_tracker.my_phone", "device_tracker.tablet"]'
custom_message: "Drink water! 💧"
```

### Chore Reminder (Daily)
```
yaml
reminder_name: "Water Plants"
rfid_tag: "5555555555"
interval_hours: 24
volume: 0.6
media_players: '["media_player.living_room"]'
notification_targets: '["device_tracker.my_phone"]'
custom_message: "Time to water the plants 🌱"
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No sound on media players | Verify `alert.mp3` exists in `/config/www/media/` |
| Phone notifications not working | Use correct device IDs from Settings → Devices & Services → Mobile App |
| RFID tag not clearing | Check that the tag ID matches exactly |
| Reminder not triggering | Check conditions and verify reminder is enabled |
| Conditions not working | Check that condition entities exist and have valid states |

## License

MIT License

---

*Remember: After installation, restart Home Assistant and test with a single reminder before adding more!*
