#!/bin/bash
URL_SW=${1}
PROJECT_TYPE=${2}
TEST_SUITE=${3}
TEST_SUITE_VERSION=${4}
MTC_CONFIG_VERSION=${5}
TEST_PLAN=${6}
WORK_SPACE=${7}
RUN_PROCESS=${8}
DEVICES_LIST=${9}
SCREEN_DPI=${10}
GSI_IMAGE_VERSION=${11}
foldersw="$WORK_SPACE/Environment/Storage/Binary/"
mtc_config_file="/home/lge/Environment/MTC/$PROJECT_TYPE/$MTC_CONFIG_VERSION"
gsi_image_file="/home/lge/Environment/GSI_IMAGE/$GSI_IMAGE_VERSION"
planFile="$WORK_SPACE/Environment/TestPlan/$TEST_PLAN"
export CI=""
echo "lge@1234" | sudo -S chmod +x -R $WORK_SPACE
cd $WORK_SPACE/
echo $RUN_PROCESS
tmux kill-session -t "AutoRetry"
if [[ "$PROJECT_TYPE" == "NISSAN_DA" ]]; then
    case "$RUN_PROCESS" in
    "Download_FLash_RunTest")
      python3 DownloadSW.py -sw $URL_SW -t $mtc_config_file -w $WORK_SPACE
      sleep 20
      python3 AutoFlashing.py -p $foldersw -t $PROJECT_TYPE -i $TEST_SUITE -w $WORK_SPACE -k $DEVICES_LIST
      sleep 20
      byobu-tmux new-session -d -s "AutoRetry"
      tmux send-keys -t "AutoRetry" "cd $WORK_SPACE" Enter
      tmux send-keys -t "AutoRetry" "python3 AutoRetry.py -t $TEST_SUITE -v $TEST_SUITE_VERSION -p $planFile -w $WORK_SPACE" Enter
      ;;
    "Only_Flashing")
      python3 DownloadSW.py -sw $URL_SW -t $mtc_config_file -w $WORK_SPACE
      sleep 20
      python3 AutoFlashing.py -p $foldersw -t $PROJECT_TYPE -i $TEST_SUITE -w $WORK_SPACE -k $DEVICES_LIST
      sleep 20
      ;;
    "Only_Run_Test")
      echo "Only TEST"
      byobu-tmux new-session -d -s "AutoRetry"
      tmux send-keys -t "AutoRetry" "cd $WORK_SPACE" Enter
      tmux send-keys -t "AutoRetry" "python3 AutoRetry.py -t $TEST_SUITE -v $TEST_SUITE_VERSION -p $planFile -w $WORK_SPACE" Enter
      ;;
    esac
elif [[ "$PROJECT_TYPE" == "ACCESS_DA" ]]; then
    case "$RUN_PROCESS" in
    "Download_FLash_RunTest")
      python3 DownloadSW.py -sw $URL_SW -t $mtc_config_file -w $WORK_SPACE
      sleep 20
      python3 AutoFlashing.py -p $foldersw -t $PROJECT_TYPE -i $TEST_SUITE -d $SCREEN_DPI -w $WORK_SPACE -k $DEVICES_LIST
      sleep 20
      byobu-tmux new-session -d -s "AutoRetry"
      tmux send-keys -t "AutoRetry" "cd $WORK_SPACE" Enter
      tmux send-keys -t "AutoRetry" "python3 AutoRetry.py -t $TEST_SUITE -v $TEST_SUITE_VERSION -p $planFile -w $WORK_SPACE" Enter
      ;;
    "Only_Flashing")
      python3 DownloadSW.py -sw $URL_SW -t $mtc_config_file -w $WORK_SPACE
      sleep 20
      python3 AutoFlashing.py -p $foldersw -t $PROJECT_TYPE -i $TEST_SUITE -d $SCREEN_DPI -w $WORK_SPACE -k $DEVICES_LIST
      sleep 20
      ;;
    "Only_Run_Test")
      echo "Only TEST"
      byobu-tmux new-session -d -s "AutoRetry"
      tmux send-keys -t "AutoRetry" "cd $WORK_SPACE" Enter
      tmux send-keys -t "AutoRetry" "python3 AutoRetry.py -t $TEST_SUITE -v $TEST_SUITE_VERSION -p $planFile -w $WORK_SPACE" Enter
      ;;
    esac
elif [[ "$PROJECT_TYPE" == "NISSAN_EU" ]]; then
    case "$RUN_PROCESS" in
    "Download_FLash_RunTest")
      python3 DownloadSW.py -sw $URL_SW -t $mtc_config_file -w $WORK_SPACE
      sleep 20
      if [[ "$TEST_SUITE" == "GSI" || "$TEST_SUITE" == "VTS" ]];
        python3 AutoFlashing.py -p $foldersw -t $PROJECT_TYPE -i $TEST_SUITE -w $WORK_SPACE -g $GSI_IMAGE_VERSION -k $DEVICES_LIST
      else
        python3 AutoFlashing.py -p $foldersw -t $PROJECT_TYPE -i $TEST_SUITE -w $WORK_SPACE -k $DEVICES_LIST
      fi
      sleep 20
      byobu-tmux new-session -d -s "AutoRetry"
      tmux send-keys -t "AutoRetry" "cd $WORK_SPACE" Enter
      tmux send-keys -t "AutoRetry" "python3 AutoRetry.py -t $TEST_SUITE -v $TEST_SUITE_VERSION -p $planFile -w $WORK_SPACE" Enter
      ;;
    "Only_Flashing")
      python3 DownloadSW.py -sw $URL_SW -t $mtc_config_file -w $WORK_SPACE
      sleep 20
      python3 AutoFlashing.py -p $foldersw -t $PROJECT_TYPE -i $TEST_SUITE -w $WORK_SPACE -k $DEVICES_LIST
      sleep 20
      ;;
    "Only_Run_Test")
      echo "Only TEST"
      byobu-tmux new-session -d -s "AutoRetry"
      tmux send-keys -t "AutoRetry" "cd $WORK_SPACE" Enter
      tmux send-keys -t "AutoRetry" "python3 AutoRetry.py -t $TEST_SUITE -v $TEST_SUITE_VERSION -p $planFile -w $WORK_SPACE" Enter
      ;;
    esac
fi

#python3 AutoRetry.py -t $TOOL_FOLDER -p $TEST_PLAN
#echo "FINISH"
