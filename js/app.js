/* -*- coding: utf-8 -*-
 * MOTOR INTERACTIVO MANYA SERVICIOTI (js/app.js)
 * Controla:
 * 1. Hidratación en tiempo real desde /data/*.json (ESPN API, Clima CDS, Noticias GFlash 3.8, Galería Gemini Web Vision).
 * 2. Cuenta regresiva al segundo para el próximo partido de Peñarol.
 * 3. Simulador Interactivo de la Tabla Anual Acumulada.
 * 4. Pizarra Táctica "Armá tu 11 Titular" con cambio de esquema (4-2-3-1, 4-3-3, 4-4-2), cambios desde el banco y exportación PNG.
 * 5. Trivia Interactiva "Sabiduría Carbonera 1891".
 */
(function () {
  'use strict';

  let state = {
    live: null,
    digest: null,
    ig: [],
    squad: null,
    history: null,
    escudosCatalog: null,
    formation: '4-2-3-1',
    selectedSlotIndex: null,
    lineup: [],
    bench: [],
    simPointsDelta: 0,
    standingsTab: 'clausura',
    triviaIndex: 0,
    triviaScore: 0
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
      { x: 70, y: 44, role: 'MC' },
      { x: 30, y: 44, role: 'MC' },
      { x: 78, y: 22, role: 'ED' },
      { x: 22, y: 22, role: 'EI' },
      { x: 50, y: 14, role: 'DC' }
    ],
    '4-4-2': [
      { x: 50, y: 88, role: 'ARQ' },
      { x: 82, y: 70, role: 'LD' },
      { x: 62, y: 74, role: 'DFC' },
      { x: 38, y: 74, role: 'DFC' },
      { x: 18, y: 70, role: 'LI' },
      { x: 82, y: 46, role: 'MD' },
      { x: 60, y: 50, role: 'MC' },
      { x: 40, y: 50, role: 'MC' },
      { x: 18, y: 46, role: 'MI' },
      { x: 62, y: 18, role: 'DC' },
      { x: 38, y: 18, role: 'DC' }
    ]
  };

  const TRIVIA_QUESTIONS = [
    {
      cat: 'general',
      catName: 'Fundación & Raíces',
      q: '¿En qué fecha exacta y en qué histórico enclave se fundó nuestra institución (CURCC / Club Atlético Peñarol)?',
      opts: ['28 de septiembre de 1891 en la Villa Peñarol', '14 de mayo de 1899 en La Blanqueada', '18 de julio de 1900 en el Centro de Montevideo', '25 de agosto de 1891 en Pocitos'],
      ans: 0,
      exp: 'El 28 de septiembre de 1891 los trabajadores ferroviarios británicos y criollos fundaron el Central Uruguay Railway Cricket Club (CURCC) en la Villa Peñarol, decano indiscutido del fútbol uruguayo.'
    },
    {
      cat: 'libertadores',
      catName: 'Copas Libertadores',
      q: '¿Quién convirtió el gol agónico en el minuto 120 en Santiago de Chile para ganar la quinta Copa Libertadores en 1987?',
      opts: ['Diego "La Fiera" Aguirre', 'Fernando Morena', 'Alberto Spencer', 'Jorge Cabrera'],
      ans: 0,
      exp: 'Diego Aguirre recibió de zurda y cruzó un remate legendario a los 120 minutos ante América de Cali en el Estadio Nacional de Santiago, sellando la quinta Libertadores.'
    },
    {
      cat: 'libertadores',
      catName: 'Copas Libertadores',
      q: '¿Quién es el máximo goleador histórico de toda la Copa CONMEBOL Libertadores de América con 54 goles?',
      opts: ['Alberto "Cabeza Mágica" Spencer', 'Fernando Morena', 'Pedro Virgilio Rocha', 'Juan Alberto Schiaffino'],
      ans: 0,
      exp: 'Alberto Spencer ostenta el récord absoluto de la Copa Libertadores con 54 goles (48 de ellos convertidos con la gloriosa camiseta de Peñarol).'
    },
    {
      cat: 'libertadores',
      catName: 'Copas Libertadores',
      q: '¿Contra qué tres gigantes de Europa conquistó Peñarol sus 3 Copas Intercontinentales del Mundo?',
      opts: ['Benfica (1961), Real Madrid (1966) y Aston Villa (1982)', 'Milan (1961), Real Madrid (1966) y Liverpool (1982)', 'Benfica (1960), Inter (1966) y Hamburgo (1982)', 'Ajax (1961), Real Madrid (1966) y Juventus (1982)'],
      ans: 0,
      exp: 'Peñarol fue tricampeón del mundo venciendo al Benfica de Eusébio (1961), al Real Madrid en Montevideo y en el Bernabéu (1966) y al Aston Villa en Tokio (1982).'
    },
    {
      cat: 'idolos',
      catName: 'Ídolos Eternos',
      q: '¿Cómo se llama el legendario capitán que disputó 574 partidos oficiales jugando exclusivamente en Peñarol toda su carrera?',
      opts: ['Néstor "Tito" Gonçalves', 'Obdulio Varela', 'William Martínez', 'Walter Olivera'],
      ans: 0,
      exp: 'Néstor "Tito" Gonçalves, el "Capitán de Capitanes", defendió únicamente la camiseta oro y carbón entre 1957 y 1970, conquistando 3 Libertadores, 2 Intercontinentales y 9 Campeonatos Uruguayos.'
    },
    {
      cat: 'records',
      catName: 'Récords & Hazañas',
      q: '¿Qué récord imbatible estableció Fernando Morena el 16 de julio de 1978 ante Huracán Buceo en el Estadio Centenario?',
      opts: ['Anotó 7 goles en un mismo partido oficial', 'Convirtió 5 goles de cabeza en un solo tiempo', 'Marcó 3 goles en menos de 4 minutos', 'Anotó 4 goles de tiro libre en un partido'],
      ans: 0,
      exp: 'Fernando Morena anotó 7 goles en la victoria 7-0 ante Huracán Buceo, récord absoluto en la historia de la Primera División uruguaya.'
    },
    {
      cat: 'records',
      catName: 'Récords & Hazañas',
      q: '¿Cuántos minutos con valla invicta consecutiva acumuló Ladislao Mazurkiewicz en 1968, récord récord histórico del fútbol uruguayo?',
      opts: ['987 minutos', '720 minutos', '840 minutos', '1040 minutos'],
      ans: 0,
      exp: 'Ladislao Mazurkiewicz mantuvo su arco invicto durante 987 minutos (casi 11 partidos completos) en el Campeonato Uruguayo de 1968, marca insuperada.'
    },
    {
      cat: 'clasicos',
      catName: 'Clásicos Inolvidables',
      q: '¿Por qué se conoce al clásico del 23 de abril de 1987 como "El Clásico de los 8 contra 11"?',
      opts: ['Peñarol sufrió 3 expulsiones y aun así ganó 2-1 con gol de Diego Aguirre', 'Nacional jugó con 8 futbolistas por lesión', 'Peñarol defendió un 0-0 con 8 jugadores durante 85 minutos', 'El partido terminó con 8 jugadores aurinegros festejando'],
      ans: 0,
      exp: 'Con 3 futbolistas menos por expulsiones, el Peñarol de Washington Tabárez atacó heroicamente y Diego Aguirre anotó el 2-1 definitivo en el minuto 82.'
    },
    {
      cat: 'clasicos',
      catName: 'Clásicos Inolvidables',
      q: '¿Qué hecho histórico originó el célebre "Clásico de la Fuga" el 9 de octubre de 1949?',
      opts: ['Nacional perdía 2-0 ante la Máquina del 49 y decidió no salir a jugar el 2° tiempo', 'Peñarol ganó 5-0 escapándose en la Tabla Anual', 'El clásico se suspendió por un apagón en el Centenario', 'El arquero rival se retiró por el túnel sin autorización'],
      ans: 0,
      exp: 'Peñarol arrollaba 2-0 con goles de Ghiggia y Míguez; en el entretiempo, Nacional abandonó el Estadio Centenario por la chimenea/ventana del vestuario sin disputar el complemento.'
    },
    {
      cat: 'clasicos',
      catName: 'Clásicos Inolvidables',
      q: '¿Cuál fue el marcador del histórico clásico del 27 de abril de 2014, mayor goleada clásica en torneos cortos modernos?',
      opts: ['Peñarol 5 - 0 Nacional', 'Peñarol 4 - 0 Nacional', 'Peñarol 5 - 1 Nacional', 'Peñarol 6 - 0 Nacional'],
      ans: 0,
      exp: 'Histórico 5 a 0 aurinegro con goles de Marcelo Zalayeta, Damián Macaluso, Jorge "Japo" Rodríguez y doblete inolvidable de Luis Aguiar.'
    },
    {
      cat: 'records',
      catName: 'Récords & Hazañas',
      q: '¿Cuántos goles oficiales convirtió Fernando Morena con la camiseta del Club Atlético Peñarol según 1891 BD?',
      opts: ['350 goles', '280 goles', '310 goles', '215 goles'],
      ans: 0,
      exp: 'Fernando Morena es el máximo artillero de la historia del Decano con 350 goles oficiales certificados por la Comisión de Historia y Patrimonio de Peñarol.'
    },
    {
      cat: 'cds',
      catName: 'Estadio Campeón del Siglo',
      q: '¿En qué fecha se inauguró oficialmente el Estadio Campeón del Siglo y quién convirtió el primer gol en su campo?',
      opts: ['28 de marzo de 2016 — Diego Forlán', '28 de septiembre de 2015 — Marcelo Zalayeta', '19 de abril de 2016 — Leonardo Fernández', '31 de octubre de 2016 — Diego Aguirre'],
      ans: 0,
      exp: 'El Campeón del Siglo se inauguró el 28 de marzo de 2016 con triunfo 4-1 ante River Plate argentino; Diego Forlán convirtió el histórico primer gol en la Catedral.'
    },
    {
      cat: 'records',
      catName: 'Récords & Hazañas',
      q: '¿En qué años conquistó Peñarol sus dos célebres Quinquenios de Oro en el Campeonato Uruguayo?',
      opts: ['1958-1962 y 1993-1997', '1960-1964 y 1995-1999', '1955-1959 y 1990-1994', '1965-1969 y 1980-1984'],
      ans: 0,
      exp: 'Peñarol es el único club uruguayo con dos Quinquenios de Oro: 1958-1962 (bajo Hugo Bagnulo y Roberto Scarone) y 1993-1997 (con Gregorio Pérez y Pablo Bengoechea).'
    },
    {
      cat: 'general',
      catName: 'Distinciones Mundiales',
      q: '¿Qué histórica distinción otorgó la IFFHS a Peñarol en septiembre de 2009 tras el balance del siglo?',
      opts: ['Club Campeón del Siglo XX de Sudamérica (con 531 puntos)', 'Mejor club de la década de 1980', 'Club con mayor hinchada proporcional del planeta', 'Institución deportiva más laureada de América'],
      ans: 0,
      exp: 'La Federación Internacional de Historia y Estadística de Fútbol (IFFHS) proclamó oficialmente a Peñarol como el Mejor Club del Siglo XX de Sudamérica por su palmarés continental.'
    },
    {
      cat: 'libertadores',
      catName: 'Copas Libertadores',
      q: '¿Quién anotó el gol agónico en el minuto 89 en Santiago de Chile para consagrar a Peñarol campeón de América ante Cobreloa en 1982?',
      opts: ['Fernando Morena', 'Venancio Ramos', 'Jair Gonçalves', 'Ernesto Vargas'],
      ans: 0,
      exp: 'Tras empatar 0-0 en Montevideo, Morena conectó de derecha un centro de Ramos a los 89 minutos en el Estadio Nacional de Santiago, conquistando la cuarta Libertadores.'
    },
    {
      cat: 'idolos',
      catName: 'Ídolos Eternos',
      q: '¿Quién fue el capitán y emblema del Segundo Quinquenio (1993-1997), célebre por su precisión quirúrgica en tiros libres?',
      opts: ['Pablo Javier Bengoechea', 'Gabriel Cedrés', 'Antonio Pacheco', 'Darío Silva'],
      ans: 0,
      exp: 'Pablo "El Profesor" Bengoechea fue el capitán y arquitecto del Quinquenio 93-97, autor de goles clásicos decisivos y dueño de una pegada de tiro libre inolvidable.'
    },
    {
      cat: 'idolos',
      catName: 'Ídolos Eternos',
      q: '¿Qué ídolo moderno disputó 475 partidos oficiales con Peñarol en el siglo XXI y conquistó 8 títulos de Campeón Uruguayo?',
      opts: ['Antonio "Tony" Pacheco', 'Marcelo Zalayeta', 'Darío Rodríguez', 'Cristian "Cebolla" Rodríguez'],
      ans: 0,
      exp: 'Antonio "Tony" Pacheco vistió la aurinegra en 475 encuentros oficiales, convirtiéndose en el gran referente del siglo XXI y en uno de los jugadores más queridos de la hinchada.'
    },
    {
      cat: 'libertadores',
      catName: 'Copas Libertadores',
      q: '¿Quién anotó el primer gol de la historia de la Copa Libertadores el 19 de abril de 1960 en la goleada 7-1 de Peñarol a Jorge Wilstermann?',
      opts: ['Carlos "Lucho" Borges', 'Alberto Spencer', 'Luis Cubilla', 'José Sasía'],
      ans: 0,
      exp: 'Carlos "Lucho" Borges abrió la cuenta a los 13 minutos, convirtiendo el primer gol de la historia de la Copa Libertadores de América.'
    },
    {
      cat: 'records',
      catName: 'Récords & Hazañas',
      q: '¿Cuál es el récord histórico de partidos oficiales invicto en el Campeonato Uruguayo que ostenta Peñarol?',
      opts: ['56 partidos consecutivos invicto (1966-1969)', '42 partidos consecutivos invicto', '34 partidos consecutivos invicto', '62 partidos consecutivos invicto'],
      ans: 0,
      exp: 'Entre 1966 y 1969, el Glorioso Peñarol hilvanó 56 partidos consecutivos sin conocer la derrota en el Campeonato Uruguayo, récord absoluto hasta nuestros días.'
    },
    {
      cat: 'libertadores',
      catName: 'Copas Libertadores',
      q: '¿En qué final épica de Copa Libertadores Peñarol perdía 0-2 en Santiago y terminó consagrándose campeón con remontada 4-2 ante River Plate argentino?',
      opts: ['Final de 1966 en Santiago de Chile', 'Final de 1961 en San Pablo', 'Final de 1982 en Santiago', 'Final de 1960 en Asunción'],
      ans: 0,
      exp: 'El 20 de mayo de 1966 en el Estadio Nacional de Santiago, Peñarol remontó un 0-2 para ganar 4-2 en tiempo extra con goles de Spencer (2), Abbadie y Rocha.'
    }
  ];

  async function loadJsonSafe(path) {
    try {
      const r = await fetch(path + '?v=' + Date.now());
      if (!r.ok) return null;
      return await r.json();
    } catch (_) {
      return null;
    }
  }

  function startCountdown(isoString) {
    if (!isoString) return;
    const target = new Date(isoString).getTime();
    if (isNaN(target)) return;

    if (window._manyaCountdownInterval) {
      clearInterval(window._manyaCountdownInterval);
    }

    function tick() {
      const now = Date.now();
      const diff = Math.max(0, target - now);
      const d = Math.floor(diff / 86400000);
      const h = Math.floor((diff % 86400000) / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      const elD = document.getElementById('cd-days');
      const elH = document.getElementById('cd-hours');
      const elM = document.getElementById('cd-mins');
      const elS = document.getElementById('cd-secs');
      if (elD) elD.textContent = String(d).padStart(2, '0');
      if (elH) elH.textContent = String(h).padStart(2, '0');
      if (elM) elM.textContent = String(m).padStart(2, '0');
      if (elS) elS.textContent = String(s).padStart(2, '0');

      if (diff === 0) {
        const tDate = document.getElementById('hero-match-date');
        if (tDate) {
          tDate.textContent = '🔴 ¡HORA DE JUGAR! • EN VIVO / POR COMENZAR';
          tDate.style.color = '#ef4444';
        }
      }
    }
    tick();
    window._manyaCountdownInterval = setInterval(tick, 1000);
  }

  function resolveClubCrest(team) {
    if (!team) return 'assets/img/escudos/escudo_penarol.webp';
    if (team.es_penarol || (team.nombre && team.nombre.toLowerCase().includes('peñarol'))) {
      return 'assets/img/escudos/escudo_penarol.webp';
    }
    // Si el objeto ya trae el escudo oficial verificado localmente, usarlo directamente
    if (team.escudo && (team.escudo.startsWith('assets/img/escudos/') || team.escudo.endsWith('.webp') || team.escudo.endsWith('.png'))) {
      return team.escudo;
    }
    const rawName = (team.nombre || team.equipo || '').toLowerCase();
    const norm = rawName
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9 ]/g, '')
      .trim();

    if (state.escudosCatalog && state.escudosCatalog.alias_index) {
      const slug = state.escudosCatalog.alias_index[norm];
      if (slug && state.escudosCatalog.clubes && state.escudosCatalog.clubes[slug]) {
        return state.escudosCatalog.clubes[slug].ruta_webp;
      }
    }
    // Mapeos rápidos directos por palabras clave
    if (norm.includes('juventud')) return 'assets/img/escudos/escudo_juventud.webp';
    if (norm.includes('liverpool')) return 'assets/img/escudos/escudo_liverpool.webp';
    if (norm.includes('nacional')) return 'assets/img/escudos/escudo_nacional.webp';
    if (norm.includes('defensor')) return 'assets/img/escudos/escudo_defensor_sporting.webp';
    if (norm.includes('danubio')) return 'assets/img/escudos/escudo_danubio.webp';
    if (norm.includes('boston')) return 'assets/img/escudos/escudo_boston_river.webp';
    if (norm.includes('wanderers')) return 'assets/img/escudos/escudo_montevideo_wanderers.webp';
    if (norm.includes('cerro largo')) return 'assets/img/escudos/escudo_cerro_largo.webp';
    if (norm.includes('cerro')) return 'assets/img/escudos/escudo_cerro.webp';
    if (norm.includes('racing')) return 'assets/img/escudos/escudo_racing.webp';
    if (norm.includes('progreso')) return 'assets/img/escudos/escudo_progreso.webp';
    if (norm.includes('maldonado')) return 'assets/img/escudos/escudo_deportivo_maldonado.webp';
    if (norm.includes('torque')) return 'assets/img/escudos/escudo_montevideo_city_torque.webp';
    if (norm.includes('albion')) return 'assets/img/escudos/escudo_albion.webp';
    if (norm.includes('central')) return 'assets/img/escudos/escudo_central_espanol.webp';
    if (norm.includes('miramar')) return 'assets/img/escudos/escudo_miramar_misiones.webp';
    if (norm.includes('rampla')) return 'assets/img/escudos/escudo_rampla_juniors.webp';
    if (norm.includes('river')) return 'assets/img/escudos/escudo_river_plate.webp';
    if (norm.includes('plaza')) return 'assets/img/escudos/escudo_plaza_colonia.webp';
    if (norm.includes('rentistas')) return 'assets/img/escudos/escudo_rentistas.webp';
    if (norm.includes('fenix')) return 'assets/img/escudos/escudo_fenix.webp';

    if (team.logo && team.logo.startsWith('http')) return team.logo;
    return 'assets/img/escudos/escudo_penarol.webp';
  }

  function renderMatchHero(live) {
    if (!live) return;
    const prox = live.proximo_partido || {};
    const ult = live.ultimo_partido || {};
    const w = live.clima_campeon_del_siglo || {};

    const wEl = document.getElementById('hero-weather');
    if (wEl && w.temperatura_c !== undefined) {
      wEl.textContent = `🌡️ Campeón del Siglo: ${w.temperatura_c}°C • ${w.condicion || 'Despejado'} (Viento ${w.viento_kmh || 12} km/h)`;
    }

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
    const tLast = document.getElementById('hero-last-result');

    if (prox.local) {
      if (tHome) {
        tHome.textContent = prox.local.nombre;
        tHome.className = 'match-team-name ' + (prox.local.es_penarol ? 'is-penarol' : '');
      }
      if (tHomeCrest) {
        tHomeCrest.src = resolveClubCrest(prox.local);
        tHomeCrest.alt = 'Escudo Oficial de ' + prox.local.nombre;
      }
      if (tHomeWrap) {
        tHomeWrap.className = 'hero-crest-wrap ' + (prox.local.es_penarol ? 'is-penarol' : 'is-rival');
      }
      if (tHomeTag) {
        tHomeTag.textContent = prox.local.es_penarol ? 'El Decano • 1891' : 'Local • Torneo Oficial AUF';
      }
    }

    if (prox.visitante) {
      if (tAway) {
        tAway.textContent = prox.visitante.nombre;
        tAway.className = 'match-team-name ' + (prox.visitante.es_penarol ? 'is-penarol' : '');
      }
      if (tAwayCrest) {
        tAwayCrest.src = resolveClubCrest(prox.visitante);
        tAwayCrest.alt = 'Escudo Oficial de ' + prox.visitante.nombre;
      }
      if (tAwayWrap) {
        tAwayWrap.className = 'hero-crest-wrap ' + (prox.visitante.es_penarol ? 'is-penarol' : 'is-rival');
      }
      if (tAwayTag) {
        tAwayTag.textContent = prox.visitante.es_penarol ? 'El Decano • 1891' : 'Visitante • Torneo Oficial AUF';
      }
    }

    const cdGrid = document.getElementById('hero-countdown-grid');
    const liveScoreBox = document.getElementById('hero-live-score-container');
    const sHome = document.getElementById('hero-live-score-home');
    const sAway = document.getElementById('hero-live-score-away');
    const clkTxt = document.getElementById('hero-live-clock-text');
    const bLiveUrl = live.blogger_live_url || 'https://www.servicioti.com.uy/2026/10/penarol-en-vivo-juventud-vs-penarol.html';

    const heroBadge = document.getElementById('hero-match-badge');

    if (live.fase_partido === 'EN_VIVO') {
      if (cdGrid) cdGrid.style.display = 'none';
      if (liveScoreBox) liveScoreBox.style.display = 'flex';
      if (sHome) sHome.textContent = prox.local ? (prox.local.goles || '0') : '0';
      if (sAway) sAway.textContent = prox.visitante ? (prox.visitante.goles || '0') : '0';
      if (clkTxt) clkTxt.textContent = `EN VIVO • (${prox.minuto_reloj || "1T"})`;

      if (heroBadge) {
        heroBadge.textContent = '🔴 EN VIVO • MINUTO A MINUTO EN DIRECTO';
        heroBadge.style.background = '#ef4444';
        heroBadge.style.color = '#ffffff';
        heroBadge.style.borderColor = '#f87171';
      }

      if (tDate) {
        tDate.textContent = `🔴 EN VIVO (${prox.minuto_reloj || '1T'}) • ${prox.torneo || 'Campeonato Uruguayo'}`;
        tDate.style.color = '#ef4444';
      }

      document.querySelectorAll('.dynamic-blogger-link').forEach(a => {
        a.textContent = '⚡ SEGUIR MINUTO A MINUTO EN DIRECTO →';
        a.style.background = '#ffd100';
        a.style.color = '#09090b';
        a.style.fontWeight = '900';
        a.href = bLiveUrl;
      });
    } else {
      if (cdGrid) cdGrid.style.display = 'grid';
      if (liveScoreBox) liveScoreBox.style.display = 'none';

      if (heroBadge) {
        heroBadge.textContent = `★ PRÓXIMO PARTIDO • ${prox.torneo || 'Torneo Clausura 2026'}`.toUpperCase();
        heroBadge.style.background = '#ffd100';
        heroBadge.style.color = '#09090b';
        heroBadge.style.borderColor = '#eab308';
      }

      if (tDate) {
        const fStr = prox.fecha_legible || 'Sábado 31/10/2026 16:30 hs';
        const tStr = prox.torneo || 'Torneo Clausura 2026';
        tDate.textContent = `★ PRÓXIMO PARTIDO • ${fStr} • ${tStr}`;
        tDate.style.color = 'var(--manya-gold)';
      }

      startCountdown(prox.fecha_iso);
    }

    if (tVenue && prox.estadio) tVenue.textContent = prox.estadio;
    if (tLast && ult.local && ult.visitante) {
      tLast.textContent = `${ult.local.nombre} ${ult.local.goles} - ${ult.visitante.goles} ${ult.visitante.nombre} (${ult.torneo || 'Torneo Clausura'} • ${ult.estadio || 'Estadio Centenario'})`;
    }

    // Ticker interactivo de alerta de partido
    const tickerEl = document.getElementById('manya-live-ticker');
    const tickerTxt = document.getElementById('ticker-text');
    if (tickerEl) {
      if (live.alerta_banner) {
        tickerEl.style.display = 'flex';
        if (tickerTxt) tickerTxt.textContent = live.alerta_banner;
        if (live.fase_partido === 'EN_VIVO') {
          tickerEl.style.borderColor = '#ef4444';
          tickerEl.style.background = '#450a0a';
          tickerEl.style.animation = 'pulse 2s infinite';
        } else if (live.fase_partido === 'PREVIA') {
          tickerEl.style.borderColor = '#ffd100';
          tickerEl.style.background = '#18181b';
          tickerEl.style.animation = 'none';
        } else {
          tickerEl.style.borderColor = 'rgba(255, 209, 0, 0.35)';
          tickerEl.style.background = '#09090b';
          tickerEl.style.animation = 'none';
        }
      } else {
        tickerEl.style.display = 'none';
      }
    }

    // Cuenta regresiva gestionada en bloque hero
    renderLiveTimeline(live);
  }

  function renderLiveTimeline(live) {
    const card = document.getElementById('match-center-live-card');
    const feed = document.getElementById('live-timeline-feed');
    if (!card || !feed) return;

    const eventos = live.minuto_a_minuto || [];
    if (!eventos.length) {
      if (live.fase_partido !== 'EN_VIVO' && live.fase_partido !== 'FINALIZADO') {
        card.style.display = 'none';
        return;
      }
    }

    card.style.display = 'block';
    const bUrl = live.blogger_live_url || 'https://www.servicioti.com.uy/2026/10/penarol-en-vivo-juventud-vs-penarol.html';
    const btnCard = document.getElementById('btn-live-blogger-card');
    if (btnCard) btnCard.href = bUrl;

    feed.innerHTML = eventos.slice().reverse().map(e => `
      <div style="display:flex;gap:12px;padding:12px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);border-left:3px solid var(--manya-gold);border-radius:8px;">
        <div style="flex-shrink:0;width:52px;text-align:center;">
          <span style="background:var(--manya-gold);color:#09090b;font-weight:900;font-size:11.5px;padding:2px 7px;border-radius:999px;">${e.minuto}</span>
        </div>
        <div style="flex-grow:1;">
          <div style="font-weight:800;color:#ffffff;font-size:14.5px;margin-bottom:3px;">${e.icono || '⚡'} ${e.titulo}</div>
          <div style="font-size:13px;color:#d4d4d8;line-height:1.5;">${e.descripcion}</div>
        </div>
      </div>
    `).join('');
  }

  function setupLivePolling() {
    if (window._manyaLivePolling) return;
    window._manyaLivePolling = setInterval(async () => {
      if (state.live && (state.live.fase_partido === 'EN_VIVO' || state.live.fase_partido === 'PREVIA')) {
        try {
          const fresh = await loadJsonSafe(`data/live_status.json?v=${Date.now()}`);
          if (fresh && fresh.actualizado !== state.live.actualizado) {
            state.live = fresh;
            renderMatchHero(fresh);
            renderLiveTimeline(fresh);
            renderStandings();
          }
        } catch (_) {}
      }
    }, 30000);
  }

  function renderStandingsTabs() {
    const container = document.getElementById('standings-tabs-container');
    if (!container) return;

    const tabs = (state.live && state.live.tablas_campeonatos && state.live.tablas_campeonatos.length)
      ? state.live.tablas_campeonatos
      : [
          { id: 'clausura', nombre: 'Torneo Clausura 2026', nombre_corto: 'Torneo Clausura', icono: '⚽', badge: 'Hoy Juega', es_proximo: true },
          { id: 'anual', nombre: 'Tabla Anual Acumulada Oficial (AUF)', nombre_corto: 'Tabla Anual', icono: '🏆', badge: 'Líder 64p', es_proximo: false },
          { id: 'libertadores', nombre: 'Copa CONMEBOL Libertadores', nombre_corto: 'Copa Libertadores', icono: '🌎', badge: 'Conmebol', es_proximo: false }
        ];

    // Por defecto en la carga: asignar el torneo del próximo partido a jugar
    if (!state.standingsTab || !tabs.some(t => t.id === state.standingsTab)) {
      state.standingsTab = (state.live && state.live.torneo_activo_id) ? state.live.torneo_activo_id : 'clausura';
    }

    container.innerHTML = tabs.map(t => {
      const isActive = t.id === state.standingsTab;
      const badgeHtml = t.badge ? `<span class="pill-badge">${t.badge}</span>` : '';
      return `
        <button type="button" class="standings-pill ${isActive ? 'active' : ''}" data-tab="${t.id}" title="Ver ${t.nombre}">
          <span>${t.icono || '🏆'} ${t.nombre_corto || t.nombre}</span>
          ${badgeHtml}
        </button>
      `;
    }).join('');

    container.querySelectorAll('.standings-pill').forEach(btn => {
      btn.addEventListener('click', () => {
        const tabId = btn.getAttribute('data-tab');
        if (tabId && tabId !== state.standingsTab) {
          state.standingsTab = tabId;
          renderStandingsTabs();
          renderStandings();
          // Actualizar texto del simulador si hay puntos proyectados
          const ptsEl = document.getElementById('sim-delta-label');
          if (ptsEl && state.simPointsDelta > 0) {
            const activeTourn = tabs.find(t => t.id === state.standingsTab);
            const tournName = activeTourn ? activeTourn.nombre_corto : 'campeonato';
            ptsEl.textContent = `+${state.simPointsDelta} pts proyectados para Peñarol en ${tournName}`;
          }
        }
      });
    });
  }

  function renderStandings() {
    if (!state.live) return;
    const tbody = document.getElementById('standings-tbody');
    if (!tbody) return;

    const tabs = state.live.tablas_campeonatos || [];
    const activeTourn = tabs.find(t => t.id === state.standingsTab) || {
      id: state.standingsTab,
      nombre: state.standingsTab === 'clausura' ? 'Torneo Clausura 2026' : 'Tabla Anual Acumulada Oficial (AUF)',
      nombre_corto: state.standingsTab === 'clausura' ? 'Torneo Clausura' : 'Tabla Anual',
      icono: state.standingsTab === 'clausura' ? '⚽' : '🏆',
      es_proximo: state.standingsTab === (state.live.torneo_activo_id || 'clausura')
    };

    // Actualizar encabezados y badges
    const titleEl = document.getElementById('standings-table-title');
    const badgeEl = document.getElementById('standings-context-badge');
    const subInfoEl = document.getElementById('standings-sub-info');

    if (titleEl) {
      titleEl.innerHTML = `${activeTourn.icono || '🏆'} ${activeTourn.nombre}`;
    }

    if (badgeEl) {
      if (activeTourn.es_proximo) {
        badgeEl.textContent = 'PRÓXIMO PARTIDO';
        badgeEl.style.display = 'inline-block';
      } else if (activeTourn.id === 'anual') {
        badgeEl.textContent = 'OFICIAL AUF';
        badgeEl.style.display = 'inline-block';
      } else if (activeTourn.id === 'libertadores') {
        badgeEl.textContent = 'CONMEBOL';
        badgeEl.style.display = 'inline-block';
      } else {
        badgeEl.textContent = 'OFICIAL';
        badgeEl.style.display = 'inline-block';
      }
    }

    if (subInfoEl) {
      if (activeTourn.id === 'clausura') {
        subInfoEl.textContent = 'Torneo Clausura Oficial AUF. Tabla del torneo actual correspondiente al cruce de hoy ante Juventud.';
      } else if (activeTourn.id === 'anual') {
        subInfoEl.textContent = 'Tabla Anual Oficial AUF Acumulada (Apertura + Intermedio + Clausura). Peñarol es líder en solitario con 64 puntos.';
      } else if (activeTourn.id === 'libertadores') {
        subInfoEl.textContent = 'Copa CONMEBOL Libertadores. Tabla de posiciones del grupo de Peñarol con datos oficiales de Conmebol.';
      } else {
        subInfoEl.textContent = `Clasificación oficial actualizada de ${activeTourn.nombre}.`;
      }
    }

    // Resolver fuente de datos
    let sourceData = [];
    if (activeTourn && activeTourn.datos && activeTourn.datos.length) {
      sourceData = activeTourn.datos;
    } else if (state.standingsTab === 'clausura') {
      sourceData = state.live.tabla_clausura || state.live.tabla_posiciones || [];
    } else if (state.standingsTab === 'libertadores') {
      sourceData = state.live.tabla_libertadores || [];
    } else {
      sourceData = state.live.tabla_anual || state.live.tabla_posiciones || [];
    }

    // Nombre del próximo rival para destacarlo en la tabla
    const proxMatch = state.live.proximo_partido || {};
    const rivalName = (proxMatch.local && !proxMatch.local.es_penarol)
      ? proxMatch.local.nombre
      : (proxMatch.visitante && !proxMatch.visitante.es_penarol ? proxMatch.visitante.nombre : '');
    const rivalNorm = (rivalName || '').toLowerCase().trim();

    const rows = sourceData.map(r => {
      const isPenarol = r.es_penarol || (r.equipo && r.equipo.toLowerCase().includes('peñarol'));
      const pts = isPenarol ? (r.pts + state.simPointsDelta) : r.pts;
      const pj = isPenarol && state.simPointsDelta > 0 ? (r.pj + Math.ceil(state.simPointsDelta / 3)) : r.pj;
      return Object.assign({}, r, { es_penarol: isPenarol, pts_calc: pts, pj_calc: pj });
    });

    rows.sort((a, b) => b.pts_calc - a.pts_calc);

    tbody.innerHTML = rows.map((r, i) => {
      const isRivalNext = activeTourn.es_proximo && rivalNorm && r.equipo.toLowerCase().includes(rivalNorm);
      const crest = resolveClubCrest({ nombre: r.equipo, es_penarol: r.es_penarol, logo: r.logo, escudo: r.escudo });
      const rowClass = r.es_penarol ? 'row-penarol' : (isRivalNext ? 'row-rival-proximo' : '');

      let tagExtra = '';
      if (r.es_penarol) {
        tagExtra = '<span style="color:var(--manya-gold);font-weight:900;margin-left:4px;">★</span>';
      } else if (isRivalNext) {
        tagExtra = '<span class="badge-gold" style="font-size:9.5px;padding:1px 5px;margin-left:6px;background:rgba(255,255,255,0.12);color:#e4e4e7;border-color:rgba(255,255,255,0.25);">RIVAL DE HOY</span>';
      }

      return `
        <tr class="${rowClass}">
          <td>${i + 1}</td>
          <td>
            <div style="display:flex;align-items:center;gap:8px;">
              <img src="${crest}" alt="${r.equipo}" width="20" height="20" style="object-fit:contain;vertical-align:middle;border-radius:2px;flex-shrink:0;" onerror="this.src='assets/img/escudos/escudo_auf.webp'" />
              <span style="white-space:nowrap;">${r.equipo}${tagExtra}</span>
            </div>
          </td>
          <td>${r.pj_calc}</td>
          <td>${r.pg}</td>
          <td>${r.pe}</td>
          <td>${r.pp}</td>
          <td>${r.dg}</td>
          <td><strong>${r.pts_calc}</strong></td>
        </tr>
      `;
    }).join('');
  }

  function initStandingsTabs() {
    renderStandingsTabs();
  }

  function initSimulator() {
    const container = document.getElementById('sim-matches-box');
    if (!container) return;
    const proxMatch = state.live && state.live.proximo_partido ? state.live.proximo_partido : null;
    const match1Label = proxMatch
      ? `Fecha 11: ${proxMatch.nombre || 'Juventud vs Peñarol'} (${proxMatch.estadio || 'Estadio Centenario'})`
      : 'Fecha 11: Juventud vs Peñarol (Estadio Centenario)';
    const fechas = [
      { id: 1, label: match1Label },
      { id: 2, label: 'Fecha 12: Peñarol vs Cerro Largo (Campeón del Siglo)' },
      { id: 3, label: 'Fecha 13: Danubio vs Peñarol (Jardines del Hipódromo)' }
    ];
    const picks = { 1: 0, 2: 0, 3: 0 };

    function updateSim() {
      state.simPointsDelta = Object.values(picks).reduce((a, b) => a + b, 0);
      const ptsEl = document.getElementById('sim-delta-label');
      if (ptsEl) {
        if (state.simPointsDelta > 0) {
          const tabs = (state.live && state.live.tablas_campeonatos) ? state.live.tablas_campeonatos : [];
          const activeTourn = tabs.find(t => t.id === state.standingsTab);
          const tournName = activeTourn ? activeTourn.nombre_corto : 'la tabla';
          ptsEl.textContent = `+${state.simPointsDelta} pts proyectados para Peñarol en ${tournName}`;
        } else {
          ptsEl.textContent = 'Tabla actual oficial (sin proyección)';
        }
      }
      renderStandings();
    }

    container.innerHTML = fechas.map(f => `
      <div class="sim-row" data-fid="${f.id}">
        <span><strong>${f.label}</strong></span>
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

    const resetBtn = document.getElementById('sim-reset-btn');
    if (resetBtn) {
      resetBtn.addEventListener('click', () => {
        state.simPointsDelta = 0;
        picks[1] = 0;
        picks[2] = 0;
        picks[3] = 0;
        container.querySelectorAll('.sim-btn').forEach(b => b.classList.remove('active'));
        const ptsEl = document.getElementById('sim-delta-label');
        if (ptsEl) ptsEl.textContent = 'Tabla actual oficial (sin proyección)';
        renderStandings();
      });
    }
  }

  function renderTacticalBoard() {
    const pitch = document.getElementById('tactical-pitch');
    const benchBox = document.getElementById('tactical-bench');
    if (!pitch || !state.lineup.length) return;

    const coords = FORMATIONS[state.formation] || FORMATIONS['4-2-3-1'];
    const playersHtml = state.lineup.slice(0, 11).map((p, idx) => {
      const c = coords[idx] || { x: 50, y: 50 };
      const isSel = state.selectedSlotIndex === idx;
      return `
        <div class="pitch-player" data-slot="${idx}" style="left:${c.x}%;top:${c.y}%;">
          <div class="player-token" style="${isSel ? 'border-color:#ffd100;box-shadow:0 0 18px #ffd100;' : ''}">${p.numero}</div>
          <div class="player-label">${p.nombre.split(' ').slice(-1)[0]} (${c.role})</div>
        </div>
      `;
    }).join('');

    pitch.innerHTML = `
      <div class="pitch-mid-line"></div>
      <div class="pitch-center-circle"></div>
      ${playersHtml}
    `;

    pitch.querySelectorAll('.pitch-player').forEach(el => {
      el.addEventListener('click', () => {
        const idx = parseInt(el.getAttribute('data-slot'), 10);
        state.selectedSlotIndex = (state.selectedSlotIndex === idx) ? null : idx;
        renderTacticalBoard();
      });
    });

    if (benchBox) {
      benchBox.innerHTML = state.bench.map((b, bIdx) => `
        <button type="button" class="sim-btn" style="padding:7px 12px;" data-bidx="${bIdx}">
          #${b.numero} ${b.nombre} (${b.posicion})
        </button>
      `).join('');

      benchBox.querySelectorAll('button').forEach(btn => {
        btn.addEventListener('click', () => {
          const bIdx = parseInt(btn.getAttribute('data-bidx'), 10);
          const targetSlot = state.selectedSlotIndex !== null ? state.selectedSlotIndex : 10;
          const temp = state.lineup[targetSlot];
          state.lineup[targetSlot] = state.bench[bIdx];
          state.bench[bIdx] = temp;
          state.selectedSlotIndex = null;
          renderTacticalBoard();
        });
      });
    }
  }

  function exportLineupPNG() {
    const canvas = document.createElement('canvas');
    canvas.width = 1080;
    canvas.height = 1350;
    const ctx = canvas.getContext('2d');

    // Fondo Oro y Carbón
    ctx.fillStyle = '#09090b';
    ctx.fillRect(0, 0, 1080, 1350);
    ctx.fillStyle = '#ffd100';
    ctx.fillRect(0, 0, 1080, 18);

    ctx.fillStyle = '#ffd100';
    ctx.font = '900 44px Inter, sans-serif';
    ctx.textAlign = 'center';
    ctx.fillText('★ MI 11 TITULAR DEL GLORIOSO PEÑAROL ★', 540, 85);

    ctx.fillStyle = '#e4e4e7';
    ctx.font = '700 24px Inter, sans-serif';
    ctx.fillText(`Esquema Táctico: ${state.formation} • manya.servicioti.com.uy`, 540, 130);

    // Cancha reglamentaria completa
    const px0 = 90, py0 = 170, pw = 900, ph = 1020;
    const midY = py0 + ph / 2;
    const midX = px0 + pw / 2;

    // Césped
    ctx.fillStyle = '#14532d';
    ctx.fillRect(px0, py0, pw, ph);

    // Franjas de corte de césped sutiles
    ctx.fillStyle = 'rgba(255, 255, 255, 0.03)';
    const stripH = ph / 8;
    for (let i = 0; i < 8; i += 2) {
      ctx.fillRect(px0, py0 + i * stripH, pw, stripH);
    }

    // Líneas perimetrales y de medio campo
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.85)';
    ctx.lineWidth = 4;
    ctx.strokeRect(px0, py0, pw, ph);

    ctx.beginPath();
    ctx.moveTo(px0, midY);
    ctx.lineTo(px0 + pw, midY);
    ctx.stroke();

    // Círculo central y punto medio
    ctx.beginPath();
    ctx.arc(midX, midY, 110, 0, Math.PI * 2);
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(midX, midY, 7, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();

    // Área Grande Superior (Rival)
    ctx.strokeRect(midX - 250, py0, 500, 160);
    // Área Chica Superior
    ctx.strokeRect(midX - 120, py0, 240, 60);
    // Punto Penal Superior
    ctx.beginPath();
    ctx.arc(midX, py0 + 115, 6, 0, Math.PI * 2);
    ctx.fill();
    // Medialuna Superior
    ctx.beginPath();
    ctx.arc(midX, py0 + 115, 80, 0.23 * Math.PI, 0.77 * Math.PI);
    ctx.stroke();

    // Área Grande Inferior (Arco Decano)
    ctx.strokeRect(midX - 250, py0 + ph - 160, 500, 160);
    // Área Chica Inferior
    ctx.strokeRect(midX - 120, py0 + ph - 60, 240, 60);
    // Punto Penal Inferior
    ctx.beginPath();
    ctx.arc(midX, py0 + ph - 115, 6, 0, Math.PI * 2);
    ctx.fill();
    // Medialuna Inferior
    ctx.beginPath();
    ctx.arc(midX, py0 + ph - 115, 80, 1.23 * Math.PI, 1.77 * Math.PI);
    ctx.stroke();

    // Arcos de córner en las 4 esquinas
    const cornerR = 26;
    ctx.beginPath();
    ctx.arc(px0, py0, cornerR, 0, 0.5 * Math.PI);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(px0 + pw, py0, cornerR, 0.5 * Math.PI, Math.PI);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(px0, py0 + ph, cornerR, 1.5 * Math.PI, 2 * Math.PI);
    ctx.stroke();
    ctx.beginPath();
    ctx.arc(px0 + pw, py0 + ph, cornerR, Math.PI, 1.5 * Math.PI);
    ctx.stroke();

    // Dibujar futbolistas con dorsales y etiquetas legibles
    const coords = FORMATIONS[state.formation] || FORMATIONS['4-2-3-1'];
    state.lineup.slice(0, 11).forEach((p, idx) => {
      const c = coords[idx] || { x: 50, y: 50 };
      const px = px0 + (c.x / 100) * pw;
      const py = py0 + (c.y / 100) * ph;

      // Sombra
      ctx.beginPath();
      ctx.arc(px, py + 4, 34, 0, Math.PI * 2);
      ctx.fillStyle = 'rgba(0,0,0,0.5)';
      ctx.fill();

      // Ficha Oro y Carbón
      ctx.beginPath();
      ctx.arc(px, py, 34, 0, Math.PI * 2);
      ctx.fillStyle = '#ffd100';
      ctx.fill();
      ctx.lineWidth = 4;
      ctx.strokeStyle = '#09090b';
      ctx.stroke();

      // Dorsal
      ctx.fillStyle = '#09090b';
      ctx.font = '900 26px Inter, sans-serif';
      ctx.fillText(String(p.numero), px, py + 9);

      // Nombre y Rol
      const lastName = p.nombre.split(' ').slice(-1)[0];
      const nameTxt = `${lastName} (${c.role})`;
      ctx.font = '800 20px Inter, sans-serif';
      const textMetrics = ctx.measureText(nameTxt);
      const textW = textMetrics.width + 16;
      ctx.fillStyle = 'rgba(9, 9, 11, 0.9)';
      ctx.fillRect(px - textW / 2, py + 42, textW, 26);
      ctx.strokeStyle = 'rgba(255, 209, 0, 0.6)';
      ctx.lineWidth = 1.5;
      ctx.strokeRect(px - textW / 2, py + 42, textW, 26);

      ctx.fillStyle = '#ffffff';
      ctx.fillText(nameTxt, px, py + 61);
    });

    ctx.fillStyle = '#ffd100';
    ctx.font = '800 24px Inter, sans-serif';
    ctx.fillText('Creado en https://manya.servicioti.com.uy • ServicioTI Uruguay', 540, 1280);

    const link = document.createElement('a');
    link.download = `mi-11-penarol-${state.formation}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  }

  let triviaAudioEnabled = true;

  function playAudioTone(type) {
    if (!triviaAudioEnabled) return;
    try {
      const AudioCtx = window.AudioContext || window.webkitAudioContext;
      if (!AudioCtx) return;
      const ctx = new AudioCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.connect(gain);
      gain.connect(ctx.destination);

      if (type === 'correct') {
        osc.type = 'sine';
        osc.frequency.setValueAtTime(587.33, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(880, ctx.currentTime + 0.12);
        gain.gain.setValueAtTime(0.09, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + 0.25);
      } else if (type === 'wrong') {
        osc.type = 'triangle';
        osc.frequency.setValueAtTime(260, ctx.currentTime);
        osc.frequency.exponentialRampToValueAtTime(170, ctx.currentTime + 0.22);
        gain.gain.setValueAtTime(0.09, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.25);
        osc.start(ctx.currentTime);
        osc.stop(ctx.currentTime + 0.25);
      } else if (type === 'fanfare') {
        [523.25, 659.25, 783.99, 1046.50].forEach((freq, i) => {
          const o = ctx.createOscillator();
          const g = ctx.createGain();
          o.connect(g);
          g.connect(ctx.destination);
          o.frequency.value = freq;
          g.gain.setValueAtTime(0.08, ctx.currentTime + i * 0.1);
          g.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + i * 0.1 + 0.25);
          o.start(ctx.currentTime + i * 0.1);
          o.stop(ctx.currentTime + i * 0.1 + 0.25);
        });
      }
    } catch (_) {}
  }

  function getTriviaHighScore() {
    try {
      return parseInt(localStorage.getItem('manya_trivia_highscore') || '0', 10);
    } catch (_) {
      return 0;
    }
  }

  function saveTriviaHighScore(score) {
    try {
      const cur = getTriviaHighScore();
      if (score > cur) {
        localStorage.setItem('manya_trivia_highscore', String(score));
        return true;
      }
    } catch (_) {}
    return false;
  }

  function prepareTriviaQuestion(q) {
    // Generar opciones barajadas dinámicamente para que la respuesta correcta no esté siempre en 'A'
    const paired = q.opts.map((opt, idx) => ({
      text: opt,
      isCorrect: idx === q.ans
    }));
    // Fisher-Yates shuffle
    for (let i = paired.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [paired[i], paired[j]] = [paired[j], paired[i]];
    }
    return Object.assign({}, q, {
      opts: paired.map(p => p.text),
      ans: paired.findIndex(p => p.isCorrect)
    });
  }

  let triviaState = {
    category: 'all',
    currentIndex: 0,
    score: 0,
    streak: 0,
    maxStreak: 0,
    answered: false,
    questionsPool: []
  };

  function getTriviaQuestionsPool(cat) {
    const rawList = (!cat || cat === 'all')
      ? TRIVIA_QUESTIONS
      : TRIVIA_QUESTIONS.filter(q => q.cat === cat);
    const list = rawList.length ? rawList : TRIVIA_QUESTIONS;
    // Barajar aleatoriamente el orden de las preguntas y sus opciones
    const shuffled = [...list].sort(() => Math.random() - 0.5);
    return shuffled.map(prepareTriviaQuestion);
  }

  function renderTrivia() {
    const box = document.getElementById('trivia-box');
    if (!box) return;

    if (!triviaState.questionsPool.length) {
      triviaState.questionsPool = getTriviaQuestionsPool(triviaState.category);
    }

    const pool = triviaState.questionsPool;
    const total = pool.length;
    const idx = triviaState.currentIndex;
    const personalRecord = getTriviaHighScore();

    // Si terminó la tanda de preguntas
    if (idx >= total) {
      const pct = Math.round((triviaState.score / (total * 100)) * 100);
      const isNewRecord = saveTriviaHighScore(triviaState.score);
      if (pct >= 70 || isNewRecord) {
        playAudioTone('fanfare');
      }

      let rankBadge = '';
      let rankTitle = '';
      let rankMsg = '';

      if (pct >= 90) {
        rankBadge = '🏆 Rango: Capitán de Capitanes';
        rankTitle = '¡Nivel Tito Gonçalves!';
        rankMsg = 'Tenés la mística y los datos del club grabados a fuego en el corazón. ¡Orgullo aurinegro total!';
      } else if (pct >= 70) {
        rankBadge = '⭐ Rango: Gloria de Primera';
        rankTitle = '¡Sabiduría de la Tribuna Damiani!';
        rankMsg = 'Gran conocimiento de las copas, clásicos y hazañas. Estás listo para cualquier debate futbolero.';
      } else if (pct >= 50) {
        rankBadge = '🟡 Rango: Carbonero de Ley';
        rankTitle = '¡Pasión de la Tribuna Ámsterdam!';
        rankMsg = 'Buen puntaje. Conocés las hazañas esenciales, aunque todavía quedan joyitas por repasar en 1891.uy.';
      } else {
        rankBadge = '📖 Rango: Hincha en Formación';
        rankTitle = '¡A estudiar las fichas decanas!';
        rankMsg = 'Peñarol tiene 135 años de gloria. Date una vuelta por el archivo de 1891.uy para revivir la historia.';
      }

      box.innerHTML = `
        <div class="trivia-container trivia-game-over">
          <div style="font-size:38px;margin-bottom:8px;">🏆</div>
          <h4 style="font-size:20px;color:#fff;margin-bottom:4px;">${rankTitle}</h4>
          ${isNewRecord ? '<div style="background:#22c55e;color:#000;font-weight:900;padding:4px 12px;border-radius:999px;font-size:12px;display:inline-block;margin-bottom:8px;">🎉 ¡NUEVO RÉCORD PERSONAL!</div>' : ''}
          <div class="trivia-rank-badge">${rankBadge}</div>
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:16px 0;background:rgba(0,0,0,0.5);padding:14px;border-radius:8px;border:1px solid rgba(255,209,0,0.2);">
            <div>
              <div style="font-size:20px;font-weight:900;color:var(--manya-gold);font-family:'JetBrains Mono',monospace;">${triviaState.score}</div>
              <div style="font-size:11px;color:var(--text-secondary);text-transform:uppercase;">Puntos Totales</div>
            </div>
            <div>
              <div style="font-size:20px;font-weight:900;color:#fff;font-family:'JetBrains Mono',monospace;">${pct}%</div>
              <div style="font-size:11px;color:var(--text-secondary);text-transform:uppercase;">Efectividad</div>
            </div>
            <div>
              <div style="font-size:20px;font-weight:900;color:#f97316;font-family:'JetBrains Mono',monospace;">🔥 x${triviaState.maxStreak}</div>
              <div style="font-size:11px;color:var(--text-secondary);text-transform:uppercase;">Mejor Racha</div>
            </div>
          </div>
          <p style="font-size:13px;color:#d4d4d8;line-height:1.5;margin-bottom:16px;">${rankMsg}</p>
          <div style="display:flex;gap:10px;justify-content:center;flex-wrap:wrap;">
            <button type="button" class="btn-manya" id="trivia-restart-btn">🔄 Jugar de Nuevo</button>
            <a href="https://1891.uy/" target="_blank" rel="noopener noreferrer" class="btn-outline-gold" style="font-size:13px;padding:8px 14px;">Explorar Archivo 1891.uy ↗</a>
          </div>
        </div>
      `;

      const rBtn = box.querySelector('#trivia-restart-btn');
      if (rBtn) {
        rBtn.addEventListener('click', () => {
          triviaState.currentIndex = 0;
          triviaState.score = 0;
          triviaState.streak = 0;
          triviaState.maxStreak = 0;
          triviaState.answered = false;
          triviaState.questionsPool = getTriviaQuestionsPool(triviaState.category);
      
  function initLiveVoting() {
    const buttons = document.querySelectorAll('.vote-player-btn');
    const countEl = document.getElementById('vote-total-count');
    if (!buttons.length) return;

    let voted = localStorage.getItem('manya_mvp_voted');
    let counts = JSON.parse(localStorage.getItem('manya_mvp_counts') || '{"leo": 685, "cabrera": 342, "damian": 214, "guzman": 187}');

    function updateUI() {
      const total = Object.values(counts).reduce((a, b) => a + b, 0);
      if (countEl) countEl.textContent = `${total.toLocaleString('es-UY')} Votos Emitidos`;
      buttons.forEach(btn => {
        const p = btn.getAttribute('data-player');
        const pct = Math.round((counts[p] / total) * 100) || 0;
        const pctEl = btn.querySelector('.vote-pct');
        const barEl = btn.querySelector('.vote-bar');
        if (pctEl) pctEl.textContent = `${pct}%`;
        if (barEl) barEl.style.width = `${pct}%`;
        if (voted === p) {
          btn.classList.add('has-voted');
          const voteTxt = btn.querySelector('span:nth-child(1)');
          if (voteTxt && voteTxt.textContent === 'Votar') voteTxt.textContent = '✓ Tu Voto';
        } else {
          btn.classList.remove('has-voted');
          const voteTxt = btn.querySelector('span:nth-child(1)');
          if (voteTxt && voteTxt.textContent === '✓ Tu Voto') voteTxt.textContent = 'Votar';
        }
      });
    }

    buttons.forEach(btn => {
      btn.addEventListener('click', () => {
        const p = btn.getAttribute('data-player');
        if (voted === p) return;
        if (voted && counts[voted] > 0) counts[voted]--;
        counts[p] = (counts[p] || 0) + 1;
        voted = p;
        localStorage.setItem('manya_mvp_voted', voted);
        localStorage.setItem('manya_mvp_counts', JSON.stringify(counts));
        updateUI();
      });
    });

    updateUI();
  }

    initLiveVoting();
    renderTrivia();
        });
      }
      return;
    }

    const item = pool[idx];
    triviaState.answered = false;
    const progressPct = Math.round(((idx) / total) * 100);

    const categoriesList = [
      { id: 'all', label: 'Todas' },
      { id: 'libertadores', label: '🏆 Libertadores' },
      { id: 'clasicos', label: '⚡ Clásicos' },
      { id: 'idolos', label: '⭐ Ídolos' },
      { id: 'records', label: '📊 Récords' },
      { id: 'cds', label: '🏟️ CDS' }
    ];

    box.innerHTML = `
      <div class="trivia-container">
        <!-- Selector de Categorías y Sonido -->
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
          <div class="trivia-cat-chips" role="tablist">
            ${categoriesList.map(cat => `
              <button type="button" class="trivia-chip ${triviaState.category === cat.id ? 'active' : ''}" data-cat="${cat.id}">
                ${cat.label}
              </button>
            `).join('')}
          </div>
          <button type="button" id="trivia-sound-toggle" title="Activar/Desactivar Sonido" style="background:transparent;border:1px solid rgba(255,255,255,0.15);color:#d4d4d8;padding:4px 8px;border-radius:6px;cursor:pointer;font-size:12px;">
            ${triviaAudioEnabled ? '🔊 Sonido' : '🔇 Mudo'}
          </button>
        </div>

        <!-- Barra de Progreso y Estadísticas -->
        <div class="trivia-stats-row">
          <span>Pregunta <strong>${idx + 1}</strong> de ${total} • <em style="color:var(--manya-gold);font-style:normal;">${item.catName || 'Historia'}</em></span>
          <div style="display:flex;align-items:center;gap:12px;">
            ${personalRecord > 0 ? `<span style="font-size:11px;color:#a1a1aa;">🏅 Récord: <strong style="color:#ffd100;">${personalRecord}</strong></span>` : ''}
            ${triviaState.streak > 1 ? `<span class="trivia-streak-badge">🔥 x${triviaState.streak}</span>` : ''}
            <span style="color:var(--manya-gold);font-weight:800;font-family:'JetBrains Mono',monospace;">${triviaState.score} pts</span>
          </div>
        </div>
        <div class="trivia-progress-bar-wrap">
          <div class="trivia-progress-fill" style="width:${progressPct}%;"></div>
        </div>

        <!-- Pregunta -->
        <h4 class="trivia-q-title">${item.q}</h4>

        <!-- Opciones (Distribuidas aleatoriamente) -->
        <div class="trivia-opts-grid" id="trivia-opts">
          ${item.opts.map((o, i) => {
            const letter = ['A', 'B', 'C', 'D'][i] || (i + 1);
            return `
              <button type="button" class="trivia-opt-btn" data-idx="${i}">
                <span class="trivia-opt-letter">${letter}</span>
                <span>${o}</span>
              </button>
            `;
          }).join('')}
        </div>

        <!-- Feedback y Explicación -->
        <div id="trivia-feedback" style="display:none;"></div>
      </div>
    `;

    // Toggle de sonido
    const sndBtn = box.querySelector('#trivia-sound-toggle');
    if (sndBtn) {
      sndBtn.addEventListener('click', () => {
        triviaAudioEnabled = !triviaAudioEnabled;
        sndBtn.textContent = triviaAudioEnabled ? '🔊 Sonido' : '🔇 Mudo';
      });
    }

    // Eventos a las fichas de categoría
    box.querySelectorAll('.trivia-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        const selectedCat = btn.getAttribute('data-cat');
        triviaState.category = selectedCat;
        triviaState.currentIndex = 0;
        triviaState.score = 0;
        triviaState.streak = 0;
        triviaState.maxStreak = 0;
        triviaState.answered = false;
        triviaState.questionsPool = getTriviaQuestionsPool(selectedCat);
        renderTrivia();
      });
    });

    // Eventos a las opciones de respuesta
    const fb = box.querySelector('#trivia-feedback');
    const optBtns = box.querySelectorAll('#trivia-opts .trivia-opt-btn');

    optBtns.forEach(btn => {
      btn.addEventListener('click', () => {
        if (triviaState.answered) return;
        triviaState.answered = true;

        const chosen = parseInt(btn.getAttribute('data-idx'), 10);
        optBtns.forEach(b => b.disabled = true);

        if (chosen === item.ans) {
          playAudioTone('correct');
          triviaState.streak++;
          if (triviaState.streak > triviaState.maxStreak) {
            triviaState.maxStreak = triviaState.streak;
          }
          const bonus = (triviaState.streak - 1) * 25;
          const gained = 100 + bonus;
          triviaState.score += gained;

          btn.classList.add('is-correct');
          fb.className = 'trivia-feedback-card correct';
          fb.innerHTML = `
            <div style="font-weight:800;font-size:14px;color:#22c55e;display:flex;align-items:center;justify-content:space-between;">
              <span>✅ ¡Correcto, Carbonero! (+${gained} pts)</span>
              ${triviaState.streak > 1 ? `<span style="font-size:11.5px;color:#f97316;">🔥 Racha x${triviaState.streak}</span>` : ''}
            </div>
            <div class="trivia-feedback-exp">${item.exp}</div>
            <button type="button" class="btn-manya" style="margin-top:10px;padding:7px 14px;font-size:13px;" id="trivia-next-btn">Siguiente Pregunta →</button>
          `;
        } else {
          playAudioTone('wrong');
          triviaState.streak = 0;
          btn.classList.add('is-wrong');
          const correctBtn = box.querySelector(`#trivia-opts .trivia-opt-btn[data-idx="${item.ans}"]`);
          if (correctBtn) correctBtn.classList.add('is-correct');

          fb.className = 'trivia-feedback-card wrong';
          fb.innerHTML = `
            <div style="font-weight:800;font-size:14px;color:#ef4444;">❌ Respuesta Histórica Certificada</div>
            <div class="trivia-feedback-exp">${item.exp}</div>
            <button type="button" class="btn-manya" style="margin-top:10px;padding:7px 14px;font-size:13px;" id="trivia-next-btn">Siguiente Pregunta →</button>
          `;
        }
        fb.style.display = 'block';

        const nxtBtn = box.querySelector('#trivia-next-btn');
        if (nxtBtn) {
          nxtBtn.addEventListener('click', () => {
            triviaState.currentIndex++;
            renderTrivia();
          });
        }
      });
    });
  }
  function setupLightbox() {
    const modal = document.getElementById('manya-lightbox');
    const overlay = document.getElementById('lightbox-overlay');
    const closeBtn = document.getElementById('lightbox-close');
    if (!modal) return;

    function closeModal() {
      modal.style.display = 'none';
      modal.setAttribute('aria-hidden', 'true');
      document.body.style.overflow = '';
    }

    if (overlay) overlay.addEventListener('click', closeModal);
    if (closeBtn) closeBtn.addEventListener('click', closeModal);
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && modal.style.display !== 'none') {
        closeModal();
      }
    });
  }

  function openLightbox(item) {
    const modal = document.getElementById('manya-lightbox');
    const is1891 = (item.cuenta === '1891.uy') || (item.url_post && item.url_post.includes('1891.uy')) || (item.fuente && item.fuente.includes('1891'));
    if (!modal) return;

    const imgEl = document.getElementById('lightbox-img');
    const badgeEl = document.getElementById('lightbox-badge');
    const metaEl = document.getElementById('lightbox-meta');
    const titleEl = document.getElementById('lightbox-title');
    const descEl = document.getElementById('lightbox-desc');
    const linkEl = document.getElementById('lightbox-external-link');

    if (imgEl) {
      imgEl.src = item.imagen_webp || item.imagen_jpg;
      imgEl.alt = item.titulo;
    }
    if (badgeEl) {
      badgeEl.textContent = is1891 ? '📜 FICHA OFICIAL 1891 BD' : `📸 ${item.categoria ? item.categoria.toUpperCase() : 'PEÑAROL'}`;
    }
    if (metaEl) {
      if (is1891) {
        metaEl.textContent = `1891 BD (Comisión de Historia) • ${item.estadio || 'Estadio Centenario'} • ${item.fecha || '2026'}`;
      } else {
        metaEl.textContent = `${item.cuenta} • ❤️ ${item.likes ? item.likes.toLocaleString() : '25.000'} • 💬 ${item.comments || 350}`;
      }
    }
    if (titleEl) titleEl.textContent = item.titulo;
    if (descEl) descEl.textContent = item.descripcion || item.caption || '';
    if (linkEl) {
      const isTenfield = (item.cuenta === '@tenfield') || (item.url_post && item.url_post.includes('tenfield'));
      const isPD = (item.cuenta === '@padreydecano') || (item.url_post && item.url_post.includes('padreydecano'));
      const pUrl = item.url_post || (isPD ? 'https://www.padreydecano.com/cms/' : (isTenfield ? 'https://www.tenfield.com.uy' : 'https://www.instagram.com/oficialcap/'));
      const pUrl1891 = is1891 ? 'https://1891.uy/partidos' : pUrl;
      linkEl.href = pUrl1891;
      linkEl.textContent = is1891 ? 'Ver ficha del partido en 1891.uy ↗' : (isPD ? 'Ver artículo en Padre y Decano ↗' : (isTenfield ? 'Ver cobertura oficial en Tenfield Deportes ↗' : 'Ver publicación original en Instagram ↗'));
    }

    modal.style.display = 'flex';
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  function renderHeroInstagramPost(item, digest) {
    const card = document.getElementById('portada-visual');
    if (!card) return;

    const pv = (digest && digest.portada_visual) ? digest.portada_visual : {};
    const effectiveItem = Object.assign({}, item || {}, pv);

    const avatarEl = document.getElementById('hero-post-avatar');
    const accountEl = document.getElementById('hero-post-account');
    const timeEl = document.getElementById('hero-post-time');
    const locEl = document.getElementById('hero-post-location');
    const extLink = document.getElementById('hero-post-external-link');
    const mediaWrap = document.getElementById('hero-post-media');
    const imgEl = document.getElementById('hero-post-img');
    const badgeEl = document.getElementById('hero-post-badge');
    const expandBtn = document.getElementById('hero-post-expand-btn');
    const zoomBtn = document.getElementById('hero-post-zoom-btn');
    const likeBtn = document.getElementById('hero-post-like-btn');
    const likeIcon = document.getElementById('hero-post-like-icon');
    const likesCountEl = document.getElementById('hero-post-likes-count');
    const commentBtn = document.getElementById('hero-post-comment-btn');
    const commentsCountEl = document.getElementById('hero-post-comments-count');
    const shareBtn = document.getElementById('hero-post-share-btn');
    const catTag = document.getElementById('hero-post-category-tag');
    const headlineEl = document.getElementById('hero-post-headline');
    const textEl = document.getElementById('hero-post-text');
    const readMoreEl = document.getElementById('hero-post-read-more');

    const cuenta = effectiveItem.cuenta || '@oficialcap';
    const isOficialCap = cuenta === '@oficialcap';
    const postUrl = effectiveItem.url_post || (isOficialCap ? 'https://www.instagram.com/oficialcap/' : 'https://www.padreydecano.com/cms/');
    const imgSource = effectiveItem.imagen_webp || effectiveItem.imagen_jpg || 'assets/ig/manya_campeon_del_siglo_nocturno.webp';
    const headline = pv.titular_portada || (digest && digest.titular_dia) || effectiveItem.titulo || 'Peñarol y la obsesión por la Tabla Anual: El laboratorio de Aguirre';
    const bajada = pv.bajada_portada || (digest && digest.bajada_seo) || effectiveItem.caption || effectiveItem.descripcion || '';

    if (avatarEl) {
      avatarEl.src = isOficialCap ? 'assets/img/escudo_penarol_oficial.svg' : 'assets/img/escudos/escudo_penarol.webp';
      avatarEl.alt = isOficialCap ? 'Club Atlético Peñarol Oficial' : 'Padre y Decano';
    }
    if (accountEl) accountEl.textContent = cuenta;
    if (timeEl) timeEl.textContent = 'Actualizado Hoy';
    if (locEl) {
      locEl.textContent = effectiveItem.ubicacion || (effectiveItem.categoria === 'los-aromos' ? '📍 Complejo Deportivo Washington Cataldi (Los Aromos)' : '📍 Estadio Campeón del Siglo • Montevideo');
    }
    if (extLink) {
      extLink.href = postUrl;
      extLink.innerHTML = `<span>${isOficialCap ? 'Ver en Instagram' : 'Ver en Padre y Decano'}</span> ↗`;
    }
    if (imgEl) {
      imgEl.src = imgSource;
      imgEl.alt = headline + ' - Club Atlético Peñarol';
    }
    if (badgeEl) {
      badgeEl.textContent = `📸 ${effectiveItem.categoria ? effectiveItem.categoria.replace('-', ' ').toUpperCase() : 'PORTADA OFICIAL'}`;
    }
    if (catTag) {
      catTag.textContent = `⭐ ${isOficialCap ? 'EDICIÓN OFICIAL CAP' : 'PADRE Y DECANO'}`;
    }
    if (headlineEl) headlineEl.textContent = headline;
    if (textEl) textEl.innerHTML = bajada;

    let currentLikes = parseInt(effectiveItem.likes || 38450, 10);
    const storageKey = 'manya_hero_liked_' + (effectiveItem.id || 'main');
    let isLiked = false;
    try {
      isLiked = localStorage.getItem(storageKey) === 'true';
    } catch (_) {}

    function updateLikeUI() {
      if (likesCountEl) likesCountEl.textContent = currentLikes.toLocaleString('es-UY');
      if (likeIcon) {
        likeIcon.textContent = isLiked ? '❤️' : '🤍';
        likeIcon.style.transform = isLiked ? 'scale(1.2)' : 'scale(1)';
        likeIcon.style.transition = 'transform 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
      }
      if (likeBtn) {
        likeBtn.style.color = isLiked ? '#ef4444' : '';
      }
    }
    if (isLiked) currentLikes += 1;
    updateLikeUI();

    if (likeBtn) {
      likeBtn.onclick = () => {
        isLiked = !isLiked;
        currentLikes += isLiked ? 1 : -1;
        try {
          localStorage.setItem(storageKey, isLiked ? 'true' : 'false');
        } catch (_) {}
        updateLikeUI();
      };
    }

    if (commentsCountEl) {
      commentsCountEl.textContent = (effectiveItem.comments || 892).toLocaleString('es-UY');
    }

    if (commentBtn) {
      commentBtn.onclick = () => {
        const target = document.getElementById('analisis-editorial');
        if (target) target.scrollIntoView({ behavior: 'smooth' });
      };
    }

    if (shareBtn) {
      shareBtn.onclick = async () => {
        const shareData = {
          title: headline,
          text: bajada,
          url: window.location.href
        };
        if (navigator.share) {
          try {
            await navigator.share(shareData);
          } catch (_) {}
        } else if (navigator.clipboard) {
          await navigator.clipboard.writeText(window.location.href);
          const orig = shareBtn.innerHTML;
          shareBtn.innerHTML = '<span>✅</span><span>¡Copiado!</span>';
          setTimeout(() => { shareBtn.innerHTML = orig; }, 2200);
        }
      };
    }

    const openHeroLightbox = () => {
      openLightbox({
        titulo: headline,
        descripcion: bajada,
        cuenta: cuenta,
        categoria: effectiveItem.categoria || 'portada',
        likes: currentLikes,
        comments: effectiveItem.comments || 892,
        url_post: postUrl,
        imagen_webp: imgSource,
        imagen_jpg: imgSource
      });
    };

    if (mediaWrap) mediaWrap.onclick = openHeroLightbox;
    if (expandBtn) expandBtn.onclick = (e) => { e.stopPropagation(); openHeroLightbox(); };
    if (zoomBtn) zoomBtn.onclick = openHeroLightbox;

    if (readMoreEl) {
      readMoreEl.href = (digest && digest.blogger_post_url) ? digest.blogger_post_url : 'https://www.servicioti.com.uy/p/penarol-proximo-partido-radiografia.html';
      readMoreEl.target = '_blank';
      readMoreEl.rel = 'noopener noreferrer';
    }
  }

  function renderGallery(items, currentFilter) {
    const grid = document.getElementById('gallery-main-grid') || document.querySelector('#muro-visual .ig-grid');
    if (!grid) return;

    const filter = currentFilter || 'all';
    const filtered = (filter === 'all')
      ? items
      : items.filter(it => (it.categoria || '').toLowerCase().includes(filter.toLowerCase()));

    if (!filtered.length) {
      grid.innerHTML = `<div style="grid-column:1/-1;text-align:center;padding:40px;color:var(--text-secondary);">No se encontraron fotos en esta categoría.</div>`;
      return;
    }

    grid.innerHTML = filtered.map((item, idx) => {
      const isTenfield = (item.cuenta === '@tenfield') || (item.url_post && item.url_post.includes('tenfield'));
      const isPD = (item.cuenta === '@padreydecano') || (item.url_post && item.url_post.includes('padreydecano'));
      const postUrl = item.url_post || (isPD ? 'https://www.padreydecano.com/cms/' : (isTenfield ? 'https://www.tenfield.com.uy' : 'https://www.instagram.com/oficialcap/'));
      const sourceLabel = isPD ? 'Padre y Decano ↗' : (isTenfield ? 'Tenfield ↗' : 'Instagram ↗');
      const isItem1891 = (item.cuenta === '1891.uy') || (item.url_post && item.url_post.includes('1891.uy')) || (item.fuente && item.fuente.includes('1891'));
      const badgeTxt = isItem1891 ? '📜 FICHA 1891 BD' : `📸 ${(item.categoria || 'Peñarol').replace('-', ' ').toUpperCase()}`;
      const likesTxt = item.likes ? (item.likes >= 1000 ? (item.likes / 1000).toFixed(1) + 'K' : item.likes) : '25K';
      const commentsTxt = item.comments || 450;
      const descTxt = item.descripcion || item.caption || '';

      return `
        <article class="ig-card" data-idx="${idx}">
          <div class="ig-card-link" style="cursor:pointer;" title="Click para ampliar en alta definición (16:9)">
            <div class="ig-img-wrap">
              <img src="${item.imagen_webp || item.imagen_jpg}" alt="${item.titulo} - Club Atlético Peñarol" width="1280" height="720" loading="lazy" decoding="async" />
              <span class="ig-badge-tag">${badgeTxt}</span>
            </div>
          </div>
          <div class="ig-body">
            <div class="ig-meta">
              <span>${item.cuenta} • ${(item.categoria || '').toUpperCase()}</span>
              <span>❤️ ${likesTxt} • 💬 ${commentsTxt}</span>
            </div>
            <h3 class="ig-title">
              <a href="${postUrl}" target="_blank" rel="noopener noreferrer">${item.titulo}</a>
            </h3>
            <p class="ig-caption">${descTxt}</p>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:10px;gap:8px;">
              <button type="button" class="btn-outline-gold open-lightbox-btn" style="padding:4px 10px;font-size:11.5px;cursor:pointer;">🔍 Ampliar Foto</button>
              <a href="${postUrl}" target="_blank" rel="noopener noreferrer" class="ig-external-btn" style="margin-top:0;">${sourceLabel}</a>
            </div>
          </div>
        </article>
      `;
    }).join('');

    grid.querySelectorAll('.ig-card').forEach((card) => {
      const idx = parseInt(card.getAttribute('data-idx'), 10);
      const targetItem = filtered[idx];
      const linkArea = card.querySelector('.ig-card-link');
      const zoomBtn = card.querySelector('.open-lightbox-btn');

      if (linkArea) {
        linkArea.addEventListener('click', () => openLightbox(targetItem));
      }
      if (zoomBtn) {
        zoomBtn.addEventListener('click', (e) => {
          e.stopPropagation();
          openLightbox(targetItem);
        });
      }
    });
  }

  function setupGalleryFilters(allItems) {
    const tabs = document.querySelectorAll('#gallery-filters .gallery-tab');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const filter = tab.getAttribute('data-filter') || 'all';
        renderGallery(allItems, filter);
      });
    });
  }

  function hydrateEditorialSection(digest) {
    if (!digest) return;
    const headlineEl = document.getElementById('editorial-headline');
    const p1El = document.getElementById('editorial-p1');
    const p2El = document.getElementById('editorial-p2');
    const p3El = document.getElementById('editorial-p3');
    const clavesBox = document.getElementById('claves-editorial-container');
    const newsBox = document.getElementById('live-news-list');

    const art = digest.articulo_principal || {};
    if (headlineEl && (art.titulo || digest.titular_dia)) {
      headlineEl.textContent = art.titulo || digest.titular_dia;
    }
    if (art.parrafos && art.parrafos.length >= 3) {
      if (p1El) p1El.innerHTML = art.parrafos[0];
      if (p2El) p2El.innerHTML = art.parrafos[1];
      if (p3El) p3El.innerHTML = art.parrafos[2];
    }

    const pullquoteEl = document.querySelector('.editorial-pullquote');
    if (pullquoteEl && art.cita_destacada) {
      pullquoteEl.innerHTML = `“${art.cita_destacada}” ${art.autor_cita ? `<span style="display:block;font-size:12px;margin-top:6px;color:var(--manya-gold);">— ${art.autor_cita}</span>` : ''}`;
    }

    if (clavesBox && digest.claves_60_segundos && digest.claves_60_segundos.length) {
      clavesBox.innerHTML = digest.claves_60_segundos.map(c => `
        <div class="clave-item">
          <div class="clave-item-title">${c.icono || '⚽'} ${c.titulo}</div>
          <p class="clave-item-desc">${c.detalle}</p>
        </div>
      `).join('');
    }

    if (newsBox && digest.noticias_fuentes && digest.noticias_fuentes.length) {
      newsBox.innerHTML = digest.noticias_fuentes.slice(0, 7).map(n => `
        <div class="clave-item" style="border-left-color:#71717a;">
          <div style="font-size:11px;color:var(--manya-gold);font-weight:800;margin-bottom:3px;">
            ${n.fuente} • ${n.fecha_raw ? n.fecha_raw.slice(0, 16) : 'Actualidad'}
          </div>
          <div style="font-size:13px;font-weight:700;color:#fff;margin-bottom:4px;">
            <a href="${n.url || digest.blogger_post_url || 'https://www.servicioti.com.uy'}" target="_blank" rel="noopener noreferrer" style="color:#ffffff;text-decoration:none;">
              ${n.titulo}
            </a>
          </div>
          <p style="font-size:12px;color:#a1a1aa;line-height:1.4;margin-bottom:6px;">
            ${(n.resumen || '').slice(0, 130)}...
          </p>
          <a href="${n.url || digest.blogger_post_url || 'https://www.servicioti.com.uy'}" target="_blank" rel="noopener noreferrer" style="font-size:11px;color:var(--manya-gold);font-weight:800;text-decoration:none;">
            Leer cobertura completa ↗
          </a>
        </div>
      `).join('');
    }

    const prensaGrid = document.getElementById('prensa-nacional-grid');
    if (prensaGrid) {
      if (digest.prismas_analisis) {
        const prismasMeta = {
          epica_tribuna: { icon: '🏟️', color: '#ffd100' },
          pizarron_tactico: { icon: '♟️', color: '#38bdf8' },
          trastienda_vestuario: { icon: '🔥', color: '#f87171' },
          aritmetica_campeonato: { icon: '📐', color: '#34d399' }
        };
        prensaGrid.innerHTML = Object.entries(digest.prismas_analisis).map(([k, item]) => {
          const meta = prismasMeta[k] || { icon: '⚡', color: '#ffd100' };
          return `
            <div class="clave-item" style="border-left:3px solid ${meta.color};background:#141419;padding:12px;border-radius:8px;">
              <div style="font-size:11.5px;color:${meta.color};font-weight:800;margin-bottom:4px;">
                ${meta.icon} ${item.eje ? item.eje.toUpperCase() : 'PRISMA'} • ${item.subtitulo || ''}
              </div>
              <p style="font-size:12.5px;color:#e4e4e7;line-height:1.45;margin:0;">
                “${item.texto}”
              </p>
            </div>
          `;
        }).join('');
      } else if (digest.periodistas_prensa) {
        const colors = {
          ovacion: '#ffd100',
          tenfield: '#38bdf8',
          canal12: '#ef4444',
          canal4: '#f59e0b',
          elobservador: '#10b981',
          portalmvd: '#a855f7'
        };
        prensaGrid.innerHTML = Object.entries(digest.periodistas_prensa).map(([k, item]) => {
          const c = colors[k] || '#ffd100';
          return `
            <div class="clave-item" style="border-left:3px solid ${c};background:#141419;padding:12px;border-radius:8px;">
              <div style="font-size:11.5px;color:${c};font-weight:800;margin-bottom:4px;">
                ${item.medio} • ${item.cronistas}
              </div>
              <p style="font-size:12.5px;color:#e4e4e7;line-height:1.45;margin:0;">
                “${item.cita}”
              </p>
            </div>
          `;
        }).join('');
      }
    }
  }




  function initHistoricoDrawer() {
    const toggleBtn = document.getElementById('btn-toggle-historico');
    const content = document.getElementById('historico-drawer-content');
    const label = document.getElementById('historico-toggle-label');
    const icon = document.getElementById('historico-toggle-icon');

    if (!toggleBtn || !content) return;

    toggleBtn.addEventListener('click', () => {
      const isHidden = content.style.display === 'none' || content.style.display === '';
      if (isHidden) {
        content.style.display = 'block';
        toggleBtn.setAttribute('aria-expanded', 'true');
        if (label) label.textContent = '📁 Ocultar Registro Histórico del Partido Anterior';
        if (icon) {
          icon.textContent = '▲';
          icon.style.transform = 'rotate(180deg)';
        }
        toggleBtn.style.borderColor = 'var(--manya-gold)';
      } else {
        content.style.display = 'none';
        toggleBtn.setAttribute('aria-expanded', 'false');
        if (label) label.textContent = '📂 Ver Registro Completo, Minuto a Minuto y Estadísticas';
        if (icon) {
          icon.textContent = '▼';
          icon.style.transform = 'rotate(0deg)';
        }
        toggleBtn.style.borderColor = 'rgba(255,209,0,0.5)';
      }
    });
  }

  function renderRivalIntelligence(rival) {
    if (!rival) return;
    const dtEl = document.getElementById('scout-dt');
    const schEl = document.getElementById('scout-esquema');
    const estEl = document.getElementById('scout-estadio');
    const funEl = document.getElementById('scout-fundacion');
    const propEl = document.getElementById('scout-propuesta');
    const figEl = document.getElementById('scout-figuras');

    const sc = rival.scouting_tactico || {};
    const inst = rival.datos_institucionales_auf || {};

    if (dtEl && sc.entrenador) dtEl.textContent = sc.entrenador;
    if (schEl && sc.esquema_base) schEl.textContent = sc.esquema_base;
    if (estEl && inst.estadio_propio) estEl.textContent = inst.estadio_propio;
    if (funEl && inst.fundacion) funEl.textContent = inst.fundacion;
    if (propEl && sc.propuesta_juego) propEl.textContent = sc.propuesta_juego;

    if (figEl && sc.figuras_a_seguir && sc.figuras_a_seguir.length) {
      figEl.innerHTML = sc.figuras_a_seguir.map(f => `
        <div style="margin-bottom:4px;">
          • <strong>${f.nombre} (${f.rol}):</strong> <span style="color:#a1a1aa;">${f.analisis}</span>
        </div>
      `).join('');
    }

    const duelosContainer = document.getElementById('duelos-tacticos-container');
    if (duelosContainer && rival.duelos_tacticos_1x1 && rival.duelos_tacticos_1x1.length) {
      duelosContainer.innerHTML = rival.duelos_tacticos_1x1.map(d => `
        <div class="duel-item">
          <div class="duel-title-bar">
            <span class="duel-zone">${d.zona_campo}</span>
            <span class="duel-headline">${d.titulo}</span>
          </div>
          <div class="duel-sides-wrap">
            <div class="duel-side is-penarol">
              <div class="duel-player-header">
                <span class="duel-num">${d.penarol.dorsal || '★'}</span>
                <div>
                  <strong class="duel-player-name">${d.penarol.jugador}</strong>
                  <div class="duel-player-role">${d.penarol.rol}</div>
                </div>
              </div>
              <p class="duel-player-desc">${d.penarol.atributos_clave}</p>
            </div>

            <div class="duel-vs-divider">VS</div>

            <div class="duel-side is-rival">
              <div class="duel-player-header">
                <span class="duel-num rival">${d.rival.dorsal || 'R'}</span>
                <div>
                  <strong class="duel-player-name">${d.rival.jugador}</strong>
                  <div class="duel-player-role">${d.rival.rol}</div>
                </div>
              </div>
              <p class="duel-player-desc">${d.rival.atributos_clave}</p>
            </div>
          </div>
          <div class="duel-verdict">
            <strong>Clave del Duelo:</strong> ${d.clave_del_duelo}
          </div>
        </div>
      `).join('');
    }
  }

  function renderHeadToHead(h2h) {
    if (!h2h || !h2h.resumen) return;
    const res = h2h.resumen;
    const elPJ = document.getElementById('h2h-pj');
    const elPG = document.getElementById('h2h-pg');
    const elPE = document.getElementById('h2h-pe');
    const elPP = document.getElementById('h2h-pp');
    const elGF = document.getElementById('h2h-gf');
    const elEff = document.getElementById('h2h-eff');
    if (elPJ) elPJ.textContent = res.partidos_jugados;
    if (elPG) elPG.textContent = res.ganados_penarol;
    if (elPE) elPE.textContent = res.empatados;
    if (elPP) elPP.textContent = res.perdidos_penarol;
    if (elGF) elGF.textContent = `${res.goles_penarol} - ${res.goles_rival}`;
    if (elEff) elEff.textContent = res.efectividad_pct;
  }

  function renderEfemerides(efem) {
    if (!efem || !efem.partidos_historicos) return;
    const tagEl = document.getElementById('efemerides-date-tag');
    if (tagEl && efem.dia_mes) tagEl.textContent = efem.dia_mes;

    const gridEl = document.getElementById('efemerides-matches-grid');
    if (gridEl && efem.partidos_historicos.length) {
      gridEl.innerHTML = efem.partidos_historicos.slice(0, 6).map(m => {
        return `
          <article class="efemeride-item">
            <div class="efemeride-top-line">
              <span class="efemeride-year">${m.ano}</span>
              <span class="efemeride-torneo">${m.torneo || 'Torneo Oficial'}</span>
            </div>
            <div class="efemeride-score">${m.resultado}</div>
            <div class="efemeride-meta">
              <div>🏟️ ${m.estadio || 'Estadio Centenario'}</div>
              ${m.goles_detalle ? `<div style="margin-top:4px;color:#d4d4d8;">⚽ ${m.goles_detalle}</div>` : ''}
            </div>
          </article>
        `;
      }).join('');
    }

    const gloriasEl = document.getElementById('efemerides-glorias-line');
    if (gloriasEl && efem.cumpleanos_glorias && efem.cumpleanos_glorias.length) {
      // Filtrar nombres duplicados
      const nombresSet = new Set(efem.cumpleanos_glorias.map(g => g.nombre));
      const nombres = Array.from(nombresSet).map(n => `<strong>${n}</strong>`).join(' • ');
      gloriasEl.innerHTML = `<span>🎂 <strong>Glorias del Club:</strong> En estas fechas celebran su nacimiento: ${nombres}.</span>`;
    }
  }

  function renderInfluencersSection(influencers) {
    const grid = document.getElementById('influencers-grid');
    if (!grid || !influencers || !influencers.length) return;

    grid.innerHTML = influencers.map((inf, idx) => {
      return `
        <article class="ig-card influencer-card" data-inf-idx="${idx}" style="background:#111115;border:1px solid rgba(255,209,0,0.25);border-radius:14px;overflow:hidden;display:flex;flex-direction:column;transition:all 0.25s ease;">
          <!-- Header de Cuenta / Influencer -->
          <div style="padding:12px 16px;background:rgba(18,18,24,0.95);border-bottom:1px solid rgba(255,255,255,0.06);display:flex;align-items:center;justify-content:space-between;gap:10px;">
            <div style="display:flex;align-items:center;gap:10px;min-width:0;">
              <div class="ig-avatar-ring" style="width:42px;height:42px;flex-shrink:0;">
                <img src="${inf.avatar}" alt="Avatar ${inf.handle}" width="42" height="42" class="ig-avatar-img" style="border-radius:50%;object-fit:cover;" />
              </div>
              <div style="min-width:0;">
                <div style="display:flex;align-items:center;gap:4px;">
                  <strong style="font-size:13.5px;color:#ffffff;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${inf.nombre}</strong>
                  <span class="ig-verified-badge" title="Cuenta Verificada / Destacada" style="color:var(--manya-gold);font-size:12px;">✓</span>
                </div>
                <div style="font-size:12px;color:var(--manya-gold);font-weight:700;">${inf.handle}</div>
              </div>
            </div>
            <a href="${inf.url_instagram}" target="_blank" rel="noopener noreferrer" class="btn-outline-gold" style="padding:4px 10px;font-size:11px;font-weight:800;border-radius:999px;flex-shrink:0;text-decoration:none;">
              Seguir ↗
            </a>
          </div>

          <!-- Imagen del Partido Publicada -->
          <div class="ig-img-wrap" style="cursor:pointer;position:relative;aspect-ratio:16/9;overflow:hidden;" title="Click para ampliar imagen en alta definición">
            <img src="${inf.imagen_webp || inf.imagen_jpg}" alt="${inf.titulo} - ${inf.handle}" width="1280" height="720" loading="lazy" style="width:100%;height:100%;object-fit:cover;transition:transform 0.35s ease;" />
            <span class="ig-badge-tag" style="position:absolute;top:10px;left:10px;background:rgba(0,0,0,0.8);color:#ffd100;border:1px solid #ffd100;font-size:10.5px;padding:3px 8px;border-radius:6px;font-weight:800;">
              ${inf.badge}
            </span>
            <span style="position:absolute;bottom:10px;right:10px;background:rgba(0,0,0,0.75);color:#fff;font-size:11px;padding:3px 8px;border-radius:6px;">
              🔍 Ampliar
            </span>
          </div>

          <!-- Cuerpo: Stats, Titulo, Caption y Enlace a Instagram -->
          <div class="ig-body" style="padding:14px 16px;display:flex;flex-direction:column;flex-grow:1;justify-content:space-between;">
            <div>
              <div class="ig-meta" style="display:flex;justify-content:space-between;font-size:12px;color:var(--text-secondary);margin-bottom:8px;">
                <span>⚽ ${inf.partido}</span>
                <span style="color:#f87171;font-weight:800;">❤️ ${inf.likes_formato} • 💬 ${inf.comments}</span>
              </div>
              <h3 style="font-size:15px;font-weight:900;color:#ffffff;margin:0 0 8px;line-height:1.35;">
                <a href="${inf.url_instagram}" target="_blank" rel="noopener noreferrer" style="color:#ffffff;text-decoration:none;">${inf.titulo}</a>
              </h3>
              <p style="font-size:13px;color:#d4d4d8;line-height:1.5;margin:0 0 10px;">${inf.descripcion}</p>
              <div style="font-size:11.5px;color:var(--manya-gold);font-weight:700;margin-bottom:12px;">${inf.hashtags}</div>
            </div>
            <div style="display:flex;gap:8px;align-items:center;justify-content:space-between;padding-top:10px;border-top:1px solid rgba(255,255,255,0.06);">
              <button type="button" class="btn-outline-gold inf-zoom-btn" style="padding:5px 12px;font-size:11.5px;cursor:pointer;border-radius:6px;">
                🔍 Ver en Grande
              </button>
              <a href="${inf.url_instagram}" target="_blank" rel="noopener noreferrer" class="ig-external-btn" style="padding:5px 14px;font-size:11.5px;background:#ffd100;color:#09090b;font-weight:900;border-radius:6px;text-decoration:none;display:inline-flex;align-items:center;gap:4px;">
                Ver en Instagram ↗
              </a>
            </div>
          </div>
        </article>
      `;
    }).join('');

    // Conectar lightbox a las cards de influencers
    grid.querySelectorAll('.influencer-card').forEach(card => {
      const idx = parseInt(card.getAttribute('data-inf-idx'), 10);
      const item = influencers[idx];
      const imgWrap = card.querySelector('.ig-img-wrap');
      const zoomBtn = card.querySelector('.inf-zoom-btn');

      const triggerLightbox = () => {
        openLightbox({
          titulo: `${item.titulo} — ${item.handle}`,
          descripcion: `${item.descripcion}\n\n${item.hashtags}\nCuenta Oficial: ${item.nombre} (${item.handle})`,
          cuenta: item.handle,
          categoria: item.categoria,
          likes: item.likes,
          comments: item.comments,
          url_post: item.url_instagram,
          imagen_webp: item.imagen_webp,
          imagen_jpg: item.imagen_jpg
        });
      };

      if (imgWrap) imgWrap.addEventListener('click', triggerLightbox);
      if (zoomBtn) zoomBtn.addEventListener('click', triggerLightbox);
    });
  }

  async function init() {
    setupLightbox();

    const [live, digest, ig, galleries, squad, history, escudosCatalog, h2hJuventud, efemeridesHoy, rivalIntel, influencers] = await Promise.all([
      loadJsonSafe('data/live_status.json'),
      loadJsonSafe('data/news_digest.json'),
      loadJsonSafe('data/instagram_feed.json'),
      loadJsonSafe('data/galleries.json'),
      loadJsonSafe('data/squad_2026.json'),
      loadJsonSafe('data/history_1891.json'),
      loadJsonSafe('data/escudos_uruguay.json'),
      loadJsonSafe('data/historial_juventud.json'),
      loadJsonSafe('data/efemerides_hoy.json'),
      loadJsonSafe('data/rival_intelligence.json'),
      loadJsonSafe('data/influencers_feed.json')
    ]);

    if (escudosCatalog) {
      state.escudosCatalog = escudosCatalog;
    }

    if (live) {
      state.live = live;
      state.standingsTab = live.torneo_activo_id || 'clausura';
      renderMatchHero(live);
      renderLiveTimeline(live);
      renderStandings();
      setupLivePolling();
    }
    if (h2hJuventud) {
      renderHeadToHead(h2hJuventud);
    }
    if (efemeridesHoy) {
      renderEfemerides(efemeridesHoy);
    }
    if (rivalIntel) {
      renderRivalIntelligence(rivalIntel);
    }
    initHistoricoDrawer();
    initStandingsTabs();
    initSimulator();
    if (influencers && influencers.length) {
      renderInfluencersSection(influencers);
    }

    // Priorizar galería completa multicanal (galleries.json) combinada con instagram_feed.json
    const allGalleryItems = (galleries && galleries.length) ? galleries : (ig || []);
    renderHeroInstagramPost(allGalleryItems.length ? allGalleryItems[0] : null, digest);

    if (allGalleryItems.length) {
      state.galleries = allGalleryItems;
      renderGallery(allGalleryItems, 'all');
      setupGalleryFilters(allGalleryItems);
    }

    if (squad && squad.jugadores) {
      state.squad = squad;
      state.lineup = squad.jugadores.filter(p => p.titular).slice(0, 11);
      state.bench = squad.jugadores.filter(p => !p.titular);
      renderTacticalBoard();
    }

    document.querySelectorAll('[data-formation]').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('[data-formation]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        state.formation = btn.getAttribute('data-formation');
        renderTacticalBoard();
      });
    });

    const expBtn = document.getElementById('export-lineup-btn');
    if (expBtn) expBtn.addEventListener('click', exportLineupPNG);

    const shareLineupBtn = document.getElementById('share-lineup-btn');
    if (shareLineupBtn) {
      shareLineupBtn.addEventListener('click', async () => {
        const text = `⚽ Mi 11 Titular del Glorioso Peñarol (${state.formation}) armado en manya.servicioti.com.uy:\n` +
          state.lineup.slice(0, 11).map((p, i) => `#${p.numero} ${p.nombre}`).join('\n') +
          '\n\n¡Armá tu 11 y compartilo desde https://manya.servicioti.com.uy/#pizarra-tactica !';
        if (navigator.share) {
          try {
            await navigator.share({
              title: 'Mi 11 Titular del Glorioso Peñarol',
              text: text,
              url: 'https://manya.servicioti.com.uy/#pizarra-tactica'
            });
          } catch (e) {
            if (e.name !== 'AbortError') {
              navigator.clipboard?.writeText(text);
              alert('¡11 Titular copiado al portapapeles!');
            }
          }
        } else {
          navigator.clipboard?.writeText(text);
          const orig = shareLineupBtn.textContent;
          shareLineupBtn.textContent = '✅ ¡Copiado!';
          setTimeout(() => { shareLineupBtn.textContent = orig; }, 2000);
        }
      });
    }

    if (digest) {
      const bUrl = digest.blogger_post_url || 'https://www.servicioti.com.uy/p/penarol-proximo-partido-radiografia.html';
      document.querySelectorAll('.dynamic-blogger-link').forEach(a => {
        a.href = bUrl;
        a.target = '_blank';
        a.rel = 'noopener noreferrer';
      });
      hydrateEditorialSection(digest);
    }

    renderTrivia();

    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

