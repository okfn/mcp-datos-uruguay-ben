from mcp.types import CallToolResult, TextContent

from mcp_server import DataToolOutput
from mcp_ckan_datos_uruguay_ben.datasets.BEN import consultas as ben
from mcp_ckan_datos_uruguay_ben.resources import register_mcp_resources


def register_tools(mcp):
    _register_ben_tools(mcp)


def register_resources(mcp):
    """ Documentos y materiales de referencia citables desde tools.
        Los recursos no son usados por la IA, lo definimos nosotros para que
        estén disponibles para la UI o para llamarse desde las tools
    """
    register_mcp_resources(mcp)


def _register_ben_tools(mcp):  # noqa: C901
    # C901 (complejidad): es una función de *wiring* que registra las tools en
    # secuencia (un `@mcp.tool` por dataset/consulta); la complejidad
    # ciclomática crece con cada tool pero no hay ramificación real que
    # simplificar. Se silencia a propósito.
    """BEN - Balance Energético Nacional (MIEM).

    Fuente: catalogodatos.gub.uy. Datos anuales desde 1965 (la serie de
    generación eléctrica arranca en 2002). Detalle por dataset y mapa
    pregunta → fuente en `datasets/BEN/data/INDEX.md`.
    """
    mcp.set_plugin_info(
        description=(
            "Herramientas sobre datos abiertos del Uruguay (catalogodatos.gub.uy). "
        ),
        instructions=(
            "Sos un asistente especializado EXCLUSIVAMENTE en energía de "
            "Uruguay. Única fuente: el Balance Energético Nacional (BEN) del "
            "Ministerio de Industria, Energía y Minería (MIEM), publicado en "
            "catalogodatos.gub.uy. Cobertura anual, sin granularidad mensual "
            "ni horaria.\n"
            "- Respondés SOLO sobre energía de Uruguay y SOLO con datos de "
            "estas tools. Nada de otros países, otros temas (como clima "
            "relacionado a energia o empresas energeticas en particular no "
            "mencionadas explicitamente en los datos), ni conocimiento "
            "propio.\n"
            "- No confundas unidades: ktep (balance energético) != GWh "
            "(energía eléctrica generada) != MW (potencia/capacidad "
            "instalada). Usá la tool que corresponde a la unidad pedida.\n"
            "- Si la pregunta no es sobre energía de Uruguay, o ninguna tool "
            "la cubre, llamá a no_tool_disponible con el motivo; no improvises "
            "con una tool que no aplica."
        ),
        sample_questions=[
            "¿Cuál es la principal fuente de generación eléctrica de Uruguay?",
            "¿Qué porcentaje de la generación es renovable?",
            "¿Cómo evolucionó la matriz desde 2002?",
            "¿Cuándo entró la energía eólica/solar en Uruguay?",
            "¿Qué fuentes están creciendo más?",
            "¿Cuánta potencia eólica/solar/hidráulica tiene Uruguay?",
            "¿Qué fuentes están creciendo en capacidad?",
            "¿Cuándo entró la primera planta solar?",
            "¿Qué tan limpia es la matriz eléctrica de Uruguay?",
            "¿Cómo evolucionó la 'limpieza' del SIN con la transición?",
            "¿En qué años fue más alta la intensidad de CO2 del SIN?",
            "¿Uruguay importa o exporta electricidad?",
            "¿Cómo evolucionó la posición exportadora del país?",
            "¿En qué años fue exportador / importador neto?",
            "¿Qué energía usan los hogares uruguayos?",
            "¿Cuánto pesa la leña en el consumo de los hogares?",
            "¿Se electrificaron los hogares? ¿Cuándo superó la electricidad a la leña?",
            "¿Aumenta o baja el consumo de energía de los hogares?",
            "¿Cuándo dejó de usarse el queroseno en los hogares?",
            "¿Qué tan renovable es la energía que usan los hogares?",
            "¿Cómo se calcula el % renovable del consumo de los hogares?",
            "¿Con qué energía se mueve el transporte en Uruguay?",
            "¿Cuánto pesan el gasoil y la gasolina en el transporte?",
            "¿Cuándo entraron los biocombustibles al transporte y cuánto pesan?",
            "¿Aumenta el consumo de energía del transporte?",
            "¿Qué tan renovable es el transporte? ¿Por qué cuesta descarbonizarlo?",
            "¿Qué significa 'energía final' en el BEN?",
            "¿Qué incluye 'residuos de biomasa'?",
            "¿Cómo define el BEN el ktep?",
        ],
    )

    @mcp.tool()
    def no_tool_disponible(razon: str | None = None) -> DataToolOutput:
        """Llamar **únicamente** cuando ninguna otra tool puede responder la
            pregunta: temas que no son energía de Uruguay (otros países, clima,
            deportes, política, etc.), o preguntas fuera del alcance del BEN.
            **Nunca** la uses si hay una tool de datos que pueda contribuir,
            aunque sea parcialmente - siempre preferí la tool específica.
            Define el alcance de ESTA instancia: solo energía de Uruguay
            (BEN/MIEM). Emite un mensaje estándar diciéndole al usuario que el
            sistema no cubre ese tema.

        Args:
            razon: Breve explicación (1 frase) de por qué ninguna tool aplica.
                Ej: "pregunta sobre Argentina, no Uruguay", "no es un tema de
                energía". Se incluye en el mensaje para que el usuario entienda
                el alcance.

        Examples:
            - no_tool_disponible(razon="pregunta sobre clima, no energía")
            - no_tool_disponible(razon="datos de Brasil, esta instancia es UY")
        """
        msg = (
            "Esta instancia responde únicamente sobre energía de Uruguay, con "
            "datos del Balance Energético Nacional (BEN/MIEM, "
            "catalogodatos.gub.uy)."
        )
        if razon:
            msg += f" Motivo: {razon}."
        msg += " Para otros temas o países, consultá otra fuente."
        return CallToolResult(
            content=[TextContent(type="text", text=msg)],
            structuredContent={"sources": []},
        )

    @mcp.tool()
    def matriz_generacion_electrica_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Matriz de generación eléctrica de Uruguay por fuente y por año, en GWh.
            Responde preguntas sobre la **matriz energética eléctrica**, la
            **transición a renovables** y la **evolución del peso de cada fuente**
            (hidráulica, eólica, solar, biomasa, fósil) en el sistema
            interconectado nacional (SIN). Útil para preguntas como:
                - ¿Cuál es la principal fuente de generación eléctrica de Uruguay?
                - ¿Qué porcentaje de la generación es renovable?
                - ¿Cómo evolucionó la matriz desde 2002?
                - ¿Cuándo entró la energía eólica/solar en Uruguay?
                - ¿Qué fuentes están creciendo más?
            Cobertura: 2002-2024 (anual; sin granularidad mensual ni horaria).
            Devuelve un texto con el mix del último año + % renovables, una
            tabla año-por-año con todas las fuentes, y un gráfico: **pie
            chart** si se pide un único año (mix de ese año), o **barras
            apiladas (stacked)** si se piden varios años (evolución).
            Datos del Ministerio de Industria, Energía y Minería (MIEM) - Balance
            Energético Nacional, publicados en catalogodatos.gub.uy. Unidad: GWh
            (gigavatios-hora) - energía eléctrica efectivamente generada,
            incluye servicio público + autoproducción industrial entregada al
            SIN. **No** confundir con `MW` (potencia instalada / capacidad) ni
            con `ktep` (que es la convención de balance energético usada en
            consumo y abastecimiento).

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 2002, el
                primer año de la serie. Para ver sólo la "era renovable" usar
                2014.
            anio_hasta: Año final del rango (incluido). Default: el último año
                disponible (típicamente 2024).

        Returns:
            str: Resumen del mix del último año (GWh y % por fuente, % de
                 renovables totales), tabla con todos los años en el rango y
                 gráfico de barras stacked por fuente.

        Examples:
            - matriz_generacion_electrica_uy()
            - matriz_generacion_electrica_uy(anio_desde=2014)
            - matriz_generacion_electrica_uy(anio_desde=2020, anio_hasta=2024)
        """
        return ben.matriz_generacion_electrica(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def potencia_instalada_electrica_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Capacidad eléctrica instalada en Uruguay por fuente, en MW (megavatios).
            Responde preguntas sobre **capacidad** (potencia físicamente
            instalada) - no confundir con generación. Cuándo se incorporó cada
            tecnología, cuánto MW de eólica/solar/hidro/biomasa/fósil hay,
            % renovables del parque generador.
            Útil para preguntas como:
                - ¿Cuánta potencia eólica/solar/hidráulica tiene Uruguay?
                - ¿Qué fuentes están creciendo en capacidad?
                - ¿Cuándo entró la primera planta solar?
            **MW = potencia (capacidad), no energía.** Una central de 100 MW
            funcionando todo el año al 100% generaría 876 GWh; el cociente
            real (factor de capacidad) es típicamente 30-90%. Para energía
            efectivamente generada usar `matriz_generacion_electrica_uy`.
            Cobertura útil real: 2003-2024 (datos previos casi todos vacíos).
            Pie chart si se pide 1 año, stacked bar si se piden varios.

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 2003.
            anio_hasta: Año final del rango (incluido). Default: último
                año disponible.

        Examples:
            - potencia_instalada_electrica_uy()
            - potencia_instalada_electrica_uy(anio_desde=2024, anio_hasta=2024)
            - potencia_instalada_electrica_uy(anio_desde=2010)
        """
        return ben.potencia_instalada_por_fuente(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def factor_emision_electrico_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Intensidad de carbono del sistema eléctrico uruguayo (FE_SIN), en
            **toneladas de CO2 por GWh** generado. Métrica única que resume
            qué tan limpio es el SIN: baja cuando crece la generación
            renovable y sube cuando aumenta el despacho de térmica fósil.
            Útil para responder:
                - ¿Qué tan limpia es la matriz eléctrica de Uruguay?
                - ¿Cómo evolucionó la 'limpieza' del SIN con la transición?
                - ¿En qué años fue más alta la intensidad de CO2 del SIN?
            Referencias: térmica gas ciclo combinado ≈ 350-400 t CO2/GWh,
            térmica carbón ≈ 800-1000, renovables ≈ 0. Uruguay 2024 = 6.3.
            Cobertura: 1965-2024 anual.
            Devuelve gráfico de líneas (varios años) o de barras vs
            referencias técnicas (un solo año).

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último
                año disponible.

        Examples:
            - factor_emision_electrico_uy()
            - factor_emision_electrico_uy(anio_desde=2010)
            - factor_emision_electrico_uy(anio_desde=2024, anio_hasta=2024)
        """
        return ben.factor_emision_electrico(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def consumo_energetico_por_sector_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Consumo final energético de Uruguay desagregado por sector, en ktep.
            Responde quién consume la energía: industria, transporte,
            residencial, comercial/servicios/sector público, primarias.
            Útil para:
                - ¿Qué sector consume más energía?
                - ¿Cómo evolucionó el consumo por sector?
                - ¿Qué sector creció más?
            Cobertura: 1965-2024 (anual). Limitación: no hay sub-segmentación
            del transporte (auto/ómnibus/aviación no se distinguen). Para
            'intensidad energética industrial' (energía/VAB) hay que cruzar
            con BCU - no está en BEN.
            Pie chart si se pide 1 año, stacked bar si se piden varios.
            **ktep ≈ 11.63 GWh** - unidad estándar de balance energético.

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último
                año disponible (típicamente 2024).

        Examples:
            - consumo_energetico_por_sector_uy()
            - consumo_energetico_por_sector_uy(anio_desde=2024, anio_hasta=2024)
            - consumo_energetico_por_sector_uy(anio_desde=2000)
        """
        return ben.consumo_final_por_sector(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def consumo_energetico_por_fuente_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Consumo final energético de Uruguay desagregado por fuente, en ktep.
            Responde **qué tipo de energía** consumen los usuarios finales:
            derivados del petróleo, electricidad, biomasa (leña/residuos),
            gas natural, biocombustibles, etc.
            Útil para:
                - ¿Qué fuentes predominan del lado demanda?
                - ¿Cuánto pesan los combustibles fósiles en el consumo final?
                - ¿% renovable del consumo final?
            El TOTAL coincide con el de `consumo_energetico_por_sector_uy`
            (misma magnitud, dos desagregaciones).
            Cobertura: 1965-2024 (anual). Pie chart si se pide 1 año,
            stacked bar si se piden varios.
            **ktep ≈ 11.63 GWh** - unidad estándar de balance energético.

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - consumo_energetico_por_fuente_uy()
            - consumo_energetico_por_fuente_uy(anio_desde=2024, anio_hasta=2024)
            - consumo_energetico_por_fuente_uy(anio_desde=2000)
        """
        return ben.consumo_final_por_fuente(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def tendencia_demanda_energetica_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Evolución del consumo energético TOTAL de Uruguay, en ktep/año.
            Vista macro: ¿el país aumenta o reduce su demanda? ¿Cuánto creció
            en los últimos 5 años? ¿Cuál es el consumo total del último año?
            Devuelve serie de tiempo (gráfico de líneas) con todos los años
            del rango.
            Cobertura: 1965-2024 (anual).
            **No** computa per-cápita ni intensidad/PIB: BEN no incluye
            población ni PIB; cruzar con INE/BCU para esas métricas.

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - tendencia_demanda_energetica_uy()
            - tendencia_demanda_energetica_uy(anio_desde=2020)
            - tendencia_demanda_energetica_uy(anio_desde=2000)
        """
        return ben.tendencia_demanda_total(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def consumo_residencial_por_fuente_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Consumo de energía del SECTOR RESIDENCIAL (hogares) de Uruguay,
            abierto fuente por fuente, en ktep.
            Mientras `consumo_energetico_por_fuente_uy` agrupa las fuentes para
            todo el país, esta tool las muestra **una por una sólo para los
            hogares**: electricidad, leña, supergás (GLP), gas natural,
            residuos de biomasa, solar térmica, queroseno, gasoil, carbón
            vegetal, etc.
            Útil para:
                - ¿Qué energía usan los hogares uruguayos hoy?
                - ¿Cuánto pesa la leña / el supergás / la electricidad en el hogar?
                - ¿Qué porcentaje del consumo del hogar es renovable?
                - ¿Cómo cambió el mix energético residencial desde 1965?
            El TOTAL coincide con la columna 'Residencial' de
            `consumo_energetico_por_sector_uy` (misma magnitud, otra apertura).
            Cobertura: 1965-2024 (anual). Pie chart si se pide 1 año, stacked
            bar si se piden varios. Devuelve mix del último año + % renovable,
            tabla año-por-año y gráfico. **ktep ≈ 11.63 GWh.**

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año
                disponible (típicamente 2024).

        Examples:
            - consumo_residencial_por_fuente_uy()
            - consumo_residencial_por_fuente_uy(anio_desde=2024, anio_hasta=2024)
            - consumo_residencial_por_fuente_uy(anio_desde=2000)
        """
        return ben.consumo_residencial_por_fuente(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def tendencia_consumo_residencial_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Evolución del consumo energético TOTAL del sector residencial
            (hogares) de Uruguay, en ktep/año.
            Vista macro del hogar: ¿los hogares consumen más o menos energía
            que antes? ¿cuánto creció en los últimos años? ¿cuál es el total
            del último año?
            Útil para:
                - ¿Cuánta energía consumen los hogares de Uruguay?
                - ¿Aumenta o baja el consumo residencial?
                - ¿Cómo evolucionó desde 1965 / en la última década?
            Devuelve serie de tiempo (gráfico de líneas) del TOTAL del hogar.
            Cobertura: 1965-2024 (anual).
            **No** computa per-cápita ni por hogar: BEN no incluye población
            ni cantidad de hogares; cruzar con INE para esas métricas.

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - tendencia_consumo_residencial_uy()
            - tendencia_consumo_residencial_uy(anio_desde=2000)
            - tendencia_consumo_residencial_uy(anio_desde=2020)
        """
        return ben.tendencia_consumo_residencial(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def electrificacion_hogares_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Participación (%) de cada fuente en el consumo del hogar uruguayo a
            lo largo del tiempo, con foco en la **electrificación** y el cruce
            histórico leña <-> electricidad.
            A diferencia de `consumo_residencial_por_fuente_uy` (que da ktep
            absolutos), esta tool entrega **porcentajes del total de cada año**,
            ideal para contar la transición del hogar.
            Útil para:
                - ¿Se electrificaron los hogares uruguayos?
                - ¿En qué año la electricidad superó a la leña en el hogar?
                - ¿Cómo perdió peso el queroseno / ganó peso el supergás?
                - ¿Qué participación tiene la solar térmica en el hogar?
            Devuelve un gráfico de líneas con la participación (%) de las
            principales fuentes del hogar año a año.
            Cobertura: 1965-2024 (anual). Los valores son % del total del año,
            no ktep (para absolutos usar `consumo_residencial_por_fuente_uy`).

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - electrificacion_hogares_uy()
            - electrificacion_hogares_uy(anio_desde=1990)
            - electrificacion_hogares_uy(anio_desde=2000, anio_hasta=2024)
        """
        return ben.electrificacion_hogares(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def fuente_residencial_detalle_uy(
        fuente: str,
        anio_desde: int | None = None,
        anio_hasta: int | None = None,
    ) -> DataToolOutput:
        """Serie histórica de UNA fuente puntual en el consumo del hogar
            uruguayo, en ktep (drill-down para análisis fino).
            Devuelve la evolución de esa fuente, su participación en el total
            del hogar, su año pico, su primer año con dato y su crecimiento
            anual compuesto.
            Útil para:
                - ¿Cómo evolucionó el uso de leña / supergás / electricidad
                  en los hogares?
                - ¿Cuándo dejó de usarse el queroseno en el hogar?
                - ¿Cuándo apareció la solar térmica / la biomasa moderna?
                - ¿En qué año fue máximo el consumo de una fuente?
            Cobertura: 1965-2024 (anual). Devuelve gráfico de líneas de la
            fuente elegida.

        Args:
            fuente: Código de la fuente a analizar. Opciones (código = fuente):
                EE = electricidad, L = leña, GLP = supergás/propano,
                GN = gas natural, RB = residuos de biomasa (pellets, etc.),
                S = solar térmica, Go = gasoil, CV = carbón vegetal,
                Q = queroseno, Ga = gasolina automotora, Fo = fueloil,
                Be = bioetanol, Do = diéseloil, GM = gas manufacturado,
                Bd = biodiésel. Acepta también el nombre (ej. "supergas",
                "leña", "solar").
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - fuente_residencial_detalle_uy(fuente="EE")
            - fuente_residencial_detalle_uy(fuente="L", anio_desde=1990)
            - fuente_residencial_detalle_uy(fuente="GLP")
        """
        return ben.fuente_residencial_detalle(
            fuente=fuente, anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def renovables_residencial_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """% renovable del consumo energético del hogar uruguayo según el
            criterio del **Indicador ODS 7.2.1 del BEN** ('Proporción de la
            energía renovable en el consumo final total de energía'), año a año.
            A diferencia de un conteo de 'renovables directas', este criterio
            **cuenta también la parte renovable de la electricidad**: como la
            matriz del SIN es casi totalmente renovable, electrificar el hogar
            sube el indicador. La electricidad se reparte en su fracción
            renovable y fósil según el mix de generación del SIN de cada año,
            por lo que la serie arranca en **2002** (primer año con mix del SIN).
            Útil para:
                - ¿Qué tan renovable es la energía que usan los hogares?
                - ¿Cómo evolucionó el % renovable del consumo residencial?
                - ¿Cuánto aporta la electricidad limpia al renovable del hogar?
            El 64% que publica el BEN para 2024 es el indicador NACIONAL (todos
            los sectores); esta tool da el del sector residencial, más alto por
            el peso de la electricidad y la leña.
            Cobertura: 2002-2024 (anual). Devuelve gráfico de barras apiladas
            (renovable vs no renovable) por año. **ktep ≈ 11.63 GWh.**

        Args:
            anio_desde: Año inicial del rango (incluido). Default y mínimo:
                2002 (años anteriores se recortan: sin mix del SIN no se puede
                aplicar el criterio 7.2.1).
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - renovables_residencial_uy()
            - renovables_residencial_uy(anio_desde=2013)
            - renovables_residencial_uy(anio_desde=2024, anio_hasta=2024)
        """
        return ben.renovables_residencial(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def renovable_residencial_calculo_uy(anio: int | None = None) -> DataToolOutput:
        """% renovable del consumo del hogar uruguayo para UN año, mostrando el
            **cálculo paso a paso** a partir de los dos datasets que lo
            alimentan (consumo residencial por fuente + generación eléctrica
            del SIN). Es la versión auditable/explicativa de
            `renovables_residencial_uy`: en vez de una serie, desglosa un único
            año para que se vea de dónde sale el número.
            Muestra: (1) las renovables directas del hogar fuente por fuente,
            (2) la fracción renovable del SIN ese año (GWh renovables / GWh
            totales), (3) la electricidad renovable del hogar (electricidad x
            esa fracción), (4) el % renovable final, y la comparación con el
            renovable "sólo directo" (sin electricidad).
            Útil para:
                - ¿Cómo se calcula el % renovable del hogar?
                - ¿Por qué da X% y no el 64% nacional?
                - ¿Cuánto del renovable del hogar es leña y cuánto electricidad?
            Para años anteriores a 2002 (sin mix del SIN) sólo puede informar el
            renovable directo y lo aclara. Devuelve un pie chart con la
            composición renovable directa / electricidad renovable / no
            renovable del año.

        Args:
            anio: Año a desglosar. Default: último año disponible (2024). El
                criterio completo (con electricidad) requiere año >= 2002.

        Examples:
            - renovable_residencial_calculo_uy()
            - renovable_residencial_calculo_uy(anio=2024)
            - renovable_residencial_calculo_uy(anio=2010)
        """
        return ben.renovable_residencial_calculo(anio=anio)

    @mcp.tool()
    def consumo_transporte_por_fuente_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Consumo de energía del SECTOR TRANSPORTE de Uruguay, abierto fuente
            por fuente, en ktep.
            Muestra qué combustibles mueven el transporte: gasoil, gasolina
            automotora, biocombustibles (bioetanol, biodiésel), turbocombustible
            y gasolina de aviación, fueloil (marítimo), y la incipiente
            electricidad.
            Útil para:
                - ¿Con qué energía se mueve el transporte en Uruguay?
                - ¿Cuánto pesan el gasoil y la gasolina?
                - ¿Qué porcentaje es biocombustible?
                - ¿Cómo cambió el mix del transporte desde 1965?
            El TOTAL coincide con la columna 'Transporte' de
            `consumo_energetico_por_sector_uy` (misma magnitud, otra apertura).
            Cobertura: 1965-2024 (anual). Pie chart si se pide 1 año, stacked
            bar si se piden varios. **ktep ≈ 11.63 GWh.**

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - consumo_transporte_por_fuente_uy()
            - consumo_transporte_por_fuente_uy(anio_desde=2024, anio_hasta=2024)
            - consumo_transporte_por_fuente_uy(anio_desde=2000)
        """
        return ben.consumo_transporte_por_fuente(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def tendencia_consumo_transporte_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Evolución del consumo energético TOTAL del sector transporte de
            Uruguay, en ktep/año.
            Vista macro del transporte: ¿consume más o menos energía que antes?
            ¿cuánto creció? El transporte es de los sectores que más creció en
            demanda.
            Útil para:
                - ¿Cuánta energía consume el transporte en Uruguay?
                - ¿Aumenta o baja el consumo del transporte?
                - ¿Cómo evolucionó desde 1965 / en la última década?
            Devuelve serie de tiempo (gráfico de líneas) del TOTAL del sector.
            Cobertura: 1965-2024 (anual). BEN no incluye parque automotor ni
            población; cruzar con otras fuentes para 'consumo por vehículo'.

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - tendencia_consumo_transporte_uy()
            - tendencia_consumo_transporte_uy(anio_desde=2000)
            - tendencia_consumo_transporte_uy(anio_desde=2020)
        """
        return ben.tendencia_consumo_transporte(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def participacion_fuentes_transporte_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Participación (%) de cada fuente en el consumo del transporte de
            Uruguay a lo largo del tiempo, con foco en la entrada de los
            biocombustibles (2010) y el peso gasoil vs gasolina.
            A diferencia de `consumo_transporte_por_fuente_uy` (que da ktep
            absolutos), entrega porcentajes del total de cada año.
            Útil para:
                - ¿Qué fuente domina el transporte y cómo cambió?
                - ¿Cuándo entraron los biocombustibles y cuánto pesan?
                - ¿Cuándo el gasoil superó a la gasolina?
            Devuelve un gráfico de líneas con la participación (%) de las
            principales fuentes año a año.
            Cobertura: 1965-2024 (anual). Los valores son % del total del año,
            no ktep (para absolutos usar `consumo_transporte_por_fuente_uy`).

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - participacion_fuentes_transporte_uy()
            - participacion_fuentes_transporte_uy(anio_desde=2005)
            - participacion_fuentes_transporte_uy(anio_desde=2010, anio_hasta=2024)
        """
        return ben.participacion_fuentes_transporte(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def fuente_transporte_detalle_uy(
        fuente: str,
        anio_desde: int | None = None,
        anio_hasta: int | None = None,
    ) -> DataToolOutput:
        """Serie histórica de UNA fuente puntual en el consumo del transporte
            de Uruguay, en ktep (drill-down para análisis fino).
            Devuelve la evolución de esa fuente, su participación en el total
            del transporte, su año pico, su primer año con dato y su
            crecimiento anual compuesto.
            Útil para:
                - ¿Cómo evolucionó el gasoil / la gasolina / el biodiésel?
                - ¿Cuándo entraron los biocombustibles y cuánto crecieron?
                - ¿En qué año fue máximo el consumo de una fuente?
            Cobertura: 1965-2024 (anual). Devuelve gráfico de líneas de la
            fuente elegida.

        Args:
            fuente: Código de la fuente a analizar. Opciones (código = fuente):
                Go = gasoil, Ga = gasolina automotora, Be = bioetanol,
                Bd = biodiésel, EE = electricidad, T = turbocombustible,
                GAv = gasolina de aviación, Fo = fueloil, Do = diéseloil,
                Q = queroseno. Acepta también el nombre (ej. "gasoil",
                "biodiesel", "turbo").
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - fuente_transporte_detalle_uy(fuente="Go")
            - fuente_transporte_detalle_uy(fuente="Bd", anio_desde=2010)
            - fuente_transporte_detalle_uy(fuente="Ga")
        """
        return ben.fuente_transporte_detalle(
            fuente=fuente, anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def renovables_transporte_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """% renovable del consumo del transporte de Uruguay según el criterio
            del **Indicador ODS 7.2.1 del BEN**, año a año.
            Cuenta como renovable los biocombustibles (bioetanol, biodiésel) y
            la parte renovable de la electricidad consumida (repartida según el
            mix de generación del SIN de cada año). La serie arranca en **2002**
            (primer año con mix del SIN); los biocombustibles entraron en 2010.
            Útil para:
                - ¿Qué tan renovable es la energía del transporte?
                - ¿Cómo evolucionó el % renovable del transporte?
                - ¿Por qué el transporte es el sector más difícil de
                  descarbonizar?
            El transporte es el sector más fósil: el % renovable es bajo aun con
            este criterio. El 64% que publica el BEN para 2024 es el indicador
            NACIONAL (todos los sectores), no el del transporte.
            Cobertura: 2002-2024 (anual). Devuelve gráfico de barras apiladas
            (renovable vs no renovable). **ktep ≈ 11.63 GWh.**

        Args:
            anio_desde: Año inicial del rango (incluido). Default y mínimo:
                2002 (sin mix del SIN no se puede aplicar el criterio 7.2.1).
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - renovables_transporte_uy()
            - renovables_transporte_uy(anio_desde=2010)
            - renovables_transporte_uy(anio_desde=2024, anio_hasta=2024)
        """
        return ben.renovables_transporte(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def renovable_transporte_calculo_uy(anio: int | None = None) -> DataToolOutput:
        """% renovable del consumo del transporte de Uruguay para UN año,
            mostrando el **cálculo paso a paso** a partir de los dos datasets
            que lo alimentan (consumo transporte por fuente + generación
            eléctrica del SIN). Es la versión auditable/explicativa de
            `renovables_transporte_uy`.
            Muestra: (1) los biocombustibles del transporte, (2) la fracción
            renovable del SIN ese año (GWh renovables / GWh totales), (3) la
            electricidad renovable del transporte, (4) el % renovable final, y
            la comparación con el renovable "sólo biocombustibles".
            Útil para:
                - ¿Cómo se calcula el % renovable del transporte?
                - ¿Cuánto aportan los biocombustibles vs la electricidad?
            Para años anteriores a 2002 (sin mix del SIN) sólo informa el
            renovable directo y lo aclara. Devuelve un pie chart con la
            composición del año.

        Args:
            anio: Año a desglosar. Default: último año disponible (2024). El
                criterio completo (con electricidad) requiere año >= 2002.

        Examples:
            - renovable_transporte_calculo_uy()
            - renovable_transporte_calculo_uy(anio=2024)
            - renovable_transporte_calculo_uy(anio=2015)
        """
        return ben.renovable_transporte_calculo(anio=anio)

    @mcp.tool()
    def matriz_energetica_primaria_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Oferta primaria de energía total del país por fuente, en ktep.
            Es **la matriz energética** completa (no sólo eléctrica): suma
            todas las fuentes que ingresan al sistema (importación +
            producción local) - petróleo y derivados, biomasa, hidráulica,
            eólica, solar, gas natural, carbón/coque, electricidad importada,
            residuos industriales.
            Útil para:
                - ¿Qué fuentes predominan en la matriz energética?
                - ¿% renovable vs no renovable de la oferta primaria?
                - ¿Cómo evolucionó la participación renovable?
                - Diversificación (índice de Herfindahl normalizado).
            Cobertura: 1965-2024 (anual). Pie chart si 1 año, stacked bar si
            varios.
            **ktep ≈ 11.63 GWh.** Para sólo el sub-sistema eléctrico ver
            `matriz_generacion_electrica_uy`.

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - matriz_energetica_primaria_uy()
            - matriz_energetica_primaria_uy(anio_desde=2024, anio_hasta=2024)
            - matriz_energetica_primaria_uy(anio_desde=2000)
        """
        return ben.matriz_abastecimiento_primario(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def dependencia_energetica_externa_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """% de energía importada vs producida localmente, año a año (ktep).
            Indicador de **seguridad energética y dependencia externa**.
            Definición usada: importado = electricidad importada + gas
            natural + petróleo y derivados + carbón y coque. Local = el
            resto (renovables locales, biomasa, residuos industriales).
            Útil para:
                - ¿Cuánta energía se importa vs se produce localmente?
                - ¿Cuál es el nivel de dependencia energética del país?
                - ¿Cómo evolucionó la dependencia con la entrada de
                  renovables locales?
            Cobertura: 1965-2024. Pie chart (importado vs local) si se pide
            1 año; stacked bar evolutivo si se piden varios años.

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - dependencia_energetica_externa_uy()
            - dependencia_energetica_externa_uy(anio_desde=2024, anio_hasta=2024)
            - dependencia_energetica_externa_uy(anio_desde=2000)
        """
        return ben.dependencia_energetica_externa(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def perdidas_transformacion_energetica_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Pérdidas de transformación + autoconsumo del sector energético, en ktep.
            Calcula la diferencia entre **oferta primaria** (lo que entra al
            sistema) y **consumo final** (lo que llega a los usuarios).
            Esta diferencia agrupa: pérdidas físicas en transporte y
            distribución, autoconsumo del sector energético (refinería,
            centrales) y pérdidas termodinámicas de transformación
            (calor → electricidad).
            Útil para:
                - ¿Qué pérdidas tiene el sistema en transformación y
                  distribución?
                - ¿Cómo evolucionó la eficiencia agregada del sistema?
            Cobertura: 1965-2024. Cruza dos datasets: abastecimiento +
            consumo final por fuente.

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - perdidas_transformacion_energetica_uy()
            - perdidas_transformacion_energetica_uy(anio_desde=2010)
            - perdidas_transformacion_energetica_uy(anio_desde=2024, anio_hasta=2024)
        """
        return ben.perdidas_transformacion(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def importacion_petroleo_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Importación de petróleo crudo + carga de refinería, en ktep.
            Dos magnitudes: cuánto crudo se importó y cuánto efectivamente
            se procesó en refinería. La diferencia refleja stocks.
            Útil para:
                - ¿Cuánto petróleo importa Uruguay?
                - ¿Cómo evolucionaron las importaciones de petróleo?
                - Vulnerabilidad ante shocks del precio del petróleo (input
                  clave).
            Cobertura: 1965-2024. Devuelve gráfico de líneas (varios años) o
            barras (un único año).

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - importacion_petroleo_uy()
            - importacion_petroleo_uy(anio_desde=2010)
            - importacion_petroleo_uy(anio_desde=2024, anio_hasta=2024)
        """
        return ben.importacion_petroleo(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def importacion_gas_natural_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Serie anual de importaciones de gas natural a Uruguay, en ktep.
            Volúmenes modestos comparados con petróleo y biomasa. La serie
            tiene datos desde 1998 (años previos vacíos).
            Útil para:
                - ¿Cuánto gas natural importa Uruguay?
                - ¿Cómo evolucionaron las importaciones de gas?
                - Peso del gas natural en la matriz primaria (combinar con
                  `matriz_energetica_primaria_uy`).
            Cobertura útil: 1998-2024 (años pre-1998 vacíos).

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1998.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - importacion_gas_natural_uy()
            - importacion_gas_natural_uy(anio_desde=2010)
            - importacion_gas_natural_uy(anio_desde=2024, anio_hasta=2024)
        """
        return ben.importacion_gas_natural(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def intercambio_electrico_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Intercambio eléctrico de Uruguay - importación, exportación y
            saldo neto, en ktep.
            Las dos columnas son **magnitudes positivas** (no usar signo):
            el saldo neto se calcula como exportación menos importación. La
            serie muestra el paso de una posición importadora a una
            exportadora neta en varios años de la última década.
            Útil para:
                - ¿Uruguay importa o exporta electricidad?
                - ¿Cómo evolucionó la posición exportadora del país?
                - ¿En qué años fue exportador / importador neto?
            Cobertura: 1965-2024 (anual). Devuelve gráfico de barras
            agrupadas (impo vs expo) por año.

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - intercambio_electrico_uy()
            - intercambio_electrico_uy(anio_desde=2010)
            - intercambio_electrico_uy(anio_desde=2024, anio_hasta=2024)
        """
        return ben.intercambio_electricidad(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def emisiones_co2_por_sector_uy(
        anio_desde: int | None = None, anio_hasta: int | None = None
    ) -> DataToolOutput:
        """Emisiones de CO2 por sector en Uruguay (combustión de combustibles
            fósiles), en **Gg CO2** (gigagramos = kilotoneladas).
            Sectores: transporte, industrial, centrales eléctricas (servicio
            público), residencial, comercial/servicios/sec.público,
            actividades primarias, consumo propio del sector energético.
            Útil para:
                - ¿Qué sectores son los grandes emisores?
                - ¿Cómo evolucionaron las emisiones por sector?
                - 'Termómetro' de la transición: caída de CE_SP con la
                  entrada de renovables.
            Cobertura: 1965-2024. Pie chart si 1 año, stacked bar si varios.
            Notas IPCC: las partidas Q_B (quema de biomasa) y BI (búnker
            internacional) son **informativas**, no se suman al inventario
            nacional. Sólo CO2 (no CH4/N2O) y sólo combustión (no procesos
            industriales como cemento). Para intensidad eléctrica del SIN
            usar `factor_emision_electrico_uy`.

        Args:
            anio_desde: Año inicial del rango (incluido). Default: 1965.
            anio_hasta: Año final del rango (incluido). Default: último año.

        Examples:
            - emisiones_co2_por_sector_uy()
            - emisiones_co2_por_sector_uy(anio_desde=2024, anio_hasta=2024)
            - emisiones_co2_por_sector_uy(anio_desde=2000)
        """
        return ben.emisiones_co2_por_sector(
            anio_desde=anio_desde, anio_hasta=anio_hasta,
        )

    @mcp.tool()
    def glosario_ben(concepto: str) -> DataToolOutput:
        """Definición oficial de un concepto del Balance Energético Nacional,
            tomada **textualmente** del capítulo "8. Metodología" del Libro del
            BEN 2024 (MIEM). Usar cuando el usuario pregunta qué significa o
            cómo se define un término del BEN, o qué incluye una fuente de
            energía. Las tools de datos ya adjuntan las definiciones que les
            aplican; esta tool es para definiciones pedidas explícitamente o
            para conceptos que ninguna tool de datos cubre.
            Útil para preguntas como:
                - ¿Qué es la energía final / neta / bruta / primaria?
                - ¿Qué incluye 'residuos de biomasa' / 'residuos industriales'?
                - ¿Cómo se define el ktep? ¿Y un centro de transformación?
                - ¿Qué cuenta como renovable en el abastecimiento?
            Devuelve la definición literal, la sección del libro (§8.x) y cita
            el recurso del libro (PDF).
            Usar tambien para ser mas claros en las respuestas. No usar
            definiciones genéricas.

        Args:
            concepto: Clave exacta del concepto a definir. Conceptos
                disponibles:
                energia_primaria, energia_secundaria, energia_bruta,
                energia_neta, energia_final, centro_de_transformacion,
                sector_de_consumo, produccion, importacion, exportacion,
                perdidas, variacion_de_inventario, energia_no_utilizada,
                carbon_mineral, gas_natural, energia_solar, residuos_de_biomasa,
                biomasa_para_biocombustibles, residuos_industriales, ktep,
                emisiones_co2, matriz_primaria, clasificacion_por_origen,
                clasificacion_por_tipo, renovable_consumo_final.

        Examples:
            - glosario_ben(concepto="energia_final")
            - glosario_ben(concepto="residuos_de_biomasa")
            - glosario_ben(concepto="ktep")
        """
        return ben.glosario(concepto=concepto)


def main() -> None:
    print("Hello from mcp-ckan-datos-uruguay-ben")
