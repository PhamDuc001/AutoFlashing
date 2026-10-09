#!/bin/bash
list_plan=()
workSpace=$PWD
home=$HOME
# Function to read directory and display a list of files
function read_directory() {
  # Get directory path as argument
  dir_path=""$home/Environment/TestPlan""

  # Check if the directory exists
  if [ ! -d "$dir_path" ]; then
    echo "Error: $dir_path is not a valid directory."
    return 1
  fi

  # Iterate through the files in the given directory
  count=0
  for entry in "$dir_path"/*; do
    if [ -f "$entry" ]; then
      ((count++))
      echo "$count) $entry"
      list_plan[$count]=$entry
    fi
  done

  # Check if there are any files
  if [ $count -eq 0 ]; then
    echo "Directory is empty."
    return 1
  fi
}

# Function to get user choice
function get_user_choice() {
  # Display prompt
  #echo "Enter the number corresponding to the file you want to select:"

  # Read user choice
  read -r choice
  #echo $count
  # Check if the choice is valid
  if [ $choice -lt 1 -o $choice -gt $count ]; then
    echo "Invalid choice. Please enter a number from 1 to $count."
    return 1
  fi

  # Return the path of the selected file
  echo "${list_plan[$((choice))]}"
}


# Read directory and display list of files
read_directory

# Get user choice
selected_file=$(get_user_choice)
echo $selected_file $workSpace
python3 AutoRetry.py -p $selected_file -w $workSpace

