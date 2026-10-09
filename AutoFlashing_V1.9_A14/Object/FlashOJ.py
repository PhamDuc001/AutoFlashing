class flashOJ:
    def __init__(self,project,testSuite,seri,mtc):
        self.project=project
        self.serial_list = seri
        self.testSuite = testSuite
        self.sw_path = None
        self.dpi=None
        self.mtc_ver=None
        self.gsi_ver=None
    def add_devices(self,seriallist):
        self.serial_list+="-"+seriallist