# Plantillas de ceremonias Scrum (copiar a Jira/Confluence)

Estas plantillas **no son evidencia**: la evidencia es lo que el equipo registra en Jira
(tablero, daily, review y retrospectiva reales). Complétalas con datos reales.

## Sprint Planning
- **Sprint:** N — fechas: __ a __ — duración: 2 semanas
- **Objetivo del Sprint:** …
- **Capacidad del equipo:** __ SP (velocidad previa: __)
- **Historias comprometidas:** (claves PAQ-n, SP)
- **Riesgos / dependencias:** …
- **Definición de Hecho:** código revisado, tests pasan en CI, OpenAPI actualizado, tablero al día.

## Daily (bitácora)
Registrar en un comentario del Sprint o en Confluence, una entrada por día:
| Fecha | Persona | Ayer | Hoy | Impedimentos |
|---|---|---|---|---|

## Sprint Review
- **Demo:** historias terminadas y cómo se mostraron (Swagger, Postman/newman, docker compose).
- **Historias no terminadas y motivo:** …
- **Retroalimentación del Product Owner / docente:** …
- **Cambios al backlog resultantes:** (reordenamientos, nuevas historias)

## Retrospectiva
| ¿Qué salió bien? | ¿Qué mejorar? | Acciones (responsable, fecha) |
|---|---|---|
| | | |

- **Velocidad lograda:** __ SP de __ comprometidos
- **Acuerdo de mejora para el siguiente Sprint:** …

## Trazabilidad commit ↔ historia
Incluye la clave de Jira en el mensaje del commit (Conventional Commits), p. ej.
`feat(pedidos): filtros y ordenamiento PAQ-14`. Jira lo vincula automáticamente si se conecta GitHub.
