// Copyright (c) 2023, Ahmed and contributors
// For license information, please see license.txt

frappe.ui.form.on('Free Items', {
	validate: function(frm) {
		var current_date = frappe.datetime.nowdate();
		var to_date = frm.doc.to_date;

		if (to_date >= current_date) {
		  frm.set_df_property('enabled', 'read_only', 1);
		  frm.set_value('enabled', 1);
		  frm.set_df_property('is_free_items', 'read_only', 1);
		  frm.set_value('is_free_items', 1);
		  frm.set_df_property('disabled', 'read_only', 0);
		  frm.set_value('disabled', 0);
		} else {
		  frm.set_df_property('enabled', 'read_only', 0);
		  frm.set_value('enabled', 0);
		  frm.set_df_property('is_free_items', 'read_only', 0);
		  frm.set_value('is_free_items', 0);
		  frm.set_df_property('disabled', 'read_only', 1);
		  frm.set_value('disabled', 1);
		}
	 }
});

