// Copyright (c) 2024, Ahmed and contributors
// For license information, please see license.txt

frappe.ui.form.on('Overtime Request', {
    pay_on: function (frm) {
        if (frm.doc.pay_on === "Leave Day") {
            // Reset total salary to 0 when 'Leave Day' is selected
            frm.set_value('total_salary', 0);
            frm.set_value('rate_per_hour', 1); // Set default rate per hour
            calculate_per_day(frm); // Recalculate per day for leave day
        } else if (frm.doc.pay_on === "On Salary") {
            // Clear total salary when 'On Salary' is selected
            frm.set_value('total_salary', null);
            calculate_hourly_rate(frm); // Recalculate hourly rate
        } else {
            frm.set_value('total_salary', null); // Clear total salary if neither option is selected
        }
    },


    salary: calculate_hourly_rate,
    working_days: calculate_hourly_rate,
    total_working_hours: function (frm) {
        calculate_total_salary(frm); // Recalculate total salary when working hours change
        calculate_per_day(frm); // Recalculate per day
    },

    on_submit: function (frm) {
        frappe.call({
            method: 'customizer.customizer.employee_self_service.doctype.overtime_request.overtime_request_on_submit',
            args: { doc: frm.doc },
            callback: function (response) {
                if (response.message) {
                    frappe.msgprint(__('Action completed successfully.'));
                }
            }
        });
    }
});


// Child Table Events for Time Sheets
frappe.ui.form.on('Time Sheets', {
    hrs: function (frm) {
        calculate_total_working_hours(frm);
    },
    time_sheets_remove: function (frm) {
        calculate_total_working_hours(frm);
    }
});

// Calculation Functions
function calculate_hourly_rate(frm) {
    if (frm.doc.salary) {
        const working_days = frm.doc.working_days || 30;
        const hourly_rate = (frm.doc.salary / working_days / 8) * 1.5;
        frm.set_value('hourly_rate', hourly_rate);
    }
}

function calculate_total_salary(frm) {
    const total_working_hours = frm.doc.total_working_hours || 0;
    const hourly_rate = frm.doc.hourly_rate || 0;
    const total_salary = total_working_hours * hourly_rate;
    frm.set_value('total_salary', total_salary);
}

function calculate_per_day(frm) {
    const total_working_hours = frm.doc.total_working_hours || 0;
    const rate_per_hour = frm.doc.rate_per_hour || 1;
    const per_day = (total_working_hours / 8) * rate_per_hour;
    frm.set_value('per_day', per_day);
}

function calculate_total_working_hours(frm) {
    let total_hrs = 0;
    (frm.doc.time_sheets || []).forEach(row => {
        total_hrs += flt(row.hrs);
    });
    frm.set_value('total_working_hours', total_hrs);
    calculate_total_salary(frm);
    calculate_per_day(frm);
}


