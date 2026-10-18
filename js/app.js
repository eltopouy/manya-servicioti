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
    formation: '4-2-3-1',
    selectedSlotIndex: null,
    lineup: [],
    bench: [],
    simPointsDelta: 0,
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
      q: '¿En qué fecha exacta se fundó nuestra gloriosa institución (CURCC / Club Atlético Peñarol)?',
      opts: ['28 de septiembre de 1891', '14 de mayo de 1899', '18 de julio de 1900', '25 de agosto de 1891'],
      ans: 0,
      exp: 'El 28 de septiembre de 1891 en la Villa Peñarol se fundó el Central Uruguay Railway Cricket Club (CURCC), decano del fútbol uruguayo.'
    },
    {
      q: '¿Quién convirtió el gol agónico en el minuto 120 en Santiago de Chile para ganar la quinta Copa Libertadores en 1987?',
      opts: ['Diego Aguirre', 'Fernando Morena', 'Alberto Spencer', 'Jorge Cabrera'],
      ans: 0,
      exp: 'Diego "La Fiera" Aguirre anotó de zurda a los 120 minutos ante América de Cali el 31 de octubre de 1987 en el Estadio Nacional de Santiago.'
    },
    {
      q: '¿Quién es el máximo goleador histórico de toda la Copa CONMEBOL Libertadores de América con 54 goles?',
      opts: ['Alberto "Cabeza Mágica" Spencer', 'Fernando Morena', 'Pedro Virgilio Rocha', 'Juan Alberto Schiaffino'],
      ans: 0,
      exp: 'Alberto Spencer convirtió 54 goles en la Copa Libertadores (48 de ellos con la camiseta de Peñarol), récord absoluto desde 1960 hasta hoy.'
    },
    {
      q: '¿Contra qué gigantes europeos e ingleses ganó Peñarol sus 3 Copas Intercontinentales del Mundo?',
      opts: ['Benfica (1961), Real Madrid (1966) y Aston Villa (1982)', 'Milan (1961), Real Madrid (1966) y Liverpool (1982)', 'Benfica (1960), Inter (1966) y Hamburgo (1982)', 'Ajax (1961), Real Madrid (1966) y Juventus (1982)'],
      ans: 0,
      exp: 'Peñarol fue tricampeón del mundo superando al Benfica de Eusébio (1961), al Real Madrid (1966, ganando en Montevideo y en el Bernabéu) y al Aston Villa en Tokio (1982).'
    },
    {
      q: '¿Cómo se llama el histórico capitán que jugó toda su carrera profesional en Peñarol (1957–1970) y da nombre a nuestra Ciudad Deportiva?',
      opts: ['Néstor "Tito" Gonçalves', 'Obdulio Varela', 'William Martínez', 'Walter Olivera'],
      ans: 0,
      exp: 'Néstor "Tito" Gonçalves, el "Capitán de Capitanes", disputó 574 partidos oficiales exclusivamente con la camiseta oro y carbón.'
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
    const target = isoString ? new Date(isoString).getTime() : (Date.now() + 3 * 86400000);
    function tick() {
      const diff = Math.max(0, target - Date.now());
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
    }
    tick();
    setInterval(tick, 1000);
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
    const tDate = document.getElementById('hero-match-date');
    const tVenue = document.getElementById('hero-match-venue');
    const tLast = document.getElementById('hero-last-result');

    if (tHome && prox.local) {
      tHome.textContent = prox.local.nombre;
      tHome.className = 'match-team-name ' + (prox.local.es_penarol ? 'is-penarol' : '');
    }
    if (tAway && prox.visitante) {
      tAway.textContent = prox.visitante.nombre;
      tAway.className = 'match-team-name ' + (prox.visitante.es_penarol ? 'is-penarol' : '');
    }
    if (tDate && prox.fecha_legible) tDate.textContent = prox.fecha_legible;
    if (tVenue && prox.estadio) tVenue.textContent = prox.estadio;
    if (tLast && ult.local && ult.visitante) {
      tLast.textContent = `${ult.local.nombre} ${ult.local.goles} - ${ult.visitante.goles} ${ult.visitante.nombre}`;
    }

    startCountdown(prox.fecha_iso);
  }

  function renderStandings() {
    if (!state.live || !state.live.tabla_posiciones) return;
    const tbody = document.getElementById('standings-tbody');
    if (!tbody) return;

    const rows = state.live.tabla_posiciones.map(r => {
      const pts = r.es_penarol ? (r.pts + state.simPointsDelta) : r.pts;
      const pj = r.es_penarol && state.simPointsDelta > 0 ? (r.pj + Math.ceil(state.simPointsDelta / 3)) : r.pj;
      return Object.assign({}, r, { pts_calc: pts, pj_calc: pj });
    });

    rows.sort((a, b) => b.pts_calc - a.pts_calc);

    tbody.innerHTML = rows.map((r, i) => `
      <tr class="${r.es_penarol ? 'row-penarol' : ''}">
        <td>${i + 1}</td>
        <td>${r.es_penarol ? '★ ' : ''}${r.equipo}</td>
        <td>${r.pj_calc}</td>
        <td>${r.pg}</td>
        <td>${r.pe}</td>
        <td>${r.pp}</td>
        <td>${r.dg}</td>
        <td><strong>${r.pts_calc}</strong></td>
      </tr>
    `).join('');
  }

  function initSimulator() {
    const container = document.getElementById('sim-matches-box');
    if (!container) return;
    const fechas = [
      { id: 1, label: 'Próxima Fecha (Local en el CDS)' },
      { id: 2, label: 'Fecha +2 (Visitante)' },
      { id: 3, label: 'Fecha +3 (Local en el CDS)' }
    ];
    const picks = { 1: 3, 2: 3, 3: 3 };

    function updateSim() {
      state.simPointsDelta = Object.values(picks).reduce((a, b) => a + b, 0);
      const ptsEl = document.getElementById('sim-delta-label');
      if (ptsEl) ptsEl.textContent = `+${state.simPointsDelta} pts proyectados para Peñarol`;
      renderStandings();
    }

    container.innerHTML = fechas.map(f => `
      <div class="sim-row" data-fid="${f.id}">
        <span><strong>${f.label}</strong></span>
        <div class="sim-btns">
          <button type="button" class="sim-btn active" data-pts="3">Gana (+3)</button>
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
    ctx.font = '700 26px Inter, sans-serif';
    ctx.fillText(`Esquema Táctico: ${state.formation} • manya.servicioti.com.uy`, 540, 130);

    // Cancha
    ctx.fillStyle = '#14532d';
    ctx.fillRect(90, 170, 900, 1020);
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 4;
    ctx.strokeRect(90, 170, 900, 1020);
    ctx.beginPath();
    ctx.moveTo(90, 680);
    ctx.lineTo(990, 680);
    ctx.stroke();

    const coords = FORMATIONS[state.formation] || FORMATIONS['4-2-3-1'];
    state.lineup.slice(0, 11).forEach((p, idx) => {
      const c = coords[idx] || { x: 50, y: 50 };
      const px = 90 + (c.x / 100) * 900;
      const py = 170 + (c.y / 100) * 1020;

      ctx.beginPath();
      ctx.arc(px, py, 34, 0, Math.PI * 2);
      ctx.fillStyle = '#ffd100';
      ctx.fill();
      ctx.lineWidth = 4;
      ctx.strokeStyle = '#09090b';
      ctx.stroke();

      ctx.fillStyle = '#09090b';
      ctx.font = '900 26px Inter, sans-serif';
      ctx.fillText(String(p.numero), px, py + 9);

      ctx.fillStyle = '#ffffff';
      ctx.font = '800 22px Inter, sans-serif';
      ctx.fillText(p.nombre, px, py + 62);
    });

    ctx.fillStyle = '#ffd100';
    ctx.font = '800 24px Inter, sans-serif';
    ctx.fillText('Creado en https://manya.servicioti.com.uy • ServicioTI Uruguay', 540, 1280);

    const link = document.createElement('a');
    link.download = `mi-11-penarol-${state.formation}.png`;
    link.href = canvas.toDataURL('image/png');
    link.click();
  }

  function renderTrivia() {
    const box = document.getElementById('trivia-box');
    if (!box) return;
    const item = TRIVIA_QUESTIONS[state.triviaIndex % TRIVIA_QUESTIONS.length];

    box.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <span class="badge-gold">Pregunta ${(state.triviaIndex % TRIVIA_QUESTIONS.length) + 1} de ${TRIVIA_QUESTIONS.length}</span>
        <span style="color:var(--manya-gold);font-weight:800;">Puntaje Aurinegro: ${state.triviaScore} pts</span>
      </div>
      <h4 style="font-size:17px;margin-bottom:14px;color:#fff;">${item.q}</h4>
      <div style="display:grid;gap:10px;" id="trivia-opts">
        ${item.opts.map((o, i) => `
          <button type="button" class="sim-btn" style="text-align:left;padding:12px 14px;font-size:14px;" data-idx="${i}">
            ${o}
          </button>
        `).join('')}
      </div>
      <div id="trivia-feedback" style="margin-top:14px;font-size:13.5px;color:#fde047;display:none;"></div>
    `;

    const fb = box.querySelector('#trivia-feedback');
    box.querySelectorAll('#trivia-opts button').forEach(btn => {
      btn.addEventListener('click', () => {
        const chosen = parseInt(btn.getAttribute('data-idx'), 10);
        if (chosen === item.ans) {
          state.triviaScore += 100;
          btn.style.background = '#15803d';
          fb.innerHTML = `✅ <strong>¡Correcto, Carbonero!</strong> ${item.exp} <br><button type="button" class="btn-manya" style="margin-top:10px;padding:7px 14px;" id="trivia-next">Siguiente Pregunta →</button>`;
        } else {
          btn.style.background = '#b91c1c';
          fb.innerHTML = `❌ <strong>Respuesta histórica:</strong> ${item.exp} <br><button type="button" class="btn-manya" style="margin-top:10px;padding:7px 14px;" id="trivia-next">Siguiente Pregunta →</button>`;
        }
        fb.style.display = 'block';
        const nxt = box.querySelector('#trivia-next');
        if (nxt) {
          nxt.addEventListener('click', () => {
            state.triviaIndex++;
            renderTrivia();
          });
        }
      });
    });
  }

  async function init() {
    const [live, digest, ig, squad, history] = await Promise.all([
      loadJsonSafe('data/live_status.json'),
      loadJsonSafe('data/news_digest.json'),
      loadJsonSafe('data/instagram_feed.json'),
      loadJsonSafe('data/squad_2026.json'),
      loadJsonSafe('data/history_1891.json')
    ]);

    if (live) {
      state.live = live;
      renderMatchHero(live);
      renderStandings();
    }
    initSimulator();

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

    if (digest) {
      const bUrl = digest.blogger_post_url;
      if (bUrl) {
        document.querySelectorAll('.dynamic-blogger-link').forEach(a => {
          a.href = bUrl;
        });
      }
      if (digest.noticias_fuentes && digest.noticias_fuentes.length) {
        const newsListEl = document.getElementById('live-news-list');
        if (newsListEl) {
          newsListEl.innerHTML = digest.noticias_fuentes.slice(0, 8).map(n => `
            <article class="clave-card" style="border-top-color:#3f3f46;">
              <div style="font-size:11.5px;color:var(--manya-gold);font-weight:800;margin-bottom:4px;">📰 ${n.fuente} • ${n.fecha}</div>
              <h3 style="font-size:15px;color:#fff;margin-bottom:6px;">${n.titulo}</h3>
              <p style="font-size:13px;color:#a1a1aa;margin-bottom:10px;">${n.resumen}</p>
              <a href="${bUrl || 'https://www.servicioti.com.uy'}" class="btn-outline-gold" style="padding:5px 12px;font-size:12px;">Leer análisis en ServicioTI →</a>
            </article>
          `).join('');
        }
      }
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
