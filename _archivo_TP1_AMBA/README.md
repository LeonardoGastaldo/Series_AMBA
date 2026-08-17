# Propuesta de Proyecto

## Trabajo Práctico 1 - Series Temporales

**Maestría en Ciencia de Datos / Análisis de Series Temporales**

---

# Título

**Análisis y Pronóstico de la Demanda Eléctrica del Área Metropolitana de Buenos Aires (AMBA) mediante Modelos SARIMA y VAR**

---

# Objetivo General

Desarrollar un análisis integral de tres series temporales relacionadas con el sistema eléctrico argentino utilizando técnicas univariadas y multivariadas de series temporales.

El objetivo es modelar el comportamiento de la demanda eléctrica del Área Metropolitana de Buenos Aires (AMBA), considerando la influencia de variables operativas y climáticas, para realizar pronósticos y estudiar las relaciones dinámicas entre ellas mediante modelos SARIMA y VAR.

---

# Series Seleccionadas

Se trabajará con tres series temporales horarias provenientes de organismos oficiales argentinos.

| Serie                | Unidad | Fuente                                |
| -------------------- | ------ | ------------------------------------- |
| Demanda eléctrica    | MW     | CAMMESA                               |
| Generación eléctrica | MW     | CAMMESA                               |
| Temperatura          | °C     | Servicio Meteorológico Nacional (SMN) |

---

# Justificación de la elección

A diferencia de seleccionar tres series independientes, se eligieron variables que poseen una relación física y operativa claramente establecida.

La demanda eléctrica depende, entre otros factores, de las condiciones meteorológicas, especialmente de la temperatura, debido al uso intensivo de sistemas de calefacción y refrigeración.

Por otra parte, la generación eléctrica responde directamente a las necesidades de abastecimiento del sistema eléctrico, ajustándose continuamente a la demanda de energía.

Esta relación puede representarse mediante el siguiente esquema conceptual:

```
Temperatura
      │
      ▼
Demanda Eléctrica
      │
      ▼
Generación Eléctrica
```

Este vínculo permite aplicar modelos VAR, funciones impulso-respuesta y pruebas de causalidad de Granger con una sólida fundamentación teórica.

---

# Alcance del Trabajo

Se desarrollarán los siguientes análisis:

- Exploración inicial de las series.
- Análisis de tendencia y estacionalidad.
- Conversión a series estacionarias.
- Pruebas de raíces unitarias.
- Modelado SARIMA individual.
- Comparación entre modelos.
- Diagnóstico de residuos.
- Pronósticos individuales.
- Modelos VAR.
- Causalidad de Granger.
- Funciones Impulso-Respuesta.
- Descomposición de la varianza del error de pronóstico.

---

# Alcance del TP Inicial

**Actualizado tras verificar las fuentes reales (ver "Notas y Limitaciones" más abajo).** El período 2018-2023 planteado originalmente no es alcanzable: el histórico horario real de CAMMESA (demanda por provincia y oferta por fuente/tecnología) sólo está disponible, vía el reporte de "Reportes Actuales e Históricos", desde:

**2023-01-01 a 2026-06-30**

Frecuencia:

**Horaria**

Cantidad real (verificada leyendo los archivos, no estimada):

**30.648 observaciones horarias por serie**

Es una cantidad menor a la estimación original de 50.000-60.000, pero de sobra suficiente para desarrollar todos los procedimientos estadísticos solicitados por la cátedra (ADF/KPSS/SARIMA/VAR/Granger) manteniendo tiempos de procesamiento razonables.

---

# Proyección para el Trabajo Final

En caso de requerirse un volumen superior de información (por ejemplo, más de 100.000 registros), el proyecto se encuentra diseñado para ampliar fácilmente el horizonte temporal.

Se prevé extender la descarga histórica hasta el año 2000 (o anterior si las fuentes lo permiten), reutilizando exactamente el mismo proceso de adquisición, limpieza y modelado.

De esta manera, el código desarrollado será completamente reutilizable sin necesidad de modificaciones importantes.

---

