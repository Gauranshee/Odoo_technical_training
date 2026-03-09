# Estate Module — Code Walkthrough

This document explains every key concept implemented in the Estate module,
written for freshers to understand **what**, **why**, and **how**.

---

## 1. Model Definition (`estate_property.py`)

```python
class EstateProperty(models.Model):
    _name = 'estate.property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"
```

| Attribute | Why |
|---|---|
| `_name` | Defines the technical model name. Creates the DB table `estate_property`. |
| `_inherit = ['mail.thread', ...]` | Adds chatter (message log) and activity scheduling to the form view. |
| `_order = "id desc"` | Default sort: newest property first in all list views. |

---

## 2. Field Types Used

```python
state        = fields.Selection([...], required=True, copy=False, default='new')
name         = fields.Char(string='Title', required=True)
expected_price = fields.Float(string='Expected Price', required=True)
garden       = fields.Boolean(string='Garden')
garden_area  = fields.Integer(string='Garden Area (sqm)')
expiry_date  = fields.Date(string="Expiry Date")
description  = fields.Text(string='Description')

# Relational
property_type_id = fields.Many2one('estate.property.type')   # N records → 1 type
offer_ids        = fields.One2many('estate.property.offer', 'property_id')  # 1 → N
tag_ids          = fields.Many2many('estate.property.tag')   # N → N

# Computed
best_price   = fields.Float(compute='_compute_best_price')
total_area   = fields.Float(compute='_compute_total_area')
```

**Why `copy=False`?** Prevents the field value from being copied when duplicating a record.
**Why `readonly=True` on `seq_estate_property`?** System-generated codes must not be manually edited.

---

## 3. Compute Fields

```python
@api.depends("offer_ids.price")
def _compute_best_price(self):
    for record in self:
        record.best_price = max(record.offer_ids.mapped('price') or [0])
```

- `@api.depends`: tells Odoo when to re-run the compute — here, whenever any offer price changes.
- `mapped('price')`: returns a list of all offer prices without loading full ORM objects.
- `or [0]`: fallback so `max()` does not crash on an empty list.

---

## 4. Onchange

```python
@api.onchange('garden')
def _onchange_garden(self):
    for estate in self:
        if not estate.garden:
            estate.garden_area = 0
```

- `@api.onchange`: triggered in the UI when the user changes the `garden` checkbox.
- Automatically resets `garden_area` to 0 when garden is unchecked.
- Does NOT save to DB — it only updates the form before the user saves.

---

## 5. Constraints

### SQL Constraint (DB level)
```python
_sql_constraints = [
    ('check_expected_price', 'CHECK(expected_price > 0)',
     'Expected price must be positive.'),
]
```
- Enforced directly by PostgreSQL — cannot be bypassed by any Python code path.
- Fastest validation method; runs on every INSERT and UPDATE.

### Python Constraint (ORM level)
```python
@api.constrains('selling_price')
def _check_constraints(self):
    for estate in self:
        if estate.selling_price > 0 and \
           estate.selling_price < estate.expected_price * 0.9:
            raise ValidationError("Selling price must be at least 90%...")
```
- `@api.constrains`: runs after the record is saved but before the transaction commits.
- `selling_price > 0` guard: skip validation for new records where price is not set yet.

---

## 6. CRUD Override

```python
@api.model
def create(self, vals):
    vals['seq_estate_property'] = self.env['ir.sequence'].next_by_code('estate.code')
    return super(EstateProperty, self).create(vals)
```

- `@api.model`: method runs at model level, not on a specific record.
- `ir.sequence.next_by_code('estate.code')`: generates PROP0001, PROP0002, etc.
- Always call `super()` to preserve Odoo's default create behaviour.

```python
def unlink(self):
    for record in self:
        if record.state not in ('new', 'canceled'):
            raise UserError('Only New or Cancelled properties can be deleted.')
    return super().unlink()
```

- Prevents accidental deletion of active/sold properties.

---

## 7. Cron Job with ir.config_parameter

```python
def _cron_mark_expired_properties(self):
    auto_expire = self.env['ir.config_parameter'].sudo().get_param(
        'estate.auto_expire_enabled', default='True'
    )
    if auto_expire != 'True':
        return

    properties = self.search([
        ('expiry_date', '<', date.today()),
        ('state', 'not in', ['sold', 'canceled']),
    ])
    if properties:
        properties.write({'state': 'canceled'})

    self.env['ir.config_parameter'].sudo().set_param(
        'estate.last_expire_cron_run', str(date.today())
    )
```

- `ir.config_parameter`: key-value store in DB. View at Settings → Technical → System Parameters.
- `get_param()`: reads a value. `set_param()`: writes a value.
- `.sudo()`: runs without user permission restrictions (needed in cron context).
- `properties.write(...)`: **bulk update** — single SQL UPDATE for all matched records.

---

## 8. Model Inheritance

