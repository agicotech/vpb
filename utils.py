from requests import get
import logging
import countryflag
import random, string

def my_ip():
    return get('https://api.ipify.org').content.decode('utf8')

def get_flag(ip):
    res = get(f'https://geolocation-db.com/json/{ip}&position=true')
    country_code = res.json()['country_code'].lower()
    flags = ''
    try:
        flags = countryflag.getflag([country_code])
    except Exception as e:
        logging.warning('Today without a flag :(')
    return flags

def randomstr(length, with_special = True):
   letters = string.ascii_letters + string.digits + ('_!.@' if with_special else '')
   return ''.join(random.choice(letters) for _ in range(length))
