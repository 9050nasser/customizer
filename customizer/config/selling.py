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
					"name": "POS Closing Voucher",
					"doctype": "POS Closing Voucher",
					"onboard": 1,
				},
				{
					"type": "report",
					"is_query_report": True,
					"name": "Cash Custody",
					"doctype": "POS Closing Voucher",
					"onboard": 1,
				},
			]
		},
		
	]
