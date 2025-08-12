#!/usr/bin/env python3

# All used libraries are standard libraries, works well on a standart Debian/Ubuntu box

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
Implements ISPMail Tutorial of Christoph Haas as in https://workaround.org
Details are in https://ispmailinstall.x386.org/ or README.MD
version: 0.3.0

Aimed target versions are Debian 11/12 and Ubuntu 22.04/24.04. Program refuse to run if you don't have Debian or Ubuntu.
  If you have other versions, it will warn you but will let you to take your chance. Success is not guaranteed.
  This program is tested thoroughly on fresh installed servers. I don't know if it is absolutely necessary but you are 
  advised to do so too.

Debian upgrades Dovecot from 2.3 to 2.4 on version 13. So it is certain that this program will not work on Debian 13
  when it is released. I'm going to update it as soon as Dear Christoph Haas updates it in https://workaround.org.

In Christoph Haas's site https://workaround.org there are ansible scripts, you can use them to install ISPMail too. Linux
  community loves alternatives, so I decided to keep this program too.

I started writing this program in 2019, with every version I tried to patch it. But I guess it is time to rewrite it.

You are free to use, change, modify (whatever you want) with this program. But if you want to change and produce a product 
  using it, you have to supply the source code. That is what GPL says. 

Before running it, I'd advice you to check and fill the configuration file ispmail.conf. It will be easier to set your 
  parameters there; otherwise you'll have to enter a lot of things when the program runs.


Exit Codes:
0:    Program completed succesfully (Still there might be some errors processing commands)
1:    Error in config file
11:   Platform is not Linux
12:   User is not root or not by sudo
13:   Platform is not Debian or Ubuntu
21:   Error creating a log file
22:   Error adding to log file

   ---Copyright (C) 2021 - 2025 Exforge exforge@x386.xyz
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

# GLOBAL VARIABLES
# Parameters
hostname = ""
domains = []
email = ""

# Passwords
mailadminpw = ""
mailserverpw = ""
rspamdpw = ""
ispmailadminpw = ""

print_all_passwords = False

# Password flags
mailadminpwauto = False
mailserverpwauto = False
rspamdpwauto = False
ispmailadminpwauto = False

# Config, log and password files
config_file = "ispmail.conf"
applog = "ispmail.log"
errorlog = "ispmail.error.log"
passwordfile = "ispmailpasswords.txt"

# General
distro = ""
release = ""
distro_release = ""
supported_releases = ["Ubuntu 22.04", "Ubuntu 24.04", "Debian GNU/Linux 11", "Debian GNU/Linux 12"]
separator = "----"
line_separator = "----------------------------------------------------------------------------"

# Today is used as a DKIM Selector
todayt = datetime.datetime.now()
today = todayt.strftime("%Y%m%d")

# UTILITY FUNCTIONS

def get_distro_release():
   """ Returns Distro name and release number
   /etc/os-release file contains distro name and release numbers among
   other information. We try to reach the information in the following format:
   distro = "Ubuntu"
   distro = "Debian GNU Linux"
   release = "22.04"
   release = "24.04"
   release = "11"
   release = "12"
   distro_release = "Ubuntu 22.04"
   distro_release = "Ubuntu 24.04"
   distro_release = "Debian GNU Linux 11"
   distro_release = "Debian GNU Linux 12"
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
      release = d["VERSION_ID"]
   # No /etc/os-release file, return as Other Other
   except:
      distro = "Other"
      release = "Other"
   distro_release = distro + " " + release
   return distro, release, distro_release

def find_between(s, first, last):
   """
   Find and return substring between 2 strings
   s, first and last are strings
   returns the substring of s between first and last strings
   written by: https://stackoverflow.com/users/280995/cji
   taken from: https://stackoverflow.com/questions/3368969/find-string-between-two-substrings
   This function is used to extract DKIM key
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
   On error exits the program with the code 21
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
   On error exits the program with the code 22
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
   # Command ended succesfully
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
   # Command ended succesfully
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
   If the file already exists, back it up as: file.backup.YYYYMMDDHHSSMsMsMsMsMsMsMs
   otherwise do nothing.
   Called when overwriting a file
   """
   if os.path.isfile(filename):
      now = datetime.datetime.now()
      formatted_now = now.strftime("%Y%m%d%H%M%S") + f"{now.microsecond:06d}"
      backup_file = filename + ".backup." + formatted_now
      # Try to make a backup file
      try:
         command = "cp " + filename + " " + backup_file
         process_command(command)
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
   backup(filename)
   add_log(applog, line_separator)
   add_log(applog, "Filling file: " + filename)
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
   backup(filename)
   add_log(applog, line_separator)
   add_log(applog, "Appending to file: " + filename)
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

def replace_in_string(str, source, target):
   """
   In string str, replaces every occurences of source with target.
   Returns the replaced string.
   """
   return(str.replace(source, target))

def replace_in_file(filename, source, target):
   """
   In file filename, replaces every occurences of source with target.
   Return Codes:
      0: Success
      1: Error (Error message is logged)
   """

   backup(filename)
   try:
      # Read the entire file
      with open(filename, 'r', encoding='utf-8') as file:
         content = file.read()
   except Exception as e:
      add_log(applog, "Error replacing in file: " + filename)
      add_log(errorlog, line_separator)
      add_log(errorlog, "Error replacing in file: " + filename)
      add_log(errorlog, "Error message: " + str(e))
      return(1)

   # Replace the substring
   new_content = content.replace(source, target)
    
   try:
      # Write back to the same file
      with open(filename, 'w', encoding='utf-8') as file:
         file.write(new_content)
   except Exception as e:
      add_log(applog, "Error replacing in file: " + filename)
      add_log(errorlog, line_separator)
      add_log(errorlog, "Error replacing in file: " + filename)
      add_log(errorlog, "Error message: " + str(e))
      return(1)
   add_log(applog, "Success replacing in  file: " + filename)
   return 0

def password(length):
   """
   Generates and returns a password of specified length (minimum 3).
   Password consists of uppercase and lowercase letters and digits (at least 1 from each).
   I was so lazy to write this, so I requested from claude.ai 
   """
   
   # Return empty string if length < 3
   if length < 3:
      return("")
    
   # Define character sets
   uppercase = string.ascii_uppercase
   lowercase = string.ascii_lowercase  
   numbers = string.digits
   all_chars = uppercase + lowercase + numbers
    
   # Start with one character from each required type
   password = [
      random.choice(uppercase),
      random.choice(lowercase), 
      random.choice(numbers)
   ]
    
    # Fill the rest with random characters from all sets
   for _ in range(length - 3):
      password.append(random.choice(all_chars))
    
    # Shuffle to avoid predictable pattern
   random.shuffle(password)
    
   return ''.join(password)

def get_parameter(message):
   """
   Reads and returns a parameter value from the user.
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
   Reads and returns a password value from the user.
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

