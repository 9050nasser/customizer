# -*- coding: utf-8 -*-
# Copyright (c) 2021, Ahmed and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils.background_jobs import enqueue
#from frappe import msgprint, _

class AdministrativeCommunication(Document):
	pass
	#def update_read_status(self):
		#user = frappe.session.user 
		#for d in self.get("recipient"):	
			#if d.user == user and d.status !="Read" :	
				#frappe.db.sql("""update`tabRecipient` set status = "Read" where name ="{0}" """.format(d.name))
		#return 1


		
	def on_submit(self):
		self.send_email()
		
	def send_email(self):
		# send email to recipient
		users = []
		if self.get("recipient"):
			for r in self.get("recipient"):
				users.append(r.user)

			frappe.sendmail(
				recipients=users,
				message=self.message,
				subject= self.title ,
				reference_doctype=self.doctype,
				reference_name=self.name,
				)
			
			enqueue(method=frappe.sendmail, queue='short', timeout=300, async=True)
						

def validate_access(doc, user):
	recipients =[]
	if not user: 
		user = frappe.session.user 
	if "System Manager" in frappe.get_roles(user):
		return True
	for u in  doc.get("recipient"):
		recipients.append(u.user)
	if user not in recipients and not doc.for_all and not user == doc.owner:
		return False
	
	return True

