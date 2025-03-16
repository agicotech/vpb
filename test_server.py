import random
from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from typing import Dict, Optional, Literal
import random
from outline_vpn.outline_vpn import OutlineVPN
from fastapi.responses import RedirectResponse
import hashlib
import uuid

from fastapi import FastAPI, Request, Response, status
import hashlib
import os
import re
from consts import API_PASSWORD, API_USERNAME

from py3xui import Api as Api3x, Client as Client3x
from py3xui import Inbound
from inbound_generator import gen_inbound_reality
from proto_detector import Proto_detector

from consts import *
from database import JsonDataBase
import time
import os, subprocess
from requests import get
from urllib.parse import urlencode
from utils import *

MACHINE_IP = my_ip()
FLAG, CITY = get_flag_and_city()
BOT_NAME = f'@agicovpnbot {CITY} {FLAG}'

logger = logging.getLogger()
logger.setLevel(20)
logger.addHandler(logging.StreamHandler())
#Available_Protos = {"IKEv2", 'Outline', 'WireGuard', 'OpenVPN', 'VLESS'} #TODO: Сделать автоматический поиск установленных протоколов
# здесь допишем автоматическое определение установленных на сервере протоколов как-нибудь потом
Available_Protos = Proto_detector()()
logger.info(f'Available protos: {Available_Protos}')
Available_protos_set = set(Available_Protos)

class VPN_Proto():
    """Родительский класс для протоколов, уже сделан"""
    clients: JsonDataBase
    def generate_conf(expire_date: int, max_clients: int) -> dict: ...
    def get_confs() -> dict: ...
    def remove_key(key_id: str):...
    @classmethod
    def renew_conf(cls, key_id: str, renewal_time: int, max_clients: int):
        if not key_id in cls.clients:
            return False
        cls.clients[key_id]['_exp'] += renewal_time
        cls.clients.save()
        return True
    @classmethod
    def save_user(cls, user: dict):
        cls.clients[user['_key_id']] = user
        cls.clients.save()
        


class IKEv2(VPN_Proto):
    clients = JsonDataBase('db_clients_IKEv2')
    clients.load()

    @classmethod
    def save_user(cls, user: dict):
        cls.clients[user['username']] = user
        cls.clients.save()
        
    
    @classmethod
    def generate_conf(cls, expire_date: int, max_clients: int) -> dict:
        username = randomstr(8, with_special = False)
        password = randomstr(12)
        user = {
            "username": username,
            "password": password,
            "_exp": expire_date,
            "_key_id": username,

            #"_key_id": username,
        }
        #TODO: вот сюда надо переписать функцию ниже, логин должен иметь длину 8, пароль - 12
        cls.save_user(user)
        os.system(f'echo \'{username}\n{password}\ny\' | ./add_vpn_user.sh ')
        return user
    @classmethod
    def get_confs(cls) -> dict:
        names = list(cls.clients.keys())
        for name in names:
            client_exp = int(cls.clients[name]['_exp'])
            if not(client_exp > time.time() or client_exp == 0):
                cls.clients.pop(name, None)
        return cls.clients.data
    @classmethod
    def remove_key(cls, key_id: str):
        if cls.clients.pop(key_id, None) is not None:
            os.system(f'echo \'{key_id}\ny\' | ./del_vpn_user.sh ')
            cls.clients.save()
            return True
        else:
            return False
    
