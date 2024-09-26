from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
            "label": _("Retail Operations"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Sales Invoice",
                    "label": _("Sales Invoice"),
                    "onboard": 1,
                },
            ]
        }
	]
