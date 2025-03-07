#!/usr/bin/env python3
import subprocess
import os
import platform
import datetime
import configparser
import random
import string
import getpass
 
"""
ISPMailInstall Utility
Implements ISPMail Tutorial of Christoph Haas as in https://workaround.org/ispmail/buster/
Details are in https://ispmailinstall.x386.org/ or README.MD
version: 0.2.1

Exit Codes:
0:    Program completed succesfully (Still there might be some errors processing commands)
1:    Error in config file
11:   Platform is not Linux
12:   User is not root or not by sudo
13:   Platform is not Debian or Ubuntu
21:   Error creating a log file
22:   Error adding to log file

   ---Copyright (C) 2021 - 2023 Exforge exforge@x386.xyz
   This program is free text: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   any later version.
   This document is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.
   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

def distro_version():
   """ Returns Distro name and version
   /etc/os-release file contains distro name and release versions among
   other information. We try to reach the information in the following format:
   NAME="Ubuntu"
   VERSION_ID="22.04"
   Supported distros are: Ubuntu 22.04, 24.04, Debian GNU/Linux 11, 12
   """
   d = {}
   try:
      with open("/etc/os-release") as f:
         for line in f:
            # Clear " and Newlines
            line = line.replace('"', '')          
            line = line.replace('\n', '')
            # Skip empty lines
            if line == "":
               continue
            (key, val) = line.split("=")
            d[(key)] = val
      distro = d["NAME"]
      version = d["VERSION_ID"]
   except:
      distro = "Other"
      version = "Other"
   return distro, version

def find_between(s, first, last):
   """
   Find and return substring between 2 strings
   s, first and last are strings
   returns the substring of s between first and last strings
   written by: https://stackoverflow.com/users/280995/cji
   taken from: https://stackoverflow.com/questions/3368969/find-string-between-two-substrings
   """
   try:
      start = s.index(first) + len(first)
      end = s.index(last, start)
      return s[start:end]
   except ValueError:
      return ""

def now():
   """
   Return current Date-Time in format : 2020-09-17 10:50:44
   Used for timestamping in log files
   """
   now_raw = datetime.datetime.now()
   return (now_raw.strftime("%Y-%m-%d %H:%M:%S "))

def start_log(log_file):
   """
   Initialize a log file
   log_file : Name (including path) of log file
   """
   try:
      with open(log_file, "w") as out_file:
         out_file.write(now() + "Log started\n")   
   except Exception as e:
      print("Error creating log file: " + log_file)
      print("Exiting...Error message: " + str(e))
      exit(21)

def add_log(log_file, log):
   """
   Adds a log to the log file
   log_file: Name of log file
   log: log to be added
   """
   try:
      with open(log_file, "a") as out_file:
         out_file.write(now() + str(log) + "\n")   
   except Exception as e:
      print("Error adding to log file: " + log_file)
      print("Exiting...Error message: " + str(e))
      exit(22)

def process_command(command):
   """
   Process a command on bash shell, capture stdout and stderr
   If process completes succesfully, log stdout in applog
   Otherwise log stderr in errorlog, stdout in applog
   """
   
   # Add separator line and processing command logs
   add_log(applog, line_separator)
   add_log(applog, "Processing command --> " + command)
   print("Processing command --> " + command)
   # Run command
   proc = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, executable='/bin/bash')
   # Get stdout and stderr
   out, err = proc.communicate()
   ret = proc.returncode
   # Command ended succefully
   if ret == 0:
      add_log(applog, "Command Ended succesfully --> " + command)
      print("Command Ended succesfully --> " + command)
      add_log(applog, "Command output: " + separator + str(out) + separator)
   # Error in command
   else:
      add_log(applog, "Error code: " + str(ret) + " at command --> " + command)
      print("Error code: " + str(ret) + " at command --> " + command)
      add_log(applog, "Command output: " + separator + str(out) + separator)
      add_log(errorlog, line_separator)
      add_log(errorlog, "Error code: " + str(ret) + " at command --> " + command)
      add_log(errorlog, "Error output: " + separator + str(err) + separator)
   return ret

def process_command_wpipe(command):
   """
   Same as process_command, but does not capture stdout, so that we can use > redirection
   on a command.
   """
   # Add separator line and processing command logs
   add_log(applog, line_separator)
   add_log(applog, "Processing command --> " + command)
   print("Processing command --> " + command)
   # Run command
   proc = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE, executable='/bin/bash')
   # Get stdout and stderr (stdout is empty)
   out, err = proc.communicate()
   ret = proc.returncode
   # Command ended succefully
   if ret == 0:
      add_log(applog, "Command Ended succesfully --> " + command)
      print("Command Ended succesfully --> " + command)
   # Error in command
   else:
      add_log(applog, "Error code: " + str(ret) + " at command --> " + command)
      print("Error code: " + str(ret) + " at command --> " + command)
      add_log(errorlog, line_separator)
      add_log(errorlog, "Error code: " + str(ret) + " at command --> " + command)
      add_log(errorlog, "Error output: " + separator + str(err) + separator)
   return ret

def backup(filename):
   """
   If file already exists, back it up as: file.backup.YYYYMMDD
   otherwise do nothing.
   Called when overwriting a file
   """
   if os.path.isfile(filename):
      backup_file = filename + ".backup." + today
      # Try to rename file as backup file
      try:
         os.rename(filename, backup_file)
      except Exception as e:
         add_log(applog, "Error backing file up: " + filename)
         add_log(errorlog, line_separator)
         add_log(errorlog, "Error backing file up: " + filename)
         add_log(errorlog, "Error message: " + str(e))
         return(1)
      else:
         add_log(applog, "File: " + filename + " backed up to: " + backup_file)
         return(0)
   return(0)         

def to_file(filename, value):
   """
   Fill the file with the value
   """
   add_log(applog, line_separator)
   add_log(applog, "Filling file: " + filename)
   backup(filename)
   try:
      with open(filename, "w") as out_file:
         out_file.write(value)
   except Exception as e:
      add_log(applog, "Error filling file: " + filename)
      add_log(errorlog, line_separator)
      add_log(errorlog, "Error filling file: " + filename)
      add_log(errorlog, "Error message: " + str(e))
      return(1)
   else:
      add_log(applog, "Success filling file: " + filename)
      return(0)

def append_file(filename, value):
   """
   Append the value to the file
   """
   add_log(applog, line_separator)
   add_log(applog, "Appending to file: " + filename)
   backup(filename)
   try:
      with open(filename, "a") as out_file:
         out_file.write(value)   
   except Exception as e:
      add_log(applog, "Error appending to file: " + filename)
      add_log(errorlog, line_separator)
      add_log(errorlog, "Error appending to file: " + filename)
      add_log(errorlog, "Error message: " + str(e))
      return(1)
   else:
      add_log(applog, "Success appending to file: " + filename)
      return(0)
   
def from_file(filename):
   """
   Returns the contents of a file. 
   Return value may have an extra newline character
   """
   add_log(applog, line_separator)
   add_log(applog, "Reading from file: " + filename)
   try:
      with open(filename, "r") as in_file:
         value = in_file.read()
   except Exception as e:
      add_log(applog, "Error reading from file: " + filename)
      add_log(errorlog, line_separator)
      add_log(errorlog, "Error reading from file: " + filename)
      add_log(errorlog, "Error message: " + str(e))
      return(1, "")
   else:
      add_log(applog, "Success reading from file: " + filename)
      return(0, value)

def password(length):
   """
   Generates a password of specified length.
   Password consists of uppercase and lowercase letters and digits.
   """
   # Add digits twice to increase their chance
   passwdbase = string.ascii_letters + string.digits + string.digits 
   result = ''.join(random.choice(passwdbase) for i in range(length))
   return(result)

def get_parameter(message):
   """
   Reads and returns a parameter value.
   Empty values are not allowed
   """
   ans = ""
   while (ans.strip() == ""):
      ans = input(message)
      if ans.strip() == "":
         print("No empty values!!!")
   return(ans.strip())
   
def get_password(message):
   """
   Reads and returns a password value.
   Reads twice to make sure
   Empty values are not allowed
   """
   passwd = passwd1 = passwd2 = ""
   while (passwd.strip() == ""):
      while (passwd1.strip() == ""):
         passwd1 = getpass.getpass(message)
         if passwd1.strip() == "":
            print("No empty passwords!!!")
      while (passwd2.strip() == ""):
         passwd2 = getpass.getpass("Enter it again: ")
         if passwd2.strip() == "":
            print("No empty passwords!!!")
      if passwd1.strip() == passwd2.strip():
         passwd = passwd1.strip()
      else:
         print("Passwords don't match")
         passwd1 = passwd2 = ""
   return(passwd)

def read_config_file():
   """
   Reads from config_file to get all parameters.
   """
   global hostname, domains, email
   global domains, mailadminpw, mailserverpw, dbadminpw, rspamdpw, ispmailadminpw
   global print_all_passwords

   if not os.path.isfile(config_file):
      # No config file, nothing to do
      return(1)
   config = configparser.ConfigParser()
   try:
      config.read(config_file)
   except Exception as e:
      print("Error in config file " + config_file)
      print(str(e))
      exit(1)
   hostname = config.get("Mail Server", "hostname", fallback="")
   # We may have more than 1 domains, store them in a list
   domains_raw = config.get("Mail Server", "domains", fallback="")
   if domains_raw.strip() != "":
      domains = domains_raw.split(" ")
   email = config.get("Mail Server", "email", fallback="")
   mailadminpw = config.get("Passwords", "mailadminpw", fallback="")
   mailserverpw = config.get("Passwords", "mailserverpw", fallback="")
   dbadminpw = config.get("Passwords", "dbadminpw", fallback="")
   rspamdpw = config.get("Passwords", "rspamdpw", fallback="")
   ispmailadminpw = config.get("Passwords", "ispmailadminpw", fallback="")
   print_all_passwords_raw = config.get("Program Options", "print_all_passwords", fallback ="")
   if print_all_passwords_raw in ["yes", "Yes", "YES"]:
      print_all_passwords = True

def get_missing_parameters():
   """
   Any parameters not obtained from config_file are obtained from user
   """
   global hostname, domains, email
   global domains, mailadminpw, mailserverpw, dbadminpw, rspamdpw, ispmailadminpw

   if hostname == "":
      hostname = get_parameter("Please enter hostname (mail.example.com): ")
   # We may have more than 1 domains, store them in a list
   if len(domains) == 0:
      domains_raw = get_parameter("Please enter domains to host, separated by spaces: ")
      domains = domains_raw.split(" ")
   if email == "":
      email = get_parameter("Please enter email address: ")
   if mailadminpw == "":
      mailadminpw = get_password("Enter password mailadminpw (auto to autogenerate): ")
   if mailserverpw == "":
      mailserverpw = get_password("Enter password mailserverpw (auto to autogenerate): ")
   if dbadminpw == "":
      dbadminpw = get_password("Enter password dbadminpw: (auto to autogenerate) ")
   if rspamdpw == "":
      rspamdpw = get_password("Enter password rspamdpw: (auto to autogenerate) ")
   if ispmailadminpw == "":
      ispmailadminpw = get_password("Enter password ispmailadminpw: (auto to autogenerate) ")
   
def generate_auto_passwords():
   """
   Generate all passwords set for auto generate.
   Set flags for autogenerated passwords to print them later
   """
   global domains, mailadminpw, mailserverpw, dbadminpw, rspamdpw, ispmailadminpw
   global mailadminpwauto, mailserverpwauto, dbadminpwauto, rspamdpwauto, ispmailadminpwauto

   if mailadminpw == "auto":
      mailadminpw = password(12)
      mailadminpwauto = True
   if mailserverpw == "auto":
      mailserverpw = password(12)
      mailserverpwauto = True
   if dbadminpw == "auto":
      dbadminpw = password(12)
      dbadminpwauto = True
   if rspamdpw == "auto":
      rspamdpw = password(12)
      rspamdpwauto = True
   if ispmailadminpw == "auto":
      ispmailadminpw = password(12)
      ispmailadminpwauto = True
   return(0)

def initialize_parameters():
   """
   Do everything necessary for setting parameters.
   Must be called before initializing all content.
   """
   read_config_file()
   get_missing_parameters()
   generate_auto_passwords()


def apt_install():
   """
   Install all necessary applications.
   Set parameters for postfix and roundcube, otherwise they ask for user interaction.
   Install apache, php, mariadb, postfix, rspamd, certbot, dovecot, adminer, roundcube
   """
   commands = ["apt-get update",
   "debconf-set-selections <<< \"postfix postfix/mailname string " + hostname + "\"",
   "debconf-set-selections <<< \"postfix postfix/main_mailer_type string 'Internet Site'\"",
   "debconf-set-selections <<< \"roundcube roundcube/dbconfig-install boolean true\"",
   "debconf-set-selections <<< \"roundcube roundcube/database-type string mysql\"",
   "debconf-set-selections <<< \"roundcube roundcube/mysql/app-pass password\"",
   "apt-get -qq install apache2",
   "apt-get -qq install php",
   "apt-get -qq install mariadb-server",
   "apt-get -qq install postfix",
   "apt-get -qq install postfix-mysql",
   "apt-get -qq install rspamd",
   "apt-get -qq install certbot",
   "apt-get -qq install dovecot-mysql",
   "apt-get -qq install dovecot-pop3d",
   "apt-get -qq install dovecot-imapd",
   "apt-get -qq install dovecot-managesieved",
   "apt-get -qq install dovecot-lmtpd",
   "apt-get -qq install adminer",
   "apt-get -qq install ca-certificates",
   "apt-get -qq install roundcube",
   "apt-get -qq install roundcube-plugins",
   "apt-get -qq install roundcube-plugins-extra",
   "apt-get -qq install roundcube-mysql",
   "apt-get -qq install git"]

   for command in commands:
      process_command(command)
      
def apache_configs():
   """
   All necessary apache configs.
   Create an http site, enable it, reload apache to make it active
   Run certbot to get a free certificate from letsencrypt
   Create a config for https site
   Add a renewal hook to certbot to restart necessary services after certificate renewal
   """
   commands1 = ["mkdir /var/www/" + hostname]
   files1 = [(http_conf1_file, http_conf1)]
   commands2 = ["a2ensite " + hostname +"-http.conf",
   "a2dissite 000-default.conf",
   "systemctl reload apache2",
   "certbot certonly -n --webroot --webroot-path /var/www/" + hostname+ " -d "+ hostname + " --agree-tos --email " + email,
   ]
   files2 = [(http_conf2_file, http_conf2), 
   (https_conf_file, https_conf),]
   commands3 = ["a2enmod ssl",
   "a2enmod proxy_http",
   "a2enmod rewrite",
   "a2ensite " + hostname +"-https"]
   files3 = [(letsencrypt_ini_file, letsencrypt_ini)]
   commands4 = ["chmod +x /etc/letsencrypt/renewal-hooks/deploy/reloadall.sh"]

   for command in commands1:
      process_command(command)
   for filename, content in files1:
      to_file(filename, content)
   for command in commands2:
      process_command(command)
   for filename, content in files2:
      to_file(filename, content)
   for command in commands3:
      process_command(command)
   for filename, content in files3:
      to_file(filename, content)
   for command in commands4:
      process_command(command)

def mariadb_scripts():
   """
   Run a mariadb script to create a database and add users
   """
   to_file(mariadb_sql_file, mariadb_sql)
   command = "mariadb < " + mariadb_sql_file
   process_command(command)   

def postfix_mysql():
   """
   Add necessary configurations for postfix-mysql connection
   """
   commands = [ "postconf virtual_mailbox_domains=mysql:/etc/postfix/mysql-virtual-mailbox-domains.cf",
   "postconf virtual_mailbox_maps=mysql:/etc/postfix/mysql-virtual-mailbox-maps.cf", 
   "postconf virtual_alias_maps=mysql:/etc/postfix/mysql-virtual-alias-maps.cf", 
   "postconf virtual_alias_maps=mysql:/etc/postfix/mysql-virtual-alias-maps.cf,mysql:/etc/postfix/mysql-email2email.cf",
   "chgrp postfix /etc/postfix/mysql-*.cf",
   "chmod u=rw,g=r,o= /etc/postfix/mysql-*.cf"
   ]
   files = [(postfix_mailbox_domains_file, postfix_mailbox_domains),
   (postfix_mailbox_maps_file, postfix_mailbox_maps),
   (postfix_alias_maps_file, postfix_alias_maps),
   (postfix_email2email_file, postfix_email2email)]

   for filename, content in files:
      to_file(filename, content)
   for command in commands:
      process_command(command)

def dovecot_config():
   """
   Necessary configurations for Dovecot
   """
   commands1 = ["groupadd -g 5000 vmail",
   "useradd -g vmail -u 5000 vmail -d /var/vmail -m",
   "chown -R vmail:vmail /var/vmail"]

   commands2 = ["chown root:root /etc/dovecot/dovecot-sql.conf.ext",
   "chmod go= /etc/dovecot/dovecot-sql.conf.ext",
   "postconf virtual_transport=lmtp:unix:private/dovecot-lmtp",
   "postconf 'smtpd_recipient_restrictions = reject_unauth_destination check_policy_service unix:private/quota-status'",
   "chmod +x /usr/local/bin/quota-warning.sh",
   "systemctl restart dovecot"]

   files = [(dovecot_10_mail_conf_file, dovecot_10_mail_conf),
   (dovecot_10_auth_conf_file, dovecot_10_auth_conf),
   (dovecot_auth_sql_conf_file, dovecot_auth_sql_conf),
   (dovecot_10_master_conf_file, dovecot_10_master_conf),
   (dovecot_10_ssl_conf_file, dovecot_10_ssl_conf),
   (dovecot_sql_conf_ext_file, dovecot_sql_conf_ext),
   (dovecot_20_lmtp_conf_file, dovecot_20_lmtp_conf),
   (dovecot_90_quota_conf_file, dovecot_90_quota_conf),
   (dovecot_quota_warning_file, dovecot_quota_warning)]

   for command in commands1:
      process_command(command)
   for filename, content in files:
      to_file(filename, content)
   for command in commands2:
      process_command(command)

def roundcube_config():
   """
   Configura Roundcube's connection to Dovecot and Postfix
   """
   files = [(roundcube_main_config_file, roundcube_main_config),
   (roundcube_password_config_file, roundcube_password_config),
   (roundcube_managesieve_config_file, roundcube_managesieve_config)]
   for filename, content in files:
      to_file(filename, content)

def postfix_config():
   """
   Necessary postfix configurations for mail sending.
   """
   files = [(postfix_master_config_file, postfix_master_config)]
   commands = ["postconf smtpd_sasl_type=dovecot",
   "postconf smtpd_sasl_path=private/auth",
   "postconf smtpd_sasl_auth_enable=yes",
   "postconf smtpd_tls_security_level=may",
   "postconf smtpd_tls_auth_only=yes",
   "postconf smtpd_tls_cert_file=/etc/letsencrypt/live/" + hostname + "/fullchain.pem",
   "postconf smtpd_tls_key_file=/etc/letsencrypt/live/" + hostname + "/privkey.pem",
   "postconf smtp_tls_security_level=may",
   "postconf smtpd_sender_login_maps=mysql:/etc/postfix/mysql-email2email.cf",
   "postconf smtpd_milters=inet:127.0.0.1:11332",
   "postconf non_smtpd_milters=inet:127.0.0.1:11332",
   "postconf milter_mail_macros=\"i {mail_addr} {client_addr} {client_name} {auth_authen}\""]
   for filename, content in files:
      to_file(filename, content)
   for command in commands:
      process_command(command)

def rspamd_config():
   """
   All rspamd configs, including filtering and spam learning
   """
   commands1 = ["mkdir /etc/dovecot/sieve",
   "mkdir /etc/dovecot/sieve-after",
   "systemctl restart dovecot"]

   commands2 = ["sievec /etc/dovecot/sieve-after/spam-to-folder.sieve",
   "sievec /etc/dovecot/sieve/learn-spam.sieve",
   "sievec /etc/dovecot/sieve/learn-ham.sieve",
   "chmod u=rw,go= /etc/dovecot/sieve/learn-{spam,ham}.{sieve,svbin}",
   "chown vmail.vmail /etc/dovecot/sieve/learn-{spam,ham}.{sieve,svbin}",
   "chmod u=rwx,go= /etc/dovecot/sieve/rspamd-learn-{spam,ham}.sh",
   "chown vmail.vmail /etc/dovecot/sieve/rspamd-learn-{spam,ham}.sh"]

   files = [(rspamd_milter_headers_file, rspamd_milter_headers),
   (dovecot_90_sieve_conf_file, dovecot_90_sieve_conf),
   (dovecot_spam_to_folder_sieve_file, dovecot_spam_to_folder_sieve),
   (rspamd_override_bayes_file, rspamd_override_bayes),
   (rspamd_local_bayes_file, rspamd_local_bayes),
   (dovecot_20_imap_conf_file, dovecot_20_imap_conf),
   (dovecot_learn_spam_sieve_file, dovecot_learn_spam_sieve),
   (dovecot_learn_ham_sieve_file, dovecot_learn_ham_sieve),
   (rspamd_learn_spam_file, rspamd_learn_spam),
   (rspamd_learn_ham_file, rspamd_learn_ham),
   (dovecot_15_mailboxes_conf_file, dovecot_15_mailboxes_conf)]

   for command in commands1:
      process_command(command)
   for filename, content in files:
      to_file(filename, content)
   for command in commands2:
      process_command(command)

   # Configure password for accessing rspamd interface
   command = "rspamadm pw -p " + rspamdpw + " > /tmp/rspamdpw"
   process_command_wpipe(command)
   filename = "/tmp/rspamdpw"
   ret, rspamdencpw = from_file(filename)
   # Remove \n at the end
   rspamdencpw = rspamdencpw[:-1]
   command = "rm /tmp/rspamdpw"
   process_command(command)
   filename = "/etc/rspamd/local.d/worker-controller.inc"
   content = 'password = "' + rspamdencpw + '"'
   to_file(filename, content)

def dkim_config():
   """
   DKIM key signing for all the hosted domains
   """
   commands1 = ["mkdir /var/lib/rspamd/dkim",
   "chown _rspamd:_rspamd /var/lib/rspamd/dkim"]

   filename = rspamd_dkim_signing_conf_file
   content = rspamd_dkim_signing_conf

   for command in commands1:
      process_command(command)
   to_file(filename, content)

   # Create Dkim keypairs for all domains
   for domain in domains:
      command = "rspamadm dkim_keygen -d "+ domain + " -s " + today + " -k /var/lib/rspamd/dkim/" 
      command = command + domain + "." + today + ".key > /tmp/" + domain + ".dkim"
      process_command_wpipe(command)
   
   # Fill Dkim map file with domains and selectors
   content = ""
   filename = "/etc/rspamd/dkim_selectors.map"
   for domain in domains:
      content = content + domain + " " + today + "\n"
   to_file(filename, content)
   
   commands2 = ["chown _rspamd /var/lib/rspamd/dkim/*",
   "chmod u=r,go= /var/lib/rspamd/dkim/*"]
   for command in commands2:
      process_command(command)

def ispmailadmin_config():
   """
   Download ISPMail Admin and configure its interface
   """
   commands = ["mkdir /var/www/ispmailadmin",
   "git clone  -b buster https://gitlab.com/ToKe79/ispmailadmin.git /var/www/ispmailadmin"]
   # The buster branch is not compatible with PHP 8, so use master branch for Ubuntu 22.04
   if (distro_release == "Ubuntu22.04"):
      commands[1] = "git clone  -b master https://gitlab.com/ToKe79/ispmailadmin.git /var/www/ispmailadmin"
   for command in commands:
      process_command(command)
   filename = ispmailadmin_configs_file
   content = ispmailadmin_configs
   to_file(filename, content)

def finish_installations():
   """
   Final touches. Set permissions for /var/www and restart services
   """
   commands = ["chown -R www-data:www-data /var/www/",
   "chmod -R 770 /var/www/",
   "systemctl restart apache2",
   "systemctl restart dovecot",
   "systemctl restart postfix",
   "systemctl restart rspamd"]

   for command in commands:
      process_command(command)

def prepare_dns_config():
   """
   Document all necessary DNS configs for all domains
   and put them in a file for user's reference.
   """
   for domain in domains:
      keyfile = "/tmp/" + domain + ".dkim"
      dns_config_file = domain + ".dns.config"
      ret, keyraw = from_file(keyfile)
      # Retrieve p= part
      start_str = '"p='
      end_str = '" ) ;'
      key = find_between(keyraw, start_str, end_str)
      config0 = "RecordType Host Value (Priority for MX Record)\n"
      config1 = "MX @ " + hostname + " 10\n"
      config2 = "TXT @ v=spf1 mx -all\n"
      config3 = "TXT _dmarc v=DMARC1; aspf=s; adkim=s; pct=100; p=reject; rua=mailto:postmaster@" + domain + "\n"
      config4 = "TXT " + today + "._domainkey v=DKIM1; k=rsa; p=" + key + "\n"
      dns_config = config0 + config1 + config2 + config3 + config4
      to_file(dns_config_file, dns_config)

def prepare_password_file():
   """
   Print all generated password (or others too if print_all_passwords flag is set) in 
   password file
   """
   print_passwords = (mailadminpwauto or mailserverpwauto or dbadminpwauto or rspamdpwauto)
   print_passwords = (print_passwords or ispmailadminpwauto or print_all_passwords)
   if print_passwords:
      filename = passwordfile
      content = ""
      if mailadminpwauto or print_all_passwords:
         content += "mailadminpw: " + mailadminpw + "\n"
      if mailserverpwauto or print_all_passwords:
         content += "mailserverpw: " + mailserverpw + "\n"
      if dbadminpwauto or print_all_passwords:
         content += "dbadminpw: " + dbadminpw + "\n"
      if rspamdpwauto or print_all_passwords:
         content += "rspamdpw: " + rspamdpw + "\n"
      if ispmailadminpwauto or print_all_passwords:
         content += "ispmailadminpw: " + ispmailadminpw + "\n"
      to_file(filename, content)
      # Secure password file
      commands = ["chown root:root " + filename,
      "chmod 600 " + filename]
      for command in commands:
         process_command(command)

def prepare_autoconfig_files():
   """
   Prepare mail autoconfig files for domains and prepare ispmail.autoconfig.txt file
   for instructions to apply mail autoconfig files.
   Mail autoconfig files will be names as domain.config-v1.1.xml
   """
   for domain in domains:
      filename = domain + ".config-v1.1.xml"
      content = """<?xml version="1.0" encoding="UTF-8"?>