# Organización del Proyecto

```
Series_AMBA/

│
├── data/
│   ├── raw/
│   │   ├── smn/                              (descarga automática)
│   │   └── cammesa/
│   │       ├── demanda_reciente_api/          (descarga automática, ventana ~7 meses)
│   │       └── sintesis_mensual_manual/       (adquisición manual, ver Notas y Limitaciones)
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
│   ├── limpieza.py
│   ├── sarima.py
│   ├── var.py
│   └── utils.py
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

# Notas y Limitaciones de las Fuentes de Datos (importante)

Antes de escribir el código de descarga se verificaron los endpoints reales
de CAMMESA y del SMN (no se asumió que "publican un CSV histórico horario"
sólo porque lo mencionen en su sitio). El resultado cambia parcialmente el
plan original:

## SMN (temperatura) — 100% automatizable

El SMN publica un archivo de texto por día (`datohorarioYYYYMMDD.txt`) con
observaciones horarias de todas las estaciones del país, con profundidad
histórica confiable desde aproximadamente **enero de 2018** hasta el día
anterior a la fecha de ejecución — es decir, el SMN por sí solo permitiría
un rango mucho más amplio que el de CAMMESA. Pero como el rango realmente
utilizable del proyecto queda acotado por CAMMESA (2023-01-01 – 2026-06-30,
ver más abajo), `01_descarga_datos.ipynb` descarga la temperatura acotada a
ese mismo período, no el histórico completo desde 2018, para que las tres
series terminen con la misma cantidad de registros.

## CAMMESA (demanda y generación) — NO tiene un histórico horario descargable por script

- La API pública de CAMMESA (`api.cammesa.com/demanda-svc`) sólo expone una
  **ventana móvil reciente** (aproximadamente los últimos 7 meses) de
  demanda a intervalos de 5 minutos. Pedir una fecha de 2019, 2023 o incluso
  hace 8 meses devuelve una lista vacía, no un error.
- Los datasets horarios/mensuales de `datos.gob.ar` para CAMMESA son
  **mensuales por agente/central** (MWh por mes), no series horarias de
  sistema.
- Las páginas del portal de CAMMESA que sí muestran históricos horarios por
  mes ("Demanda Horaria por Tipo", "Síntesis Mensual") tienen botones de
  descarga implementados en JavaScript sin URL de archivo real detrás
  (`href="#"`); no son automatizables con `requests` sin simular un
  navegador completo, lo cual excede el alcance de este notebook.

**Consecuencia práctica:** `01_descarga_datos.ipynb` automatiza la ventana
reciente de demanda vía API (útil para actualizar el proyecto en el
tiempo, y como demostración del mecanismo). El histórico horario real sí
existe, pero por otra vía a la estimada originalmente: el reporte
autogenerado **"Reportes Actuales e Históricos"** del portal (no "Síntesis
Mensual"), que expone dos descargas `.xlsx` con URL de archivo real:

- **"Demanda Horaria por Provincia"** — MWh por hora, una columna por cada
  una de las 24 provincias + columna `TOTAL`.
- **"Oferta Total Horaria"** — MWh por hora, una columna por cada una de 12
  fuentes/tecnologías (agrupadas en Nuclear / Renovable / Térmica /
  Importación) + columna `TOTAL [MWh]`.

Ambos archivos, descargados manualmente y guardados en
`data/raw/cammesa/sintesis_mensual_manual/`, cubren **2023-01-01 a
2026-06-30** (30.648 horas), verificado leyendo la primera y última fila de
datos — no sólo el nombre del archivo. Esto acota el período utilizable del
proyecto a esas fechas (ver "Alcance del TP Inicial" arriba, ya corregido).
Los archivos se llaman `Demanda Horaria por Provincia 01012023_30062026.xlsx`
y `Oferta Total Horaria 01012023_30062026.xlsx` — renombrados por el usuario
para que la fecha del nombre coincida con el período real y común de ambos
(los nombres originales del reporte traían fechas levemente distintas entre
sí, `23012023_26062026` y `01012023_01062026`, que no reflejaban con
precisión el contenido real de cada archivo). La columna `HORA` usa la
convención 1-24 de CAMMESA (paso 1 = 00:00–01:00 … paso 24 = 23:00–00:00), a
convertir en `02_limpieza.ipynb`. Como proxy de "demanda del AMBA" se usará
la columna `BUENOS AIRES` (demanda de toda la provincia, no sólo del
conurbano/CABA — la misma limitación de fuente ya señalada arriba).

`01_descarga_datos.ipynb` valida automáticamente la presencia de estos dos
archivos por nombre (sección 4.2) e ignora el resto de lo que haya en esa
carpeta (viejos intentos con datos.gob.ar o con "Síntesis Mensual").

## Nota para el TP Final: ¿"transponer" provincia/tecnología para sumar registros?

Idea evaluada (no implementada): pasar de formato ancho (una columna por
provincia/tecnología) a formato largo (una fila por hora-provincia u
hora-tecnología) infla la cantidad de _filas_ (30.648 × 24 ≈ 735.000 para
demanda), pero **no agrega ningún instante de tiempo nuevo** — siguen siendo
los mismos ~30.648 momentos repetidos. Para SARIMA/VAR/pruebas de raíz
unitaria, lo que importa es la longitud real de la serie temporal, no el
número de filas de una tabla. Si la cátedra pide "≥100.000 registros" en
el sentido de longitud temporal, la única vía legítima es extender el
rango de fechas (ver si CAMMESA permite el mismo reporte para años
anteriores a 2023), no reformatear las columnas existentes. El detalle por
provincia/tecnología sí es valioso, pero como **variables adicionales de un
VAR más rico** — no como filas extra. Ver la sección 4.3 de
`01_descarga_datos.ipynb` para el detalle completo de esta evaluación.

---

# Filosofía del Proyecto

El proyecto seguirá una metodología reproducible de Ciencia de Datos.

Los datos originales nunca serán modificados.

Se mantendrán tres niveles de almacenamiento:

## data/raw

Contendrá exclusivamente los archivos descargados desde las fuentes oficiales.

Nunca serán modificados.

---

## data/interim

Contendrá los datos luego de los procesos de limpieza iniciales.

Ejemplos:

- Conversión de fechas.
- Corrección de formatos.
- Eliminación de duplicados.
- Tratamiento de valores faltantes.

---

## data/processed

Contendrá las series listas para el modelado estadístico.

Todos los notebooks posteriores utilizarán exclusivamente esta carpeta.

---

# Productos esperados

Al finalizar la primera etapa del proyecto se dispondrá de:

- demanda.csv
- generacion.csv
- temperatura.csv

y además un archivo integrado:

- series_amba.csv

con las tres variables perfectamente alineadas temporalmente.

---

# Notebooks del Proyecto

## Notebook 01

Inicialización del proyecto y descarga automática de datos.

---

## Notebook 02

Limpieza y preparación de las series.

---

## Notebook 03

Análisis exploratorio (EDA).

---

## Notebook 04

Estacionariedad y pruebas de raíces unitarias.

---

## Notebook 05

Modelado SARIMA.

---

## Notebook 06

Modelado VAR, causalidad e impulso-respuesta.

---

## Notebook 07

Pronósticos y comparación de modelos.

---

# Objetivo Final

Obtener un flujo de trabajo completamente reproducible que permita descargar, limpiar, analizar, modelar y pronosticar las tres series temporales mediante metodologías econométricas modernas, facilitando tanto la realización del Trabajo Práctico inicial como su posterior ampliación para el Trabajo Final de la asignatura.

---

# Próximo Paso

Desarrollar el Notebook **01_descarga_datos.ipynb**, encargado de:

- Crear automáticamente toda la estructura del proyecto.
- Verificar el entorno de trabajo.
- Descargar las series oficiales desde CAMMESA y el SMN.
- Validar los archivos descargados.
- Generar un resumen de calidad de los datos.
- Dejar preparado el proyecto para las etapas de limpieza y modelado.
