"""Proveedores de IA detrás de una interfaz única: Gemini (producción) y mock (local/tests)."""

import re
from dataclasses import dataclass, field

from django.conf import settings

from .services import DECLARACIONES

SYSTEM_PROMPT = (
    "Eres el asistente de atención al cliente de una paquetería en México. Responde en español, "
    "breve y amable. NUNCA inventes estados, ubicaciones ni montos: obtén siempre los datos con "
    "las herramientas. Si no puedes resolver la consulta o el usuario pide hablar con una persona, "
    "usa escalar_a_humano."
)


@dataclass
class Resultado:
    texto: str
    herramientas: list = field(default_factory=list)
    escalado: bool = False


class Ejecutor:
    """Ejecuta herramientas, registra cuáles se usaron y captura el escalamiento."""

    def __init__(self, funciones):
        self.funciones = funciones
        self.usadas = []
        self.escalado = False

    def __call__(self, nombre, args):
        self.usadas.append(nombre)
        if nombre == "escalar_a_humano":
            self.escalado = True
            return {"ok": True, "motivo": args.get("motivo", "")}
        if nombre not in self.funciones:
            return {"error": f"Herramienta desconocida: {nombre}"}
        try:
            return self.funciones[nombre](**args)
        except Exception as exc:  # el error se devuelve al LLM, no rompe el chat
            return {"error": str(exc)}


class MockProvider:
    """Reglas simples en español; permite probar el flujo completo sin clave ni red."""

    ID = re.compile(
        r"#?\b(\d+|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\b", re.I
    )

    def responder(self, historial, mensaje, ejecutar):
        texto = mensaje.lower()
        pedido = self.ID.search(mensaje)
        if re.search(r"humano|agente|persona|asesor", texto):
            ejecutar("escalar_a_humano", {"motivo": "El usuario pidió atención humana"})
            return "Te paso con un agente humano; en breve te atenderá."
        if pedido and re.search(r"d[oó]nde|ubicaci[oó]n|rastre|localiz", texto):
            datos = ejecutar("ubicacion_pedido", {"pedido": pedido.group(1)})
            if "error" in datos:
                return datos["error"]
            if not datos["ubicacion"]:
                return datos["nota"]
            u = datos["ubicacion"]
            return f"Tu pedido va en camino. Última ubicación: {u['latitud']}, {u['longitud']}."
        if pedido:
            datos = ejecutar("consultar_pedido", {"pedido": pedido.group(1)})
            if "error" in datos:
                return datos["error"]
            return f"Tu pedido #{datos['id']} está en estado «{datos['estado']}»."
        if re.search(r"mis pedidos|mis env[ií]os|mis paquetes", texto):
            datos = ejecutar("listar_mis_pedidos", {})
            if "error" in datos:
                return datos["error"]
            return f"Tienes {datos['total']} pedido(s)."
        return "Puedo consultar el estado y la ubicación de tu pedido. Dame tu número o folio."


class GeminiProvider:
    def __init__(self):
        from google import genai
        from google.genai import types

        if not settings.GEMINI_API_KEY:
            raise RuntimeError("Falta GEMINI_API_KEY para usar el proveedor gemini.")
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(timeout=settings.LLM_TIMEOUT_SECONDS * 1000),
        )

    def responder(self, historial, mensaje, ejecutar):
        from google.genai import types

        contenidos = [
            types.Content(
                role="user" if m["rol"] == "usuario" else "model",
                parts=[types.Part(text=m["texto"])],
            )
            for m in historial
        ]
        contenidos.append(types.Content(role="user", parts=[types.Part(text=mensaje)]))
        config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[types.Tool(function_declarations=DECLARACIONES)],
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )
        for _ in range(settings.LLM_MAX_TOOL_ROUNDS):
            resp = self.client.models.generate_content(
                model=settings.GEMINI_MODEL, contents=contenidos, config=config
            )
            llamadas = resp.function_calls or []
            if not llamadas:
                return resp.text or ""
            contenidos.append(resp.candidates[0].content)
            partes = [
                types.Part.from_function_response(
                    name=c.name, response={"resultado": ejecutar(c.name, dict(c.args or {}))}
                )
                for c in llamadas
            ]
            contenidos.append(types.Content(role="user", parts=partes))
        return "No pude completar la consulta; te paso con un agente."


def get_provider():
    if settings.LLM_PROVIDER == "gemini":
        return GeminiProvider()
    return MockProvider()
