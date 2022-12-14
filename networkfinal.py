#!/usr/bin/env python

# Copyright (C) 2003-2007  Robey Pointer <robeypointer@gmail.com>
#
# This file is part of paramiko.
#
# Paramiko is free software; you can redistribute it and/or modify it under the
# terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# Paramiko is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with Paramiko; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301 USA.

# based on code provided by raymond mosteller (thanks!)

import base64  #importing modules for the code
import getpass
import os
import socket
import sys
import traceback # see above 

import paramiko
from paramiko.py3compat import input #importing specific module from paramiko for use


# setup logging
paramiko.util.log_to_file("demo_sftp.log") # where log file is located

# Paramiko client configuration
UseGSSAPI = True  # enable GSS-API / SSPI authentication
DoGSSAPIKeyExchange = True  # will exchange public keys between clients
Port = 22. # connection port / SSH

# get hostname
username = ""
if len(sys.argv) > 1: #checks if there is a username and host on file len>1 
    hostname = sys.argv[1]
    if hostname.find("@") >= 0:
        username, hostname = hostname.split("@") #will split into user name and host name
else:
    hostname = input("Hostname: ") # if no hostname then user will input one
if len(hostname) == 0:  #validates that a hostname is present
    print("*** Hostname required.") #if no hostname will print this line
    sys.exit(1)

if hostname.find(":") >= 0:
    hostname, portstr = hostname.split(":")
    Port = int(portstr) #designates port an integer


# get username
if username == "":
    default_username = getpass.getuser()
    username = input("Username [%s]: " % default_username) #parses username
    if len(username) == 0:
        username = default_username
if not UseGSSAPI:  #generic security service
    password = getpass.getpass("Password for %s@%s: " % (username, hostname)) #defines how the user and host is formatted
else:
    password = None


# get host key, if we know one..... searches both locations for ssh key to known hosts
hostkeytype = None
hostkey = None
try:
    host_keys = paramiko.util.load_host_keys(
        os.path.expanduser("~/.ssh/known_hosts")
    )
except IOError:
    try:
        # try ~/ssh/ too, because windows can't have a folder named ~/.ssh/
        host_keys = paramiko.util.load_host_keys(
            os.path.expanduser("~/ssh/known_hosts")
        )
    except IOError:
        print("*** Unable to open host keys file")
        host_keys = {}

if hostname in host_keys:
    hostkeytype = host_keys[hostname].keys()[0]
    hostkey = host_keys[hostname][hostkeytype]
    print("Using host key of type %s" % hostkeytype)


# now, connect and use paramiko Transport to negotiate SSH2 across the connection
try:
    t = paramiko.Transport((hostname, Port))
    t.connect(
        hostkey,
        username,
        password,
        gss_host=socket.getfqdn(hostname),
        gss_auth=UseGSSAPI,
        gss_kex=DoGSSAPIKeyExchange,
    )
    sftp = paramiko.SFTPClient.from_transport(t)

    # dirlist on remote host
    dirlist = sftp.listdir(".")
    print("Dirlist: %s" % dirlist) #prints directory list on remote system

    # copy this demo onto the server
    try:
        sftp.mkdir("demo_sftp_folder") #makes the directory on remote system
    except IOError:
        print("(assuming demo_sftp_folder/ already exists)")
    with sftp.open("demo_sftp_folder/README", "w") as f:
        f.write("This was created by demo_sftp.py.\n")
    with open("demo_sftp.py", "r") as f:
        data = f.read()
    sftp.open("demo_sftp_folder/demo_sftp.py", "w").write(data)
    print("created demo_sftp_folder/ on the server")

    # copy the README back here
    with sftp.open("demo_sftp_folder/README", "r") as f: # puts readme file in directory
        data = f.read()
    with open("README_demo_sftp", "w") as f:
        f.write(data)
    print("copied README back here")

    # BETTER: use the get() and put() methods
    sftp.put("demo_sftp.py", "demo_sftp_folder/demo_sftp.py")
    sftp.get("demo_sftp_folder/README", "README_demo_sftp")

    t.close()

except Exception as e:
    print("*** Caught exception: %s: %s" % (e.__class__, e)) #error checking
    traceback.print_exc()
    try:
        t.close()
    except:
        pass
    sys.exit(1)