<clientConfig version="1.1">
  <emailProvider id=\"""" + domain + """\">
    <domain>""" + domain + """</domain>
    <displayName>""" + domain + """ Mail Service</displayName>
    <displayShortName>""" + domain + """</displayShortName>
    <incomingServer type="imap">
      <hostname>""" + hostname + """</hostname>
      <port>143</port>
      <socketType>STARTTLS</socketType>
      <authentication>password-cleartext</authentication>
      <username>%EMAILADDRESS%</username>
    </incomingServer>
    <incomingServer type="pop3">
      <hostname>""" + hostname + """</hostname>
      <port>110</port>
      <socketType>STARTTLS</socketType>
      <authentication>password-cleartext</authentication>
      <username>%EMAILADDRESS%</username>
    </incomingServer>
    <outgoingServer type="smtp">
      <hostname>""" + hostname + """</hostname>
      <port>587</port>
      <socketType>STARTTLS</socketType>
      <authentication>password-cleartext</authentication>
      <username>%EMAILADDRESS%</username>
    </outgoingServer>
  </emailProvider>
</clientConfig>
"""
      to_file(filename, content)
   filename = "ispmail.autoconfig.txt"
   content = "Instructions for Auto Mail Configuration\n"
   content += "This step is optional.\n"
   content += "Rename domain.config-v1.1.xml files to config-v1.1.xml and "
   content += "put them in domain's web site as it can be reached as:\n"
   content += "https://domain/.well-known/autoconfig/mail/config-v1.1.xml\n"
   content += "(You can use http, if you don't have ssl)\n\n"
   for domain in domains:
      content += "Rename " + domain + ".config-v1.1.xml to config-v1.1.xml and place it in as "
      content += "https://" + domain + "/.well-known/autoconfig/mail/config-v1.1.xml \n\n"
   to_file(filename, content)

# Ubuntu 20.04 and Ubuntu 22.04 have some differences in roundcube package (So do Debian 10 
#   and Debian 11/12) . So we should know if the distro is Ubuntu20, Ubuntu22, Debian12, Debian11, 
#   or Debian10. 

supported_releases = ["Ubuntu22.04", "Ubuntu24.04", "Debian GNU/Linux11", "Debian GNU/Linux12"]


# Clear all parameters
hostname = ""
domains = []
email = ""
mailadminpw = ""
mailserverpw = ""
dbadminpw = ""
rspamdpw = ""
ispmailadminpw = ""
print_all_passwords = False

# Clear password flags
mailadminpwauto = False
mailserverpwauto = False
dbadminpwauto = False
rspamdpwauto = False
ispmailadminpwauto = False

# Set config, log and password files
config_file = "ispmail.conf"
applog = "ispmail.log"
errorlog = "ispmail.error.log"
passwordfile = "ispmailpasswords.txt"

# Runs only on Linux
system = platform.system()
if system != "Linux":
   print("This program runs on Linux only, exiting!")
   exit(11)

# Require root or sudo
euid = os.geteuid()
if euid != 0:
   print("This program must be run by root or with sudo, exiting!")
   exit(12)

# Runs only on Debian and Ubuntu
version = platform.version()
if not (("Ubuntu" in version) or ("Debian" in version)):
   print("This program runs on Debian or Ubuntu only, exiting!")
   exit(13)

# Check releases other than Ubuntu 22.04, 24.04, and Debian 11, 12

distro, release = distro_version()
distro_release = distro + release


if (distro_release not in supported_releases):
   print("Your version ", distro_release, " is not supported.")
   print("Press Enter to continue anyway, CTRL-C to exit.")
   input()

# Get all parameters before initializing all settings
initialize_parameters()

#------------------- apache_configs() definitions BEGIN-------------------
# Initial http config file to acquire ssl certificate
http_conf1 = """<VirtualHost *:80>
 ServerName """ + hostname + """
 DocumentRoot /var/www/""" + hostname + """
