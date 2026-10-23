# Backlog y plan de Sprints (para cargar en Jira)

Proyecto Jira sugerido: clave `PAQ`. Épicas = un servicio. Estimación en story points (SP).
Las fechas y el reparto real los define el equipo en Jira; aquí está el contenido de partida.

## Épicas
| Clave | Épica |
|---|---|
| PAQ-1 | Infraestructura y calidad (scaffolding, Docker, CI) |
| PAQ-2 | Servicio Pedidos (PostgreSQL) |
| PAQ-3 | Servicio Auth y Usuarios (PostgreSQL, JWT) |
| PAQ-4 | Servicio Tracking (MongoDB) |
| PAQ-5 | Servicio Chatbot IA (Gemini) |
| PAQ-6 | Documentación y pruebas de API |

## Sprint 1 — Fundamentos y servicio de negocio (objetivo: Pedidos y Auth funcionando en Docker)
| Historia | Épica | SP | Criterio de aceptación |
|---|---|---|---|
| Scaffolding independiente de los 4 servicios (settings, requirements, Dockerfile) | PAQ-1 | 5 | Cada servicio arranca solo y responde `/health/` |
| Calidad de código: ruff, black, isort, pytest | PAQ-1 | 2 | Los 4 pasan lint y tests |
| Modelo relacional de Pedidos (Cliente, Dirección, Pedido, Historial) | PAQ-2 | 5 | Migraciones aplican en PostgreSQL |
| CRUD de Pedidos con DRF, validaciones y transiciones de estado | PAQ-2 | 8 | Estados siguen el ciclo del README |
| Paginación, filtros y ordenamiento de pedidos | PAQ-2 | 3 | Filtra por estado, prioridad, fecha, peso |
| Auth: usuario con roles, registro y login JWT | PAQ-3 | 8 | Token incluye `role`; contraseñas validadas |
| Auth: refresh, logout (lista negra), cambio de contraseña, /me | PAQ-3 | 5 | Refresh rotado queda invalidado |
| Validación local de JWT en los demás servicios y permisos por rol | PAQ-3 | 3 | Rol cliente solo ve sus pedidos |

## Sprint 2 — Datos no estructurados, IA, integración y evidencia
| Historia | Épica | SP | Criterio de aceptación |
|---|---|---|---|
| Tracking: ubicaciones GPS en MongoDB (CRUD, filtros, última ubicación) | PAQ-4 | 8 | Un repartidor solo escribe con su id |
| Tracking: eventos de reparto con esquema flexible | PAQ-4 | 5 | `datos` acepta estructura libre; incidencia exige motivo |
| Chatbot: contrato `/api/chat/` y conversaciones en MongoDB | PAQ-5 | 5 | Contrato documentado en OpenAPI |
| Chatbot: Gemini con function calling hacia Pedidos y Tracking | PAQ-5 | 8 | Los datos vienen del servicio, no del modelo |
| Chatbot: escalamiento a humano y cola para el operador | PAQ-5 | 3 | Conversación escalada deja de usar el LLM |
| docker compose con los 4 servicios + 2 PostgreSQL + MongoDB | PAQ-1 | 5 | `docker compose up --build` → todo healthy |
| OpenAPI/Swagger por servicio | PAQ-6 | 3 | `/api/docs/` en cada servicio; YAML en `docs/api/` |
| Colección Postman/newman extremo a extremo | PAQ-6 | 3 | Corre completa sin fallos |
| Pipeline CI (matriz por servicio + e2e) | PAQ-1 | 3 | Verde en PR |
| Evidencia Scrum: review y retrospectivas en Jira | PAQ-6 | 2 | Capturas del tablero y retros |

## Backlog repriorizado (candidatos tras el Sprint 2)
1. API Gateway con rate limit (semanas 8–9 del plan).
2. Redis pub/sub: eventos `pedido_creado`, `entrega_confirmada`, etc.
3. Servicio de Ruteo (OR-Tools) y de Reparto con evidencia.
4. Notificaciones por WhatsApp/SMS.
5. Panel administrativo y reportes.
