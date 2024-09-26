# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
import json
import math
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, \
    comma_or, get_fullname, add_years, add_months, add_days, nowdate,get_first_day,get_last_day
import datetime
from datetime import date
from frappe.utils import date_diff
from dateutil import relativedelta



class EndofServiceAward(Document):
	def on_submit(self):
		emp = frappe.get_doc("Employee", self.employee)
		emp.status = "Left"
		emp.relieving_date = getdate(get_last_day(add_months(getdate(self.end_date),-1)))
		emp.save(ignore_permissions=True)
		ss = frappe.get_doc("Salary Structure", {"employee": self.employee}, "name")
		ss.is_active = "No"
		ss.save(ignore_permissions=True)

	def get_days_months_years(self):
		difference = relativedelta.relativedelta(getdate(self.end_date), getdate(self.work_start_date))
		return difference.years, difference.months, difference.days + 1


	def get_salary(self,employee):
		basic_salary = 0
		housing_allowance = 0
		transportation_allowance = 0
		salary_structure = frappe.get_value("Salary Structure", {"employee": self.employee}, "name")
		if salary_structure:
			result = frappe.db.sql("select sum(amount) from `tabSalary Detail` where parent='{0}' and parentfield = 'earnings' and abbr in ('TeA','B','SA','TA','IA','OA', 'MA' ,'HA', 'M', 'GOSI' ,'ot_1','p', 'lo', 'Bo', 'OT')".format(salary_structure))

			if result:
				result2 = frappe.db.sql("select sum(amount) from `tabSalary Detail` where parent='{0}' and parentfield = 'earnings' and salary_component in ('Basic','Housing Allowance')".format(salary_structure))

				return cstr(result[0][0]), round(result[0][0]/30, 2), round(result2[0][0]/30, 2)
			else:
				frappe.throw(_("No salary structure found for this employee"))
		else:
			frappe.throw(_("No salary structure found for this employee"))


	def get_leave_balance(self,employee):
		total_leave_balance = frappe.db.sql("select total_leaves_allocated,from_date,to_date,name from `tabLeave Allocation` where employee='{0}' and leave_type='Annual Leave - اجازة اعتيادية' order by creation desc limit 1".format(employee))
		if total_leave_balance:
			leave_days = frappe.db.sql("select sum(total_leave_days) from `tabLeave Application` where employee='{0}' and leave_type='Annual Leave - اجازة اعتيادية' and posting_date between '{1}' and '{2}'".format(employee,total_leave_balance[0][1],total_leave_balance[0][2]))[0][0]
			if not leave_days:
				leave_days = 0
			leave_balance =  int(total_leave_balance[0][0])-int(leave_days)
		else:
			leave_balance = 0
		return leave_balance
        
    
@frappe.whitelist()
def get_award(start_date, end_date, salary, toc, reason):
    start = start_date
    end = end_date
    ret_dict = {}

    if getdate(end) < getdate(start):
        frappe.throw("تاريخ نهاية العمل يجب أن يكون أكبر من تاريخ بداية العمل")
    else:
        diffDays = date_diff(end, start)
        years = math.floor(diffDays / 360)
        daysrem = diffDays - (years * 360)
        months = math.floor(daysrem / 30)
        days = math.ceil(daysrem - (months * 30))
        ret_dict = {"days":days, "months":months, "years":years, "award":0}
    years = flt(years) + (flt(months) / 12) + (flt(days) / 360)
    if not reason:
        frappe.throw("برجاء اختيار سبب انتهاء العلاقة العمالية")
    else:
        if  "كفالة فقط" in toc:
            if reason == "":
                ret_dict["award"] = 0
            else:
                firstPeriod = 0
                secondPeriod = 0
                if years > 5:
                    firstPeriod = 5
                    secondPeriod = years - 5
                else:
                    firstPeriod = years
                result = (firstPeriod * salary * 0.5) + (secondPeriod * salary)
                ret_dict["award"] = result
        else:

            if reason == "فسخ العقد":
                ret_dict["award"] = 0
            elif reason =="استقالة الموظف قبل انتهاء مدة العقد":
                if years < 2:
                    result = 0
                elif years <= 5:
                    result = (1.0 / 6.0) *  salary * years 
                elif years <= 10:
                    result = ((1.0 / 3.0) *  salary * 5) + ((2.0 / 3.0) *  salary * (years - 5))
                else:
                    result = (0.5 *  salary * 5) + ( salary * (years - 5))
                ret_dict["award"] = result
            else:
                if years <= 5:
                    result = 0.5 *  salary * years
                else:
                    result = (0.5 *  salary * 5) + salary * (years - 5)
                ret_dict["award"] = result
               
    return ret_dict
        

