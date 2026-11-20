/* -*- coding: utf-8 -*-
 * MOTOR INTERACTIVO MANYA SERVICIOTI v11.0 (Zero-Hardcode, XSS-Safe & Full UX Pro)
 * Controla:
 * 1. Hidratación 100% dinámica y sanitizada desde /data/*.json (ESPN API, AUF, 1891 BD, Open-Meteo, Prensa).
 * 2. Match Center adaptativo (EN_VIVO, POST_PARTIDO 48h con goleadores/video, PREVIA, FINAL URUGUAYO).
 * 3. Tablas oficiales (Anual, Clausura, Libertadores) + Cuadro de Definición / Simulador interactivo.
 * 4. Pizarra Táctica Pro "Armá tu 11" (3 formaciones, filtro de banco por línea, Último 11 de Aguirre, 11 Ideal 2026 y PNG 1080x1350).
 * 5. Prensa Deportiva Filtrable + Búsqueda Instantánea (#prensa-vivo).
 * 6. Lightbox Profesional Accesible con navegación Prev/Next, teclado, swipe táctil y soporte en Galerías, Influencers y Piel Carbonera.
 * 7. Scroll-Spy (IntersectionObserver), Sistema de Toasts (aria-live), Shimmer Lazy-Load y PWA Install CTA.
 */