class VLESS(VPN_Proto):
    clients = JsonDataBase('db_clients_VLESS')
    clients.load()
    api = Api3x(XUI_HOST, XUI_USERNAME, XUI_PASSWORD, logger=logger) 
    _active_inbound = None
    # Это не я придумал писать хуй - это так в офф примерах к py3xui

    @classmethod
    def _activeinbound(cls) -> Inbound:
        if cls._active_inbound is not None:
            # здесь бы еще проверочку на работоспособность замутить
            return cls._active_inbound
        cls.api.login()
        available_inbounds = cls.api.inbound.get_list()
        if len(available_inbounds) == 0:           
            inbound = gen_inbound_reality(XUI_HOST, cls.api.session, BOT_NAME)
            cls.api.inbound.add(inbound=inbound)
            available_inbounds = cls.api.inbound.get_list()
        cls._active_inbound = available_inbounds[0]
        return cls._active_inbound
    
    @classmethod
    def _generate_token(cls, x3_client_id: str, inbound: Inbound):
        settings = inbound.stream_settings
        reality = settings.reality_settings
        reality_set = reality.get('settings', {})
        pbk = reality_set.get('publicKey', "")
        fp = reality_set.get('fingerprint', '')
        fakehost = reality.get('serverNames', [''])[0]
        sid = random.choice(reality.get('shortIds', ['']))
        query = urlencode(dict(
            type=settings.network,
            security=settings.security,
            pbk=pbk,
            fp=fp,
            sni=fakehost,
            sid=sid
        ))
        token = f'vless://{x3_client_id}@{MACHINE_IP}:{inbound.port}?{query}#{BOT_NAME}'
        #&sid=38&spx=%2F
        return token


    @classmethod
    def generate_conf(cls, expire_date: int = 0, max_clients: int = 5) -> dict:
        key_id = randomstr(10, with_special = False)
        # Надо сгенерировать какой-нибудь id клиенту, чтоб мы не выглядели как ебланы, отдавая юзерам наши внутренние key_id
        # Поэтому ща хэшей насчитаем бля
        seed = hashlib.sha256(key_id.encode('utf-8')).hexdigest()[:32] # Просто первые 32 символа hex хэша от key_id
        user_id = str(uuid.UUID(seed, version=1)) # Генерируем UUID1 Не случайным образом, а на основе hex строки
        client = Client3x(
            email=key_id.lower(), # требование апи
            enable=True,
            id=user_id,
            subId=key_id,
            flow= "",
            limitIp= max_clients,
            expiryTime=0,
            tgId="",
            reset= 0
        )
        cls.api.login()
        inbound = cls._activeinbound() 
        resp = cls.api.client.add(inbound_id=inbound.id, clients=[client])
        token = cls._generate_token(user_id, inbound)
        user = {
            "token": token,
            "_key_id": key_id,
            "_exp": expire_date
        }
        cls.save_user(user)
        return user
    
    @classmethod
    def remove_key(cls, key_id: str):
        if cls.clients.pop(key_id, None) is not None:
            seed = hashlib.sha256(key_id.encode('utf-8')).hexdigest()[:32]
            user_id = str(uuid.UUID(seed, version=1))
            try:
                cls.api.client.delete(cls._activeinbound().id, user_id)
            except:
                logger.warning(f'Error while deleting {key_id} from api')
            cls.clients.save()
            return True
        else:
            return False
    @classmethod
    def get_confs(cls) -> dict:
        names = list(cls.clients.keys())
        for name in names:
            client_exp = int(cls.clients[name]['_exp'])
            if not(client_exp > time.time() or client_exp == 0):
                cls.clients.pop(name, None)
        return cls.clients.data


class Outline(VPN_Proto):
    outline = OutlineVPN(api_url=OUTLINE_API, cert_sha256=OUTLINE_SHA)
    clients = JsonDataBase('db_clients_Outline')
    clients.load()


    @classmethod
    def generate_conf(cls, expire_date: int = 0, max_clients: int = 5) -> dict:
        key_id = randomstr(10, with_special = False)
        key = cls.outline.create_key(key_id=key_id, name=key_id)
        token = f'{key.access_url}#{BOT_NAME}'
        user = {
            "token": token,
            "_key_id": key_id,
            "_exp": expire_date
        }
        cls.save_user(user)
        return user
    
    @classmethod
    def remove_key(cls, key_id: str):
        if cls.clients.pop(key_id, None) is not None:
            cls.outline.delete_key(key_id=key_id)
            cls.clients.save()
            return True
        else:
            return False
    @classmethod
    def get_confs(cls) -> dict:
        names = list(cls.clients.keys())
        for name in names:
            client_exp = int(cls.clients[name]['_exp'])
            if not(client_exp > time.time() or client_exp == 0):
                cls.clients.pop(name, None)
        return cls.clients.data

