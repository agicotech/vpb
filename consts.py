import json, logging, re, os
from dotenv import load_dotenv
from collections import Counter
from database import JsonDataBase

load_dotenv()

config = lambda key, default=None : os.getenv(key, default)

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

XUI_USERNAME = config('XUI_USERNAME', default = 'admin')
XUI_PASSWORD = config('XUI_PASSWORD', default = 'admin')
XUI_HOST = config('XUI_HOST', 'http://localhost:2053')