from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Key Reports"),
			"icon": "fa fa-table",
			"items": [
				{
					"type": "report",
					"is_query_report": True,
					"name": "Item Expired",
					"doctype": "Stock Ledger Entry",
					"onboard": 1,
				},
			]
		},
		{
            "label": _("Stock Transactions"),
            "items": [
				{
					"type": "doctype",
					"name": "Material Request Planing",
					"onboard": 1,
					"dependencies": ["Item"],
				},
        ]
		
	}
]
