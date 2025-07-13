from __future__ import unicode_literals
from frappe import _

def get_data():
    return [

        {
            "label": _("Payroll"),
            "items": [
                {
                    "type": "doctype",
                    "name": "Attendance Deduction"
                },
                {
                    "type": "doctype",
                    "name": "End of Service Award"
                },
                {
                    "type": "report",
                    "is_query_report": True,
                    "name": "Salary Details",
                    "doctype": "Salary Slip"
                },
                
            ]
        },
        {
            "label": _("Employee"),
            "items":[
                {
                    "type": "doctype",
                    "name": "Employee Resignation"
                },
                {
                    "type": "report",
                    "is_query_report": True,
                    "name": "Employee details",
                    "doctype": "Employee"
                },

            ]
        }
    ]