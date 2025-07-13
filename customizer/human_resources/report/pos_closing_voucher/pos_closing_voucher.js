// Copyright (c) 2016, Ahmed and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["POS Closing Voucher"] = {
	"filters": [
		{
			"fieldname":"pos_profile",
			"label": __("POS Profile"),
			"fieldtype": "Link",
			"options": "POS Profile"
		},
		{
			"fieldname":"cashier",
			"label": __("Cashier"),
			"fieldtype": "Link",
			"options": "User"
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
		}
	]
};
