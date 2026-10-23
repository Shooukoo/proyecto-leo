"""Conversaciones del chatbot en MongoDB (pymongo directo)."""

from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from django.conf import settings
from pymongo import DESCENDING, MongoClient

_client = None


def get_db():
    global _client
    if _client is None:
        _client = MongoClient(settings.MONGO_URI, tz_aware=True)
    return _client[settings.MONGO_DB_NAME]


def _out(doc):
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    return doc


def _oid(value):
    try:
        return ObjectId(value)
    except (InvalidId, TypeError):
        return None


def ahora():
    return datetime.now(timezone.utc)


class Conversaciones:
    name = "conversaciones"

    @property
    def col(self):
        return get_db()[self.name]

    def crear(self, usuario_id):
        doc = {
            "usuario_id": usuario_id,
            "estado": "abierta",
            "mensajes": [],
            "creado": ahora(),
            "actualizado": ahora(),
        }
        doc["_id"] = self.col.insert_one(dict(doc)).inserted_id
        return _out(doc)

    def obtener(self, conversation_id):
        oid = _oid(conversation_id)
        return _out(self.col.find_one({"_id": oid})) if oid else None

    def agregar_mensajes(self, conversation_id, mensajes, estado=None):
        cambios = {"$push": {"mensajes": {"$each": mensajes}}, "$set": {"actualizado": ahora()}}
        if estado:
            cambios["$set"]["estado"] = estado
        self.col.update_one({"_id": _oid(conversation_id)}, cambios)
        return self.obtener(conversation_id)

    def listar(self, filtro, skip=0, limit=20):
        total = self.col.count_documents(filtro)
        cursor = self.col.find(filtro).sort("actualizado", DESCENDING).skip(skip).limit(limit)
        return total, [_out(d) for d in cursor]


conversaciones = Conversaciones()
