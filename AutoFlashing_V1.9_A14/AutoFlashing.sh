#!/bin/bash
list_gsi=()
workSpace=$PWD
PROJECT_TYPE=()
PROJECT_TYPE[0]="ACCESS_DA"
PROJECT_TYPE[1]="NISSAN_EU"
PROJECT_TYPE[2]="NISSAN_DA"
TEST_ITEM=("CTS" "ATS" "VTS" "STS" "GSI" "ONLY_USERDEBUG" "ONLY_USER" "ONLY_MTC")
TEST_ITEM[0]="CTS"
TEST_ITEM[1]="ATS"
TEST_ITEM[2]="VTS"
TEST_ITEM[3]="STS"
TEST_ITEM[4]="GSI"
TEST_ITEM[5]="ONLY_USERDEBUG"
TEST_ITEM[6]="ONLY_USER"
TEST_ITEM[7]="ONLY_MTC"
MTC_HOME="/home/lge/Environment/MTC"
DPI_LIST=("160" "180")
DPI_LIST[0]="160"
DPI_LIST[1]="180"
GSI_IMAGE_HOME="/home/lge/Environment/GSI_IMAGE"
# Function to read directory and display a list of files
function read_directory() {
  # Get directory path as argument
  local dir_path="$1"
  # Check if the directory exists
  if [ ! -d "$dir_path" ]; then
    echo "Error: $dir_path is not a valid directory."
    return 1
  fi
  # Iterate through the files in the given directory
  local count=0
  for entry in "$dir_path"/*; do
    if [ -f "$entry" ]; then
      ((count++))
      echo "$count) $entry"
      list_gsi[$count]=$entry
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
  # Check if the choice is valid
  if [ $choice -lt 1 -o $choice -gt $1 ]; then
    echo "Invalid choice. Please enter a number from 1 to $1."
    return 1
  fi

  # Return the path of the selected file
  echo "$((choice-1))"
}
count=0
echo "Chooose Type of Project"
for entry in "${PROJECT_TYPE[@]}"; do
  ((count++))
  echo "$count) $entry"
done
temp=$(get_user_choice $count)
PROJECT=${PROJECT_TYPE[$temp]}
echo "$PROJECT"
echo "Chooose Type of Test"
count=0
for entry in "${TEST_ITEM[@]}"; do
  ((count++))
  echo "$count) $entry"
done
temp2=$(get_user_choice $count)
TESTSUITE=${TEST_ITEM[$temp2]}
echo "$TESTSUITE"
echo -n "Input binary path file: "
read ans
BINARY_PATH=$ans
echo $TESTSUITE
# Read directory and display list of files
if [[ "$PROJECT" == "ACCESS_DA" ]]; then
  echo "Chooose screen DPI"
  temp3=$(get_user_choice 2)
  SCREEN_DPI=${DPI_LIST[$temp3]}
  echo "$SCREEN_DPI"
fi
echo -n "Input DEVICES LIST: "
read ansW
DEVICES_LIST=$ansW
echo "Running on $DEVICES_LIST"
read_directory "$GSI_IMAGE_HOME"
dem=0
for element in "${list_gsi[@]}"; do
  listtemp[dem]="${element}"
  ((dem++))
done
if [[ "$TESTSUITE" == "GSI" || "$TESTSUITE" == "VTS" ]]; then
  echo "Chooose GSI image version"
  temp4=$(get_user_choice $dem)
  GSI_IMAGE_FILE=${listtemp[$temp4]}
  echo "$GSI_IMAGE_FILE"
  #echo ${GSI_IMAGE_FILE:(-12):8}
  python3 AutoFlashing.py -p $BINARY_PATH -t $PROJECT -i $TESTSUITE -w $workSpace -g ${GSI_IMAGE_FILE:(-12):8} -k $DEVICES_LIST
elif [[ "$PROJECT" == "ACCESS_DA" ]]; then
  python3 AutoFlashing.py -p $BINARY_PATH -t $PROJECT -i $TESTSUITE -d $SCREEN_DPI -w $workSpace -k $DEVICES_LIST
else
  python3 AutoFlashing.py -p $BINARY_PATH -t $PROJECT -i $TESTSUITE -w $workSpace -k $DEVICES_LIST
fi

# Get user choice
#selected_file=$(get_user_choice)
#echo $selected_file $workSpace
#python3 AutoRetry.py -p $selected_file -w $workSpace

