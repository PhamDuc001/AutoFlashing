import argparse
import os
import subprocess
from os import listdir
from pdb import run

import requests
from requests import RequestException

parser = argparse.ArgumentParser(description='This is script to download SW',argument_default=0)
parser.add_argument('-sw', '--linkSW', help='Link to download SW')
parser.add_argument('-t','--linkMTC',help='Link to MTC file')
parser.add_argument('-w','--workspace',help='WorkSpace')
args=parser.parse_args()
link = args.linkSW
workspace=args.workspace
url_api=""
download_base=""
for tp in str(link).split("/"):
    if not tp.__contains__("native") and not tp.__eq__("ui"):
        download_base +=tp+"/"
    if not tp.__contains__("native"):
        url_api+=tp+"/"
    if tp.__eq__("ui"):
        url_api+="api/v1/ui/nativeBrowser/"
        download_base+="artifactory/"
masterFolder = "{}/Environment/Storage/Binary/".format(workspace)
storage_folder = "{}/Environment/Storage/".format(workspace)
try:
    os.mkdir(storage_folder)
except Exception as e:
    print(e)
try:
    os.mkdir(masterFolder)
except Exception as e:
    print(e)
userdebug_link=None
user_link=None
mtc_link=args.linkMTC
def run_command(command):
    print("Start download")
    try:
        process = subprocess.Popen(command,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(e)
    while True:
        output = process.stdout.readline()
        if output.decode("utf-8").__contains__("complete"):
            print("Download finish")
            break
        if output:
            print(output.decode("utf-8"))
def run_command_copy(command):
    print("Start command")
    try:
        process = subprocess.Popen(command,stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except Exception as e:
        print(e)
    output = process.stdout.readline()
    if output:
        print(output.decode("utf-8"))
try:
    respond = requests.get(url_api)
except RequestException as e:
    print(e)
try:
    html=respond.json()
except Exception as e:
    print(e)
try:
    link =html["children"]
except Exception as e:
    print(e)
userDebug_name = None
user_name=None
for line in link:
    if str(line["name"]).__contains__(".tar.gz") and (not str(line["name"]).__contains__("car_emulator") or not str(line["name"]).__contains__("CAR_EMULATOR")):
        if str(line["name"]).__contains__("FULL.YAK") or str(line["name"]).__contains__("ACCESSDA.ANT") or str(line["name"]).__contains__("AIVI2_N_DA2.RIS"):
            if str(line["name"]).__contains__("userdebug"):
                userdebug_link=download_base+str(line["name"])
                userDebug_name = str(line["name"])
            else:
                user_link=download_base+str(line["name"])
                user_name=str(line["name"])
try:
    os.chdir(masterFolder)
except Exception as e:
    print(e)
for dir in listdir(masterFolder):
    if os.path.isfile(os.path.join(masterFolder,dir)):
        if not (user_name.__contains__(dir) or userDebug_name.__contains__(dir) or str(mtc_link).__contains__(dir)):
            run_command_copy(["rm","-r",str(os.path.join(masterFolder,dir))])
if not os.path.exists(os.path.join(masterFolder,userDebug_name)):
    process = subprocess.Popen("rm -r "+masterFolder+"/*", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    process.wait()
    output, error = process.communicate()
    if not error is None:
        for line in error.decode("utf-8").split("\n"):
            print(line)
    if not output is None:
        for ot in output.decode("utf-8").split("\n"):
            print(ot)
    run_command(['/usr/bin/aria2c', '-x16', userdebug_link])
if not os.path.exists(os.path.join(masterFolder,user_name)):
    run_command(['/usr/bin/aria2c', '-x16', user_link])
if mtc_link != 0:
    run_command_copy(['cp', '-r', str(mtc_link),masterFolder])
print("DONE")
