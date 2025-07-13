<p><!DOCTYPE html>
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
              السلام عليكم و رحمة الله</h3></p>

<pre><code>        &lt;h3 class="text-right" style="direction: rtl;"&gt;
          اشعار بانتهاء صلاحية المنتج خلال 4 أشهر من الآن &lt;/h3&gt;

        &lt;p style="text-align: right;"&gt;  نود التنوية بأن المنتج {{doc.item}}&lt;/p&gt;

         &lt;p style="text-align: right;"&gt; ستنتهي صلاحيته بتاريخ    {{doc.expiry_date}}&lt;/p&gt;

        &lt;p dir="rtl" align="right"&gt; الرجاء متابعة الأمر عبر الضغط على الرابط في الأسفل إذا توفر المنتج في معرضكم &lt;/p&gt;

         &lt;p dir="ltr" align="right"&gt; &lt;a href="{{ frappe.utils.get_url_to_form(doc.doctype, doc.name) }}"&gt;{{doc.name}}&lt;/a&gt; &lt;/p&gt;

        &lt;h3 class="text-right" style="direction: rtl;"&gt;
        لكم فائق الإحترام  &lt;/h3&gt;


&lt;/div&gt;
</code></pre>

<p></body>
</html></p>
