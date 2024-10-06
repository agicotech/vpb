import json, logging, re, os
from decouple import config
from collections import Counter
from database import JsonDataBase

if os.path.exists('/opt/outline/access.txt'):
    data = {}
    with open('/opt/outline/access.txt', 'r') as f:
        for line in f.readlines():
            line = line.strip()
            ptr = line.index(':')
            key, val = line[:ptr], line[ptr+1:]
            data[key] = val
    OUTLINE_API = data.get('apiUrl')
    OUTLINE_SHA = data.get('certSha256')
else:
    OUTLINE_API = config('OUTLINE_API', default = '')
    OUTLINE_SHA = config('OUTLINE_SHA', default = '')

VLESS_LINK = config('VLESS_LINK', default = '')
VLESS_USERNAME = config('VLESS_USERNAME', default = '', cast = str)
VLESS_PASSWORD = config('VLESS_PASSWORD', default = '', cast = str).replace('__', '%') # без ебатории с реплейсом ошибка, не хотел себе ебать мозги как и почему, скорее всего выебоны питона