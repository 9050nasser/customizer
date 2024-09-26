// Copyright (c) 2016, Ahmed and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Branch Sales Report"] = {
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
		{
			"fieldname":"from_time",
			"label": __("From Time"),
			"fieldtype": "Time"

		},
		{
			"fieldname":"to_time",
			"label": __("To Time"),
			"fieldtype": "Time"

		},
	]
};
