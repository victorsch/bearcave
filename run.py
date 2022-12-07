#!/usr/bin/env python

import socket
import os
import json
from datetime import datetime

# Create a list of common Linux files
files = ["bin", "dev", "etc", "home", "lib", "lib64", "media", "mnt", "opt", "proc", "root", "run", "sbin", "srv", "sys", "tmp", "usr", "var"]

# Add some fake users to the list of files
fake_users = ["alice", "bob", "chris", "dave", "eve", "frank", "grace", "hannah", "ian", "jessica"]

# Print a welcome message
print("Awaiting connection...")

# Set the initial fake directory to the root directory
fake_dir = "/"

logs = []
existing_log = ""

# Get the current date
now = datetime.now()
date = now.strftime("%m-%d-%Y")

log_file = f"logs/logs-{date}.json"
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
    
    
# Create a socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Bind the socket to a port
sock.bind(("localhost", 8080))

# Listen for incoming connections
sock.listen(1)

# Accept incoming connections
conn, addr = sock.accept()  
conn.send("Last login: Tue Dec  6 22:21:49 2022".encode())
    
while True:
  # Display the current working directory
  print(f"{fake_dir}$ ", end="")

  # Get the command from the user
  cmd = conn.recv(1024).decode()

  # Split the command into tokens
  tokens = cmd.split()

  # Check if the user wants to exit
  if cmd == "exit":
    break
  
  if (len(tokens) != 0):
    # If the user entered the "ls" command, print a list of common Linux files
    if tokens[0] == "ls":
      if fake_dir == "/home":
        # If the fake_dir is in the home directory, print the fake users
        for user in fake_users:
          print(user, end="  ")
      else:
        # Otherwise, print the common Linux files
        for file in files:
          print(file, end="  ")
      print()

    # If the user entered the "cd" command, pretend to change the working directory
    elif tokens[0] == "cd":
      if len(tokens) == 1:
        # If no directory was specified, pretend to go to the home directory
        fake_dir = "/home"
        print(fake_dir)
      elif tokens[1] == "..":
          # If the user specified "..", pretend to move back to the parent directory
          fake_dir = "/"
          print(fake_dir)
      elif tokens[1] in files:
        # If a valid directory was specified, pretend to go to that directory
        fake_dir = f"/{tokens[1]}"
        print(fake_dir)
      else:
        # If an invalid directory was specified, print an error message
        print("No such file or directory")
    else:
      # If the user entered an invalid command, print an error message
      print("Command not found")

  # Log the user input to a json file
  now = datetime.now()
  date = now.strftime("%m-%d-%Y")
  log = {
    "date": date,
    "input": cmd
  }
  logs.append(log)
  # with open(f"logs-{date}.json", "a") as f:
  #   json.dump(log, f)

f = open(log_file, "w")
json.dump(logs, f)
f.close()