import openerp.release
#import galtys_deploy
#import deploy

if openerp.release.version in ['10.0']:
    import galtys_deploy
    import deploy
else:    
    import galtys_deploy8
    import deploy8
