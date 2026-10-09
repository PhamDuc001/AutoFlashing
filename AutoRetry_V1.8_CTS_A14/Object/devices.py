class devices:
    def __init__(self):
        self.serial = None
        self.fingerprint = None
        self.typeOfDevices = None
        self.kb_connect = None
        self.rl_connect = None
        self.kb_doubleClick = None
        self.kb_tribleClick = None
    def setup(self):
        if self.kb_connect != None:
            self.kb_doubleClick = self.kb_connect+self.kb_connect[1]
            self.kb_tribleClick=self.kb_doubleClick+self.kb_connect[1]
if __name__ == '__main__':
    test=devices
    test.setup()