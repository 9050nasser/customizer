# -*- coding: utf-8 -*-
# Copyright (c) 2019, Mawrederp  and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import flt, cstr, cint, date_diff, getdate, get_first_day, get_last_day
from customizer.utils import make_salary_slip
from erpnext.hr.doctype.employee.employee import get_holiday_list_for_employee

class AttendanceDeduction(Document):

    def validate(self):
        self.get_working_days()
        self.calculate_amount()
        self.validate_multiple()

    def validate_multiple(self):
        if self.multiple <= 0 and self.ed_type == "Salary Component":
            frappe.throw(_("multiple should be greater than 0"))

    def before_submit(self):
        self.make_additional_salary()


    def make_additional_salary(self):
        if self.calculated_amount > 0:
            as_doc = frappe.new_doc("Additional Salary")
            as_doc.update(dict(
                payroll_date = self.payroll_date,
                employee = self.employee,
                salary_component = "Absence" if self.type == "Attendance" else "Penalty",
                amount = self.calculated_amount,

                ))
            as_doc.insert()
            self.additional_salary = as_doc.name
            as_doc.submit()
            msg = """Additional Salary has been created: <b><a href="#Form/Additional Salary/{0}">{0}</a></b>""".format(as_doc.name)
            frappe.msgprint(_(msg))
        else:
            frappe.throw(_("The calculated amount must be greater than 0"))

    def on_cancel(self):
        if self.additional_salary:
            as_doc = frappe.get_doc("Additional Salary", {"name":self.additional_salary})
            if as_doc and as_doc.docstatus == 1:
                as_doc.cancel()

    def on_trash(self):
        if self.additional_salary:
            as_doc = frappe.get_doc("Additional Salary", {"name":self.additional_salary})
            if as_doc and as_doc.docstatus == 2:
                frappe.delete_doc("Additional Salary", self.additional_salary)

    def calculate_amount(self):
        if self.ed_type == 'Amount':
            self.calculated_amount = self.amount
        else:
            salary_doc = self.get_salary_slip()
            if self.ed_type == "Salary Component":
                if self.main_salary_component in [e.salary_component for e in salary_doc.earnings]:
                    for e in salary_doc.earnings:
                        if self.main_salary_component == e.salary_component:
                            self.calculated_amount = e.default_amount * self.multiple
                            break
                elif self.main_salary_component in [d.salary_component for d in salary_doc.deductions]:
                    for d in salary_doc.deductions:
                        if self.main_salary_component == d.salary_component:
                            self.calculated_amount = d.default_amount * self.multiple
                            break
                else:
                    frappe.throw(_("this employee has no such main component in salary structure"))


            elif salary_doc.earnings:
                if self.ed_type == 'Days': 
                    self.calculated_amount = self.get_total_amount(salary_doc.earnings, days = self.days)
                elif self.ed_type == 'Hours':
                    self.calculated_amount = self.get_total_amount(salary_doc.earnings, hours = self.hours)

                        # (self.calculated_amount = e.amount for e in salary_doc.earnings if self.main_salary_component == e.salary_component)

            else:
                frappe.throw(_("No earnings components found for this employee"))

    def get_total_amount(self,earnings, days = 0, hours = 0):
        total_rate = 0
        day_working_hours = 8 if hours > 0 else 1

        for earning in earnings:
            if earning.salary_component in ['Basic', 'Housing', 'Transportation']:
                total_rate += flt(earning.default_amount/(self.working_days*day_working_hours))
        return days*total_rate if days > 0 else hours*total_rate

    def get_salary_slip(self):
        employee_salary_structure = frappe.db.sql("""select salary_structure, base from `tabSalary Structure Assignment`
            where employee='{0}' and docstatus = 1 order by creation desc limit 1""".format(self.employee), as_dict=True)
        if employee_salary_structure and employee_salary_structure[0]:
            salary_slip_doc = make_salary_slip(employee_salary_structure[0].salary_structure, employee = self.employee)
            return salary_slip_doc
        else:
            frappe.throw(_("No Salary structure Assignment Found For This Employee"))

    def get_working_days(self):
        month_first_day = get_first_day(getdate(self.payroll_date))
        month_last_day = get_last_day(getdate(self.payroll_date))
        holidays = self.get_holidays_for_employee(month_first_day, month_last_day)
        working_days = date_diff(month_last_day, month_first_day) + 1
        if not cint(frappe.db.get_value("HR Settings", None, "include_holidays_in_total_working_days")):
            working_days -= len(holidays)
            if working_days < 0:
                frappe.throw(_("There are more holidays than working days this month."))
        self.working_days = working_days

    def get_holidays_for_employee(self, start_date, end_date):
        holiday_list = get_holiday_list_for_employee(self.employee)
        holidays = frappe.db.sql_list('''select holiday_date from `tabHoliday`
            where
                parent=%(holiday_list)s
                and holiday_date >= %(start_date)s
                and holiday_date <= %(end_date)s''', {
                    "holiday_list": holiday_list,
                    "start_date": start_date,
                    "end_date": end_date
                })

        holidays = [cstr(i) for i in holidays]

        return holidays