# -*- coding: utf-8 -*-
# Copyright (c) 2020, Sa Qanawat and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import cint, cstr, date_diff, flt, formatdate, getdate, get_link_to_form, \
    comma_or, get_fullname, add_years, add_months, add_days, nowdate , comma_and
from frappe.model.document import Document

class ReturnFromLeave(Document):
	def validate(self):
		absent_days = date_diff(getdate(self.return_date), getdate(self.to_date)) - 1
		if absent_days < 0:
			frappe.throw(_("Return Date can't be less than or equal To Date"))

	def on_submit(self):
		self.enable_employee_salary()

	def enable_employee_salary(self):
	    ss_doc = frappe.get_doc("Salary Structure", {"employee": self.employee})
	    emp_doc = frappe.get_doc("Employee", self.employee)
	    if ss_doc.is_active == "No":
	    	ss_doc.db_set("is_active", "Yes")
	    emp_doc.db_set("employment_status", "Active")
	    

	def make_attendance_deduction(self):
		ad = frappe.new_doc("Attendance Deduction")
		ad.employee = self.employee
		ad.type = "Attendance"
		ad.payroll_date = self.return_date
		ad.reason = "Return from leave Absence"
		ad.ed_type = "Days"
		ad.days = self.absent_days
		ad.docstatus = 1
		ad.insert(ignore_permissions = True)
		self.db_set("attendance_deduction", ad.name)


