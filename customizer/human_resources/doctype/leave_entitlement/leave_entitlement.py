# -*- coding: utf-8 -*-
# Copyright (c) 2020, Sa Qanawat and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, \
    comma_or, get_fullname, add_years, add_months, add_days, nowdate , comma_and, get_first_day, get_last_day
from frappe.model.document import Document

class LeaveEntitlement(Document):

    def validate(self):
        if self.employee_ticket_price > 0:
            self.get_salary()
            self.get_current_month_working_days()
            self.update_salary_structure_status()
    
    def get_salary(self):
        if self.total_leave_days>=30:
            salary_amount = 0

            salary_slip_name = frappe.db.sql("select name from `tabSalary Slip` where employee='{0}' order by creation desc limit 1".format(self.employee))
            if salary_slip_name:
                doc = frappe.get_doc('Salary Slip', salary_slip_name[0][0])

                for earning in doc.earnings:
                    if earning.salary_component =='Basic':
                        salary_amount = earning.amount+(earning.amount/4)

            else:
                doc = frappe.new_doc("Salary Slip")
                doc.payroll_frequency= "Monthly"
                doc.start_date=get_first_day(getdate(nowdate()))
                doc.end_date=get_last_day(getdate(nowdate()))
                doc.employee= str(self.employee)
                doc.posting_date= nowdate()
                doc.insert(ignore_permissions=True)


                if doc.name:
                    for earning in doc.earnings:
                        if earning.salary_component =='Basic':
                            salary_amount = earning.amount+(earning.amount/4)

                    doc.delete()

            self.month_salary = round(salary_amount)
            return round(salary_amount)

    def get_current_month_working_days(self):
        if self.total_leave_days>=30 and getdate(self.from_date).day-1!=0:
            self.current_month_working_days = (self.get_salary()/30)*(getdate(self.from_date).day-1)

    def update_salary_structure_status(self):
        ss_doc = frappe.get_doc("Salary Structure", {"employee": self.employee})
        ss_doc.db_set("is_active", "No")

    # def get_existing_leaves(self):
    #   existing_leaves = 1

    #     leave_allocation_records = get_leave_allocation_records(nowdate(), self.employee, "Annual Leave - اجازة اعتيادية")
    #     if leave_allocation_records:
    #         from_date = leave_allocation_records[doc.employee]["Annual Leave - اجازة اعتيادية"].from_date
    #         to_date = leave_allocation_records[doc.employee]["Annual Leave - اجازة اعتيادية"].to_date

    #       existing_leaves = frappe.db.sql(""" select count(name) from `tabLeave Application` where employee='{0}' and 
    #             nationality!='Saudi' and leave_type='Annual Leave - اجازة اعتيادية' and total_leave_days >=15 and 
    #             to_date between '{1}' and '{2}' and docstatus=1 """.format(self.employee, from_date, to_date))[0][0]
    #       return existing_leaves

