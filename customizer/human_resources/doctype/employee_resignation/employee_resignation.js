// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
cur_frm.add_fetch("employee", "employee_name", "employee_name");
cur_frm.add_fetch('employee', 'department', 'department');
frappe.ui.form.on('Employee Resignation', {
    setup: function (frm) {

        frm.set_query("employee", function () {
            return {
                filters: {
                    company: frm.doc.company,
                    status: 'Active',
                }
            };
        });
    },
    permission_date: function (frm) {
        frm.set_value("last_working_date", cur_frm.doc.permission_date);
    },
    notice_month: function (frm) {
        if(cur_frm.doc.permission_date){
            if(cur_frm.doc.notice_month){                
                frm.set_value("last_working_date", frappe.datetime.add_months(cur_frm.doc.permission_date, 1));
            }else if(!cur_frm.doc.notice_month){
                frm.set_value("last_working_date", cur_frm.doc.permission_date);
            }
        }
    },
    refresh: function(frm) {

        // if ((cur_frm.doc.company).includes('SA')) {
        //     if (cur_frm.doc.type_of_contract == "Part time") {
        //         cur_frm.set_df_property("reason", "options", "\nانتهاء مدة العقد , أو باتفاق الطرفين على إنهاء العقد\nفسخ العقد من قبل صاحب العمل\nفسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)\nترك الموظف العمل نتيجة لقوة قاهرة\nإنهاء الموظفة لعقد العمل خلال ستة أشهر من عقد الزواج أو خلال ثلاثة أشهر من الوضع\nترك الموظف العمل لأحد الحالات الواردة في المادة (81)\nفسخ العقد من قبل الموظف أو ترك الموظف العمل لغير الحالات الواردة في المادة (81)");
        //     } else {
        //         cur_frm.set_df_property("reason", "options", "\nاتفاق الموظف وصاحب العمل على إنهاء العقد\nفسخ العقد من قبل صاحب العمل\nفسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)\nترك الموظف العمل نتيجة لقوة قاهرة\nإنهاء الموظفة لعقد العمل خلال ستة أشهر من عقد الزواج أو خلال ثلاثة أشهر من الوضع\nترك الموظف العمل لأحد الحالات الواردة في المادة (81)\nترك الموظف العمل دون تقديم استقالة لغير الحالات الواردة في المادة (81)\nاستقالة الموظف");
        //     }
        // } else if ((cur_frm.doc.company).includes('KW')) {
        //     cur_frm.set_df_property("reason", "options", "\nانتهاء العقد من قبل صاحب العمل\nانتهاء مدة العقد المحدد\nانتهاء العقد طبقا لأحكام المواد (50،49،48) من هذا القانون\nإنهاء العاملة العقد من طرفها بسبب زواجها خلال سنة من تاريخ الزواج\nانتهاء العقد من قبل العامل");
        // } else if ((cur_frm.doc.company).includes('UAE')) {

        //     cur_frm.set_df_property("reason", "options", "\nإنهاء العقد\nاستقالة الموظف");

        // } else {
        //     if (cur_frm.doc.type_of_contract == "Part time") {
        //         cur_frm.set_df_property("reason", "options", "\nانتهاء مدة العقد , أو باتفاق الطرفين على إنهاء العقد\nفسخ العقد من قبل صاحب العمل\nفسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)\nترك الموظف العمل نتيجة لقوة قاهرة\nإنهاء الموظفة لعقد العمل خلال ستة أشهر من عقد الزواج أو خلال ثلاثة أشهر من الوضع\nترك الموظف العمل لأحد الحالات الواردة في المادة (81)\nفسخ العقد من قبل الموظف أو ترك الموظف العمل لغير الحالات الواردة في المادة (81)");
        //     } else {
        //         cur_frm.set_df_property("reason", "options", "\nاتفاق الموظف وصاحب العمل على إنهاء العقد\nفسخ العقد من قبل صاحب العمل\nفسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)\nترك الموظف العمل نتيجة لقوة قاهرة\nإنهاء الموظفة لعقد العمل خلال ستة أشهر من عقد الزواج أو خلال ثلاثة أشهر من الوضع\nترك الموظف العمل لأحد الحالات الواردة في المادة (81)\nترك الموظف العمل دون تقديم استقالة لغير الحالات الواردة في المادة (81)\nاستقالة الموظف");
        //     }
        // }

    },
    employee: function(frm){

        // if ((cur_frm.doc.company).includes('SA')) {
        //     if (cur_frm.doc.type_of_contract == "Part time") {
        //         cur_frm.set_df_property("reason", "options", "\nانتهاء مدة العقد , أو باتفاق الطرفين على إنهاء العقد\nفسخ العقد من قبل صاحب العمل\nفسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)\nترك الموظف العمل نتيجة لقوة قاهرة\nإنهاء الموظفة لعقد العمل خلال ستة أشهر من عقد الزواج أو خلال ثلاثة أشهر من الوضع\nترك الموظف العمل لأحد الحالات الواردة في المادة (81)\nفسخ العقد من قبل الموظف أو ترك الموظف العمل لغير الحالات الواردة في المادة (81)");
        //     } else {
        //         cur_frm.set_df_property("reason", "options", "\nاتفاق الموظف وصاحب العمل على إنهاء العقد\nفسخ العقد من قبل صاحب العمل\nفسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)\nترك الموظف العمل نتيجة لقوة قاهرة\nإنهاء الموظفة لعقد العمل خلال ستة أشهر من عقد الزواج أو خلال ثلاثة أشهر من الوضع\nترك الموظف العمل لأحد الحالات الواردة في المادة (81)\nترك الموظف العمل دون تقديم استقالة لغير الحالات الواردة في المادة (81)\nاستقالة الموظف");
        //     }
        // } else if ((cur_frm.doc.company).includes('KW')) {
        //     cur_frm.set_df_property("reason", "options", "\nانتهاء العقد من قبل صاحب العمل\nانتهاء مدة العقد المحدد\nانتهاء العقد طبقا لأحكام المواد (50،49،48) من هذا القانون\nإنهاء العاملة العقد من طرفها بسبب زواجها خلال سنة من تاريخ الزواج\nانتهاء العقد من قبل العامل");
        // } else if ((cur_frm.doc.company).includes('UAE')) {

        //     cur_frm.set_df_property("reason", "options", "\nإنهاء العقد\nاستقالة الموظف");

        // } else {
        //     if (cur_frm.doc.type_of_contract == "Part time") {
        //         cur_frm.set_df_property("reason", "options", "\nانتهاء مدة العقد , أو باتفاق الطرفين على إنهاء العقد\nفسخ العقد من قبل صاحب العمل\nفسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)\nترك الموظف العمل نتيجة لقوة قاهرة\nإنهاء الموظفة لعقد العمل خلال ستة أشهر من عقد الزواج أو خلال ثلاثة أشهر من الوضع\nترك الموظف العمل لأحد الحالات الواردة في المادة (81)\nفسخ العقد من قبل الموظف أو ترك الموظف العمل لغير الحالات الواردة في المادة (81)");
        //     } else {
        //         cur_frm.set_df_property("reason", "options", "\nاتفاق الموظف وصاحب العمل على إنهاء العقد\nفسخ العقد من قبل صاحب العمل\nفسخ العقد من قبل صاحب العمل لأحد الحالات الواردة في المادة (80)\nترك الموظف العمل نتيجة لقوة قاهرة\nإنهاء الموظفة لعقد العمل خلال ستة أشهر من عقد الزواج أو خلال ثلاثة أشهر من الوضع\nترك الموظف العمل لأحد الحالات الواردة في المادة (81)\nترك الموظف العمل دون تقديم استقالة لغير الحالات الواردة في المادة (81)\nاستقالة الموظف");
        //     }
        // }

    }
});
