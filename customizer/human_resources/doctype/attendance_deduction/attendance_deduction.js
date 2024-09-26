// Copyright (c) 2019, Ahmed and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance Deduction', {
	setup: function (frm) {

		frm.set_query("employee", function () {
			return {
				filters: {
					company: frm.doc.company,
					status: 'Active',
				}
			};
		});
	},
	type: function (frm) {
		if(cur_frm.doc.type=='Penalty'){
			frm.set_value("check_transportation", 1);
			frm.set_value("check_basic_salary", 1);
			frm.set_value("check_housing", 1);
			frm.set_value("check_cola", 1);
			frm.set_value("check_gosi", 1);
		}else{
			frm.set_value("check_transportation", 1);
			frm.set_value("check_basic_salary", 1);
			frm.set_value("check_housing", null);
			frm.set_value("check_cola", null);
			frm.set_value("check_gosi", null);
		}
	},
	refresh: function (frm) {
		validate_checkboxes(frm);
	},
	check_transportation: function (frm) {
		validate_checkboxes(frm)
	},
	check_basic_salary: function (frm) {
		validate_checkboxes(frm)
	},
	check_housing: function (frm) {
		validate_checkboxes(frm)
	},
	check_cola: function (frm) {
		validate_checkboxes(frm)
	},
	check_gosi: function (frm) {
		validate_checkboxes(frm)
	},
});

function validate_checkboxes(frm) {
	if ((frm.doc.check_transportation === 0 && frm.doc.check_basic_salary === 0
			&& frm.doc.check_housing === 0 && frm.doc.check_cola === 0
			&& frm.doc.check_gosi === 0) 
		|| (!frm.doc.check_transportation && !frm.doc.check_basic_salary
			&& !frm.doc.check_housing && !frm.doc.check_cola
			&& !frm.doc.check_gosi) ) {

		frm.set_value("check_transportation", null);
		frm.set_value("check_basic_salary", null);
		frm.set_value("check_housing", null);
		frm.set_value("check_cola", null);
		frm.set_value("check_gosi", null);

		frm.set_df_property("check_transportation", "reqd", true);
		frm.set_df_property("check_basic_salary", "reqd", true);
		frm.set_df_property("check_housing", "reqd", true);
		frm.set_df_property("check_cola", "reqd", true);
		frm.set_df_property("check_gosi", "reqd", true);
	} else {
		frm.set_df_property("check_transportation", "reqd", false);
		frm.set_df_property("check_basic_salary", "reqd", false);
		frm.set_df_property("check_housing", "reqd", false);
		frm.set_df_property("check_cola", "reqd", false);
		frm.set_df_property("check_gosi", "reqd", false);
	}
}