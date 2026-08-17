# Propuesta de Proyecto

## Trabajo Práctico - Series Temporales

**Maestría en Ciencia de Datos / Análisis de Series Temporales**

---

# Título

**Ozono Troposférico, Clima y Radiación Solar en la Cuenca de Los Ángeles (California, EE.UU.) — Modelos SARIMA y VAR**

---

# Nota sobre el origen de este proyecto

Este proyecto **reemplaza** a uno anterior, basado en demanda eléctrica, generación y temperatura del AMBA (Argentina). El contenido de aquel proyecto se conserva sin borrar en `_archivo_TP1_AMBA/`.

El motivo del cambio: se necesitaba superar los 100.000 registros por serie para el TP Final. El histórico horario real de CAMMESA (demanda por provincia, oferta por fuente/tecnología) sólo cubre 2023-01-01 a 2026-06-30 (~30.648 horas) — muy por debajo de lo necesario, y sin una vía automatizable para extenderlo hacia atrás sin recurrir a trucos de conteo (sumar provincias o tecnologías como si fueran observaciones independientes). Tras evaluar varias alternativas (otros países, otros dominios: tránsito, calidad del aire, radiación solar), se eligió esta combinación en California porque:

- Las tres fuentes son de **acceso público y gratuito**.
- Cada serie por sí sola supera los 100.000 registros horarios.
- Las tres correlacionan entre sí por una razón física real (ver más abajo), no sólo por casualidad de volumen.

---

# Objetivo General

Modelar el comportamiento horario del ozono troposférico en la cuenca de Los Ángeles, considerando su dependencia de variables meteorológicas y de radiación solar, para realizar pronósticos (SARIMA) y estudiar las relaciones dinámicas entre las tres series (VAR, Granger, impulso-respuesta).

---

# Series Seleccionadas

| Serie                   | Unidad                 | Fuente                   | Frecuencia nativa |
| ----------------------- | ---------------------- | ------------------------ | ----------------- |
| Ozono troposférico (O₃) | ppm                    | EPA AQS / AirData        | Horaria           |
| Temperatura y clima     | °C (y otras variables) | NOAA ISD (Global Hourly) | Horaria           |
| Radiación solar         | W/m²                   | NSRDB (NLR, ex-NREL)     | 30 minutos        |

---

# Justificación de la elección

El ozono troposférico (smog fotoquímico) se forma por una reacción bien documentada en química atmosférica: óxidos de nitrógeno (NOx) + compuestos orgánicos volátiles + **radiación solar** → ozono. La concentración de ozono es máxima a media tarde, cuando la radiación solar es más intensa, y depende también de la temperatura. Es la misma lógica causal que se usaba en el proyecto anterior con temperatura → demanda eléctrica, pero aplicada a calidad del aire:

```
Radiación Solar ──┐
                   ▼
              Ozono Troposférico
                   ▲
Temperatura/Clima ─┘
```

Este vínculo permite aplicar VAR, funciones impulso-respuesta y causalidad de Granger con fundamento físico, no sólo estadístico.

---

# Ubicación elegida: Los Ángeles, California

Para que las tres series sean comparables (mismo punto geográfico, mismo huso horario, misma cuenca atmosférica):

- **Clima y radiación solar**: coordenadas de LAX — 33.9425, -118.4081.
- **Ozono**: estación de EPA AQS _Los Angeles-North Main Street_ (sitio `06-037-1103`), a pocos kilómetros de LAX, dentro de la misma cuenca del aire (South Coast Air Basin) — una de las estaciones de ozono con historial más largo de California.

---

# Alcance del proyecto (verificado, no estimado)

| Fuente                                  | Cobertura horaria real verificada |
| --------------------------------------- | --------------------------------- |
| EPA AQS (ozono)                         | Desde 1990                        |
| NOAA ISD (LAX)                          | Desde 1944                        |
| NSRDB GOES Aggregated (radiación solar) | Desde 1998                        |

**El período común del proyecto es 1998 – año actual - 1** (NSRDB es la fuente que acota el rango; se excluye el año en curso porque los tres organismos publican sus archivos anuales con demora). Con este rango:

