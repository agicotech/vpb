import os
from consts import *
from requests import get

def try_get(url):
    try:
        resp = get(url)
        return True
    except:
        return False

class Proto_detector:
    def __init__(self):
        self.available = set()

    def __call__(self) -> set:
        self.available = set()
        for name, method in self.__class__.__dict__.items():
            if name.startswith('detect_'):
                pr = method.__func__()
                if pr:
                    self.available.add(pr)
        return self.available

    @classmethod
    def detect_Outline():
        return "Outline" if OUTLINE_SHA and len(OUTLINE_SHA) else None

    @classmethod
    def detect_VLESS():
        return "VLESS" if XUI_HOST and len(XUI_HOST) and try_get(XUI_HOST) else None
    
    @classmethod
    def detect_WG():
        return "WireGuard" if os.path.exists('./wireguard.sh') else None

    @classmethod
    def detect_OpenVpn():
        return "OpenVPN" if os.path.exists('./openvpn.sh') else None