#!/bin/bash
# restart.sh - Restart uWSGI
# Turku University (2018) Department of Future Technologies
# Jani Tammi <jasata@utu.fi>
#
#if [[ $EUID -ne 0 ]]; then
#   echo "This script must be run as root"
#   exit 1
#fi

# Clear out the log
[ -f /srv/nginx-root/uwsgi.log ] && :> /srv/nginx-root/uwsgi.log

# Restart uwsgi
systemctl restart uwsgi && sleep 1 && systemctl status uwsgi

# EOF
