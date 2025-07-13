// Copyright (c) 2025, Ahmed and contributors
// For license information, please see license.txt

frappe.query_reports["Branch Sales Report Based On Day of Month"] = {
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
