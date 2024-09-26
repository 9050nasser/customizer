# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe import _

def execute(filters=None):
	if not filters: filters = {}
	salary_slips = get_salary_slips(filters)
	if not salary_slips: return [], []

	columns, earning_types, ded_types = get_columns(salary_slips)
	ss_earning_map = get_ss_earning_map(salary_slips)


	data = []
	for ss in salary_slips:
		# if ss.direct_manager:
		# 	direct_manager_name = frappe.get_value("Employee", ss.direct_manager, "full_name_arabic")
		# else:
		# 	direct_manager_name = ""

		# if ss.department_manager:
		# 	department_manager_name = frappe.get_value("Employee", ss.department_manager, "full_name_arabic")
		# else:
		# 	department_manager_name = ""
		row = [ss.employee_name, ss.date_of_joining, ss.designation, ss.employment_type, ss.id_no, ss.department, ss.branch]


		for e in earning_types:
			row.append(ss_earning_map.get(ss.name, {}).get(e))

		row += [ss.total_amount]

		data.append(row)

	return columns, data

def get_columns(salary_slips):
	columns = [
		("Employee Name") + "::140", ("Date of Joining") + "::140", 
		("Designation") + "::140", ("Employment Type") + "::140", ("ID No") + "::140", ("Department") + "::140", ("Branch") + "::140"
	]

	salary_components = {("Earning"): [], ("Deduction"): []}

	for component in frappe.db.sql("""select distinct sd.salary_component, sc.type
		from `tabSalary Detail` sd, `tabSalary Component` sc
		where sc.name=sd.salary_component and sd.amount != 0 and sd.parent in (%s) ORDER BY sd.idx""" %
		(', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=1):
		salary_components[(component.type)].append(component.salary_component)
		
	columns = columns + [(e + ":Currency:120") for e in salary_components[("Earning")]] + [("Gross Pay") + ":Currency:120"] 

	return columns, salary_components[("Earning")], []

def get_salary_slips(filters):
	# salary_slips = frappe.db.sql("""select * from `tabSalary Structure` where docstatus = 1 order by employee""" , as_dict=1)

	salary_slips = frappe.db.sql("""select `tabSalary Structure`.*, `tabEmployee`.employee_name, `tabEmployee`.date_of_joining, 
	`tabEmployee`.designation, `tabEmployee`.employment_type, `tabEmployee`.id_no, `tabEmployee`.department, `tabEmployee`.branch from `tabSalary Structure` join 
		`tabEmployee` on `tabSalary Structure`.employee = `tabEmployee`.name 
		where `tabEmployee`.status = 'Active' """ , as_dict=1)

	return salary_slips or []


def get_ss_earning_map(salary_slips):
	ss_earnings = frappe.db.sql("""select parent, salary_component, amount
		from `tabSalary Detail` where parent in (%s)""" %
		(', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=1)

	ss_earning_map = {}
	for d in ss_earnings:
		ss_earning_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, [])
		ss_earning_map[d.parent][d.salary_component] = flt(d.amount)

	return ss_earning_map


