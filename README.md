# Correios

[![CI](https://github.com/roquerodrigo/ha-correios/actions/workflows/ci.yml/badge.svg)](https://github.com/roquerodrigo/ha-correios/actions/workflows/ci.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-db61a2?logo=githubsponsors&logoColor=white&style=for-the-badge)](https://github.com/sponsors/roquerodrigo)

[![Open your Home Assistant instance and open the repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=roquerodrigo&repository=ha-correios&category=integration)

---

[Home Assistant](https://www.home-assistant.io/) integration that tracks the
[Correios](https://rastreamento.correios.com.br/app/index.php) packages tied to
your CPF or CNPJ. There are no tracking codes to type: the integration signs in
to the Correios tracking website with your account and follows every package the
website lists for you — the ones addressed to you and the ones you sent.

## Requirements

- A Correios account (the same username and password used on the Correios
  website and app). The username can be a CPF, a CNPJ or an idCorreios.
- Home Assistant 2026.7.2 or newer.

## Installation

### HACS (recommended)

1. Open the repository inside HACS with the button above, or add
   `https://github.com/roquerodrigo/ha-correios` as a custom repository of type
   **Integration**.
2. Install **Correios** and restart Home Assistant.

### Manual

Copy `custom_components/correios/` into the `custom_components/` directory of
your Home Assistant configuration and restart Home Assistant.

## Configuration

Go to **Settings → Devices & services → Add integration → Correios** and enter
your username and password. Each account becomes one service device, named
after the account (a CPF is masked, e.g. `***.456.789-**`).

Options (**Configure** on the integration entry):

| Option | Default | Description |
| --- | --- | --- |
| Polling interval | 900 s | How often the package list is refreshed (minimum 300 s). |
| Keep delivered packages for | 7 days | How long a delivered package keeps its sensor. `0` drops it as soon as it is delivered. |

If the password changes, Home Assistant asks for the new one through the
re-authentication flow; the credentials can also be edited with **Reconfigure**.

## Entities

| Entity | Description |
| --- | --- |
| `sensor.correios_<account>_packages_in_transit` | Number of packages on their way to you. Attribute `tracking_codes` lists them. |
| `sensor.correios_<account>_sent_packages_in_transit` | Number of packages you sent that were not delivered yet. Attribute `tracking_codes` lists them. |
| `sensor.correios_<account>_next_delivery` | Closest expected delivery date among the packages on their way to you. Attribute `tracking_code` tells which package it is. |
| `sensor.correios_<account>_package_<tracking code>` | One per tracked package. The state is the latest tracking status as reported by Correios. |
| `event.correios_<account>_package_update` | Fires `new_package`, `status_changed` or `delivered` whenever a refresh detects a change. |

Package sensors are created and removed automatically: a package gets a sensor
when the website starts listing it and loses it once it has been delivered for
longer than the configured retention.

### Package sensor attributes

`tracking_code`, `direction` (`received` / `sent`), `delivered`, `delayed`,
`detail`, `location`, `category`, `expected_delivery`, `last_event_at` and
`events` — the full history, newest first, each entry with `description`,
`detail`, `occurred_at`, `location` and `destination`. The `events` attribute is
not written to the recorder.

## Dashboard card

The integration ships a companion card and registers it as a dashboard resource
on setup — there is nothing to install. Add it from the card picker
(**Correios**) or in YAML:

```yaml
type: custom:correios-card
title: Packages
show_delivered: true
show_sent: true
show_history: true
max_events: 10
```

The card finds the package sensors by itself, lists packages in transit first,
and expands a package into its tracking history on tap. A package sensor renamed
in Home Assistant (e.g. "Mechanical keyboard") is shown by that name, with the
tracking code underneath.

| Option | Default | Description |
| --- | --- | --- |
| `title` | `Correios` | Card title. |
| `show_delivered` | `true` | List delivered packages still being tracked. |
| `show_sent` | `true` | List packages sent by the account holder. |
| `show_history` | `true` | Expand the tracking history on tap. When `false`, a tap opens the more-info dialog. |
| `max_events` | `10` | Maximum number of events shown in the history. |

On dashboards managed in YAML mode the resource cannot be registered
automatically; the card is loaded as an extra frontend module instead.

### Notification example

```yaml
automation:
  - alias: Correios - package update
    triggers:
      - trigger: state
        entity_id: event.correios_456_789_package_update
        not_from: unavailable
    actions:
      - action: notify.notify
        data:
          title: "Correios {{ trigger.to_state.attributes.tracking_code }}"
          message: >-
            {{ trigger.to_state.attributes.status }}
            ({{ trigger.to_state.attributes.location }})
```

## Notes

- Statuses, details and locations are shown exactly as Correios reports them,
  in Portuguese.
- The Correios website has frequent short outages. A failed refresh keeps the
  last known data for up to one hour before the entities become unavailable.
- This project is not affiliated with Correios. It relies on the public
  tracking website, which can change without notice.

## Development

```bash
scripts/setup     # create .venv with uv and install the dev + lint groups
scripts/lint      # ruff format --check, ruff check, mypy, pytest, node --check on the card
scripts/develop   # run Home Assistant with the integration loaded
```

Conventions for contributors live in [`CODE_STYLE.md`](./CODE_STYLE.md) and
[`CONTRIBUTING.md`](./CONTRIBUTING.md).

## Support

This integration is built and maintained on personal time. If it is useful to you, consider [sponsoring the work](https://github.com/sponsors/roquerodrigo) — it keeps the development, the testing and the releases coming.

## License

[MIT](LICENSE)
