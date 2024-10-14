from requests import get
import logging
import countryflag
import random, string

def my_ip():
    return get('https://api.ipify.org').content.decode('utf8')


def get_flag_and_city():
    res = get('https://ipinfo.io')
    flags, city = '', ''
    try:
        res = res.json()
        city = res.get('city', "Default")
        flags = countryflag.getflag([res.get('country', "")]).strip()
    except Exception as e:
        logging.warning('Today without a flag :(')
    return flags, city

def randomstr(length, with_special = True):
   letters = string.ascii_letters + string.digits + ('_!.@' if with_special else '')
   return ''.join(random.choice(letters) for _ in range(length))

if __name__ == '__main__':
    print(my_ip())
    print(get_flag_and_city())