</VirtualHost>
"""
http_conf1_file = "/etc/apache2/sites-available/" + hostname + "-http.conf"

# http config is changed to forward to ssl site after getting ssl certificate
http_conf2 = """<VirtualHost *:80>
 ServerName """ + hostname + """
 DocumentRoot /var/www/""" + hostname + """
 RewriteEngine On
 RewriteCond %{REQUEST_URI} !.well-known/acme-challenge
 RewriteRule ^(.*)$ https://%{SERVER_NAME}$1 [R=301,L]  
</VirtualHost>
"""
http_conf2_file = "/etc/apache2/sites-available/" + hostname + "-http.conf"

# Our main https site config
# This site includes, roundcube, adminer, rspamd and ispmailadmin interfaces

# In Debian 10 and Ubuntu 20.04, roundcube runtime resides in /var/lib/roundcube
# In Debian 11, 12 and Ubuntu 22.04, roundcube runtime resides in /var/lib/roundcube/public_html
roundcube_directory = "/var/lib/roundcube"
if (distro_release in ["Ubuntu22.04", "Debian GNU/Linux11", "Debian GNU/Linux12"]):
   roundcube_directory = "/var/lib/roundcube/public_html"
https_conf ="""
<VirtualHost *:443>
 Alias /adminer /usr/share/adminer/adminer
 Alias /admin /var/www/ispmailadmin
 Include /etc/roundcube/apache.conf
 ServerName """ + hostname + """
 DocumentRoot """ + roundcube_directory + """
 SSLEngine on
 SSLCertificateFile /etc/letsencrypt/live/""" + hostname + """/fullchain.pem
 SSLCertificateKeyFile /etc/letsencrypt/live/""" + hostname + """/privkey.pem
 <Location /rspamd>
   Require all granted   
 </Location>
 RewriteEngine On
 RewriteRule ^/rspamd$ /rspamd/ [R,L]
 RewriteRule ^/rspamd/(.*) http://localhost:11334/$1 [P,L]
