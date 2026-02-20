{
    "name": "Estatess",
    "version": "1.0",
    "license":"LGPL-3",
    "depends":['base','mail','crm','sale','stock','account'],
    "application":True,
    'demo': ['demo/demo.xml',],
    "data":[
        "data/sequence.xml",
        "data/cron.xml",
        "security/res_groups.xml",
        "security/ir.model.access.csv",
        "security/crm_record_rule.xml",
        "views/estate_property_views.xml",
        "views/estate_menu.xml",
        "views/invoice_report.xml",
        "views/crm_inherit_view.xml",
        "views/stock_picking_views.xml",
    ]

}