def file_attachment(filename):
    with open(filename, 'rb') as f:
            fcontent = f.read().decode('utf-8', errors='ignore')
    return [fcontent, filename]

class WireGuard(VPN_Proto):
    clients = JsonDataBase('db_clients_WireGuard')
    clients.load()

    @classmethod
    def generate_conf(cls, expire_date: int = 0, max_clients: int = 5) -> dict:
        key_id = randomstr(10, with_special = False)
        os.system(f'echo \'1\n{key_id}\n2\nN\n\' | ./wireguard.sh ')
        user = {
            "_key_id": key_id,
            "_exp": expire_date
        }
        cls.save_user(user)
        return dict(**user, _file = file_attachment(f'{key_id}.conf') )
    
    @classmethod
    def remove_key(cls, key_id: str):
        if cls.clients.pop(key_id, None) is not None:
            try:
                id_out = subprocess.check_output(f"echo '2' | ./wireguard.sh | grep '{key_id}' | cut -d')' -f1", shell=True)
            except subprocess.CalledProcessError as e:
                id_out = e.output
            if id_out != b'':
                os.system(f"echo  \'3\n{int(id_out)}\ny\' | ./wireguard.sh ")
                cls.clients.pop(key_id)
                cls.clients.save()
                try: os.remove(f'{key_id}.ovpn')
                except: ...
                return True
        else:
            return False
    
    @classmethod
    def get_confs(cls) -> dict:
        names = list(cls.clients.keys())
        for name in names:
            client_exp = int(cls.clients[name]['_exp'])
            if not(client_exp > time.time() or client_exp == 0):
                cls.remove_key(name)
        return cls.clients.data

class OpenVPN(WireGuard):
    clients = JsonDataBase('db_clients_OpenVPN')
    clients.load()

    @classmethod
    def generate_conf(cls, expire_date: int = 0, max_clients: int = 5) -> dict:
        key_id = randomstr(10, with_special = False)

        os.system(f'echo \'1\n{key_id}\n\' | ./openvpn.sh ')
        with open(f'{key_id}.ovpn', 'rb') as f:
            fcontent = f.read().decode('utf-8', errors='ignore')
        user = {
            "_key_id": key_id,
            "_exp": expire_date
        }
        cls.save_user(user)
        return dict(**user, _file= [fcontent, f'{key_id}.ovpn'])
    
    @classmethod
    def remove_key(cls, key_id: str):
        if cls.clients.pop(key_id, None) is not None:
            try:
                id_out = subprocess.check_output(f"echo '3' | ./openvpn.sh | grep '{key_id}' | cut -d')' -f1", shell=True)
            except subprocess.CalledProcessError as e:
                id_out = e.output
            if id_out != b'':
                os.system(f"echo  \'4\n{int(id_out)}\ny\n\' | ./openvpn.sh ")
                cls.clients.pop(key_id)
                cls.clients.save()
                try: os.remove(f'{key_id}.ovpn')
                except: ...
                return True
            else: return False
        else:
            return False


Protos: Dict[str, VPN_Proto] = {"IKEv2" : IKEv2, "Outline": Outline, 'WireGuard': WireGuard, 'OpenVPN': OpenVPN, "VLESS": VLESS}
PROTO_LIT = Literal["IKEv2", "Outline", 'WireGuard', 'OpenVPN', 'VLESS']
PROTO_LIT = Literal[Available_Protos]
print(PROTO_LIT)

class new_user(BaseModel):
    """Класс для работы пост запроса создания нового пользователя"""
    expire_date: Optional[int | float] = 0 # если 0, то логин вечный
    max_clients: Optional[int] = 1


class key_for_removal(BaseModel):
    """Класс для работы пост запроса создания нового пользователя"""
    key_id: str

class data_for_renewal(BaseModel):
    """Класс для работы пост запроса создания нового пользователя"""
    key_id: str
    renewal_time: int = 0 # если 0, то логин вечный
    max_clients: Optional[int] = 0

# Optional позволяет не кидать ошибок если что-то из аргументов не передали - 
# - просто заполнить дефолтным значением

#Тг логин здесь нахуй не нужен, а вот максимально допустимое количество клиентов - вполне

