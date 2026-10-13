# Atas 5.0.6 — Asistente de configuración por páginas

## Cambios
- Ocho páginas del asistente, identificadas por `/setup?step=N`, con navegación Anterior/Siguiente y progreso.
- Cada paso se valida en servidor antes de avanzar mediante `POST /setup/validate-step`.
- La página de bancos comprueba conectores reales antes de avanzar; una fuente válida es suficiente.
- Corrección del banco secundario cuando sólo se configura un banco.
- Errores visibles sin borrar los campos ya ingresados y recuperación temporal de datos no sensibles.

## Limitaciones
- La navegación cambia la URL sin recargar el DOM; los borradores no sensibles se guardan en la sesión del navegador y las contraseñas no se almacenan allí.
- La validación de URL Service Layer comprueba el formato, pero no garantiza conectividad SAP; la validación final y la política de escritura permanecen.
- El guardado permanente de cada etapa en el servidor sigue pendiente; se efectúa al finalizar correctamente el asistente.
- La prueba con el XLSX BCH publicado actualmente aún requiere verificación en un entorno con acceso al archivo oficial.

## Evidencias
- PR #3; CI Python Windows/Ubuntu y escaneo de seguridad satisfactorios antes de merge.
