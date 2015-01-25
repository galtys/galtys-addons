#!/bin/bash

### BEGIN INIT INFO
# Provides:		openerp-server
# Required-Start:	$remote_fs $syslog
# Required-Stop:	$remote_fs $syslog
# Should-Start:		$network
# Should-Stop:		$network
# Default-Start:	2 3 4 5
# Default-Stop:		0 1 6
# Short-Description:	Enterprise Resource Management software
# Description:		Open ERP is a complete ERP and CRM software.
### END INIT INFO

<%
  import os
  PATH="/sbin:/bin:/usr/sbin:/usr/bin"
  DAEMON=os.path.join(o.validated_server_path, 'openerp-server')
  NAME=o.name
  DESC=o.name
  CONFIG=o.odoo_config
  USER=o.user_id.name
  GROUP=o.user_id.group_id.name
  ROOT=o.validated_root
  OPENERP_LOG=os.path.join(ROOT,'%s.log'%o.name)
%>

test -x ${DAEMON} || exit 0

set -e

case "$${1}" in
	start)
		echo -n "Starting ${DESC}: "

		start-stop-daemon --start --quiet --pidfile /var/run/${NAME}.pid \
			--chuid ${USER} --group ${GROUP} --background --make-pidfile \
			--exec ${DAEMON} -- --config=${CONFIG} --logfile=${OPENERP_LOG}
		echo "${NAME}."
		;;

	stop)
		echo -n "Stopping ${DESC}: "

		start-stop-daemon --stop --quiet --pidfile /var/run/${NAME}.pid \
			--oknodo

		echo "${NAME}."
		;;

	restart|force-reload)
		echo -n "Restarting ${DESC}: "

		start-stop-daemon --stop --quiet --pidfile /var/run/${NAME}.pid \
			--oknodo

		sleep 1

		start-stop-daemon --start --quiet --pidfile /var/run/${NAME}.pid \
			--chuid ${USER} --group ${GROUP} --background --make-pidfile \
			--exec ${DAEMON} -- --config=${CONFIG} --logfile=${OPENERP_LOG}
		echo "${NAME}."
		;;

	*)
		N=/etc/init.d/${NAME}
		echo "Usage: ${NAME} {start|stop|restart|force-reload}" >&2
		exit 1
		;;
esac
exit 0
