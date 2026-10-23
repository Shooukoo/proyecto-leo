"""Acceso a MongoDB con pymongo directo y un repositorio genérico por colección."""

from bson import ObjectId
from bson.errors import InvalidId
from django.conf import settings
from pymongo import ASCENDING, DESCENDING, MongoClient

_client = None


def get_db():
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGO_URI, tz_aware=True)
    return _client[settings.MONGO_DB_NAME]


def to_object_id(value):
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def _out(doc):
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


class Repository:
    """CRUD mínimo sobre una colección; los documentos salen con `id` en texto."""

    def __init__(self, collection_name, indexes=()):
        self.collection_name = collection_name
        self.indexes = indexes
        self._indexed = False

    @property
    def col(self):
        col = get_db()[self.collection_name]
        if not self._indexed:
            for keys in self.indexes:
                col.create_index(keys)
            self._indexed = True
        return col

    def create(self, data):
        result = self.col.insert_one(dict(data))
        return self.get(result.inserted_id)

    def get(self, doc_id):
        oid = doc_id if isinstance(doc_id, ObjectId) else to_object_id(doc_id)
        return _out(self.col.find_one({"_id": oid})) if oid else None

    def list(self, filtro=None, orden=None, skip=0, limit=20):
        cursor = self.col.find(filtro or {})
        if orden:
            campo, descendente = orden
            cursor = cursor.sort(campo, DESCENDING if descendente else ASCENDING)
        total = self.col.count_documents(filtro or {})
        return total, [_out(d) for d in cursor.skip(skip).limit(limit)]

    def replace(self, doc_id, data):
        oid = to_object_id(doc_id)
        if not oid or not self.col.find_one_and_replace({"_id": oid}, dict(data)):
            return None
        return self.get(oid)

    def update(self, doc_id, data):
        oid = to_object_id(doc_id)
        if not oid or not data:
            return self.get(doc_id)
        if not self.col.update_one({"_id": oid}, {"$set": dict(data)}).matched_count:
            return None
        return self.get(oid)

    def delete(self, doc_id):
        oid = to_object_id(doc_id)
        return bool(oid) and self.col.delete_one({"_id": oid}).deleted_count == 1


ubicaciones = Repository(
    "ubicaciones", indexes=[[("repartidor_id", 1), ("timestamp", -1)], [("pedido_id", 1)]]
)
eventos = Repository(
    "eventos_reparto", indexes=[[("pedido_id", 1), ("timestamp", -1)], [("tipo", 1)]]
)
