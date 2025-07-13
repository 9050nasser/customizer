// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
cur_frm.add_fetch('employee', 'department', 'department');
cur_frm.add_fetch("employee", "date_of_joining", "work_start_date");

frappe.ui.form.on('End of Service Award', {
        setup: function(frm) {

        frm.set_query("employee", function() {
            return {
                filters: {
                    status: 'Active',
                }
            };
        });
    },
    refresh: function(frm) {

        if (cur_frm.doc.employee) {

            if (cur_frm.doc.type_of_contract == "عمل عن بعد" || cur_frm.doc.type_of_contract == "عقد وظيفي جزئي" || cur_frm.doc.type_of_contract =="عقود موظفين" || cur_frm.doc.type_of_contract =="عقود عمال" || cur_frm.doc.type_of_contract == "عقد أجير" || cur_frm.doc.type_of_contract == "كفالة فقط") {
				cur_frm.set_df_property("reason", "options", "\nانتهاء مدة العقد أو الاتفاق بين الطرفين على انهاء العقد أو انهاء العقد من قبل الشركة\nاستقالة الموظف قبل انتهاء مدة العقد");
            } else {
                cur_frm.set_df_property("reason", "options", "");
            }
        }
    },
    notice_month: function(frm) {
        if (frm.doc.notice_month) {
            frm.set_df_property("notice_month_start", "reqd", true);
            frm.set_df_property("notice_month_end", "reqd", true);
        } else {
            frm.set_df_property("notice_month_start", "reqd", false);
            frm.set_df_property("notice_month_end", "reqd", false);
        }
    },
    employee: function(frm) {

        if (cur_frm.doc.employee) {
            frappe.call({
                "method": "get_salary",
                doc: cur_frm.doc,
                args: { "employee": cur_frm.doc.employee },
                callback: function(data) {
                    if (data) {
                        cur_frm.set_value('salary', data.message[0]);
                        cur_frm.set_value('day_value', data.message[1]);
                        cur_frm.set_value('leave_cost', data.message[2]);

                        cur_frm.set_value('basic', data.message[3]);
                        cur_frm.set_value('housing_allowance', data.message[4]);
                        cur_frm.set_value('transportation_allowance', data.message[5]);
                    }
                }
            });
        }

        if (cur_frm.doc.employee && cur_frm.doc.end_date) {
            var end_resignation_date = new Date(cur_frm.doc.end_date);

            var date1 = new Date(cur_frm.doc.work_start_date);
            var date2 = new Date(cur_frm.doc.end_date);
            var diffTime = date2.getTime() - date1.getTime();
            var diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            
            

            if (diffDays < 30) {
                cur_frm.set_value("days_number", diffDays)
            } else {
                cur_frm.set_value("days_number", end_resignation_date.getDate())
            }

            cur_frm.set_value("total_month_salary", cur_frm.doc.days_number * cur_frm.doc.day_value)
        }

    },
    salary: function(frm) {
        if (cur_frm.doc.salary) {
            frappe.call({
                "method": "get_leave_balance",
                doc: cur_frm.doc,
                args: { "employee": cur_frm.doc.employee },
                callback: function(data) {
                    if (data) {
                        cur_frm.set_value('leave_number', data.message);
                        cur_frm.set_value('leave_total_cost', Math.round(data.message * cur_frm.doc.leave_cost));
                        
                        
                    }
                }
            });
        }
    },
    
    
      type_of_contract: function(frm) {
        if (cur_frm.doc.type_of_contract == "عمل عن بعد" || cur_frm.doc.type_of_contract == "عقد وظيفي جزئي" || cur_frm.doc.type_of_contract =="عقود موظفين" || cur_frm.doc.type_of_contract =="عقود عمال") {
			cur_frm.set_df_property("reason", "options", "\nانتهاء مدة العقد أو الاتفاق بين الطرفين على انهاء العقد أو انهاء العقد من قبل الشركة\nاستقالة الموظف قبل انتهاء مدة العقد");
        } else {
			cur_frm.set_df_property("reason", "options", "");
        }
    },
   end_date: function(frm) {


        frm.trigger("get_days_months_years");


        if (cur_frm.doc.employee && cur_frm.doc.end_date) {

            var end_resignation_date = new Date(cur_frm.doc.end_date);


            var date1 = new Date(cur_frm.doc.work_start_date);
            var date2 = new Date(cur_frm.doc.end_date);
            var diffTime = Math.abs(date2 - date1);
            var diffDays = Math.ceil(diffTime / (1000 * 3600 * 24 ));
            
            

            if (diffDays < 30) {
                cur_frm.set_value("days_number", diffDays)
            } else {
                cur_frm.set_value("days_number", end_resignation_date.getDate())
            }

            cur_frm.set_value("total_month_salary", cur_frm.doc.days_number * cur_frm.doc.day_value)
        }

    },

	get_days_months_years: function(frm) {
        var start = cur_frm.doc.work_start_date;
        var end = cur_frm.doc.end_date;

        if (end < start) {
            cur_frm.set_value('years', 0);
            cur_frm.set_value('months', 0);
            cur_frm.set_value('days', 0);
            validated = false;
            frappe.throw("تاريخ نهاية العمل يجب أن يكون أكبر من تاريخ بداية العمل");


        } else {


            frappe.call({
                "method": "get_days_months_years",
                doc: cur_frm.doc,
                callback: function(data) {
                    if (data) {
						cur_frm.set_value('years', data.message[0]);
						cur_frm.set_value('months', data.message[1]);
						cur_frm.set_value('days', data.message[2]);
					} else {
						cur_frm.set_value('years', 0);
						cur_frm.set_value('months', 0);
						cur_frm.set_value('days', 0);
					}
                }
            });


        };


    },
 
    validate: function(frm) {

        var total = 0;
        $.each(frm.doc.end_of_service_award_deduction || [], function(i, d) {
            total += parseFloat(d.deduction);
        });

        cur_frm.set_value("total_deduction", total);



        var total = 0;
        $.each(frm.doc.end_of_service_award_earning || [], function(i, d) {
            total += parseFloat(d.earning);
        });

        cur_frm.set_value("total_earning", total);


        frm.trigger("get_award");
    },
    after_save: function(frm) {
        var notice_month_salary = 0
        if (cur_frm.doc.notice_month) {
            notice_month_salary = parseFloat(cur_frm.doc.salary)
        }

        cur_frm.set_value('total', cur_frm.doc.award + cur_frm.doc.ticket_total_cost + cur_frm.doc.total_earning - cur_frm.doc.total_deduction);
    },
    find: function(frm) {
        frm.trigger("get_award");
    },
    ticket_number: function(frm) {
        if (cur_frm.doc.ticket_number && cur_frm.doc.ticket_cost) {
            cur_frm.set_value('ticket_total_cost', cur_frm.doc.ticket_number * cur_frm.doc.ticket_cost);
        }
    },
    ticket_cost: function(frm) {
        if (cur_frm.doc.ticket_number && cur_frm.doc.ticket_cost) {
            cur_frm.set_value('ticket_total_cost', cur_frm.doc.ticket_number * cur_frm.doc.ticket_cost);
        }
    },

    get_award: function(frm) {
        var result = 0
        if (!cur_frm.doc.reason) {
            frappe.throw("أرجو اختيار سبب نهاية الخدمة");
        }
        cur_frm.set_value('award', 0);

        var salary = cur_frm.doc.salary;
        var years = parseInt(cur_frm.doc.years) + (parseInt(cur_frm.doc.months) / 12) + (parseInt(cur_frm.doc.days) / 360);
        var reason = cur_frm.doc.reason;

        if (!reason) {
            frappe.throw("برجاء اختيار سبب انتهاء العلاقة العمالية");
            cur_frm.set_value('award', 0);
        } else { 
			if (cur_frm.doc.reason == "انتهاء مدة العقد أو الاتفاق بين الطرفين على انهاء العقد أو انهاء العقد من قبل الشركة"){
                    // cur_frm.set_value('award', "");
                    var firstPeriod, secondPeriod = 0;
                    // set periods
                    if (years > 5) {
                        firstPeriod = 5;
                        secondPeriod = years - 5;
                    } else {
                        firstPeriod = years;
                    }
                    // calculate
                    result = (firstPeriod * cur_frm.doc.salary * 0.5) + (secondPeriod * cur_frm.doc.salary);
                    cur_frm.set_value('award', Math.round(result*100)/100);
			} else {
                if (cur_frm.doc.reason == "") {
                    cur_frm.set_value('award', 0);
                } else if (cur_frm.doc.reason =="استقالة الموظف قبل انتهاء مدة العقد") {
                    if (years < 2) {
                        result = 0;
                    } else if (years <= 5) {
                        result = (1 / 6) * cur_frm.doc.salary * years;
                    } else if (years <= 10) {
                        result = ((1 / 3) * cur_frm.doc.salary * 5) + ((2 / 3) * cur_frm.doc.salary * (years - 5));
                    } else {
                        result = (0.5 * cur_frm.doc.salary * 5) + (cur_frm.doc.salary * (years - 5));
                    }
                    if (typeof(result) === 'number') {
                        cur_frm.set_value('award', Math.round(result*100)/100 );
                    } else {
                        cur_frm.set_value('award', Math.round(result*100)/100);
                    }
                } else {
                    if (years <= 5) {
                        result = 0.5 * cur_frm.doc.salary * years;
                    } else {
                        result = (0.5 * cur_frm.doc.salary * 5) + (cur_frm.doc.salary * (years - 5));
                    }
                    if (typeof(result) === 'number') {
                        cur_frm.set_value('award', Math.round(result*100)/100);
                    } else {
                        cur_frm.set_value('award', Math.round(result*100)/100);
                    }
                    console.log(Math.round(result*100)/100);
                }


            }
        };
    }

});






frappe.ui.form.on('End of Service Award Deduction', {
    deduction: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];

        var total = 0;
        $.each(frm.doc.end_of_service_award_deduction || [], function(i, d) {
            total += parseFloat(d.deduction);
        });

        cur_frm.set_value("total_deduction", total);

    }

});





frappe.ui.form.on('End of Service Award Earning', {
    earning: function(frm, cdt, cdn) {
        var row = locals[cdt][cdn];

        var total = 0;
        $.each(frm.doc.end_of_service_award_earning || [], function(i, d) {
            total += parseFloat(d.earning);
        });

        cur_frm.set_value("total_earning", total);

    }

});
