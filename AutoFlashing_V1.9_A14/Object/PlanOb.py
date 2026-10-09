class Plan:
    def __init__(self,plan,seri,testSuite,toolPath,commandline):
        self.PlanName = plan
        self.serial = seri
        self.testSuite = testSuite
        self.toolPath = toolPath
        self.ListCommand = []
        self.ListCommand.append(commandline)
class commandline:
    def __init__(self,cmd,num,typerun):
        self.command=cmd
        self.numOfRetry=num
        self.typeRun = typerun