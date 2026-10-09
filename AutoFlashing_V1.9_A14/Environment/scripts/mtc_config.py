import argparse
import subprocess
import sys
import pexpect

def agruments():
    parser = argparse.ArgumentParser(description='parse an XML file')
    parser.add_argument('-t', '--project', help='type of project')
    parser.add_argument('-p', '--mtcPath', help='Path to mtc file')
    parser.add_argument('-s', '--serial', help='Screen DPI')
    args = parser.parse_args()
    prject = str(args.project)
    mtcPath = str(args.mtcPath).replace("\\", "/")
    mtcPath.replace("//", "/")
    seri = str(args.serial)
    return prject, mtcPath,seri
def run_script(path):
    print("Run scripts ", path)
    p1 = subprocess.Popen(path, stdout=subprocess.PIPE, stderr=subprocess.PIPE,universal_newlines=True)
    # output, error = p1.communicate()
    for line in p1.stdout:
        print(line,end=' ')
    p1.wait()
def mtc_config_160dpi(path,serial):
    try:
        argss = "-s "+serial
        child = pexpect.spawn(path,[argss],encoding='utf-8',timeout=1000,maxread=5000)
        child.logfile = sys.stdout
        child.expect("Please select a vehicle type from above list:")
        child.sendline("11")
        child.expect("Do you want to select VC \(vehicle check\) configuration\?")
        child.sendline("y")
        child.expect("Please select a vehicle configuration")
        child.sendline("16")
        child.expect("Do you want to set screen out to hmdi")
        child.sendline("n")
        child.expect("Do you want to use default fake assets")
        child.sendline("y")
        child.expect(pexpect.EOF)
    except Exception as e:
        print(e)
def mtc_config_180dpi(path,serial):
    argss = "-s " + serial
    child = pexpect.spawn(path, [argss],encoding='utf-8',timeout=1000,maxread=5000)
    child.logfile = sys.stdout
    child.expect("Please select a vehicle type from above list:")
    child.sendline("2")
    child.expect("Do you want to select VC \(vehicle check\) configuration\?")
    child.sendline("y")
    child.expect("Please select a vehicle configuration")
    child.sendline("21")
    child.expect("Do you want to set screen out to hmdi")
    child.sendline("n")
    child.expect("Do you want to use default fake assets")
    child.sendline("y")
    child.expect(pexpect.EOF)
def mtc_config_nissan(path,serial):
    with open(path, "r") as f:
        for line in f:
            line_temp = (line.rstrip())
            if str(line_temp).startswith("adb"):
                adbcommand=line_temp.split(" ")
                adbcommand.insert(1,"-s")
                adbcommand.insert(2, serial)
                run_script(adbcommand)
            elif str(line_temp).startswith("timeout"):
                adbcommand = line_temp.split(" ")
                run_script(["sleep",adbcommand[2]])
if __name__ == '__main__':
    project,mtc_path,serial = agruments()
    if project == "ACCESS_DA_160":
        mtc_config_160dpi(mtc_path,serial)
    elif project == "ACCESS_DA_180":
            mtc_config_180dpi(mtc_path,serial)
    elif project.__contains__("NISSAN"):
        mtc_config_nissan(mtc_path,serial)
