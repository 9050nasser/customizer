# Copyright (c) 2024, Ahmed and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import flt
from datetime import datetime
from frappe.utils import nowdate, get_link_to_form
from frappe import _ as __
from frappe.utils import flt, cint 

class LatencyDeduction(Document):
    def on_submit(self):
        self.create_additional_salary()

    def create_additional_salary(self):
        if not self.latency_employee_details:
            frappe.throw("No employee records to process for salary deductions.")
        
        for row in self.latency_employee_details:

            if not row.deductions_amount or flt(row.deductions_amount) <= 0:
                continue
            

            existing_salary = frappe.db.exists(
                "Additional Salary",
                {
                    "employee": row.employee,
                    "salary_component": "Late Working Hours(تأخر في ساعات عمل)",
                    "payroll_date": self.posting_date
                }
            )
            
            if existing_salary:

                frappe.msgprint(f"Additional Salary already exists for employee {row.employee} for this date.")
                continue  


            additional_salary = frappe.new_doc("Additional Salary")
            additional_salary.employee = row.employee
            additional_salary.salary_component = "Late Working Hours(تأخر في ساعات عمل)"
            additional_salary.amount = flt(row.deductions_amount)
            additional_salary.payroll_date = self.posting_date  
            additional_salary.company = self.company
            additional_salary.overwrite_salary_structure_amount = 1
        

            additional_salary.insert()
            additional_salary.save()
            

            additional_salary_link = get_link_to_form('Additional Salary', additional_salary.name)
            frappe.msgprint(__('Additional Salary created successfully for {0}.').format(additional_salary_link))


@frappe.whitelist()
def get_employees(company, start_date, end_date):
    if not start_date or not end_date:
        frappe.throw("Start Date and End Date are required.")

    # Query attendance records
    attendance_records = frappe.db.sql("""
        SELECT 
            att.employee,
            att.employee_name,
            att.custom_basic_salary,
            att.custom_late_entry_hrs
        FROM `tabAttendance` AS att
        WHERE att.company = %s
          AND att.attendance_date BETWEEN %s AND %s
    """, (company, start_date, end_date), as_dict=True)

    processed_records = {}
    
    # Process each record to calculate total late minutes
    for record in attendance_records:
        employee = record["employee"]
        employee_name = record["employee_name"]
        custom_basic_salary = flt(record.get("custom_basic_salary", 0))
        late_entry_hrs = record.get("custom_late_entry_hrs", "00:00")
        late_minutes = time_to_minutes(late_entry_hrs)

        if employee not in processed_records:
            processed_records[employee] = {
                "employee": employee,
                "employee_name": employee_name,
                "custom_basic_salary": custom_basic_salary,
                "total_late_minutes": 0,
            }

        # Sum up late minutes
        processed_records[employee]["total_late_minutes"] += late_minutes

    results = []
    allow_late_by_min = 60  # Configurable constant for allowed lateness

    for employee, data in processed_records.items():
        basic_salary = data["custom_basic_salary"]
        total_late_minutes = data["total_late_minutes"]

        # Calculate per-minute rate
        min_rate = basic_salary / (30 * 8 * 60) if basic_salary else 0

        # Net late minutes after allowed lateness
        net_late_minutes = max(0, total_late_minutes - allow_late_by_min)

        # Deduction amount
        deduction_amount = net_late_minutes * min_rate

        # Convert minutes to HH:MM format for display
        total_late_hhmm = minutes_to_time(total_late_minutes)

        # Convert net late minutes to HH:MM format for display
        net_late_hhmm = minutes_to_time(net_late_minutes)

        # Add fields for late_by_min and net_late_in_minutes
        late_by_min = total_late_minutes  # Total late minutes
        net_late_in_minutes = str(net_late_minutes)  # Ensure it's a string for the Data field

        results.append({
            "employee": employee,
            "employee_name": data["employee_name"],
            "basic_salary": basic_salary,
            "min_rate": round(min_rate, 4),
            "allow_late_by_min": allow_late_by_min,
            "total_late": total_late_hhmm,
            "late_by_min": late_by_min,
            "net_late": net_late_hhmm,
            "net_late_in_minutes": net_late_in_minutes,  # Now a string value
            "deductions_amount": round(deduction_amount, 2),
        })

    return results


def time_to_minutes(time_str):
    """
    Convert time in HH:MM format to total minutes.
    """
    try:
        hours, minutes = map(int, time_str.split(":"))
        return hours * 60 + minutes
    except (ValueError, AttributeError):
        return 0  # Return 0 for invalid time strings


def minutes_to_time(total_minutes):
    """
    Convert total minutes to HH:MM format.
    """
    try:
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours:02}:{minutes:02}"  # Format as HH:MM
    except (ValueError, TypeError):
        return "00:00"


