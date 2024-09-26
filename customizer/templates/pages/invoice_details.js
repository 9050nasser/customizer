
frappe.ready(function () {

    //~ var invoice = getUrlParameter('i');
    var sales_invoice_id = getUrlParameter('invoice');
    var is_return = getUrlParameter('is_return');
    // var return_against = getUrlParameter('return_against');
    var company = getUrlParameter('company');
    var tax_id = getUrlParameter('tax_id');
    var amount_without_tax = getUrlParameter('amount_without_tax');
    var tax_amount = getUrlParameter('tax_amount');
    var total_amount = getUrlParameter('total_amount');
    var date1 = getUrlParameter('date');
    var time1 = getUrlParameter('time');


    //~ $(".invoice").text(invoice);
    $(".company").text("Pets-Oasis - واحة الحيوان " );
    $(".tax_id").text(tax_id);
    $(".amount_without_tax").text(amount_without_tax);
    $(".tax_amount").text(tax_amount);
    $(".total_amount").text(total_amount);
    $(".date").text(date1);
    $(".time").text(time1);
    $(".sales_invoice_id").text(sales_invoice_id);
    


    //~ frappe.call({
        //~ method: 'loginapp.templates.pages.invoice_details.get_invoice_details',
        //~ args:{'invoice': invoice},
        //~ callback: function(r) {
          //~ if(r.message){
            
            //~ if(is_return==1){
                //~ $(".returned_invoice").text("فاتورة مرتجع");

                //~ against_invoice = "<tr><th>مقابل فاتورة</th><td>"+r.message[0]+"</td></tr>"
                //~ date = "<tr><th>التاريخ</th><td>"+r.message[1]+"</td></tr>"
                //~ time = "<tr><th>الوقت</th><td>"+r.message[2]+"</td></tr>"

                //~ $(".invoice_table tr:first-child").after(against_invoice);
                //~ $(".invoice_table tr:nth-child(2)").after(date);
                //~ $(".invoice_table tr:nth-child(3)").after(time);

            //~ }else{

                //~ date = "<tr><th>التاريخ</th><td>"+r.message[1]+"</td></tr>"
                //~ time = "<tr><th>الوقت</th><td>"+r.message[2]+"</td></tr>"

                //~ $(".invoice_table tr:first-child").after(date);
                //~ $(".invoice_table tr:nth-child(2)").after(time);

            //~ }


          //~ }
        //~ }
    //~ });



    



});


function getUrlParameter(name) {
    name = name.replace(/[\[]/, '\\[').replace(/[\]]/, '\\]');
    var regex = new RegExp('[\\?&]' + name + '=([^&#]*)');
    var results = regex.exec(location.search);
    return results === null ? '' : decodeURIComponent(results[1].replace(/\+/g, ' '));
};


