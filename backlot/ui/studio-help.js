(() => {
  const helpRegion = document.getElementById('studio-button-help');
  const preference = document.getElementById('context-help-enabled');
  if (!helpRegion || !preference) return;

  const preferenceKey = 'openmontage.studio.context-help.v1';
  const helpById = {
    'refresh-status': 'Vuelve a consultar la salud y las capacidades locales de Studio.',
    'agent-toggle': 'Muestra u oculta el estado del agente para el proyecto actual.',
    'top-new-project': 'Abre el formulario para crear una carpeta de proyecto nueva.',
    'new-project-inline': 'Abre el formulario para crear una carpeta de proyecto nueva.',
    'social-toggle': 'Muestra los ajustes de salida para adaptar el montaje a una plataforma.',
    'social-apply': 'Aplica al montaje los ajustes locales de la plataforma seleccionada.',
    'preview-refresh': 'Solicita una nueva previsualización con el montaje guardado.',
    'edit-undo': 'Revierte el último cambio del proyecto compartido.',
    'edit-redo': 'Reaplica el último cambio que se deshizo.',
    'edit-save': 'Guarda los cambios del proyecto compartido.',
    'edit-export': 'Exporta el montaje con el formato y los ajustes seleccionados.',
    'timeline-add': 'Añade a la línea de tiempo el medio seleccionado en la biblioteca.',
    'clip-split': 'Divide el clip seleccionado en la posición actual del cabezal.',
    'clip-remove': 'Quita el clip seleccionado del montaje; deshacer puede restaurarlo.',
    'subtitle-style-apply': 'Aplica el estilo seleccionado a los bloques de subtítulos.',
    'subtitle-add': 'Inserta un bloque de subtítulo si la API activa lo admite.',
    'projects-create': 'Abre el formulario para crear una carpeta de proyecto nueva.',
    'create-confirm': 'Crea el proyecto y su estructura dentro de la carpeta raíz local.',
    'channel-filter-open': 'Abre los filtros históricos de búsqueda de canales de YouTube.',
    'channel-submit': 'Consulta YouTube con el tema, las páginas y los filtros seleccionados.',
    'manual-data-toggle': 'Muestra el formulario para añadir datos aportados por ti.',
    'manual-data-save': 'Guarda los datos aportados dentro del informe local actual.',
    'channel-filter-close': 'Cierra los filtros y descarta los cambios sin aplicar.',
    'channel-recent-preset': 'Rellena el ejemplo de publicaciones recientes con tres coincidencias.',
    'channel-young-preset': 'Rellena el ejemplo de canales con muchas vistas y hasta 90 días.',
    'channel-filter-reset': 'Restablece los filtros a sus valores iniciales.',
    'channel-filter-cancel': 'Cierra los filtros y descarta los cambios sin aplicar.',
    'sports-copy': 'Copia el informe deportivo consultado para reutilizarlo o editarlo.',
    'agent-close': 'Oculta el panel de estado del agente.'
  };
  const labels = {
    video: 'Vídeo', audio: 'Audio', subtitles: 'Subtítulos', library: 'Biblioteca',
    projects: 'Proyectos', channels: 'Investigación', sports: 'Comparativas',
    thumbnails: 'Miniaturas', avatars: 'Avatares', clips: 'Clips y tráileres', settings: 'Preferencias'
  };
  const actionHelp = new Map([
    ['aplicar', 'Aplica los cambios revisados a este elemento.'],
    ['aplicar filtros', 'Valida y guarda estos criterios para la próxima consulta de YouTube.'],
    ['consultar fuente', 'Envía los campos indicados al conector UEFA configurado.'],
    ['mute', 'Silencia o reactiva esta pista en la mezcla.'],
    ['solo', 'Aísla esta pista de las demás durante la reproducción y la exportación.'],
    ['abrir en editor', 'Abre este proyecto en el editor compartido.'],
    ['añadir seleccionado', 'Añade el medio seleccionado a la línea de tiempo.'],
    ['dividir en posición', 'Divide el clip en la posición actual del cabezal.'],
    ['quitar clip', 'Quita el clip seleccionado del montaje.']
  ]);
  let enabled = true;
  let hoveredButton = null;
  let focusedButton = null;
  let activeButton = null;

  try { enabled = localStorage.getItem(preferenceKey) !== 'false'; } catch { /* Preferencias locales pueden estar bloqueadas. */ }
  preference.checked = enabled;

  function accessibleName(button) {
    return (button.getAttribute('aria-label') || button.innerText || button.value || button.title || '')
      .replace(/\s+/g, ' ').trim();
  }

  function contextualHelp(button) {
    if (helpById[button.id]) return helpById[button.id];
    if (button.classList.contains('timeline-clip')) return 'Selecciona este corte para inspeccionar su posición y propiedades.';
    if (button.classList.contains('media-row')) return 'Selecciona este medio para revisar su procedencia o añadirlo al montaje.';
    if (button.classList.contains('nav-item')) return `Abre el módulo ${labels[button.dataset.module] || 'seleccionado'}.`;
    if (button.title) return button.title;
    const name = accessibleName(button);
    const mapped = actionHelp.get(name.toLocaleLowerCase('es'));
    if (mapped) return mapped;
    if (button.classList.contains('mode-chip')) return `${name}: muestra o selecciona este modo de trabajo.`;
    const panel = button.closest('.panel');
    const heading = panel?.querySelector('h2')?.innerText?.trim();
    const module = button.closest('.module-page')?.dataset.page;
    const context = heading || labels[module] || 'Studio';
    return name ? `${context}: ${name}.` : `Acción de ${context}.`;
  }

  function attach(button) {
    if (button.dataset.contextHelpReady === 'true') return;
    button.dataset.contextHelpReady = 'true';
  }

  function attachTree(root) {
    if (root instanceof Element && root.matches('button')) attach(root);
    root.querySelectorAll?.('button').forEach(attach);
  }

  function addDescription(button) {
    const ids = new Set((button.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean));
    ids.add(helpRegion.id);
    button.setAttribute('aria-describedby', [...ids].join(' '));
  }

  function removeDescription(button) {
    const ids = (button.getAttribute('aria-describedby') || '').split(/\s+/).filter(id => id && id !== helpRegion.id);
    if (ids.length) button.setAttribute('aria-describedby', ids.join(' '));
    else button.removeAttribute('aria-describedby');
  }

  function show(button) {
    if (!enabled || !button?.isConnected) return;
    activeButton = button;
    helpRegion.textContent = contextualHelp(button);
    helpRegion.hidden = false;
    addDescription(button);
  }

  function hideIfInactive(button) {
    if (button && button !== hoveredButton && button !== focusedButton) removeDescription(button);
    const next = focusedButton || hoveredButton;
    if (next) return show(next);
    if (!activeButton || activeButton === button) {
      helpRegion.textContent = '';
      helpRegion.hidden = true;
      activeButton = null;
    }
  }

  function setEnabled(value) {
    enabled = value;
    document.documentElement.dataset.contextHelp = enabled ? 'on' : 'off';
    try { localStorage.setItem(preferenceKey, String(enabled)); } catch { /* La opción sigue activa en esta sesión. */ }
    if (!enabled) {
      document.querySelectorAll(`[aria-describedby~="${helpRegion.id}"]`).forEach(removeDescription);
      helpRegion.textContent = '';
      helpRegion.hidden = true;
      activeButton = null;
      return;
    }
    const current = focusedButton || hoveredButton;
    if (current) show(current);
  }

  document.documentElement.dataset.contextHelp = enabled ? 'on' : 'off';
  attachTree(document);
  new MutationObserver(records => records.forEach(record => record.addedNodes.forEach(node => {
    if (node.nodeType === Node.ELEMENT_NODE) attachTree(node);
  }))).observe(document.body, { childList: true, subtree: true });

  document.addEventListener('pointerover', event => {
    const button = event.target.closest?.('button');
    if (!button || button === hoveredButton) return;
    hoveredButton = button;
    show(button);
  }, true);
  document.addEventListener('pointerout', event => {
    const button = event.target.closest?.('button');
    if (!button || button.contains(event.relatedTarget)) return;
    if (hoveredButton === button) hoveredButton = null;
    hideIfInactive(button);
  }, true);
  document.addEventListener('focusin', event => {
    const button = event.target.closest?.('button');
    if (!button) return;
    focusedButton = button;
    show(button);
  });
  document.addEventListener('focusout', event => {
    const button = event.target.closest?.('button');
    if (!button) return;
    if (focusedButton === button) focusedButton = null;
    hideIfInactive(button);
  });
  preference.addEventListener('change', () => setEnabled(preference.checked));
})();
