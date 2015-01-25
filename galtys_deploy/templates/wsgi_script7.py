import sys
import openerp
openerp.tools.config.parse_config(['--config=%s'])
application = openerp.service.wsgi_server.application
