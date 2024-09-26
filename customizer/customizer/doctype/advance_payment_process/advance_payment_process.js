// Copyright (c) 2021, Ahmed and contributors
// For license information, please see license.txt
cur_frm.add_fetch("company", "default_employee_advance_account", "advance_payment_account");
frappe.ui.form.on('Advance Payment Process', {
	
	setup: function(frm) {
		//~ frm.add_fetch("company", "default_employee_advance_account", "advance_payment_account");
		frm.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Company",
					filters: { name: frm.doc.company },
					fieldname: "default_employee_advance_account",
				},
				callback: function(r, rt) {
					if(r.message) {
						frm.set_value("advance_payment_account", r.message.default_employee_advance_account);
					}
				}
			});
	}

});

frappe.ui.form.on('Advance Payment Process Details', {
	employee: (frm, cdt, cdn) => {
		//~ let row = frm.selected_doc;
		let d = locals[cdt][cdn];
		
		frappe.call({
			method: 'get_employee_advance_balance',
			doc: frm.doc,
			args:{
				employee:d.employee
			},
			callback: function(r) {
				if (r.message) {
					console.log(r.message)
					frappe.model.set_value(cdt, cdn, "current_value", r.message);
				}
			}
		});
	},

});