**≈ 28 años × 8.760 horas ≈ 245.000 observaciones horarias por serie**

Muy por encima de los 100.000 registros requeridos, con una sola serie limpia por variable — sin sumar estaciones, provincias ni tecnologías para inflar el conteo.

---

# Acceso y licencias de las tres fuentes (verificado)

- **EPA AQS / AirData**: dominio público, sin restricciones, no requiere pedir permiso. Descarga directa: `https://aqs.epa.gov/aqsweb/airdata/hourly_{código_parámetro}_{año}.zip` (código de ozono: `44201`).
- **NOAA / NCEI (ISD)**: datos del gobierno federal de EE.UU., política de dominio público (CC0), se recomienda citar como buena práctica. Descarga directa: `https://www.ncei.noaa.gov/data/global-hourly/access/{año}/{id_estación}.csv`.
- **NSRDB (NLR, ex-NREL)**: pública y gratuita, requiere una **API key propia gratuita y autoservicio** (a diferencia de Caltrans PeMS, que requiere aprobación manual de 1-2 días — por eso se descartó tránsito como tercera serie). Alta en `https://developer.nlr.gov/signup/`.

**Nota sobre el nombre del organismo:** NREL ("National Renewable Energy Laboratory") se renombró a **NLR** ("National Laboratory of the Rockies"); el dominio `developer.nrel.gov` ya no resuelve, el actual es `developer.nlr.gov`. Verificado en vivo antes de escribir el notebook de descarga.

El único límite de uso real encontrado (Caltrans, no aplica a estas 3 fuentes): no usar el nombre de la agencia para publicidad — irrelevante para un TP académico.

---

# Organización del Proyecto

```
Serie_Temporales/

│
├── _archivo_TP1_AMBA/              (proyecto anterior, conservado sin borrar)
│
├── data/
│   ├── raw/
│   │   ├── epa_aqs/                (descarga automática, un .zip por año)
│   │   ├── noaa_isd/                (descarga automática, un .csv por año)
│   │   └── nsrdb/                   (descarga automática, requiere API key propia)
│   ├── interim/
│   └── processed/
│
├── notebooks/
│   ├── 01_descarga_datos.ipynb
│   ├── 02_limpieza.ipynb
│   ├── 03_eda.ipynb
│   ├── 04_estacionariedad.ipynb
│   ├── 05_sarima.ipynb
│   ├── 06_var.ipynb
│   └── 07_pronosticos.ipynb
│
├── src/
│   ├── descarga.py
│   ├── utils.py
│   ├── limpieza.py
│   ├── sarima.py
│   └── var.py
│
├── outputs/
│   ├── figuras/
│   ├── tablas/
│   ├── modelos/
│   └── reportes/
│
├── docs/
│
├── logs/
│
├── README.md
│
└── requirements.txt
```

---

# Próximo paso

Ejecutar `01_descarga_datos.ipynb`: crea la estructura de carpetas, descarga las tres series (EPA AQS y NOAA ISD sin necesidad de credenciales; NSRDB requiere que cada integrante saque su propia API key gratuita), y valida que los archivos anuales esperados estén completos antes de pasar a `02_limpieza.ipynb`.

---

# Portabilidad — correrlo desde cualquier ubicación

El notebook detecta la raíz del proyecto de forma relativa (a partir del directorio donde corre, no de una ruta fija), así que **la carpeta `Serie_Temporales/` puede copiarse a cualquier disco, usuario o equipo** (`C:\`, `C:\TEMP`, un pendrive, etc.) y funciona igual, sin editar ninguna ruta en el código. Cada integrante del grupo sólo necesita:

1. Un entorno de Python con las librerías de `requirements.txt`.
2. Su propia API key gratuita de NSRDB (ver sección de arriba) — **no reutilizar la de otro integrante**, ni pegarla directamente en el notebook si van a compartir la carpeta: mejor definirla como variable de entorno (`NSRDB_API_KEY`, `NSRDB_EMAIL`) antes de abrir Jupyter.
