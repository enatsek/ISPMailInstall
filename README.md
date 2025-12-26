# ISPMailInstall v.0.3.0

- Multi Domain Mail Server Installation Tool for Debian 12, 13 and Ubuntu 22.04, 24.04 Linux

Totally based on ISPMail Tutorial by Christoph Haas at https://workaround.org/ispmail

ISPMail is a very detailed and intensive tutorial for installing a full featured mail server, prepared by Christoph Haas. You can reach it at at https://workaround.org/ispmail

ISPMailInstall is a Python3 program written by me. It is named ispmail.py. The program is written to implement the tutorial. That means, everything you are expected to do on your server is implemented by the program.

The program needs some parameters to run, they are explained in Technical Details section. There is a ispmail.conf file, which contains the sample configurations. After you change it with your parameters, you can run ispmail.py.

ispmail.py python script installs and configures everything necessary on your server.

Server must be freshly installed to guarantee working. After the full installation you will have a fully functional mail server with following options:
- Web based free SSL encrytpted Domain and User Management
- Unlimited Multi Domain Structure
- Unlimited Mail Users
- Unlimited Mail Space (Limited by your disk size)
- Spf, Dmarc and DKIM support
- Web based free SSL encrytpted mail interface for users
- Web based free SSL encrytpted database management
- Spam filtering and spam/ham learning on user base
- Web based free SSL encrytpted spam management
- Support for Thunderbird and many other mail clients.
- All Open Source components.

Everything in the tutorial is applied except following 3:
- Blocking Malware: I decided to skip it because imho it needs a little bit too much resources.
- Firewalling and Brute Force Mitigation: I thought not everyone wants to run a firewall.
- Server Based Mail Encryption: It was already optional

Following applications will be installed:
- Apache: Web Server
- PHP: Programming Language
- MariaDB: Database Server
- Adminer: Database Management
- Postfix: Mail Server
- RspamD: Spam Handler
- Dovecot: IMAP, POP3 and SMTP Server
- Roundcube: Webmail
- ISPMailAdmin: ISP Mail Admin
- Certbot: Automatic free TLS (SSL) acquirer

Database Structure: - A database named mailserver will be created for domain and user management. Also the following DB users will be created with the specified grants:
- mailadmin: all grant for mailserver database. Used by postfix, dovecot, rspamd and ispmailadmin. (mailadminpw)
- mailserver: read grant for mailserver database. Used by postfix dovecot and rspamd. (mailserverpw)
- admin: All grant for all databases. To be used for Adminer. You can login to admined with these user. (dbadminpw)
- Rspamd require a password for the web interface. (rspamdpw)
- ISPMailAdmin requires a password for the web interface. (ispmailadminpw)

- A fresh installed Debian 12, 13 or Ubuntu 22.04, 24.04 Server
- The hostname of the server must be in mail.example org format and both A and PTR DNS Records must be present (otherwise your mails could be considered as spam)
- The domains to host must be decided. (example.org, example.com, example.net)
- Python3 must be present (it is present at default Debian and Ubuntu Servers)

- ispmail.py must be run by root or sudo. The script asks for the hostname, domains to host, and 5 passwords for the configuration. You may include domains and passwords in a .conf file (ispmail.conf), enter when script runs or may ask the script to generate passwords for you.

-After the configuration completed, you need to make necessary DNS configurations for the hosted domains. All the necessary DNS configurations will be supplied by the script.

You can download ispmail.py and ispmail.conf sample configuration files at my github.

- Login to ISPMailAdmin with admin username and ispmailadminpw password at https://mail.example.org/admin to create and manage mail users.
- Login to Adminer interface with mailadmin username and mailadminpw password at https://mail.example.org/adminer , if you need to manage the databases.
- Login to RspamD management with rspamdpw password at https://mail.example.org/rspamd if you want to view or manage rspamd.
- All users can login to webmail interface at https://mail.example.org with their email address as username (user@example.org) and mail password as password.
- Users can use Thunderbird (or another mail client) to reach their mails. 

***Remember to change all occurences of mail.example.org to your hostname


