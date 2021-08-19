# -*- coding: utf-8 -*- 
<html>
<head>
        <script>
            function subst() {
            var vars={};
            var x=document.location.search.substring(1).split('&');
            for(var i in x) {var z=x[i].split('=',2);vars[z[0]] = unescape(z[1]);}
            var x=['frompage','topage','page','webpage','section','subsection','subsubsection'];
            for(var i in x) {
            var y = document.getElementsByClassName(x[i]);
            for(var j=0; j<y.length; ++j) y[j].textContent = vars[x[i]];
                }
            }
        </script>

    <style type="text/css">
body {
font-family:helvetica;
font-size:12;
}


.dest_address {
margin-left:60%;
font-size:12;
}
.header {
margin-left:0;
text-align:left;
width:300px;
font-size:12;
}

.title {
font-size:16;
font-weight: bold;

}

h1{padding-top: 40px;}

.basic_table{
text-align:center;
border:0px solid  #4e4e4e;
border-collapse: collapse;
margin-bottom: 10px;
}
.basic_table td {
border-bottom:1px solid  #4e4e4e;
font-size:12;
padding: 3px;

}

.basic_table tr:first-child > td{background: #4e4e4e;color:#eaeaea;}
.basic_table tr:nth-child(even) {background: #efefef;}
.basic_table tr:nth-child(odd)  {background: #FFF;}

.list_table {
border-color:black;
text-align:center;
border-collapse: collapse;

}
.list_table td {
border-color:gray;
border-top:1px solid gray;
text-align:left;
font-size:12;
padding-right:3px;
padding-left:3px;
padding-top:3px;
padding-bottom:3px;
}

.list_table th {
border-bottom:2px solid black;
text-align:left;
font-size:12;
font-weight:bold;
padding-right:3px;
padding-left:3px;
}

.list_tabe thead {
    display:table-header-group;
}


.total {
width:100%;
}
.lib {
width:10.3%;
}
.tot {
text-align:right;
width:15%;
}
.lefttot {
width:74%;
}
.tax {
width:50%;
} 


			.list_sale_table {
			border:thin solid #E3E4EA;
			text-align:center;
			border-collapse: collapse;
			}
			.list_sale_table td {
			border-top : thin solid #EEEEEE;
			text-align:right;
			font-size:12;
			padding-right:3px
			padding-left:3px
			padding-top:3px
			padding-bottom:3px
			}

			.list_bank_table {
			text-align:center;
			border-collapse: collapse;
			}
			.list_bank_table td {
			text-align:left;
			font-size:12;
			padding-right:3px
			padding-left:3px
			padding-top:3px
			padding-bottom:3px
			}

			.list_bank_table th {
			background-color: #EEEEEE;
			text-align:left;
			font-size:12;
			font-weight:bold;
			padding-right:3px
			padding-left:3px
			}
			
			.list_sale_table th {
			background-color: #EEEEEE;
			border: thin solid #000000;
			text-align:center;
			font-size:12;
			font-weight:bold;
			padding-right:3px
			padding-left:3px
			}
			
			.list_table thead {
			    display:table-header-group;
			}


			.list_tax_table {
			}
			.list_tax_table td {
			text-align:left;
			font-size:12;
			}
			
			.list_tax_table th {
			}


			.list_table thead {
			    display:table-header-group;
			}


			.list_total_table {
				border-collapse: collapse;
			}
			.list_total_table td {
			text-align:right;
			font-size:12;
			}

			.no_bloc {
				border-top: thin solid  #ffffff ;
			}

			
			.list_total_table th {
				background-color: #F7F7F7;
				border-collapse: collapse;
			}

            tfoot.totals tr:first-child td{
                padding-top: 15px;
            }



			.right_table {
			right: 4cm;
			width:"100%";
			}
			
			.std_text {
				font-size:12;
				}


    </style>

</head>

<%def name="render_table(header,dates, data)">
    <table class="basic_table" align="left">

        <tr>
            %for hh in header:
            <td style="font-weight:bold;">${hh}</td>
	    %endfor
        </tr>

	%for d,dd,row in rows:
        <tr>    
          <td style="font-weight:bold;" align="left"> ${3*dd*"&nbsp;"} + ${to_ascii(d.name) }</td>
	    %for col in row:	        
	        <td align="right">${"%0.2f"%col}</td>
	    %endfor
        </tr>
	%endfor

    </table>
</%def>

<%def name="render_table2(header2,shop,table)">
    <table class="basic_table">
        <tr>
            %for hh in header2:
            <td style="font-weight:bold;">${hh}</td>
	    %endfor
        </tr>

	%for categ,dd,row in table:
        <tr>    
          <td style="font-weight:bold;" align="left"> ${3*dd*"&nbsp;"} ${categ.name}</td>
	    %for col in row:	        
	        <td align="right">${"%0.2f"%col}</td>
	    %endfor
        </tr>
	%endfor

    </table>
</%def>

<%def name="render_table3(delivery_header,delivery_table)">
    <table class="basic_table">
        <tr>
            %for hh in delivery_header:
            <td style="font-weight:bold;">${hh}</td>
	    %endfor
        </tr>

	%for categ_id,prod_id,categ,prod,dd,row in delivery_table:
        <tr>    
	  %if categ:
          <td style="font-weight:bold;" align="left"> ${3*dd*"&nbsp;"} ${categ.name} [${categ.id}]</td>
	  %elif prod:
          <td style="font-weight:bold;color:blue" align="left"> ${3*dd*"&nbsp;"} [${prod.default_code}] ${prod.name} </td>
	  %else:
          <td style="font-weight:bold;color:red" align="left"> ${3*dd*"&nbsp;"} Category: ${categ_id} Product ID: ${prod_id} </td>
	  %endif

	  %for col in row:	        
	       <td align="right">${"%0.2f"%col}</td>
	  %endfor
        </tr>
	%endfor

    </table>
</%def>



<body>
    <h1 style="clear:both;">${title} 2015 (this is using cashed data from beg. August 2015)</h1>
    ${render_table(header, dates,data)}


    <h1 style="clear:both;">Sale Analysis, by Shop, Category</h1>
    %for shop,table in tables:
      <h2>${shop.name}</h2>
      <p> </p>
      ${render_table2(delivery_header, shop, table)}
    %endfor

    <h1 style="clear:both;">Product delivery report</h1>
    ${render_table3(delivery_header, delivery_table)}
</body>


</html>
