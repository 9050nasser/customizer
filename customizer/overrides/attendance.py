import frappe
from hrms.hr.doctype.attendance.attendance import Attendance


class CustomAttendance(Attendance):
    def validate_duplicate_record(self):
        # Override to allow duplicates by skipping validation
        pass

