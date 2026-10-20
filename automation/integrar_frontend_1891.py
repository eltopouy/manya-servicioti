# -*- coding: utf-8 -*-
"""
Integra los componentes de 1891 BD en index.html y js/app.js:
1. Historial Frente a Frente vs Juventud en #match-center.
2. Filtro 'Fichas 1891 BD' en la galería #muro-visual.
3. Efemérides Aurinegras 'Un día como hoy' en #museo-1891.
4. Soporte en js/app.js para renderizar los datos y lightbox.
"""

from pathlib import Path
import sys

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_HTML = BASE_DIR / "index.html"
APP_JS = BASE_DIR / "js" / "app.js"

def actualizar_index_html():
    content = INDEX_HTML.read_text(encoding="utf-8")

    # 1. Historial Frente a Frente en #match-center
    h2h_html = """
      <!-- Historial Oficial Frente a Frente (1891 BD) -->
      <div class="match-h2h-bar" id="match-h2h-box" aria-label="Historial Oficial Frente a Frente contra Juventud">
        <div class="match-h2h-header">
          <div class="match-h2h-title">
            <span>📜 Historial Oficial Frente a Frente: Peñarol vs Juventud</span>
          </div>
          <span class="match-h2h-source">Fuente Oficial: <strong>1891 BD</strong> (Comisión de Historia y Patrimonio)</span>
        </div>

        <div class="match-h2h-stats">
          <div class="match-h2h-stat">
            <div class="match-h2h-stat-num" id="h2h-pj">33</div>
            <div class="match-h2h-stat-lbl">Partidos Jugados</div>
          </div>
          <div class="match-h2h-stat">
            <div class="match-h2h-stat-num gold" id="h2h-pg">23</div>
            <div class="match-h2h-stat-lbl">Ganados Peñarol</div>
          </div>
          <div class="match-h2h-stat">
            <div class="match-h2h-stat-num" id="h2h-pe">7</div>
            <div class="match-h2h-stat-lbl">Empates</div>
          </div>
          <div class="match-h2h-stat">
            <div class="match-h2h-stat-num" id="h2h-pp">3</div>
            <div class="match-h2h-stat-lbl">Derrotas</div>
          </div>
          <div class="match-h2h-stat">
            <div class="match-h2h-stat-num gold" id="h2h-gf">67 - 22</div>
            <div class="match-h2h-stat-lbl">Goles (Dif: +45)</div>
          </div>
          <div class="match-h2h-stat">
            <div class="match-h2h-stat-num gold" id="h2h-eff">76.7%</div>
            <div class="match-h2h-stat-lbl">Efectividad Aurinegra</div>
          </div>
        </div>

        <div class="match-h2h-recent">
          <span class="match-h2h-pill">★ +20 partidos a favor del Decano</span>
          <span><strong>Últimos choques oficiales:</strong> 2-2 en Campeón del Siglo (Apertura 2026), 1-0 en CDS (Clausura 2025, gol de Leo Fernández 49'), 2-0 en Parque Artigas (Apertura 2025).</span>
          <a href="https://1891.uy/partidos" target="_blank" rel="noopener noreferrer" style="color:var(--manya-gold);text-decoration:underline;margin-left:auto;font-size:11.5px;font-weight:700;">Ver fichas completas en 1891.uy ↗</a>
        </div>
      </div>
    </section>"""

    # Buscar el cierre de section id="match-center"
    # Reemplazamos la sección final de match-center si no fue insertado aún
    if "match-h2h-box" not in content:
        # Reemplazar el cierre de match-center
        target_mc = '      </div>\n    </section>\n\n    <!-- MÓDULO 2:'
        target_mc_crlf = '      </div>\r\n    </section>\r\n\r\n    <!-- MÓDULO 2:'
        
        if target_mc_crlf in content:
            content = content.replace(target_mc_crlf, '      </div>\r\n' + h2h_html.replace('\n', '\r\n') + '\r\n\r\n    <!-- MÓDULO 2:')
        elif target_mc in content:
            content = content.replace(target_mc, '      </div>\n' + h2h_html + '\n\n    <!-- MÓDULO 2:')
        else:
            print("AVISO: No se encontró el marcador exacto para #match-center")

    # 2. Botón de filtro 'Fichas 1891 BD' en la galería
    filter_old = '<button type="button" class="gallery-tab" data-filter="partidos">Partidos &amp; Goles</button>'
    filter_new = '<button type="button" class="gallery-tab" data-filter="1891">Fichas 1891 BD</button>\n          <button type="button" class="gallery-tab" data-filter="partidos">Partidos &amp; Goles</button>'
    if 'data-filter="1891"' not in content:
        content = content.replace(filter_old, filter_new)

    # 3. Efemérides Aurinegras en #museo-1891
    efem_html = """
      <!-- Efemérides "Un día como hoy en la historia aurinegra" (1891 BD) -->
      <div class="efemerides-card" id="efemerides-1891-card" aria-label="Efemérides aurinegras del día">
        <div class="efemerides-header">
          <div>
            <h3 style="font-size:18px;color:var(--manya-gold);margin-bottom:4px;display:flex;align-items:center;gap:8px;">
              <span>📅 Efemérides Aurinegras: "Un día como hoy"</span>
              <span id="efemerides-date-tag" class="badge-gold">20 de Octubre</span>
            </h3>
            <p style="font-size:13px;color:var(--text-secondary);margin:0;">
              Partidos históricos y glorias decanas registradas en la base oficial de la Comisión de Historia y Patrimonio de Peñarol (1891 BD).
            </p>
          </div>
          <a href="https://1891.uy/" target="_blank" rel="noopener noreferrer" class="btn-outline-gold" style="font-size:12px;padding:6px 12px;">
            Consultar Archivo 1891.uy ↗
          </a>
        </div>

        <div class="efemerides-grid" id="efemerides-matches-grid">
          <!-- Renderizado dinámicamente desde data/efemerides_hoy.json -->
        </div>

        <div class="efemerides-glorias" id="efemerides-glorias-line">
          <!-- Cumpleaños de glorias aurinegras -->
        </div>
      </div>
    </section>"""

    if "efemerides-1891-card" not in content:
        target_museo = '        </div>\n      </div>\n    </section>\n\n    <!-- PREGUNTAS FRECUENTES'
        target_museo_crlf = '        </div>\r\n      </div>\r\n    </section>\r\n\r\n    <!-- PREGUNTAS FRECUENTES'
        if target_museo_crlf in content:
            content = content.replace(target_museo_crlf, '        </div>\r\n      </div>\r\n' + efem_html.replace('\n', '\r\n') + '\r\n\r\n    <!-- PREGUNTAS FRECUENTES')
        elif target_museo in content:
            content = content.replace(target_museo, '        </div>\n      </div>\n' + efem_html + '\n\n    <!-- PREGUNTAS FRECUENTES')
        else:
            print("AVISO: No se encontró el marcador exacto para #museo-1891")

    INDEX_HTML.write_text(content, encoding="utf-8")
    print("✓ index.html actualizado exitosamente.")

