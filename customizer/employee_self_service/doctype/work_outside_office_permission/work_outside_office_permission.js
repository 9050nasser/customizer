// Copyright (c) 2024, Ahmed and contributors
// For license information, please see license.txt

 frappe.ui.form.on("Work Outside Office Permission", {
 	from_date: function(frm) {
 		calculate_total_day(frm);
 	},
 	to_date: function(frm) {
 		calculate_total_day(frm);
 	},
 });
 
 function calculate_total_day(frm) {
 	if (frm.doc.from_date && frm.doc.to_date) {
 		var from_date = new Date(frm.doc.from_date);
 		var to_date = new Date(frm.doc.to_date);
 		var time_difference = to_date - from_date;
 		var total_day = time_difference / (1000 * 3600 * 24);
 		frm.set_value('total_day', total_day + 1);
 		
 	}else{
 		frm.set_value('total_day', 0)
 	}
}


frappe.ui.form.on('Work Outside Office Permission', {
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

