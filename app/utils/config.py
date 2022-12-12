import json


class Config:
    """
    Represents a config dictionary that can be also saved.
    """

    def __init__(self, dic):
        self._dic = dic

    def __getitem__(self, key):
        return self._dic.get(key)

    def __repr__(self) -> str:
        return self._dic.__repr__()

    def save(self):
        """
        Persists any changes.
        """
        pass


class FileConfig(Config):
    """
    Config file that can be read from and written to a file.
    """

    def __init__(self, filename):
        self.filename = filename
        with open(filename, "r", encoding="UTF-8") as f:
            super().__init__(json.load(f))

    def save(self):
        with open(self.filename, "w") as f:
            json.dump(self._dic, f, ensure_ascii=False, indent=2)
