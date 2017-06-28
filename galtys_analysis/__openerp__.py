{
    'name': 'Galtys Analysis',
    'version': '1.0',
    'category': 'Analysis',
    'description': """

     """,
    'author': 'Galtys Ltd',
    'website': 'galtys.com',
<<<<<<< HEAD
    #'depends': ['sale', 'stock_return', 'account_invoice_shop_id', 'report_webkit'],
    'depends': ['sale', 'report_webkit'],
=======
#    'depends': ['sale', 'stock_return', 'account_invoice_shop_id', 'report_webkit'],
    'depends': ['sale',  'report_webkit'],
>>>>>>> 4108a106e5e4a57a21c7ea595f1d43ac94b5794e
    'data': [
        'galtys_analysis_view.xml',
        'analysis_phase_data.xml',
        'sql_query_view.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
