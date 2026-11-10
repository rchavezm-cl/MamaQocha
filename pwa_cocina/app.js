/**
 * ==============================================================================
 * MAMÁ QOCHA - CONTROLADOR TERMINAL DE COCINA PWA (LOCAL-FIRST)
 * Archivo: pwa_cocina/app.js
 * Descripción:
 *   - Manejo de almacenamiento local persistente con Dexie.js (IndexedDB).
 *   - Lógica de deducción FEFO en memoria local (< 5 ms).
 *   - Patrón Outbox: encolado inmutable de eventos con UUIDs y sincronización batch.
 *   - Detección de conectividad y semáforo visual de contingencia.
 * ==============================================================================
 */

// 1. INICIALIZACIÓN DE BASE DE DATOS LOCAL EN EL NAVEGADOR (INDEXEDDB)
const dbLocal = new Dexie('MamaQocha_KDS_DB');

dbLocal.version(1).stores({
  config: 'clave',
  recetas: 'id_receta, categoria, nombre',
  stock_lotes: 'id_lote, id_producto, fecha_vencimiento',
  outbox_pendientes: 'id_evento, tipo_evento, fecha_local, estado',
  historial_sync: 'id_evento, fecha_local, fecha_sync'
});

// 2. ESTADO GLOBAL DE LA APLICACIÓN
const state = {
  idLocal: 1,
  nombreLocal: 'Cargando...',
  turno: 'Almuerzo',
  comandaActiva: {},       // { id_receta: cantidad }
  recetasList: [],
  categoriaActiva: 'TODAS',
  simulacionOfflineForzada: false,
  isSyncing: false
};

// 3. REGISTRO DEL SERVICE WORKER (CERO INSTALACIÓN / APERTURA OFFLINE)
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/cocina/sw.js')
      .then(reg => console.log('[PWA] Service Worker registrado:', reg.scope))
      .catch(err => console.warn('[PWA] Fallo registro SW:', err));
  });
}

