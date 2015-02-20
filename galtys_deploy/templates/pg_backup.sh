#!/bin/bash
CURRENT=${o.home}/${o.backup_subdir}/current
ARCHIVE=${o.home}/${o.backup_subdir}/archive
LOG=${o.home}/${o.backup_subdir}/log

mkdir -p $CURRENT
mkdir -p $ARCHIVE
mkdir -p $LOG

mv $CURRENT/* $ARCHIVE/

%for deployment in o.deploy_ids:
%for db in deployment.db_ids:

%if db.backup:
/usr/bin/pg_dump -U ${deployment.pg_user_id.login} -O ${db.name} | gzip -9 > $CURRENT/${db.name}-$( date +\%Y-\%m-\%d_\%H\%M ).sql.gz; echo "Database backup: $(date)" >> $LOG/${db.name}.log
%endif

%endfor
%endfor
#delete all archive files older than 1000 days, #we have enough space
find $ARCHIVE -xdev -ctime +1000 -type f -exec rm \{\} \;
