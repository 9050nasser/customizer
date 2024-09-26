# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe import msgprint, _
from customizer.human_resources.doctype.end_of_service_award.end_of_service_award import get_award
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, \
    comma_or, get_fullname, add_years, add_months, add_days, nowdate, get_first_day, get_last_day
import math
import datetime

class EmployeeResignation(Document):

    def on_submit(self):
        emp = frappe.get_doc("Employee",self.employee)
        emp.status ="Left"
        # emp.employment_status = "Resignation" if self.termination_type == "استقالة الموظف" else "Termination"
        emp.relieving_date =self.last_working_date
        emp.save(ignore_permissions=True)

        total_leave_balance = frappe.db.sql("select total_leaves_allocated,from_date,to_date,name from `tabLeave Allocation` where employee='{0}' and leave_type='Annual Leave - اجازة اعتيادية' and docstatus=1 and database()='d671f24654dde3bf' order by creation desc limit 1".format(self.employee))
        leave_balance = 0
        if total_leave_balance:
            leave_days = frappe.db.sql("select sum(total_leave_days) from `tabLeave Application` where employee='{0}' and database()='d671f24654dde3bf' and posting_date between '{1}' and '{2}'".format(self.employee,total_leave_balance[0][1],total_leave_balance[0][2]))[0][0]
            if not leave_days:
                leave_days = 0
            leave_balance =  flt(total_leave_balance[0][0])-flt(leave_days)

        salary = self.get_salary()
        employment_type = self.employment_type if self.employment_type else "Full Time"
        award_info = get_award(self.date_of_joining, self.last_working_date, salary,self.termination_type, employment_type)


        month_worked_days = datetime.datetime.strptime(self.last_working_date, '%Y-%m-%d')

        eos_award = frappe.new_doc("End of Service Award")
        eos_award.employee = self.employee
        eos_award.end_date = self.last_working_date
        eos_award.salary = salary
        eos_award.reason= self.termination_type
        eos_award.days = award_info['days']
        eos_award.months = award_info['months']
        eos_award.years = award_info['years']
        eos_award.award = award_info['award']

        eos_award.days_number = int(month_worked_days.day)
        eos_award.day_value = salary/30
        eos_award.total_month_salary = eos_award.days_number*eos_award.day_value

        eos_award.leave_number = leave_balance
        eos_award.leave_cost = salary/30
        eos_award.leave_total_cost = eos_award.leave_number*eos_award.leave_cost
        
        if self.notice_month:
            salary_slip_name = frappe.db.sql("select name from `tabSalary Slip` where employee='{0}' order by creation desc limit 1".format(self.employee))
            if salary_slip_name:
                doc = frappe.get_doc('Salary Slip', salary_slip_name[0][0])

                for earning in doc.earnings:
                    eos_award.append("end_of_service_award_adjustment",{
                        'adjustment': earning.amount,
                        'adjustment_type': 'Increment',
                        'reason': earning.salary_component
                    })

                for deduction in doc.deductions:
                    eos_award.append("end_of_service_award_adjustment",{
                        'adjustment': deduction.amount,
                        'adjustment_type': 'Decrement',
                        'reason': deduction.salary_component
                    })

                eos_award.total = eos_award.total+doc.net_pay

            else:
                doc = frappe.new_doc("Salary Slip")
                doc.payroll_frequency= "Monthly"
                doc.start_date=get_first_day(getdate(nowdate()))
                doc.end_date=get_last_day(getdate(nowdate()))
                doc.employee= str(self.employee)
                doc.employee_name=str(self.employee_name)
                doc.company= self.company
                doc.posting_date= nowdate()
                doc.insert(ignore_permissions=True)

                if doc.name:
                    for earning in doc.earnings:
                        eos_award.append("end_of_service_award_adjustment",{
                            'adjustment': earning.amount,
                            'adjustment_type': 'Increment',
                            'reason': earning.salary_component
                        })

                    for deduction in doc.deductions:
                        eos_award.append("end_of_service_award_adjustment",{
                            'adjustment': deduction.amount,
                            'adjustment_type': 'Decrement',
                            'reason': deduction.salary_component
                        })

                eos_award.total = eos_award.total+doc.net_pay

                doc.delete()


        eos_award.total = flt(eos_award.total) + flt(eos_award.award) + flt(eos_award.total_month_salary) + flt(eos_award.leave_total_cost)

        eos_award.insert()
        msg = """تم انشاء مكافأة نهاية الخدمة: <b><a href="#Form/End of Service Award/{0}">{0}</a></b>""".format(eos_award.name)
        frappe.msgprint(msg)




    def get_salary(self):
        salary_amount = 0

        salary_structure = frappe.get_value("Salary Structure", {"employee": self.employee}, "name")

        doc = frappe.get_doc("Salary Structure", salary_structure)

        for earning in doc.earnings:
            if earning.salary_component in ('Basic','Housing','Transportation'):
                salary_amount += earning.amount

        return round(salary_amount)




    def validate(self):
        if not self.last_working_date:
            frappe.throw("Please enter your last working date")

        if frappe.get_value('Employee Loan', filters={'employee' : self.employee,'status':'Sanctioned'}):
            name=frappe.get_value('Employee Loan', filters={'employee' : self.employee,'status':'Sanctioned'}) 
            loan_emp =frappe.get_doc("Employee Loan",name)      
            mm=loan_emp.status
            frappe.throw(self.employee+"/ "+self.employee_name+" have an active loan")
