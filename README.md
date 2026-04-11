# HomePulse

Custom Home Assistant integration for managing recurring home maintenance tasks with Google Calendar synchronization.

## Features

- **Task management** — create, complete, and delete recurring tasks
- **Binary sensors** — one sensor per task; state `ON` when the task is due or overdue
- **Google Calendar sync** — creates calendar events automatically when tasks are completed
- **Lovelace card** — inline task management directly on the dashboard, no page navigation needed

## Installation (HACS)

1. Add this repository to HACS as a custom repository (type: Integration)
2. Install **HomePulse** from HACS
3. Restart Home Assistant
4. Go to **Settings → Devices & Services → Add Integration** and search for **HomePulse**

## Lovelace card setup

After installing the integration, register the frontend resource:

```yaml
# configuration.yaml or via Settings → Dashboards → Resources
lovelace:
  resources:
    - url: /local/home-pulse-card.js
      type: module
```

Add the card to your dashboard:

```yaml
type: custom:home-pulse-card
title: Konserwacja domu
```

## Services

| Service | Description |
|---|---|
| `home_pulse.add_task` | Create a new maintenance task |
| `home_pulse.complete_task` | Mark a task as done and schedule next occurrence |
| `home_pulse.delete_task` | Permanently remove a task |

### Example: add a task via automation

```yaml
service: home_pulse.add_task
data:
  title: Wymiana filtrów powietrza
  interval_value: 3
  interval_unit: months
  google_calendar_entity: calendar.home
```

## Binary sensor attributes

Each task exposes a `binary_sensor.home_pulse_*` entity with:

| Attribute | Description |
|---|---|
| `task_id` | UUID of the task |
| `next_due_date` | Next scheduled date (ISO) |
| `days_until_next` | Days until due (0 when overdue) |
| `overdue_by_days` | How many days past due |
| `interval_value` | Repeat interval number |
| `interval_unit` | `days` / `weeks` / `months` |
| `last_performed` | Date of last completion |

## Google Calendar integration

HomePulse uses HA's built-in `calendar.create_event` service. Make sure you have the [Google Calendar integration](https://www.home-assistant.io/integrations/google/) configured in Home Assistant.

## Storage

Task data is stored in `.storage/home_pulse` inside your HA config directory. No external database required.
