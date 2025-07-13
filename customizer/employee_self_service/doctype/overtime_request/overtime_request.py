# Copyright (c) 2024, Ahmed and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, get_link_to_form
from frappe.utils import getdate, today, formatdate
from frappe import _ as __
from frappe import _

class OvertimeRequest(Document):
    def before_insert(self):
        if not self.working_days:
            self.working_days = 30
            
        #current_date = getdate(today())
        
        # Check if it's after the 25th of the current month
        #if current_date.day > 25:
       #     frappe.throw(_("Overtime requests cannot be created after the 25th of the month."))
        
        # Ensure posting date is within 1st to 25th of the current month
      #  if self.posting_date:
       #     posting_date = getdate(self.posting_date)
        #    if posting_date.month == current_date.month and posting_date.day > 25:
         #       frappe.throw(_("Overtime requests cannot be created after the 25th of the month."))

    def on_submit(self):
        overtime_request_on_submit(self)
        
    def validate(self):
        self.update_dates_based_on_pay_on()


    def update_dates_based_on_pay_on(self):
        if self.pay_on:
            current_date = getdate()

            if self.pay_on == 'On Salary':
                # Set from_date and to_date to today's date
                self.from_date = current_date
                self.to_date = current_date
                frappe.logger().info(f"From Date and To Date Set to Today's Date: {current_date}")

            elif self.pay_on == 'Leave Day':
                if self.date_of_joining and self.employee_type:
                    joining_date = getdate(self.date_of_joining)
                    current_year = current_date.year

                    # Calculate from_date based on the joining date and the current year
                    from_date = joining_date.replace(year=current_year)

                    # Calculate to_date based on employee type
                    if self.employee_type == 'Labor':
                        to_date = from_date.replace(year=from_date.year + 2)
                    elif self.employee_type == 'Employee':
                        to_date = from_date.replace(year=from_date.year + 1)
                    else:
                        to_date = None

                    self.from_date = from_date
                    self.to_date = to_date

                    frappe.logger().info(f"Calculated From Date: {formatdate(from_date)}")
                    frappe.logger().info(f"Calculated To Date: {formatdate(to_date)}")
                else:
                    frappe.logger().warning("Required fields missing: Date of Joining or Employee Type")
            else:
                # Clear from_date and to_date
                self.from_date = None
                self.to_date = None


@frappe.whitelist()
def overtime_request_on_submit(doc):
    """Handle on-submit actions for Overtime Request."""
    if doc.get("pay_on") == "On Salary" and doc.get("total_salary") > 0:
        create_additional_salary(doc)
    elif doc.get("pay_on") == "Leave Day":
        create_leave_allocation(doc)

def create_additional_salary(doc):
    """Create an Additional Salary document."""
    additional_salary = frappe.get_doc({
        'doctype': 'Additional Salary',
        'employee': doc.employee,
        'amount': doc.total_salary,
        'payroll_date': doc.posting_date or nowdate(),
        'salary_component': 'Extra work(العمل الإضافي)',
        'custom_total_working_hours': doc.total_working_hours,
        'overtime_request': doc.name
        
    })
    additional_salary.insert(ignore_permissions=True)

    additional_salary_link = get_link_to_form('Additional Salary', additional_salary.name)
    frappe.msgprint(__('Additional Salary created successfully: {0}').format(additional_salary_link))

def create_leave_allocation(doc):
    """Create a Leave Allocation document."""
    leave_allocation = frappe.get_doc({
        'doctype': 'Leave Allocation',
        'employee': doc.employee,
        'leave_type': 'Compensatory Off (تعويض اوفر تايم)',
        'from_date': doc.from_date,
        'to_date': doc.to_date,
        'posting_date': doc.posting_date,
        'new_leaves_allocated': doc.per_day,
        'carry_forward': 1,
        'description': doc.note
    })
    leave_allocation.insert(ignore_permissions=True)

    leave_allocation_link = get_link_to_form('Leave Allocation', leave_allocation.name)
    frappe.msgprint(__('Leave Allocation created successfully: {0}').format(leave_allocation_link))





