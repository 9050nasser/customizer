# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import frappe


@frappe.whitelist(allow_guest=True)
def get_invoice_details(invoice):
	# conn = FrappeClient("https://demo.pas.sa")
	# conn.login("administrator", "LkOqnVQapzRZWMd")

	# doc = conn.get_doc('Sales Invoice', invoice)

	doc = frappe.get_doc('Sales Invoice', invoice)

	return doc.return_against, doc.posting_date, ':'.join(str(doc.posting_time).split(':')[:2])

