// Copyright (c) 2016, Ahmed and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales Report"] = {
    "filters": [
        {
            "fieldname": "cost_center",
            "label": __("Cost Center"),
            "fieldtype": "Link",
            "options": "Cost Center"
        },
        {
            "fieldname":"from_date",
            "label": __("From Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1 ,
            "on_change": function() {
                calculateTimeRelatedFilters();
            }
        },
        {
            "fieldname": "to_date",
            "label": __("To Date"),
            "fieldtype": "Date",
            "default": frappe.datetime.get_today(),
            "reqd": 1,
            "on_change": function() {
                calculateTimeRelatedFilters();
            }
        },
        {
            "fieldname": "working_day_based_on_the_calendar",
            "label": __("Working Day Based on the Calendar"),
            "fieldtype": "Int"
        },
        {
            "fieldname": "work_day_balance",
            "label": __("Work Day Balance"),
            "fieldtype": "Float"
        },
        {
            "fieldname": "time_gone",
            "label": __("Time Gone"),
            "fieldtype": "Int"
        },
        {
            "fieldname": "time_gone_percentage",
            "label": __("Time Gone Percentage"),
            "fieldtype": "Data"
        }
    ]
};

function calculateTimeRelatedFilters() {
    var filters = frappe.query_report.get_filter_values();
    var from_date = frappe.datetime.str_to_obj(filters.from_date);
    var to_date = frappe.datetime.str_to_obj(filters.to_date);
    
    // Calculate working day based on calendar (total days in the month)
    var working_day_based_on_calendar = calculateWorkingDayBasedOnCalendar(from_date);

    // Calculate work day balance (days remaining in the month)
    var work_day_balance = calculateWorkDayBalance(to_date);

    // Calculate time gone (days passed in the month)
    var time_gone = working_day_based_on_calendar - work_day_balance;

    // Calculate time gone percentage
    var time_gone_percentage = (time_gone / working_day_based_on_calendar) * 100;

    // Update filter values
    frappe.query_report.set_filter_value("working_day_based_on_the_calendar", working_day_based_on_calendar.toString());
    frappe.query_report.set_filter_value("work_day_balance", work_day_balance.toString());
    frappe.query_report.set_filter_value("time_gone", time_gone.toString());
    frappe.query_report.set_filter_value("time_gone_percentage", time_gone_percentage.toFixed(2).toString() + "%");
}

function calculateWorkingDayBasedOnCalendar(from_date) {
    var total_days_in_month = new Date(from_date.getFullYear(), from_date.getMonth() + 1, 0).getDate();
    return total_days_in_month;
}

function calculateWorkDayBalance(to_date) {
    var today = new Date();
    var total_days_in_month = new Date(today.getFullYear(), today.getMonth() + 1, 0).getDate();
    var days_remaining = total_days_in_month - to_date.getDate();
    return days_remaining;
}