# STEP 0 : Get Parameters

def read_config_file():
   """
   Reads from config_file to get all parameters.
   """
   global hostname, domains, email
   global domains, mailadminpw, mailserverpw, rspamdpw, ispmailadminpw
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
   global domains, mailadminpw, mailserverpw, rspamdpw, ispmailadminpw

   if hostname == "":
      hostname = get_parameter("Please enter hostname (mail.example.org): ")
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
   if rspamdpw == "":
      rspamdpw = get_password("Enter password rspamdpw: (auto to autogenerate) ")
   if ispmailadminpw == "":
      ispmailadminpw = get_password("Enter password ispmailadminpw: (auto to autogenerate) ")
   
def generate_auto_passwords():
   """
   Generate all passwords set for auto generate.
   Set flags for autogenerated passwords to print them later
   """
   global domains, mailadminpw, mailserverpw, rspamdpw, ispmailadminpw
   global mailadminpwauto, mailserverpwauto, rspamdpwauto, ispmailadminpwauto

   if mailadminpw == "auto":
      mailadminpw = password(12)
      mailadminpwauto = True
   if mailserverpw == "auto":
      mailserverpw = password(12)
      mailserverpwauto = True
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

# STEP 1 : Install Packages

def apt_install():
   """
   Install all necessary packages.
   Set parameters for postfix and roundcube, otherwise they ask for user interaction.
   Install apache, php, mariadb, postfix, rspamd, certbot, dovecot, adminer, roundcube, and dependency packages
   """

   # debconf-set-selections commands are used to set default answers to apt-get questions
   commands = ["apt-get update",
   "debconf-set-selections <<< \"postfix postfix/mailname string " + hostname + "\"",
   "debconf-set-selections <<< \"postfix postfix/main_mailer_type string 'Internet Site'\"",
   "debconf-set-selections <<< \"roundcube roundcube/dbconfig-install boolean true\"",
   "debconf-set-selections <<< \"roundcube roundcube/database-type string mysql\"",
   "debconf-set-selections <<< \"roundcube roundcube/mysql/app-pass password\"",
   "apt-get -qq install apache2",
   "apt-get -qq install php",
   "apt-get -qq install php-bcmath",
   "apt-get -qq install mariadb-server",
   "apt-get -qq install postfix",
   "apt-get -qq install postfix-mysql",
   "apt-get -qq install rspamd",
   "apt-get -qq install redis-server",
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


# STEP 2: Configure Apache and TLS

def configure_apache():
   """
   Configure Apache, create websites, get TLS certificates   
   """

   # Remove existing unnecessary configuration
   process_command("rm /etc/apache2/sites-enabled/*")

   # Create a web root directory with the host name, set permissions:
   process_command("mkdir -p /var/www/" + hostname)
   process_command("chown www-data:www-data /var/www/" + hostname)

   # Create a new virtual host configuration
   filename = "/etc/apache2/sites-available/" + hostname + "-http.conf"
   content = """<VirtualHost *:80>
  ServerName mail.example.org
  DocumentRoot /var/www/mail.example.org
</VirtualHost>"""
   content = replace_in_string(content, "mail.example.org", hostname)
   to_file(filename, content)

   # Enable the site and reload apache 2
   process_command("a2ensite " + hostname + "-http")
   process_command("systemctl reload apache2")

   # Get TLS certificates from Let's Encrypt using certbot
   command = "sudo certbot certonly -n --webroot --webroot-path /var/www/" + hostname + " \\\n"
   command = command + "-d " + hostname + " --agree-tos --email " + email
   process_command(command)

   # Create HTTPS site
   filename = "/etc/apache2/sites-available/" + hostname + "-https.conf"
   content = """<VirtualHost *:443>
   ServerName mail.example.org
   DocumentRoot /var/www/mail.example.org
   SSLEngine on
   SSLCertificateFile /etc/letsencrypt/live/mail.example.org/fullchain.pem
   SSLCertificateKeyFile /etc/letsencrypt/live/mail.example.org/privkey.pem
</VirtualHost>"""
   content = replace_in_string(content, "mail.example.org", hostname)
   to_file(filename, content)

   # Enable SSL module of Apache and the new https site
   process_command("a2enmod ssl")
   process_command("a2ensite " + hostname + "-https")

   # Redirect HTTP to HTTPS, except Let's Encrypt Challenge
   filename = "/etc/apache2/sites-available/" + hostname + "-http.conf"
   content = """<VirtualHost *:80>
   ServerName mail.example.org
   DocumentRoot /var/www/mail.example.org
   RewriteEngine On
   RewriteCond %{REQUEST_URI} !.well-known/acme-challenge
   RewriteRule ^(.*)$ https://%{SERVER_NAME}$1 [R=301,L]
</VirtualHost>"""
   content = replace_in_string(content, "mail.example.org", hostname)
   to_file(filename, content)

   # Enable rewrite Apache mode and restart Apache
   process_command("a2enmod rewrite")
   process_command("systemctl restart apache2")

   # Add a certbot hook to restart postfix, dovecot and apache when the certificates are renewed.   
   filename = "/etc/letsencrypt/renewal-hooks/deploy/reloadall.sh"
   content = """#!/bin/bash
systemctl reload apache2
systemctl reload postfix
systemctl reload dovecot"""
   to_file(filename, content)

   # Make the script executable
   process_command("chmod +x /etc/letsencrypt/renewal-hooks/deploy/reloadall.sh")
   return()


# STEP 3: Mariadb Configuration

def db_preparation():
   """
   Run a mariadb script to create a database and add domains
   """

   db_script_file = "/tmp/ispmail_mariadb.sql"
   db_script = """CREATE DATABASE mailserver;
grant all privileges on mailserver.* to 'mailadmin'@'localhost' identified by 'mailadminpw';
grant select on mailserver.* to 'mailserver'@'127.0.0.1' identified by 'mailserverpw';
USE mailserver;
CREATE TABLE IF NOT EXISTS `virtual_domains` (
   `id` int(11) NOT NULL auto_increment,
   `name` varchar(50) NOT NULL,
   PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE IF NOT EXISTS `virtual_users` (
   `id` int(11) NOT NULL auto_increment,
   `domain_id` int(11) NOT NULL,
   `email` varchar(100) NOT NULL,
   `password` varchar(150) NOT NULL,
   `quota` bigint(11) NOT NULL DEFAULT 0,
   PRIMARY KEY (`id`),
   UNIQUE KEY `email` (`email`),
   FOREIGN KEY (domain_id) REFERENCES virtual_domains(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
CREATE TABLE IF NOT EXISTS `virtual_aliases` (
   `id` int(11) NOT NULL auto_increment,
   `domain_id` int(11) NOT NULL,
   `source` varchar(100) NOT NULL,
   `destination` varchar(100) NOT NULL,
   PRIMARY KEY (`id`),
   FOREIGN KEY (domain_id) REFERENCES virtual_domains(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
"""

   # Create domain records
   for domain in domains:
      db_script += "INSERT INTO virtual_domains (name) VALUES ('" + domain +"');\n"

   db_script = replace_in_string(db_script, "mailadminpw", mailadminpw)
   db_script = replace_in_string(db_script, "mailserverpw", mailserverpw)
   to_file(db_script_file, db_script)
   command = "mariadb < " + db_script_file
   process_command(command)
   return()

# STEP 4: Postfix - Mariadb Connection

def postfix_mariadb_connection():
   """
   Necessary configurations to connect Postfix to Mariadb
   Postfix authenticates using the tables in Mariadb
   """

   # Connect domains
   # Create a new config file and add a postfix config
   config_file = "/etc/postfix/mysql-virtual-mailbox-domains.cf"
   config_contents = """user = mailserver
password = mailserverpw
hosts = 127.0.0.1
dbname = mailserver
query = SELECT 1 FROM virtual_domains WHERE name='%s'"""
   config_contents = replace_in_string(config_contents, "mailserverpw", mailserverpw)
   to_file(config_file, config_contents)
   command = "postconf virtual_mailbox_domains=mysql:/etc/postfix/mysql-virtual-mailbox-domains.cf"
   process_command(command)

   # Connect users
   # Create a new config file and add a postfix config
   config_file = "/etc/postfix/mysql-virtual-mailbox-maps.cf"
   config_contents = """user = mailserver
password = mailserverpw
hosts = 127.0.0.1
dbname = mailserver
query = SELECT 1 FROM virtual_users WHERE email='%s'"""
   config_contents = replace_in_string(config_contents, "mailserverpw", mailserverpw)
   to_file(config_file, config_contents)
   command = "postconf virtual_mailbox_maps=mysql:/etc/postfix/mysql-virtual-mailbox-maps.cf"
   process_command(command)

   # Connect aliases
   # Create a new config file and add a postfix config
   config_file = "/etc/postfix/mysql-virtual-alias-maps.cf"
   config_contents = """user = mailserver
password = mailserverpw
hosts = 127.0.0.1
dbname = mailserver
query = SELECT destination FROM virtual_aliases WHERE source='%s'"""
   config_contents = replace_in_string(config_contents, "mailserverpw", mailserverpw)
   to_file(config_file, config_contents)
   command = "postconf virtual_alias_maps=mysql:/etc/postfix/mysql-virtual-alias-maps.cf"
   process_command(command)

   # Fix ownerships & permissions
   command = "chgrp postfix /etc/postfix/mysql-*.cf"
   process_command(command)
   command = "chmod u=rw,g=r,o= /etc/postfix/mysql-*.cf"
   process_command(command)

   return()

# STEP 5: Dovecot Setup

def dovecot_setup():
   """
   Dovecot configuration
   """

   # Create a new system user that will own all virtual mailboxes
   command = "groupadd -g 5000 vmail"
   process_command(command)
   command = "useradd -g vmail -u 5000 vmail -d /var/vmail -m"
   process_command(command)
   command = "chown -R vmail:vmail /var/vmail"
   process_command(command)

   # Modify /etc/dovecot/conf.d/10-auth.conf
   filename = "/etc/dovecot/conf.d/10-auth.conf"
   source = "auth_mechanisms = plain"
   target = "auth_mechanisms = plain login"
   replace_in_file(filename, source, target)
   source = """!include auth-system.conf.ext
#!include auth-sql.conf.ext"""
   target = """#!include auth-system.conf.ext
!include auth-sql.conf.ext"""
   replace_in_file(filename, source, target)

   # Modify /etc/dovecot/conf.d/10-mail.conf
   filename = "/etc/dovecot/conf.d/10-mail.conf"
   source = "mail_location = mbox:~/mail:INBOX=/var/mail/%u"
   target = "mail_location = maildir:~/Maildir"
   replace_in_file(filename, source, target)
   source = "#mail_plugins ="
   target = "mail_plugins = quota"
   replace_in_file(filename, source, target)

   # Modify /etc/dovecot/conf.d/10-master.conf
   filename = "/etc/dovecot/conf.d/10-master.conf"
   source = """  # Postfix smtp-auth
  #unix_listener /var/spool/postfix/private/auth {
  #  mode = 0666
  #}"""
   target = """  # Postfix smtp-auth
  unix_listener /var/spool/postfix/private/auth {
    mode = 0660
    user = postfix
    group = postfix
  }"""
   replace_in_file(filename, source, target)

   # Modify /etc/dovecot/conf.d/10-ssl.conf
   filename = "/etc/dovecot/conf.d/10-ssl.conf"
   source = "ssl = yes"
   target = "ssl = required"
   replace_in_file(filename, source, target)

   source = """ssl_cert = </etc/dovecot/private/dovecot.pem
ssl_key = </etc/dovecot/private/dovecot.key"""
   target = """ssl_cert = </etc/letsencrypt/live/mail.example.org/fullchain.pem
ssl_key = </etc/letsencrypt/live/mail.example.org/privkey.pem"""
   target = replace_in_string(target, "mail.example.org", hostname)
   replace_in_file(filename, source, target)

   # Modify /etc/dovecot/dovecot-sql.conf.ext (append)
   filename = "/etc/dovecot/dovecot-sql.conf.ext"
   content = """
driver = mysql

connect = \
host=127.0.0.1 \
dbname=mailserver \
user=mailserver \
password=mailserverpw

user_query = SELECT email as user, \
concat('*:bytes=', quota) AS quota_rule, \
'/var/vmail/%d/%n' AS home, \
5000 AS uid, 5000 AS gid \
FROM virtual_users WHERE email='%u'

password_query = SELECT password FROM virtual_users WHERE email='%u'

iterate_query = SELECT email AS user FROM virtual_users"""
   content = replace_in_string(content, "mailserverpw", mailserverpw)
   append_file(filename, content)

   # Fix ownerships and permissions, restart dovecot
   command = "chown root:root /etc/dovecot/dovecot-sql.conf.ext"
   process_command(command)
   command = "chmod go= /etc/dovecot/dovecot-sql.conf.ext"
   process_command(command)
   command = "systemctl restart dovecot"
   process_command(command)

   return()

# STEP 6: Postfix - Dovecot Connection

def postfix_dovecot_connection():
   """
   Configurations for connecting postfix to dovecot
   Postfix sends to dovecot, dovecot listens from postfix
   """

   # Tell dovecot to listen from postfix
   filename = "/etc/dovecot/conf.d/10-master.conf"
   source = """  unix_listener lmtp {
    #mode = 0666
  }"""
   target = """  unix_listener /var/spool/postfix/private/dovecot-lmtp {
    group = postfix
    mode = 0600
    user = postfix
  }"""
   replace_in_file(filename, source, target)

   # Tell Postfix to deliver emails to Dovecot
   command = "postconf virtual_transport=lmtp:unix:private/dovecot-lmtp"
   process_command(command)

   # Enable Server-side Mail Rules
   filename = "/etc/dovecot/conf.d/20-lmtp.conf"
   source = "  #mail_plugins = $mail_plugins"
   target = "  mail_plugins = $mail_plugins sieve"
   replace_in_file(filename, source, target)

   return(0)

# STEP 7: Quota Configuration
def configure_quotas():
   """
   Configure quotas and quota warnings
   """
   
   # Dovecot Quota Policy Service
   filename = "/etc/dovecot/conf.d/90-quota.conf"
   content = """
plugin {
  quota = count:User quota
  quota_vsizes = yes

  quota_status_success = DUNNO
  quota_status_nouser = DUNNO
  quota_status_overquota = "452 4.2.2 Mailbox is full and cannot receive any more emails"
}
service quota-status {
  executable = /usr/lib/dovecot/quota-status -p postfix
  unix_listener /var/spool/postfix/private/quota-status {
    user = postfix
  }
}
plugin {
   quota_warning = storage=95%% quota-warning 95 %u
   quota_warning2 = storage=80%% quota-warning 80 %u
}
service quota-warning {
   executable = script /usr/local/bin/quota-warning.sh
   unix_listener quota-warning {
     user = vmail
     group = vmail
     mode = 0660
   }
}
"""
   append_file(filename, content)

   # Enable postfix recipient restrictions
   command = '''postconf smtpd_recipient_restrictions=reject_unauth_destination, \
    "check_policy_service=unix:private/quota-status"'''
   process_command(command)

   # Quota warning script
   filename = "/usr/local/bin/quota-warning.sh"
   content = """#!/bin/sh
PERCENT=$1
USER=$2
cat << EOF | /usr/lib/dovecot/dovecot-lda -d $USER -o "plugin/quota=maildir:User quota:noenforcing"
From: postmaster@mail.example.org
Subject: Quota warning - $PERCENT% reached

Your mailbox can only store a limited amount of emails.
Currently it is $PERCENT% full. If you reach 100% then
new emails cannot be stored. Thanks for your understanding.
EOF"""
   to_file(filename, content)

   # Make the script executable and restart Dovecot & Postfix
   command = "chmod +x /usr/local/bin/quota-warning.sh"
   process_command(command)
   command = "systemctl restart dovecot"
   process_command(command)
   command = "systemctl restart postfix"
   process_command(command)

   return()

# STEP 8: Roundcube Configuration

def roundcube_configuration():
   """
   Roundcube access and plugin configurations
   """

   # Limit roundcube's access to localhost only
   filename = "/etc/roundcube/config.inc.php"
   source = "$config['default_host'] = '';"
   target = "$config['default_host'] = 'tls://mail.example.org';"
   target = replace_in_string(target, "mail.example.org", hostname)
   replace_in_file(filename, source, target)

   source = "$config['smtp_server'] = 'localhost';"
   target = "$config['smtp_server'] = 'tls://mail.example.org';"
   target = replace_in_string(target, "mail.example.org", hostname)
   replace_in_file(filename, source, target)

   source = """$config['imap_host'] = ["localhost:143"];"""
   target = """$config['imap_host'] = "tls://mail.example.org:143";"""
   target = replace_in_string(target, "mail.example.org", hostname)
   replace_in_file(filename, source, target)

   source = "$config['smtp_host'] = 'localhost:587';"
   target = "$config['smtp_host'] = 'tls://mail.example.org:587';"
   target = replace_in_string(target, "mail.example.org", hostname)
   replace_in_file(filename, source, target)

   # Configure plugins (keep changing the same file)
   source = """$config['plugins'] = array(
);"""
   target = """$config['plugins'] = array(
     'managesieve',
     'password',
 );"""
   replace_in_file(filename, source, target)

   source = """$config['plugins'] = [
    // 'archive',
    // 'zipdownload',
];"""
   replace_in_file(filename, source, target)   # Target is the same as the previous one

   # Configure password plugin
   filename = "/etc/roundcube/plugins/password/config.inc.php"
   if distro_release == "Debian GNU/Linux 11":
      content = """<?php
$config['password_driver'] = 'sql';
$config['password_minimum_length'] = 12;
$config['password_force_save'] = true;
$config['password_algorithm'] = 'dovecot';
$config['password_dovecotpw'] = '/usr/bin/doveadm pw -s BLF-CRYPT';
$config['password_dovecotpw_method'] = 'BLF-CRYPT';
$config['password_dovecotpw_with_method'] = true;
$config['password_db_dsn'] = 'mysql://mailadmin:mailadminpw@localhost/mailserver';
$config['password_query'] = "UPDATE virtual_users SET password=%D WHERE email=%u";
?>"""
   else:
      content = """<?php
$config['password_driver'] = 'sql';
$config['password_minimum_length'] = 12;
$config['password_force_save'] = true;
$config['password_algorithm'] = 'blowfish-crypt';
$config['password_algorithm_prefix'] = '{CRYPT}';
$config['password_db_dsn'] = 'mysql://mailadmin:mailadminpw@localhost/mailserver';
$config['password_query'] = "UPDATE virtual_users SET password=%P WHERE email=%u";
?>"""
   content = replace_in_string(content, "mailadminpw", mailadminpw)
   to_file(filename, content)

   # Fix the file's permissions and ownership
   command = "chown root:www-data /etc/roundcube/plugins/password/config.inc.php"
   process_command(command)
   command = "chmod u=rw,g=r,o= /etc/roundcube/plugins/password/config.inc.php"
   process_command(command)

   # Configure sieve plugin
   filename = "/etc/roundcube/plugins/managesieve/config.inc.php"
   content = """<?php
$config['managesieve_host'] = 'localhost';
?>"""
   to_file(filename, content)

   return()

# STEP 9: Send mails to postfix

def send_mails_to_postfix():
   """
   Configurations for forwarding outgoing mails to postfix
   """

   # Make Postfix use Dovecot for authentication
   command = "postconf smtpd_sasl_type=dovecot"
   process_command(command)
   command = "postconf smtpd_sasl_path=private/auth"
   process_command(command)
   command = "postconf smtpd_sasl_auth_enable=yes"
   process_command(command)

   # Enable encryption
   command = "postconf smtpd_tls_security_level=may"
   process_command(command)
   command = "postconf smtpd_tls_auth_only=yes"
   process_command(command)
   command = "postconf smtpd_tls_cert_file=/etc/letsencrypt/live/mail.example.org/fullchain.pem"
   command = replace_in_string(command, "mail.example.org", hostname)
   process_command(command)
   command = "postconf smtpd_tls_key_file=/etc/letsencrypt/live/mail.example.org/privkey.pem"
   command = replace_in_string(command, "mail.example.org", hostname)
   process_command(command)
   command = "postconf smtp_tls_security_level=may"
   process_command(command)

   # Enable submission ports
   filename = "/etc/postfix/master.cf"
   source = "#submission inet n       -       y       -       -       smtpd"
   target = """submission inet n       -       y       -       -       smtpd
  -o syslog_name=postfix/submission
  -o smtpd_tls_security_level=encrypt
  -o smtpd_sasl_auth_enable=yes
  -o smtpd_tls_auth_only=yes
  -o smtpd_reject_unlisted_recipient=no
  -o smtpd_client_restrictions=
  -o smtpd_helo_restrictions=
  -o smtpd_relay_restrictions=
  -o smtpd_recipient_restrictions=permit_sasl_authenticated,reject
  -o milter_macro_daemon_name=ORIGINATING
  -o smtpd_sender_restrictions=reject_sender_login_mismatch,permit_sasl_authenticated,reject"""
   replace_in_file(filename, source, target)

   # Configure sender user maps
   filename = "/etc/postfix/mysql-email2email.cf"
   content = """user = mailserver
password = mailserverpw
hosts = 127.0.0.1
dbname = mailserver
query = SELECT email FROM virtual_users WHERE email='%s'"""
   content = replace_in_string(content, "mailserverpw", mailserverpw)
   to_file(filename, content)

   # Add the configuration to postfix and restart it
   command = "postconf smtpd_sender_login_maps=mysql:/etc/postfix/mysql-email2email.cf"
   process_command(command)
   command = "systemctl restart postfix"
   process_command(command)

   return()

# STEP 10: Rspamd Configuration

def rspamd_configuration():
   """
   Necessary rspamd configuration
   Connect postfix to rspamd, spam headers and sending junk mail to junk folder,
   Spam detection training, learn from user actions, rspamd web interface
   """

   # Make postfix use rspamd
   command = "postconf smtpd_milters=inet:127.0.0.1:11332"
   process_command(command)
   command = "postconf non_smtpd_milters=inet:127.0.0.1:11332"
   process_command(command)
   command = 'postconf milter_mail_macros="i {mail_addr} {client_addr} {client_name} {auth_authen}"'
   process_command(command)


   # Create a custom score metrics, this will never reject a spam mail, instead put it in Junk folder
   filename = "/etc/rspamd/local.d/actions.conf"
   content = """reject = 150;
add_header = 6;
greylist = 4;"""
   to_file(filename, content)

   # Add spam headers
   filename = "/etc/rspamd/override.d/milter_headers.conf"
   content = "extended_spam_headers = true;"
   to_file(filename, content)

   # Restart rspamd
   command = "systemctl restart rspamd"
   process_command(command)

   ## Configure dovecot to send the spam mails to junk folder
   filename = "/etc/dovecot/conf.d/90-sieve.conf"
   source = "  #sieve_after ="
   target = "  sieve_after = /etc/dovecot/sieve-after"
   replace_in_file(filename, source, target)

   # Create the sieve after folder
   command = "mkdir -p /etc/dovecot/sieve-after"
   process_command(command)

   # Create a file there and compile it to make Dovecot use it
   filename = "/etc/dovecot/sieve-after/spam-to-folder.sieve"
   content = """require ["fileinto"];

if header :contains "X-Spam" "Yes" {
 fileinto "Junk";
 stop;
}"""
   to_file(filename, content)
   command = "sievec /etc/dovecot/sieve-after/spam-to-folder.sieve"
   process_command(command)

   ## Spam Detection Training
   # Connect Redis server to Rspamd
   filename = "/etc/rspamd/override.d/redis.conf"
   content = """servers = "127.0.0.1";"""
   to_file(filename, content)
   # Restart rspamd
   command = "systemctl restart rspamd"
   process_command(command)

   # Enable Auto-learning and Per-user spam training
   filename = "/etc/rspamd/override.d/classifier-bayes.conf"
   content = """autolearn = [-5, 10];
users_enabled = true;"""
   to_file(filename, content)

   # Autoexpunge (Delete Junk and Trash after 30 days)
   filename = "/etc/dovecot/conf.d/15-mailboxes.conf"
   source = r"""  mailbox Junk {
    special_use = \Junk
  }
  mailbox Trash {
    special_use = \Trash
  }"""
   target = r"""  mailbox Junk {
    special_use = \Junk
    auto = subscribe
    autoexpunge = 30d
  }
  mailbox Trash {
    special_use = \Trash
    auto = subscribe
    autoexpunge = 30d
  }"""
   replace_in_file(filename, source, target)
   # Auto subscribe to Sent folder (update the same config file)
   source = r"""  mailbox Sent {
    special_use = \Sent
  }"""
   target = r"""  mailbox Sent {
    special_use = \Sent
    auto = subscribe
  }"""
   replace_in_file(filename, source, target)

   ## Learning from User Actions, sending a mail to Junk means it is spam, removing a mail from junk means it is ham
   # Add plugin
   filename = "/etc/dovecot/conf.d/20-imap.conf"
   source = "  #mail_plugins = $mail_plugins"
   target = "  mail_plugins = $mail_plugins quota imap_sieve imap_quota"
   replace_in_file(filename, source, target)
   # Enable plugins
   filename = "/etc/dovecot/conf.d/90-sieve.conf"
   source = "}"
   target = """
  # From elsewhere to Junk folder
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
}"""
   replace_in_file(filename, source, target)

   # Create sieve scripts
   command = "mkdir -p /etc/dovecot/sieve"
   process_command(command)
   filename = "/etc/dovecot/sieve/learn-spam.sieve"
   content = """require ["vnd.dovecot.pipe", "copy", "imapsieve"];
pipe :copy "rspamd-learn-spam.sh";"""
   to_file(filename, content)
   filename = "/etc/dovecot/sieve/learn-ham.sieve"
   content = """require ["vnd.dovecot.pipe", "copy", "imapsieve", "variables"];
if string "${mailbox}" "Trash" {
  stop;
}
pipe :copy "rspamd-learn-ham.sh";"""
   to_file(filename, content)
   command = "systemctl restart dovecot"
   process_command(command)

   # Compile sieve scripts and fix permissions
   command = "sievec /etc/dovecot/sieve/learn-spam.sieve"
   process_command(command)
   command = "sievec /etc/dovecot/sieve/learn-ham.sieve"
   process_command(command)
   command = "chmod u=rw,go= /etc/dovecot/sieve/learn-{spam,ham}.{sieve,svbin}"
   process_command(command)
   command = "chown vmail:vmail /etc/dovecot/sieve/learn-{spam,ham}.{sieve,svbin}"
   process_command(command)
   
   # Create actual shell scripts
   filename = "/etc/dovecot/sieve/rspamd-learn-spam.sh"
   content = """#!/bin/sh
exec /usr/bin/rspamc learn_spam"""
   to_file(filename, content)
   filename = "/etc/dovecot/sieve/rspamd-learn-ham.sh"
   content = """#!/bin/sh
exec /usr/bin/rspamc learn_ham"""
   to_file(filename, content)

   # Fix permissions and restart dovecot
   command = "chmod u=rwx,go= /etc/dovecot/sieve/rspamd-learn-{spam,ham}.sh"
   process_command(command)
   command = "chown vmail:vmail /etc/dovecot/sieve/rspamd-learn-{spam,ham}.sh"
   process_command(command)
   command = "systemctl restart dovecot"
   process_command(command)
   
   ## Rspamd Web Interface
   command = "rspamadm pw -p rspamdpw > /tmp/rspamdpassword"
   command = replace_in_string(command, "rspamdpw", rspamdpw)
   process_command_wpipe(command)
   filename = "/tmp/rspamdpassword"
   ret, rspamdencpw = from_file(filename)
   # Remove \n at the end
   rspamdencpw = rspamdencpw[:-1]
   command = "rm /tmp/rspamdpassword"
   process_command(command)
   filename = "/etc/rspamd/local.d/worker-controller.inc"
   content = 'password = "' + rspamdencpw + '"'
   to_file(filename, content)
   command = "systemctl restart rspamd"
   process_command(command)

   return()

# STEP 11: DKIM Configuration
def dkim_configuration():
   """
   DKIM keys, maps and configuration
   """

   ## DKIM key creation
   # Prepare folder and fix ownerships
   command = "mkdir -p /var/lib/rspamd/dkim"
   process_command(command)
   command = "chown _rspamd:_rspamd /var/lib/rspamd/dkim"
   process_command(command)
   # Create the keys for all domains
   for domain in domains:
      command = "rspamadm dkim_keygen -d "+ domain + " -s " + today + " -k /var/lib/rspamd/dkim/" 
      command = command + domain + "." + today + ".key > /tmp/" + domain + ".dkim"
      process_command_wpipe(command)

   ## Enable DKIM Maps
   # Create configuration
   filename = "/etc/rspamd/local.d/dkim_signing.conf"
   content = """path = "/var/lib/rspamd/dkim/$domain.$selector.key";
selector_map = "/etc/rspamd/dkim_selectors.map";"""
   to_file(filename, content)
   # Map file
   filename = "/etc/rspamd/dkim_selectors.map"
   content = ""
   for domain in domains:
      content = content + domain + " " + today + "\n"
   to_file(filename, content)

   # Fix ownerships and permissions, restart rspamd
   command = "chown -R _rspamd:_rspamd /var/lib/rspamd/dkim"
   process_command(command)
   command = "chmod -R u=rx,go= /var/lib/rspamd/dkim"
   process_command(command)
   command = "systemctl restart rspamd"
   process_command(command)
   
   return()

# STEP 12: ISPMainAdmin Configuration

def ispmailadmin_configuration():
   """
   Download ISPMailAdmin and configure it
   """

   # Get it
   command = "git clone https://github.com/enatsek/ISPMailAdmin.git /var/www/ispmailadmin"
   process_command(command)

   # Update configuration file

   filename = "/var/www/ispmailadmin/cfg/config.inc.php"
   source = """define('IMA_CFG_DB_USER',     'db_user');
define('IMA_CFG_DB_PASSWORD', 'db_pass');"""
   target = """define('IMA_CFG_DB_USER',     'mailadmin');
define('IMA_CFG_DB_PASSWORD', 'mailadminpw');"""
   target = replace_in_string(target, "mailadminpw", mailadminpw)
   replace_in_file(filename, source, target)

   source = "// define('IMA_CFG_LOGIN', IMA_LOGINTYPE_ADM);"
   target = "define('IMA_CFG_LOGIN', IMA_LOGINTYPE_ADM);"
   replace_in_file(filename, source, target)

   source = """define('IMA_CFG_ADM_USER',  'admin_user');     // admin username
define('IMA_CFG_ADM_PASS',  'admin_Pass');     // admin password"""
   target = """define('IMA_CFG_ADM_USER',  'admin');     // admin username
define('IMA_CFG_ADM_PASS',  'ispmailadminpw');     // admin password"""
   target = replace_in_string(target, "ispmailadminpw", ispmailadminpw)
   replace_in_file(filename, source, target)

   source = "define('IMA_SUPPORT_BLACKLIST', true);"
   target = "// define('IMA_SUPPORT_BLACKLIST', true);"
   replace_in_file(filename, source, target)

   # Update web site configuration to include ISPMailAdmin and rspamd interface
   filename = "/etc/apache2/sites-available/mail.example.org-https.conf"
   filename = replace_in_string(filename, "mail.example.org", hostname)
   content = """<VirtualHost *:443>
  ServerName mail.example.org
  DocumentRoot /var/lib/roundcube/public_html
  Include /etc/roundcube/apache.conf
  Alias /adminer /usr/share/adminer/adminer
  Alias /admin /var/www/ispmailadmin
  <Location /rspamd>
    Require all granted
  </Location>

  RewriteEngine On
  RewriteRule ^/rspamd$ /rspamd/ [R,L]
  RewriteRule ^/rspamd/(.*) http://localhost:11334/$1 [P,L]

  SSLEngine on
  SSLCertificateFile /etc/letsencrypt/live/mail.example.org/fullchain.pem
  SSLCertificateKeyFile /etc/letsencrypt/live/mail.example.org/privkey.pem
</VirtualHost>"""
   content = replace_in_string(content, "mail.example.org", hostname)
   to_file(filename, content)

   # Enable reverse proxy and restart Apache
   command = "a2enmod proxy_http"
   process_command(command)
   command = "systemctl restart apache2"
   process_command(command)

   return()

# STEP 13: Finalize Installation

def finalize_installation():
   """
   Restart services and fix permissions
   """

   commands = ["chown -R www-data:www-data /var/www/",
      "chmod -R 770 /var/www/",
      "systemctl restart apache2",
      "systemctl restart dovecot",
      "systemctl restart postfix",
      "systemctl restart rspamd"]

   for command in commands:
      process_command(command)

   return()

# STEP 14: Produce DNS Documents

def produce_dns_documents():
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
      config2 = 'TXT @ "v=spf1 mx -all"\n'
      config3 = 'TXT _dmarc "v=DMARC1; aspf=s; adkim=s; pct=100; p=reject; rua=mailto:postmaster@' + domain + '"\n'
      config4 = 'TXT ' + today + '._domainkey "v=DKIM1; k=rsa;" "p=' + key + '"\n'
      dns_config = config0 + config1 + config2 + config3 + config4
      to_file(dns_config_file, dns_config)

   return()

# STEP 15: Prepare Password File

def prepare_password_file():
   """
   Print all generated password (or others too if print_all_passwords flag is set) in 
   password file
   """
   print_passwords = (mailadminpwauto or mailserverpwauto or rspamdpwauto)
   print_passwords = (print_passwords or ispmailadminpwauto or print_all_passwords)
   if print_passwords:
      filename = passwordfile
      content = ""
      if mailadminpwauto or print_all_passwords:
         content += "mailadminpw: " + mailadminpw + "\n"
      if mailserverpwauto or print_all_passwords:
         content += "mailserverpw: " + mailserverpw + "\n"
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

   return()

# MAIN FUNCTION


def main():

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
   distro, release, distro_release = get_distro_release()
   if not (("Ubuntu" in distro) or ("Debian GNU/Linux" in distro)):
      print("This program runs on Debian or Ubuntu only, exiting!")
      exit(13)

   # Check releases other than Ubuntu 22.04, 24.04, and Debian 11, 12
   if (distro_release not in supported_releases):
      print("Your release ", distro_release, " is not supported.")
      print("Press Enter to continue anyway, CTRL-C to exit.")
      input()

   
   # Start applog and errorlog
   start_log(applog)
   start_log(errorlog)

   initialize_parameters()
   apt_install()
   configure_apache()
   db_preparation()
   postfix_mariadb_connection()
   dovecot_setup()
   postfix_dovecot_connection()
   configure_quotas()
   roundcube_configuration()
   send_mails_to_postfix()
   rspamd_configuration()
   dkim_configuration()
   ispmailadmin_configuration()
   finalize_installation()
   produce_dns_documents()
   prepare_password_file()

   # Finished
   print("Operation completed, you can check installation log: ispmail.log")
   print("For possible errors check error log: ispmail.error.log")
   print(line_separator)
   print("The following information file(s) are created as reference to DNS configuration.")
   print("Configure your DNS according to them, and your mail server will be ready:")
   for domain in domains:
      print(domain + ".dns.config")
   print(line_separator)
   print("The following file has your generated passwords (if any),")
   print("or all of your passwords if you set the print_all_passwords flag: ")
   print(passwordfile)


if __name__ == "__main__":
   main()