// ==============================================================================
// OBJETO CONTROLADOR DE LA APLICACIÓN (app)
// ==============================================================================
const app = {
  async init() {
    // Detectar id_local de la URL (?local=X) o de config local
    const urlParams = new URLSearchParams(window.location.search);
    const paramLocal = urlParams.get('local');
    if (paramLocal) {
      state.idLocal = parseInt(paramLocal, 10);
      document.getElementById('sel-local').value = state.idLocal;
    } else {
      const cfgLocal = await dbLocal.config.get('id_local');
      if (cfgLocal) {
        state.idLocal = cfgLocal.valor;
        document.getElementById('sel-local').value = state.idLocal;
      }
    }

    // Escuchar eventos de red del navegador
    window.addEventListener('online', () => this.evaluarConectividad());
    window.addEventListener('offline', () => this.evaluarConectividad());

    // Cargar turno guardado si existe
    const selTurno = document.getElementById('sel-turno');
    selTurno.addEventListener('change', (e) => state.turno = e.target.value);

    // Cargar datos (Bootstrap si hay red, o caché IndexedDB si offline)
    await this.cargarBootstrap(state.idLocal);
    await this.actualizarContadorOutbox();
    this.evaluarConectividad();
  },

  // ----------------------------------------------------------------------------
  // CARGA DE DATOS: SNAPSHOT INICIAL O RESTAURACIÓN OFFLINE
  // ----------------------------------------------------------------------------
  async cargarBootstrap(idLocal) {
    const isRedReal = navigator.onLine && !state.simulacionOfflineForzada;

    if (isRedReal) {
      try {
        this.mostrarToast('🌐 Conectando', 'Descargando snapshot del local...', 'info');
        const resp = await fetch(`/api/bootstrap/${idLocal}`, { cache: 'no-store' });
        if (!resp.ok) throw new Error('Respuesta HTTP inválida');
        
        const data = await resp.json();
        
        // Guardar configuración y metadatos
        state.nombreLocal = data.nombre_local;
        document.getElementById('txt-nombre-local').textContent = state.nombreLocal;
        document.getElementById('txt-snapshot-time').textContent = new Date(data.timestamp_snapshot).toLocaleTimeString();

        await dbLocal.config.put({ clave: 'id_local', valor: idLocal });
        await dbLocal.config.put({ clave: 'nombre_local', valor: data.nombre_local });
        await dbLocal.config.put({ clave: 'timestamp_snapshot', valor: data.timestamp_snapshot });

        // Guardar recetas en IndexedDB
        await dbLocal.recetas.clear();
        await dbLocal.recetas.bulkPut(data.recetas);

        // Guardar existencias de lotes FEFO en IndexedDB
        await dbLocal.stock_lotes.clear();
        await dbLocal.stock_lotes.bulkPut(data.stock_fefo);

        state.recetasList = data.recetas;
        this.renderMenu();
        this.renderSelectorMerma(data.stock_fefo);
        this.mostrarToast('✅ Datos Sincronizados', `Recetas: ${data.total_recetas} • Lotes: ${data.total_lotes_disponibles}`, 'success');
        return;
      } catch (err) {
        console.warn('[Bootstrap] Falla de red, recurriendo a base local:', err);
      }
    }

    // MODO OFFLINE / FALLBACK A INDEXEDDB LOCAL
    const recetasLocales = await dbLocal.recetas.toArray();
    const stockLocal = await dbLocal.stock_lotes.toArray();
    const cfgNombre = await dbLocal.config.get('nombre_local');
    const cfgSnap = await dbLocal.config.get('timestamp_snapshot');

    state.nombreLocal = cfgNombre ? cfgNombre.valor : `Local ${idLocal}`;
    document.getElementById('txt-nombre-local').textContent = state.nombreLocal;
    document.getElementById('txt-snapshot-time').textContent = cfgSnap ? new Date(cfgSnap.valor).toLocaleTimeString() : 'Local Cache';

    if (recetasLocales.length > 0) {
      state.recetasList = recetasLocales;
      this.renderMenu();
      this.renderSelectorMerma(stockLocal);
      this.mostrarToast('📦 Modo Autónomo', 'Cargado desde caché local (IndexedDB)', 'warning');
    } else {
      document.getElementById('grid-platos').innerHTML = `
        <div class="col-span-full text-center py-20 text-gray-400">
          <p class="text-3xl mb-2">📡</p>
          <p class="font-bold">Sin datos locales previos</p>
          <p class="text-xs text-gray-500 mt-1">Conecta a internet al menos 3 segundos para inicializar el local.</p>
        </div>
      `;
    }
  },

  // ----------------------------------------------------------------------------
  // DEDUCCIÓN LOCAL FEFO Y GENERACIÓN DE EVENTO (PATRÓN OUTBOX)
  // ----------------------------------------------------------------------------
  async despacharComanda() {
    const recetasSeleccionadas = Object.entries(state.comandaActiva).filter(([_, cant]) => cant > 0);
    if (recetasSeleccionadas.length === 0) return;

    const btnDespachar = document.getElementById('btn-despachar');
    btnDespachar.disabled = true;

    const tInicio = performance.now();

    // 1. Calcular insumos requeridos en base a recetas
    const requerimientos = {}; // { id_producto: kg_totales }
    const platosResumen = {};

    for (const [idRecStr, cant] of recetasSeleccionadas) {
      const idRec = parseInt(idRecStr, 10);
      platosResumen[idRec] = cant;
      const rec = state.recetasList.find(r => r.id_receta === idRec);
      if (!rec) continue;

      for (const ing of rec.ingredientes) {
        const cantKg = ing.cantidad_kg * cant;
        requerimientos[ing.id_producto] = (requerimientos[ing.id_producto] || 0) + cantKg;
      }
    }

    // 2. Ejecutar deducción FEFO en IndexedDB local
    const lotesActualizados = [];
    const lotesAfectados = [];

    for (const [idProdStr, kgRequeridos] of Object.entries(requerimientos)) {
      const idProd = parseInt(idProdStr, 10);
      let pendiente = kgRequeridos;

      // Buscar lotes de ese producto ordenados por fecha de vencimiento (FEFO)
      const lotesProd = await dbLocal.stock_lotes
        .where('id_producto').equals(idProd)
        .sortBy('fecha_vencimiento');

      for (const lote of lotesProd) {
        if (lote.cantidad <= 0) continue;
        if (lote.cantidad >= pendiente) {
          lote.cantidad -= pendiente;
          lotesAfectados.push({ id_lote: lote.id_lote, consumido: pendiente, lote: lote.codigo_lote });
          pendiente = 0;
          lotesActualizados.push(lote);
          break;
        } else {
          pendiente -= lote.cantidad;
          lotesAfectados.push({ id_lote: lote.id_lote, consumido: lote.cantidad, lote: lote.codigo_lote });
          lote.cantidad = 0;
          lotesActualizados.push(lote);
        }
      }
    }

    // Guardar cambios en el stock local de IndexedDB
    if (lotesActualizados.length > 0) {
      await dbLocal.stock_lotes.bulkPut(lotesActualizados);
    }

    // 3. Generar Evento Inmutable para el Outbox con UUID v4
    const idEvento = crypto.randomUUID();
    const evento = {
      id_evento: idEvento,
      tipo_evento: 'PRODUCCION_RECETAS',
      fecha_local: new Date().toISOString(),
      estado: 'PENDIENTE',
      payload: {
        orden_platos: platosResumen,
        turno: state.turno,
        observaciones: `Despacho táctil KDS • Local ${state.idLocal}`,
        lotes_afectados_estimados: lotesAfectados
      }
    };

    // Guardar en la cola Outbox local
    await dbLocal.outbox_pendientes.put(evento);

    const tFin = performance.now();
    const deltaMs = (tFin - tInicio).toFixed(1);

    // 4. Limpiar comanda y actualizar UI de inmediato (Optimistic UI)
    this.limpiarComanda();
    await this.actualizarContadorOutbox();
    this.mostrarToast('⚡ Despacho Local Exitoso', `Stock FEFO descontado en ${deltaMs} ms (UUID: ${idEvento.substring(0, 8)})`, 'success');

    // 5. Si hay red, sincronizar en segundo plano sin bloquear al cocinero
    if (navigator.onLine && !state.simulacionOfflineForzada) {
      this.sincronizarColaBackground();
    }
  },

  // ----------------------------------------------------------------------------
  // SINCRONIZACIÓN DE LA COLA OUTBOX (BACKGROUND SYNC)
  // ----------------------------------------------------------------------------
  async sincronizarColaBackground() {
    if (state.isSyncing) return;
    const pendientes = await dbLocal.outbox_pendientes.toArray();
    if (pendientes.length === 0) return;

    state.isSyncing = true;
    this.actualizarSemaforo('syncing', `Sincronizando ${pendientes.length} eventos...`);

    try {
      const payloadEnvio = {
        id_local: state.idLocal,
        timestamp_envio: new Date().toISOString(),
        eventos: pendientes.map(p => ({
          id_evento: p.id_evento,
          tipo_evento: p.tipo_evento,
          fecha_local: p.fecha_local,
          payload: p.payload
        }))
      };

      const resp = await fetch('/api/sync', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payloadEnvio)
      });

      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const resultado = await resp.json();

      // Mover pendientes a historial
      const fechaSync = new Date().toISOString();
      const eventosHistorial = pendientes.map(p => ({ ...p, fecha_sync: fechaSync, estado: 'SINCRONIZADO' }));
      await dbLocal.historial_sync.bulkPut(eventosHistorial);
      await dbLocal.outbox_pendientes.bulkDelete(pendientes.map(p => p.id_evento));

      await this.actualizarContadorOutbox();
      this.evaluarConectividad();
      this.mostrarToast('☁️ Nube Actualizada', `Procesados: ${resultado.procesados_exitosamente} • Duplicados: ${resultado.duplicados_ignorados}`, 'success');
    } catch (err) {
      console.warn('[Sync] No se pudo enviar el paquete, se reintentará luego:', err);
      this.evaluarConectividad();
    } finally {
      state.isSyncing = false;
    }
  },

  async forzarSincronizacion() {
    await this.sincronizarColaBackground();
  },

  // ----------------------------------------------------------------------------
  // CONTROL DE RED, SEMÁFORO Y BLOQUEO DE TRASPASOS INTER-LOCALES
  // ----------------------------------------------------------------------------
  evaluarConectividad() {
    const isOnline = navigator.onLine && !state.simulacionOfflineForzada;
    const btnTraspasos = document.getElementById('btn-traspasos');

    dbLocal.outbox_pendientes.count().then(count => {
      if (!isOnline) {
        this.actualizarSemaforo('offline', `Modo Autónomo (${count} pendientes)`);
        // BLOQUEAR TRASPASOS EN MODO OFFLINE (REGLA DE NEGOCIO DISTRIBUIDA)
        btnTraspasos.classList.add('opacity-40', 'cursor-not-allowed', 'border-red-800');
        btnTraspasos.title = 'Función deshabilitada: Traspasos inter-locales requieren validación central.';
      } else if (count > 0) {
        this.actualizarSemaforo('offline', `Pendientes de envío (${count})`);
        btnTraspasos.classList.remove('opacity-40', 'cursor-not-allowed', 'border-red-800');
        btnTraspasos.title = 'Traspaso a otra sucursal';
      } else {
        this.actualizarSemaforo('online', 'En Línea • Sincronizado');
        btnTraspasos.classList.remove('opacity-40', 'cursor-not-allowed', 'border-red-800');
        btnTraspasos.title = 'Traspaso a otra sucursal';
      }
    });
  },

  actualizarSemaforo(tipo, texto) {
    const semaforo = document.getElementById('semaforo-red');
    const semTxt = document.getElementById('semaforo-txt');
    semaforo.className = 'flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-bold text-white shadow transition ';
    
    if (tipo === 'online') {
      semaforo.classList.add('badge-online');
    } else if (tipo === 'offline') {
      semaforo.classList.add('badge-offline');
    } else if (tipo === 'syncing') {
      semaforo.classList.add('badge-syncing');
    }
    semTxt.textContent = texto;
  },

  simularCorteRed() {
    state.simulacionOfflineForzada = !state.simulacionOfflineForzada;
    const btn = document.getElementById('btn-toggle-red');

    if (state.simulacionOfflineForzada) {
      btn.textContent = 'Restaurar Red 🟢';
      btn.className = 'bg-green-600 hover:bg-green-500 text-white font-bold px-2 py-0.5 rounded transition';
      this.mostrarToast('⚡ Conexión Cortada', 'Simulando caída total de internet en cocina', 'warning');
    } else {
      btn.textContent = 'Cortar Conexión ⚡';
      btn.className = 'bg-yellow-600 hover:bg-yellow-500 text-white font-bold px-2 py-0.5 rounded transition';
      this.mostrarToast('🌐 Conexión Restaurada', 'Detectando internet y vaciando Outbox...', 'info');
      this.sincronizarColaBackground();
    }
    this.evaluarConectividad();
  },

  intentarTraspaso() {
    const isOnline = navigator.onLine && !state.simulacionOfflineForzada;
    if (!isOnline) {
      alert('⚠️ OPERACIÓN BLOQUEADA POR DISEÑO:\n\nLos traspasos entre sucursales requieren conexión activa con el servidor central para prevenir duplicidad o descuadre de inventario.\n\nLa cocina local puede seguir despachando pedidos sin problemas.');
    } else {
      alert('ℹ️ Para coordinar traspasos entre locales, utiliza el módulo corporativo en el Panel Central de Streamlit.');
    }
  },

  // ----------------------------------------------------------------------------
  // GESTIÓN DE LA INTERFAZ: MENÚ DE PLATOS Y COMANDAS
  // ----------------------------------------------------------------------------
  renderMenu() {
    const grid = document.getElementById('grid-platos');
    const categoria = state.categoriaActiva;
    const filtrados = categoria === 'TODAS' 
      ? state.recetasList 
      : state.recetasList.filter(r => r.categoria.toLowerCase().includes(categoria.toLowerCase()));

    if (filtrados.length === 0) {
      grid.innerHTML = `<div class="col-span-full text-center py-12 text-gray-500">No hay platos en esta categoría</div>`;
      return;
    }

    grid.innerHTML = filtrados.map(r => {
      const cant = state.comandaActiva[r.id_receta] || 0;
      const numIng = r.ingredientes ? r.ingredientes.length : 0;
      return `
        <div class="card-plato bg-gray-900 border ${cant > 0 ? 'border-red-500 ring-1 ring-red-500' : 'border-gray-800'} rounded-xl p-3 flex flex-col justify-between shadow hover:border-gray-700 cursor-pointer">
          <div>
            <div class="flex justify-between items-start">
              <span class="text-xs font-semibold px-2 py-0.5 rounded bg-gray-800 text-red-400">${r.categoria}</span>
              <span class="text-xs text-gray-400 font-medium">⏱️ ${r.tiempo_min}m</span>
            </div>
            <h3 class="font-bold text-white text-sm mt-2 leading-tight">${r.nombre}</h3>
            <p class="text-xs text-gray-400 mt-1">${numIng} insumos con FEFO</p>
          </div>

          <div class="mt-3 pt-2 border-t border-gray-800 flex items-center justify-between">
            <span class="text-xs font-bold text-gray-300">$${r.precio_venta.toLocaleString('es-CL')}</span>
            <div class="flex items-center space-x-1.5" onclick="event.stopPropagation();">
              ${cant > 0 ? `
                <button onclick="app.modificarCantidad(${r.id_receta}, -1)" class="w-7 h-7 bg-gray-800 hover:bg-gray-700 text-white rounded-lg flex items-center justify-center font-bold text-sm">-</button>
                <span class="w-6 text-center font-bold text-sm text-red-400">${cant}</span>
              ` : ''}
              <button onclick="app.modificarCantidad(${r.id_receta}, 1)" class="w-7 h-7 bg-red-600 hover:bg-red-500 text-white rounded-lg flex items-center justify-center font-bold text-sm shadow">+</button>
            </div>
          </div>
        </div>
      `;
    }).join('');
  },

  filtrarCategoria(cat) {
    state.categoriaActiva = cat;
    document.querySelectorAll('.cat-btn').forEach(b => {
      b.classList.remove('active', 'bg-red-700', 'text-white');
      b.classList.add('bg-gray-900', 'text-gray-300');
    });
    event.target.classList.add('active', 'bg-red-700', 'text-white');
    event.target.classList.remove('bg-gray-900', 'text-gray-300');
    this.renderMenu();
  },

  modificarCantidad(idReceta, delta) {
    const actual = state.comandaActiva[idReceta] || 0;
    const nuevo = Math.max(0, actual + delta);
    if (nuevo === 0) {
      delete state.comandaActiva[idReceta];
    } else {
      state.comandaActiva[idReceta] = nuevo;
    }
    this.renderMenu();
    this.renderComanda();
  },

  limpiarComanda() {
    state.comandaActiva = {};
    this.renderMenu();
    this.renderComanda();
  },

  renderComanda() {
    const lista = document.getElementById('lista-comanda');
    const txtTotal = document.getElementById('txt-total-platos');
    const btnDespachar = document.getElementById('btn-despachar');

    const items = Object.entries(state.comandaActiva);
    const totalPlatos = items.reduce((acc, [_, cant]) => acc + cant, 0);
    txtTotal.textContent = totalPlatos;
    btnDespachar.disabled = totalPlatos === 0;

    if (items.length === 0) {
      lista.innerHTML = `
        <div class="text-center py-10 text-gray-500 text-sm">
          <span class="text-3xl block mb-2">🍽️</span>
          Selecciona platos del menú para preparar
        </div>
      `;
      return;
    }

    lista.innerHTML = items.map(([idStr, cant]) => {
      const idRec = parseInt(idStr, 10);
      const rec = state.recetasList.find(r => r.id_receta === idRec);
      if (!rec) return '';
      return `
        <div class="bg-gray-800/80 border border-gray-700/60 rounded-lg p-2.5 flex items-center justify-between">
          <div class="pr-2">
            <h4 class="text-xs font-bold text-white leading-tight">${rec.nombre}</h4>
            <span class="text-[10px] text-gray-400">FEFO automático</span>
          </div>
          <div class="flex items-center space-x-1.5 flex-shrink-0">
            <button onclick="app.modificarCantidad(${idRec}, -1)" class="w-6 h-6 bg-gray-700 hover:bg-gray-600 rounded text-xs font-bold text-white">-</button>
            <span class="w-5 text-center font-bold text-xs text-red-400">${cant}</span>
            <button onclick="app.modificarCantidad(${idRec}, 1)" class="w-6 h-6 bg-red-600 hover:bg-red-500 rounded text-xs font-bold text-white">+</button>
          </div>
        </div>
      `;
    }).join('');
  },

  // ----------------------------------------------------------------------------
  // MODAL Y MANEJO DE MERMAS OPERATIVAS
  // ----------------------------------------------------------------------------
  renderSelectorMerma(lotes) {
    const sel = document.getElementById('sel-merma-lote');
    if (!lotes || lotes.length === 0) {
      sel.innerHTML = '<option value="">No hay lotes disponibles</option>';
      return;
    }
    sel.innerHTML = lotes.map(l => `
      <option value="${l.id_lote}">
        ${l.producto} (Lote: ${l.codigo_lote} | Disp: ${l.cantidad} ${l.unidad_medida})
      </option>
    `).join('');
  },

  abrirModalMerma() {
    document.getElementById('modal-merma').classList.remove('hidden');
  },

  cerrarModalMerma() {
    document.getElementById('modal-merma').classList.add('hidden');
  },

  async guardarMerma() {
    const idLote = parseInt(document.getElementById('sel-merma-lote').value, 10);
    const cant = parseFloat(document.getElementById('inp-merma-cant').value);
    const motivo = document.getElementById('sel-merma-motivo').value;

    if (!idLote || isNaN(cant) || cant <= 0) {
      alert('Por favor especifica una cantidad válida.');
      return;
    }

    // Descontar en stock local
    const lote = await dbLocal.stock_lotes.get(idLote);
    if (lote) {
      lote.cantidad = Math.max(0, lote.cantidad - cant);
      await dbLocal.stock_lotes.put(lote);
    }

    // Encolar evento en Outbox
    const idEvento = crypto.randomUUID();
    await dbLocal.outbox_pendientes.put({
      id_evento: idEvento,
      tipo_evento: 'SALIDA_COCINA_MANUAL',
      fecha_local: new Date().toISOString(),
      estado: 'PENDIENTE',
      payload: {
        id_lote: idLote,
        cantidad: cant,
        observaciones: `Merma Operativa: ${motivo}`
      }
    });

    this.cerrarModalMerma();
    await this.actualizarContadorOutbox();
    this.mostrarToast('⚠️ Merma Registrada', `${cant} descontados localmente (UUID: ${idEvento.substring(0, 8)})`, 'warning');

    if (navigator.onLine && !state.simulacionOfflineForzada) {
      this.sincronizarColaBackground();
    }
  },

  // ----------------------------------------------------------------------------
  // DRAWER Y VISUALIZACIÓN DEL PATRÓN OUTBOX
  // ----------------------------------------------------------------------------
  async actualizarContadorOutbox() {
    const count = await dbLocal.outbox_pendientes.count();
    document.getElementById('txt-pendientes-count').textContent = count;
    document.getElementById('txt-outbox-status').textContent = `${count} pendientes`;
  },

  async toggleDrawerOutbox() {
    const modal = document.getElementById('modal-outbox');
    const container = document.getElementById('outbox-items-container');

    if (modal.classList.contains('hidden')) {
      const items = await dbLocal.outbox_pendientes.toArray();
      const historial = await dbLocal.historial_sync.limit(5).reverse().toArray();

      if (items.length === 0 && historial.length === 0) {
        container.innerHTML = `<div class="text-center py-8 text-gray-500 text-sm">Bandeja vacía. No hay eventos pendientes ni recientes.</div>`;
      } else {
        let html = '';
        if (items.length > 0) {
          html += `<h4 class="text-xs font-bold uppercase text-yellow-400 mb-2">Pendientes de Envío (${items.length}):</h4>`;
          html += items.map(it => `
            <div class="bg-gray-800 border border-yellow-700/50 p-2.5 rounded-lg text-xs space-y-1">
              <div class="flex justify-between items-center">
                <span class="font-bold text-white">${it.tipo_evento}</span>
                <span class="text-yellow-400 font-mono text-[10px]">UUID: ${it.id_evento}</span>
              </div>
              <p class="text-gray-300 text-[11px]">${it.payload.observaciones || 'Sin observaciones'}</p>
              <p class="text-gray-500 text-[10px]">Generado local: ${new Date(it.fecha_local).toLocaleTimeString()}</p>
            </div>
          `).join('');
        }

        if (historial.length > 0) {
          html += `<h4 class="text-xs font-bold uppercase text-green-400 mt-4 mb-2">Últimos Sincronizados con Éxito:</h4>`;
          html += historial.map(h => `
            <div class="bg-gray-950 border border-gray-800 p-2 rounded-lg text-xs space-y-0.5 opacity-80">
              <div class="flex justify-between items-center">
                <span class="font-semibold text-gray-300">${h.tipo_evento}</span>
                <span class="text-green-400 font-mono text-[10px]">Sincronizado ✅</span>
              </div>
              <p class="text-gray-500 text-[10px]">UUID: ${h.id_evento} • Sync: ${new Date(h.fecha_sync).toLocaleTimeString()}</p>
            </div>
          `).join('');
        }

        container.innerHTML = html;
      }
      modal.classList.remove('hidden');
    } else {
      modal.classList.add('hidden');
    }
  },

  cambiarLocal(nuevoId) {
    state.idLocal = parseInt(nuevoId, 10);
    this.limpiarComanda();
    this.cargarBootstrap(state.idLocal);
  },

  mostrarToast(titulo, mensaje, tipo = 'info') {
    const toast = document.getElementById('toast');
    document.getElementById('toast-title').textContent = titulo;
    document.getElementById('toast-msg').textContent = mensaje;
    const icon = document.getElementById('toast-icon');
    
    if (tipo === 'success') icon.textContent = '✅';
    else if (tipo === 'warning') icon.textContent = '⚠️';
    else icon.textContent = 'ℹ️';

    toast.classList.remove('translate-y-20', 'opacity-0');
    setTimeout(() => {
      toast.classList.add('translate-y-20', 'opacity-0');
    }, 3200);
  }
};

// Autoarranque al cargar el DOM
document.addEventListener('DOMContentLoaded', () => app.init());
