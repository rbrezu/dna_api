import datetime
import json

from bson import ObjectId


class Encoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        if isinstance(o, datetime.datetime):
            return str(o)

        obj = json.JSONEncoder.default(self, o)
        return obj
