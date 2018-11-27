#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware (PMAPI)
# PATE Monitor API setup script
#
# setup.py - Jani Tammi <jasata@utu.fi>
#   0.1.0   2018.11.26  Initial version.
#   0.2.0   2018.11.27  Permission and ownership setting fixed.
#
#
import os
import pwd
import grp
import time
import subprocess

instance_application_conf = r"""
#! /usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Turku University (2018) Department of Future Technologies
# Foresail-1 / PATE Monitor / Middleware (PMAPI)
# Flask application configuration
#
# application.conf - Jani Tammi <jasata@utu.fi>
#
#   0.1.0   2018.10.11  Initial version.
#   0.2.0   2018.10.23  Renamed as 'application.conf'
#   0.3.0   2018.10.23  Move version numbers to APIVERSION and APPVERSION.
#
#
# See http://flask.pocoo.org/docs/0.12/config/ for built-in config values.
#
# To generate SECRET_KEY:
# >>> import os
# >>> os.urandom(24)
# b'\\xb5R\\x8d...
#
import os
import logging

DEBUG                    = True
SESSION_COOKIE_NAME      = 'pmapisession'
SECRET_KEY               = b'\\xb5R\\x8d\\x8aZa\\x07\\x90i\\xe5Y\\xff\\x9e|\\xe8p\\x0b\\x86;\\xc3}\\xd0\\xfc?'
EXPLAIN_TEMPLATE_LOADING = True
TOP_LEVEL_DIR            = os.path.abspath(os.curdir)
BASEDIR                  = os.path.abspath(os.path.dirname(__file__))


#
# Command table configuration (seconds)
#
COMMAND_TIMEOUT         = 0.5
COMMAND_POLL_INTERVAL   = 0.2


#
# Flask app logging
#
LOG_FILENAME             = 'application.log'
LOG_LEVEL                = 'DEBUG'              # DEBUG, INFO, WARNING, ERROR, CRITICAL


#
# MariaDB configuration
#
MYSQL_DATABASE_HOST      = 'localhost'
MYSQL_DATABASE_PORT      = 3306
MYSQL_DATABASE_USER      = 'ridb'
MYSQL_DATABASE_PASSWORD  = 'ridb'
MYSQL_DATABASE_DB        = 'ridb'
MYSQL_DATABASE_CHARSET   = 'utf8'	# PyMySQL requires 'utf8', others 'utf-8'

#
# SQLite3 configuration
#
SQLITE3_DATABASE_FILE   = '../patemon.sqlite3'

#
# Flask email
#



# EOF
"""

etc_nginx_sites_available_default = """
server {
        listen 80 default_server;
        listen [::]:80 default_server;

        root /srv/nginx-root;
        server_name _;
        location / {
                include uwsgi_params;
                uwsgi_pass unix:/tmp/patemon.uwsgi.sock;
        }
}
"""

etc_systemd_system_uwsgi_service = """
[Unit]
Description=uWSGI instance
After=network.target

[Service]
ExecStartPre=-/bin/bash -c 'mkdir -p /run/uwsgi; chown www-data:www-data /run/uwsgi;'
ExecStart=/bin/bash -c 'cd /srv/nginx-root; uwsgi --ini uwsgi.ini'

[Install]
WantedBy=multi-user.target
"""

def do_or_die(cmd: list):
    prc = subprocess.run(cmd.split(" "))
    if prc.returncode:
        print("Command '{}' failed!".format(cmd))
        os._exit(-1)


###############################################################################
#
# Begin setup
#
###############################################################################

if __name__ == '__main__':

    print("Beginning pmapi setup...")

    # Create instance/application.conf
    appconf = "/srv/nginx-root/instance/application.conf"
    # Directory
    if not os.path.exists(os.path.dirname(appconf)):
        os.makedirs(os.path.dirname(appconf))
    elif not os.path.isdir(os.path.dirname(appconf)):
        print(
            "ERROR! '{}' exists and is not a directory!".format(
                os.path.dirname(appconf)
            )
        )
        os._exit(-1)
    # Write file
    with open(appconf, 'w') as cfgfile:
        cfgfile.write(instance_application_conf)


    # New 'default' site for Nginx
    nginxconf = "/etc/nginx/sites-available/default"
    if os.path.exists(nginxconf):
        if os.path.isfile(nginxconf):
            os.rename(nginxconf, nginxconf + ".original")
        else:
            print(
                "'{}' does not seem to be a regular file!".format(
                    nginxconf
                )
            )
            print("Please check manually!")
            os._exit(-1)
    with open(nginxconf, 'w') as cfgfile:
        cfgfile.write(etc_nginx_sites_available_default)



    # systemd file for uwsgi
    sysdservice = "/etc/systemd/system/uwsgi.service"
    if os.path.exists(sysdservice):
        if os.path.isfile(sysdservice):
            os.rename(sysdservice, sysdservice + ".original")
        else:
            print(
                "'{}' does not seem to be a regular file!".format(
                    sysdservice
                )
            )
            print("Please check manually!")
            os._exit(-1)
    with open(sysdservice, 'w') as servicefile:
        servicefile.write(etc_systemd_system_uwsgi_service)




    # File permissions
    def set_basic_perms(path):
        """Expects to receive a directory (sets it 0o775 right off the bat)."""
        ignore = [".git", ".gitignore", ".gitmodules", "__pycache__"]
        os.chmod(path, 0o775)
        for filename in os.listdir(path):
            if os.path.basename(filename) in ignore:
                continue
            path_file = path + "/" + filename
            print(
                "  {:.<{width}} ".format(path_file, width=50),
                end="",
                flush=True
            )
            # ownership
            os.chown(
                path_file,
                pwd.getpwnam("www-data").pw_uid,
                grp.getgrnam("www-data").gr_gid
            )
            # permissions
            if os.path.isdir(path_file):
                print("directory")
                set_basic_perms(path_file)
            else:
                print("file")
                os.chmod(path_file, 0o664)
            # if filename.endswith(".c") or filename.endswith(".py"): 

    print("Setting basic permissions and ownerships...")
    set_basic_perms("/srv/nginx-root")
    # Specials
    print("Setting special permissions and ownerships...", end="", flush=True)
    do_or_die("chmod 700 restart.sh")
    do_or_die("chown root.root restart.sh")
    do_or_die("chmod 744 setup.py")
    do_or_die("chown root.root setup.py")
    do_or_die("chmod 444 LICENSE")
    do_or_die("chmod 444 APPVERSION")
    do_or_die("chmod 444 APIVERSION")
    do_or_die("chmod 444 uwsgi.ini")
    print("Done!")

    print("Enabling uWSGI service in systemd...", end="", flush=True)
    do_or_die("systemctl enable uwsgi")
    print("Done!")

    print("Restarting services")
    # Restart Nginx
    print("  {:.<{width}} ".format("nginx", width=20), end="", flush=True)
    do_or_die("systemctl restart nginx")
    print("done!")

    # Enable uWSGI
    socketfile = "/tmp/patemon.uwsgi.sock"
    print("  {:.<{width}} ".format("uwsgi", width=20), end="", flush=True)
    do_or_die("systemctl restart uwsgi")
    # Check that the socket has been created
    time.sleep(2)
    if not os.path.exists(socketfile):
        print(
            "uWSGI start-up failure! Socket '{}' not created!".format(
                socketfile
            )
        )
        os._exit(-1)
    print("Done!")


    print("Repository 'pmapi' setup completed!\n")

# EOF