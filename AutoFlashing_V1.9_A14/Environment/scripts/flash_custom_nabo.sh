#!/bin/bash
exit=false
SERIAL=${1}
batFile=${2}
fastboot()
{
	local i=0
	while [ $i -lt 5 ] && ! $(which fastboot) $@
	do
		i=$((i+1))
		echo "Retrying..."
	done
	if [ $i -eq 5 ] ; then
		echo "Permanent flashing error. Exiting"
		exit=true
	fi 
}

if [ -f "$batFile" ]; then
    echo "fastboot flash start!!"
    while [ $exit != true ] && read line
    do
        if [[ $line =~ "::" || $line =~ "rem" ]]; then
            echo "Skip "$line
        else
        	FILE=/userdata_assets.img
        	if [[ $line =~ "fastboot" ]]; then
        		echo "[Convert from line: "$line"]"
        		IFS=' '
        		read -ra aarr <<< "$line"
        		arraylength=${#aarr[@]}
        		commandd=${aarr[0]}" -s $SERIAL "
        		for (( i = 1; i < $arraylength; i++ )); do
        			commandd+=${aarr[i]}" "
        		done
        		echo "$commandd"
        		if [[ -f FILE && $commandd =~ "userdata_assets.img" ]];then
        			echo "Lenh duoc thu thi $commandd"
        			$commandd
        		elif [[ -f FILE && $commandd =~ "userdata.img" ]];then
        			echo "file userdata_assets.img exist"
        		elif [[ ! -f FILE && $commandd =~ "userdata_assets.img" ]];then
        			echo "file userdata_assets.img not exist"
        		elif [[ ! -f FILE && $commandd =~ "userdata.img" ]];then
        			echo "Lenh duoc thu thi $commandd"
        			$commandd
        		else
        		  echo "Lenh duoc thu thi $commandd"
        			$commandd
        		fi
        		
        	else
        		echo "Non fastboot" $line
        		#$line
        	fi
        fi
    done < $batFile
else
    echo "$batFile not exist"
    echo "File fastboot**.bat and fastboot**.sh must be in the same folder. "
fi
