# Multi-RFID Reminder System for Home Assistant

A powerful, customizable reminder system that supports **multiple reminders** with different RFID tags, each with its own interval, message, media players, and phone notifications. Alerts loop until the correct RFID tag is scanned.

## Features

- ✅ Multiple independent reminders
- ✅ Per-reminder RFID tags
- ✅ Customizable intervals (0.5–24 hours)
- ✅ Media player alerts (looping sound)
- ✅ Phone notifications (Find My style – critical alerts, vibration, LED, action buttons)
- ✅ Snooze (10 minutes) from notification
- ✅ JSON‑based configuration stored in an `input_text` helper
- ✅ Easy management via service calls

---

## Installation

### Option 1: Manual Installation (Packages)

1. Copy `multi_rfid_reminder.yaml` into your Home Assistant `packages/` directory.  
   (Create the folder if it doesn't exist.)
2. Ensure your `configuration.yaml` includes:
   ```yaml
   homeassistant:
     packages: !include_dir_named packages
   ```

   ## Option 2: HACS (as a custom repository)

1. Add this repository to HACS as a custom repository (category: "Integration" or "Package")
2. Download the files
3. Follow the manual installation steps above

---

## Prerequisites

Before using this system, you need:

| Requirement | Description |
|------------|-------------|
| RFID Reader | Connected to Home Assistant (MQTT or direct integration) |
| Audio File | Place `alert.mp3` in `/config/www/media/` |
| Mobile App | Home Assistant Companion app installed on phones |
| Notification Targets | Device IDs from Settings → Devices & Services → Mobile App |

---

## Adding Your First Reminder

Go to **Developer Tools → Services** and call:

```yaml
service: script.add_rfid_reminder
data:
  reminder_name: "Medication"
  rfid_tag: "1234567890"
  interval_hours: 8
  volume: 0.8
  media_players: '["media_player.living_room"]'
  notification_targets: '["device_tracker.my_phone"]'
  custom_message: "Time for your medication!"
```
## Service Details

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| reminder_name | Yes | - | Unique name for the reminder |
| rfid_tag | Yes | - | The RFID tag ID that clears this reminder |
| interval_hours | Yes | - | Hours between triggers (0.5 to 24) |
| volume | No | 0.7 | Alert volume (0.1 to 1.0) |
| media_players | No | [] | JSON array of media_player entity IDs |
| notification_targets | No | [] | JSON array of mobile_app device IDs |
| custom_message | Yes | - | Message shown in notifications |

---

## How It Works

1. **Monitor runs every minute** checking all reminders
2. **When interval elapsed** → reminder activates
3. **Alerts loop until cleared**:
   - Media players play sound every 10 seconds
   - Phones receive critical notifications every 30 seconds
4. **Scan RFID tag** → stops all alerts for that tag
5. **Snooze from notification** → pauses for 10 minutes

---

## Notification Features (Find My Style)

| Feature | Implementation |
|---------|----------------|
| Critical Alerts | Bypasses silent mode |
| Persistent Sound | Loops until cleared |
| LED Indicator | Red LED on supported devices |
| Vibration Pattern | 1s on, 1s off, 1s on |
| Action Buttons | Snooze (10min) and Clear |
| Dedicated Channel | Uses "alarm_stream" channel |
| High Priority | Bypasses Do Not Disturb |

---

## Viewing Active Reminders

Check current configurations in **Developer Tools → States**:
 ```
Search for: input_text.reminder_configs
 ```

The value shows a JSON array of all reminders with their current status:
- `active: true` = currently alerting
- `enabled: true` = active in the system
- `snooze_until` = timestamp if snoozed

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| No sound on media players | Verify `alert.mp3` exists in `/config/www/media/` and test with `media_player.play_media` service |
| Phone notifications not working | Ensure mobile app is installed and use correct device IDs from Settings → Devices & Services → Mobile App |
| RFID tag not clearing | Check tag ID matches exactly and monitor logs for errors |
| Reminder not triggering | Verify `enabled: true` in config and check automation logs |

---

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
yaml
reminder_name: "Water Plants"
rfid_tag: "5555555555"
interval_hours: 24
volume: 0.6
media_players: '["media_player.living_room"]'
notification_targets: '["device_tracker.my_phone"]'
custom_message: "Time to water the plants 🌱"
```

---

## File Structure

```
text
/config/
├── packages/
│   └── multi_rfid_reminder.yaml
├── www/
│   └── media/
│       └── alert.mp3
└── configuration.yaml
```
---

## Credits

- Inspired by the Google Find My integration style
- Based on original RFID reminder system
- Phone notification pattern from mobile_app integration

---

## License

MIT License - feel free to modify and share

---

## Support

- GitHub Issues: [Open an issue](https://github.com/YOUR_USERNAME/ha-multi-rfid-reminder/issues)
- Home Assistant Community: Search for "RFID reminder"

---

*Remember: After installation, restart Home Assistant and test with a single reminder before adding more!*
