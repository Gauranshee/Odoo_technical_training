# Estate Module — Odoo 17.0

A custom Odoo module built as a capstone project for the Odoo Technical Training program.
It demonstrates production-safe practices across all 12 training modules.

---

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Module Structure](#module-structure)
4. [Installation](#installation)
5. [Configuration](#configuration)
6. [Modules Covered](#modules-covered)
7. [Ready-Made Tasks](#ready-made-tasks)
8. [API Reference](#api-reference)
9. [Cron Jobs](#cron-jobs)
10. [Security](#security)
11. [Dependencies](#dependencies)

---

## Overview

The **Estate** module is a real estate property management system built on Odoo 17.0.
It covers property listings, offer management, property types, tags, and integrates with
Odoo's core modules: CRM, Sales, Inventory, and Accounting.

---

## Features

| Feature | Description |
|---|---|
| Property Management | Create, track, and manage real estate properties with status pipeline |
| Auto Sequence | Properties are auto-assigned codes: PROP0001, PROP0002, ... |
| Offer Management | Buyers submit offers; salesperson accepts/refuses with price tracking |
| Property Types | Categorise properties with drag-and-drop ordering |
| Tags | Color-coded many2many tags for quick property classification |
| CRM Integration | `source_reference` field + validation on Won stage |
| Sales Integration | Blocks Sale Order confirmation if customer GST is missing |
| Inventory Integration | `delivery_note_no` added to stock transfers |
| External API | Fetches and stores posts from JSONPlaceholder REST API |
| Cron Automation | Daily jobs for expiry management and CRM lead prioritisation |
| Invoice Report | Custom note injected into Odoo's standard invoice PDF |
| Security | Role-based groups, model access rules, and record-level rules |

---

## Module Structure

```
estate/
├── __init__.py                     # Registers models and controllers
├── __manifest__.py                 # Module metadata and file load order
│
├── models/
│   ├── estate_property.py          # Core property model (cron, constraints, sequence)
│   ├── estate_property_offer.py    # Offer model (compute/inverse, CRUD override)
│   ├── estate_property_type.py     # Property type with offer count (read_group)
│   ├── estate_property_tag.py      # Many2many tags with color support
│   ├── res_users.py                # Extends res.users with property list
│   ├── crm_inherit.py              # Task 1: CRM validation
│   ├── sale_order.py               # Task 2: Sale Order GST check
│   ├── sale_stock_inherit.py       # Task 3: Delivery note fields
│   ├── cron_job.py                 # Task 5: Scheduled CRM automation
│   └── estate_api_data.py          # Task 6: External API integration
│
├── controllers/
│   └── main.py                     # JSON API endpoint: GET /api/properties
│
├── views/
│   ├── estate_property_views.xml   # All estate views + XPath inheritance
│   ├── estate_api_views.xml        # API data tree/form + server action
│   ├── estate_menu.xml             # Menu structure
│   ├── invoice_report.xml          # QWeb invoice report customisation
│   ├── crm_inherit_view.xml        # CRM form XPath inheritance
│   └── stock_picking_views.xml     # Stock picking form/tree inheritance
│
├── security/
│   ├── res_groups.xml              # Estate Manager + Estate Read Only groups
│   ├── ir.model.access.csv         # Model-level CRUD permissions
│   └── crm_record_rule.xml         # Record rule: users see own CRM leads only
│
├── data/
│   ├── sequence.xml                # PROP0001 sequence (noupdate=1)
│   └── cron.xml                    # Scheduled action definitions
│
└── demo/
    └── demo.xml                    # Demo property record
```

---

## Installation

### Prerequisites

- Odoo 17.0 Community
- Python 3.10+
- PostgreSQL 14+

### Steps

```bash
# 1. Clone or copy the estate directory into your addons path
# addons_path in odoo.conf must include the parent directory of estate/

# 2. Install dependencies
pip install -r requirements.txt

# 3. Install the module
python setup/odoo -c odoo.conf -i estate --stop-after-init

# 4. To upgrade after code changes
python setup/odoo -c odoo.conf -u estate --stop-after-init
```

---

## Configuration

### System Parameters

The following keys can be set at **Settings → Technical → Parameters → System Parameters**:

| Key | Default | Description |
|---|---|---|
| `estate.auto_expire_enabled` | `True` | Enable/disable the daily property expiry cron |
| `estate.last_expire_cron_run` | *(set by cron)* | Timestamp of last successful expiry run |

### Enable Developer Mode

**Settings → Activate Developer Mode**
or append `?debug=1` to any URL.

---

## Modules Covered

| # | Module | Key Implementation |
|---|---|---|
| 4 | Security & Access | `res_groups.xml`, `ir.model.access.csv`, `crm_record_rule.xml` |
| 5 | Metadata Models | `ir.sequence` (PROP code), `ir.config_parameter` (cron flag) |
| 6 | Environment & Context | `with_context` in Cancel & Archive button |
| 7 | ORM Customisation | `_inherit`, `@api.depends`, `@api.onchange`, `@api.constrains` |
| 8 | XML Views & Inheritance | XPath on `res.users`, `crm.lead`, `stock.picking` |
| 9 | Core Business Modules | CRM, Sales, Inventory integrations |
| 10 | Automation & APIs | Cron jobs, JSON controller, QWeb report |
| 11 | Logging & Performance | `_logger` everywhere, `read_group()`, bulk `write()` |

---

## Ready-Made Tasks

### Task 1 — CRM Validation (`crm_inherit.py`)
- Added `source_reference` field to `crm.lead`
- Mandatory when lead stage `is_won = True`
- Validates `expected_revenue > 0`

### Task 2 — Sale Order Rule (`sale_order.py`)
- Overrides `action_confirm()`
- Raises `ValidationError` if `partner_id.vat` is empty

### Task 3 — Inventory Tracking (`sale_stock_inherit.py`)
- Adds `delivery_note_no` and `delivery_note` to `stock.picking`
- Shown in both form and tree views via XPath

### Task 4 — Record Rule (`crm_record_rule.xml`)
- `ir.rule` restricts CRM leads to the record creator only
- Domain: `[('create_uid', '=', user.id)]`

### Task 5 — Cron Job (`cron_job.py` + `estate_property.py`)
- `estate.cron`: daily bulk-update of CRM lead priorities
- `estate.property._cron_mark_expired_properties`: cancels expired properties
- Controlled by `ir.config_parameter` feature flag

### Task 6 — External API (`estate_api_data.py`)
- Fetches from `https://jsonplaceholder.typicode.com/posts`
- Stores first 10 posts in `estate.api.data` model
- Full error handling: `ConnectionError`, `Timeout`, `HTTPError`
- Trigger via: **Estate → API Data → Action → Fetch from External API**

---

## API Reference

### GET /api/properties

Returns all estate properties as JSON.

**Authentication:** Requires active Odoo user session (`auth='user'`)

**Method:** POST (Odoo JSON-RPC standard)

**Request:**
```json
{
    "jsonrpc": "2.0",
    "method": "call",
    "params": {}
}
```

**Response:**
```json
{
    "status": "success",
    "count": 3,
    "data": [
        {
            "name": "Sea View Villa",
            "expected_price": 5000000.0,
            "state": "new"
        }
    ]
}
```

---

## Cron Jobs

| Name | Model | Method | Schedule | Purpose |
|---|---|---|---|---|
| Mark Expired Properties | `estate.property` | `_cron_mark_expired_properties` | Daily | Cancels properties past expiry date |
| Set All CRM Leads to High Priority | `estate.cron` | `daily_cron_job` | Daily | Bulk-sets all CRM lead priority to 1 |

Run manually: **Settings → Technical → Automation → Scheduled Actions → Run Manually**

---

## Security

| Group | Access | Description |
|---|---|---|
| `estate.estate_admin` | Full CRUD | Estate Manager — full access |
| `base.group_user` | Full CRUD | All internal users |
| `estate.group_estate_readonly` | Read only | Can view own properties only |

---

## Dependencies

```python
depends = ['base', 'mail', 'crm', 'sale', 'stock', 'account']
```

| Module | Reason |
|---|---|
| `base` | Core Odoo models (`res.users`, `res.partner`) |
| `mail` | Chatter and activity tracking on properties |
| `crm` | CRM lead inheritance (Task 1, Task 4) |
| `sale` | Sale order inheritance (Task 2) |
| `stock` | Stock picking inheritance (Task 3) |
| `account` | Invoice QWeb report customisation |
