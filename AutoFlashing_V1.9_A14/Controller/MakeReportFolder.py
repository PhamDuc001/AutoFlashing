import argparse
import shutil
import subprocess

class color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'
def run_script(path):
    print(color.BOLD + "Start run command: [{}]".format(path) + color.END)
    p1 = subprocess.Popen(path, stdout=subprocess.PIPE, stderr=subprocess.PIPE,universal_newlines=True)
    # output, error = p1.communicate()
    for line in p1.stdout:
        print(line,end=' ')
    p1.wait()
    print(color.BOLD + "Complete command: [{}]".format(path) + color.END)

parser = argparse.ArgumentParser(description='This is push notification to Windows',argument_default=0)
parser.add_argument('-p', '--test_result', help='Path to XML file')
parser.add_argument('-m', '--module', help="Module name")
args=parser.parse_args()
path = str(args.test_result)
ModuleName = args.module
resultName = path[len(path) - 35:len(path) - 16]
ReportFolder = path[0:len(path) - 44] + "/Report"
LogFolder = path[0:len(path) - 44] + "/logs"
tempModuleFol = ReportFolder + "/" + ModuleName
resultModule = tempModuleFol + "/results/"
logModule = tempModuleFol + "/logs/"
run_script(["cp","-r",path[0:len(path) - 16],resultModule])
run_script(["cp","-r",path[0:len(path) - 16] + ".zip",resultModule])
run_script(["cp","-r",LogFolder + "/" + resultName,logModule])
# try:
#     shutil.copytree(path[0:len(path) - 16], resultModule + "/" + resultName)
# except shutil.Error:
#     print("Fail Copy")
# try:
#     shutil.copy2(path[0:len(path) - 16] + ".zip", resultModule)
# except shutil.Error:
#     print("Fail Copy")
# try:
#     shutil.copytree(LogFolder + "/" + resultName, logModule + "/" + resultName)
# except shutil.Error:
#     print("Fail Copy")