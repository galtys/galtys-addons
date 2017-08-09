import openerp.release
if openerp.release.version in ['10.0']:
    import skynet
else:
    import skynet70

