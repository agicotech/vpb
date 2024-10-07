from py3xui.inbound import *
import logging
import requests

def get_cert(host, session) -> dict:
    resp = requests.post(f'{host}/server/getNewX25519Cert', cookies={'3x-ui': session})
    if resp.status_code == 200:
        resp = resp.json()
    else:
        logging.warning(f'Troubles to reach a cert: {resp.status_code}')
        return {}
    return resp.get('obj')

def gen_inbound_reality(host, session):
    settings = Settings()
    tcp_settings = {
    "acceptProxyProtocol": False,
    "header": {"type": "none"},
        }
    sniffing = Sniffing(enabled=True)
    cert = get_cert(host, session)
    realitySettings = {
        "show": False,
        "xver": 0,
        "dest": "yahoo.com:443",
        "serverNames": [
                    "yahoo.com",
                    "www.yahoo.com"
                        ],
        'privateKey': cert['privateKey'],
        "settings":{
            "publicKey":cert['publicKey']
        }
    }

    stream_settings = StreamSettings(security="reality", network="tcp", realitySettings=realitySettings, tcp_settings=tcp_settings)
    inbound = Inbound(
        id=1488,
        enable=True,
        port=4430,
        protocol="vless",
        settings=settings,
        stream_settings=stream_settings,
        sniffing=sniffing,
        remark='API inbound')
    return inbound