### Classical Inheritance (`_inherit` without `_name`)
```python
class CrmLead(models.Model):
    _inherit = 'crm.lead'   # No _name → extends existing table
    source_reference = fields.Char(string="Source Reference")
```
- Adds a new column to the existing `crm_lead` table.
- No new table created. Used in: `crm_inherit.py`, `sale_order.py`, `res_users.py`.

### Prototype Inheritance (`_inherit` with `_name`)
```python
class EstateProperty(models.Model):
    _name = 'estate.property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
```
- New table `estate_property` is created.
- Copies behaviour (methods/fields) from `mail.thread` without creating a relation.

---

## 9. XML View Inheritance (XPath)

```xml
<record id="view_users_form_inherit_estate" model="ir.ui.view">
    <field name="inherit_id" ref="base.view_users_form"/>
    <field name="arch" type="xml">
        <xpath expr="//notebook" position="inside">
            <page string="Properties">
                <field name="property_ids">...</field>
            </page>
        </xpath>
    </field>
</record>
```

- `inherit_id`: points to the existing view to extend.
- `xpath expr`: CSS-like selector to find the target element.
- `position="inside"`: inserts content inside the matched element.
- Other positions: `after`, `before`, `replace`, `attributes`.

---

## 10. Security Architecture

```
ir.model.access.csv         → Who can READ/WRITE/CREATE/DELETE a model
res_groups.xml              → Define user groups (Estate Manager, Read Only)
crm_record_rule.xml         → Row-level filter (users see only own records)
```

```
User → belongs to Group → Group has Model Access → User can CRUD the model
                        → Group has Record Rule  → User sees filtered rows only
```

**Difference:**
- **Access rights** (`ir.model.access`): controls if a user can access the model at all.
- **Record rules** (`ir.rule`): controls which specific rows a user can see/edit.

---

## 11. Performance Patterns

### read_group instead of len()

```python
# BAD — loads all offer records into memory just to count
rec.offer_count = len(rec.offer_ids)

# GOOD — single SQL COUNT(*) GROUP BY query, no records loaded
offer_data = self.env['estate.property.offer'].read_group(
    domain=[('property_type_id', 'in', self.ids)],
    fields=['property_type_id'],
    groupby=['property_type_id'],
)
```

### Bulk write instead of loop

```python
# BAD — N SQL UPDATE statements (one per record)
for rec in records:
    rec.write({'priority': '1'})

# GOOD — single SQL UPDATE for all records
records.write({'priority': '1'})
```

### mapped() for field extraction

```python
# BAD — Python loop to collect prices
prices = [offer.price for offer in self.offer_ids]

# GOOD — mapped() extracts values efficiently from the recordset
prices = self.offer_ids.mapped('price')
```

---

## 12. External API Integration

```python
response = requests.get(DUMMY_API_URL, timeout=10)
response.raise_for_status()   # raises HTTPError for 4xx/5xx
data = response.json()

old_records = self.search([])
old_records.unlink()           # clear stale data first

for post in data[:10]:
    self.create({...})
```

- `timeout=10`: always set a timeout to prevent server hangs.
- `raise_for_status()`: converts HTTP errors into exceptions.
- Clear-then-insert pattern: ensures data is always fresh.
- Limit to 10 records: prevents overloading the DB in demo context.

---

## 13. JSON API Controller

```python
@http.route('/api/properties', type='json', auth='user', methods=['POST'])
def get_properties(self):
    _logger.info("Called by user: %s", request.env.user.name)
    try:
        properties = request.env['estate.property'].search([])
        result = [{'name': r.name, ...} for r in properties]
        return {'status': 'success', 'data': result}
    except Exception as e:
        _logger.error("Failed: %s", str(e), exc_info=True)
        return {'status': 'error', 'message': str(e)}
```

- `type='json'`: Odoo handles JSON-RPC serialisation automatically.
- `auth='user'`: requires an authenticated session.
- `exc_info=True`: includes full Python traceback in server logs.

---

## 14. QWeb Report Inheritance

```xml
<template id="custom_invoice_report"
          inherit_id="account.report_invoice_document">
    <xpath expr="//t[@t-call='web.external_layout']" position="inside">
        <p>
            <strong>Custom Note:</strong>
            This invoice is generated from Estate System.
        </p>
    </xpath>
</template>
```

- `inherit_id`: extends the existing Odoo invoice PDF template.
- XPath targets the outer layout wrapper to inject content at the top.
- No original template code is copied or duplicated — upgrade-safe.

---

## 15. Logging Standards

```python
import logging
_logger = logging.getLogger(__name__)

_logger.info("Action started for record ID: %s", self.id)
_logger.warning("Unexpected state: %s", self.state)
_logger.error("Failed: %s", str(e), exc_info=True)
```

| Level | When to use |
|---|---|
| `info` | Normal flow: cron started, API called, records updated |
| `warning` | Unexpected but non-fatal: feature disabled, no records found |
| `error` | Failure: exception caught, operation could not complete |

- Always use `%s` formatting (not f-strings) — Python's logging evaluates lazily.
- `exc_info=True` on errors: prints the full traceback to server logs.
