#!/usr/bin/env python

import os

# Set the initial working directory to the root directory
os.chdir("/")

# Create a list of common Linux files
files = ["bin", "dev", "etc", "home", "lib", "lib64", "media", "mnt", "opt", "proc", "root", "run", "sbin", "srv", "sys", "tmp", "usr", "var"]

# Print a welcome message
print("Welcome to the fake Linux terminal honeypot")

while True:
  # Display the current working directory
  cwd = os.getcwd()
  print(f"{cwd}$ ", end="")

  # Get the command from the user
  cmd = input()

  # Split the command into tokens
  tokens = cmd.split()

  # Check if the user wants to exit
  if cmd == "exit":
    break

  # If the user entered the "ls" command, print a list of common Linux files
  if tokens[0] == "ls":
    for file in files:
      print(file, end="  ")
    print()

  # If the user entered the "cd" command, change the working directory
  elif tokens[0] == "cd":
    if len(tokens) == 1:
      # If no directory was specified, go to the home directory
      os.chdir("/home")
    elif tokens[1] in files:
      # If a valid directory was specified, go to that directory
      os.chdir(f"/{tokens[1]}")
    else:
      # If an invalid directory was specified, print an error message
      print("No such file or directory")
  else:
    # If the user entered an invalid command, print an error message
    print("Command not found")