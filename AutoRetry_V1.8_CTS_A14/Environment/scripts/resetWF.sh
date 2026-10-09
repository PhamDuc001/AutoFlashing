#!/bin/bash
Serial=${1}
output=$(adb -s $Serial shell cmd wifi list-networks) 
while IFS= read -r line; do
    if [[ $line =~ "Network" ]]; then
    	echo " "
    else
    	echo ${line:0:1}
    	output2=$(adb -s $Serial shell cmd wifi forget-network ${line:0:1})
    	echo $output2
    fi
done <<< "$output"