def actualizar_app_js():
    content = APP_JS.read_text(encoding="utf-8")

    # Actualizar openLightbox con soporte para 1891 BD
    old_lb_badge = "badgeEl.textContent = `📸 ${item.categoria ? item.categoria.toUpperCase() : 'PEÑAROL'}`;"
    new_lb_badge = """const is1891 = (item.cuenta === '1891.uy') || (item.url_post && item.url_post.includes('1891.uy')) || (item.fuente && item.fuente.includes('1891'));
      badgeEl.textContent = is1891 ? '📜 FICHA OFICIAL 1891 BD' : `📸 ${item.categoria ? item.categoria.toUpperCase() : 'PEÑAROL'}`;"""
    if "is1891" not in content:
        content = content.replace(old_lb_badge, new_lb_badge)

    old_lb_meta = "metaEl.textContent = `${item.cuenta} • ❤️ ${item.likes ? item.likes.toLocaleString() : '25.000'} • 💬 ${item.comments || 350}`;"
    new_lb_meta = """if (is1891) {
        metaEl.textContent = `1891 BD (Comisión de Historia) • ${item.estadio || 'Estadio Centenario'} • ${item.fecha || '2026'}`;
      } else {
        metaEl.textContent = `${item.cuenta} • ❤️ ${item.likes ? item.likes.toLocaleString() : '25.000'} • 💬 ${item.comments || 350}`;
      }"""
    content = content.replace(old_lb_meta, new_lb_meta)

    old_lb_link = """      linkEl.href = pUrl;
      linkEl.textContent = isPD ? 'Ver artículo en Padre y Decano ↗' : (isTenfield ? 'Ver cobertura oficial en Tenfield Deportes ↗' : 'Ver publicación original en Instagram ↗');"""
    new_lb_link = """      const pUrl1891 = is1891 ? 'https://1891.uy/partidos' : pUrl;
      linkEl.href = pUrl1891;
      linkEl.textContent = is1891 ? 'Ver ficha del partido en 1891.uy ↗' : (isPD ? 'Ver artículo en Padre y Decano ↗' : (isTenfield ? 'Ver cobertura oficial en Tenfield Deportes ↗' : 'Ver publicación original en Instagram ↗'));"""
    content = content.replace(old_lb_link, new_lb_link)

    # Actualizar renderGallery para el badge de 1891
    old_rg_badge = "const badgeTxt = `📸 ${(item.categoria || 'Peñarol').replace('-', ' ').toUpperCase()}`;"
    new_rg_badge = """const isItem1891 = (item.cuenta === '1891.uy') || (item.url_post && item.url_post.includes('1891.uy')) || (item.fuente && item.fuente.includes('1891'));
      const badgeTxt = isItem1891 ? '📜 FICHA 1891 BD' : `📸 ${(item.categoria || 'Peñarol').replace('-', ' ').toUpperCase()}`;"""
    content = content.replace(old_rg_badge, new_rg_badge)

    # Agregar funciones renderHeadToHead y renderEfemerides si no existen
    if "function renderHeadToHead" not in content:
        extra_funcs = """
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
"""
        # Insertar antes de async function init()
        content = content.replace("  async function init() {", extra_funcs + "\n  async function init() {")

    # Actualizar init() para cargar h2h y efemerides
    old_init_load = """    const [live, digest, ig, galleries, squad, history, escudosCatalog] = await Promise.all([
      loadJsonSafe('data/live_status.json'),
      loadJsonSafe('data/news_digest.json'),
      loadJsonSafe('data/instagram_feed.json'),
      loadJsonSafe('data/galleries.json'),
      loadJsonSafe('data/squad_2026.json'),
      loadJsonSafe('data/history_1891.json'),
      loadJsonSafe('data/escudos_uruguay.json')
    ]);"""
    new_init_load = """    const [live, digest, ig, galleries, squad, history, escudosCatalog, h2hJuventud, efemeridesHoy] = await Promise.all([
      loadJsonSafe('data/live_status.json'),
      loadJsonSafe('data/news_digest.json'),
      loadJsonSafe('data/instagram_feed.json'),
      loadJsonSafe('data/galleries.json'),
      loadJsonSafe('data/squad_2026.json'),
      loadJsonSafe('data/history_1891.json'),
      loadJsonSafe('data/escudos_uruguay.json'),
      loadJsonSafe('data/historial_juventud.json'),
      loadJsonSafe('data/efemerides_hoy.json')
    ]);"""
    if "h2hJuventud" not in content:
        content = content.replace(old_init_load, new_init_load)

    # Llamar renderHeadToHead y renderEfemerides en init
    old_init_calls = """    if (live) {
      state.live = live;
      renderMatchHero(live);
      renderStandings();
    }"""
    new_init_calls = """    if (live) {
      state.live = live;
      renderMatchHero(live);
      renderStandings();
    }
    if (h2hJuventud) {
      renderHeadToHead(h2hJuventud);
    }
    if (efemeridesHoy) {
      renderEfemerides(efemeridesHoy);
    }"""
    if "renderHeadToHead(h2hJuventud)" not in content:
        content = content.replace(old_init_calls, new_init_calls)

    APP_JS.write_text(content, encoding="utf-8")
    print("✓ js/app.js actualizado exitosamente.")

if __name__ == "__main__":
    actualizar_index_html()
    actualizar_app_js()
