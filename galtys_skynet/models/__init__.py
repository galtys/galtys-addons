import openerp.release
if openerp.release.version in ['10.0', '11.0']:
    import skynet
    import hashsync_demo
else:
    import skynet70
    

