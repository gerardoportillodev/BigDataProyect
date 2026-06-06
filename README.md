# Proyecto Big Data — Riesgo Crediticio

## Cómo iniciar con Codex
1. Descomprime este paquete.
2. Copia el archivo a `data/raw/ConvertidorEstructura - DATA.xlsm`.
3. Copia los PDFs del curso a `docs/reference/`.
4. Abre Terminal en la raíz del proyecto.
5. Ejecuta:

```bash
git init
codex
```

Codex leerá `AGENTS.md` automáticamente al iniciar desde esta carpeta.

## Verificar contexto
```bash
codex --ask-for-approval never "Resume las instrucciones activas y enumera los archivos de contexto que leíste."
```

## Primera tarea
Pega el contenido de `prompts/FIRST_CODEX_PROMPT.txt`.

## Seguridad
`data/` está excluido de Git. No subas el Excel ni información personal a GitHub.
