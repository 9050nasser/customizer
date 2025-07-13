# Copyright (c) 2024, Ahmed and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import nowdate, get_link_to_form
from frappe import _ as __


class DeductionRequest(Document):
    def before_insert(self):
        if not self.working_days:
            self.working_days = 30  

    def on_update(self):
        self.calculate_total_working_currency()

    def on_submit(self):
        self.create_additional_salary()  

    def calculate_total_working_currency(self):
        total_currency = 0

        if self.deduction_timesheet:
            for row in self.deduction_timesheet:
                total_currency += row.currency  

        self.total_working_currency = total_currency

    def create_additional_salary(self):
        """Create an Additional Salary document."""
        if self.total_working_currency > 0:
            additional_salary = frappe.get_doc({
                'doctype': 'Additional Salary',
                'employee': self.employee,
                'amount': self.total_working_currency,
                'payroll_date': self.posting_date or nowdate(),
                'salary_component': 'Penalties(جزاءات اخرى)',
                'overtime_request': self.name
            })
            additional_salary.insert(ignore_permissions=True)
            additional_salary_link = get_link_to_form('Additional Salary', additional_salary.name)
            frappe.msgprint(__('Additional Salary created successfully: {0}').format(additional_salary_link))


