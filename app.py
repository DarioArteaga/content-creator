"""
App Chainlit para el crew Content-Creator.

- Chat: el usuario pega un texto y recibe un hilo viral (Analista → Redactor → Editor).
- Trazabilidad: cada fase se muestra como Step en la UI.
- OpenLIT: opcional vía variable de entorno OTEL_EXPORTER_OTLP_ENDPOINT.
"""

import asyncio
import os

import chainlit as cl
from dotenv import load_dotenv

load_dotenv()

# OpenLIT (trazabilidad open-source): solo si está configurado el endpoint
_otel_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
if _otel_endpoint:
    try:
        import openlit
        openlit.init(otlp_endpoint=_otel_endpoint)
    except ImportError:
        pass

from content_creator.crew import run_crew

STEP_NAMES = ("Analista (puntos clave)", "Redactor (borrador)", "Editor (texto final)")


@cl.on_chat_start
async def start():
    await cl.Message(
        content="**Agencia de contenido** — Pega un texto largo o un tema y lo convertiré en un hilo para redes (X/Twitter). "
                "Flujo: Analista → Redactor → Editor."
    ).send()


@cl.on_message
async def on_message(message: cl.Message):
    if not message.content or not message.content.strip():
        await cl.Message(content="Escribe o pega el texto que quieres convertir en hilo.").send()
        return

    msg = cl.Message(content="")
    await msg.send()

    # Ejecutar el crew en un hilo para no bloquear el event loop (run_crew es síncrono)
    try:
        result = await asyncio.to_thread(run_crew, message.content.strip())
    except Exception as e:
        await cl.Message(content=f"Error al ejecutar el crew: {e}").send()
        return

    tasks_output = result.get("tasks_output") or []
    final_output = result.get("output") or ""

    # Mostrar cada fase como Step (trazabilidad en UI)
    for i, step_name in enumerate(STEP_NAMES):
        text = tasks_output[i] if i < len(tasks_output) else "(sin salida)"
        async with cl.Step(name=step_name, type="tool") as step:
            step.input = message.content[:200] + ("..." if len(message.content) > 200 else "") if i == 0 else ""
            step.output = text

    msg.content = final_output
    await msg.update()


if __name__ == "__main__":
    # Para ejecutar: chainlit run app.py -w
    pass
