// Copyright (c) 2024, Ahmed and contributors
// For license information, please see license.txt

frappe.ui.form.on('Latency Deduction', {
    refresh: function(frm) {

        frm.add_custom_button(__('Get Employees'), function() {
            frm.trigger('fetch_employees');
        });
    },

    fetch_employees: function(frm) {

        if (!frm.doc.company || !frm.doc.start_date || !frm.doc.end_date) {
            frappe.msgprint(__('Please select a Company, Start Date, and End Date.'));
            return;
        }


        frappe.call({
            method: "customizer.customizer.doctype.latency_deduction.latency_deduction.get_employees",
            args: {
                company: frm.doc.company,
                start_date: frm.doc.start_date,
                end_date: frm.doc.end_date
            },
            callback: function(r) {
                if (r.message) {

                    frm.clear_table("latency_employee_details");
                    r.message.forEach(function(employee) {
                        let row = frm.add_child("latency_employee_details");
                        row.employee = employee.employee;
                        row.employee_name = employee.employee_name;
                        row.basic_salary = employee.basic_salary;
                        row.min_rate = employee.min_rate;
                        row.allow_late_by_min = employee.allow_late_by_min;
                        row.total_late = employee.total_late;
                        row.late_by_min = employee.late_by_min;
                        row.net_late = employee.net_late;
                        row.net_late_in_minutes = employee.net_late_in_minutes;
                        row.deductions_amount = employee.deductions_amount;
                    });


                    frm.set_value("number_of_employees", frm.doc.latency_employee_details.length);


                    frm.refresh_field("latency_employee_details");
                    frappe.msgprint(__('Employee records fetched successfully.'));
                } else {
                    frappe.msgprint(__('No records found for the selected criteria.'));

                    frm.set_value("number_of_employees", 0);
                }
            }
        });
    }
});

// Triggered whenever rows in the child table are added or removed
frappe.ui.form.on('Latency Employee Details', {
    latency_employee_details_add: function(frm) {
        // Update the Number of Employees field on adding a row
        update_number_of_employees(frm);
    },
    latency_employee_details_remove: function(frm) {
        // Update the Number of Employees field on removing a row
        update_number_of_employees(frm);
    },
    employee: function(frm) {
        // Also update on editing the employee field in child table
        update_number_of_employees(frm);
    }
});

// Function to calculate and update the Number of Employees field
function update_number_of_employees(frm) {
    let count = frm.doc.latency_employee_details.length || 0;
    frm.set_value("number_of_employees", count);
}