#
# app = FastAPI(docs_url=None, redoc_url=None)
app = FastAPI(docs_url='/xxx/fuckingdogs', redoc_url='/yyy/redocsggg1')

@app.exception_handler(404)
async def handle_404(_, __):
        return RedirectResponse('https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygUIcmlja3JvbGw%3D')  

@app.get("/ping")
def ping_processor():
    """Люблю собраться за уютной игрой в настольный пенис"""
    return "pong"

@app.get("/protos")
def read_available_protos():
    """Возвращает список активных протоколов"""
    return list(Available_Protos)

@app.get("/{proto}/active_confs")
def read_active_users(proto: PROTO_LIT):
    """Возвращает список активных пользователей"""
    if not proto in Available_protos_set:
        return {"error" : "This protocol is not imlemented on this server"}
    return Protos[proto].get_confs()

@app.post("/{proto}/renew_conf")
def renew_config(proto: PROTO_LIT, data: data_for_renewal):
    if not proto in Available_protos_set:
        return {"error" : "This protocol is not imlemented on this server"}
    
    return Protos[proto].renew_conf(data.key_id, data.renewal_time, data.max_clients)



@app.post("/{proto}/generate_conf")
def add_new_user(proto: PROTO_LIT, new_user_info: new_user):
    """Добавляет нового пользователя по пост запросу"""

    protocol = str(proto)
    if not protocol in Available_protos_set:
        return {"error" : "This protocol is not imlemented on this server"}
    return Protos[protocol].generate_conf(expire_date = new_user_info.expire_date,
                                       max_clients = new_user_info.max_clients)

@app.post("/{proto}/revoke_key")
def revoke_link(proto: PROTO_LIT, removal_info: key_for_removal):
    """Удаляет Аутлайн ключ по его айди"""
    protocol = str(proto)
    if not protocol in Available_protos_set:
        return {"error" : "This protocol is not imlemented on this server"}
    key_id = removal_info.key_id
    return Protos[protocol].remove_key(key_id)

USERNAME = API_USERNAME
PASSWORD = API_PASSWORD
REALM = 'VPN'


def generate_nonce():
    return os.urandom(16).hex()

def generate_opaque():
    return os.urandom(16).hex()

OPAQUE = generate_opaque()

def parse_digest_auth(auth_header):
    pattern = re.compile(r'(\w+)=("([^"]+)"|([^,]+))')
    auth_dict = {}
    for match in pattern.finditer(auth_header):
        key = match.group(1)
        value = match.group(3) or match.group(4)
        auth_dict[key] = value
    return auth_dict

async def digest_authentication(request: Request, call_next):
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Digest '):
        auth_info = auth_header[7:]
        credentials = parse_digest_auth(auth_info)
        if credentials.get('username') == USERNAME:
            HA1_str = f"{USERNAME}:{REALM}:{PASSWORD}"
            HA1 = hashlib.md5(HA1_str.encode()).hexdigest()

            HA2_str = f"{request.method}:{credentials.get('uri')}"
            HA2 = hashlib.md5(HA2_str.encode()).hexdigest()

            response_str = f"{HA1}:{credentials.get('nonce')}:{credentials.get('nc')}:{credentials.get('cnonce')}:{credentials.get('qop')}:{HA2}"
            valid_response = hashlib.md5(response_str.encode()).hexdigest()

            if credentials.get('response') == valid_response:
                response = await call_next(request)
                return response
    # Генерируем новый NONCE для каждого запроса аутентификации
    NONCE = generate_nonce()
    response = Response(
        status_code=status.HTTP_401_UNAUTHORIZED,
        headers={
            'WWW-Authenticate': f'Digest realm="{REALM}",'
                                f'nonce="{NONCE}",'
                                f'opaque="{OPAQUE}",'
                                f'qop="auth",'
                                f'algorithm="MD5"'
        }
    )
    return response

app.middleware('http')(digest_authentication)


if __name__ == '__main__':
    
    uvicorn.run(app, host="0.0.0.0", port=1488, loop='none',
                ssl_keyfile="./server.key",
                ssl_certfile="./server.crt")
    # print(Outline_VPN.generate_conf(expire_date=100, max_clients=1))