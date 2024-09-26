// Copyright (c) 2020, Ahmed and contributors
// For license information, please see license.txt

frappe.ui.form.on('Reset Stock', {
	onload: function(frm) {
		frm.add_fetch("item_code", "item_name", "item_name");

		// end of life
		frm.set_query("item_code", "items", function(doc, cdt, cdn) {
			return {
				query: "erpnext.controllers.queries.item_query",
				filters:{
					"is_stock_item": 1
				}
			}
		});

		if (!frm.doc.expense_account) {
			frm.trigger("set_expense_account");
		}
			
		frm.set_query( "sub_stock_reconciliation","sub_stock_reconciliation_details", function() {
			
			return {
				filters: [
					['warehouse', '=', frm.doc.warehouse],
					['posting_date', '>=', frm.doc.from_date],
					['posting_date', '<=', frm.doc.to_date]
				]
			};
		});
	
	},

	refresh: function(frm) {
		if(frm.doc.docstatus < 1) {
			frm.add_custom_button(__("Fetch Items from Warehouse"), function() {
				frm.events.get_items(frm);
			});
		}

		if(frm.doc.company) {
			frm.trigger("toggle_display_account_head");
		}
	},
	review_stock_reconciliation: function(frm) {
		if (frm.doc.warehouse && frm.doc.posting_date && frm.doc.review_stock_reconciliation && !frm.doc.items)
		frappe.call({
					method:"customizer.customizer.doctype.reset_stock.reset_stock.get_items",
					freeze: true,
					freeze_message: __('Retriving Items ...'),
					args: {
						warehouse: frm.doc.warehouse,
						posting_date: frm.doc.posting_date,
						posting_time: frm.doc.posting_time,
						review_stock_reconciliation: frm.doc.review_stock_reconciliation,
						company:frm.doc.company
					},
					callback: function(r) {
						var items = [];
						frm.clear_table("items");
						for(var i=0; i< r.message.length; i++) {
							var d = frm.add_child("items");
							$.extend(d, r.message[i]);
							if(!d.qty) d.qty = null;
							if(!d.valuation_rate) d.valuation_rate = null;
						}
						frm.refresh_field("items");
					}
		});
	},
	get_items: function(frm) {
		if (frm.doc.warehouse && frm.doc.posting_date && frm.doc.review_stock_reconciliation)
				frappe.call({
					method:"customizer.customizer.doctype.reset_stock.reset_stock.get_items",
					freeze: true,
					freeze_message: __('Retriving Items ...'),
					args: {
						warehouse: frm.doc.warehouse,
						posting_date: frm.doc.posting_date,
						posting_time: frm.doc.posting_time,
						review_stock_reconciliation: frm.doc.review_stock_reconciliation,
						company:frm.doc.company
					},
					callback: function(r) {
						var items = [];
						frm.clear_table("items");
						for(var i=0; i< r.message.length; i++) {
							var d = frm.add_child("items");
							$.extend(d, r.message[i]);
							if(!d.qty) d.qty = null;
							if(!d.valuation_rate) d.valuation_rate = null;
						}
						frm.refresh_field("items");
					}
				});
	},
});
