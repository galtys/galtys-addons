{
    'name': 'Galtys Analysis',
    'version': '1.0',
    'category': 'Analysis',
    'description': """

     """,
    'author': 'Galtys Ltd',
    'website': 'galtys.com',
    #'depends': ['sale', 'stock_return', 'account_invoice_shop_id', 'report_webkit'],
    'depends': ['sale', 'report_webkit'],
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
