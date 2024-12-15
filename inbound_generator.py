import logging
import requests
import hashlib
import random
from py3xui.inbound import Inbound
from py3xui.inbound import Settings, Sniffing, StreamSettings
from py3xui.client import Client
import uuid

def generate_sids():
    seed = random.randbytes(30)
    sha = hashlib.sha256(seed).hexdigest()
    def get_sid():
        l = random.randint(4, 8)*2
        start = random.randint(0, len(sha)-1-l)
        return sha[start:start+l]

    sids = [get_sid() for _ in range(16)]
    return sids

def get_cert(host: str, session: str) -> dict:
    host = host.strip('/')
    headers = {
    "Accept": "application/json, text/plain, */*",
    "Content-Type":"application/x-www-form-urlencoded; charset=UTF-8",
    "Cookie": f"lang=en-US; 3x-ui={session}"
    }
    resp = requests.post(f'{host}/server/getNewX25519Cert', headers=headers)
    if resp.status_code == 200:
        resp = resp.json()
    else:
        logging.warning(f'Troubles to reach a cert: {resp.status_code}')
        return {}
    return resp.get('obj')

def gen_inbound_reality(host, session, tag = ''):
    tcp_settings = {
    "acceptProxyProtocol": False,
    "header": {"type": "none"},
        }
    clients = [Client(
        email='test',
        enable=True,
        id= str(uuid.uuid1())
    )]
    settings = Settings(decryption="none", clients=clients)
    sniffing = Sniffing(enabled=True)
    cert = get_cert(host, session)
    realitySettings = {
        "show": False,
        "xver": 0,
        "dest": "wikipedia.com:443",
        "serverNames": [
                    "wikipedia.com",
                    "www.wikipedia.com"
                        ],

        'privateKey': cert.get('privateKey', ''),
            "minClient": "",
        "maxClient": "",
        "maxTimediff": 0,
        "shortIds":generate_sids(),
        "settings":{
            "publicKey":cert.get('publicKey', ''),
            "fingerprint": "chrome"
        }
    }

    stream_settings = StreamSettings(security="reality", network="tcp", realitySettings=realitySettings, tcp_settings=tcp_settings)
    inbound = Inbound(up=0, 
                    down=0, 
                    total=0,
                    remark='API inbound',
                    enable=True,
                    expiryTime=0,
                    listen='',
                    port=443,
                    protocol="vless",
                    settings=settings,
                    stream_settings=stream_settings,
                    sniffing=sniffing,
                    tag=tag,)
#                    allocate=Allocate()
    return inbound

if __name__ == '__main__':
    print(generate_sids())