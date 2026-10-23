from types import SimpleNamespace

import pytest
from google.genai import types

from chatbot_api import llm


def test_proveedor_por_defecto_es_mock(settings):
    settings.LLM_PROVIDER = "mock"
    assert isinstance(llm.get_provider(), llm.MockProvider)


def test_gemini_requiere_clave(settings):
    settings.LLM_PROVIDER, settings.GEMINI_API_KEY = "gemini", ""
    with pytest.raises(RuntimeError):
        llm.get_provider()


def test_ejecutor_registra_herramientas_y_captura_errores():
    def falla(**_):
        raise ValueError("sin permiso")

    ejecutor = llm.Ejecutor({"consultar_pedido": falla})
    assert ejecutor("consultar_pedido", {"pedido": "1"}) == {"error": "sin permiso"}
    assert ejecutor("inexistente", {})["error"].startswith("Herramienta desconocida")
    ejecutor("escalar_a_humano", {"motivo": "x"})
    assert ejecutor.escalado and ejecutor.usadas[0] == "consultar_pedido"


def test_gemini_ejecuta_function_calling_y_devuelve_texto_final():
    """Bucle de function calling con un cliente falso: sin red ni clave."""
    llamada = SimpleNamespace(name="consultar_pedido", args={"pedido": "5"})
    respuestas = iter(
        [
            SimpleNamespace(
                function_calls=[llamada],
                text=None,
                candidates=[
                    SimpleNamespace(
                        content=types.Content(role="model", parts=[types.Part(text="…")])
                    )
                ],
            ),
            SimpleNamespace(function_calls=None, text="Tu pedido está en ruta.", candidates=[]),
        ]
    )
    provider = llm.GeminiProvider.__new__(llm.GeminiProvider)
    provider.client = SimpleNamespace(
        models=SimpleNamespace(generate_content=lambda **kw: next(respuestas))
    )
    ejecutor = llm.Ejecutor({"consultar_pedido": lambda pedido: {"estado": "en_ruta"}})
    texto = provider.responder([], "¿pedido 5?", ejecutor)
    assert texto == "Tu pedido está en ruta." and ejecutor.usadas == ["consultar_pedido"]
