// Copyright (c) 2024, Ahmed and contributors
// For license information, please see license.txt

frappe.ui.form.on('Leave Permission', {
    end_time: function(frm) {
        if (frm.doc.start_time && frm.doc.end_time) {
            const start = moment(frm.doc.start_time, 'HH:mm');
            const end = moment(frm.doc.end_time, 'HH:mm');

            const duration = moment.duration(end.diff(start));
            const hours = duration.asHours();

            frm.set_value('total_hours', hours);
        }
    }
});

