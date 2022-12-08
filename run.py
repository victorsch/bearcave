#!/usr/bin/env python

import uuid
import socket
import os
import json
from datetime import datetime

import base64
from binascii import hexlify
import sys
import threading
import traceback

import paramiko
from paramiko.py3compat import b, u, decodebytes


# setup logging
paramiko.util.log_to_file("demo_server.log")

host_key = paramiko.RSAKey(filename="id_rsa")
# host_key = paramiko.DSSKey(filename='test_dss.key')

print("Read key: " + u(hexlify(host_key.get_fingerprint())))

logs = []
existing_log = ""

class Server(paramiko.ServerInterface):
    # 'data' is the output of base64.b64encode(key)
    # (using the "user_rsa_key" files)
    data = (
        b"AAAAB3NzaC1yc2EAAAABIwAAAIEAyO4it3fHlmGZWJaGrfeHOVY7RWO3P9M7hp"
        b"fAu7jJ2d7eothvfeuoRFtJwhUmZDluRdFyhFY/hFAh76PJKGAusIqIQKlkJxMC"
        b"KDqIexkgHAfID/6mqvmnSJf0b5W8v5h2pI/stOSwTQ+pxVhwJ9ctYDhRSlF0iT"
        b"UWT10hcuO4Ks8="
    )
    good_pub_key = paramiko.RSAKey(data=decodebytes(data))

    def __init__(self):
        self.event = threading.Event()

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_auth_password(self, username, password):
        if (username == "robey") and (password == "foo"):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_publickey(self, username, key):
        print("Auth attempt with key: " + u(hexlify(key.get_fingerprint())))
        if (username == "robey") and (key == self.good_pub_key):
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_with_mic(
        self, username, gss_authenticated=paramiko.AUTH_FAILED, cc_file=None
    ):
        """
        .. note::
            We are just checking in `AuthHandler` that the given user is a
            valid krb5 principal! We don't check if the krb5 principal is
            allowed to log in on the server, because there is no way to do that
            in python. So if you develop your own SSH server with paramiko for
            a certain platform like Linux, you should call ``krb5_kuserok()`` in
            your local kerberos library to make sure that the krb5_principal
            has an account on the server and is allowed to log in as a user.
        .. seealso::
            `krb5_kuserok() man page
            <http://www.unix.com/man-page/all/3/krb5_kuserok/>`_
        """
        if gss_authenticated == paramiko.AUTH_SUCCESSFUL:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_auth_gssapi_keyex(
        self, username, gss_authenticated=paramiko.AUTH_FAILED, cc_file=None
    ):
        if gss_authenticated == paramiko.AUTH_SUCCESSFUL:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def enable_auth_gssapi(self):
        return True

    def get_allowed_auths(self, username):
        return "gssapi-keyex,gssapi-with-mic,password,publickey"

    def check_channel_shell_request(self, channel):
        self.event.set()
        return True

    def check_channel_pty_request(
        self, channel, term, width, height, pixelwidth, pixelheight, modes
    ):
        return True

# Get the current date
now = datetime.now()
date = now.strftime("%m-%d-%Y")
log_file = f"logs/logs-{date}.json"
# called at the initiation of every session
def setup_log():
  # Create log file if it doesn't exist
  if not os.path.exists(log_file):
      with open(log_file, "w") as f:
          # Initialize the log file with an empty list of logs
          f.write("")
  else:
    try:
      existing_log = json.loads(open(log_file, "r+").read())
      if (len(existing_log) != 0):
        for log in existing_log:
          logs.append(log)
    except json.decoder.JSONDecodeError as e:
      pass
def close_log_session():
  try:
      f = open(log_file, "w")
      json.dump(logs, f)
      f.close()
  except json.decoder.JSONDecodeError as e:
    pass
    
def wait_connection():
  # Create a socket
  sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  # Bind the socket to a port
  sock.bind(("localhost", 8080))
  # Print status to console
  print("Awaiting connection...")
  # Listen for incoming connections
  sock.listen(1)
  # Accept incoming connections
  conn, addr = sock.accept() 
  print("Received connection from ")
  return conn, addr

