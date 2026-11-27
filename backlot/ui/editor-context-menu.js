// Context actions are supplied by the editor and reuse its existing commands.
export function contextMenuItems(context, state = {}) {
  const item = (id, label, enabled = true, reason = '') => ({ id, label, enabled, reason });
  if (context?.type === 'clip') {
    const items = [item('properties', 'Propiedades del clip', state.canEdit !== false, state.editReason || '')];
    items.push(item('split-cursor', 'Dividir en el cursor', Boolean(state.canSplit), state.splitReason || 'El cursor debe dejar material a ambos lados.'));
    if (state.canMute) items.push(item(state.muted ? 'unmute' : 'mute', state.muted ? 'Activar audio' : 'Silenciar audio', Boolean(state.canMute), state.muteReason || ''));
    if (state.canDuplicate) items.push(item('duplicate', `Duplicar selección${state.selectedCount > 1 ? ` (${state.selectedCount})` : ''}`));
    if (context.track === 'audio') {
      items.push(item('remove-audio', 'Quitar audio seleccionado', Boolean(state.canRemove), state.removeReason || ''));
    } else {
      items.push(item('keep-gap', 'Borrar y conservar el hueco', Boolean(state.canKeepGap), state.keepGapReason || ''));
      items.push(item('ripple-delete', 'Borrar y cerrar el hueco', Boolean(state.canRippleDelete), state.rippleReason || ''));
    }
    return items;
  }
  if (context?.type === 'cue') return [item('edit-cue', 'Editar subtítulo'), item('seek-cue', 'Ir al inicio del subtítulo')];
  if (context?.type === 'title') return [item('edit-title', 'Editar título'), item('remove-title', 'Quitar título', Boolean(state.canRemove), state.removeReason || '')];
  if (context?.type === 'layer') return [
    item('edit-layer', 'Editar capa'), item('lower-layer', 'Bajar capa', Boolean(state.canLower), state.lowerReason || ''),
    item('raise-layer', 'Subir capa', Boolean(state.canRaise), state.raiseReason || ''),
    item('remove-layer', 'Quitar capa', Boolean(state.canRemove), state.removeReason || '')
  ];
  if (context?.type === 'source') return [item('view-source', 'Ver fuente'), item('add-source', 'Añadir a pista')];
  if (context?.type === 'library') return [item('import-media', 'Importar medios')];
  if (context?.type === 'monitor') return [
    item('toggle-play', state.playable ? 'Reproducir o pausar' : 'Sin medio reproducible', Boolean(state.playable), state.playable ? '' : 'Selecciona una fuente o prepara una vista previa.'),
    item('prepare-preview', 'Preparar vista previa', Boolean(state.hasProject), state.hasProject ? '' : 'Abre un proyecto antes de preparar la vista previa.')
  ];
  if (context?.type === 'empty') return [
    item('import-media', 'Importar medios'), item('add-marker', 'Añadir marcador en el cursor', Boolean(state.canAddMarker), state.markerReason || '')
  ];
  return [];
}

export function clampMenuPosition(x, y, menuWidth, menuHeight, viewportWidth, viewportHeight, margin = 8) {
  const right = Math.max(margin, viewportWidth - menuWidth - margin);
  const bottom = Math.max(margin, viewportHeight - menuHeight - margin);
  return {
    left: Math.min(Math.max(margin, x), right),
    top: Math.min(Math.max(margin, y), bottom)
  };
}

export function describeEditorContext(target) {
  const node=target?.closest?.('[data-editor-context]');
  if(node){
    const type=node.dataset.editorContext;
    if(type==='empty')return {type,node};
    if(type==='clip')return {type,id:node.dataset.contextId,track:node.dataset.contextTrack,node};
    if(type==='cue')return {type,index:Number(node.dataset.contextIndex),node};
    return {type,id:node.dataset.contextId,node};
  }
  if(target?.closest?.('#editor-monitor .editor-screen'))return {type:'monitor'};
  const library=target?.closest?.('.editor-library');
  if(library&&!target.closest?.('button,input,select,textarea,a,summary,[contenteditable="true"]'))return {type:'library'};
  const tracks=target?.closest?.('#edit-tracks');
  return tracks?{type:'empty',node:tracks}:null;
}

