# 🦙 Manual Paso a Paso de Operación — Plataforma Mamá Qocha (v2.4)

> **Diseñado para lectura rápida y operación sin errores.**  
> No necesitas memorizar nada: busca el apartado que vas a usar, sigue los pasos numerados **uno por uno** y apóyate en los colores del semáforo.

---

## 🗺️ Índice Rápido (Haz clic para ir directo)

1. [🚀 Antes de Empezar: Cómo Abrir la Plataforma](#-1-antes-de-empezar-cómo-abrir-la-plataforma)
2. [🧭 Conoce la Pantalla: Barra Lateral y Cabecera](#-2-conoce-la-pantalla-barra-lateral-y-cabecera)
3. [🚦 Cómo Leer el Semáforo y Todos los KPI](#-3-cómo-leer-el-semáforo-y-todos-los-kpi)
4. [📥 Apartado 1: Recepción de Compras](#-4-apartado-1-recepción-de-compras)
5. [🍳 Apartado 2: Salidas a Cocina (FEFO)](#-5-apartado-2-salidas-a-cocina-fefo)
6. [📱 Área Especial: Terminal KDS de Cocina (Pantalla Táctil / Offline)](#-6-área-especial-terminal-kds-de-cocina-pantalla-táctil--offline)
7. [🚚 Apartado 3: Traspasos entre Locales](#-7-apartado-3-traspasos-entre-locales)
8. [🗑️ Apartado 4: Control de Mermas (Bajas)](#-8-apartado-4-control-de-mermas-bajas)
9. [🔍 Apartado 5: Trazabilidad y Auditoría](#-9-apartado-5-trazabilidad-y-auditoría)
10. [🖨️ Apartado 6: Reportes SEREMI (PDF)](#-10-apartado-6-reportes-seremi-pdf)
11. [⚙️ Apartado 7: Maestros (Catálogos y Personal)](#-11-apartado-7-maestros-catálogos-y-personal)
12. [✅ Rutina Diaria en 30 Segundos y Solución de Problemas](#-12-rutina-diaria-en-30-segundos-y-solución-de-problemas)

---

## 🚀 1. Antes de Empezar: Cómo Abrir la Plataforma

La plataforma funciona en la nube con **dos pantallas** conectadas entre sí:
* **Panel Central (Administración y Control):** https://mamaqocha.streamlit.app *(para oficina, bodega, gerencia o caja)*.
* **Terminal KDS de Cocina (Pantalla Táctil):** https://qochacocina.onrender.com/cocina/ *(para tablet o computador dentro de la cocina)*.

### Pasos para entrar en producción (Nube)
1. Abre tu navegador (Chrome, Edge o Safari en tablet/PC).
2. Para administración, bodega, reportes o traslados, entra a: **https://mamaqocha.streamlit.app**
3. Para operación rápida en cocina, entra a: **https://qochacocina.onrender.com/cocina/** *(o desde el Panel Central, entra a **`🍳 Salidas a Cocina (FEFO)`** y presiona **`🚀 Abrir Terminal KDS`**)*.

> **Uso local / respaldo sin servidor en nube:** Si en algún momento necesitas correr el sistema localmente desde este computador, haz doble clic en `iniciar_completo.bat` (abrirá el Panel en `http://localhost:8501` y la Cocina en `http://localhost:8000/cocina/`).

> **Regla de oro:** Si en algún momento sientes que los números no se actualizaron después de usar la tablet de cocina, ve a la barra izquierda del Panel Central y presiona **`🔄 Sincronizar Datos en Vivo`**.

---

## 🧭 2. Conoce la Pantalla: Barra Lateral y Cabecera

Antes de tocar cualquier módulo, revisa **siempre** dónde estás parado mirando la barra izquierda y la cabecera azul superior.

### A. Barra Lateral Izquierda (Tu ubicación y firma)
1. **🏢 Simulación de Local (`Local Activo en Pantalla`):**
   * Presiona **`🌐 Todos (5)`** si eres Administrador y quieres ver la cadena completa.
   * Presiona **`📍 [Nombre del Local]`** si trabajas en una sucursal específica (por ejemplo, Providencia o Las Condes).
   * *¿Qué cambia?* Cuando eliges un local específico, todos los formularios se bloquean automáticamente a ese local para evitar que cargues datos en la sucursal equivocada.
2. **👤 Operador en Sesión:**
   * Selecciona **tu nombre** en la lista desplegable.
   * El sistema usará tu nombre como firma por defecto en recepciones, cocina, traslados y mermas.
3. **📦 Stock del Local (4 mini-números rápidos):**
   * **Lotes:** Cantidad de lotes físicos con stock positivo.
   * **Total (kg):** Kilos totales disponibles hoy.
   * **Valor Total:** Dinero invertido en ese inventario (en miles `k` o millones `M`).
   * **En Riesgo:** Dinero que está por vencer pronto o ya vencido.
4. **🔄 Sincronizar Datos en Vivo:** Botón para limpiar la memoria temporal y traer los datos más recientes desde la nube (PostgreSQL Neon).
5. **📄 Descargar Manual (PDF):** Descarga una copia de respaldo en PDF si existe en la carpeta del sistema.

### B. Cabecera Superior (Hero Banner y HUD)
En la parte alta verás 3 indicadores instantáneos:
* **Vista Operativa:** Muestra si estás viendo `🌐 Consolidado (5 Locales)` o `📍 [Tu Local]`.
* **Stock Físico:** Muestra los kilos totales y cantidad de lotes activos.
* **Alerta FEFO:**
  * `✅ 0 lotes críticos`: Todo está bajo control.
  * `🚨 X lotes críticos`: Hay productos vencidos o por vencer en ≤ 7 días. ¡Atención!

Debajo de la cabecera está la **barra de 8 botones (pastillas)** para cambiar de apartado:

| Botón en Pantalla | Para qué sirve |
| :--- | :--- |
| **`🚦 Semáforo y Costos en Riesgo`** | Ver alertas de vencimiento, dinero en riesgo y qué platos cocinar hoy. |
| **`📥 Recepción de Compras`** | Ingresar mercadería nueva que llega del proveedor (con factura/guía y temperatura). |
| **`🍳 Salidas a Cocina (FEFO)`** | Descontar ingredientes al cocinar, abrir la Terminal KDS o revisar la bitácora offline. |
| **`🚚 Traspasos entre Locales`** | Enviar insumos de una sucursal a otra (ida y retorno) antes de que venzan. |
| **`🗑️ Control de Mermas (Bajas)`** | Dar de baja productos vencidos o dañados y registrar por qué se perdieron. |
| **`🔍 Trazabilidad y Auditoría`** | Rastrear la historia completa de un lote o ver los últimos movimientos. |
| **`🖨️ Reportes SEREMI (PDF)`** | Descargar actas individuales o libros completos en PDF para inspección sanitaria. |
| **`⚙️ Maestros (Catálogos)`** | Crear o editar proveedores, materias primas, personal/PIN y consultar recetas. |

---

## 🚦 3. Cómo Leer el Semáforo y Todos los KPI

Entra al primer apartado: **`🚦 Semáforo y Costos en Riesgo`**. Aquí ves la salud del negocio en un vistazo.

### A. ¿Qué significa cada color del Semáforo?

El sistema usa lógica **FEFO** (*First Expired, First Out*: **lo que vence primero, sale primero**).

| Color | Nombre en Sistema | Días para Vencer | ¿Qué debes hacer? |
| :---: | :--- | :--- | :--- |
| 🔴 | **Vencido** | Menos de `0` días (ya caducó) | **PROHIBIDO cocinar.** Ve a **Mermas** y dalo de baja de inmediato. |
| 🟠 | **Crítico (≤ 7 d)** | De `0` a `7` días | **URGENTE.** Úsalo primero en cocina, promuévelo como "Plato del Día" o trasládalo a otro local. |
| 🟡 | **Preventivo (8-30 d)** | De `8` a `30` días | **OBSERVACIÓN.** Rotación normal siguiendo el orden de vencimiento. |
| 🟢 | **Óptimo (> 30 d)** | Más de `30` días | **SEGURO.** Stock sano con vida útil holgada. |

> **Ojo en Traspasos entre Locales:** En las tablas *Top 7* de traspasos verás una escala más fina para decidir fletes urgentes: `🔴 Vencido (<0d)`, `🔴 Crítico (≤2d)`, `🟠 Urgente (3-5d)`, `🟡 Preventivo (6-10d)` y `🟢 Normal (>10d)`.

---

### B. Cómo leer los KPI Financieros (Tarjeta Principal)

1. **💼 Valorización del Inventario Activo (`$ CLP`):**
   * Es todo el dinero que hoy está invertido en bodega/cámara según el costo real de compra.
   * *Ejemplo:* Si dice `$12.500.000 CLP`, tienes esa plata convertida en comida en tus cámaras.
2. **⚠️ Capital en Riesgo de Vencimiento (`$ CLP`):**
   * Es la suma de todo el dinero en lotes **🔴 Vencidos + 🟠 Críticos (≤ 7 días)**.
   * Debajo verás una insignia roja con el **porcentaje (`%`)**.
   * *Lectura rápida:* Mientras más cercano a `0%`, mejor. Si sube de `15% - 20%`, hay riesgo serio de pérdida.
3. **Barra de Distribución del Capital:**
   * Una barra horizontal dividida en rojo, naranja, amarillo y verde. Te muestra qué porcentaje de tu dinero está en cada color del semáforo.

---

### C. Cómo leer las 4 Tarjetas del Semáforo y los 4 KPI Ejecutivos

#### Fila 1: Las 4 Tarjetas del Semáforo
Cada tarjeta muestra **cuántos lotes** tienes en ese color y **cuánto dinero (`$`)** representan.

#### Fila 2: Los 4 KPI de Control Ejecutivo
| KPI | Qué mide | Cómo interpretarlo |
| :--- | :--- | :--- |
| **💵 Potencial Facturación Carta** | `Valor del inventario × 3.2` | Cuánto dinero debería vender el restaurante al transformar todo el stock actual en platos de la carta. |
| **🛡️ Inocuidad HACCP (≤ 4°C)** | `% de lotes que entraron a ≤ 4.0 °C` | Mide la seguridad de cadena de frío al recibir compras. **Meta ideal: `100%`**. Si baja, revisa qué proveedor entregó caliente. |
| **⏳ Vida Útil Ponderada (días)** | Promedio de días de vida útil según el peso en dinero de cada lote | Si es bajo (ej. `< 10 días`), tienes mucho capital en productos que vencen pronto. |
| **🍽️ Capacidad de Comandas (platos)** | `Total kg activos ÷ 0.220 kg` | Estimación aproximada de cuántos platos puedes servir con los kilos actuales en bodega. |

---

### D. Secciones de Acción debajo de los KPI (En el mismo apartado 1)

1. **🍲 Top Preparaciones Recomendadas para la Carta del Día (Rescate de Insumos):**
   * Cruza tus insumos que vencen en `0 a 7 días` con las recetas de la carta.
   * Te muestra las **3 mejores tarjetas** con:
     * **Porciones Sugeridas:** Cuántos platos alcanzas a hacer antes de que se pierda el insumo.
     * **Venta Recuperable (`+$ CLP`):** Cuánto dinero rescatas si vendes esos platos hoy.
     * **Insumo Crítico** y **Sucursales**.
   * *Tip:* Haz clic en **`🔍 Ver todas las recetas recomendadas para rescate de stock`** para ver la lista completa.
2. **Gráficos Centrales:**
   * **🥧 Distribución del Semáforo (Dona):** Proporción visual de lotes por color. Pasa el mouse encima para ver el `%`.
   * **🥩 Stock Total por Producto (kg):** Qué materia prima tienes en mayor volumen.
   * **🎯 Matriz de Dispersión (Riesgo Temporal vs Capital):** Cada burbuja es un lote. **Mira siempre la esquina superior izquierda** (arriba y a la izquierda de la línea roja `≤ 7 días`): ahí están los lotes más caros que están a punto de vencer.
3. **🏢 Exposición y Riesgo de Venta por Sucursal:**
   * Compara los 5 locales en barras apiladas.
   * En el recuadro derecho (**🎯 Diagnóstico Ejecutivo de Riesgo**) destaca cuál es la **Sucursal con Mayor Exposición** y muestra el ranking con bolita:
     * `🔴` = Más de `20%` del stock en riesgo.
     * `🟠` = Entre `0.1%` y `20%` en riesgo.
     * `🟢` = `0%` en riesgo.
4. **🚚 Oportunidades de Rebalanceo Logístico (solo visible en modo `🌐 Todos (5)`):**
   * Muestra tarjetas azules automáticas cuando un local tiene stock crítico (≤ 7 días) y otro local tiene `0 kg` de ese mismo producto. Te dice exactamente cuántos `kg` mover y desde dónde hacia dónde.
5. **📋 Detalle de Lotes en Stock (Tabla inferior):**
   * Usa las pastillas **`Filtrar por nivel de riesgo`** (`🌐 Todos`, `🔴 Vencido`, `🟠 Crítico`, `🟡 Preventivo`, `🟢 Óptimo`) o escribe en el buscador (producto, proveedor o código de lote) para encontrar cualquier lote exacto.

---

## 📥 4. Apartado 1: Recepción de Compras

Úsalo **cada vez que llegue mercadería de un proveedor**. Al guardar, el sistema crea el lote y suma el stock de inmediato.

### Paso a paso
1. En el menú superior, haz clic en **`📥 Recepción de Compras`**.
2. En la columna izquierda (**📄 1. Datos del Proveedor y Factura**):
   * Verifica el **Local receptor** (si estás en modo "Todos", elige el local en las pastillas; si ya elegiste local en la barra lateral, aparecerá fijo).
   * Selecciona el **Proveedor** en la lista.
   * Elige el **Tipo de documento**: `🧾 Factura`, `🚚 Guía` o `📄 Boleta`.
   * Escribe el **N° Documento** (obligatorio, ej. `FAC-2026-0045`).
   * Verifica **Fecha de emisión/compra** y **Fecha de recepción física** *(la recepción no puede ser anterior a la compra)*.
   * Verifica quién es el **Responsable que recibe en bodega/local**.
3. En la columna derecha (**🏷️ 2. Especificación de Materia Prima y Lote**):
   * Selecciona el **Producto recibido**.
   * Ingresa la **Cantidad recibida** (ej. `25.000`).
   * Ingresa el **Costo unitario ($)** por kg/unidad (importante para que los KPI financieros sean reales).
   * Escribe el **Lote del proveedor** tal como viene impreso en la etiqueta o caja (obligatorio).
   * Selecciona la **Fecha de vencimiento** de la etiqueta.
   * Mide con termómetro e ingresa la **Temp. Ingreso (°C)**:
     * ✅ **`0.0 °C` a `4.0 °C`:** Conforme (cadena de frío segura).
     * ⚠️ **`4.1 °C` a `5.0 °C`:** Sale advertencia amarilla (límite superior).
     * 🚨 **Más de `5.0 °C`:** Sale **ALERTA SANITARIA ROJA (HACCP)**. Revisa si debes rechazar o declarar deterioro.
   * Escribe observaciones si hubo algún detalle (ej. estado del sello al vacío).
4. Haz clic en el botón azul **`📥 Registrar Recepción e Incorporar al Stock`**.
5. **Verificación:** Aparecerá un recuadro verde (**🧾 Comprobante de Recepción de Lote**) y un botón para descargar **`🖨️ Descargar Acta de Recepción y Control HACCP (PDF)`**.

---

## 🍳 5. Apartado 2: Salidas a Cocina (FEFO)

Úsalo para descontar insumos cuando la cocina produce platos. Entra en **`🍳 Salidas a Cocina (FEFO)`**.

> **Primero revisa arriba:** Si estás en modo `🌐 Todos (5)`, selecciona en las pastillas en qué local está operando la cocina. Si ya fijaste el local en la barra izquierda, se selecciona solo.

Aquí tienes un botón destacado arriba (**`🚀 Abrir Terminal KDS`**) para abrir la pantalla táctil de cocina, y **3 sub-apartados**:

### Sub-apartado A: `📋 Producción por Recetas (Comanda / Turno)` *(Uso habitual)*
Sirve para descontar varios platos de una sola vez según su receta estándar (escandallo).
1. Elige el **Turno de Cocina / Servicio** (`☀️ Almuerzo`, `🌤️ Tarde`, `🌙 Cena` o `🎉 Evento`).
2. Selecciona el **Chef / Responsable**.
3. (Opcional) Escribe una referencia de comanda u observación.
4. En **Selecciona los platos a elaborar en este turno**, agrega o quita los platos preparados.
5. En **🔢 Cantidad de Porciones por Plato**, escribe cuántos platos se hicieron de cada receta.
6. Revisa la tabla **📊 Simulación de Consumo vs Stock Disponible en Sucursal**:
   * Si todo dice **`✅ Suficiente`**, puedes continuar.
   * Si algo dice **`❌ Faltan X kg`**, el botón de confirmar se bloqueará. Reduce las porciones o solicita un traspaso antes de continuar.
7. Haz clic en **`🍳 Confirmar y Descontar Producción por FEFO`**.
8. Revisa el resumen generado (platos, costo de insumos FEFO, margen bruto) y descarga si lo necesitas el **`🖨️ Descargar Acta de Manipulación y Producción en Cocina (PDF)`**.

### Sub-apartado B: `📦 Salida Manual por Lote Individual` *(Consumos puntuales)*
Úsalo para pruebas de sabor, calibración o salidas directas de un solo lote sin receta.
1. En **Selecciona el lote a utilizar (ordenado por FEFO)**, el sistema ya pone **primero los lotes que vencen antes**.
2. Escribe la **Cantidad a consumir** (no puede superar el máximo disponible).
3. Escribe la **Estación de cocina o partida** (ej. `Cevichería`, `Parrilla`) y elige el **Chef / Responsable**.
4. Mira la **Ficha rápida** a la derecha para confirmar que el lote sea `🔴 Urgente` o `🟢 Normal`.
5. Haz clic en **`🍳 Confirmar Salida a Cocina`**.

### Sub-apartado C: `🛰️ Bitácora Offline (Outbox)` *(Auditoría de la Terminal KDS)*
Aquí no tienes que ingresar datos; solo sirve para **verificar** que lo que cocinó la tablet (KDS) sin internet ya llegó a la nube:
* **Total Eventos Recibidos:** Cuántas operaciones envió la Terminal KDS.
* **Desfase Medio de Contingencia (s):** Cuántos segundos pasaron entre el clic en cocina y su llegada a la nube.
* **Integrados a PostgreSQL Neon:** Debe coincidir `X / X ✅`.
* En la tabla inferior ves el UUID único, sucursal, tipo de evento, hora exacta en cocina y hora de llegada a la nube.

---

## 📱 6. Área Especial: Terminal KDS de Cocina (Pantalla Táctil / Offline)

Esta es la pantalla rápida diseñada para tablets dentro de la cocina. Funciona **aunque se caiga el internet** porque guarda todo en el dispositivo (IndexedDB) y lo envía cuando vuelve la señal.

### Cómo entrar
* Directamente en el navegador de la tablet o PC de cocina: **https://qochacocina.onrender.com/cocina/**
* O desde el Panel Central (`https://mamaqocha.streamlit.app` → **`🍳 Salidas a Cocina (FEFO)`** → botón **`🚀 Abrir Terminal KDS`**).

### Guía rápida de la pantalla KDS
1. **Barra Superior (Configuración rápida):**
   * Elige el **Turno** (`Almuerzo`, `Cena`, `Mise en place`).
   * Elige el **👨‍🍳 Chef Turno**.
   * Elige el **Local** en la esquina derecha.
   * Revisa el **Semáforo de Red**:
     * 🟢 **`En Línea • Sincronizado`**: Conectado a la nube.
     * 🟠 **Offline**: Sin internet (puedes seguir cocinando sin parar).
     * 🔵 **Sincronizando**: Enviando eventos pendientes.
   * Botón **`Sincronizar (N)`**: Muestra cuántos eventos están esperando subir a la nube; presiónalo si quieres forzar el envío manual.
2. **Despachar platos (Panel Derecho + Izquierdo):**
   * Filtra por categoría (`Todas`, `Ceviches`, `Calientes`, `Entradas`, `Postres/Bebidas`).
   * **Toca las tarjetas de los platos** para sumarlos a la **📋 Comanda en Preparación** (panel izquierdo).
   * Cuando la comanda esté lista, presiona el botón rojo **`⚡ Despachar y Descontar FEFO`**.
   * El descuento ocurre en milisegundos aplicando FEFO automáticamente.
3. **Botones auxiliares en el Panel Izquierdo:**
   * **`⚠️ Reg. Merma`:** Selecciona el lote, cantidad, motivo, elige quién autoriza e ingresa su **PIN de 4 dígitos** → presiona **`Registrar Merma`**.
   * **`📥 Recepción Emergencia (Offline)`:** Aparece cuando hay caída de red o quiebre para ingresar mercadería de urgencia sin frenar la cocina. Completa producto, proveedor, cantidad (tiene botones rápidos `+5`, `+10`, `+20`), N° guía, código de lote (o botón `Auto`), vencimiento, temperatura, responsable y **PIN de 4 dígitos** → **`Ingresar y Desbloquear Stock`**.
   * **`🚚 Traspaso Local`:** Si estás sin internet, el sistema lo **bloquea a propósito** para evitar descuadres entre locales. Con internet, te recuerda hacerlo desde el Panel Central.
4. **Barra Inferior (`Patrón Outbox`):**
   * Haz clic en **`Ver Detalle de Cola Offline`** si quieres ver qué operaciones están pendientes de subir o presionar **`Sincronizar Lote Ahora`**.

---

## 🚚 7. Apartado 3: Traspasos entre Locales

Úsalo para mover insumos que están por vencer desde un local con sobrestock hacia otro local donde sí se venderán. Además permite aprovechar el **viaje de regreso (Retorno / Backhaul)** en el mismo flete.

Entra en **`🚚 Traspasos entre Locales`**.

### Paso A: Definir la Ruta
1. Elige el **Local de Origen (Emisor)** (si ya fijaste un local en la barra lateral, quedará fijo como Origen).
2. Elige el **Local de Destino (Receptor)**.

### Paso B: Cargar los Lotes (Flete de Ida y/o Retorno)
Verás dos tablas lado a lado con los **Top 7 Lotes en Riesgo FEFO**:
* **Izquierda (`🔴 Flete de Ida`):** Lo que sale del Origen hacia el Destino.
* **Derecha (`🔄 Retorno Oportuno`):** Lo que el camión puede traer de regreso desde el Destino hacia el Origen.

Para cargar lotes al manifiesto tienes **3 formas fáciles**:
* **Opción 1 (Varios a la vez):** Marca los cuadritos (checkbox) a la izquierda de las filas que quieras y presiona **`➕ Cargar (N)`** (o **`➕ Retorno (N)`**).
* **Opción 2 (Uno puntual):** Elige un lote en la lista desplegable de abajo y presiona **`➕ Cargar`** (o **`➕ Retorno`**).
* **Opción 3 (Todos los críticos):** Presiona **`⚡ Cargar 7`** para subir los 7 lotes críticos de golpe.

### Paso C: Ajustar Cantidades y Emitir Guías
Baja a **📋 Vista Previa de las Guías de Despacho (Manifiesto de Carga)**:
1. En la columna **`A Enviar (kg)`** (o **`A Retornar (kg)`**), haz doble clic si deseas enviar solo una parte del lote en vez de todo el lote. *(Si quieres quitar una fila, selecciónala en la tabla y borra o usa **`🗑️ Vaciar Guía`**).*
2. Revisa el **Resumen Logístico del Viaje Redondo**:
   * **Carga Total Movilizada (kg)**
   * **Capital Total Rescatado ($ CLP)**
   * **Aprovechamiento Flete:** `⚖️ 100% (Ida + Retorno Completo)` si cargaste ambos sentidos, o `50% (Solo un sentido)`.
3. Selecciona al **Responsable Origen** (quien despacha) y al **Responsable Destino** (quien recibe).
4. Verifica el texto de **Protocolo y Condiciones de Transporte** (cadena de frío).
5. Presiona el botón azul **`🚚 Confirmar y Emitir...`**.
6. Aparecerá el voucher de confirmación y arriba el botón **`🖨️ Descargar Guía de Despacho / Traslado (PDF)`**.

> **¿Solo necesitas mover 1 lote puntual que no está en el Top 7?**  
> Abre la caja desplegable **`➕ Registro de Traslado Individual Manual (1 solo lote)`** debajo del manifiesto, elige el lote, cantidad, referencia, responsables y presiona **`🚚 Ejecutar Traslado Individual`**.

*Tip:* Al final de la página puedes activar el interruptor **`Ver últimos 20 traslados registrados`** para revisar el historial.

---

## 🗑️ 8. Apartado 4: Control de Mermas (Bajas)

Úsalo para dar de baja **todo insumo vencido, dañado o perdido**. Entra en **`🗑️ Control de Mermas (Bajas)`**.

### A. Cómo leer los 3 KPI Superiores
* **Pérdida Monetaria en Mermas (`$ CLP`):** Dinero perdido por bajas acumuladas (impacto directo al costo de ventas).
* **Volumen Descartado (`kg`):** Total de kilos dados de baja.
* **Eventos Declarados (`actas`):** Cantidad de actas de merma registradas.

### B. Paso a paso para Declarar una Baja Consolidada
1. Si estás en modo `🌐 Todos (5)`, selecciona arriba el **Local donde ocurrió la merma**.
2. En la **🔴 Grilla de Selección Rápida de Lotes para Baja (FEFO)**:
   * Usa los filtros rápidos de la derecha: **`Todos`**, **`Vencidos (<0d)`** o **`Críticos (≤2d)`**.
   * Carga los lotes al acta usando cualquiera de estas opciones:
     * Marca filas con el checkbox y presiona **`➕ Cargar Marcas (N)`**.
     * Selecciona un lote puntual en la lista y presiona **`➕ Cargar`**.
     * Presiona **`⚡ Vencidos (N)`** para cargar **todos los lotes ya vencidos** en un clic.
     * Presiona **`⚡ Top 7`** para cargar los 7 más críticos.
3. En **📝 Vista Previa: Acta de Baja Consolidada por Merma**:
   * Edita la columna **`A Descartar (kg)`** si solo se perdió una parte del lote (o déjalo completo si es baja total).
   * Revisa las métricas: `Lotes en Acta`, `Total Volumen a Descartar` y `Pérdida Financiera Estimada`.
4. **Tipificación Obligatoria de Causa Raíz** (elige **1** de las 4 pastillas oficiales):
   * `❄️ Ruptura de frío` (*Ruptura de cadena de frío en cocina*)
   * `🔴 Vencimiento FEFO` (*Vencimiento de fecha límite FEFO*)
   * `⚠️ Deterioro recepción` (*Deterioro organoléptico en recepción*)
   * `🔪 Error porcionado` (*Manipulación / Error de porcionado*)
5. Selecciona quién **Autoriza / Declara** la baja.
6. Escribe la **Justificación sanitaria / Causa Raíz detallada** *(obligatorio; si lo dejas vacío el sistema no te dejará confirmar)*.
7. Presiona **`🗑️ Confirmar y Procesar Baja Consolidada`**.
8. Descarga el respaldo oficial en **`🖨️ Descargar Acta Oficial de Baja por Merma (PDF)`**.

### C. Analítica e Historial de Mermas (Parte inferior)
* **📊 Reporte Estadístico de Causas de Merma:** Muestra un gráfico de dona por costo (`$ CLP`), una tabla con el `% Impacto` por cada causa y un botón **`📥 Exportar Resumen Estadístico (CSV para Informe)`**.
* **📋 Libro de Actas de Merma y Desecho:** Activa el interruptor **`Ver últimas 50 actas de merma registradas`** para auditar actas pasadas.

---

## 🔍 9. Apartado 5: Trazabilidad y Auditoría

Úsalo cuando necesites responder: *"¿De qué proveedor vino este producto, a qué temperatura llegó, a qué locales se movió y quién lo manipuló?"*. Entra en **`🔍 Trazabilidad y Auditoría`**.

Tiene **2 sub-apartados**:

### Sub-apartado A: `📦 Ficha de Trazabilidad por Lote`
1. En la lista desplegable, busca y selecciona el **lote que quieres auditar**.
2. Arriba verás su nombre, código de lote de proveedor y su **etiqueta de semáforo** (`🔴 VENCIDO`, `🟠 CRÍTICO`, `🟡 PREVENTIVO` o `🟢 ÓPTIMO`).
3. Presiona **`🖨️ Descargar Expediente Completo SEREMI — Lote #X (PDF)`** si necesitas el informe oficial de ese lote.
4. Lee la **🧭 Línea de Vida del Lote (3 tarjetas)**:
   * **1. 🏢 Origen / Compra:** Proveedor, RUT, tipo y número de documento, fecha de compra.
   * **2. 📥 Recepción Física:** Local que lo recibió, quién lo recibió, fecha, volumen inicial, costo unitario y temperatura de ingreso HACCP.
   * **3. ⏳ Estado Caducidad:** Fecha de vencimiento, días restantes, estado y observaciones.
5. Abajo revisa las dos tablas:
   * **📊 Stock Actual por Sucursal:** Cuánto queda hoy de ese lote en cada local (si dice que no tiene existencias, ya se consumió al 100%).
   * **🔄 Historial de Movimientos del Lote:** Cada salida a cocina, traslado o merma con fecha, cantidad, quien despachó y quien recibió.

### Sub-apartado B: `📋 Registro Global de Movimientos`
* Muestra la bitácora cronológica de las **últimas 50 operaciones** (traslados, salidas a cocina, mermas) filtrada por el local que tengas elegido en la barra lateral.

---

## 🖨️ 10. Apartado 6: Reportes SEREMI (PDF)

Centro oficial para fiscalizaciones sanitarias y auditorías internas. Entra en **`🖨️ Reportes SEREMI (PDF)`**.

### Paso a paso para emitir documentos
1. Elige el **Tipo de Documento / Auditoría SEREMI**:
   * `🗑️ Actas de Merma (Crítico)`
   * `🍳 Operaciones Cocina (FEFO)`
   * `🚚 Guías de Traslado`
   * `📥 Recepciones (HACCP)`
   * `📦 Expediente por Lote`
2. Define la **Sucursal** (`🌐 Todas` o una específica, si no está fijada en la barra lateral) y el rango de fechas (**Desde** y **Hasta**).
3. *(Si elegiste `📦 Expediente por Lote`)*: Solo elige el lote y presiona **`🖨️ Descargar Expediente Completo SEREMI — Lote #X (PDF)`**.
4. *(Para los otros 4 tipos)*:
   * (Opcional) Escribe en **`🔎 Búsqueda rápida`** para filtrar por folio, manipulador, proveedor, producto, causa o factura.
   * Revisa los 3 KPI del período (`Documentos / Folios`, `Total Lotes`, `Volumen Total`).
   * **Para imprimir todo el período junto:** Presiona **`📚 Descargar Libro Consolidado del Período (PDF)`**.
   * **Para imprimir 1 documento puntual:** Selecciona el folio en **`Selecciona el folio a imprimir en PDF`**, revisa su **👁️ Vista previa de trazabilidad** y presiona **`🖨️ Imprimir [Documento] #X (PDF)`**.

---

## ⚙️ 11. Apartado 7: Maestros (Catálogos y Personal)

Úsalo para mantener al día la información base del sistema. Entra en **`⚙️ Maestros (Catálogos)`**.

### Sub-apartado A: `🏢 Catálogo de Proveedores`
* **Ver:** Tabla izquierda con todos los proveedores y su estado `Activo`.
* **Crear:** A la derecha elige **`➕ Registrar Nuevo`**, llena Nombre (obligatorio), RUT, Teléfono, Correo, Dirección, deja marcado `Proveedor Habilitado (Activo)` y presiona **`💾 Guardar Proveedor`**.
* **Editar o Desactivar:** Elige **`✏️ Modificar Existente`**, selecciona el proveedor, cambia los datos (o desmarca `Activo` para ocultarlo de las compras) y presiona **`🔄 Actualizar Proveedor`**.

### Sub-apartado B: `🥩 Catálogo de Materias Primas`
* **Crear:** Elige **`➕ Registrar Nuevo`**, escribe el **Nombre**, elige la **Unidad de Medida** (`kg`, `g`, `l`, `ml`, `unidad`), agrega descripción, marca `Activa` y presiona **`💾 Guardar Producto`**.
* **Editar:** Elige **`✏️ Modificar Existente`**, selecciona el insumo, actualiza y presiona **`🔄 Actualizar Producto`**.

### Sub-apartado C: `🍽️ Fichas Técnicas de Recetas` *(Solo lectura / consulta)*
* Muestra 3 KPI rápidos: **Recetas Estandarizadas**, **Categorías de Menú** y **Ticket Promedio Carta (`$ CLP`)**.
* La tabla principal muestra el precio de venta, tiempo de preparación y el **Escandallo** (ingredientes por porción).
* Abre **`🔍 Ver Detalle de Gramajes por Plato`** para ver el gramaje exacto (`kg`) de cada ingrediente por receta.

### Sub-apartado D: `👥 Personal y Usuarios (Trazabilidad)`
Sirve para dar de alta a manipuladores, chefs, bodegueros y administradores, y asignarles su **PIN táctil de 4 dígitos** (usado en la Terminal KDS para autorizar mermas y recepciones de emergencia).
* **Crear:** Elige **`➕ Registrar Nuevo Personal`**, llena:
  1. **Nombre y Apellido** y **Nombre de usuario (Login)** *(en minúsculas, sin espacios)*.
  2. **Rol operativo:** `jefe_cocina`, `cocinero`, `bodeguero`, `administrador`, `cajero_garzon` u `operador`.
  3. **Local asignado:** Elige una sucursal o `🌐 Todos (Corporativo)`.
  4. **PIN Táctil KDS (4 dígitos):** Debe tener exactamente **4 números** (ej. `1234`).
  5. Marca `Usuario Activo` y presiona **`💾 Guardar Personal`**.
* **Editar o Resetear PIN:** Elige **`✏️ Modificar Personal / PIN`**, selecciona a la persona, cambia su rol, local, nuevo PIN de 4 dígitos o estado Activo y presiona **`🔄 Actualizar Datos`**.

---

## ✅ 12. Rutina Diaria en 30 Segundos y Solución de Problemas

### Checklist Diario por Horario
1. **Al abrir el local (Mañana):**
   * Elige tu local y tu nombre en la barra izquierda.
   * Mira **`🚦 Semáforo y Costos en Riesgo`**: si hay lotes **🔴 Vencidos**, retíralos de cámara y decláralos en **`🗑️ Mermas`**.
   * Mira los lotes **🟠 Críticos (≤ 7 d)** y las **🍲 Preparaciones Recomendadas**: avisa al Chef qué platos empujar hoy.
2. **Al recibir camiones/proveedores:**
   * Registra todo de inmediato en **`📥 Recepción de Compras`** midiendo la **temperatura (`≤ 4°C`)**.
3. **Durante el servicio (Almuerzo / Cena):**
   * Cocina despacha platos en la **Terminal KDS (`https://qochacocina.onrender.com/cocina/`)** o en **`🍳 Salidas a Cocina (FEFO)`**.
4. **Si sobra mucho insumo crítico en un local:**
   * Coordina un envío en **`🚚 Traspasos entre Locales`** (idealmente aprovechando ida y retorno).
5. **Al cerrar o ante inspección:**
   * Presiona **`🔄 Sincronizar Datos en Vivo`** y descarga lo que necesites desde **`🖨️ Reportes SEREMI (PDF)`**.

### ¿Qué hago si...? (Guía de Rescate Rápido)

| Situación | Solución paso a paso |
| :--- | :--- |
| **"El botón de Confirmar Producción en Cocina está bloqueado / gris"** | Algún ingrediente aparece en `❌ Faltan X kg`. Reduce las porciones, registra la factura pendiente en **Recepción**, o pide stock desde **Traspasos**. |
| **"Se cortó el internet en la cocina"** | No te detengas. Sigue despachando platos, mermas y recepciones de emergencia en la **Terminal KDS (`https://qochacocina.onrender.com/cocina/`)**. Cuando vuelva internet, los datos suben solos (o presiona `Sincronizar`). |
| **"La Terminal KDS no me deja hacer un Traspaso"** | Es normal: los traspasos entre locales requieren internet para no descuadrar dos bodegas a la vez. Hazlo desde el **Panel Central (`https://mamaqocha.streamlit.app`)** cuando haya señal. |
| **"Hice una operación y no la veo reflejada en las tablas"** | Haz clic en **`🔄 Sincronizar Datos en Vivo`** en la barra izquierda. |
| **"La Terminal KDS me pide un PIN y no me acuerdo"** | Pide a un Administrador que entre a **`⚙️ Maestros` → `👥 Personal y Usuarios`** → **`✏️ Modificar Personal / PIN`** para ver o cambiar tu PIN de 4 dígitos. |
| **"No me deja confirmar una Merma"** | Revisa dos cosas: 1) Que hayas elegido una de las 4 pastillas de **Causa Raíz**, y 2) Que hayas escrito texto en **Justificación sanitaria / Causa Raíz detallada**. |
| **"La temperatura al recibir marca más de 5.0 °C"** | El producto rompió la cadena de frío (Alerta HACCP). Evalúa rechazo con el proveedor o deja registro en observaciones / merma por deterioro en recepción. |