</VirtualHost>
"""
https_conf_file = "/etc/apache2/sites-available/" + hostname + "-https.conf"

letsencrypt_ini = """#!/bin/bash
systemctl reload apache2
systemctl reload postfix
systemctl reload dovecot
"""
letsencrypt_ini_file = "/etc/letsencrypt/renewal-hooks/deploy/reloadall.sh"
#------------------- apache_configs() definitions END-------------------

#------------------- mariadb_scripts() definitions BEGIN-------------------
# SQL script to create database, users and tables, 
mariadb_sql = """CREATE DATABASE IF NOT EXISTS mailserver;
GRANT ALL PRIVILEGES ON *.* TO 'admin'@'localhost' IDENTIFIED BY '""" + dbadminpw + "';" + """
GRANT ALL ON mailserver.* TO 'mailadmin'@'localhost' IDENTIFIED BY '""" + mailadminpw + "';" + """
GRANT SELECT ON mailserver.* to 'mailserver'@'127.0.0.1' IDENTIFIED BY '""" + mailserverpw + "';" + """
GRANT SELECT, UPDATE, INSERT, DELETE on mailserver.* TO 'ispmailadmin'@'127.0.0.1' 
IDENTIFIED BY '""" + ispmailadminpw + "';" + """
USE mailserver;
CREATE TABLE IF NOT EXISTS virtual_domains (
 id int(11) NOT NULL auto_increment,
 name varchar(50) NOT NULL,
 PRIMARY KEY (id)
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE IF NOT EXISTS virtual_users (
 id int(11) NOT NULL auto_increment,
 domain_id int(11) NOT NULL,
 email varchar(100) NOT NULL,
 password varchar(150) NOT NULL,
 quota bigint(11) NOT NULL DEFAULT 0,
 PRIMARY KEY (id),
 UNIQUE KEY email (email),
 FOREIGN KEY (domain_id) REFERENCES virtual_domains(id) ON DELETE CASCADE
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
 #   virtual_aliases:
 CREATE TABLE IF NOT EXISTS virtual_aliases (
 id int(11) NOT NULL auto_increment,
 domain_id int(11) NOT NULL,
 source varchar(100) NOT NULL,
 destination varchar(100) NOT NULL,
 PRIMARY KEY (id),
 FOREIGN KEY (domain_id) REFERENCES virtual_domains(id) ON DELETE CASCADE
 ) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""
# Add records to virtual_domains for all domains
for domain in domains:
   mariadb_sql += "INSERT INTO virtual_domains (name) VALUES ('" + domain +"');\n"
mariadb_sql_file = "/tmp/ispmail_mariadb.sql"
#------------------- mariadb_scripts() definitions END-------------------

#------------------- postfix_mysql() definitions BEGIN-------------------
# Postfix mailbox domains map
postfix_mailbox_domains = """user = mailserver
password = """ +mailserverpw + """
hosts = 127.0.0.1
dbname = mailserver
query = SELECT 1 FROM virtual_domains WHERE name='%s'
"""
postfix_mailbox_domains_file = "/etc/postfix/mysql-virtual-mailbox-domains.cf"

# Postfix mailbox users map
postfix_mailbox_maps = """user = mailserver
password = """ + mailserverpw + """
hosts = 127.0.0.1
dbname = mailserver
query = SELECT 1 FROM virtual_users WHERE email='%s'
"""
postfix_mailbox_maps_file = "/etc/postfix/mysql-virtual-mailbox-maps.cf"

# Postfix mailbox aliases map
postfix_alias_maps = """user = mailserver
password = """ + mailserverpw + """
hosts = 127.0.0.1
dbname = mailserver
query = SELECT destination FROM virtual_aliases WHERE source='%s'
"""
postfix_alias_maps_file = "/etc/postfix/mysql-virtual-alias-maps.cf"

# Necessary for catch-all mail accounts
postfix_email2email = """user = mailserver
password = """ + mailserverpw + """
hosts = 127.0.0.1
dbname = mailserver
query = SELECT email FROM virtual_users WHERE email='%s'
"""
postfix_email2email_file = "/etc/postfix/mysql-email2email.cf"
#------------------- postfix_mysql() definitions END-------------------

#------------------- dovecot_config definitions BEGIN-------------------
# dovecot authentication conf
dovecot_10_auth_conf = """##
## Authentication processes
##
#
# Disable LOGIN command and all other plaintext authentications unless
# SSL/TLS is used (LOGINDISABLED capability). Note that if the remote IP
# matches the local IP (ie. you're connecting from the same computer), the
# connection is considered secure and plaintext authentication is allowed.
# See also ssl=required setting.
#disable_plaintext_auth = yes
#
# Authentication cache size (e.g. 10M). 0 means it's disabled. Note that
# bsdauth, PAM and vpopmail require cache_key to be set for caching to be used.
#auth_cache_size = 0
# Time to live for cached data. After TTL expires the cached record is no
# longer used, *except* if the main database lookup returns internal failure.
# We also try to handle password changes automatically: If user's previous
# authentication was successful, but this one wasn't, the cache isn't used.
# For now this works only with plaintext authentication.
#auth_cache_ttl = 1 hour
# TTL for negative hits (user not found, password mismatch).
# 0 disables caching them completely.
#auth_cache_negative_ttl = 1 hour
#
# Space separated list of realms for SASL authentication mechanisms that need
# them. You can leave it empty if you don't want to support multiple realms.
# Many clients simply use the first one listed here, so keep the default realm
# first.
#auth_realms =
#
# Default realm/domain to use if none was specified. This is used for both
# SASL realms and appending @domain to username in plaintext logins.
#auth_default_realm = 
#
# List of allowed characters in username. If the user-given username contains
# a character not listed in here, the login automatically fails. This is just
# an extra check to make sure user can't exploit any potential quote escaping
# vulnerabilities with SQL/LDAP databases. If you want to allow all characters,
# set this value to empty.
#auth_username_chars = abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ01234567890.-_@
#
# Username character translations before it's looked up from databases. The
# value contains series of from -> to characters. For example "#@/@" means
# that '#' and '/' characters are translated to '@'.
#auth_username_translation =
#
# Username formatting before it's looked up from databases. You can use
# the standard variables here, eg. %Lu would lowercase the username, %n would
# drop away the domain if it was given, or "%n-AT-%d" would change the '@' into
# "-AT-". This translation is done after auth_username_translation changes.
#auth_username_format = %Lu
#
# If you want to allow master users to log in by specifying the master
# username within the normal username string (ie. not using SASL mechanism's
# support for it), you can specify the separator character here. The format
# is then <username><separator><master username>. UW-IMAP uses "*" as the
# separator, so that could be a good choice.
#auth_master_user_separator =
#
# Username to use for users logging in with ANONYMOUS SASL mechanism
#auth_anonymous_username = anonymous
#
# Maximum number of dovecot-auth worker processes. They're used to execute
# blocking passdb and userdb queries (eg. MySQL and PAM). They're
# automatically created and destroyed as needed.
#auth_worker_max_count = 30
#
# Host name to use in GSSAPI principal names. The default is to use the
# name returned by gethostname(). Use "$ALL" (with quotes) to allow all keytab
# entries.
#auth_gssapi_hostname =
#
# Kerberos keytab to use for the GSSAPI mechanism. Will use the system
# default (usually /etc/krb5.keytab) if not specified. You may need to change
# the auth service to run as root to be able to read this file.
#auth_krb5_keytab = 
#
# Do NTLM and GSS-SPNEGO authentication using Samba's winbind daemon and
# ntlm_auth helper. <doc/wiki/Authentication/Mechanisms/Winbind.txt>
#auth_use_winbind = no
#
# Path for Samba's ntlm_auth helper binary.
#auth_winbind_helper_path = /usr/bin/ntlm_auth
#
# Time to delay before replying to failed authentications.
#auth_failure_delay = 2 secs
#
# Require a valid SSL client certificate or the authentication fails.
#auth_ssl_require_client_cert = no
#
# Take the username from client's SSL certificate, using 
# X509_NAME_get_text_by_NID() which returns the subject's DN's
# CommonName. 
#auth_ssl_username_from_cert = no
#
# Space separated list of wanted authentication mechanisms:
#   plain login digest-md5 cram-md5 ntlm rpa apop anonymous gssapi otp skey
#   gss-spnego
# NOTE: See also disable_plaintext_auth setting.
auth_mechanisms = plain login
#
##
## Password and user databases
##
#
#
# Password database is used to verify user's password (and nothing more).
# You can have multiple passdbs and userdbs. This is useful if you want to
# allow both system users (/etc/passwd) and virtual users to login without
# duplicating the system users into virtual database.
#
# <doc/wiki/PasswordDatabase.txt>
#
# User database specifies where mails are located and what user/group IDs
# own them. For single-UID configuration use "static" userdb.
#
# <doc/wiki/UserDatabase.txt>
#
#!include auth-deny.conf.ext
#!include auth-master.conf.ext
#
#!include auth-system.conf.ext
!include auth-sql.conf.ext
#!include auth-ldap.conf.ext
#!include auth-passwdfile.conf.ext
#!include auth-checkpassword.conf.ext
#!include auth-vpopmail.conf.ext
#!include auth-static.conf.ext
"""
dovecot_10_auth_conf_file = "/etc/dovecot/conf.d/10-auth.conf"

# Dovecot SQL conf
dovecot_auth_sql_conf = """# Authentication for SQL users. Included from 10-auth.conf.
#
# <doc/wiki/AuthDatabase.SQL.txt>
#
passdb {
  driver = sql
  #
  # Path for SQL configuration file, see example-config/dovecot-sql.conf.ext
  args = /etc/dovecot/dovecot-sql.conf.ext
}
#
# "prefetch" user database means that the passdb already provided the
# needed information and there's no need to do a separate userdb lookup.
# <doc/wiki/UserDatabase.Prefetch.txt>
#userdb {
#  driver = prefetch
#}
#
userdb {
  driver = sql
  args = /etc/dovecot/dovecot-sql.conf.ext
}
#
# If you don't have any user-specific settings, you can avoid the user_query
# by using userdb static instead of userdb sql, for example:
# <doc/wiki/UserDatabase.Static.txt>
#userdb {
  #driver = static
  #args = uid=vmail gid=vmail home=/var/vmail/%u
#}
"""
dovecot_auth_sql_conf_file = "/etc/dovecot/conf.d/auth-sql.conf.ext"

# Dovecot Mailbox conf
dovecot_10_mail_conf = """
##
## Mailbox locations and namespaces
##
#
# Location for users' mailboxes. The default is empty, which means that Dovecot
# tries to find the mailboxes automatically. This won't work if the user
# doesn't yet have any mail, so you should explicitly tell Dovecot the full
# location.
#
# If you're using mbox, giving a path to the INBOX file (eg. /var/mail/%u)
# isn't enough. You'll also need to tell Dovecot where the other mailboxes are
# kept. This is called the "root mail directory", and it must be the first
# path given in the mail_location setting.
#
# There are a few special variables you can use, eg.:
#
#   %u - username
#   %n - user part in user@domain, same as %u if there's no domain
#   %d - domain part in user@domain, empty if there's no domain
#   %h - home directory
#
# See doc/wiki/Variables.txt for full list. Some examples:
#
#   mail_location = maildir:~/Maildir
#   mail_location = mbox:~/mail:INBOX=/var/mail/%u
#   mail_location = mbox:/var/mail/%d/%1n/%n:INDEX=/var/indexes/%d/%1n/%n
#
# <doc/wiki/MailLocation.txt>
#
mail_location = maildir:~/Maildir
#
# If you need to set multiple mailbox locations or want to change default
# namespace settings, you can do it by defining namespace sections.
#
# You can have private, shared and public namespaces. Private namespaces
# are for user's personal mails. Shared namespaces are for accessing other
# users' mailboxes that have been shared. Public namespaces are for shared
# mailboxes that are managed by sysadmin. If you create any shared or public
# namespaces you'll typically want to enable ACL plugin also, otherwise all
# users can access all the shared mailboxes, assuming they have permissions
# on filesystem level to do so.
namespace inbox {
  # Namespace type: private, shared or public
  #type = private
  #
  # Hierarchy separator to use. You should use the same separator for all
  # namespaces or some clients get confused. '/' is usually a good one.
  # The default however depends on the underlying mail storage format.
  #separator = 
  #
  # Prefix required to access this namespace. This needs to be different for
  # all namespaces. For example "Public/".
  #prefix = 
  #
  # Physical location of the mailbox. This is in same format as
  # mail_location, which is also the default for it.
  #location =
  #
  # There can be only one INBOX, and this setting defines which namespace
  # has it.
  inbox = yes
  #
  # If namespace is hidden, it's not advertised to clients via NAMESPACE
  # extension. You'll most likely also want to set list=no. This is mostly
  # useful when converting from another server with different namespaces which
  # you want to deprecate but still keep working. For example you can create
  # hidden namespaces with prefixes "~/mail/", "~%u/mail/" and "mail/".
  #hidden = no
  #
  # Show the mailboxes under this namespace with LIST command. This makes the
  # namespace visible for clients that don't support NAMESPACE extension.
  # "children" value lists child mailboxes, but hides the namespace prefix.
  #list = yes
  #
  # Namespace handles its own subscriptions. If set to "no", the parent
  # namespace handles them (empty prefix should always have this as "yes")
  #subscriptions = yes
  #
  # See 15-mailboxes.conf for definitions of special mailboxes.
}
#
# Example shared namespace configuration
#namespace {
  #type = shared
  #separator = /
  #
  # Mailboxes are visible under "shared/user@domain/"
  # %%n, %%d and %%u are expanded to the destination user.
  #prefix = shared/%%u/
  #
  # Mail location for other users' mailboxes. Note that %variables and ~/
  # expands to the logged in user's data. %%n, %%d, %%u and %%h expand to the
  # destination user's data.
  #location = maildir:%%h/Maildir:INDEX=~/Maildir/shared/%%u
  #
  # Use the default namespace for saving subscriptions.
  #subscriptions = no
  #
  # List the shared/ namespace only if there are visible shared mailboxes.
  #list = children
#}
# Should shared INBOX be visible as "shared/user" or "shared/user/INBOX"?
#mail_shared_explicit_inbox = no
#
# System user and group used to access mails. If you use multiple, userdb
# can override these by returning uid or gid fields. You can use either numbers
# or names. <doc/wiki/UserIds.txt>
#mail_uid =
#mail_gid =
#
# Group to enable temporarily for privileged operations. Currently this is
# used only with INBOX when either its initial creation or dotlocking fails.
# Typically this is set to "mail" to give access to /var/mail.
mail_privileged_group = mail
#
# Grant access to these supplementary groups for mail processes. Typically
# these are used to set up access to shared mailboxes. Note that it may be
# dangerous to set these if users can create symlinks (e.g. if "mail" group is
# set here, ln -s /var/mail ~/mail/var could allow a user to delete others'
# mailboxes, or ln -s /secret/shared/box ~/mail/mybox would allow reading it).
#mail_access_groups =
#
# Allow full filesystem access to clients. There's no access checks other than
# what the operating system does for the active UID/GID. It works with both
# maildir and mboxes, allowing you to prefix mailboxes names with eg. /path/
# or ~user/.
#mail_full_filesystem_access = no
#
# Dictionary for key=value mailbox attributes. This is used for example by
# URLAUTH and METADATA extensions.
#mail_attribute_dict =
#
# A comment or note that is associated with the server. This value is
# accessible for authenticated users through the IMAP METADATA server
# entry "/shared/comment". 
#mail_server_comment = ""
#
# Indicates a method for contacting the server administrator. According to
# RFC 5464, this value MUST be a URI (e.g., a mailto: or tel: URL), but that
# is currently not enforced. Use for example mailto:admin@example.com. This
# value is accessible for authenticated users through the IMAP METADATA server
# entry "/shared/admin".
#mail_server_admin = 
#
##
## Mail processes
##
#
# Don't use mmap() at all. This is required if you store indexes to shared
# filesystems (NFS or clustered filesystem).
#mmap_disable = no
#
# Rely on O_EXCL to work when creating dotlock files. NFS supports O_EXCL
# since version 3, so this should be safe to use nowadays by default.
#dotlock_use_excl = yes
#
# When to use fsync() or fdatasync() calls:
#   optimized (default): Whenever necessary to avoid losing important data
#   always: Useful with e.g. NFS when write()s are delayed
#   never: Never use it (best performance, but crashes can lose data)
#mail_fsync = optimized
#
# Locking method for index files. Alternatives are fcntl, flock and dotlock.
# Dotlocking uses some tricks which may create more disk I/O than other locking
# methods. NFS users: flock doesn't work, remember to change mmap_disable.
#lock_method = fcntl
#
# Directory where mails can be temporarily stored. Usually it's used only for
# mails larger than >= 128 kB. It's used by various parts of Dovecot, for
# example LDA/LMTP while delivering large mails or zlib plugin for keeping
# uncompressed mails.
#mail_temp_dir = /tmp
#
# Valid UID range for users, defaults to 500 and above. This is mostly
# to make sure that users can't log in as daemons or other system users.
# Note that denying root logins is hardcoded to dovecot binary and can't
# be done even if first_valid_uid is set to 0.
#first_valid_uid = 500
#last_valid_uid = 0
#
# Valid GID range for users, defaults to non-root/wheel. Users having
# non-valid GID as primary group ID aren't allowed to log in. If user
# belongs to supplementary groups with non-valid GIDs, those groups are
# not set.
#first_valid_gid = 1
#last_valid_gid = 0
#
# Maximum allowed length for mail keyword name. It's only forced when trying
# to create new keywords.
#mail_max_keyword_length = 50
#
# ':' separated list of directories under which chrooting is allowed for mail
# processes (ie. /var/mail will allow chrooting to /var/mail/foo/bar too).
# This setting doesn't affect login_chroot, mail_chroot or auth chroot
# settings. If this setting is empty, "/./" in home dirs are ignored.
# WARNING: Never add directories here which local users can modify, that
# may lead to root exploit. Usually this should be done only if you don't
# allow shell access for users. <doc/wiki/Chrooting.txt>
#valid_chroot_dirs = 
#
# Default chroot directory for mail processes. This can be overridden for
# specific users in user database by giving /./ in user's home directory
# (eg. /home/./user chroots into /home). Note that usually there is no real
# need to do chrooting, Dovecot doesn't allow users to access files outside
# their mail directory anyway. If your home directories are prefixed with
# the chroot directory, append "/." to mail_chroot. <doc/wiki/Chrooting.txt>
#mail_chroot = 
#
# UNIX socket path to master authentication server to find users.
# This is used by imap (for shared users) and lda.
#auth_socket_path = /var/run/dovecot/auth-userdb
#
# Directory where to look up mail plugins.
#mail_plugin_dir = /usr/lib/dovecot/modules
#
# Space separated list of plugins to load for all services. Plugins specific to
# IMAP, LDA, etc. are added to this list in their own .conf files.
mail_plugins = quota
#
##
## Mailbox handling optimizations
##
#
# Mailbox list indexes can be used to optimize IMAP STATUS commands. They are
# also required for IMAP NOTIFY extension to be enabled.
#mailbox_list_index = yes
#
# Trust mailbox list index to be up-to-date. This reduces disk I/O at the cost
# of potentially returning out-of-date results after e.g. server crashes.
# The results will be automatically fixed once the folders are opened.
#mailbox_list_index_very_dirty_syncs = yes
#
# Should INBOX be kept up-to-date in the mailbox list index? By default it's
# not, because most of the mailbox accesses will open INBOX anyway.
#mailbox_list_index_include_inbox = no
#
# The minimum number of mails in a mailbox before updates are done to cache
# file. This allows optimizing Dovecot's behavior to do less disk writes at
# the cost of more disk reads.
#mail_cache_min_mail_count = 0
#
# When IDLE command is running, mailbox is checked once in a while to see if
# there are any new mails or other changes. This setting defines the minimum
# time to wait between those checks. Dovecot can also use inotify and
# kqueue to find out immediately when changes occur.
#mailbox_idle_check_interval = 30 secs
#
# Save mails with CR+LF instead of plain LF. This makes sending those mails
# take less CPU, especially with sendfile() syscall with Linux and FreeBSD.
# But it also creates a bit more disk I/O which may just make it slower.
# Also note that if other software reads the mboxes/maildirs, they may handle
# the extra CRs wrong and cause problems.
#mail_save_crlf = no
#
# Max number of mails to keep open and prefetch to memory. This only works with
# some mailbox formats and/or operating systems.
#mail_prefetch_count = 0
#
# How often to scan for stale temporary files and delete them (0 = never).
# These should exist only after Dovecot dies in the middle of saving mails.
#mail_temp_scan_interval = 1w
#
# How many slow mail accesses sorting can perform before it returns failure.
# With IMAP the reply is: NO [LIMIT] Requested sort would have taken too long.
# The untagged SORT reply is still returned, but it's likely not correct.
#mail_sort_max_read_count = 0
#
protocol !indexer-worker {
  # If folder vsize calculation requires opening more than this many mails from
  # disk (i.e. mail sizes aren't in cache already), return failure and finish
  # the calculation via indexer process. Disabled by default. This setting must
  # be 0 for indexer-worker processes.
  #mail_vsize_bg_after_count = 0
}
#
##
## Maildir-specific settings
##
#
# By default LIST command returns all entries in maildir beginning with a dot.
# Enabling this option makes Dovecot return only entries which are directories.
# This is done by stat()ing each entry, so it causes more disk I/O.
# (For systems setting struct dirent->d_type, this check is free and it's
# done always regardless of this setting)
#maildir_stat_dirs = no
#
# When copying a message, do it with hard links whenever possible. This makes
# the performance much better, and it's unlikely to have any side effects.
#maildir_copy_with_hardlinks = yes
#
# Assume Dovecot is the only MUA accessing Maildir: Scan cur/ directory only
# when its mtime changes unexpectedly or when we can't find the mail otherwise.
#maildir_very_dirty_syncs = no
#
# If enabled, Dovecot doesn't use the S=<size> in the Maildir filenames for
# getting the mail's physical size, except when recalculating Maildir++ quota.
# This can be useful in systems where a lot of the Maildir filenames have a
# broken size. The performance hit for enabling this is very small.
#maildir_broken_filename_sizes = no
#
# Always move mails from new/ directory to cur/, even when the \Recent flags
# aren't being reset.
#maildir_empty_new = no
#
##
## mbox-specific settings
##
#
# Which locking methods to use for locking mbox. There are four available:
#  dotlock: Create <mailbox>.lock file. This is the oldest and most NFS-safe
#           solution. If you want to use /var/mail/ like directory, the users
#           will need write access to that directory.
#  dotlock_try: Same as dotlock, but if it fails because of permissions or
#               because there isn't enough disk space, just skip it.
#  fcntl  : Use this if possible. Works with NFS too if lockd is used.
#  flock  : May not exist in all systems. Doesn't work with NFS.
#  lockf  : May not exist in all systems. Doesn't work with NFS.
#
# You can use multiple locking methods; if you do the order they're declared
# in is important to avoid deadlocks if other MTAs/MUAs are using multiple
# locking methods as well. Some operating systems don't allow using some of
# them simultaneously.
#
# The Debian value for mbox_write_locks differs from upstream Dovecot. It is
# changed to be compliant with Debian Policy (section 11.6) for NFS safety.
#       Dovecot: mbox_write_locks = dotlock fcntl
#       Debian:  mbox_write_locks = fcntl dotlock
#
#mbox_read_locks = fcntl
#mbox_write_locks = fcntl dotlock
#
# Maximum time to wait for lock (all of them) before aborting.
#mbox_lock_timeout = 5 mins
#
# If dotlock exists but the mailbox isn't modified in any way, override the
# lock file after this much time.
#mbox_dotlock_change_timeout = 2 mins
#
# When mbox changes unexpectedly we have to fully read it to find out what
# changed. If the mbox is large this can take a long time. Since the change
# is usually just a newly appended mail, it'd be faster to simply read the
# new mails. If this setting is enabled, Dovecot does this but still safely
# fallbacks to re-reading the whole mbox file whenever something in mbox isn't
# how it's expected to be. The only real downside to this setting is that if
# some other MUA changes message flags, Dovecot doesn't notice it immediately.
# Note that a full sync is done with SELECT, EXAMINE, EXPUNGE and CHECK 
# commands.
#mbox_dirty_syncs = yes
#
# Like mbox_dirty_syncs, but don't do full syncs even with SELECT, EXAMINE,
# EXPUNGE or CHECK commands. If this is set, mbox_dirty_syncs is ignored.
#mbox_very_dirty_syncs = no
#
# Delay writing mbox headers until doing a full write sync (EXPUNGE and CHECK
# commands and when closing the mailbox). This is especially useful for POP3
# where clients often delete all mails. The downside is that our changes
# aren't immediately visible to other MUAs.
#mbox_lazy_writes = yes
#
# If mbox size is smaller than this (e.g. 100k), don't write index files.
# If an index file already exists it's still read, just not updated.
#mbox_min_index_size = 0
#
# Mail header selection algorithm to use for MD5 POP3 UIDLs when
# pop3_uidl_format=%m. For backwards compatibility we use apop3d inspired
# algorithm, but it fails if the first Received: header isn't unique in all
# mails. An alternative algorithm is "all" that selects all headers.
#mbox_md5 = apop3d
#
##
## mdbox-specific settings
##
#
# Maximum dbox file size until it's rotated.
#mdbox_rotate_size = 10M
#
# Maximum dbox file age until it's rotated. Typically in days. Day begins
# from midnight, so 1d = today, 2d = yesterday, etc. 0 = check disabled.
#mdbox_rotate_interval = 0
#
# When creating new mdbox files, immediately preallocate their size to
# mdbox_rotate_size. This setting currently works only in Linux with some
# filesystems (ext4, xfs).
#mdbox_preallocate_space = no
#
##
## Mail attachments
##
#
# sdbox and mdbox support saving mail attachments to external files, which
# also allows single instance storage for them. Other backends don't support
# this for now.
#
# Directory root where to store mail attachments. Disabled, if empty.
#mail_attachment_dir =
#
# Attachments smaller than this aren't saved externally. It's also possible to
# write a plugin to disable saving specific attachments externally.
#mail_attachment_min_size = 128k
#
# Filesystem backend to use for saving attachments:
#  posix : No SiS done by Dovecot (but this might help FS's own deduplication)
#  sis posix : SiS with immediate byte-by-byte comparison during saving
#  sis-queue posix : SiS with delayed comparison and deduplication
#mail_attachment_fs = sis posix
#
# Hash format to use in attachment filenames. You can add any text and
# variables: %{md4}, %{md5}, %{sha1}, %{sha256}, %{sha512}, %{size}.
# Variables can be truncated, e.g. %{sha256:80} returns only first 80 bits
#mail_attachment_hash = %{sha1}
#
# Settings to control adding $HasAttachment or $HasNoAttachment keywords.
# By default, all MIME parts with Content-Disposition=attachment, or inlines
# with filename parameter are consired attachments.
#   add-flags-on-save - Add the keywords when saving new mails.
#   content-type=type or !type - Include/exclude content type. Excluding will
#     never consider the matched MIME part as attachment. Including will only
#     negate an exclusion (e.g. content-type=!foo/* content-type=foo/bar).
#   exclude-inlined - Exclude any Content-Disposition=inline MIME part.
#mail_attachment_detection_options =
#
"""
dovecot_10_mail_conf_file = "/etc/dovecot/conf.d/10-mail.conf"

# Dovecot Master Conf
dovecot_10_master_conf = """#default_process_limit = 100
#default_client_limit = 1000
#
# Default VSZ (virtual memory size) limit for service processes. This is mainly
# intended to catch and kill processes that leak memory before they eat up
# everything.
#default_vsz_limit = 256M
#
# Login user is internally used by login processes. This is the most untrusted
# user in Dovecot system. It shouldn't have access to anything at all.
#default_login_user = dovenull
#
# Internal user is used by unprivileged processes. It should be separate from
# login user, so that login processes can't disturb other processes.
#default_internal_user = dovecot
#
service imap-login {
  inet_listener imap {
    #port = 143
  }
  inet_listener imaps {
    #port = 993
    #ssl = yes
  }
  # Number of connections to handle before starting a new process. Typically
  # the only useful values are 0 (unlimited) or 1. 1 is more secure, but 0
  # is faster. <doc/wiki/LoginProcess.txt>
  #service_count = 1
  # Number of processes to always keep waiting for more connections.
  #process_min_avail = 0
  # If you set service_count=0, you probably need to grow this.
  #vsz_limit = $default_vsz_limit
}
#
service pop3-login {
  inet_listener pop3 {
    #port = 110
  }
  inet_listener pop3s {
    #port = 995
    #ssl = yes
  }
}
#
service submission-login {
  inet_listener submission {
    #port = 587
  }
}
#
service lmtp {
  unix_listener /var/spool/postfix/private/dovecot-lmtp {
    group = postfix
    mode = 0600
    user = postfix
  }
  # Create inet listener only if you can't use the above UNIX socket
  #inet_listener lmtp {
    # Avoid making LMTP visible for the entire internet
    #address =
    #port = 
  #}
}
#
service imap {
  # Most of the memory goes to mmap()ing files. You may need to increase this
  # limit if you have huge mailboxes.
  #vsz_limit = $default_vsz_limit
  # Max. number of IMAP processes (connections)
  #process_limit = 1024
}
#
service pop3 {
  # Max. number of POP3 processes (connections)
  #process_limit = 1024
}
service submission {
  # Max. number of SMTP Submission processes (connections)
  #process_limit = 1024
}
service auth {
  # auth_socket_path points to this userdb socket by default. It's typically
  # used by dovecot-lda, doveadm, possibly imap process, etc. Users that have
  # full permissions to this socket are able to get a list of all usernames and
  # get the results of everyone's userdb lookups.
  #
  # The default 0666 mode allows anyone to connect to the socket, but the
  # userdb lookups will succeed only if the userdb returns an "uid" field that
  # matches the caller process's UID. Also if caller's uid or gid matches the
  # socket's uid or gid the lookup succeeds. Anything else causes a failure.
  #
  # To give the caller full permissions to lookup all users, set the mode to
  # something else than 0666 and Dovecot lets the kernel enforce the
  # permissions (e.g. 0777 allows everyone full permissions).
  unix_listener auth-userdb {
    #mode = 0666
    #user = 
    #group = 
  }
  #
  # Postfix smtp-auth
  unix_listener /var/spool/postfix/private/auth {
    mode = 0660
    user = postfix
    group = postfix
  }
  #
  # Auth process is run as this user.
  #user = $default_internal_user
}
#
service auth-worker {
  # Auth worker process is run as root by default, so that it can access
  # /etc/shadow. If this isn't necessary, the user should be changed to
  # $default_internal_user.
  #user = root
}
#
service dict {
  # If dict proxy is used, mail processes should have access to its socket.
  # For example: mode=0660, group=vmail and global mail_access_groups=vmail
  unix_listener dict {
    #mode = 0600
    #user = 
    #group = 
  }
}
"""
dovecot_10_master_conf_file = "/etc/dovecot/conf.d/10-master.conf"

# Dovecot SSL conf
dovecot_10_ssl_conf = """##
## SSL settings
##
#
# SSL/TLS support: yes, no, required. <doc/wiki/SSL.txt>
ssl = required
#
# PEM encoded X.509 SSL/TLS certificate and private key. They're opened before
# dropping root privileges, so keep the key file unreadable by anyone but
# root. Included doc/mkcert.sh can be used to easily generate self-signed
# certificate, just make sure to update the domains in dovecot-openssl.cnf
#________________________________________________________________________
ssl_cert = </etc/letsencrypt/live/""" + hostname + """/fullchain.pem
ssl_key = </etc/letsencrypt/live/""" + hostname + """/privkey.pem
#________________________________________________________________________
#
# If key file is password protected, give the password here. Alternatively
# give it when starting dovecot with -p parameter. Since this file is often
# world-readable, you may want to place this setting instead to a different
# root owned 0600 file by using ssl_key_password = <path.
#ssl_key_password =
#
# PEM encoded trusted certificate authority. Set this only if you intend to use
# ssl_verify_client_cert=yes. The file should contain the CA certificate(s)
# followed by the matching CRL(s). (e.g. ssl_ca = </etc/ssl/certs/ca.pem)
#ssl_ca = 
#
# Require that CRL check succeeds for client certificates.
#ssl_require_crl = yes
#
# Directory and/or file for trusted SSL CA certificates. These are used only
# when Dovecot needs to act as an SSL client (e.g. imapc backend or
# submission service). The directory is usually /etc/ssl/certs in
# Debian-based systems and the file is /etc/pki/tls/cert.pem in
# RedHat-based systems.
ssl_client_ca_dir = /etc/ssl/certs
#ssl_client_ca_file =
#
# Require valid cert when connecting to a remote server
#ssl_client_require_valid_cert = yes
#
# Request client to send a certificate. If you also want to require it, set
# auth_ssl_require_client_cert=yes in auth section.
#ssl_verify_client_cert = no
#
# Which field from certificate to use for username. commonName and
# x500UniqueIdentifier are the usual choices. You'll also need to set
# auth_ssl_username_from_cert=yes.
#ssl_cert_username_field = commonName
#
# SSL DH parameters
# Generate new params with `openssl dhparam -out /etc/dovecot/dh.pem 4096`
# Or migrate from old ssl-parameters.dat file with the command dovecot
# gives on startup when ssl_dh is unset.
ssl_dh = </usr/share/dovecot/dh.pem
#
# Minimum SSL protocol version to use. Potentially recognized values are SSLv3,
# TLSv1, TLSv1.1, and TLSv1.2, depending on the OpenSSL version used.
#ssl_min_protocol = TLSv1
#
# SSL ciphers to use, the default is:
#ssl_cipher_list = ALL:!kRSA:!SRP:!kDHd:!DSS:!aNULL:!eNULL:!EXPORT:!DES:!3DES:!MD5:!PSK:!RC4:!ADH:!LOW@STRENGTH
# To disable non-EC DH, use:
#ssl_cipher_list = ALL:!DH:!kRSA:!SRP:!kDHd:!DSS:!aNULL:!eNULL:!EXPORT:!DES:!3DES:!MD5:!PSK:!RC4:!ADH:!LOW@STRENGTH
#
# Colon separated list of elliptic curves to use. Empty value (the default)
# means use the defaults from the SSL library. P-521:P-384:P-256 would be an
# example of a valid value.
#ssl_curve_list =
#
# Prefer the server's order of ciphers over client's.
#ssl_prefer_server_ciphers = no
#
# SSL crypto device to use, for valid values run "openssl engine"
#ssl_crypto_device =
#
# SSL extra options. Currently supported options are:
#   compression - Enable compression.
#   no_ticket - Disable SSL session tickets.
#ssl_options =
"""
dovecot_10_ssl_conf_file = "/etc/dovecot/conf.d/10-ssl.conf"

# Dovecot - SQL connection
dovecot_sql_conf_ext = """driver = mysql
connect = host=127.0.0.1 dbname=mailserver user=mailserver password=""" + mailserverpw + """
user_query = SELECT email as user, \
  concat('*:bytes=', quota) AS quota_rule, \
  '/var/vmail/%d/%n' AS home, \
  5000 AS uid, 5000 AS gid \
  FROM virtual_users WHERE email='%u'
password_query = SELECT password FROM virtual_users WHERE email='%u'
iterate_query = SELECT email AS user FROM virtual_users
"""
dovecot_sql_conf_ext_file = "/etc/dovecot/dovecot-sql.conf.ext"

# Dovecot LMTP Conf
dovecot_20_lmtp_conf = """##
## LMTP specific settings
##
#
# Support proxying to other LMTP/SMTP servers by performing passdb lookups.
#lmtp_proxy = no
#
# When recipient address includes the detail (e.g. user+detail), try to save
# the mail to the detail mailbox. See also recipient_delimiter and
# lda_mailbox_autocreate settings.
#lmtp_save_to_detail_mailbox = no
#
# Verify quota before replying to RCPT TO. This adds a small overhead.
#lmtp_rcpt_check_quota = no
#
# Which recipient address to use for Delivered-To: header and Received:
# header. The default is "final", which is the same as the one given to
# RCPT TO command. "original" uses the address given in RCPT TO's ORCPT
# parameter, "none" uses nothing. Note that "none" is currently always used
# when a mail has multiple recipients.
#lmtp_hdr_delivery_address = final
#
protocol lmtp {
  # Space separated list of plugins to load (default is global mail_plugins).
  mail_plugins = $mail_plugins sieve
}
"""
dovecot_20_lmtp_conf_file = "/etc/dovecot/conf.d/20-lmtp.conf"

# Dovecot Quota Conf
dovecot_90_quota_conf = """##
## Quota configuration.
##
# Note that you also have to enable quota plugin in mail_plugins setting.
# <doc/wiki/Quota.txt>
##
## Quota limits
##
# Quota limits are set using "quota_rule" parameters. To get per-user quota
# limits, you can set/override them by returning "quota_rule" extra field
# from userdb. It's also possible to give mailbox-specific limits, for example
# to give additional 100 MB when saving to Trash:
plugin {
  #quota_rule = *:storage=1G
  #quota_rule2 = Trash:storage=+100M
  #
  # LDA/LMTP allows saving the last mail to bring user from under quota to
  # over quota, if the quota doesn't grow too high. Default is to allow as
  # long as quota will stay under 10% above the limit. Also allowed e.g. 10M.
  #quota_grace = 10%%
  #
  # Quota plugin can also limit the maximum accepted mail size.
  #quota_max_mail_size = 100M
}
#
##
## Quota warnings
##
#
# You can execute a given command when user exceeds a specified quota limit.
# Each quota root has separate limits. Only the command for the first
# exceeded limit is executed, so put the highest limit first.
# The commands are executed via script service by connecting to the named
# UNIX socket (quota-warning below).
# Note that % needs to be escaped as %%, otherwise "% " expands to empty.
#
plugin {
  #quota_warning = storage=95%% quota-warning 95 %u
  #quota_warning2 = storage=80%% quota-warning 80 %u
}
#
# Example quota-warning service. The unix listener's permissions should be
# set in a way that mail processes can connect to it. Below example assumes
# that mail processes run as vmail user. If you use mode=0666, all system users
# can generate quota warnings to anyone.
#service quota-warning {
#  executable = script /usr/local/bin/quota-warning.sh
#  user = dovecot
#  unix_listener quota-warning {
#    user = vmail
#  }
#}
#
##
## Quota backends
##
#
# Multiple backends are supported:
#   dirsize: Find and sum all the files found from mail directory.
#            Extremely SLOW with Maildir. It'll eat your CPU and disk I/O.
#   dict: Keep quota stored in dictionary (eg. SQL)
#   maildir: Maildir++ quota
#   fs: Read-only support for filesystem quota
#
plugin {
  #quota = dirsize:User quota
  #quota = maildir:User quota
  #quota = dict:User quota::proxy::quota
  #quota = fs:User quota
}
#
# Multiple quota roots are also possible, for example this gives each user
# their own 100MB quota and one shared 1GB quota within the domain:
plugin {
  #quota = dict:user::proxy::quota
  #quota2 = dict:domain:%d:proxy::quota_domain
  #quota_rule = *:storage=102400
  #quota2_rule = *:storage=1048576
}
#
plugin {
  quota = maildir:User quota
  quota_status_success = DUNNO
  quota_status_nouser = DUNNO
  quota_status_overquota = "452 4.2.2 Mailbox is full and cannot receive any more emails"
}
#
service quota-status {
  executable = /usr/lib/dovecot/quota-status -p postfix
  unix_listener /var/spool/postfix/private/quota-status {
    user = postfix
  }
}
#
plugin {
   quota_warning = storage=95%% quota-warning 95 %u
   quota_warning2 = storage=80%% quota-warning 80 %u
   quota_warning3 = -storage=100%% quota-warning below %u
}
service quota-warning {
   executable = script /usr/local/bin/quota-warning.sh
   unix_listener quota-warning {
     group = dovecot
     mode = 0660
   }
}
"""
dovecot_90_quota_conf_file = "/etc/dovecot/conf.d/90-quota.conf"

# Shell script for sending quota warning mail
dovecot_quota_warning = """
#!/bin/sh
PERCENT=$1
USER=$2
cat << EOF | /usr/lib/dovecot/dovecot-lda -d $USER -o "plugin/quota=maildir:User quota:noenforcing"
From: postmaster@""" + hostname + """
Subject: Quota warning - $PERCENT% reached

Your mailbox can only store a limited amount of emails.
Currently it is $PERCENT% full. If you reach 100% then
new emails cannot be stored. Thanks for your understanding.
EOF
"""
dovecot_quota_warning_file = "/usr/local/bin/quota-warning.sh"
#------------------- dovecot_config definitions END-------------------

#------------------- roundcube_config definitions BEGIN-------------------
# Roundcube Main Config PHP file
roundcube_main_config = """<?php
/*
+-----------------------------------------------------------------------+
| Local configuration for the Roundcube Webmail installation.           |
|                                                                       |
| This is a sample configuration file only containing the minimum       |
| setup required for a functional installation. Copy more options       |
| from defaults.inc.php to this file to override the defaults.          |
|                                                                       |
| This file is part of the Roundcube Webmail client                     |
| Copyright (C) The Roundcube Dev Team                                  |
|                                                                       |
| Licensed under the GNU General Public License version 3 or            |
| any later version with exceptions for skins & plugins.                |
| See the README file for a full license statement.                     |
+-----------------------------------------------------------------------+
*/
//
$config = array();
//
// Do not set db_dsnw here, use dpkg-reconfigure roundcube-core to configure database!
include_once("/etc/roundcube/debian-db-roundcube.php");
//
// The IMAP host chosen to perform the log-in.
// Leave blank to show a textbox at login, give a list of hosts
// to display a pulldown menu or set one host as string.
// Enter hostname with prefix ssl:// to use Implicit TLS, or use
// prefix tls:// to use STARTTLS.
// Supported replacement variables:
// %n - hostname ($_SERVER['SERVER_NAME'])
// %t - hostname without the first part
// %d - domain (http hostname $_SERVER['HTTP_HOST'] without the first part)
// %s - domain name after the '@' from e-mail address provided at login screen
// For example %n = mail.domain.tld, %t = domain.tld
$config['default_host'] = 'tls://""" + hostname + """';
//
// SMTP server host (for sending mails).
// Enter hostname with prefix ssl:// to use Implicit TLS, or use
// prefix tls:// to use STARTTLS.
// Supported replacement variables:
// %h - user's IMAP hostname
// %n - hostname ($_SERVER['SERVER_NAME'])
// %t - hostname without the first part
// %d - domain (http hostname $_SERVER['HTTP_HOST'] without the first part)
// %z - IMAP domain (IMAP hostname without the first part)
// For example %n = mail.domain.tld, %t = domain.tld
$config['smtp_server'] = 'tls://""" + hostname + """';
//
// SMTP port. Use 25 for cleartext, 465 for Implicit TLS, or 587 for STARTTLS (default)
$config['smtp_port'] = 587;
//
// SMTP username (if required) if you use %u as the username Roundcube
// will use the current username for login
$config['smtp_user'] = '%u';
//
// SMTP password (if required) if you use %p as the password Roundcube
// will use the current user's password for login
$config['smtp_pass'] = '%p';
//
// provide an URL where a user can get support for this Roundcube installation
// PLEASE DO NOT LINK TO THE ROUNDCUBE.NET WEBSITE HERE!
$config['support_url'] = '';
//
// Name your service. This is displayed on the login screen and in the window title
$config['product_name'] = 'Roundcube Webmail';
//
// this key is used to encrypt the users imap password which is stored
// in the session record (and the client cookie if remember password is enabled).
// please provide a string of exactly 24 chars.
// YOUR KEY MUST BE DIFFERENT THAN THE SAMPLE VALUE FOR SECURITY REASONS
$config['des_key'] = '2LHAAfbC[rMM]5YHUd28Asqi';
//
// List of active plugins (in plugins/ directory)
// Debian: install roundcube-plugins first to have any
$config['plugins'] = array(
     'managesieve',
     'password',
);
//
// skin name: folder from skins/
$config['skin'] = 'elastic';
//
// Disable spellchecking
// Debian: spellshecking needs additional packages to be installed, or calling external APIs
//         see defaults.inc.php for additional informations
$config['enable_spellcheck'] = false;
"""
roundcube_main_config_file = "/etc/roundcube/config.inc.php"

# Roundcube Password Config to connect to mariadb
roundcube_password_config = """<?php
// Empty configuration for password
// See /usr/share/roundcube/plugins/password/config.inc.php.dist for instructions
// Check the access right of the file if you put sensitive information in it.
$config['password_driver'] = 'sql';
$config['password_minimum_length'] = 12;
$config['password_force_save'] = true;
$config['password_algorithm'] = 'dovecot';
$config['password_dovecotpw'] = '/usr/bin/doveadm pw -s BLF-CRYPT';
$config['password_dovecotpw_method'] = 'BLF-CRYPT';
$config['password_dovecotpw_with_method'] = true;
$config['password_db_dsn'] = 'mysql://mailadmin:""" + mailadminpw + """@localhost/mailserver';
$config['password_query'] = "UPDATE virtual_users SET password=%D WHERE email=%u";
?>
"""
roundcube_password_config_file = "/etc/roundcube/plugins/password/config.inc.php"

# Roundcube Managesieve Config
roundcube_managesieve_config = """<?php
// Empty configuration for managesieve
// See /usr/share/roundcube/plugins/managesieve/config.inc.php.dist for instructions
// Check the access right of the file if you put sensitive information in it.
$config['managesieve_host'] = 'localhost';
?>
"""
roundcube_managesieve_config_file = "/etc/roundcube/plugins/managesieve/config.inc.php"
#------------------- roundcube_config definitions END-------------------


#------------------- postfix_config definitions BEGIN-------------------
# Postfix Master Config to send emails

postfix_master_config = """#
# Postfix master process configuration file.  For details on the format
# of the file, see the master(5) manual page (command: "man 5 master" or
# on-line: http://www.postfix.org/master.5.html).
#
# Do not forget to execute "postfix reload" after editing this file.
#
# ==========================================================================
# service type  private unpriv  chroot  wakeup  maxproc command + args
#               (yes)   (yes)   (no)    (never) (100)
# ==========================================================================
smtp      inet  n       -       y       -       -       smtpd
#smtp      inet  n       -       y       -       1       postscreen
#smtpd     pass  -       -       y       -       -       smtpd
#dnsblog   unix  -       -       y       -       0       dnsblog
#tlsproxy  unix  -       -       y       -       0       tlsproxy
submission inet n       -       y       -       -       smtpd
  -o syslog_name=postfix/submission
  -o smtpd_tls_security_level=encrypt
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_tls_auth_only=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_client_restrictions=$mua_client_restrictions
  -o smtpd_helo_restrictions=$mua_helo_restrictions
  -o smtpd_sender_restrictions=$mua_sender_restrictions
  -o smtpd_recipient_restrictions=
  -o smtpd_relay_restrictions=permit_sasl_authenticated,reject
  -o milter_macro_daemon_name=ORIGINATING
#smtps     inet  n       -       y       -       -       smtpd
#  -o syslog_name=postfix/smtps
#  -o smtpd_tls_wrappermode=yes
#  -o smtpd_sasl_auth_enable=yes
#  -o smtpd_reject_unlisted_recipient=no
#  -o smtpd_client_restrictions=$mua_client_restrictions
#  -o smtpd_helo_restrictions=$mua_helo_restrictions
#  -o smtpd_sender_restrictions=$mua_sender_restrictions
#  -o smtpd_recipient_restrictions=
#  -o smtpd_relay_restrictions=permit_sasl_authenticated,reject
#  -o milter_macro_daemon_name=ORIGINATING
#628       inet  n       -       y       -       -       qmqpd
pickup    unix  n       -       y       60      1       pickup
cleanup   unix  n       -       y       -       0       cleanup
qmgr      unix  n       -       n       300     1       qmgr
#qmgr     unix  n       -       n       300     1       oqmgr
tlsmgr    unix  -       -       y       1000?   1       tlsmgr
rewrite   unix  -       -       y       -       -       trivial-rewrite
bounce    unix  -       -       y       -       0       bounce
defer     unix  -       -       y       -       0       bounce
trace     unix  -       -       y       -       0       bounce
verify    unix  -       -       y       -       1       verify
flush     unix  n       -       y       1000?   0       flush
proxymap  unix  -       -       n       -       -       proxymap
proxywrite unix -       -       n       -       1       proxymap
smtp      unix  -       -       y       -       -       smtp
relay     unix  -       -       y       -       -       smtp
        -o syslog_name=postfix/$service_name
#       -o smtp_helo_timeout=5 -o smtp_connect_timeout=5
showq     unix  n       -       y       -       -       showq
error     unix  -       -       y       -       -       error
retry     unix  -       -       y       -       -       error
discard   unix  -       -       y       -       -       discard
local     unix  -       n       n       -       -       local
virtual   unix  -       n       n       -       -       virtual
lmtp      unix  -       -       y       -       -       lmtp
anvil     unix  -       -       y       -       1       anvil
scache    unix  -       -       y       -       1       scache
postlog   unix-dgram n  -       n       -       1       postlogd
#
# ====================================================================
# Interfaces to non-Postfix software. Be sure to examine the manual
# pages of the non-Postfix software to find out what options it wants.
#
# Many of the following services use the Postfix pipe(8) delivery
# agent.  See the pipe(8) man page for information about ${recipient}
# and other message envelope options.
# ====================================================================
#
# maildrop. See the Postfix MAILDROP_README file for details.
# Also specify in main.cf: maildrop_destination_recipient_limit=1
#
maildrop  unix  -       n       n       -       -       pipe
  flags=DRhu user=vmail argv=/usr/bin/maildrop -d ${recipient}
#
# ====================================================================
#
# Recent Cyrus versions can use the existing "lmtp" master.cf entry.
#
# Specify in cyrus.conf:
#   lmtp    cmd="lmtpd -a" listen="localhost:lmtp" proto=tcp4
#
# Specify in main.cf one or more of the following:
#  mailbox_transport = lmtp:inet:localhost
#  virtual_transport = lmtp:inet:localhost
#
# ====================================================================
#
# Cyrus 2.1.5 (Amos Gouaux)
# Also specify in main.cf: cyrus_destination_recipient_limit=1
#
#cyrus     unix  -       n       n       -       -       pipe
#  user=cyrus argv=/cyrus/bin/deliver -e -r ${sender} -m ${extension} ${user}
#
# ====================================================================
# Old example of delivery via Cyrus.
#
#old-cyrus unix  -       n       n       -       -       pipe
#  flags=R user=cyrus argv=/cyrus/bin/deliver -e -m ${extension} ${user}
#
# ====================================================================
#
# See the Postfix UUCP_README file for configuration details.
#
uucp      unix  -       n       n       -       -       pipe
  flags=Fqhu user=uucp argv=uux -r -n -z -a$sender - $nexthop!rmail ($recipient)
#
# Other external delivery methods.
#
ifmail    unix  -       n       n       -       -       pipe
  flags=F user=ftn argv=/usr/lib/ifmail/ifmail -r $nexthop ($recipient)
bsmtp     unix  -       n       n       -       -       pipe
  flags=Fq. user=bsmtp argv=/usr/lib/bsmtp/bsmtp -t$nexthop -f$sender $recipient
scalemail-backend unix	-	n	n	-	2	pipe
  flags=R user=scalemail argv=/usr/lib/scalemail/bin/scalemail-store ${nexthop} ${user} ${extension}
mailman   unix  -       n       n       -       -       pipe
  flags=FR user=list argv=/usr/lib/mailman/bin/postfix-to-mailman.py
  ${nexthop} ${user}

"""
postfix_master_config_file = "/etc/postfix/master.cf"
#------------------- postfix_config definitions END-------------------

#------------------- rspamd_config definitions BEGIN-------------------
# To enable Spam headers
rspamd_milter_headers = "extended_spam_headers = true;"
rspamd_milter_headers_file = "/etc/rspamd/override.d/milter_headers.conf"

# Dovecot Sieve configs
dovecot_90_sieve_conf = """##
## Settings for the Sieve interpreter
##
# Do not forget to enable the Sieve plugin in 15-lda.conf and 20-lmtp.conf
# by adding it to the respective mail_plugins= settings.
# The Sieve interpreter can retrieve Sieve scripts from several types of
# locations. The default `file' location type is a local filesystem path
# pointing to a Sieve script file or a directory containing multiple Sieve
# script files. More complex setups can use other location types such as
# `ldap' or `dict' to fetch Sieve scripts from remote databases.
#
# All settings that specify the location of one ore more Sieve scripts accept
# the following syntax:
#
# location = [<type>:]path[;<option>[=<value>][;...]]
#
# If the type prefix is omitted, the script location type is 'file' and the 
# location is interpreted as a local filesystem path pointing to a Sieve script
# file or directory. Refer to Pigeonhole wiki or INSTALL file for more
# information.
plugin {
  # The location of the user's main Sieve script or script storage. The LDA
  # Sieve plugin uses this to find the active script for Sieve filtering at
  # delivery. The "include" extension uses this location for retrieving
  # :personal" scripts. This is also where the  ManageSieve service will store
  # the user's scripts, if supported.
  # 
  # Currently only the 'file:' location type supports ManageSieve operation.
  # Other location types like 'dict:' and 'ldap:' can currently only
  # be used as a read-only script source ().
  #
  # For the 'file:' type: use the ';active=' parameter to specify where the
  # active script symlink is located.
  # For other types: use the ';name=' parameter to specify the name of the
  # default/active script.
  sieve = file:~/sieve;active=~/.dovecot.sieve
  #
  # The default Sieve script when the user has none. This is the location of a
  # global sieve script file, which gets executed ONLY if user's personal Sieve
  # script doesn't exist. Be sure to pre-compile this script manually using the
  # sievec command line tool if the binary is not stored in a global location.
  # --> See sieve_before for executing scripts before the user's personal
  #     script.
  #sieve_default = /var/lib/dovecot/sieve/default.sieve
  #
  # The name by which the default Sieve script (as configured by the 
  # sieve_default setting) is visible to the user through ManageSieve. 
  #sieve_default_name = 
  #
  # Location for ":global" include scripts as used by the "include" extension.
  #sieve_global =
  #
  # The location of a Sieve script that is run for any message that is about to
  # be discarded; i.e., it is not delivered anywhere by the normal Sieve
  # execution. This only happens when the "implicit keep" is canceled, by e.g.
  # the "discard" action, and no actions that deliver the message are executed.
  # This "discard script" can prevent discarding the message, by executing
  # alternative actions. If the discard script does nothing, the message is
	# still discarded as it would be when no discard script is configured.
  #sieve_discard =
  #
  # Location Sieve of scripts that need to be executed before the user's
  # personal script. If a 'file' location path points to a directory, all the 
  # Sieve scripts contained therein (with the proper `.sieve' extension) are
  # executed. The order of execution within that directory is determined by the
  # file names, using a normal 8bit per-character comparison.
  #
  # Multiple script locations can be specified by appending an increasing number
  # to the setting name. The Sieve scripts found from these locations are added
  # to the script execution sequence in the specified order. Reading the
  # numbered sieve_before settings stops at the first missing setting, so no
  # numbers may be skipped.
  #sieve_before = /var/lib/dovecot/sieve.d/
  #sieve_before2 = ldap:/etc/sieve-ldap.conf;name=ldap-domain
  #sieve_before3 = (etc...)
  #
  # Identical to sieve_before, only the specified scripts are executed after the
  # user's script (only when keep is still in effect!). Multiple script
  # locations can be specified by appending an increasing number.
  #sieve_after =
  #sieve_after2 =
  #sieve_after2 = (etc...)
  sieve_after = /etc/dovecot/sieve-after
  # Which Sieve language extensions are available to users. By default, all
  # supported extensions are available, except for deprecated extensions or
  # those that are still under development. Some system administrators may want
  # to disable certain Sieve extensions or enable those that are not available
  # by default. This setting can use '+' and '-' to specify differences relative
  # to the default. For example `sieve_extensions = +imapflags' will enable the
  # deprecated imapflags extension in addition to all extensions were already
  # enabled by default.
  #sieve_extensions = +notify +imapflags
  #
  # Which Sieve language extensions are ONLY available in global scripts. This
  # can be used to restrict the use of certain Sieve extensions to administrator
  # control, for instance when these extensions can cause security concerns.
  # This setting has higher precedence than the `sieve_extensions' setting
  # (above), meaning that the extensions enabled with this setting are never
  # available to the user's personal script no matter what is specified for the
  # `sieve_extensions' setting. The syntax of this setting is similar to the
  # `sieve_extensions' setting, with the difference that extensions are
  # enabled or disabled for exclusive use in global scripts. Currently, no
  # extensions are marked as such by default.
  #sieve_global_extensions =
  #
  # The Pigeonhole Sieve interpreter can have plugins of its own. Using this
  # setting, the used plugins can be specified. Check the Dovecot wiki
  # (wiki2.dovecot.org) or the pigeonhole website
  # (http://pigeonhole.dovecot.org) for available plugins.
  # The sieve_extprograms plugin is included in this release.
  #sieve_plugins =
  #
  # The maximum size of a Sieve script. The compiler will refuse to compile any
  # script larger than this limit. If set to 0, no limit on the script size is
  # enforced.
  #sieve_max_script_size = 1M
  #
  # The maximum number of actions that can be performed during a single script
  # execution. If set to 0, no limit on the total number of actions is enforced.
  #sieve_max_actions = 32
  #
  # The maximum number of redirect actions that can be performed during a single
  # script execution. If set to 0, no redirect actions are allowed.
  #sieve_max_redirects = 4
  #
  # The maximum number of personal Sieve scripts a single user can have. If set
  # to 0, no limit on the number of scripts is enforced.
  # (Currently only relevant for ManageSieve)
  #sieve_quota_max_scripts = 0
  #
  # The maximum amount of disk storage a single user's scripts may occupy. If
  # set to 0, no limit on the used amount of disk storage is enforced.
  # (Currently only relevant for ManageSieve)
  #sieve_quota_max_storage = 0
  #
  # The primary e-mail address for the user. This is used as a default when no
  # other appropriate address is available for sending messages. If this setting
  # is not configured, either the postmaster or null "<>" address is used as a
  # sender, depending on the action involved. This setting is important when
  # there is no message envelope to extract addresses from, such as when the
  # script is executed in IMAP.
  #sieve_user_email =
  #
  # The path to the file where the user log is written. If not configured, a
  # default location is used. If the main user's personal Sieve (as configured
  # with sieve=) is a file, the logfile is set to <filename>.log by default. If
  # it is not a file, the default user log file is ~/.dovecot.sieve.log.
  #sieve_user_log =
  #
  # Specifies what envelope sender address is used for redirected messages.
  # The following values are supported for this setting:
  #
  #   "sender"         - The sender address is used (default).
  #   "recipient"      - The final recipient address is used.
  #   "orig_recipient" - The original recipient is used.
  #   "user_email"     - The user's primary address is used. This is
  #                      configured with the "sieve_user_email" setting. If
  #                      that setting is unconfigured, "user_mail" is equal to
  #                      "recipient".
  #   "postmaster"     - The postmaster_address configured for the LDA.
  #   "<user@domain>"  - Redirected messages are always sent from user@domain.
  #                      The angle brackets are mandatory. The null "<>" address
  #                      is also supported.
  #
  # This setting is ignored when the envelope sender is "<>". In that case the
  # sender of the redirected message is also always "<>".
  #sieve_redirect_envelope_from = sender
  #
  ## TRACE DEBUGGING
  # Trace debugging provides detailed insight in the operations performed by
  # the Sieve script. These settings apply to both the LDA Sieve plugin and the
  # IMAPSIEVE plugin. 
  #
  # WARNING: On a busy server, this functionality can quickly fill up the trace
  # directory with a lot of trace files. Enable this only temporarily and as
  # selective as possible.
  #  
  # The directory where trace files are written. Trace debugging is disabled if
  # this setting is not configured or if the directory does not exist. If the 
  # path is relative or it starts with "~/" it is interpreted relative to the
  # current user's home directory.
  #sieve_trace_dir =
  #  
  # The verbosity level of the trace messages. Trace debugging is disabled if
  # this setting is not configured. Possible values are:
  #
  #   "actions"        - Only print executed action commands, like keep,
  #                      fileinto, reject and redirect.
  #   "commands"       - Print any executed command, excluding test commands.
  #   "tests"          - Print all executed commands and performed tests.
  #   "matching"       - Print all executed commands, performed tests and the
  #                      values matched in those tests.
  #sieve_trace_level =
  #  
  # Enables highly verbose debugging messages that are usually only useful for
  # developers.
  #sieve_trace_debug = no
  #  
  # Enables showing byte code addresses in the trace output, rather than only
  # the source line numbers.
  #sieve_trace_addresses = no 
  imapsieve_mailbox1_name = Junk
  imapsieve_mailbox1_causes = COPY
  imapsieve_mailbox1_before = file:/etc/dovecot/sieve/learn-spam.sieve
  # From Junk folder to elsewhere
  imapsieve_mailbox2_name = *
  imapsieve_mailbox2_from = Junk
  imapsieve_mailbox2_causes = COPY
  imapsieve_mailbox2_before = file:/etc/dovecot/sieve/learn-ham.sieve
  sieve_pipe_bin_dir = /etc/dovecot/sieve
  sieve_global_extensions = +vnd.dovecot.pipe
  sieve_plugins = sieve_imapsieve sieve_extprograms
}
"""
dovecot_90_sieve_conf_file = "/etc/dovecot/conf.d/90-sieve.conf"

# Config for moving an email with spam header to Junk
dovecot_spam_to_folder_sieve = """require ["fileinto","mailbox"];
if header :contains "X-Spam" "Yes" {
 fileinto :create "Junk";
 stop;
}
"""
dovecot_spam_to_folder_sieve_file = "/etc/dovecot/sieve-after/spam-to-folder.sieve"

# Enabling spam learning system wide
rspamd_override_bayes = "autolearn = true;"
rspamd_override_bayes_file = "/etc/rspamd/override.d/classifier-bayes.conf"

# Enabling user based spam learning
rspamd_local_bayes = "users_enabled = true;"
rspamd_local_bayes_file = "/etc/rspamd/local.d/classifier-bayes.conf"

# Dovecot IMAP Conf
dovecot_20_imap_conf = """
## IMAP specific settings
##
# If nothing happens for this long while client is IDLEing, move the connection
# to imap-hibernate process and close the old imap process. This saves memory,
# because connections use very little memory in imap-hibernate process. The
# downside is that recreating the imap process back uses some resources.
#imap_hibernate_timeout = 0
#
# Maximum IMAP command line length. Some clients generate very long command
# lines with huge mailboxes, so you may need to raise this if you get
# "Too long argument" or "IMAP command line too large" errors often.
#imap_max_line_length = 64k
#
# IMAP logout format string:
#  %i - total number of bytes read from client
#  %o - total number of bytes sent to client
#  %{fetch_hdr_count} - Number of mails with mail header data sent to client
#  %{fetch_hdr_bytes} - Number of bytes with mail header data sent to client
#  %{fetch_body_count} - Number of mails with mail body data sent to client
#  %{fetch_body_bytes} - Number of bytes with mail body data sent to client
#  %{deleted} - Number of mails where client added \Deleted flag
#  %{expunged} - Number of mails that client expunged, which does not
#                include automatically expunged mails
#  %{autoexpunged} - Number of mails that were automatically expunged after
#                    client disconnected
#  %{trashed} - Number of mails that client copied/moved to the
#               special_use=\Trash mailbox.
#  %{appended} - Number of mails saved during the session
#imap_logout_format = in=%i out=%o deleted=%{deleted} expunged=%{expunged} \
#  trashed=%{trashed} hdr_count=%{fetch_hdr_count} \
#  hdr_bytes=%{fetch_hdr_bytes} body_count=%{fetch_body_count} \
#  body_bytes=%{fetch_body_bytes}
#
# Override the IMAP CAPABILITY response. If the value begins with '+',
# add the given capabilities on top of the defaults (e.g. +XFOO XBAR).
#imap_capability = 
#
# How long to wait between "OK Still here" notifications when client is
# IDLEing.
#imap_idle_notify_interval = 2 mins
#
# ID field names and values to send to clients. Using * as the value makes
# Dovecot use the default value. The following fields have default values
# currently: name, version, os, os-version, support-url, support-email.
#imap_id_send = 
#
# ID fields sent by client to log. * means everything.
#imap_id_log =
#
# Workarounds for various client bugs:
#   delay-newmail:
#     Send EXISTS/RECENT new mail notifications only when replying to NOOP
#     and CHECK commands. Some clients ignore them otherwise, for example OSX
#     Mail (<v2.1). Outlook Express breaks more badly though, without this it
#     may show user "Message no longer in server" errors. Note that OE6 still
#     breaks even with this workaround if synchronization is set to
#     "Headers Only".
#   tb-extra-mailbox-sep:
#     Thunderbird gets somehow confused with LAYOUT=fs (mbox and dbox) and
#     adds extra '/' suffixes to mailbox names. This option causes Dovecot to
#     ignore the extra '/' instead of treating it as invalid mailbox name.
#   tb-lsub-flags:
#     Show \\Noselect flags for LSUB replies with LAYOUT=fs (e.g. mbox).
#     This makes Thunderbird realize they aren't selectable and show them
#     greyed out, instead of only later giving "not selectable" popup error.
#
# The list is space-separated.
#imap_client_workarounds = 
#
# Host allowed in URLAUTH URLs sent by client. "*" allows all.
#imap_urlauth_host =
#
# Enable IMAP LITERAL- extension (replaces LITERAL+)
#imap_literal_minus = no
#
# What happens when FETCH fails due to some internal error:
#   disconnect-immediately:
#     The FETCH is aborted immediately and the IMAP client is disconnected.
#   disconnect-after:
#     The FETCH runs for all the requested mails returning as much data as
#     possible. The client is finally disconnected without a tagged reply.
#   no-after:
#     Same as disconnect-after, but tagged NO reply is sent instead of
#     disconnecting the client. If the client attempts to FETCH the same failed
#     mail more than once, the client is disconnected. This is to avoid clients
#     from going into infinite loops trying to FETCH a broken mail.
#imap_fetch_failure = disconnect-immediately
#
protocol imap {
  # Space separated list of plugins to load (default is global mail_plugins).
  mail_plugins = $mail_plugins imap_sieve
  #
  # Maximum number of IMAP connections allowed for a user from each IP address.
  # NOTE: The username is compared case-sensitively.
  #mail_max_userip_connections = 10
}
"""
dovecot_20_imap_conf_file = "/etc/dovecot/conf.d/20-imap.conf"

# Dovecot Learn Spam and Learn Ham configs
dovecot_learn_spam_sieve = """require ["vnd.dovecot.pipe", "copy", "imapsieve"];
pipe :copy "rspamd-learn-spam.sh";
"""
dovecot_learn_spam_sieve_file = "/etc/dovecot/sieve/learn-spam.sieve"
dovecot_learn_ham_sieve = """require ["vnd.dovecot.pipe", "copy", "imapsieve", "variables"];
if string "${mailbox}" "Trash" {
  stop;
}
pipe :copy "rspamd-learn-ham.sh";
"""
dovecot_learn_ham_sieve_file = "/etc/dovecot/sieve/learn-ham.sieve"

# Rspamd Learn Spam and Learn Ham shell scripts
rspamd_learn_spam = """#!/bin/sh
exec /usr/bin/rspamc learn_spam
"""
rspamd_learn_spam_file = "/etc/dovecot/sieve/rspamd-learn-spam.sh"
rspamd_learn_ham = """#!/bin/sh
exec /usr/bin/rspamc learn_ham
"""
rspamd_learn_ham_file = "/etc/dovecot/sieve/rspamd-learn-ham.sh"

# Dovecot Mailbox Configs
dovecot_15_mailboxes_conf = """##
## Mailbox definitions
##
# Each mailbox is specified in a separate mailbox section. The section name
# specifies the mailbox name. If it has spaces, you can put the name
# "in quotes". These sections can contain the following mailbox settings:
#
# auto:
#   Indicates whether the mailbox with this name is automatically created
#   implicitly when it is first accessed. The user can also be automatically
#   subscribed to the mailbox after creation. The following values are
#   defined for this setting:
# 
#     no        - Never created automatically.
#     create    - Automatically created, but no automatic subscription.
#     subscribe - Automatically created and subscribed.
#  
# special_use:
#   A space-separated list of SPECIAL-USE flags (RFC 6154) to use for the
#   mailbox. There are no validity checks, so you could specify anything
#   you want in here, but it's not a good idea to use flags other than the
#   standard ones specified in the RFC:
#
#     \All      - This (virtual) mailbox presents all messages in the
#                 user's message store. 
#     \Archive  - This mailbox is used to archive messages.
#     \Drafts   - This mailbox is used to hold draft messages.
#     \Flagged  - This (virtual) mailbox presents all messages in the
#                 user's message store marked with the IMAP \Flagged flag.
#     \Junk     - This mailbox is where messages deemed to be junk mail
#                 are held.
#     \Sent     - This mailbox is used to hold copies of messages that
#                 have been sent.
#     \Trash    - This mailbox is used to hold messages that have been
#                 deleted.
#
# comment:
#   Defines a default comment or note associated with the mailbox. This
#   value is accessible through the IMAP METADATA mailbox entries
#   "/shared/comment" and "/private/comment". Users with sufficient
#   privileges can override the default value for entries with a custom
#   value.
#
# NOTE: Assumes "namespace inbox" has been defined in 10-mail.conf.
namespace inbox {
  # These mailboxes are widely used and could perhaps be created automatically:
  mailbox Drafts {
    special_use = \Drafts
  }
  mailbox Junk {
    special_use = \Junk
  }
  mailbox Trash {
    special_use = \Trash
  }
  #
  # For \Sent mailboxes there are two widely used names. We'll mark both of
  # them as \Sent. User typically deletes one of them if duplicates are created.
  mailbox Sent {
    special_use = \Sent
  }
  mailbox "Sent Messages" {
    special_use = \Sent
  }
  #
  # If you have a virtual "All messages" mailbox:
  #mailbox virtual/All {
  #  special_use = \All
  #  comment = All my messages
  #}
  #
  # If you have a virtual "Flagged" mailbox:
  #mailbox virtual/Flagged {
  #  special_use = \Flagged
  #  comment = All my flagged messages
  #}
  mailbox Junk {
    special_use = \Junk
    auto = subscribe
    autoexpunge = 30d
  }
  mailbox Trash {
    special_use = \Trash
    auto = subscribe
    autoexpunge = 30d
  }
}
"""
dovecot_15_mailboxes_conf_file = "/etc/dovecot/conf.d/15-mailboxes.conf"
#------------------- rspamd_config definitions END-------------------

#------------------- dkim_config definitions BEGIN-------------------
# DKIM Config Definition
rspamd_dkim_signing_conf = """path = "/var/lib/rspamd/dkim/$domain.$selector.key";
selector_map = "/etc/rspamd/dkim_selectors.map";
"""
rspamd_dkim_signing_conf_file = "/etc/rspamd/local.d/dkim_signing.conf"
#------------------- dkim_config definitions END-------------------

#------------------- ispmailadmin_config definitions BEGIN-------------------
# ISPMailAdmin config file
ispmailadmin_configs = """
<?php
/**
**
**
** @package    ISPmail_Admin
** @author     Ole Jungclaussen
** @version    0.9.0
**/
/**
** Database access
**
**/
define('IMA_CFG_DB_HOST',     '127.0.0.1');
define('IMA_CFG_DB_PORT',     '3306');
define('IMA_CFG_DB_USER',     'mailadmin');
define('IMA_CFG_DB_PASSWORD', '""" + mailadminpw + """');
define('IMA_CFG_DB_DATABASE', 'mailserver');
define('IMA_CFG_DB_SOCKET',   null);
/**
** Pasword hashes
** Uncomment to use dovecot/BCRYPT hashes,
** otherwise fallback to SHA256-CRYPT
**/
define('IMA_CFG_USE_BCRYPT_HASHES', true);
/**
** Quotas
** Uncomment to use quota management
**/
define('IMA_CFG_QUOTAS', true);
/// true or false
define('IMA_CFG_USE_QUOTAS', true);
/// in bytes. 0 is unlimited, 1GB = 2^30 Bytes = 1073741824
define('IMA_CFG_DEFAULT_QUOTA', 0);
/// convenience for input field
define('IMA_CFG_QUOTA_STEP', 1073741824);
/**
** access control: uncomment the type you want to use.
**
**/
// define('IMA_CFG_LOGIN', IMA_LOGINTYPE_ACCOUNT);  
define('IMA_CFG_LOGIN', IMA_LOGINTYPE_ADM);  
// define('IMA_CFG_LOGIN', IMA_LOGINTYPE_ADMAUTO);  
/**
** Define the administrator's name and password.
**
**/
define('IMA_CFG_ADM_USER',  'admin');     // admin username
define('IMA_CFG_ADM_PASS',  '""" + ispmailadminpw + """');     // admin password
/**
** LISTS
** Spread long lists on multiple "pages"
** Set number of maximum entries per page.
** Changes take effect after login/logout.
** If not defined, defaults to 65535.
**/
// define('IMA_LIST_MAX_ENTRIES', 200);
?>
"""
ispmailadmin_configs_file = "/var/www/ispmailadmin/cfg/config.inc.php"
#------------------- ispmailadmin_config definitions END-------------------

separator = "----"
line_separator = "----------------------------------------------------------------------------"

todayt = datetime.datetime.now()
today = todayt.strftime("%Y%m%d")

# Start applog and errorlog
start_log(applog)
start_log(errorlog)

# Step by Step Installation and Configuration
apt_install()
apache_configs()
mariadb_scripts()
postfix_mysql()
dovecot_config()
roundcube_config()
postfix_config()
rspamd_config()
dkim_config()
ispmailadmin_config()
finish_installations()
prepare_dns_config()
prepare_password_file()
prepare_autoconfig_files()

# Finished
print("Operation completed, you can check installation log: ispmail.log")
print("For possible errors check error log: ispmail.error.log")
print(line_separator)
print("The following information file(s) are created as reference to DNS configuration.")
print("Configure your DNS according to them, and your mail server will be ready:")
for domain in domains:
   print(domain + ".dns.config")
print(line_separator)
print("The following file(s) are created for mail autoconfigurations.")
print("Instructions for them are supplied in ispmail.autoconfig.txt:")
for domain in domains:
   print(domain + ".config-v1.1.xml")

