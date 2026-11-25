STA_IF = 0
class WLAN:
    def __init__(self, i): pass
    def active(self, on=None): return True
    def isconnected(self): return True
    def connect(self, ssid, pwd): pass
    def ifconfig(self): return ("127.0.0.1", "255.0.0.0", "127.0.0.1", "8.8.8.8")
