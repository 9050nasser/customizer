// Copyright (c) 2020, Sa Qanawat and contributors
// For license information, please see license.txt

frappe.ui.form.on('Return From Leave', {
	refresh: function(frm) {
		if (frm.doc.docstatus === 1 && !frm.doc.attendance_deduction){
			frm.add_custom_button(__("make_attendance_deduction"), function() {
				frappe.call({
				method: "make_attendance_deduction",
				freeze: true,
				doc: frm.doc,
				callback: function (r) {

					frm.refresh();

				}
				});
			});
		}

	},
	return_date: function(frm){
		let absent_days = frappe.datetime.get_diff(frm.doc.return_date, frm.doc.to_date)-1
		if (absent_days < 0){
			frappe.throw(__("Return Date can't be less than or equal To Date"));
		}
		if (frappe.datetime.str_to_obj(frm.doc.return_date).getMonth() !== frappe.datetime.str_to_obj(frm.doc.to_date).getMonth()){
			frm.set_value("absent_days", frappe.datetime.str_to_obj(frm.doc.return_date).getDate()-1);
		}
		else{
			console.log(absent_days)
			frm.set_value("absent_days", absent_days);
		}
	}
});