(function () {
  'use strict';

  const APP_VERSION = '11.0';

  let state = {
    live: null,
    digest: null,
    ig: [],
    galleries: [],
    galleryFilter: 'all',
    galleryLimit: 6,
    tattoos: [],
    tattooFilter: 'all',
    squad: null,
    history: null,
    escudosCatalog: null,
    formation: '4-2-3-1',
    selectedSlotIndex: null,
    selectedBenchIndex: null,
    benchLineFilter: 'all',
    activeLineupPreset: 'ideal',
    lineup: [],
    bench: [],
    initialLineup: [],
    initialBench: [],
    simPointsDelta: 0,
    standingsTab: 'anual',
    pressArticles: [],
    pressSourceFilter: 'all',
    pressSearchQuery: '',
    pressExpanded: false
  };

  const lightboxState = {
    items: [],
    index: 0,
    triggerEl: null,
    isOpen: false
  };

  const FORMATIONS = {
    '4-2-3-1': [
      { x: 50, y: 88, role: 'ARQ' },
      { x: 82, y: 70, role: 'LD' },
      { x: 62, y: 74, role: 'DFC' },
      { x: 38, y: 74, role: 'DFC' },
      { x: 18, y: 70, role: 'LI' },
      { x: 38, y: 53, role: 'MCD' },
      { x: 62, y: 53, role: 'MC' },
      { x: 80, y: 33, role: 'ED' },
      { x: 50, y: 35, role: 'MCO' },
      { x: 20, y: 33, role: 'EI' },
      { x: 50, y: 15, role: 'DC' }
    ],
    '4-3-3': [
      { x: 50, y: 88, role: 'ARQ' },
      { x: 82, y: 70, role: 'LD' },
      { x: 62, y: 74, role: 'DFC' },
      { x: 38, y: 74, role: 'DFC' },
      { x: 18, y: 70, role: 'LI' },
      { x: 50, y: 56, role: 'MCD' },
      { x: 68, y: 44, role: 'MC' },
      { x: 80, y: 22, role: 'ED' },
      { x: 32, y: 44, role: 'MCO' },
      { x: 20, y: 22, role: 'EI' },
      { x: 50, y: 14, role: 'DC' }
    ],
    '4-4-2': [
      { x: 50, y: 88, role: 'ARQ' },
      { x: 82, y: 70, role: 'LD' },
      { x: 62, y: 74, role: 'DFC' },
      { x: 38, y: 74, role: 'DFC' },
      { x: 18, y: 70, role: 'LI' },
      { x: 38, y: 52, role: 'MCD' },
      { x: 62, y: 52, role: 'MC' },
      { x: 82, y: 42, role: 'MD' },
      { x: 38, y: 20, role: 'SD' },
      { x: 18, y: 42, role: 'MI' },
      { x: 62, y: 16, role: 'DC' }
    ]
  };

  // Plantel real vigente de Peñarol Noviembre 2026 (respaldo inmediato si aún no cargó squad_2026.json)
  const DEFAULT_LINEUP = [
    { id: 'washington_aguerre', numero: 29, nombre: 'Washington Aguerre', posicion: 'ARQ', linea: 'portero', titular: true },
    { id: 'ignacio_alegre', numero: 28, nombre: 'Ignacio Alegre', posicion: 'LD', linea: 'defensa', titular: true },
    { id: 'german_pezzella', numero: 2, nombre: 'Germán Pezzella', posicion: 'DFC', linea: 'defensa', titular: true },
    { id: 'nahuel_herrera', numero: 34, nombre: 'Nahuel Herrera', posicion: 'DFC', linea: 'defensa', titular: true },
    { id: 'maximiliano_olivera', numero: 15, nombre: 'Maximiliano Olivera', posicion: 'LI', linea: 'defensa', titular: true },
    { id: 'eric_remedi', numero: 5, nombre: 'Eric Remedi', posicion: 'MCD', linea: 'volante', titular: true },
    { id: 'eduardo_darias', numero: 13, nombre: 'Eduardo Darias', posicion: 'MC', linea: 'volante', titular: true },
    { id: 'javier_cabrera', numero: 7, nombre: 'Javier Cabrera', posicion: 'ED', linea: 'ataque', titular: true },
    { id: 'leonardo_fernandez', numero: 10, nombre: 'Leonardo Fernández', posicion: 'MCO', linea: 'ataque', titular: true },
    { id: 'leonel_jaime', numero: 11, nombre: 'Leonel Jaime', posicion: 'EI', linea: 'ataque', titular: true },
    { id: 'matias_arezo', numero: 19, nombre: 'Matías Arezo', posicion: 'DC', linea: 'ataque', titular: true }
  ];

  const DEFAULT_BENCH = [
    { id: 'sebastian_britos', numero: 1, nombre: 'Sebastián Britos', posicion: 'ARQ', linea: 'portero', titular: false },
    { id: 'mauricio_lemos', numero: 3, nombre: 'Mauricio Lemos', posicion: 'DFC', linea: 'defensa', titular: false },
    { id: 'lucas_ferreira', numero: 6, nombre: 'Lucas Ferreira', posicion: 'DFC', linea: 'defensa', titular: false },
    { id: 'diego_laxalt', numero: 93, nombre: 'Diego Laxalt', posicion: 'LI', linea: 'defensa', titular: false },
    { id: 'thiago_espinosa', numero: 26, nombre: 'Thiago Espinosa', posicion: 'LI', linea: 'defensa', titular: false },
    { id: 'lucas_hernandez', numero: 27, nombre: 'Lucas Hernández', posicion: 'LI', linea: 'defensa', titular: false },
    { id: 'jesus_trindade', numero: 21, nombre: 'Jesús Trindade', posicion: 'MCD', linea: 'volante', titular: false },
    { id: 'roberto_fernandez', numero: 8, nombre: 'Roberto Fernández', posicion: 'MC', linea: 'volante', titular: false },
    { id: 'leandro_umpierrez', numero: 32, nombre: 'Leandro Umpiérrez', posicion: 'MCO', linea: 'ataque', titular: false },
    { id: 'luis_miguel_angulo', numero: 77, nombre: 'Luis Miguel Angulo', posicion: 'EI', linea: 'ataque', titular: false },
    { id: 'abel_hernandez', numero: 99, nombre: 'Abel Hernández', posicion: 'DC', linea: 'ataque', titular: false },
    { id: 'facundo_batista', numero: 9, nombre: 'Facundo Batista', posicion: 'DC', linea: 'ataque', titular: false }
  ];

  const TRIVIA_QUESTIONS = [
    { cat: 'general', catName: 'Fundación & Raíces', q: '¿En qué fecha exacta y en qué histórico enclave se fundó nuestra institución (CURCC / Club Atlético Peñarol)?', opts: ['28 de septiembre de 1891 en la Villa Peñarol', '14 de mayo de 1899 en La Blanqueada', '18 de julio de 1900 en el Centro de Montevideo', '25 de agosto de 1891 en Pocitos'], ans: 0, exp: 'El 28 de septiembre de 1891 los trabajadores ferroviarios fundaron el Central Uruguay Railway Cricket Club (CURCC) en la Villa Peñarol, decano indiscutido del fútbol uruguayo.' },
    { cat: 'libertadores', catName: 'Copas Libertadores', q: '¿Quién convirtió el gol agónico en el minuto 120 en Santiago de Chile para ganar la quinta Copa Libertadores en 1987?', opts: ['Diego "La Fiera" Aguirre', 'Fernando Morena', 'Alberto Spencer', 'Jorge Cabrera'], ans: 0, exp: 'Diego Aguirre cruzó un remate de zurda legendario a los 120 minutos ante América de Cali en el Estadio Nacional de Santiago, sellando la quinta Libertadores.' },
    { cat: 'libertadores', catName: 'Copas Libertadores', q: '¿Quién es el máximo goleador histórico de toda la Copa CONMEBOL Libertadores de América con 54 goles?', opts: ['Alberto "Cabeza Mágica" Spencer', 'Fernando Morena', 'Pedro Virgilio Rocha', 'Juan Alberto Schiaffino'], ans: 0, exp: 'Alberto Spencer ostenta el récord absoluto de la Copa Libertadores con 54 goles (48 de ellos convertidos con la gloriosa camiseta de Peñarol).' },
    { cat: 'libertadores', catName: 'Copas Libertadores', q: '¿Contra qué tres gigantes de Europa conquistó Peñarol sus 3 Copas Intercontinentales del Mundo?', opts: ['Benfica (1961), Real Madrid (1966) y Aston Villa (1982)', 'Milan (1961), Real Madrid (1966) y Liverpool (1982)', 'Benfica (1960), Inter (1966) y Hamburgo (1982)', 'Ajax (1961), Real Madrid (1966) y Juventus (1982)'], ans: 0, exp: 'Peñarol fue tricampeón del mundo venciendo al Benfica de Eusébio (1961), al Real Madrid en Montevideo y en el Bernabéu (1966) y al Aston Villa en Tokio (1982).' },
    { cat: 'idolos', catName: 'Ídolos Eternos', q: '¿Cómo se llama el legendario capitán que disputó 574 partidos oficiales jugando exclusivamente en Peñarol toda su carrera?', opts: ['Néstor "Tito" Gonçalves', 'Obdulio Varela', 'William Martínez', 'Walter Olivera'], ans: 0, exp: 'Néstor "Tito" Gonçalves, el "Capitán de Capitanes", defendió únicamente la camiseta oro y carbón entre 1957 y 1970, conquistando 3 Libertadores, 2 Intercontinentales y 9 Uruguayos.' },
    { cat: 'records', catName: 'Récords & Hazañas', q: '¿Qué récord imbatible estableció Fernando Morena el 16 de julio de 1978 ante Huracán Buceo en el Estadio Centenario?', opts: ['Anotó 7 goles en un mismo partido oficial', 'Convirtió 5 goles de cabeza en un solo tiempo', 'Marcó 3 goles en menos de 4 minutos', 'Anotó 4 goles de tiro libre en un partido'], ans: 0, exp: 'Fernando Morena anotó 7 goles en la victoria 7-0 ante Huracán Buceo, récord absoluto en la historia de la Primera División uruguaya.' },
    { cat: 'records', catName: 'Récords & Hazañas', q: '¿Cuántos minutos con valla invicta consecutiva acumuló Ladislao Mazurkiewicz en 1968, récord histórico del fútbol uruguayo?', opts: ['987 minutos', '720 minutos', '840 minutos', '1040 minutos'], ans: 0, exp: 'Ladislao Mazurkiewicz mantuvo su arco invicto durante 987 minutos en el Campeonato Uruguayo de 1968, marca insuperada.' },
    { cat: 'clasicos', catName: 'Clásicos Inolvidables', q: '¿Por qué se conoce al clásico del 23 de abril de 1987 como "El Clásico de los 8 contra 11"?', opts: ['Peñarol sufrió 3 expulsiones y aun así ganó 2-1 con gol de Diego Aguirre', 'Nacional jugó con 8 futbolistas por lesión', 'Peñarol defendió un 0-0 con 8 jugadores durante 85 minutos', 'El partido terminó con 8 jugadores aurinegros festejando'], ans: 0, exp: 'Con 3 futbolistas menos por expulsiones, el Peñarol de Washington Tabárez atacó heroicamente y Diego Aguirre anotó el 2-1 definitivo en el minuto 82.' },
    { cat: 'clasicos', catName: 'Clásicos Inolvidables', q: '¿Qué hecho histórico originó el célebre "Clásico de la Fuga" el 9 de octubre de 1949?', opts: ['Nacional perdía 2-0 ante la Máquina del 49 y decidió no salir a jugar el 2° tiempo', 'Peñarol ganó 5-0 escapándose en la Tabla Anual', 'El clásico se suspendió por un apagón en el Centenario', 'El arquero rival se retiró por el túnel sin autorización'], ans: 0, exp: 'Peñarol arrollaba 2-0 con goles de Ghiggia y Míguez; en el entretiempo, Nacional no salió a disputar el complemento.' },
    { cat: 'clasicos', catName: 'Clásicos Inolvidables', q: '¿Cuál fue el marcador del histórico clásico del 27 de abril de 2014, mayor goleada clásica en torneos cortos modernos?', opts: ['Peñarol 5 - 0 Nacional', 'Peñarol 4 - 0 Nacional', 'Peñarol 5 - 1 Nacional', 'Peñarol 6 - 0 Nacional'], ans: 0, exp: 'Histórico 5 a 0 aurinegro con goles de Marcelo Zalayeta, Damián Macaluso, Jorge "Japo" Rodríguez y doblete de Luis Aguiar.' },
    { cat: 'records', catName: 'Récords & Hazañas', q: '¿Cuántos goles oficiales convirtió Fernando Morena con la camiseta del Club Atlético Peñarol según 1891 BD?', opts: ['350 goles', '280 goles', '310 goles', '215 goles'], ans: 0, exp: 'Fernando Morena es el máximo artillero de la historia del Decano con 350 goles oficiales certificados por la Comisión de Historia y Patrimonio.' },
    { cat: 'cds', catName: 'Estadio Campeón del Siglo', q: '¿En qué fecha se inauguró oficialmente el Estadio Campeón del Siglo y quién convirtió el primer gol en su campo?', opts: ['28 de marzo de 2016 — Diego Forlán', '28 de septiembre de 2015 — Marcelo Zalayeta', '19 de abril de 2016 — Leonardo Fernández', '31 de octubre de 2016 — Diego Aguirre'], ans: 0, exp: 'El Campeón del Siglo se inauguró el 28 de marzo de 2016 con triunfo 4-1 ante River Plate argentino; Diego Forlán convirtió el histórico primer gol.' },
    { cat: 'records', catName: 'Récords & Hazañas', q: '¿En qué años conquistó Peñarol sus dos célebres Quinquenios de Oro en el Campeonato Uruguayo?', opts: ['1958-1962 y 1993-1997', '1960-1964 y 1995-1999', '1955-1959 y 1990-1994', '1965-1969 y 1980-1984'], ans: 0, exp: 'Peñarol es el único club uruguayo con dos Quinquenios de Oro: 1958-1962 y 1993-1997.' },
    { cat: 'general', catName: 'Distinciones Mundiales', q: '¿Qué histórica distinción otorgó la IFFHS a Peñarol en septiembre de 2009 tras el balance del siglo?', opts: ['Club Campeón del Siglo XX de Sudamérica (con 531 puntos)', 'Mejor club de la década de 1980', 'Club con mayor hinchada proporcional del planeta', 'Institución deportiva más laureada de América'], ans: 0, exp: 'La IFFHS proclamó oficialmente a Peñarol como el Mejor Club del Siglo XX de Sudamérica.' },
    { cat: 'libertadores', catName: 'Copas Libertadores', q: '¿Quién anotó el gol agónico en el minuto 89 en Santiago de Chile para consagrar a Peñarol campeón de América ante Cobreloa en 1982?', opts: ['Fernando Morena', 'Venancio Ramos', 'Jair Gonçalves', 'Ernesto Vargas'], ans: 0, exp: 'Morena conectó de derecha un centro de Ramos a los 89 minutos en el Estadio Nacional de Santiago, conquistando la cuarta Libertadores.' },
    { cat: 'idolos', catName: 'Ídolos Eternos', q: '¿Quién fue el capitán y emblema del Segundo Quinquenio (1993-1997), célebre por su precisión quirúrgica en tiros libres?', opts: ['Pablo Javier Bengoechea', 'Gabriel Cedrés', 'Antonio Pacheco', 'Darío Silva'], ans: 0, exp: 'Pablo "El Profesor" Bengoechea fue el capitán y arquitecto del Quinquenio 93-97.' },
    { cat: 'idolos', catName: 'Ídolos Eternos', q: '¿Qué ídolo moderno disputó 475 partidos oficiales con Peñarol en el siglo XXI y conquistó 8 títulos de Campeón Uruguayo?', opts: ['Antonio "Tony" Pacheco', 'Marcelo Zalayeta', 'Darío Rodríguez', 'Cristian "Cebolla" Rodríguez'], ans: 0, exp: 'Antonio "Tony" Pacheco vistió la aurinegra en 475 encuentros oficiales.' },
    { cat: 'libertadores', catName: 'Copas Libertadores', q: '¿Quién anotó el primer gol de la historia de la Copa Libertadores el 19 de abril de 1960 en la goleada 7-1 de Peñarol a Jorge Wilstermann?', opts: ['Carlos "Lucho" Borges', 'Alberto Spencer', 'Luis Cubilla', 'José Sasía'], ans: 0, exp: 'Carlos "Lucho" Borges abrió la cuenta a los 13 minutos, convirtiendo el primer gol de la historia de la Copa Libertadores.' },
    { cat: 'records', catName: 'Récords & Hazañas', q: '¿Cuál es el récord histórico de partidos oficiales invicto en el Campeonato Uruguayo que ostenta Peñarol?', opts: ['56 partidos consecutivos invicto (1966-1969)', '42 partidos consecutivos invicto', '34 partidos consecutivos invicto', '62 partidos consecutivos invicto'], ans: 0, exp: 'Entre 1966 y 1969, Peñarol hilvanó 56 partidos consecutivos sin conocer la derrota en el Campeonato Uruguayo.' },
    { cat: 'libertadores', catName: 'Copas Libertadores', q: '¿En qué final épica de Copa Libertadores Peñarol perdía 0-2 en Santiago y terminó consagrándose campeón con remontada 4-2 ante River Plate argentino?', opts: ['Final de 1966 en Santiago de Chile', 'Final de 1961 en San Pablo', 'Final de 1982 en Santiago', 'Final de 1960 en Asunción'], ans: 0, exp: 'El 20 de mayo de 1966 en Santiago, Peñarol remontó un 0-2 para ganar 4-2 en tiempo extra con goles de Spencer (2), Abbadie y Rocha.' }
  ];

  // ==================== SEGURIDAD XSS, SANITIZACIÓN & UTILIDADES ====================
  function escapeHtml(value) {
    if (value === null || value === undefined) return '';
    return String(value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function safeUrl(rawUrl, fallback = '#') {
    if (typeof rawUrl !== 'string') return fallback;
    const trimmed = rawUrl.trim();
    if (!trimmed) return fallback;
    // Bloquear esquemas peligrosos, caracteres de control y rutas protocol-relative
    if (/[\u0000-\u001F\u007F]/.test(trimmed)) return fallback;
    if (/^(javascript|vbscript|data|file):/i.test(trimmed)) return fallback;
    if (trimmed.startsWith('//')) return fallback;

    if (trimmed.startsWith('#')) {
      return /^#[a-zA-Z0-9_-]+$/.test(trimmed) ? trimmed : fallback;
    }
    if (/^https?:\/\//i.test(trimmed)) {
      try {
        const parsed = new URL(trimmed);
        if (parsed.protocol === 'https:' || parsed.protocol === 'http:') {
          return parsed.href;
        }
      } catch (_) {
        return fallback;
      }
      return fallback;
    }
    // Rutas relativas locales seguras (sin ../)
    if (/^(\/)?(assets|data|css|js|index\.html|llms\.txt|manifest\.json)[a-zA-Z0-9._/?=&%-]*$/i.test(trimmed) && !trimmed.includes('..')) {
      return trimmed;
    }
    return fallback;
  }

  function safeImgSrc(rawSrc, fallback = 'assets/img/escudo_penarol_oficial.svg') {
    return safeUrl(rawSrc, fallback);
  }

  function normalizeText(value) {
    return String(value || '')
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim();
  }

  function showToast(message, type = 'gold') {
    if (!message) return;
    let region = document.getElementById('manya-toast-region');
    if (!region) {
      region = document.createElement('div');
      region.id = 'manya-toast-region';
      region.className = 'manya-toast-region';
      region.setAttribute('role', 'status');
      region.setAttribute('aria-live', 'polite');
      region.setAttribute('aria-atomic', 'true');
      document.body.appendChild(region);
    }
    while (region.children.length >= 3) {
      region.removeChild(region.firstChild);
    }
    const toast = document.createElement('div');
    const variant = ['success', 'warning', 'info', 'gold'].includes(type) ? type : 'gold';
    toast.className = `manya-toast toast-${variant}`;
    toast.textContent = String(message);
    region.appendChild(toast);

    setTimeout(() => {
      toast.classList.add('is-hiding');
      setTimeout(() => {
        if (toast.parentNode) toast.parentNode.removeChild(toast);
      }, 260);
    }, 3200);
  }

  function enhanceLazyImages(root) {
    if (!root) return;
    const imgs = root.querySelectorAll('img');
    imgs.forEach(img => {
      const wrap = img.closest('.ig-img-wrap, .ig-post-media-wrap, .tattoo-img-wrap');
      const fallbackSrc = img.getAttribute('data-fallback-src');

      if (fallbackSrc) {
        img.addEventListener('error', () => {
          if (img.dataset.fallbackApplied) return;
          img.dataset.fallbackApplied = '1';
          img.src = safeImgSrc(fallbackSrc);
        });
      }

      if (img.getAttribute('loading') !== 'lazy' && !img.classList.contains('manya-lazy-img')) return;
      img.classList.add('manya-lazy-img');

      const markLoaded = () => {
        img.classList.remove('is-loading');
        img.classList.add('is-loaded');
        if (wrap) wrap.classList.remove('is-loading');
      };

      if (img.complete && img.naturalWidth > 0) {
        markLoaded();
      } else {
        img.classList.add('is-loading');
        if (wrap) wrap.classList.add('is-loading');
        img.addEventListener('load', markLoaded, { once: true });
        img.addEventListener('error', () => {
          if (fallbackSrc && !img.dataset.fallbackApplied) {
            img.dataset.fallbackApplied = '1';
            img.src = safeImgSrc(fallbackSrc);
          } else {
            markLoaded();
          }
        }, { once: true });
      }
    });
  }

  async function loadJsonSafe(path) {
    try {
      const r = await fetch(path + '?v=' + APP_VERSION + '_' + Math.floor(Date.now() / 60000));
      if (!r.ok) return null;
      return await r.json();
    } catch (_) {
      return null;
    }
  }

  function parseDgInt(dg) {
    const n = parseInt(String(dg || '0').replace('+', ''), 10);
    return isNaN(n) ? 0 : n;
  }

  function startCountdown(isoString) {
    if (!isoString) return;
    const target = new Date(isoString).getTime();
    if (isNaN(target)) return;

    if (window._manyaCountdownInterval) clearInterval(window._manyaCountdownInterval);

    function tick() {
      const diff = Math.max(0, target - Date.now());
      const d = Math.floor(diff / 86400000);
      const h = Math.floor((diff % 86400000) / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = String(v).padStart(2, '0'); };
      set('cd-days', d);
      set('cd-hours', h);
      set('cd-mins', m);
      set('cd-secs', s);
    }
    tick();
    window._manyaCountdownInterval = setInterval(tick, 1000);
  }

  function isMatchToday(fechaIso) {
    if (!fechaIso) return false;
    try {
      const now = new Date();
      const nowUy = new Date(now.getTime() + (now.getTimezoneOffset() * 60000) - (3 * 3600000));
      const matchDate = new Date(fechaIso);
      const matchUy = new Date(matchDate.getTime() + (matchDate.getTimezoneOffset() * 60000) - (3 * 3600000));
      return nowUy.getFullYear() === matchUy.getFullYear() &&
             nowUy.getMonth() === matchUy.getMonth() &&
             nowUy.getDate() === matchUy.getDate();
    } catch (_) {
      return false;
    }
  }

  function resolveClubCrest(team) {
    if (!team) return 'assets/img/escudos/escudo_auf.svg';
    const rawName = (team.nombre || team.equipo || '').toLowerCase();
    if (team.es_penarol || rawName.includes('peñarol') || rawName.includes('penarol')) {
      return 'assets/img/escudos/escudo_penarol.webp';
    }
    if (team.escudo && (team.escudo.startsWith('assets/img/escudos/') || /\.(webp|png|svg)$/i.test(team.escudo))) {
      return safeImgSrc(team.escudo, 'assets/img/escudos/escudo_auf.svg');
    }

    const norm = rawName.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9 ]/g, '').trim();
    if (state.escudosCatalog && state.escudosCatalog.alias_index) {
      const slug = state.escudosCatalog.alias_index[norm];
      if (slug && state.escudosCatalog.clubes && state.escudosCatalog.clubes[slug]) {
        const candidate = state.escudosCatalog.clubes[slug].ruta_webp || state.escudosCatalog.clubes[slug].escudo;
        return safeImgSrc(candidate, 'assets/img/escudos/escudo_auf.svg');
      }
    }

    const directMap = [
      ['cerro largo', 'escudo_cerro_largo.webp'],
      ['cerro porteno', 'escudo_cerro_porteno.webp'],
      ['cerro', 'escudo_cerro.webp'],
      ['defensor', 'escudo_defensor_sporting.webp'],
      ['wanderers', 'escudo_montevideo_wanderers.webp'],
      ['liverpool', 'escudo_liverpool.webp'],
      ['racing', 'escudo_racing.webp'],
      ['nacional', 'escudo_nacional.webp'],
      ['danubio', 'escudo_danubio.webp'],
      ['boston', 'escudo_boston_river.webp'],
      ['progreso', 'escudo_progreso.webp'],
      ['maldonado', 'escudo_deportivo_maldonado.webp'],
      ['torque', 'escudo_montevideo_city_torque.webp'],
      ['albion', 'escudo_albion.webp'],
      ['central', 'escudo_central_espanol.webp'],
      ['juventud', 'escudo_juventud.webp'],
      ['miramar', 'escudo_miramar_misiones.webp'],
      ['corinthians', 'escudo_corinthians.webp'],
      ['platense', 'escudo_platense.webp'],
      ['santa fe', 'escudo_independiente_santa_fe.webp'],
      ['flamengo', 'escudo_flamengo.webp'],
      ['palmeiras', 'escudo_palmeiras.webp'],
      ['boca', 'escudo_boca_juniors.webp'],
      ['estudiantes', 'escudo_estudiantes.webp']
    ];
    for (const [kw, file] of directMap) {
      if (norm.includes(kw)) return 'assets/img/escudos/' + file;
    }
    if (team.logo && /^https?:\/\//i.test(team.logo)) return safeImgSrc(team.logo, 'assets/img/escudos/escudo_auf.svg');
    return 'assets/img/escudos/escudo_auf.svg';
  }

  // ==================== MATCH CENTER ====================
  function renderMatchHero(live) {
    if (!live) return;
    const fase = live.fase_partido || 'PREVIA';
    const act = live.partido_activo || {};
    const prox = live.proximo_partido || {};
    const resTemp = live.resumen_temporada || {};
    const w = live.clima_campeon_del_siglo || {};

    const featured = (fase === 'EN_VIVO' || fase === 'POST_PARTIDO' || live.estado_ciclo_vida === 'POST_48H')
      ? (act.local ? act : prox)
      : (prox.local ? prox : act);

    const wEl = document.getElementById('hero-weather');
    if (wEl && w.temperatura_c !== undefined) {
      wEl.textContent = `🌡️ Campeón del Siglo: ${w.temperatura_c}°C • ${w.condicion || 'Despejado'} (Viento ${w.viento_kmh || 12} km/h)`;
    }

    const loc = featured.local || { nombre: 'Peñarol', es_penarol: true, goles: '-' };
    const vis = featured.visitante || { nombre: 'Rival', es_penarol: false, goles: '-' };

    const tHome = document.getElementById('hero-home-name');
    const tAway = document.getElementById('hero-away-name');
    const tHomeCrest = document.getElementById('hero-home-crest');
    const tAwayCrest = document.getElementById('hero-away-crest');
    const tHomeWrap = document.getElementById('hero-home-crest-wrap');
    const tAwayWrap = document.getElementById('hero-away-crest-wrap');
    const tHomeTag = document.getElementById('hero-home-tag');
    const tAwayTag = document.getElementById('hero-away-tag');
    const tDate = document.getElementById('hero-match-date');
    const tVenue = document.getElementById('hero-match-venue');
    const tScorers = document.getElementById('hero-scorers-strip');
    const heroBadge = document.getElementById('hero-match-badge');
    const cdGrid = document.getElementById('hero-countdown-grid');
    const liveScoreBox = document.getElementById('hero-live-score-container');
    const liveStatusPill = document.getElementById('hero-score-status-pill');
    const sHome = document.getElementById('hero-live-score-home');
    const sAway = document.getElementById('hero-live-score-away');

    if (tHome) {
      tHome.textContent = loc.nombre;
      tHome.className = 'match-team-name ' + (loc.es_penarol ? 'is-penarol' : '');
    }
    if (tHomeCrest) {
      tHomeCrest.src = resolveClubCrest(loc);
      tHomeCrest.alt = 'Escudo Oficial de ' + loc.nombre;
    }
    if (tHomeWrap) tHomeWrap.className = 'hero-crest-wrap ' + (loc.es_penarol ? 'is-penarol' : 'is-rival');
    if (tHomeTag) tHomeTag.textContent = loc.es_penarol ? 'Local • El Decano 1891' : 'Local • Torneo Oficial AUF';

    if (tAway) {
      tAway.textContent = vis.nombre;
      tAway.className = 'match-team-name ' + (vis.es_penarol ? 'is-penarol' : '');
    }
    if (tAwayCrest) {
      tAwayCrest.src = resolveClubCrest(vis);
      tAwayCrest.alt = 'Escudo Oficial de ' + vis.nombre;
    }
    if (tAwayWrap) tAwayWrap.className = 'hero-crest-wrap ' + (vis.es_penarol ? 'is-penarol' : 'is-rival');
    if (tAwayTag) tAwayTag.textContent = vis.es_penarol ? 'Visitante • El Decano 1891' : 'Visitante • Torneo Oficial AUF';

    if (fase === 'EN_VIVO') {
      if (cdGrid) cdGrid.style.display = 'none';
      if (liveScoreBox) liveScoreBox.style.display = 'flex';
      if (liveStatusPill) liveStatusPill.textContent = `🔴 EN VIVO • ${featured.minuto_reloj || '1T'}`;
      if (sHome) sHome.textContent = loc.goles ?? '0';
      if (sAway) sAway.textContent = vis.goles ?? '0';
      if (heroBadge) {
        heroBadge.textContent = `🔴 EN VIVO • ${(featured.torneo || 'CAMPEONATO URUGUAYO').toUpperCase()}`;
        heroBadge.style.background = '#ef4444';
        heroBadge.style.color = '#ffffff';
      }
      if (tDate) {
        tDate.textContent = `🔴 EN DIRECTO (${featured.minuto_reloj || '1T'}) • ${featured.torneo || 'Campeonato Uruguayo'}`;
        tDate.style.color = '#f87171';
      }
    } else if (fase === 'POST_PARTIDO' || live.estado_ciclo_vida === 'POST_48H') {
      if (cdGrid) cdGrid.style.display = 'none';
      if (liveScoreBox) liveScoreBox.style.display = 'flex';
      if (liveStatusPill) liveStatusPill.textContent = resTemp.campeon_anual ? '🏁 FINAL • CAMPEÓN ANUAL' : '🏁 FINALIZADO';
      if (sHome) sHome.textContent = loc.goles ?? '-';
      if (sAway) sAway.textContent = vis.goles ?? '-';
      if (heroBadge) {
        heroBadge.textContent = `🏁 RESULTADO FINAL • ${(featured.torneo || 'CAMPEONATO URUGUAYO').toUpperCase()}`;
        heroBadge.style.background = '#10b981';
        heroBadge.style.color = '#052e16';
      }
      if (tDate) {
        tDate.textContent = `🏁 FINALIZADO • ${featured.fecha_legible || ''} • ${featured.torneo || ''}`;
        tDate.style.color = '#34d399';
      }
    } else {
      if (cdGrid) cdGrid.style.display = 'grid';
      if (liveScoreBox) liveScoreBox.style.display = 'none';
      const esHoyReal = featured.es_hoy === true && isMatchToday(featured.fecha_iso);
      if (heroBadge) {
        heroBadge.textContent = (esHoyReal ? '🟡⚫ ¡HOY JUEGA PEÑAROL! • ' : '★ PRÓXIMO PARTIDO • ') + (featured.torneo || 'CAMPEONATO URUGUAYO').toUpperCase();
        heroBadge.style.background = '#ffd100';
        heroBadge.style.color = '#09090b';
      }
      if (tDate) {
        tDate.textContent = `${esHoyReal ? '🟡⚫ HOY' : '★ PRÓXIMO'} • ${featured.fecha_legible || ''} • ${featured.torneo || ''}`;
        tDate.style.color = 'var(--manya-gold)';
      }
      startCountdown(featured.fecha_iso);
    }

    if (tVenue) tVenue.textContent = `🏟️ ${featured.estadio || 'Estadio Campeón del Siglo'}` + (featured.juez ? ` • Árbitro: ${featured.juez}` : '');

    if (tScorers) {
      if (featured.goles_texto) {
        tScorers.style.display = 'inline-flex';
        tScorers.textContent = `⚽ Goles: ${featured.goles_texto}`;
      } else {
        tScorers.style.display = 'none';
      }
    }

    const pts = resTemp.penarol_anual_pts || 69;
    const dg = resTemp.penarol_anual_dg || '+27';
    const pj = resTemp.penarol_anual_pj || 37;
    const defInfo = resTemp.definicion_uruguayo || {};

    const meta1 = document.getElementById('hero-meta-box-1');
    if (meta1) {
      if (prox.es_definicion_final) {
        meta1.innerHTML = `<span>🏆 Próximo Horizonte • Gran Final</span><strong>${escapeHtml(prox.nombre)}</strong> — ${escapeHtml(prox.fecha_legible)}. Semifinal: ${escapeHtml(defInfo.semifinal || 'Racing vs Liverpool')} (${escapeHtml(defInfo.fecha_semifinal || '29/11')}).`;
      } else {
        meta1.innerHTML = `<span>🎟️ Próximo Compromiso &amp; Sede</span><strong>${escapeHtml(prox.nombre || featured.nombre)}</strong> en ${escapeHtml(prox.estadio || featured.estadio)} (${escapeHtml(prox.fecha_legible || '')}).`;
      }
    }

    const meta2 = document.getElementById('hero-meta-box-2');
    if (meta2) {
      const ytUrl = safeUrl(featured.video_youtube_url, '');
      if (ytUrl) {
        meta2.innerHTML = `<span>🎬 Resumen Oficial &amp; TV</span>Reviví los goles del triunfo en <a href="${escapeHtml(ytUrl)}" target="_blank" rel="noopener noreferrer" style="color:var(--manya-gold);font-weight:800;text-decoration:underline;">YouTube (1891 BD) ↗</a> • TV: <strong>${escapeHtml(featured.tv || 'VTV Plus / Disney+')}</strong>.`;
      } else {
        meta2.innerHTML = `<span>📺 Transmisión Oficial</span>En vivo para todo el país por <strong>${escapeHtml(featured.tv || 'VTV Plus / Disney+ Premium')}</strong>.`;
      }
    }

    const meta3 = document.getElementById('hero-meta-box-3');
    if (meta3) {
      const crown = resTemp.campeon_anual ? 'Campeón Tabla Anual' : `#${resTemp.penarol_anual_pos || 1} Tabla Anual`;
      meta3.innerHTML = `<span>🏆 Tabla Anual Oficial AUF</span><strong id="hero-last-result">Peñarol ${escapeHtml(pts)} pts (${escapeHtml(crown)})</strong> • ${escapeHtml(dg)} DG (${escapeHtml(pj)} PJ) • Libertadores 2027.`;
    }

    const tickerEl = document.getElementById('manya-live-ticker');
    const tickerTxt = document.getElementById('ticker-text');
    if (tickerEl) {
      if (live.alerta_banner) {
        tickerEl.style.display = 'flex';
        if (tickerTxt) tickerTxt.textContent = live.alerta_banner;
        tickerEl.style.borderColor = fase === 'EN_VIVO' ? '#ef4444' : '#ffd100';
      } else {
        tickerEl.style.display = 'none';
      }
    }

    renderRecentFormStrip(live);
    renderLiveTimeline(live);
    updateDynamicLogisticsAndTacticalTitles(live);

    const footerSync = document.getElementById('footer-last-sync');
    if (footerSync && live.actualizado) {
      footerSync.textContent = `Última sincronización automática: ${live.actualizado} (UY)`;
    }
  }

  function renderRecentFormStrip(live) {
    const box = document.getElementById('historico-partido-anterior');
    if (!box) return;
    const recent = live.ultimos_resultados || [];
    if (!recent.length) return;

    const pills = recent.slice(0, 5).map(m => {
      const loc = m.local || {};
      const vis = m.visitante || {};
      const gLoc = parseInt(loc.goles, 10);
      const gVis = parseInt(vis.goles, 10);
      const gPen = loc.es_penarol ? gLoc : gVis;
      const gRiv = loc.es_penarol ? gVis : gLoc;
      const rivNom = loc.es_penarol ? vis.nombre : loc.nombre;
      let cls = 'is-draw', code = 'E';
      if (!isNaN(gPen) && !isNaN(gRiv)) {
        if (gPen > gRiv) { cls = 'is-win'; code = 'V'; }
        else if (gPen < gRiv) { cls = 'is-loss'; code = 'D'; }
      }
      const tooltip = `${m.fecha_legible || ''} • ${m.estadio || ''}`;
      return `<span class="form-pill ${cls}" title="${escapeHtml(tooltip)}"><strong>${code}</strong> ${escapeHtml(isNaN(gPen) ? '-' : gPen)}-${escapeHtml(isNaN(gRiv) ? '-' : gRiv)} vs ${escapeHtml(rivNom)}</span>`;
    }).join('');

    const summaryEl = document.getElementById('recent-form-summary');
    if (summaryEl) {
      summaryEl.innerHTML = `<div style="font-size:12.5px;color:#d4d4d8;margin-bottom:6px;"><strong>Últimos 5 partidos oficiales (ESPN / 1891 BD):</strong></div><div class="recent-form-strip">${pills}</div>`;
    }
  }

  function renderLiveTimeline(live) {
    const card = document.getElementById('match-center-live-card');
    const feed = document.getElementById('live-timeline-feed');
    if (!card || !feed) return;

    const eventos = live.minuto_a_minuto || [];
    if (!eventos.length) {
      card.style.display = 'none';
      return;
    }

    card.style.display = 'block';
    const act = live.partido_activo || live.ultimo_partido || {};
    const titleEl = document.getElementById('timeline-card-title');
    if (titleEl && act.nombre) {
      titleEl.textContent = `⏱️ Minuto a Minuto & Síntesis: ${act.nombre}`;
    }

    feed.innerHTML = eventos.slice().reverse().map(e => {
      const titulo = e.titulo || 'Incidencia del partido';
      const desc = e.descripcion || e.texto || '';
      return `
        <div style="display:flex;gap:12px;padding:10px 12px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-left:3px solid var(--manya-gold);border-radius:8px;">
          <div style="flex-shrink:0;width:54px;text-align:center;">
            <span style="background:var(--manya-gold);color:#09090b;font-weight:900;font-size:11px;padding:2px 7px;border-radius:999px;display:inline-block;">${escapeHtml(e.minuto || '•')}</span>
          </div>
          <div style="flex-grow:1;min-width:0;">
            <div style="font-weight:800;color:#ffffff;font-size:13.5px;margin-bottom:2px;">${escapeHtml(e.icono || '⚡')} ${escapeHtml(titulo)}</div>
            <div style="font-size:12.5px;color:#d4d4d8;line-height:1.45;">${escapeHtml(desc)}</div>
          </div>
        </div>
      `;
    }).join('');
  }

  function updateDynamicLogisticsAndTacticalTitles(live) {
    const prox = live.proximo_partido || {};
    const resTemp = live.resumen_temporada || {};
    const pTitle = document.getElementById('pizarra-title');
    const pSub = document.getElementById('pizarra-subtitle');
    if (pTitle && pSub) {
      if (prox.es_definicion_final) {
        pTitle.innerHTML = `👕 Pizarra Táctica: <span>Armá tu 11 para la Gran Final 2026</span>`;
        pSub.textContent = `Plantel real noviembre 2026 • Armá el once titular de Diego Aguirre para la definición del Campeonato Uruguayo (3 y 6 de diciembre).`;
      } else {
        pTitle.innerHTML = `👕 Pizarra Táctica: <span>Armá tu 11 • ${escapeHtml(prox.nombre || 'Peñarol')}</span>`;
        pSub.textContent = `Plantel vigente 2026 • Armá tu alineación ideal para ${prox.estadio || 'el próximo partido'} (${prox.fecha_legible || ''}).`;
      }
    }

    const logBox = document.getElementById('como-llegar-dinamico');
    if (logBox && prox.es_definicion_final) {
      logBox.innerHTML = `
        <div style="display:inline-block;background:var(--manya-gold);color:#000;font-size:10px;font-weight:900;padding:2px 8px;border-radius:999px;margin-bottom:6px;text-transform:uppercase;">Definición Uruguayo 2026 • Finales</div>
        <h3 style="font-size:16px;color:var(--manya-gold);margin-bottom:8px;">🏟️ Operativo Finales en el Estadio Campeón del Siglo</h3>
        <p style="font-size:13.5px;color:#d4d4d8;margin-bottom:12px;">Peñarol (Campeón Anual con ${escapeHtml(resTemp.penarol_anual_pts || 69)} pts) disputará la Gran Final ida y vuelta el 3 y 6 de diciembre ante el ganador de Racing vs Liverpool.</p>
        <ul style="font-size:13.5px;color:#e4e4e7;padding-left:18px;margin-bottom:14px;">
          <li><strong>Ingreso Vehicular:</strong> Accesos por Ruta 102 y Camino Mangangá con apertura recomendada 2 horas antes del pitazo inicial.</li>
          <li><strong>Servicios Especiales:</strong> Refuerzos CUTCSA directo "Estadio Campeón del Siglo" desde Tres Cruces, Centro y Belloni.</li>
        </ul>
        <a href="https://horarios.servicioti.com.uy/" target="_blank" rel="noopener noreferrer" class="btn-outline-gold" style="font-size:12.5px;">Consultar Horarios en Vivo en Horarios ServicioTI ↗</a>
      `;
    }
  }

  // ==================== TABLAS OFICIALES & SIMULADOR ====================
  function renderStandingsTabs() {
    const container = document.getElementById('standings-tabs-container');
    if (!container || !state.live) return;

    const tabs = (state.live.tablas_campeonatos && state.live.tablas_campeonatos.length)
      ? state.live.tablas_campeonatos
      : [
          { id: 'anual', nombre: 'Tabla Anual Acumulada Oficial (AUF)', nombre_corto: 'Tabla Anual', icono: '🏆', badge: 'Oficial AUF' },
          { id: 'clausura', nombre: 'Torneo Clausura 2026', nombre_corto: 'Torneo Clausura', icono: '⚽', badge: 'Clausura' },
          { id: 'libertadores', nombre: 'Copa CONMEBOL Libertadores', nombre_corto: 'Copa Libertadores', icono: '🌎', badge: 'CONMEBOL' }
        ];

    if (!state.standingsTab || !tabs.some(t => t.id === state.standingsTab)) {
      state.standingsTab = state.live.torneo_activo_id || 'anual';
    }

    container.setAttribute('role', 'tablist');
    container.innerHTML = tabs.map(t => {
      const isActive = t.id === state.standingsTab;
      const badgeHtml = t.badge ? `<span class="pill-badge">${escapeHtml(t.badge)}</span>` : '';
      return `<button type="button" role="tab" aria-selected="${isActive ? 'true' : 'false'}" class="standings-pill ${isActive ? 'active' : ''}" data-tab="${escapeHtml(t.id)}"><span>${escapeHtml(t.icono || '🏆')} ${escapeHtml(t.nombre_corto || t.nombre)}</span>${badgeHtml}</button>`;
    }).join('');

    container.querySelectorAll('.standings-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        const tabId = btn.getAttribute('data-tab');
        if (tabId && tabId !== state.standingsTab) {
          state.standingsTab = tabId;
          renderStandingsTabs();
          renderStandings();
        }
      });
    });
  }

  function renderStandings() {
    if (!state.live) return;
    const tbody = document.getElementById('standings-tbody');
    if (!tbody) return;

    const resTemp = state.live.resumen_temporada || {};
    const ptsAnual = resTemp.penarol_anual_pts || 69;
    const dgAnual = resTemp.penarol_anual_dg || '+27';
    const tabs = state.live.tablas_campeonatos || [];
    const activeTourn = tabs.find(t => t.id === state.standingsTab) || tabs[0] || { id: 'anual', nombre: 'Tabla Anual Oficial (AUF)', icono: '🏆' };

    const titleEl = document.getElementById('standings-table-title');
    const badgeEl = document.getElementById('standings-context-badge');
    const subInfoEl = document.getElementById('standings-sub-info');

    if (titleEl) titleEl.textContent = `${activeTourn.icono || '🏆'} ${activeTourn.nombre}`;
    if (badgeEl) {
      badgeEl.textContent = activeTourn.id === 'anual' ? 'OFICIAL AUF' : (activeTourn.id === 'libertadores' ? 'CONMEBOL' : 'CLAUSURA 2026');
    }

    if (subInfoEl) {
      if (activeTourn.id === 'anual') {
        subInfoEl.innerHTML = `<strong>🏆 TABLA ANUAL ACUMULADA (AUF):</strong> <strong style="color:var(--manya-gold);">Peñarol ${resTemp.campeon_anual ? 'CAMPEÓN ANUAL' : 'líder'} con ${escapeHtml(ptsAnual)} puntos (${escapeHtml(dgAnual)} DG)</strong> — Clasificado directo a la Gran Final del Uruguayo y Copa Libertadores 2027.`;
      } else if (activeTourn.id === 'clausura') {
        subInfoEl.innerHTML = `<strong>⚽ TORNEO CLAUSURA 2026:</strong> Clasificación oficial del certamen corto (15 fechas). Peñarol cerró con ${escapeHtml(resTemp.penarol_clausura_pts || 26)} pts en ${escapeHtml(resTemp.penarol_clausura_pj || 15)} PJ.`;
      } else {
        subInfoEl.innerHTML = `<strong>🌎 COPA CONMEBOL LIBERTADORES:</strong> Tabla oficial ordenada por posición, puntos y diferencia de goles.`;
      }
    }

    const sourceData = (activeTourn && activeTourn.datos && activeTourn.datos.length)
      ? activeTourn.datos
      : (state.standingsTab === 'clausura' ? (state.live.tabla_clausura || []) : (state.standingsTab === 'libertadores' ? (state.live.tabla_libertadores || []) : (state.live.tabla_anual || [])));

    const rows = sourceData.map(r => {
      const isPen = r.es_penarol || (r.equipo && r.equipo.toLowerCase().includes('peñarol'));
      const delta = (isPen && state.standingsTab !== 'libertadores') ? state.simPointsDelta : 0;
      return Object.assign({}, r, { es_penarol: isPen, pts_calc: (r.pts || 0) + delta, pj_calc: (r.pj || 0) + (delta > 0 ? Math.ceil(delta / 3) : 0) });
    });

    rows.sort((a, b) => (b.pts_calc - a.pts_calc) || (parseDgInt(b.dg) - parseDgInt(a.dg)) || ((b.gf || 0) - (a.gf || 0)));

    const fallbackCrest = state.standingsTab === 'libertadores' ? 'assets/img/escudos/escudo_conmebol.svg' : 'assets/img/escudos/escudo_auf.svg';
    tbody.innerHTML = rows.map((r, i) => {
      const crest = resolveClubCrest({ nombre: r.equipo, es_penarol: r.es_penarol, logo: r.logo, escudo: r.escudo });
      const rowClass = r.es_penarol ? 'row-penarol' : '';
      const tagExtra = r.es_penarol ? '<span style="color:var(--manya-gold);font-weight:900;margin-left:4px;">★</span>' : '';
      const ptsClass = r.es_penarol ? 'pts-pill is-leader' : 'pts-pill';
      return `
        <tr class="${rowClass}">
          <td class="col-pos">${i + 1}</td>
          <td class="col-team">
            <div style="display:flex;align-items:center;gap:6px;">
              <img src="${escapeHtml(crest)}" data-fallback-src="${escapeHtml(fallbackCrest)}" alt="${escapeHtml(r.equipo)}" width="18" height="18" style="object-fit:contain;border-radius:2px;flex-shrink:0;" />
              <span class="team-name-label">${escapeHtml(r.equipo)}</span>${tagExtra}
            </div>
          </td>
          <td class="col-stat col-pj">${escapeHtml(r.pj_calc)}</td>
          <td class="col-stat col-pg">${escapeHtml(r.pg)}</td>
          <td class="col-stat col-pe">${escapeHtml(r.pe)}</td>
          <td class="col-stat col-pp">${escapeHtml(r.pp)}</td>
          <td class="col-stat col-dg">${escapeHtml(r.dg)}</td>
          <td class="col-pts"><span class="${ptsClass}">${escapeHtml(r.pts_calc)}</span></td>
        </tr>
      `;
    }).join('');

    enhanceLazyImages(tbody);

    const btnToggle = document.getElementById('btn-toggle-cols');
    const tableEl = document.querySelector('.manya-table');
    if (btnToggle && tableEl) {
      btnToggle.onclick = () => {
        const isExpanded = tableEl.classList.toggle('show-all-cols');
        btnToggle.innerHTML = isExpanded ? '<span>◀ Vista Compacta (PJ/DG/PTS)</span>' : '<span>👁️ Ver Detalle (PG/PE/PP)</span>';
      };
    }
  }

  function initSimulator() {
    const container = document.getElementById('sim-matches-box');
    const titleEl = document.getElementById('sim-panel-title');
    const descEl = document.getElementById('sim-panel-desc');
    const resetBtn = document.getElementById('sim-reset-btn');
    if (!container || !state.live) return;

    const resTemp = state.live.resumen_temporada || {};
    const prox = state.live.proximo_partido || {};

    if (resTemp.campeon_anual || prox.es_definicion_final) {
      if (titleEl) titleEl.textContent = '🏆 Definición del Campeonato Uruguayo 2026';
      if (descEl) descEl.textContent = `Peñarol ganó la Tabla Anual (${resTemp.penarol_anual_pts || 69} pts) y espera directamente en las Finales. Proyectá tu camino al título:`;
      if (resetBtn) resetBtn.style.display = 'none';

      const def = resTemp.definicion_uruguayo || {};
      const savedPick = (() => {
        try {
          const val = localStorage.getItem('manya_final_rival_pick');
          return (val === 'Racing' || val === 'Liverpool') ? val : 'Liverpool';
        } catch (_) {
          return 'Liverpool';
        }
      })();
      let rivalPick = savedPick;

      const renderBracket = () => {
        container.innerHTML = `
          <div class="playoff-bracket-card">
            <div style="font-size:11.5px;font-weight:900;color:var(--manya-gold);letter-spacing:0.05em;text-transform:uppercase;">✅ OBJETIVOS YA CUMPLIDOS POR PEÑAROL</div>
            <ul style="font-size:12.5px;color:#e4e4e7;margin:8px 0 0 18px;line-height:1.55;">
              <li><strong>Campeón de la Tabla Anual 2026</strong> (${escapeHtml(resTemp.penarol_anual_pts || 69)} pts • ${escapeHtml(resTemp.penarol_anual_dg || '+27')} DG).</li>
              <li><strong>Clasificado directo a Fase de Grupos</strong> de Copa Libertadores 2027 (Uruguay 1).</li>
              <li><strong>Pase directo a la Gran Final</strong> (ida y vuelta) sin disputar semifinal.</li>
            </ul>
          </div>
          <div class="playoff-step">
            <div style="font-size:11px;color:var(--manya-gold);font-weight:800;text-transform:uppercase;">1. SEMIFINAL (CAMPEONES CORTOS) • ${escapeHtml(def.fecha_semifinal || '29/11/2026')}</div>
            <div style="font-size:13.5px;font-weight:800;color:#fff;margin:4px 0;">${escapeHtml(def.semifinal || 'Racing (Apertura) vs Liverpool (Clausura)')}</div>
            <div style="font-size:12px;color:#a1a1aa;margin-bottom:8px;">¿Quién creés que avanzará para enfrentar a Peñarol?</div>
            <div class="sim-btns">
              <button type="button" class="sim-btn ${rivalPick === 'Racing' ? 'active' : ''}" aria-pressed="${rivalPick === 'Racing' ? 'true' : 'false'}" data-pick="Racing">Racing (Apertura)</button>
              <button type="button" class="sim-btn ${rivalPick === 'Liverpool' ? 'active' : ''}" aria-pressed="${rivalPick === 'Liverpool' ? 'true' : 'false'}" data-pick="Liverpool">Liverpool (Clausura)</button>
            </div>
          </div>
          <div class="playoff-step" style="border-left-color:#10b981;">
            <div style="font-size:11px;color:#34d399;font-weight:800;text-transform:uppercase;">2. GRAN FINAL DEL CAMPEONATO URUGUAYO (IDA Y VUELTA)</div>
            <div style="font-size:14px;font-weight:900;color:#fff;margin:4px 0;">★ Peñarol vs ${escapeHtml(rivalPick)}</div>
            <div style="font-size:12px;color:#d4d4d8;line-height:1.45;">Ida tentativa: <strong>Jueves 3 de diciembre</strong> • Vuelta definitiva: <strong>Domingo 6 de diciembre de 2026</strong> (localías a sortear).</div>
          </div>
        `;
        container.querySelectorAll('[data-pick]').forEach(b => {
          b.addEventListener('click', () => {
            const pick = b.getAttribute('data-pick');
            if (pick === 'Racing' || pick === 'Liverpool') {
              rivalPick = pick;
              try { localStorage.setItem('manya_final_rival_pick', rivalPick); } catch (_) {}
              renderBracket();
              showToast(`🏆 Gran Final proyectada: Peñarol vs ${rivalPick}`, 'info');
            }
          });
        });
      };
      renderBracket();
      return;
    }

    if (resetBtn) resetBtn.style.display = 'inline-flex';
    const proxList = (state.live.proximos_partidos && state.live.proximos_partidos.length)
      ? state.live.proximos_partidos.slice(0, 3).map((m, i) => ({ id: i + 1, label: `${m.nombre} (${m.estadio || ''})` }))
      : [{ id: 1, label: `${prox.nombre || 'Próximo Partido Peñarol'} (${prox.estadio || ''})` }];

    const picks = {};
    proxList.forEach(f => { picks[f.id] = 0; });

    function updateSim() {
      state.simPointsDelta = Object.values(picks).reduce((a, b) => a + b, 0);
      const ptsEl = document.getElementById('sim-delta-label');
      if (ptsEl) {
        ptsEl.textContent = state.simPointsDelta > 0
          ? `+${state.simPointsDelta} pts proyectados para Peñarol`
          : 'Tabla actual oficial (sin proyección)';
      }
      renderStandings();
    }

    container.innerHTML = proxList.map(f => `
      <div class="sim-row" data-fid="${escapeHtml(f.id)}">
        <span><strong>${escapeHtml(f.label)}</strong></span>
        <div class="sim-btns">
          <button type="button" class="sim-btn" data-pts="3">Gana (+3)</button>
          <button type="button" class="sim-btn" data-pts="1">Empata (+1)</button>
          <button type="button" class="sim-btn" data-pts="0">Pierde (0)</button>
        </div>
      </div>
    `).join('');

    container.querySelectorAll('.sim-row').forEach(row => {
      const fid = row.getAttribute('data-fid');
      row.querySelectorAll('.sim-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          row.querySelectorAll('.sim-btn').forEach(b => b.classList.remove('active'));
          btn.classList.add('active');
          picks[fid] = parseInt(btn.getAttribute('data-pts'), 10);
          updateSim();
        });
      });
    });

    if (resetBtn) {
      resetBtn.onclick = () => {
        state.simPointsDelta = 0;
        Object.keys(picks).forEach(k => { picks[k] = 0; });
        container.querySelectorAll('.sim-btn').forEach(b => b.classList.remove('active'));
        updateSim();
        showToast('↺ Puntaje oficial restaurado', 'info');
      };
    }
  }

  // ==================== PIZARRA TÁCTICA PRO 2026 ====================
  function getPlayerLineGroup(player) {
    if (!player) return 'VOL';
    const pos = String(player.posicion || '').toUpperCase().trim();
    if (pos === 'ARQ' || pos === 'GK') return 'ARQ';
    if (['LD', 'LI', 'DFC', 'DF', 'DEF', 'CAR'].includes(pos)) return 'DEF';
    if (['MCD', 'MC', 'MD', 'MI', 'MCO', 'VOL', 'MED'].includes(pos)) return 'VOL';
    if (['ED', 'EI', 'SD', 'DC', 'DEL', 'ATA', 'EXT'].includes(pos)) return 'ATA';
    const linea = normalizeText(player.linea);
    if (linea.includes('portero') || linea.includes('arq')) return 'ARQ';
    if (linea.includes('def')) return 'DEF';
    if (linea.includes('vol') || linea.includes('med')) return 'VOL';
    return 'ATA';
  }

  function orderLineupForPitch(players11) {
    const slotOrder = [
      p => p.posicion === 'ARQ',
      p => p.posicion === 'LD',
      p => p.posicion === 'DFC',
      p => p.posicion === 'DFC',
      p => p.posicion === 'LI',
      p => p.posicion === 'MCD',
      p => p.posicion === 'MC',
      p => p.posicion === 'ED' || p.posicion === 'MD',
      p => p.posicion === 'MCO' || p.posicion === 'SD',
      p => p.posicion === 'EI' || p.posicion === 'MI',
      p => p.posicion === 'DC'
    ];
    const remaining = players11.slice(0, 11);
    const ordered = new Array(11).fill(null);

    slotOrder.forEach((pred, idx) => {
      const foundIdx = remaining.findIndex(pred);
      if (foundIdx !== -1) {
        ordered[idx] = remaining.splice(foundIdx, 1)[0];
      }
    });
    for (let i = 0; i < 11; i++) {
      if (!ordered[i] && remaining.length) {
        ordered[i] = remaining.shift();
      }
    }
    return ordered.filter(Boolean);
  }

  function updatePresetButtonsUI() {
    const btnUlt = document.getElementById('preset-ultimo-11-btn');
    const btnIdeal = document.getElementById('preset-ideal-11-btn');
    if (btnUlt) {
      const isUlt = state.activeLineupPreset === 'ultimo1891';
      btnUlt.classList.toggle('active', isUlt);
      btnUlt.setAttribute('aria-pressed', isUlt ? 'true' : 'false');
    }
    if (btnIdeal) {
      const isId = state.activeLineupPreset === 'ideal';
      btnIdeal.classList.toggle('active', isId);
      btnIdeal.setAttribute('aria-pressed', isId ? 'true' : 'false');
    }
  }

  function showTacticalToast(message, isSuccess = true) {
    const banner = document.getElementById('tactical-guidance-banner');
    if (banner) {
      banner.classList.add('active-action');
      banner.innerHTML = `<span style="font-size:15px;">${isSuccess ? '✅' : 'ℹ️'}</span> <strong>${escapeHtml(message)}</strong>`;
      setTimeout(() => {
        if (state.selectedSlotIndex === null && state.selectedBenchIndex === null && banner) {
          banner.classList.remove('active-action');
          banner.textContent = '💡 Tocá un titular en la cancha para sustituirlo o moverlo, o tocá un suplente para que ingrese.';
        }
      }, 3500);
    }
  }

  function applyIdealLineup2026(silent = false) {
    if (!state.initialLineup || !state.initialLineup.length) {
      state.initialLineup = JSON.parse(JSON.stringify(DEFAULT_LINEUP));
      state.initialBench = JSON.parse(JSON.stringify(DEFAULT_BENCH));
    }
    state.lineup = JSON.parse(JSON.stringify(state.initialLineup));
    state.bench = JSON.parse(JSON.stringify(state.initialBench));
    state.selectedSlotIndex = null;
    state.selectedBenchIndex = null;
    state.activeLineupPreset = 'ideal';
    updatePresetButtonsUI();
    renderTacticalBoard();
    if (!silent) {
      showTacticalToast('⭐ 11 Ideal 2026 cargado en la cancha.');
      showToast('⭐ 11 Ideal 2026 cargado en la pizarra', 'gold');
    }
  }

  function applyUltimoOnceAguirre() {
    const names = (state.squad && Array.isArray(state.squad.ultimo_once_1891) && state.squad.ultimo_once_1891.length >= 11)
      ? state.squad.ultimo_once_1891
      : ((state.live && state.live.partido_activo && Array.isArray(state.live.partido_activo.alineacion_1891) && state.live.partido_activo.alineacion_1891.length >= 11)
          ? state.live.partido_activo.alineacion_1891
          : null);

    if (!names) {
      showTacticalToast('No se encontró el último 11 oficial en squad_2026.json.', false);
      showToast('⚠️ Último 11 oficial no disponible aún', 'warning');
      return;
    }

    const fullPool = (state.squad && Array.isArray(state.squad.jugadores) && state.squad.jugadores.length >= 11)
      ? JSON.parse(JSON.stringify(state.squad.jugadores))
      : JSON.parse(JSON.stringify(DEFAULT_LINEUP.concat(DEFAULT_BENCH)));

    const matchedIds = new Set();
    const starters = [];

    names.slice(0, 11).forEach(rawName => {
      const targetNorm = normalizeText(rawName);
      let found = fullPool.find(p => !matchedIds.has(p.id) && normalizeText(p.nombre) === targetNorm);
      if (!found) {
        const lastTok = targetNorm.split(' ').slice(-1)[0];
        found = fullPool.find(p => !matchedIds.has(p.id) && normalizeText(p.nombre).includes(lastTok));
      }
      if (found) {
        matchedIds.add(found.id);
        starters.push(found);
      }
    });

    // Completar si faltara alguno por diferencia de nombre
    fullPool.forEach(p => {
      if (starters.length < 11 && !matchedIds.has(p.id)) {
        matchedIds.add(p.id);
        starters.push(p);
      }
    });

    const orderedStarters = orderLineupForPitch(starters);
    const remainingBench = fullPool.filter(p => !matchedIds.has(p.id));

    state.lineup = orderedStarters;
    state.bench = remainingBench;
    state.selectedSlotIndex = null;
    state.selectedBenchIndex = null;
    state.activeLineupPreset = 'ultimo1891';
    updatePresetButtonsUI();
    renderTacticalBoard();

    const matchName = (state.live && state.live.ultimo_partido && state.live.ultimo_partido.nombre) || 'último partido oficial';
    showTacticalToast(`📋 Último 11 de Diego Aguirre (${matchName} • 1891 BD) cargado.`);
    showToast(`📋 Último 11 de Aguirre cargado (1891 BD)`, 'success');
  }

  function resetTacticalLineup() {
    applyIdealLineup2026(true);
    state.benchLineFilter = 'all';
    renderTacticalBoard();
    showTacticalToast('↺ 11 inicial 2026 de Diego Aguirre restablecido con éxito.');
    showToast('↺ Alineación restablecida al 11 Ideal 2026', 'info');
  }

  function updateBenchFilterChipsUI() {
    const filterBar = document.getElementById('bench-line-filters');
    if (!filterBar) return;

    const counts = { all: state.bench.length, ARQ: 0, DEF: 0, VOL: 0, ATA: 0 };
    state.bench.forEach(p => {
      const grp = getPlayerLineGroup(p);
      if (counts[grp] !== undefined) counts[grp]++;
    });

    const labels = { all: 'Todos', ARQ: 'ARQ', DEF: 'DEF', VOL: 'VOL', ATA: 'ATA' };
    filterBar.querySelectorAll('.bench-filter-chip').forEach(btn => {
      const line = btn.getAttribute('data-line') || 'all';
      const isAct = line === state.benchLineFilter;
      btn.classList.toggle('active', isAct);
      btn.setAttribute('aria-selected', isAct ? 'true' : 'false');
      btn.innerHTML = `${escapeHtml(labels[line] || line)} <span class="bench-chip-count">(${counts[line] ?? 0})</span>`;
    });
  }

  function renderTacticalBoard() {
    const pitch = document.getElementById('tactical-pitch');
    const benchBox = document.getElementById('tactical-bench');
    const banner = document.getElementById('tactical-guidance-banner');
    if (!pitch) return;

    if (!state.lineup || !state.lineup.length) {
      state.lineup = JSON.parse(JSON.stringify(DEFAULT_LINEUP));
      state.initialLineup = JSON.parse(JSON.stringify(DEFAULT_LINEUP));
      state.bench = JSON.parse(JSON.stringify(DEFAULT_BENCH));
      state.initialBench = JSON.parse(JSON.stringify(DEFAULT_BENCH));
    }

    const coords = FORMATIONS[state.formation] || FORMATIONS['4-2-3-1'];
    const pitchMarkings = `
      <div class="pitch-corner-tl"></div><div class="pitch-corner-tr"></div>
      <div class="pitch-corner-bl"></div><div class="pitch-corner-br"></div>
      <div class="pitch-area-top"></div><div class="pitch-goal-top"></div><div class="pitch-arc-top"></div>
      <div class="pitch-mid-line"></div><div class="pitch-center-circle"></div><div class="pitch-center-spot"></div>
      <div class="pitch-area-bottom"></div><div class="pitch-goal-bottom"></div><div class="pitch-arc-bottom"></div>
    `;

    const playersHtml = state.lineup.slice(0, 11).map((p, idx) => {
      const c = coords[idx] || { x: 50, y: 50, role: p.posicion };
      const isSel = state.selectedSlotIndex === idx;
      const lastName = String(p.nombre || '').split(' ').slice(-1)[0];
      const roleBadge = c.role || p.posicion;
      const ariaTitle = `#${p.numero} ${p.nombre} (${roleBadge})`;
      return `
        <div class="pitch-player ${isSel ? 'selected' : ''}" role="button" tabindex="0" aria-pressed="${isSel ? 'true' : 'false'}" aria-label="Titular ${escapeHtml(ariaTitle)}" data-slot="${idx}" style="left:${c.x}%;top:${c.y}%;" title="${escapeHtml(ariaTitle)}">
          <div class="player-token">${escapeHtml(p.numero)}</div>
          <div class="player-label">${escapeHtml(lastName)} <span style="color:var(--manya-gold);font-weight:900;">${escapeHtml(roleBadge)}</span></div>
        </div>
      `;
    }).join('');

    pitch.innerHTML = pitchMarkings + `<div id="pitch-players-layer" class="pitch-players-layer">${playersHtml}</div>`;

    const handleSlotActivate = (idx) => {
      if (state.selectedBenchIndex !== null) {
        const benchPlayer = state.bench[state.selectedBenchIndex];
        const starterPlayer = state.lineup[idx];
        state.lineup[idx] = benchPlayer;
        state.bench[state.selectedBenchIndex] = starterPlayer;
        state.selectedSlotIndex = null;
        state.selectedBenchIndex = null;
        state.activeLineupPreset = 'custom';
        updatePresetButtonsUI();
        renderTacticalBoard();
        showTacticalToast(`🔄 Cambio: Entra #${benchPlayer.numero} ${benchPlayer.nombre}, sale #${starterPlayer.numero} ${starterPlayer.nombre}`);
      } else if (state.selectedSlotIndex === idx) {
        state.selectedSlotIndex = null;
        renderTacticalBoard();
      } else if (state.selectedSlotIndex !== null) {
        const p1 = state.lineup[state.selectedSlotIndex];
        const p2 = state.lineup[idx];
        state.lineup[state.selectedSlotIndex] = p2;
        state.lineup[idx] = p1;
        state.selectedSlotIndex = null;
        state.activeLineupPreset = 'custom';
        updatePresetButtonsUI();
        renderTacticalBoard();
        showTacticalToast(`↔ Rotación en cancha: #${p1.numero} ${p1.nombre.split(' ').slice(-1)[0]} ↔ #${p2.numero} ${p2.nombre.split(' ').slice(-1)[0]}`);
      } else {
        state.selectedSlotIndex = idx;
        state.selectedBenchIndex = null;
        renderTacticalBoard();
      }
    };

    pitch.querySelectorAll('.pitch-player').forEach(el => {
      const idx = parseInt(el.getAttribute('data-slot'), 10);
      el.addEventListener('click', () => handleSlotActivate(idx));
      el.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          handleSlotActivate(idx);
        }
      });
    });

    updateBenchFilterChipsUI();

    if (benchBox) {
      const benchEntries = state.bench
        .map((player, realIdx) => ({ player, realIdx, lineGroup: getPlayerLineGroup(player) }))
        .filter(entry => state.benchLineFilter === 'all' || entry.lineGroup === state.benchLineFilter);

      if (!benchEntries.length) {
        benchBox.innerHTML = `<div style="width:100%;padding:12px;text-align:center;font-size:12.5px;color:var(--text-secondary);border:1px dashed rgba(255,209,0,0.28);border-radius:8px;">No quedan relevos en la línea <strong>${escapeHtml(state.benchLineFilter)}</strong>. <button type="button" id="bench-reset-filter-btn" style="background:none;border:none;color:var(--manya-gold);font-weight:800;cursor:pointer;text-decoration:underline;margin-left:6px;">Ver todos</button></div>`;
        const rf = document.getElementById('bench-reset-filter-btn');
        if (rf) {
          rf.onclick = () => {
            state.benchLineFilter = 'all';
            renderTacticalBoard();
          };
        }
      } else {
        benchBox.innerHTML = benchEntries.map(({ player: b, realIdx }) => {
          const isBenchSel = state.selectedBenchIndex === realIdx;
          return `
            <button type="button" class="bench-btn ${isBenchSel ? 'selected' : ''}" aria-pressed="${isBenchSel ? 'true' : 'false'}" data-bidx="${realIdx}" title="Sustituir con #${escapeHtml(b.numero)} ${escapeHtml(b.nombre)}">
              <strong style="color:var(--manya-gold);">#${escapeHtml(b.numero)}</strong> ${escapeHtml(b.nombre)} <span style="opacity:0.75;font-size:11px;">(${escapeHtml(b.posicion)})</span>
            </button>
          `;
        }).join('');

        benchBox.querySelectorAll('button.bench-btn').forEach(btn => {
          btn.addEventListener('click', () => {
            const bIdx = parseInt(btn.getAttribute('data-bidx'), 10);
            if (state.selectedSlotIndex !== null) {
              const benchPlayer = state.bench[bIdx];
              const starterPlayer = state.lineup[state.selectedSlotIndex];
              state.lineup[state.selectedSlotIndex] = benchPlayer;
              state.bench[bIdx] = starterPlayer;
              state.selectedSlotIndex = null;
              state.selectedBenchIndex = null;
              state.activeLineupPreset = 'custom';
              updatePresetButtonsUI();
              renderTacticalBoard();
              showTacticalToast(`🔄 Cambio: Entra #${benchPlayer.numero} ${benchPlayer.nombre}, sale #${starterPlayer.numero} ${starterPlayer.nombre}`);
            } else if (state.selectedBenchIndex === bIdx) {
              state.selectedBenchIndex = null;
              renderTacticalBoard();
            } else {
              state.selectedBenchIndex = bIdx;
              state.selectedSlotIndex = null;
              renderTacticalBoard();
            }
          });
        });
      }
    }

    if (banner) {
      if (state.selectedSlotIndex !== null) {
        const sel = state.lineup[state.selectedSlotIndex];
        const role = coords[state.selectedSlotIndex]?.role || sel.posicion;
        banner.classList.add('active-action');
        banner.innerHTML = `🟡 <strong>Titular seleccionado: #${escapeHtml(sel.numero)} ${escapeHtml(sel.nombre)} (${escapeHtml(role)}).</strong> Tocá un suplente para cambiarlo, u otro titular para rotar.`;
      } else if (state.selectedBenchIndex !== null) {
        const selB = state.bench[state.selectedBenchIndex];
        banner.classList.add('active-action');
        banner.innerHTML = `🟢 <strong>Suplente seleccionado: #${escapeHtml(selB.numero)} ${escapeHtml(selB.nombre)} (${escapeHtml(selB.posicion)}).</strong> Tocá al jugador en cancha que querés sustituir.`;
      } else {
        banner.classList.remove('active-action');
        banner.textContent = '💡 Tocá un titular en la cancha para sustituirlo o moverlo, o tocá un suplente para que ingrese.';
      }
    }
  }

  function _getDynamicMatchLabelForExport() {
    const prox = state.live && state.live.proximo_partido;
    if (prox && prox.es_definicion_final) return 'Gran Final Campeonato Uruguayo 2026 • Campeón Tabla Anual';
    if (prox && prox.nombre) return `${prox.nombre} • ${prox.estadio || 'Campeonato Uruguayo 2026'}`;
    return 'Club Atlético Peñarol • Temporada 2026';
  }

  function exportLineupPNG() {
    const canvas = document.createElement('canvas');
    canvas.width = 1080;
    canvas.height = 1350;
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = '#09090b';
    ctx.fillRect(0, 0, 1080, 1350);
    ctx.fillStyle = '#ffd100';
    ctx.fillRect(0, 0, 1080, 16);

    ctx.fillStyle = '#ffd100';
    ctx.font = '900 42px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('★ CLUB ATLÉTICO PEÑAROL • 11 TITULAR ★', 540, 80);

    ctx.fillStyle = '#f4f4f5';
    ctx.font = '700 21px Inter, sans-serif';
    ctx.fillText(_getDynamicMatchLabelForExport(), 540, 118);

    ctx.fillStyle = '#ffd100';
    ctx.font = '800 20px Inter, sans-serif';
    ctx.fillText(`Esquema Táctico: ${state.formation} • DT: Diego Aguirre`, 540, 150);

    const px0 = 80, py0 = 175, pw = 920, ph = 980;
    const midY = py0 + ph / 2, midX = px0 + pw / 2;

    ctx.fillStyle = '#14532d';
    ctx.fillRect(px0, py0, pw, ph);
    ctx.fillStyle = 'rgba(255, 255, 255, 0.035)';
    for (let i = 0; i < 8; i += 2) ctx.fillRect(px0, py0 + i * (ph / 8), pw, ph / 8);

    ctx.strokeStyle = 'rgba(255, 255, 255, 0.9)';
    ctx.lineWidth = 4;
    ctx.strokeRect(px0, py0, pw, ph);
    ctx.beginPath(); ctx.moveTo(px0, midY); ctx.lineTo(px0 + pw, midY); ctx.stroke();
    ctx.beginPath(); ctx.arc(midX, midY, 110, 0, Math.PI * 2); ctx.stroke();
    ctx.strokeRect(midX - 250, py0, 500, 160);
    ctx.strokeRect(midX - 120, py0, 240, 60);
    ctx.strokeRect(midX - 250, py0 + ph - 160, 500, 160);
    ctx.strokeRect(midX - 120, py0 + ph - 60, 240, 60);

    const coords = FORMATIONS[state.formation] || FORMATIONS['4-2-3-1'];
    state.lineup.slice(0, 11).forEach((p, idx) => {
      const c = coords[idx] || { x: 50, y: 50, role: p.posicion };
      const px = px0 + (c.x / 100) * pw;
      const py = py0 + (c.y / 100) * ph;

      ctx.beginPath(); ctx.arc(px, py + 4, 34, 0, Math.PI * 2); ctx.fillStyle = 'rgba(0,0,0,0.55)'; ctx.fill();
      ctx.beginPath(); ctx.arc(px, py, 34, 0, Math.PI * 2); ctx.fillStyle = '#ffd100'; ctx.fill();
      ctx.lineWidth = 4; ctx.strokeStyle = '#09090b'; ctx.stroke();

      ctx.fillStyle = '#09090b';
      ctx.font = '900 26px Inter, sans-serif';
      ctx.fillText(String(p.numero), px, py + 9);

      const nameTxt = `${p.nombre.split(' ').slice(-1)[0]} (${c.role || p.posicion})`;
      ctx.font = '800 19px Inter, sans-serif';
      const textW = ctx.measureText(nameTxt).width + 18;
      ctx.fillStyle = 'rgba(9, 9, 11, 0.92)';
      ctx.fillRect(px - textW / 2, py + 42, textW, 26);
      ctx.strokeStyle = 'rgba(255, 209, 0, 0.7)';
      ctx.lineWidth = 1.5;
      ctx.strokeRect(px - textW / 2, py + 42, textW, 26);
      ctx.fillStyle = '#ffffff';
      ctx.fillText(nameTxt, px, py + 61);
    });

    ctx.fillStyle = 'rgba(17, 17, 21, 0.95)';
    ctx.fillRect(80, 1175, 920, 80);
    ctx.fillStyle = '#ffd100';
    ctx.font = '800 17px Inter, sans-serif';
    ctx.textAlign = 'left';
    ctx.fillText('BANCO DE RELEVOS:', 100, 1205);
    ctx.fillStyle = '#e4e4e7';
    ctx.font = '600 16px Inter, sans-serif';
    ctx.fillText(state.bench.slice(0, 7).map(b => `#${b.numero} ${b.nombre.split(' ').slice(-1)[0]}`).join('  •  '), 100, 1235);

    ctx.fillStyle = '#ffd100';
    ctx.font = '800 20px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('Creado en https://manya.servicioti.com.uy • Pasión Aurinegra ServicioTI', 540, 1315);

    const download = (href) => {
      const link = document.createElement('a');
      link.download = `mi-11-penarol-${state.formation}.png`;
      link.href = href;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      showTacticalToast('📥 ¡Tu 11 titular se ha descargado en PNG 1080×1350!');
      showToast('📥 Imagen PNG 1080×1350 de tu 11 descargada', 'success');
    };
    if (canvas.toBlob) {
      canvas.toBlob(blob => { if (blob) { const u = URL.createObjectURL(blob); download(u); setTimeout(() => URL.revokeObjectURL(u), 2000); } }, 'image/png');
    } else {
      download(canvas.toDataURL('image/png'));
    }
  }

  async function handleShareLineup() {
    const coords = FORMATIONS[state.formation] || FORMATIONS['4-2-3-1'];
    const titularesStr = (state.lineup || []).slice(0, 11).map((p, i) => `${i + 1}. #${p.numero} ${p.nombre} (${coords[i]?.role || p.posicion})`).join('\n');
    const text = `⚽ Mi 11 Titular del Glorioso Peñarol (${state.formation})\nDT: Diego Aguirre • ${_getDynamicMatchLabelForExport()}\n\n${titularesStr}\n\nArmá tu 11 en https://manya.servicioti.com.uy/#pizarra-tactica`;

    if (navigator.share) {
      try {
        await navigator.share({ title: 'Mi 11 Titular de Peñarol', text, url: 'https://manya.servicioti.com.uy/#pizarra-tactica' });
        showToast('📤 ¡11 Titular compartido con éxito!', 'success');
        return;
      } catch (_) {}
    }
    try {
      await navigator.clipboard.writeText(text);
      showTacticalToast('📋 ¡11 Titular copiado al portapapeles!');
      showToast('📋 ¡11 Titular copiado al portapapeles!', 'success');
    } catch (_) {
      showTacticalToast('⚠️ No se pudo copiar la alineación', false);
      showToast('⚠️ No se pudo copiar la alineación', 'warning');
    }
  }

  function initTacticalBoard() {
    if (!state.lineup || !state.lineup.length) {
      state.lineup = JSON.parse(JSON.stringify(DEFAULT_LINEUP));
      state.initialLineup = JSON.parse(JSON.stringify(DEFAULT_LINEUP));
      state.bench = JSON.parse(JSON.stringify(DEFAULT_BENCH));
      state.initialBench = JSON.parse(JSON.stringify(DEFAULT_BENCH));
    }
    updatePresetButtonsUI();
    renderTacticalBoard();

    document.querySelectorAll('[data-formation]').forEach(btn => {
      btn.onclick = () => {
        document.querySelectorAll('[data-formation]').forEach(b => {
          b.classList.remove('active');
          b.setAttribute('aria-pressed', 'false');
        });
        btn.classList.add('active');
        btn.setAttribute('aria-pressed', 'true');
        state.formation = btn.getAttribute('data-formation') || '4-2-3-1';
        state.selectedSlotIndex = null;
        state.selectedBenchIndex = null;
        renderTacticalBoard();
        showToast(`⚽ Esquema táctico cambiado a ${state.formation}`, 'info');
      };
    });

    const filterBar = document.getElementById('bench-line-filters');
    if (filterBar) {
      filterBar.querySelectorAll('.bench-filter-chip').forEach(btn => {
        btn.onclick = () => {
          state.benchLineFilter = btn.getAttribute('data-line') || 'all';
          renderTacticalBoard();
        };
      });
    }

    const btnUlt = document.getElementById('preset-ultimo-11-btn');
    if (btnUlt) btnUlt.onclick = applyUltimoOnceAguirre;
    const btnIdeal = document.getElementById('preset-ideal-11-btn');
    if (btnIdeal) btnIdeal.onclick = () => applyIdealLineup2026(false);

    ['reset-lineup-btn', 'btn-reset-lineup'].forEach(id => { const b = document.getElementById(id); if (b) b.onclick = resetTacticalLineup; });
    ['export-lineup-btn', 'btn-download-lineup'].forEach(id => { const b = document.getElementById(id); if (b) b.onclick = exportLineupPNG; });
    const shBtn = document.getElementById('share-lineup-btn');
    if (shBtn) shBtn.onclick = handleShareLineup;
  }

  // ==================== RIVAL SCOUT & HISTORIAL 1891 BD ====================
  function renderRivalIntelligence(rival) {
    if (!rival) return;
    const sc = rival.scouting_tactico || {};
    const inst = rival.datos_institucionales_auf || {};
    const fase = (state.live && state.live.fase_partido) || rival.fase_contexto || 'POST_PARTIDO';

    const set = (id, val) => { const el = document.getElementById(id); if (el && val) el.textContent = val; };
    const prefix = fase === 'POST_PARTIDO' ? 'Radiografía Táctica del Último Rival' : 'Radiografía Táctica del Próximo Rival';
    set('scout-rival-title', `🧭 ${prefix}: ${rival.rival_nombre || 'Rival'}${sc.entrenador ? ' (DT ' + sc.entrenador + ')' : ''}`);
    set('scout-dt', sc.entrenador);
    set('scout-esquema', sc.esquema_base);
    set('scout-estadio', inst.estadio_propio);
    set('scout-fundacion', inst.fundacion);
    set('scout-propuesta', sc.propuesta_juego);

    const webLink = document.getElementById('scout-web-link');
    if (webLink && inst.web_oficial) {
      const cleanWeb = safeUrl(inst.web_oficial, 'https://auf.org.uy/');
      webLink.href = cleanWeb;
      webLink.textContent = cleanWeb.replace(/^https?:\/\/(www\.)?/, '').replace(/\/$/, '') + ' ↗';
    }

    const strongBox = document.getElementById('scout-fortalezas');
    if (strongBox && sc.puntos_fuertes && sc.puntos_fuertes.length) {
      strongBox.innerHTML = sc.puntos_fuertes.map(p => `<span class="scout-pill strong">✓ ${escapeHtml(p)}</span>`).join('');
    }

    const weakBox = document.getElementById('scout-debilidades');
    if (weakBox && sc.vulnerabilidades_a_explotar && sc.vulnerabilidades_a_explotar.length) {
      weakBox.innerHTML = sc.vulnerabilidades_a_explotar.map(v => `<span class="scout-pill weak">⚠️ ${escapeHtml(v)}</span>`).join('');
    }

    const figEl = document.getElementById('scout-figuras');
    if (figEl && sc.figuras_a_seguir && sc.figuras_a_seguir.length) {
      figEl.innerHTML = sc.figuras_a_seguir.map(f => `<div style="margin-bottom:4px;">• <strong>${escapeHtml(f.nombre)} (${escapeHtml(f.rol)}):</strong> <span style="color:#a1a1aa;">${escapeHtml(f.analisis)}</span></div>`).join('');
    }

    const dTitle = document.getElementById('duelos-1x1-title');
    if (dTitle) {
      dTitle.textContent = `⚔️ Duelos Tácticos 1x1: Claves de Peñarol vs ${rival.rival_corto || rival.rival_nombre}`;
    }

    const duelosContainer = document.getElementById('duelos-tacticos-container');
    if (duelosContainer && rival.duelos_tacticos_1x1 && rival.duelos_tacticos_1x1.length) {
      duelosContainer.innerHTML = rival.duelos_tacticos_1x1.map(d => {
        const dp = d.penarol || {};
        const dr = d.rival || {};
        return `
          <div class="duel-item">
            <div class="duel-title-bar">
              <span class="duel-zone">${escapeHtml(d.zona_campo)}</span>
              <span class="duel-headline">${escapeHtml(d.titulo)}</span>
            </div>
            <div class="duel-sides-wrap">
              <div class="duel-side is-penarol">
                <div class="duel-player-header">
                  <span class="duel-num">${escapeHtml(dp.dorsal || '★')}</span>
                  <div>
                    <strong class="duel-player-name">${escapeHtml(dp.jugador)}</strong>
                    <div class="duel-player-role">${escapeHtml(dp.rol)}</div>
                  </div>
                </div>
                <p class="duel-player-desc">${escapeHtml(dp.atributos_clave)}</p>
              </div>
              <div class="duel-vs-divider">VS</div>
              <div class="duel-side is-rival">
                <div class="duel-player-header">
                  <span class="duel-num rival">${escapeHtml(dr.dorsal || 'R')}</span>
                  <div>
                    <strong class="duel-player-name">${escapeHtml(dr.jugador)}</strong>
                    <div class="duel-player-role">${escapeHtml(dr.rol)}</div>
                  </div>
                </div>
                <p class="duel-player-desc">${escapeHtml(dr.atributos_clave)}</p>
              </div>
            </div>
            <div class="duel-verdict"><strong>Clave del Duelo:</strong> ${escapeHtml(d.clave_del_duelo)}</div>
          </div>
        `;
      }).join('');
    }
  }

  function renderHeadToHead(h2h) {
    if (!h2h || !h2h.resumen) return;
    const res = h2h.resumen;
    const dif = (res.goles_penarol - res.goles_rival);
    const difStr = res.diferencia_goles || (dif > 0 ? `+${dif}` : String(dif));
    const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };

    set('h2h-title', `📜 Historial Oficial Verificado: Peñarol vs ${h2h.rival_oficial || h2h.rival}`);
    set('h2h-pj', res.partidos_jugados);
    set('h2h-pg', res.ganados_penarol);
    set('h2h-pe', res.empatados);
    set('h2h-pp', res.perdidos_penarol);
    set('h2h-gf', `${res.goles_penarol} - ${res.goles_rival}`);
    set('h2h-gf-lbl', `Goles (Dif: ${difStr})`);
    set('h2h-eff', res.efectividad_pct);
    set('h2h-pill', `★ ${res.ventaja_victorias}`);

    const sumEl = document.getElementById('h2h-summary-text');
    if (sumEl) {
      sumEl.innerHTML = `<strong>Supremacía histórica aurinegra (1891 BD):</strong> Peñarol suma <strong>${escapeHtml(res.ganados_penarol)} triunfos</strong>, ${escapeHtml(res.empatados)} empates y ${escapeHtml(res.perdidos_penarol)} derrotas frente a ${escapeHtml(h2h.rival || h2h.rival_oficial)} (${escapeHtml(difStr)} goles de diferencia).`;
    }
  }

  // ==================== LIGHTBOX PROFESIONAL ACCESIBLE v11.0 ====================
  function renderLightboxItem() {
    const item = lightboxState.items[lightboxState.index];
    if (!item) return;

    const is1891 = (item.cuenta === '1891.uy') || (item.url_post && item.url_post.includes('1891.uy'));
    const isTattoo = item._kind === 'tattoo';
    const imgEl = document.getElementById('lightbox-img');
    if (imgEl) {
      const primarySrc = safeImgSrc(item.imagen_webp || item.imagen_jpg);
      const fallbackSrc = safeImgSrc(item.imagen_jpg || item.imagen_webp);
      imgEl.dataset.fallbackApplied = '';
      imgEl.setAttribute('data-fallback-src', fallbackSrc);
      imgEl.src = primarySrc;
      imgEl.alt = item.titulo || 'Club Atlético Peñarol';
    }

    const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    if (isTattoo) {
      set('lightbox-badge', `💉 ${(item.estilo || 'PIEL CARBONERA').toUpperCase()}`);
      set('lightbox-meta', `${item.zona_cuerpo || 'Tatuaje'} • ${item.barrio || 'Montevideo'}`);
    } else if (is1891) {
      set('lightbox-badge', '📜 FICHA OFICIAL 1891 BD');
      set('lightbox-meta', `1891 BD • ${item.estadio || 'Escenario Oficial'} • ${item.fecha || '2026'}`);
    } else {
      set('lightbox-badge', `📸 ${(item.categoria || 'PEÑAROL').toUpperCase()}`);
      set('lightbox-meta', `${item.cuenta || '@oficialcap'} • ${item.fecha || 'Temporada 2026'}`);
    }

    set('lightbox-title', item.titulo || 'Galería Oficial del Club Atlético Peñarol');
    set('lightbox-desc', item.descripcion || item.caption || '');

    const counterEl = document.getElementById('lightbox-counter');
    if (counterEl) {
      if (lightboxState.items.length > 1) {
        counterEl.textContent = `${lightboxState.index + 1} / ${lightboxState.items.length}`;
        counterEl.style.display = 'inline-block';
      } else {
        counterEl.textContent = '';
        counterEl.style.display = 'none';
      }
    }

    const creditEl = document.getElementById('lightbox-credit');
    if (creditEl) {
      const creditText = item.credito || (isTattoo
        ? `${item.tatuador || 'Artista Aurinegro'}${item.estudio ? ' • ' + item.estudio : ''}`
        : (item.fuente || item.cuenta || '@oficialcap'));
      creditEl.innerHTML = `Crédito: <strong>${escapeHtml(creditText)}</strong>`;
    }

    const linkEl = document.getElementById('lightbox-external-link');
    if (linkEl) {
      const targetHref = safeUrl(item.url_post || item.url_instagram || 'https://www.instagram.com/oficialcap/', 'https://www.instagram.com/oficialcap/');
      linkEl.href = targetHref;
      linkEl.textContent = is1891 ? 'Ver ficha oficial en 1891.uy ↗' : (isTattoo ? 'Ver artista en Instagram ↗' : 'Ver fuente original ↗');
    }

    const prevBtn = document.getElementById('lightbox-prev');
    const nextBtn = document.getElementById('lightbox-next');
    const hasMany = lightboxState.items.length > 1;
    if (prevBtn) prevBtn.hidden = !hasMany;
    if (nextBtn) nextBtn.hidden = !hasMany;

    // Precargar imágenes vecinas para navegación instantánea
    if (hasMany) {
      const nextIdx = (lightboxState.index + 1) % lightboxState.items.length;
      const prevIdx = (lightboxState.index - 1 + lightboxState.items.length) % lightboxState.items.length;
      [nextIdx, prevIdx].forEach(idx => {
        const neighbor = lightboxState.items[idx];
        if (neighbor && (neighbor.imagen_webp || neighbor.imagen_jpg)) {
          const pre = new Image();
          pre.src = safeImgSrc(neighbor.imagen_webp || neighbor.imagen_jpg);
        }
      });
    }
  }

  function stepLightbox(delta) {
    if (!lightboxState.isOpen || lightboxState.items.length <= 1) return;
    const len = lightboxState.items.length;
    lightboxState.index = (lightboxState.index + delta + len) % len;
    renderLightboxItem();
  }

  function closeLightbox() {
    const modal = document.getElementById('manya-lightbox');
    if (!modal || !lightboxState.isOpen) return;
    lightboxState.isOpen = false;
    modal.style.display = 'none';
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    if (lightboxState.triggerEl && typeof lightboxState.triggerEl.focus === 'function') {
      try { lightboxState.triggerEl.focus(); } catch (_) {}
    }
    lightboxState.triggerEl = null;
  }

  function openLightbox(itemsOrItem, startIndex = 0) {
    const modal = document.getElementById('manya-lightbox');
    if (!modal || !itemsOrItem) return;

    const list = Array.isArray(itemsOrItem) ? itemsOrItem.filter(Boolean) : [itemsOrItem];
    if (!list.length) return;

    lightboxState.items = list;
    lightboxState.index = Math.max(0, Math.min(startIndex, list.length - 1));
    lightboxState.triggerEl = document.activeElement;
    lightboxState.isOpen = true;

    renderLightboxItem();
    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';

    const closeBtn = document.getElementById('lightbox-close');
    if (closeBtn) closeBtn.focus();
  }

  function setupLightbox() {
    const modal = document.getElementById('manya-lightbox');
    if (!modal) return;
    const ov = document.getElementById('lightbox-overlay');
    const cl = document.getElementById('lightbox-close');
    const prevBtn = document.getElementById('lightbox-prev');
    const nextBtn = document.getElementById('lightbox-next');
    const stage = document.getElementById('lightbox-stage');
    const imgEl = document.getElementById('lightbox-img');

    if (ov) ov.addEventListener('click', closeLightbox);
    if (cl) cl.addEventListener('click', closeLightbox);
    if (prevBtn) prevBtn.addEventListener('click', () => stepLightbox(-1));
    if (nextBtn) nextBtn.addEventListener('click', () => stepLightbox(1));

    if (imgEl) {
      imgEl.addEventListener('error', () => {
        const fb = imgEl.getAttribute('data-fallback-src');
        if (fb && !imgEl.dataset.fallbackApplied) {
          imgEl.dataset.fallbackApplied = '1';
          imgEl.src = safeImgSrc(fb);
        }
      });
    }

    // Soporte gestual swipe táctil en móviles
    if (stage) {
      let touchStartX = 0;
      stage.addEventListener('touchstart', e => {
        if (e.touches && e.touches.length === 1) touchStartX = e.touches[0].clientX;
      }, { passive: true });
      stage.addEventListener('touchend', e => {
        if (!touchStartX || !e.changedTouches || !e.changedTouches.length) return;
        const dx = e.changedTouches[0].clientX - touchStartX;
        touchStartX = 0;
        if (Math.abs(dx) > 45) stepLightbox(dx < 0 ? 1 : -1);
      }, { passive: true });
    }

    // Teclado accesible: Esc, Flechas Izq/Der y Focus Trap con Tab
    document.addEventListener('keydown', e => {
      if (!lightboxState.isOpen) return;
      if (e.key === 'Escape') {
        e.preventDefault();
        closeLightbox();
      } else if (e.key === 'ArrowLeft') {
        e.preventDefault();
        stepLightbox(-1);
      } else if (e.key === 'ArrowRight') {
        e.preventDefault();
        stepLightbox(1);
      } else if (e.key === 'Tab') {
        const focusables = Array.from(modal.querySelectorAll('button:not([hidden]):not([disabled]), a[href]'))
          .filter(el => el.offsetParent !== null);
        if (!focusables.length) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    });
  }

  // ==================== PORTADA, EDITORIAL, PRENSA FILTRABLE, GALERÍAS & TATUAJES ====================
  function renderHeroInstagramPost(item, digest) {
    if (!document.getElementById('portada-visual')) return;
    const pv = (digest && digest.portada_visual) ? digest.portada_visual : {};
    const effective = Object.assign({}, item || {}, pv);

    const cuenta = effective.cuenta || '@oficialcap';
    const imgSrc = safeImgSrc(effective.imagen_webp || effective.imagen_jpg || 'assets/gallery/1891_cerro_largo_32174_02.webp');
    const headline = pv.titular_portada || (digest && digest.titular_dia) || effective.titulo || 'Actualidad del Club Atlético Peñarol';
    const bajada = pv.bajada_portada || (digest && digest.bajada_seo) || effective.descripcion || '';
    const postUrl = safeUrl(effective.url_post || 'https://www.instagram.com/oficialcap/', 'https://www.instagram.com/oficialcap/');

    const set = (id, v) => { const el = document.getElementById(id); if (el) el.textContent = v; };
    set('hero-post-account', cuenta);
    set('hero-post-time', (digest && digest.actualizado) ? `Actualizado ${digest.actualizado}` : 'Actualizado Hoy');
    set('hero-post-location', effective.ubicacion || '📍 Estadio Campeón del Siglo • Montevideo');
    set('hero-post-headline', headline);
    set('hero-post-text', bajada);
    set('hero-post-badge', `📸 ${(effective.categoria || 'PORTADA OFICIAL').toUpperCase()}`);
    set('hero-post-category-tag', `⭐ ${cuenta.toUpperCase()}`);

    const imgEl = document.getElementById('hero-post-img');
    if (imgEl) {
      imgEl.src = imgSrc;
      imgEl.alt = headline;
      if (effective.imagen_jpg) imgEl.setAttribute('data-fallback-src', safeImgSrc(effective.imagen_jpg));
    }
    const ext = document.getElementById('hero-post-external-link');
    if (ext) ext.href = postUrl;

    const openHero = () => openLightbox({
      titulo: headline,
      descripcion: bajada,
      cuenta,
      credito: effective.fuente || cuenta,
      categoria: effective.categoria || 'portada',
      url_post: postUrl,
      imagen_webp: imgSrc,
      imagen_jpg: safeImgSrc(effective.imagen_jpg || imgSrc)
    });
    const mw = document.getElementById('hero-post-media');
    if (mw) {
      mw.setAttribute('role', 'button');
      mw.setAttribute('tabindex', '0');
      mw.setAttribute('aria-label', `Ampliar portada: ${headline}`);
      mw.onclick = openHero;
      mw.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); openHero(); } };
    }
    const eb = document.getElementById('hero-post-expand-btn'); if (eb) eb.onclick = e => { e.stopPropagation(); openHero(); };
    const zb = document.getElementById('hero-post-zoom-btn'); if (zb) zb.onclick = openHero;

    const likeBtn = document.getElementById('hero-post-like-btn');
    const likesEl = document.getElementById('hero-post-likes-count');
    const likeIcon = document.getElementById('hero-post-like-icon');
    let liked = false;
    try { liked = localStorage.getItem('manya_hero_liked_' + (digest?.partido_id || 'main')) === 'true'; } catch (_) {}
    let count = 42850 + (liked ? 1 : 0);
    const paintLike = () => {
      if (likesEl) likesEl.textContent = count.toLocaleString('es-UY');
      if (likeIcon) likeIcon.textContent = liked ? '❤️' : '🤍';
      if (likeBtn) likeBtn.setAttribute('aria-pressed', liked ? 'true' : 'false');
    };
    paintLike();
    if (likeBtn) {
      likeBtn.onclick = () => {
        liked = !liked; count += liked ? 1 : -1;
        try { localStorage.setItem('manya_hero_liked_' + (digest?.partido_id || 'main'), String(liked)); } catch (_) {}
        paintLike();
        if (liked) showToast('💛🖤 ¡Gracias por tu aliento aurinegro!', 'gold');
      };
    }
    const shBtn = document.getElementById('hero-post-share-btn');
    if (shBtn) {
      shBtn.onclick = async () => {
        if (navigator.share) {
          try { await navigator.share({ title: headline, text: bajada, url: window.location.href }); showToast('🔁 ¡Portada compartida!', 'success'); return; } catch (_) {}
        }
        if (navigator.clipboard) {
          try {
            await navigator.clipboard.writeText(window.location.href);
            shBtn.innerHTML = '<span>✅</span><span>¡Copiado!</span>';
            showToast('🔗 Enlace de Manya ServicioTI copiado', 'success');
            setTimeout(() => { shBtn.innerHTML = '<span>🔁</span><span>Compartir</span>'; }, 2000);
          } catch (_) {}
        }
      };
    }
  }

  function getShortPressSourceLabel(fuente) {
    const raw = String(fuente || 'Prensa').trim();
    const low = normalizeText(raw);
    if (low.startsWith('ovacion')) return 'Ovación';
    if (low.startsWith('referi')) return 'Referí';
    if (low.startsWith('futboluy')) return 'FútbolUy';
    if (low.startsWith('tenfield')) return 'Tenfield';
    if (low.startsWith('espn')) return 'ESPN';
    return raw.replace(/\s*\([^)]*\)\s*/g, '').trim() || raw;
  }

  function renderPressSourceChips() {
    const chipsBox = document.getElementById('prensa-source-chips');
    if (!chipsBox) return;

    const countsByLabel = new Map();
    state.pressArticles.forEach(n => {
      const label = getShortPressSourceLabel(n.fuente);
      countsByLabel.set(label, (countsByLabel.get(label) || 0) + 1);
    });

    const entries = [['all', 'Todas', state.pressArticles.length]];
    countsByLabel.forEach((cnt, label) => {
      entries.push([label, label, cnt]);
    });

    chipsBox.innerHTML = entries.map(([key, label, cnt]) => {
      const isAct = state.pressSourceFilter === key;
      return `<button type="button" role="tab" aria-selected="${isAct ? 'true' : 'false'}" class="prensa-chip ${isAct ? 'active' : ''}" data-source="${escapeHtml(key)}">${escapeHtml(label)} (${cnt})</button>`;
    }).join('');

    chipsBox.querySelectorAll('.prensa-chip').forEach(btn => {
      btn.onclick = () => {
        state.pressSourceFilter = btn.getAttribute('data-source') || 'all';
        renderPressSourceChips();
        renderPressNewsList();
      };
    });
  }

  function renderPressNewsList() {
    const newsBox = document.getElementById('live-news-list');
    const countBadge = document.getElementById('prensa-count-badge');
    const moreWrap = document.getElementById('prensa-load-more-wrap');
    if (!newsBox) return;

    const q = normalizeText(state.pressSearchQuery);
    const src = state.pressSourceFilter || 'all';

    const filtered = state.pressArticles.filter(n => {
      const matchesSource = src === 'all' || getShortPressSourceLabel(n.fuente) === src;
      if (!matchesSource) return false;
      if (!q) return true;
      const haystack = normalizeText(`${n.titulo || ''} ${n.resumen || ''} ${n.fuente || ''} ${n.fecha || ''}`);
      return haystack.includes(q);
    });

    const isFiltered = src !== 'all' || Boolean(q);
    if (countBadge) {
      countBadge.textContent = isFiltered
        ? `${filtered.length} de ${state.pressArticles.length}`
        : `${state.pressArticles.length} notas`;
    }

    if (!filtered.length) {
      newsBox.innerHTML = `
        <div class="prensa-empty-state">
          <span>No encontramos titulares para <strong>“${escapeHtml(state.pressSearchQuery || state.pressSourceFilter)}”</strong>.</span>
          <button type="button" class="btn-outline-gold" id="prensa-clear-filters-btn" style="padding:5px 12px;font-size:11.5px;">↺ Mostrar todas las noticias</button>
        </div>
      `;
      if (moreWrap) moreWrap.innerHTML = '';
      const clr = document.getElementById('prensa-clear-filters-btn');
      if (clr) {
        clr.onclick = () => {
          state.pressSourceFilter = 'all';
          state.pressSearchQuery = '';
          const inp = document.getElementById('prensa-search-input');
          const clrX = document.getElementById('prensa-search-clear');
          if (inp) inp.value = '';
          if (clrX) clrX.hidden = true;
          renderPressSourceChips();
          renderPressNewsList();
        };
      }
      return;
    }

    const limit = (isFiltered || state.pressExpanded) ? filtered.length : 6;
    const visible = filtered.slice(0, limit);

    newsBox.innerHTML = visible.map(n => {
      const urlSafe = safeUrl(n.url || 'https://www.servicioti.com.uy/', 'https://www.servicioti.com.uy/');
      const rawResumo = String(n.resumen || '');
      const resumo = rawResumo.length > 125 ? rawResumo.slice(0, 125) + '...' : rawResumo;
      return `
        <article class="clave-item" style="border-left-color:#71717a;">
          <div style="font-size:11px;color:var(--manya-gold);font-weight:800;margin-bottom:3px;">${escapeHtml(n.fuente)} • ${escapeHtml(n.fecha || n.fecha_raw || 'Reciente')}</div>
          <div style="font-size:13px;font-weight:700;color:#fff;margin-bottom:4px;">
            <a href="${escapeHtml(urlSafe)}" target="_blank" rel="noopener noreferrer" style="color:#ffffff;text-decoration:none;">${escapeHtml(n.titulo)}</a>
          </div>
          <p style="font-size:12px;color:#a1a1aa;line-height:1.4;margin-bottom:6px;">${escapeHtml(resumo)}</p>
          <a href="${escapeHtml(urlSafe)}" target="_blank" rel="noopener noreferrer" style="font-size:11px;color:var(--manya-gold);font-weight:800;text-decoration:none;">Leer en ${escapeHtml(n.fuente)} ↗</a>
        </article>
      `;
    }).join('');

    if (moreWrap) {
      const remaining = filtered.length - visible.length;
      if (!isFiltered && remaining > 0) {
        moreWrap.innerHTML = `<button type="button" class="btn-outline-gold" id="prensa-toggle-more-btn" style="padding:5px 12px;font-size:11.5px;width:100%;justify-content:center;">📰 Ver ${remaining} noticias más</button>`;
        const btnMore = document.getElementById('prensa-toggle-more-btn');
        if (btnMore) btnMore.onclick = () => { state.pressExpanded = true; renderPressNewsList(); };
      } else if (!isFiltered && state.pressExpanded && filtered.length > 6) {
        moreWrap.innerHTML = `<button type="button" class="btn-outline-gold" id="prensa-toggle-more-btn" style="padding:5px 12px;font-size:11.5px;width:100%;justify-content:center;">▲ Mostrar vista compacta</button>`;
        const btnLess = document.getElementById('prensa-toggle-more-btn');
        if (btnLess) btnLess.onclick = () => { state.pressExpanded = false; renderPressNewsList(); };
      } else {
        moreWrap.innerHTML = '';
      }
    }
  }

  function initPressControls(articles) {
    state.pressArticles = Array.isArray(articles) ? articles : [];
    state.pressSourceFilter = 'all';
    state.pressSearchQuery = '';
    state.pressExpanded = false;

    const searchInput = document.getElementById('prensa-search-input');
    const clearBtn = document.getElementById('prensa-search-clear');
    if (searchInput) {
      searchInput.oninput = () => {
        state.pressSearchQuery = searchInput.value || '';
        if (clearBtn) clearBtn.hidden = !state.pressSearchQuery;
        renderPressNewsList();
      };
    }
    if (clearBtn && searchInput) {
      clearBtn.onclick = () => {
        searchInput.value = '';
        state.pressSearchQuery = '';
        clearBtn.hidden = true;
        renderPressNewsList();
        searchInput.focus();
      };
    }
    renderPressSourceChips();
    renderPressNewsList();
  }

  function hydrateEditorialSection(digest) {
    if (!digest) return;
    const art = digest.articulo_principal || {};
    const set = (id, v) => { const el = document.getElementById(id); if (el && v) el.textContent = v; };

    set('editorial-headline', art.titulo || digest.titular_dia);
    if (art.parrafos && art.parrafos.length >= 3) {
      set('editorial-p1', art.parrafos[0]);
      set('editorial-p2', art.parrafos[1]);
      set('editorial-p3', art.parrafos[2]);
    }

    const pq = document.querySelector('.editorial-pullquote');
    if (pq && art.cita_destacada) {
      pq.innerHTML = `“${escapeHtml(art.cita_destacada)}”${art.autor_cita ? `<span style="display:block;font-size:12px;margin-top:6px;color:var(--manya-gold);">— ${escapeHtml(art.autor_cita)}</span>` : ''}`;
    }

    const clavesBox = document.getElementById('claves-editorial-container');
    if (clavesBox && digest.claves_60_segundos && digest.claves_60_segundos.length) {
      clavesBox.innerHTML = digest.claves_60_segundos.map(c => `
        <div class="clave-item">
          <div class="clave-item-title">${escapeHtml(c.icono || '⚽')} ${escapeHtml(c.titulo)}</div>
          <p class="clave-item-desc">${escapeHtml(c.detalle)}</p>
        </div>
      `).join('');
    }

    const prensaGrid = document.getElementById('prensa-nacional-grid');
    if (prensaGrid && digest.prismas_analisis) {
      const meta = {
        epica_tribuna: { icon: '🏟️', color: '#ffd100' },
        pizarron_tactico: { icon: '♟️', color: '#38bdf8' },
        trastienda_vestuario: { icon: '🔥', color: '#f87171' },
        aritmetica_campeonato: { icon: '📐', color: '#34d399' }
      };
      prensaGrid.innerHTML = Object.entries(digest.prismas_analisis).map(([k, item]) => {
        const m = meta[k] || { icon: '⚡', color: '#ffd100' };
        return `
          <div class="clave-item" style="border-left:3px solid ${m.color};background:#141419;padding:12px;border-radius:8px;">
            <div style="font-size:11.5px;color:${m.color};font-weight:800;margin-bottom:4px;">${m.icon} ${escapeHtml((item.eje || 'PRISMA').toUpperCase())} • ${escapeHtml(item.subtitulo || '')}</div>
            <p style="font-size:12.5px;color:#e4e4e7;line-height:1.45;margin:0;">“${escapeHtml(item.texto)}”</p>
          </div>
        `;
      }).join('');
    }

    if (digest.noticias_fuentes && digest.noticias_fuentes.length) {
      initPressControls(digest.noticias_fuentes);
    }
  }

  function renderGallery(items, currentFilter) {
    const grid = document.getElementById('gallery-main-grid');
    const loadMoreWrap = document.getElementById('gallery-load-more-wrap');
    if (!grid) return;

    const sportsOnly = (items || []).filter(it => !(it.id || '').startsWith('tattoo_') && (it.categoria || '').toLowerCase() !== 'tatuajes');
    const filter = currentFilter || 'all';
    const filtered = (filter === 'all') ? sportsOnly : sportsOnly.filter(it => (it.categoria || '').toLowerCase().includes(filter.toLowerCase()));

    if (!filtered.length) {
      grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:32px;color:var(--text-secondary);">No hay fotografías en esta categoría.</div>`;
      if (loadMoreWrap) loadMoreWrap.innerHTML = '';
      return;
    }

    const visible = filtered.slice(0, state.galleryLimit);
    grid.innerHTML = visible.map((item, idx) => {
      const is1891 = (item.cuenta === '1891.uy') || (item.url_post && item.url_post.includes('1891.uy'));
      const postUrl = safeUrl(item.url_post || (is1891 ? 'https://1891.uy/partidos' : 'https://www.instagram.com/oficialcap/'), 'https://www.instagram.com/oficialcap/');
      const badgeTxt = is1891 ? '📜 ARCHIVO 1891 BD' : `📸 ${(item.categoria || 'Peñarol').replace('-', ' ').toUpperCase()}`;
      const metaRight = item.fecha || (is1891 ? '1891 BD' : 'Temporada 2026');
      const imgPrimary = safeImgSrc(item.imagen_webp || item.imagen_jpg);
      const imgFallback = safeImgSrc(item.imagen_jpg || item.imagen_webp);
      return `
        <article class="ig-card" data-idx="${idx}">
          <div class="ig-card-link" role="button" tabindex="0" aria-label="Ampliar fotografía: ${escapeHtml(item.titulo)}" style="cursor:pointer;" title="Click para ampliar en alta definición">
            <div class="ig-img-wrap">
              <img class="manya-lazy-img" src="${escapeHtml(imgPrimary)}" data-fallback-src="${escapeHtml(imgFallback)}" alt="${escapeHtml(item.titulo)} - Club Atlético Peñarol" width="1280" height="720" loading="lazy" decoding="async" />
              <span class="ig-badge-tag">${escapeHtml(badgeTxt)}</span>
            </div>
          </div>
          <div class="ig-body">
            <div class="ig-meta">
              <span>${escapeHtml(item.cuenta || '@oficialcap')}</span>
              <span>📅 ${escapeHtml(metaRight)}</span>
            </div>
            <h3 class="ig-title"><a href="${escapeHtml(postUrl)}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.titulo)}</a></h3>
            <p class="ig-caption">${escapeHtml(item.descripcion || item.caption || '')}</p>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;gap:8px;">
              <button type="button" class="btn-outline-gold open-lightbox-btn" style="padding:4px 10px;font-size:11.5px;cursor:pointer;">🔍 Ampliar</button>
              <a href="${escapeHtml(postUrl)}" target="_blank" rel="noopener noreferrer" class="ig-external-btn" style="margin-top:0;">${is1891 ? '1891.uy ↗' : 'Fuente ↗'}</a>
            </div>
          </div>
        </article>
      `;
    }).join('');

    enhanceLazyImages(grid);

    const lightboxItems = filtered.map(it => Object.assign({}, it, {
      credito: it.fuente || it.cuenta || '@oficialcap'
    }));

    grid.querySelectorAll('.ig-card').forEach(card => {
      const idx = parseInt(card.getAttribute('data-idx'), 10);
      const trigger = () => openLightbox(lightboxItems, idx);
      const la = card.querySelector('.ig-card-link');
      if (la) {
        la.onclick = trigger;
        la.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); trigger(); } };
      }
      const zb = card.querySelector('.open-lightbox-btn');
      if (zb) zb.onclick = e => { e.stopPropagation(); trigger(); };
    });

    if (loadMoreWrap) {
      const rem = filtered.length - visible.length;
      if (rem > 0) {
        loadMoreWrap.innerHTML = `<button type="button" id="btn-gallery-load-more" class="btn-outline-gold" style="padding:10px 22px;font-size:13px;">📸 Ver más fotografías (+${rem} disponibles)</button>`;
        const lmBtn = document.getElementById('btn-gallery-load-more');
        if (lmBtn) {
          lmBtn.onclick = () => {
            state.galleryLimit += 8;
            renderGallery(items, filter);
          };
        }
      } else {
        loadMoreWrap.innerHTML = '';
      }
    }
  }

  function setupGalleryFilters(allItems) {
    const tabs = document.querySelectorAll('#gallery-filters .gallery-tab');
    tabs.forEach(tab => {
      tab.onclick = () => {
        tabs.forEach(t => {
          t.classList.remove('active');
          t.setAttribute('aria-selected', 'false');
        });
        tab.classList.add('active');
        tab.setAttribute('aria-selected', 'true');
        state.galleryFilter = tab.getAttribute('data-filter') || 'all';
        state.galleryLimit = 6;
        renderGallery(allItems, state.galleryFilter);
      };
    });
  }

  function renderInfluencersSection(influencers) {
    const grid = document.getElementById('influencers-grid');
    if (!grid || !influencers || !influencers.length) return;
    grid.innerHTML = influencers.map((inf, idx) => {
      const igUrl = safeUrl(inf.url_instagram || 'https://www.instagram.com/oficialcap/', 'https://www.instagram.com/oficialcap/');
      const avatarSrc = safeImgSrc(inf.avatar, 'assets/img/escudo_penarol_oficial.svg');
      const imgPrimary = safeImgSrc(inf.imagen_webp || inf.imagen_jpg);
      const imgFallback = safeImgSrc(inf.imagen_jpg || inf.imagen_webp);
      return `
        <article class="ig-card influencer-card" data-inf-idx="${idx}" style="background:#111115;border:1px solid rgba(255,209,0,0.25);border-radius:14px;overflow:hidden;display:flex;flex-direction:column;">
          <div style="padding:12px 16px;background:rgba(18,18,24,0.95);border-bottom:1px solid rgba(255,255,255,0.06);display:flex;align-items:center;justify-content:space-between;gap:10px;">
            <div style="display:flex;align-items:center;gap:10px;min-width:0;">
              <div class="ig-avatar-ring" style="width:40px;height:40px;flex-shrink:0;"><img src="${escapeHtml(avatarSrc)}" alt="${escapeHtml(inf.handle)}" width="40" height="40" style="border-radius:50%;object-fit:cover;" /></div>
              <div style="min-width:0;">
                <strong style="font-size:13.5px;color:#fff;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${escapeHtml(inf.nombre)} <span style="color:var(--manya-gold);">✓</span></strong>
                <div style="font-size:12px;color:var(--manya-gold);font-weight:700;">${escapeHtml(inf.handle)}</div>
              </div>
            </div>
            <a href="${escapeHtml(igUrl)}" target="_blank" rel="noopener noreferrer" class="btn-outline-gold" style="padding:4px 10px;font-size:11px;border-radius:999px;flex-shrink:0;text-decoration:none;">Seguir ↗</a>
          </div>
          <div class="ig-img-wrap" role="button" tabindex="0" aria-label="Ampliar publicación de ${escapeHtml(inf.handle)}: ${escapeHtml(inf.titulo)}" style="cursor:pointer;position:relative;aspect-ratio:16/9;overflow:hidden;">
            <img class="manya-lazy-img" src="${escapeHtml(imgPrimary)}" data-fallback-src="${escapeHtml(imgFallback)}" alt="${escapeHtml(inf.titulo)}" width="1280" height="720" loading="lazy" decoding="async" style="width:100%;height:100%;object-fit:cover;" />
            <span class="ig-badge-tag">${escapeHtml(inf.badge)}</span>
          </div>
          <div class="ig-body" style="padding:14px 16px;display:flex;flex-direction:column;flex-grow:1;justify-content:space-between;">
            <div>
              <div class="ig-meta" style="display:flex;justify-content:space-between;font-size:11.5px;color:var(--text-secondary);margin-bottom:8px;">
                <span>⚽ ${escapeHtml(inf.partido)}</span>
                <span style="color:#f87171;font-weight:800;">❤️ ${escapeHtml(inf.likes_formato)}</span>
              </div>
              <h3 style="font-size:14.5px;font-weight:900;color:#fff;margin:0 0 8px;line-height:1.35;">${escapeHtml(inf.titulo)}</h3>
              <p style="font-size:12.5px;color:#d4d4d8;line-height:1.5;margin:0 0 10px;">${escapeHtml(inf.descripcion)}</p>
            </div>
            <div style="display:flex;gap:8px;align-items:center;justify-content:space-between;padding-top:10px;border-top:1px solid rgba(255,255,255,0.06);">
              <button type="button" class="btn-outline-gold inf-zoom-btn" style="padding:5px 10px;font-size:11.5px;cursor:pointer;">🔍 Ampliar</button>
              <a href="${escapeHtml(igUrl)}" target="_blank" rel="noopener noreferrer" class="ig-external-btn" style="padding:5px 12px;font-size:11.5px;background:#ffd100;color:#09090b;font-weight:900;border-radius:6px;text-decoration:none;">Instagram ↗</a>
            </div>
          </div>
        </article>
      `;
    }).join('');

    enhanceLazyImages(grid);

    const lbItems = influencers.map(item => ({
      titulo: `${item.titulo} — ${item.handle}`,
      descripcion: item.descripcion,
      cuenta: item.handle,
      credito: `${item.nombre} (${item.handle})`,
      categoria: item.categoria || 'comunidad',
      fecha: item.partido || 'Temporada 2026',
      url_post: item.url_instagram,
      imagen_webp: item.imagen_webp,
      imagen_jpg: item.imagen_jpg
    }));

    grid.querySelectorAll('.influencer-card').forEach(card => {
      const idx = parseInt(card.getAttribute('data-inf-idx'), 10);
      const trigger = () => openLightbox(lbItems, idx);
      const iw = card.querySelector('.ig-img-wrap');
      if (iw) {
        iw.onclick = trigger;
        iw.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); trigger(); } };
      }
      const zb = card.querySelector('.inf-zoom-btn'); if (zb) zb.onclick = trigger;
    });
  }

  function renderTattooGallery(tattoos, filter = 'all') {
    const grid = document.getElementById('tattoo-cards-grid');
    const artistsList = document.getElementById('tattoo-artists-list');
    if (!grid || !tattoos || !tattoos.length) return;

    state.tattoos = tattoos;
    state.tattooFilter = filter;

    if (artistsList && !artistsList.children.length) {
      const seen = new Set();
      artistsList.innerHTML = tattoos.filter(t => t.tatuador && !seen.has(t.tatuador) && seen.add(t.tatuador)).slice(0, 6).map(a => {
        const igUrl = safeUrl(a.url_instagram || 'https://www.instagram.com/', 'https://www.instagram.com/');
        return `
          <a href="${escapeHtml(igUrl)}" target="_blank" rel="noopener noreferrer" class="tattoo-artist-chip" style="text-decoration:none;display:inline-flex;align-items:center;gap:8px;padding:6px 12px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,209,0,0.2);border-radius:999px;font-size:12px;color:#fff;">
            <span style="color:var(--manya-gold);font-weight:900;">💉</span><span><strong>${escapeHtml(a.tatuador)}</strong> (${escapeHtml(a.estudio || 'Montevideo')})</span>
          </a>
        `;
      }).join('');
    }

    const filtered = filter === 'all' ? tattoos : tattoos.filter(t => t.categoria === filter);
    grid.innerHTML = filtered.map((t, idx) => {
      const imgPrimary = safeImgSrc(t.imagen_webp || t.imagen_jpg);
      const imgFallback = safeImgSrc(t.imagen_jpg || t.imagen_webp);
      const igUrl = safeUrl(t.url_instagram || 'https://www.instagram.com/', 'https://www.instagram.com/');
      return `
        <article class="tattoo-card" data-tidx="${idx}" style="background:#111115;border:1px solid rgba(255,209,0,0.2);border-radius:12px;overflow:hidden;display:flex;flex-direction:column;">
          <div class="ig-img-wrap tattoo-media-trigger" role="button" tabindex="0" aria-label="Ampliar tatuaje: ${escapeHtml(t.titulo)}" title="Click para ampliar en alta definición" style="aspect-ratio:1/1;position:relative;cursor:pointer;">
            <img class="manya-lazy-img" src="${escapeHtml(imgPrimary)}" data-fallback-src="${escapeHtml(imgFallback)}" alt="${escapeHtml(t.titulo)}" width="600" height="600" loading="lazy" decoding="async" style="width:100%;height:100%;object-fit:cover;" />
            <span style="position:absolute;top:8px;left:8px;background:rgba(0,0,0,0.82);color:var(--manya-gold);border:1px solid var(--manya-gold);font-size:10px;padding:2px 8px;border-radius:6px;font-weight:800;">${escapeHtml(t.estilo || 'Tatuaje Aurinegro')}</span>
          </div>
          <div style="padding:12px;flex-grow:1;display:flex;flex-direction:column;justify-content:space-between;">
            <div>
              <div style="font-size:11px;color:var(--text-secondary);margin-bottom:4px;">📍 ${escapeHtml(t.zona_cuerpo || 'Piel Carbonera')} • ${escapeHtml(t.barrio || 'Montevideo')}</div>
              <h3 style="font-size:13.5px;font-weight:800;color:#fff;margin:0 0 6px;line-height:1.35;">${escapeHtml(t.titulo)}</h3>
              <p style="font-size:12px;color:#a1a1aa;margin:0 0 8px;line-height:1.4;">${escapeHtml(t.descripcion || '')}</p>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;padding-top:8px;border-top:1px solid rgba(255,255,255,0.06);font-size:11.5px;flex-wrap:wrap;">
              <span style="color:var(--manya-gold);font-weight:700;">${escapeHtml(t.tatuador)}</span>
              <div style="display:flex;align-items:center;gap:8px;">
                <button type="button" class="btn-outline-gold tattoo-zoom-btn" style="padding:3px 9px;font-size:11px;cursor:pointer;">🔍 Ampliar</button>
                <a href="${escapeHtml(igUrl)}" target="_blank" rel="noopener noreferrer" style="color:#ffd100;text-decoration:none;font-weight:700;">IG ↗</a>
              </div>
            </div>
          </div>
        </article>
      `;
    }).join('');

    enhanceLazyImages(grid);

    const lbTattoos = filtered.map(t => Object.assign({}, t, {
      _kind: 'tattoo',
      url_post: t.url_instagram || 'https://www.instagram.com/explore/tags/pe%C3%B1arolenlapiel/',
      credito: `${t.tatuador || 'Artista Aurinegro'}${t.estudio ? ' • ' + t.estudio : ''}${t.handle_instagram ? ' (' + t.handle_instagram + ')' : ''}`
    }));

    grid.querySelectorAll('.tattoo-card').forEach(card => {
      const idx = parseInt(card.getAttribute('data-tidx'), 10);
      const trigger = () => openLightbox(lbTattoos, idx);
      const imgWrap = card.querySelector('.tattoo-media-trigger');
      if (imgWrap) {
        imgWrap.onclick = trigger;
        imgWrap.onkeydown = e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); trigger(); } };
      }
      const zoomBtn = card.querySelector('.tattoo-zoom-btn');
      if (zoomBtn) zoomBtn.onclick = e => { e.stopPropagation(); trigger(); };
    });
  }

  function setupTattooFilters(tattoos) {
    const tabs = document.querySelectorAll('#tattoo-filter-tabs .tattoo-filter-btn');
    tabs.forEach(btn => {
      btn.onclick = () => {
        tabs.forEach(b => {
          b.classList.remove('active');
          b.setAttribute('aria-selected', 'false');
        });
        btn.classList.add('active');
        btn.setAttribute('aria-selected', 'true');
        renderTattooGallery(tattoos, btn.getAttribute('data-cat') || 'all');
      };
    });
  }

  function renderEfemerides(efem) {
    if (!efem || !efem.partidos_historicos) return;
    const tagEl = document.getElementById('efemerides-date-tag');
    if (tagEl && efem.dia_mes) tagEl.textContent = efem.dia_mes;

    const gridEl = document.getElementById('efemerides-matches-grid');
    if (gridEl && efem.partidos_historicos.length) {
      gridEl.innerHTML = efem.partidos_historicos.slice(0, 6).map(m => `
        <article class="efemeride-item">
          <div class="efemeride-top-line"><span class="efemeride-year">${escapeHtml(m.ano)}</span><span class="efemeride-torneo">${escapeHtml(m.torneo || 'Torneo Oficial')}</span></div>
          <div class="efemeride-score">${escapeHtml(m.resultado)}</div>
          <div class="efemeride-meta">
            <div>🏟️ ${escapeHtml(m.estadio || 'Escenario Oficial')}</div>
            ${m.goles_detalle ? `<div style="margin-top:4px;color:#d4d4d8;">⚽ ${escapeHtml(m.goles_detalle)}</div>` : ''}
          </div>
        </article>
      `).join('');
    }

    const gloriasEl = document.getElementById('efemerides-glorias-line');
    if (gloriasEl && efem.cumpleanos_glorias && efem.cumpleanos_glorias.length) {
      const nombres = Array.from(new Set(efem.cumpleanos_glorias.map(g => g.nombre))).map(n => `<strong>${escapeHtml(n)}</strong>`).join(' • ');
      gloriasEl.innerHTML = `<span>🎂 <strong>Glorias del Club:</strong> En esta fecha celebran su natalicio: ${nombres}.</span>`;
    }
  }

  // ==================== TRIVIA INTERACTIVA ====================
  let triviaAudioEnabled = true;
  let triviaState = { category: 'all', currentIndex: 0, score: 0, streak: 0, maxStreak: 0, answered: false, questionsPool: [] };

  function playAudioTone(type) {
    if (!triviaAudioEnabled) return;
    try {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (!AC) return;
      const ctx = new AC(), osc = ctx.createOscillator(), gain = ctx.createGain();
      osc.connect(gain); gain.connect(ctx.destination);
      osc.type = type === 'wrong' ? 'triangle' : 'sine';
      osc.frequency.setValueAtTime(type === 'wrong' ? 250 : 587.33, ctx.currentTime);
      osc.frequency.exponentialRampToValueAtTime(type === 'wrong' ? 165 : 880, ctx.currentTime + 0.14);
      gain.gain.setValueAtTime(0.08, ctx.currentTime);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.24);
      osc.start(); osc.stop(ctx.currentTime + 0.24);
    } catch (_) {}
  }

  function prepareTriviaQuestion(q) {
    const paired = q.opts.map((text, idx) => ({ text, isCorrect: idx === q.ans }));
    for (let i = paired.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [paired[i], paired[j]] = [paired[j], paired[i]];
    }
    return Object.assign({}, q, { opts: paired.map(p => p.text), ans: paired.findIndex(p => p.isCorrect) });
  }

  function getTriviaQuestionsPool(cat) {
    const list = (!cat || cat === 'all') ? TRIVIA_QUESTIONS : TRIVIA_QUESTIONS.filter(q => q.cat === cat);
    return [...(list.length ? list : TRIVIA_QUESTIONS)].sort(() => Math.random() - 0.5).map(prepareTriviaQuestion);
  }

  function renderTrivia() {
    const box = document.getElementById('trivia-box');
    if (!box) return;
    if (!triviaState.questionsPool.length) triviaState.questionsPool = getTriviaQuestionsPool(triviaState.category);

    const pool = triviaState.questionsPool, total = pool.length, idx = triviaState.currentIndex;
    if (idx >= total) {
      const pct = Math.round((triviaState.score / (total * 100)) * 100);
      box.innerHTML = `
        <div class="trivia-container trivia-game-over">
          <div style="font-size:36px;margin-bottom:8px;">🏆</div>
          <h4 style="font-size:19px;color:#fff;margin-bottom:6px;">¡Trivia Completada! ${escapeHtml(triviaState.score)} pts (${escapeHtml(pct)}%)</h4>
          <p style="font-size:13px;color:#d4d4d8;margin-bottom:14px;">Mejor racha: 🔥 x${escapeHtml(triviaState.maxStreak)}</p>
          <button type="button" class="btn-manya" id="trivia-restart-btn">🔄 Jugar de Nuevo</button>
        </div>`;
      const rb = box.querySelector('#trivia-restart-btn');
      if (rb) rb.onclick = () => { triviaState.currentIndex = 0; triviaState.score = 0; triviaState.streak = 0; triviaState.maxStreak = 0; triviaState.questionsPool = getTriviaQuestionsPool(triviaState.category); renderTrivia(); };
      return;
    }

    const item = pool[idx];
    triviaState.answered = false;
    const cats = [{ id: 'all', label: 'Todas' }, { id: 'libertadores', label: '🏆 Libertadores' }, { id: 'clasicos', label: '⚡ Clásicos' }, { id: 'idolos', label: '⭐ Ídolos' }, { id: 'records', label: '📊 Récords' }, { id: 'cds', label: '🏟️ CDS' }];

    box.innerHTML = `
      <div class="trivia-container">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
          <div class="trivia-cat-chips">${cats.map(c => `<button type="button" class="trivia-chip ${triviaState.category === c.id ? 'active' : ''}" data-cat="${escapeHtml(c.id)}">${escapeHtml(c.label)}</button>`).join('')}</div>
          <button type="button" id="trivia-sound-toggle" aria-label="${triviaAudioEnabled ? 'Silenciar efectos de sonido' : 'Activar efectos de sonido'}" style="background:transparent;border:1px solid rgba(255,255,255,0.15);color:#d4d4d8;padding:4px 8px;border-radius:6px;cursor:pointer;font-size:12px;">${triviaAudioEnabled ? '🔊' : '🔇'}</button>
        </div>
        <div class="trivia-stats-row">
          <span>Pregunta <strong>${idx + 1}</strong> de ${total} • <em style="color:var(--manya-gold);font-style:normal;">${escapeHtml(item.catName)}</em></span>
          <span style="color:var(--manya-gold);font-weight:800;font-family:'JetBrains Mono',monospace;">${escapeHtml(triviaState.score)} pts</span>
        </div>
        <div class="trivia-progress-bar-wrap"><div class="trivia-progress-fill" style="width:${Math.round((idx / total) * 100)}%;"></div></div>
        <h4 class="trivia-q-title">${escapeHtml(item.q)}</h4>
        <div class="trivia-opts-grid" id="trivia-opts">
          ${item.opts.map((o, i) => `<button type="button" class="trivia-opt-btn" data-idx="${i}"><span class="trivia-opt-letter">${['A','B','C','D'][i]}</span><span>${escapeHtml(o)}</span></button>`).join('')}
        </div>
        <div id="trivia-feedback" style="display:none;"></div>
      </div>`;

    const sb = box.querySelector('#trivia-sound-toggle');
    if (sb) sb.onclick = () => { triviaAudioEnabled = !triviaAudioEnabled; sb.textContent = triviaAudioEnabled ? '🔊' : '🔇'; };
    box.querySelectorAll('.trivia-chip').forEach(btn => {
      btn.onclick = () => { triviaState = { category: btn.getAttribute('data-cat'), currentIndex: 0, score: 0, streak: 0, maxStreak: 0, answered: false, questionsPool: getTriviaQuestionsPool(btn.getAttribute('data-cat')) }; renderTrivia(); };
    });

    const fb = box.querySelector('#trivia-feedback');
    const optBtns = box.querySelectorAll('#trivia-opts .trivia-opt-btn');
    optBtns.forEach(btn => {
      btn.onclick = () => {
        if (triviaState.answered) return;
        triviaState.answered = true;
        optBtns.forEach(b => { b.disabled = true; });
        const chosen = parseInt(btn.getAttribute('data-idx'), 10);
        if (chosen === item.ans) {
          playAudioTone('correct');
          triviaState.streak++;
          triviaState.maxStreak = Math.max(triviaState.maxStreak, triviaState.streak);
          const gained = 100 + (triviaState.streak - 1) * 25;
          triviaState.score += gained;
          btn.classList.add('is-correct');
          fb.className = 'trivia-feedback-card correct';
          fb.innerHTML = `<div style="font-weight:800;color:#22c55e;">✅ ¡Correcto! (+${gained} pts)</div><div class="trivia-feedback-exp">${escapeHtml(item.exp)}</div><button type="button" class="btn-manya" style="margin-top:10px;padding:7px 14px;font-size:13px;" id="trivia-next-btn">Siguiente →</button>`;
        } else {
          playAudioTone('wrong');
          triviaState.streak = 0;
          btn.classList.add('is-wrong');
          const cBtn = box.querySelector(`#trivia-opts .trivia-opt-btn[data-idx="${item.ans}"]`);
          if (cBtn) cBtn.classList.add('is-correct');
          fb.className = 'trivia-feedback-card wrong';
          fb.innerHTML = `<div style="font-weight:800;color:#ef4444;">❌ Respuesta Histórica Certificada</div><div class="trivia-feedback-exp">${escapeHtml(item.exp)}</div><button type="button" class="btn-manya" style="margin-top:10px;padding:7px 14px;font-size:13px;" id="trivia-next-btn">Siguiente →</button>`;
        }
        fb.style.display = 'block';
        const nb = box.querySelector('#trivia-next-btn');
        if (nb) nb.onclick = () => { triviaState.currentIndex++; renderTrivia(); };
      };
    });
  }

  // ==================== SCROLL-SPY, PWA INSTALL CTA & BACK-TO-TOP ====================
  function initScrollSpy() {
    const navLinks = Array.from(document.querySelectorAll('.manya-nav a[href^="#"]'));
    if (!navLinks.length) return;

    const pairs = navLinks
      .map(link => {
        const id = (link.getAttribute('href') || '').slice(1);
        const section = id ? document.getElementById(id) : null;
        return section ? { id, link, section } : null;
      })
      .filter(Boolean);

    if (!pairs.length) return;

    let currentActiveId = pairs[0].id;
    const setActiveLink = (targetId) => {
      if (!targetId || targetId === currentActiveId) return;
      currentActiveId = targetId;
      pairs.forEach(({ id, link }) => {
        const isMatch = id === targetId;
        link.classList.toggle('active', isMatch);
        if (isMatch) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
    };

    pairs.forEach(({ id, link }) => {
      link.addEventListener('click', () => setActiveLink(id));
    });

    if ('IntersectionObserver' in window) {
      const visibleSet = new Set();
      const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) visibleSet.add(entry.target.id);
          else visibleSet.delete(entry.target.id);
        });
        if (visibleSet.size > 0) {
          const topMost = pairs.find(p => visibleSet.has(p.id));
          if (topMost) setActiveLink(topMost.id);
        }
      }, {
        rootMargin: '-18% 0px -65% 0px',
        threshold: [0, 0.1, 0.25]
      });

      pairs.forEach(({ section }) => observer.observe(section));
    }

    window.addEventListener('scroll', () => {
      if (window.scrollY < 100) {
        setActiveLink(pairs[0].id);
      } else if (window.innerHeight + window.scrollY >= document.documentElement.scrollHeight - 60) {
        setActiveLink(pairs[pairs.length - 1].id);
      }
    }, { passive: true });
  }

  function initPwaInstall() {
    const installBtn = document.getElementById('pwa-install-btn');
    if (!installBtn) return;

    let deferredPrompt = null;

    window.addEventListener('beforeinstallprompt', (e) => {
      e.preventDefault();
      deferredPrompt = e;
      installBtn.hidden = false;
    });

    installBtn.addEventListener('click', async () => {
      if (!deferredPrompt) return;
      try {
        deferredPrompt.prompt();
        const choice = await deferredPrompt.userChoice;
        if (choice && choice.outcome === 'accepted') {
          installBtn.hidden = true;
          showToast('📲 ¡Manya ServicioTI instalada en tu dispositivo!', 'success');
        } else {
          showToast('ℹ️ Podés instalar la App cuando gustes desde el menú superior', 'info');
        }
      } catch (_) {}
      deferredPrompt = null;
    });

    window.addEventListener('appinstalled', () => {
      installBtn.hidden = true;
      deferredPrompt = null;
      showToast('🎉 ¡App Manya ServicioTI lista en tu pantalla de inicio!', 'success');
    });
  }

  function initBackToTop() {
    let btn = document.getElementById('manya-back-to-top');
    if (!btn) {
      btn = document.createElement('button');
      btn.id = 'manya-back-to-top';
      btn.type = 'button';
      btn.title = 'Volver arriba';
      btn.setAttribute('aria-label', 'Volver al inicio de la página');
      btn.textContent = '↑';
      document.body.appendChild(btn);
    }
    btn.onclick = () => window.scrollTo({ top: 0, behavior: 'smooth' });
    window.addEventListener('scroll', () => {
      if (window.scrollY > 520) btn.classList.add('visible');
      else btn.classList.remove('visible');
    }, { passive: true });
  }

  function setupLivePolling() {
    if (window._manyaLivePolling) return;
    window._manyaLivePolling = setInterval(async () => {
      if (state.live && (state.live.fase_partido === 'EN_VIVO' || state.live.fase_partido === 'PREVIA')) {
        const fresh = await loadJsonSafe('data/live_status.json');
        if (fresh && fresh.actualizado !== state.live.actualizado) {
          state.live = fresh;
          renderMatchHero(fresh);
          renderStandings();
        }
      }
    }, 45000);
  }

  async function init() {
    setupLightbox();
    initScrollSpy();
    initPwaInstall();
    initBackToTop();
    initTacticalBoard();

    const [live, digest, ig, galleries, squad, history, escudosCatalog, h2hActivo, efemeridesHoy, rivalIntel, influencers, tattoos] = await Promise.all([
      loadJsonSafe('data/live_status.json'),
      loadJsonSafe('data/news_digest.json'),
      loadJsonSafe('data/instagram_feed.json'),
      loadJsonSafe('data/galleries.json'),
      loadJsonSafe('data/squad_2026.json'),
      loadJsonSafe('data/history_1891.json'),
      loadJsonSafe('data/escudos_uruguay.json'),
      loadJsonSafe('data/historial_activo.json'),
      loadJsonSafe('data/efemerides_hoy.json'),
      loadJsonSafe('data/rival_intelligence.json'),
      loadJsonSafe('data/influencers_feed.json'),
      loadJsonSafe('data/tatuajes_manya.json')
    ]);

    if (escudosCatalog) state.escudosCatalog = escudosCatalog;

    if (live) {
      state.live = live;
      state.standingsTab = live.torneo_activo_id || 'anual';
      renderMatchHero(live);
      renderStandingsTabs();
      renderStandings();
      initSimulator();
      setupLivePolling();
    }

    if (h2hActivo) renderHeadToHead(h2hActivo);
    if (efemeridesHoy) renderEfemerides(efemeridesHoy);
    if (rivalIntel) renderRivalIntelligence(rivalIntel);
    if (influencers && influencers.length) renderInfluencersSection(influencers);
    if (tattoos && tattoos.length) { renderTattooGallery(tattoos); setupTattooFilters(tattoos); }

    const allGalleryItems = (galleries && galleries.length) ? galleries : (ig || []);
    renderHeroInstagramPost(allGalleryItems.length ? allGalleryItems[0] : null, digest);
    if (allGalleryItems.length) {
      state.galleries = allGalleryItems;
      renderGallery(allGalleryItems, 'all');
      setupGalleryFilters(allGalleryItems);
    }

    if (squad && squad.jugadores && squad.jugadores.length >= 11) {
      state.squad = squad;
      state.initialLineup = JSON.parse(JSON.stringify(squad.jugadores.filter(p => p.titular).slice(0, 11)));
      state.initialBench = JSON.parse(JSON.stringify(squad.jugadores.filter(p => !p.titular)));
      state.lineup = JSON.parse(JSON.stringify(state.initialLineup));
      state.bench = JSON.parse(JSON.stringify(state.initialBench));
      state.activeLineupPreset = 'ideal';
      updatePresetButtonsUI();
      renderTacticalBoard();
    }

    if (digest) {
      const bUrl = safeUrl(digest.blogger_post_url || 'https://www.servicioti.com.uy/p/penarol-proximo-partido-radiografia.html', 'https://www.servicioti.com.uy/p/penarol-proximo-partido-radiografia.html');
      document.querySelectorAll('.dynamic-blogger-link').forEach(a => { a.href = bUrl; });
      hydrateEditorialSection(digest);
    }

    renderTrivia();

    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').then(reg => reg.update()).catch(() => {});
    }
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init);
  else init();
})();
