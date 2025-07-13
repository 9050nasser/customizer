// Copyright (c) 2024, Ahmed and contributors
// For license information, please see license.txt

frappe.query_reports["Daily Branch Report"] = {
	"filters": [  

		{
			"fieldname": "cost_center",
			"label": __("Cost Center"),
			"fieldtype": "Link",
			"options": "Cost Center"
		},
            
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_start()
		},
            
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.month_end()
		},
		
	]
};
