from pydantic import BaseModel

import os

class BaseStorage(BaseModel):
    class Config:
        arbitrary_types_allowed = True

    def __init__(self, filepath: str = None, **kwargs):
        super().__init__(**kwargs)
        if filepath == None:
            filepath = f'./{self.__class__.__name__}.json'
        self.__filepath = filepath

    def __iter__(self):
        yield from (val for val in self.__dict__.items() if not val[0][0] == '_')

    def save(self):
        with open(self.__filepath, 'wb') as f:
            f.write(self.model_dump_json(
                indent = 4, exclude='filepath').encode())

    def load(self, newpath = None):
        if newpath is not None:
            self.__filepath = newpath
        if not os.path.exists(self.__filepath):
            self.save()
            return False
        else:
            with open(self.__filepath, 'rb') as f:
                loaded_model = self.model_validate_json(f.read())
                loaded_model.__filepath = self.__filepath
                self.__dict__.update(loaded_model.__dict__)
            return True
        
if __name__ == '__main__':
    print('\n')
    class test(BaseStorage):
        testfield: int = 10

    testobj = test()

    for p in testobj:
        print(p)

    testobj.save()

    for p in testobj:
        print(p)

    testobj.load()

    for p in testobj:
        print(p)