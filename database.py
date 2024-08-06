from baseclass import BaseStorage
class JsonDataBase(BaseStorage):
    data: dict = {}
    def __setitem__(self, key, val):
        self.data[key] = val

    def get(self, key, default = None):
        return self.data.get(key, default)

    def update(self, *args, **kwargs):
        self.data.update(*args, **kwargs)

    def pop(self, key, default = None):
        return self.data.pop(key, default)
    
    def keys(self):
        return self.data.keys()
    def items(self):
        return self.data.items()

    def put(self, key, val):
        self[key] = val

    def  __iter__(self):
        return self.data.__iter__()

    def __getitem__(self, key):
        return self.get(key)
    
    def values(self):
        return self.data.values()

