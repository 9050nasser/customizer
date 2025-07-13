<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta http-equiv="X-UA-Compatible" content="IE=edge">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Document</title>
</head>
<body>
    <div class="rtl">
        <h3 class="text-right" style="direction: rtl;">
            السلام عليكم</h3>
            
            <div class="text-right" style="text-align: right;">
                <b>{{ doc.batch_id}} </b> <br>
            </div>
            
            <p style="text-align: right;">  نود التنوية بأن المنتج {{doc.item}}</p>
            
             <p style="text-align: right;"> ستنتهي صلاحيته بتاريخ    {{doc.expiry_date}}</p>
            
            <p dir="rtl" align="right"> الرجاء متابعة الأمر عبر الضغط على الرابط في الأسفل  </p>
            
             <p dir="ltr" align="right"> <a href="{{ frappe.utils.get_url_to_form(doc.doctype, doc.name) }}">{{doc.name}}</a> </p>
            
            <h3 class="text-right" style="direction: rtl;">
            لكم فائق الإحترام  </h3>
    
        
    </div>
</body>
</html>