import openerp.release
print ['openerp.release', openerp.release.version]
if openerp.release.version in ['10.0', '11.0','11.0+e']:
    import skynet
    import hashsync_demo
else:
    import skynet70
    