export function initializeEditorContextMenu({ root, describe, prepare = () => {}, items, state = () => ({}), activate }) {
  let menu = null;
  let opener = null;
  let context = null;
  const close = (restoreFocus = false) => {
    if (!menu) return;
    menu.remove();
    menu = null;
    const target = opener;
    opener = null;
    context = null;
    if (restoreFocus && target?.isConnected) target.focus({ preventScroll: true });
  };
  const enabledButtons = () => [...(menu?.querySelectorAll('[role="menuitem"]') || [])].filter(node => !node.disabled);
  const open = (nextContext, target, x, y) => {
    close(false);
    if (!nextContext) return;
    prepare(nextContext);
    const choices = items(nextContext, state(nextContext));
    if (!choices.length) return;
    context = nextContext;
    opener = target;
    menu = document.createElement('div');
    menu.className = 'editor-context-menu';
    menu.setAttribute('role', 'menu');
    menu.setAttribute('aria-label', nextContext.type === 'empty' ? 'Acciones de la línea de tiempo' : 'Acciones del elemento');
    for (const choice of choices) {
      const button = document.createElement('button');
      button.type = 'button';
      button.setAttribute('role', 'menuitem');
      button.textContent = choice.label;
      button.disabled = !choice.enabled;
      if (choice.reason) { button.title = choice.reason; button.setAttribute('aria-label', `${choice.label}. ${choice.reason}`); }
      button.addEventListener('click', () => {
        const selectedContext = context;
        close(false);
        if (choice.enabled) activate(choice.id, selectedContext);
      });
      menu.append(button);
    }
    menu.addEventListener('keydown', event => {
      const buttons = enabledButtons();
      if (!buttons.length) return;
      const index = buttons.indexOf(document.activeElement);
      let next = null;
      if (event.key === 'ArrowDown') next = buttons[(index + 1 + buttons.length) % buttons.length];
      else if (event.key === 'ArrowUp') next = buttons[(index - 1 + buttons.length) % buttons.length];
      else if (event.key === 'Home') next = buttons[0];
      else if (event.key === 'End') next = buttons.at(-1);
      else if (event.key === 'Escape') { event.preventDefault(); close(true); return; }
      if (next) { event.preventDefault(); next.focus(); }
    });
    menu.addEventListener('focusout', () => queueMicrotask(() => { if (menu && !menu.contains(document.activeElement)) close(false); }));
    root.append(menu);
    const rect = menu.getBoundingClientRect();
    const position = clampMenuPosition(x, y, rect.width, rect.height, window.innerWidth, window.innerHeight);
    menu.style.left = `${position.left}px`;
    menu.style.top = `${position.top}px`;
    enabledButtons()[0]?.focus({ preventScroll: true });
  };
  root.addEventListener('contextmenu', event => {
    const nextContext = describe(event.target, event);
    if (!nextContext) return;
    event.preventDefault();
    open(nextContext, event.target.closest('[data-editor-context]') || event.target, event.clientX, event.clientY);
  });
  root.addEventListener('keydown', event => {
    if (event.key !== 'ContextMenu' && !(event.shiftKey && event.key === 'F10')) return;
    const target = document.activeElement;
    if (!root.contains(target)) return;
    const nextContext = describe(target, event);
    if (!nextContext) return;
    event.preventDefault();
    const rect = target.getBoundingClientRect();
    open(nextContext, target, rect.left, rect.bottom);
  });
  document.addEventListener('pointerdown', event => {
    if (menu && !menu.contains(event.target)) close(false);
  }, true);
  document.addEventListener('keydown', event => {
    if (event.key === 'Escape' && menu && !menu.contains(event.target)) close(true);
  }, true);
  return { close, isOpen: () => Boolean(menu) };
}
