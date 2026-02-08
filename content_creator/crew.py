"""
Crew Content-Creator: PoC migrada desde n8n.

Flujo: Analista → Redactor → Editor (secuencial).
Equivalente al agente_supervisor + agente_analista, agente_redactor, agente_editor.
"""

from crewai import Agent, Crew, Process, Task


# --- Agentes (roles y backstories alineados al flujo n8n) ---

ANALISTA_BACKSTORY = """Eres un experto en curación de contenidos y pensamiento lógico.
Tu función es recibir un texto bruto y extraer exclusivamente los puntos más impactantes,
datos estadísticos o lecciones clave.
Tu salida debe ser: Una lista numerada de conceptos clave, sin introducciones ni despedidas.
Identifica claramente cuál es el mensaje central que debería ser el 'gancho' inicial."""

REDACTOR_BACKSTORY = """Eres un redactor creativo especializado en redes sociales con un tono
'edutainment' (educativo pero entretenido). Tu misión es convertir una lista de puntos clave
en un hilo narrativo.
Reglas de estilo:
- Usa oraciones cortas y directas.
- Implementa 'espacio en blanco' entre párrafos para facilitar la lectura.
- Incluye máximo 1 emoji por punto.
- Escribe en una voz activa y cercana al lector."""

EDITOR_BACKSTORY = """Eres un editor jefe obsesionado con la perfección y la brevedad.
Tu tarea es recibir el borrador del redactor y realizar los siguientes ajustes:
- Corrige cualquier error ortográfico o gramatical.
- Asegúrate de que ningún bloque de texto supere los 280 caracteres (formato X/Twitter).
- Elimina palabras de relleno o frases repetitivas.
IMPORTANTE: Solo devuelve el texto final corregido, no añadas comentarios adicionales
ni explicaciones de lo que cambiaste."""


def create_analyst_agent() -> Agent:
    return Agent(
        role="Analista de contenido",
        goal="Desglosar textos largos en puntos clave y proponer el orden lógico del hilo; no redactar el contenido final.",
        backstory=ANALISTA_BACKSTORY,
        allow_delegation=False,
        verbose=True,
    )


def create_writer_agent() -> Agent:
    return Agent(
        role="Redactor creativo",
        goal="Convertir listas de puntos clave en hilos narrativos con tono persuasivo, informal y atractivo; usar emojis con mesura para engagement.",
        backstory=REDACTOR_BACKSTORY,
        allow_delegation=False,
        verbose=True,
    )


def create_editor_agent() -> Agent:
    return Agent(
        role="Editor",
        goal="Revisar ortografía y gramática, verificar que ningún bloque supere 280 caracteres (X) y pulir el texto final.",
        backstory=EDITOR_BACKSTORY,
        allow_delegation=False,
        verbose=True,
    )


def create_tasks(user_input: str, analyst: Agent, writer: Agent, editor: Agent):
    """Crea las tres tareas encadenadas por contexto."""
    task_analista = Task(
        description=f"""A partir del siguiente texto del usuario, extrae los puntos más impactantes,
datos estadísticos o lecciones clave. Entrega una lista numerada de conceptos clave, sin introducciones
ni despedidas. Indica cuál es el mensaje central que debería ser el 'gancho' inicial.

TEXTO DEL USUARIO:
{user_input}""",
        expected_output="Lista numerada de conceptos clave y mensaje central/gancho identificado.",
        agent=analyst,
    )

    task_redactor = Task(
        description="""Usa la lista de conceptos clave que te proporciona el contexto (salida del analista)
y conviértela en un borrador de hilo para redes sociales. Tono edutainment: oraciones cortas,
espacio entre párrafos, máximo 1 emoji por punto, voz activa y cercana.""",
        expected_output="Borrador del hilo listo para edición final.",
        agent=writer,
        context=[task_analista],
    )

    task_editor = Task(
        description="""Recibe el borrador del redactor (contexto), corrige ortografía y gramática,
asegura que ningún bloque supere 280 caracteres (X/Twitter), elimina relleno y repeticiones.
Devuelve solo el texto final, sin comentarios ni explicaciones.""",
        expected_output="Texto final del hilo, listo para publicar, cada bloque ≤280 caracteres.",
        agent=editor,
        context=[task_redactor],
    )

    return task_analista, task_redactor, task_editor


def create_content_creator_crew(user_input: str) -> Crew:
    """Construye el crew con tres agentes y tareas secuenciales."""
    analyst = create_analyst_agent()
    writer = create_writer_agent()
    editor = create_editor_agent()

    task_analista, task_redactor, task_editor = create_tasks(
        user_input, analyst, writer, editor
    )

    return Crew(
        agents=[analyst, writer, editor],
        tasks=[task_analista, task_redactor, task_editor],
        process=Process.sequential,
        verbose=True,
        # Trazabilidad: descomenta si usas CrewAI AMP (crewai login)
        # tracing=True,
    )


def run_crew(user_input: str):
    """Ejecuta el crew y devuelve el resultado y los outputs por tarea (para Chainlit/Steps)."""
    crew = create_content_creator_crew(user_input)
    result = crew.kickoff()
    # CrewOutput: .output (texto final), .tasks_output (lista de TaskOutput)
    tasks_output = []
    if hasattr(result, "tasks_output") and result.tasks_output:
        for t in result.tasks_output:
            tasks_output.append(getattr(t, "raw", str(t)))
    final_output = getattr(result, "output", None) or (
        tasks_output[-1] if tasks_output else str(result)
    )
    return {"output": final_output, "tasks_output": tasks_output, "crew_result": result}
