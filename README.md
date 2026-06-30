# MCP datos Uruguay - BEN

[![Lint and test](https://github.com/okfn/mcp-datos-uruguay-ben/actions/workflows/python-lint.yml/badge.svg)](https://github.com/okfn/mcp-datos-uruguay-ben/actions/workflows/python-lint.yml)

Herramientas MCP sobre el **Balance Energetico Nacional (BEN)** de Uruguay,
publicado por el Ministerio de Industria, Energia y Mineria (MIEM) en el
[portal de datos abiertos](https://catalogodatos.gub.uy/).

Este paquete expone como tools MCP las consultas sobre la matriz
electrica, potencia instalada, factor de emision del SIN, consumo final,
abastecimiento primario, importaciones de petroleo y gas, intercambio
electrico y emisiones de CO2 por sector, mas un glosario del BEN.

**Nota:** Esto es un trabajo en progreso en etapa Alpha.

Esto esta listo para ejecutarse con el servidor OKFN MCP definido en
https://github.com/okfn/mcp-server.

## Agregar esto a un servidor OKFN MCP

Simplemente alcanza con instalar el paquete en el entorno virtual del servidor MCP y reiniciar el servidor.

## Desarrollo

- **Python**: 3.14 (ver `.python-version`)
- **Gestor de paquetes**: uv
- **Instalar dependencias**: `uv pip install .[dev]`
- **Lint**: `uv run ruff check src`
