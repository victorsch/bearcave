#!/usr/bin/env python

import uuid
import socket
import os
import json
from datetime import datetime

logs = []
existing_log = ""

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
  
  conn.send("Last login: Tue Dec  6 22:21:49 2022 \n".encode())
  
  while True:
    try:
      # Display the current working directory
      conn.send(f"{fake_dir}$ ".encode())

      # Get the command from the user
      cmd = conn.recv(1024).decode()

      # Split the command into tokens
      tokens = cmd.split()

      # Check if the user wants to exit
      if cmd == "exit":
        conn.close()
        return True
      
      print("Printing response to command: {cmd}")
          
      if (len(tokens) != 0):
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
          conn.send("Command not found \n".encode())
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

  

# Main function
if __name__ == "__main__":
  clean_exit = True
  while clean_exit:
    connHandle, remote_addr = wait_connection()
    clean_exit = emulate_shell(connHandle, remote_addr)
    close_log_session()