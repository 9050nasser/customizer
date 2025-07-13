// Copyright (c) 2016, Ahmed and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Item-wise Price List Rate with tags"] = {
	"filters": [
		{
			"fieldname":"price_list",
			"label": __("Price List"),
			"fieldtype": "Link",
			"options": "Price List"
		},
		{
			"fieldname":"tag",
			"label": __("Tag"),
			"fieldtype": "Link",
			"options": "Tag"
		},
		{
			"fieldname":"warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse"
		},
		{
			"fieldname": "item_code",
			"label": __("Item"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Item",
			"get_query": function() {
				return {
					query: "erpnext.controllers.queries.item_query",
				};
			}
		},
		{
			"fieldname": "item_group",
			"label": __("Item Group"),
			"fieldtype": "Link",
			"width": "80",
			"options": "Item Group"
		},
	]
};
