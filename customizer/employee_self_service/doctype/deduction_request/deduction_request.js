// Copyright (c) 2024, Ahmed and contributors
// For license information, please see license.txt

frappe.ui.form.on("Deduction Request", {
	refresh(frm) {

 	},
 });


frappe.ui.form.on('Deduction Timesheet', {
    description: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        append_to_note(frm, row.description);
    }
});

function append_to_note(frm, description) {
   
    let current_note = frm.doc.note || ""; 
    let updated_note = current_note + (current_note ? "\n" : "") + description; 
    frm.set_value('note', updated_note); 
}