def wait_ssh_connection():
  # now connect
  try:
      sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
      sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
      sock.bind(("", 2222))
  except Exception as e:
      print("*** Bind failed: " + str(e))
      traceback.print_exc()
      sys.exit(1)

  try:
      sock.listen(1)
      print("Listening for connection ...")
      client, addr = sock.accept()
  except Exception as e:
      print("*** Listen/accept failed: " + str(e))
      traceback.print_exc()
      sys.exit(1)

  print("Got a connection!")
  
  try:
    t = paramiko.Transport(client, gss_kex=False)
    t.set_gss_host(socket.getfqdn(""))
    try:
        t.load_server_moduli()
    except:
        print("(Failed to load moduli -- gex will be unsupported.)")
        raise
    t.add_server_key(host_key)
    server = Server()
    try:
        t.start_server(server=server)
    except paramiko.SSHException:
        print("*** SSH negotiation failed.")
        sys.exit(1)

    # wait for auth
    chan = t.accept()
    if chan is None:
        print("*** No channel.")
        sys.exit(1)
    print("Authenticated!")

    server.event.wait(10)
    if not server.event.is_set():
        print("*** Client never asked for a shell.")
        sys.exit(1)
    return chan, addr
    # chan.send("\r\n\r\nWelcome to my dorky little BBS!\r\n\r\n")
    # chan.send(
    #     "We are on fire all the time!  Hooray!  Candy corn for everyone!\r\n"
    # )
    # chan.send("Happy birthday to Robot Dave!\r\n\r\n")
    # chan.send("Username: ")
    # f = chan.makefile("rU")
    # username = f.readline().strip("\r\n")
    # chan.send("\r\nI don't like you, " + username + ".\r\n")
    # chan.close()

  except Exception as e:
      print("*** Caught exception: " + str(e.__class__) + ": " + str(e))
      traceback.print_exc()
      try:
          t.close()
      except:
          pass
      sys.exit(1)
  
def emulate_shell(conn, remote_addr):
  session_guid = str(uuid.uuid1())
  setup_log()
  
  # Create a list of common Linux files
  files = ["bin", "dev", "etc", "home", "lib", "lib64", "media", "mnt", "opt", "proc", "root", "run", "sbin", "srv", "sys", "tmp", "usr", "var"]

  # Add some fake users to the list of files
  fake_users = ["alice", "bob", "chris", "dave", "eve", "frank", "grace", "hannah", "ian", "jessica"]

  # Set the initial fake directory to the root directory
  fake_dir = "/"

  fake_user = "root"
  
  conn.send("Last login: Tue Dec  6 22:21:49 2022 \r\n\r\n")
  
  while True:
    try:
      # Display the current working directory
      conn.send(f"\r\n{fake_dir}$ ")

      # Get the command from the user
      data = b""
      while not data.endswith(b"\n"):
        chunk = conn.recv(1024)
        data += chunk
        if not chunk:
            continue
      #f = conn.makefile("rU")
      #cmd = f.readline().strip("\r\n")
    
      # Split the command into tokens
      tokens = data.decode().split()

      # Check if the user wants to exit
      if cmd == "exit":
        conn.close()
        return True
      
      print(f"Printing response to command: {cmd}")
          
      if (len(tokens) != 0):
        first_command = tokens[0]
        conn.send("\r\n\r\n")
        # If the user entered the "ls" command, print a list of common Linux files
        if tokens[0] == "ls":
          if fake_dir == "/home":
            # If the fake_dir is in the home directory, print the fake users
            for user in fake_users:
              conn.send((user + " ").encode())
          else:
            # Otherwise, print the common Linux files
            for file in files:
              conn.send((file + " ").encode())
          conn.send("\n".encode())

        # If the user entered the "cd" command, pretend to change the working directory
        elif tokens[0] == "cd":
          if len(tokens) == 1:
            # If no directory was specified, pretend to go to the home directory
            fake_dir = "/home"
            conn.send((fake_dir + "\n").encode())
          elif tokens[1] == "..":
              # If the user specified "..", pretend to move back to the parent directory
              fake_dir = "/"
              conn.send(fake_dir.encode())
          elif tokens[1] in files:
            # If a valid directory was specified, pretend to go to that directory
            fake_dir = f"/{tokens[1]}"
            conn.send(fake_dir.encode())
          else:
            # If an invalid directory was specified, print an error message
            conn.send("No such file or directory \n".encode())
          
        # If the user entered the "whoami" command, print the current user
        elif tokens[0] == "whoami":
          conn.send(f"{fake_user}\n".encode())
        elif tokens[0] == "exit":
          conn.close()
          return True
        elif tokens[0] == "magic":
          conn.close()
          return False
        else:
          # If the user entered an invalid command, print an error message
          conn.send(f"-bash: {first_command}: command not found \n".encode())
      else:
        conn.send("\n".encode())
      # Log the user input to a json file
      now = datetime.now()
      date = now.strftime("%m-%d-%Y %H:%M:%S")
      log = {
        "log_guid": str(uuid.uuid1()),
        "session_guid": session_guid,
        "date": date,
        "remote_addr": str(remote_addr[0]),
        "command": cmd
      }
      logs.append(log)
    except BrokenPipeError as e:
      print("Connection was broken.")
      f = open(log_file, "w")
      json.dump(logs, f)
      f.close()
      return True
    except ConnectionResetError as e:
      print("Connection was reset.")
      f = open(log_file, "w")
      json.dump(logs, f)
      f.close()
      return True
    except KeyboardInterrupt as e:
      print("Connection was interrupted by keyboard.")
      f = open(log_file, "w")
      json.dump(logs, f)
      f.close()
      return True

  

# Main function
if __name__ == "__main__":
  
  
  
  clean_exit = True
  while clean_exit:
    connHandle, remote_addr = wait_ssh_connection()
    print(f"Session initiated with {remote_addr}")
    clean_exit = emulate_shell(connHandle, remote_addr)
    close_log_session()