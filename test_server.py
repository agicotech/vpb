import random
from fastapi import FastAPI
import uvicorn
from pydantic import BaseModel
from typing import Dict, Optional, Literal
import random, string
from outline_vpn.outline_vpn import OutlineVPN
from consts import OUTLINE_API, OUTLINE_SHA
from database import JsonDataBase
import time
import os, subprocess

BOT_NAME = '@agicovpnbot'

def randomstr(length, with_special = True):
   letters = string.ascii_letters + string.digits + ('_!.@' if with_special else '')
   return ''.join(random.choice(letters) for _ in range(length))

Available_Protos = {"IKEv2", 'Outline', 'WireGuard', 'OpenVPN'} #TODO: Сделать автоматический поиск установленных протоколов
# здесь допишем автоматическое определение установленных на сервере протоколов как-нибудь потом

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
    



#TODO: Логин и пароль должны генерироваться в виде !!!случайной строки из символов
# Принимать надо не промежуток в днях, а непосредственную отметку времени, на которой пользователь умирает
# Возвращать этот промежуток не надо
# Функция должна быть привязана к алгоритму, так как у разных алгоритмов разные поля 
# (далеко не всегда только логин и пароль)

'''client = clients.touch(user.id, 
                  full_name = user.full_name,
                  username = user.username,
                  balance = balance - price)     референс поступающих данных (дикт)'''




class Outline(VPN_Proto):
    outline = OutlineVPN(api_url=OUTLINE_API, cert_sha256=OUTLINE_SHA)
    clients = JsonDataBase('db_clients_Outline')
    clients.load()

    @classmethod
    def save_user(cls, user: dict):
        cls.clients[user['_key_id']] = user
        cls.clients.save()


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
    def save_user(cls, user: dict):
        cls.clients[user['_key_id']] = user
        cls.clients.save()


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


Protos: Dict[str, VPN_Proto] = {"IKEv2" : IKEv2, "Outline": Outline, 'WireGuard': WireGuard, 'OpenVPN': OpenVPN}
proto_literal = Literal["IKEv2", "Outline", 'WireGuard', 'OpenVPN']

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

app = FastAPI(docs_url=None, redoc_url=None)


@app.get("/{proto}/active_confs")
def read_active_users(proto: proto_literal):
    """Возвращает список активных пользователей"""
    if not proto in Available_Protos:
        return {"error" : "This protocol is not imlemented on this server"}
    return Protos[proto].get_confs()

@app.post("/{proto}/renew_conf")
def renew_config(proto: proto_literal, data: data_for_renewal):
    if not proto in Available_Protos:
        return {"error" : "This protocol is not imlemented on this server"}
    
    return Protos[proto].renew_conf(data.key_id, data.renewal_time, data.max_clients)



@app.post("/{proto}/generate_conf")
def add_new_user(proto: proto_literal, new_user_info: new_user):
    """Добавляет нового пользователя по пост запросу"""

    protocol = str(proto)
    if not protocol in Available_Protos:
        return {"error" : "This protocol is not imlemented on this server"}
    return Protos[protocol].generate_conf(expire_date = new_user_info.expire_date,
                                       max_clients = new_user_info.max_clients)

@app.post("/{proto}/revoke_key")
def revoke_link(proto: proto_literal, removal_info: key_for_removal):
    """Удаляет Аутлайн ключ по его айди"""
    protocol = str(proto)
    if not protocol in Available_Protos:
        return {"error" : "This protocol is not imlemented on this server"}
    key_id = removal_info.key_id
    return Protos[protocol].remove_key(key_id)

if __name__ == '__main__':
    uvicorn.run(app, host="0.0.0.0", port=1488, loop='none')
    # print(Outline_VPN.generate_conf(expire_date=100, max_clients=1))