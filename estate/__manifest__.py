{
    "name": "Estate",
    "version": "1.0",
    "license": "LGPL-3",
    "summary": "Real Estate Property Management",
    "author": "Gauranshee",
    "application": True,
    "depends": ["base", "mail", "crm", "sale", "stock", "account"],
    "demo": [
        "demo/demo.xml",
    ],
    "data": [
        # Sequences and cron must load before views that reference them
        "data/sequence.xml",
        "data/cron.xml",
        # Security: groups first, then access rules, then record rules
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "security/crm_record_rule.xml",
        # Views
        "views/estate_property_views.xml",
        "views/estate_api_views.xml",
        "views/estate_menu.xml",
        "views/invoice_report.xml",
        "views/crm_inherit_view.xml",
        "views/stock_picking_views.xml",
    ],
}
