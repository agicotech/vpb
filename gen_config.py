import json

from utils import my_ip, get_flag
from proto_detector import Proto_detector
from consts import API_USERNAME, API_PASSWORD
def generate_server_config(name: str):
    """Генерирует json файл с конфигом сервера"""
    ip = my_ip()
    json_file = {ip: {
            "name": name,
            "location": name + ' '+ get_flag(ip),
            "ip": ip,
            "active_clients": 0,
            "protos": Proto_detector()(),
            "auth": {
                "login": API_USERNAME,
                "password": API_PASSWORD
            },
            "price": {
                "180": 500,
                "90": 250,
                "30": 100,
                "10": 50,
                "3": 30
            }
        }}
    with open("server_config.json", "w", encoding='utf-8') as f:
        json.dump(json_file, f, indent = 4)
        f.close()

if __name__ == '__main__':
    generate_server_config('test_server')