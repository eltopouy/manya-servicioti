# -*- coding: utf-8 -*-
"""
REESTRUCTURACIÓN TRIPARTITA DEL FRONTEND: FUTURO, ACTUALIDAD Y PASADO
=====================================================================
Archivo: automation/reestructurar_tripartita_frontend.py
1. Futuro en Primera Plana: Scouting de Montevideo Wanderers (DT Antonio Pacheco),
   Duelos 1x1, Historial 1891 BD y Cuenta Regresiva Activa.
2. Pasado Colapsable: El partido concluido (Juventud 0-0 Peñarol: minuto a minuto,
   mapa de calor, estadísticas, audios radiales) queda oculto por defecto en un cajón
   elegante de 1-click para acceder al archivo histórico sin contaminar la portada.
3. Actualidad: El Diario de Peñarol (4 Prismas), Tabla Anual & Simulador (64 pts),
   Pizarra vs Wanderers y Portada Oficial.
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_HTML = BASE_DIR / "index.html"
APP_JS = BASE_DIR / "js" / "app.js"
DATA_DIR = BASE_DIR / "data"

def reestructurar():
    index_content = INDEX_HTML.read_text(encoding="utf-8").replace("\r\n", "\n")
    app_content = APP_JS.read_text(encoding="utf-8").replace("\r\n", "\n")

    # 1. Actualizar Navbar con la nueva arquitectura
    old_nav = """      <nav class="manya-nav" aria-label="Secciones principales">
        <a href="#match-center" class="active">🔴 Minuto a Minuto</a>
        <a href="#portada-visual">📸 Portada Oficial</a>
        <a href="#resumen-ia">📰 El Diario</a>
        <a href="#tabla-simulador">📊 Tabla</a>
        <a href="#pizarra-tactica">👕 Armá tu 11</a>
        <a href="#influencers-manya">📸 Influencers</a>
        <a href="#muro-visual">🖼️ Galerías</a>
        <a href="#como-llegar">🚌 Ómnibus</a>
      </nav>"""

    new_nav = """      <nav class="manya-nav" aria-label="Secciones principales">
        <a href="#match-center" class="active">📅 Próximo Partido</a>
        <a href="#rival-scout-box">🧭 Scouting Wanderers</a>
        <a href="#resumen-ia">📰 El Diario</a>
        <a href="#tabla-simulador">📊 Tabla</a>
        <a href="#pizarra-tactica">👕 Armá tu 11</a>
        <a href="#historico-partido-anterior">📂 Histórico</a>
        <a href="#influencers-manya">📸 Influencers</a>
        <a href="#como-llegar">🚌 Ómnibus</a>
      </nav>"""

    if old_nav in index_content:
        index_content = index_content.replace(old_nav, new_nav)
        print("[OK] Navbar actualizado.")

    # 2. Localizar y extraer:
    # a) match-center-live-card (contenido del partido anterior Juventud)
    # b) rival-scout-box + duelos-1x1-box + match-h2h-box (scouting del próximo partido)

    # Identificar match-center-live-card
    start_live = index_content.find('<!-- Match Center Minuto a Minuto en Vivo (Actualizado en Directo) -->')
    end_live = index_content.find('<!-- Historial Oficial Frente a Frente (1891 BD) -->')
    
    live_card_block = ""
    if start_live != -1 and end_live != -1:
        live_card_block = index_content[start_live:end_live].strip()

    # Identificar scouting, duelos y h2h
    start_scout_full = index_content.find('<!-- Historial Oficial Frente a Frente (1891 BD) -->')
    end_scout_full = index_content.find('</section>\n\n    <!-- MÓDULO 2:')
    if end_scout_full == -1:
        end_scout_full = index_content.find('</section>\n\n    <!-- MÓDULO 2')

    scout_block = ""
    if start_scout_full != -1 and end_scout_full != -1:
        scout_block = index_content[start_scout_full:end_scout_full].strip()

    # Nuevo Bloque de Scouting de Wanderers (FUTURO EN PRIMERA PLANA)
    nuevo_scout_wanderers = """      <!-- ============================================================== -->
      <!-- FUTURO: SCOUTING TÁCTICO & RADIOGRAFÍA DEL PRÓXIMO RIVAL (WANDERERS) -->
      <!-- ============================================================== -->
      <div class="rival-scout-card" id="rival-scout-box" aria-label="Informe Táctico y Scouting del Rival" style="margin-top:20px;">
        <div class="rival-scout-header">
          <div class="rival-scout-title">
            <span id="scout-rival-title">🧭 Radiografía Táctica del Próximo Rival: Montevideo Wanderers (DT Antonio Pacheco)</span>
          </div>
          <div class="rival-scout-badges">
            <span class="badge-gold">AUF Oficial</span>
            <span class="badge-weather">Ovación Digital</span>
            <span class="badge-gold">1891 BD Certificado</span>
          </div>
        </div>

        <div class="rival-scout-grid">
          <!-- Columna 1: Ficha Institucional AUF y DT -->
          <div class="rival-col-card">
            <div class="rival-card-sub">🏛️ Ficha Institucional AUF &amp; DT</div>
            <ul class="rival-meta-list">
              <li><strong>Entrenador:</strong> <span id="scout-dt">Antonio Pacheco</span></li>
              <li><strong>Esquema Base:</strong> <span id="scout-esquema">4-2-3-1 de posesión y transiciones veloces</span></li>
              <li><strong>Estadio Propio:</strong> <span id="scout-estadio">Parque Alfredo Víctor Viera (Prado)</span></li>
              <li><strong>Fundación:</strong> <span id="scout-fundacion">15 de agosto de 1902</span></li>
              <li><strong>Web Oficial:</strong> <a href="https://mwfc.com.uy/" target="_blank" rel="noopener noreferrer" style="color:var(--manya-gold);text-decoration:underline;">mwfc.com.uy ↗</a></li>
            </ul>
          </div>

          <!-- Columna 2: Propuesta Táctica & Puntos Fuertes -->
          <div class="rival-col-card">
            <div class="rival-card-sub">⚡ Propuesta &amp; Fortalezas</div>
            <p id="scout-propuesta" style="font-size:12.5px;color:#d4d4d8;line-height:1.45;margin-bottom:8px;">
              Montevideo Wanderers, conducido tácticamente por Antonio Pacheco, pregona un fútbol de buen trato de balón, salida limpia desde el fondo y posesión paciente. Apuestan a la creatividad de Tabaré Viudez y Bruno Veglio en tres cuartos.
            </p>
            <div class="scout-pill-group">
              <span class="scout-pill strong">✓ Fluidez en la circulación media y buen pie</span>
              <span class="scout-pill strong">✓ Peligro en tiros libres y media distancia de Viudez</span>
              <span class="scout-pill strong">✓ Conocimiento táctico del cuerpo técnico de Pacheco</span>
            </div>
          </div>

          <!-- Columna 3: Figuras a Seguir & Vulnerabilidades -->
          <div class="rival-col-card">
            <div class="rival-card-sub">🎯 Figuras a Seguir &amp; Dónde Dañar</div>
            <div id="scout-figuras" style="font-size:12px;color:#e4e4e7;margin-bottom:8px;">
              <div>• <strong>Tabaré Viudez (MCO):</strong> Calidad técnica, pausa y tiro libre letal.</div>
              <div>• <strong>Bruno Veglio (MC):</strong> El termómetro del mediocampo bohemio.</div>
              <div>• <strong>Matías Fonseca (DC):</strong> Movilidad continua en el frente de ataque.</div>
              <div>• <strong>Mauro Silveira (ARQ):</strong> Seguridad y juego con los pies.</div>
            </div>
            <div class="scout-pill-group">
              <span class="scout-pill weak">⚠️ Vulnerables si Peñarol presiona alto su salida</span>
              <span class="scout-pill weak">⚠️ Espaldas de laterales libres ante transiciones rápidas</span>
              <span class="scout-pill weak">⚠️ Desventaja física en el juego aéreo defensivo</span>
            </div>
          </div>
        </div>
      </div>

      <!-- DUELOS TÁCTICOS 1x1 CLAVE ANTE WANDERERS -->
      <div class="duelos-1x1-card" id="duelos-1x1-box" aria-label="Duelos Tácticos Clave 1x1" style="margin-top:20px;">
        <div class="duelos-1x1-header">
          <div class="duelos-1x1-title">
            <span>⚔️ Duelos Tácticos 1x1: Las Batallas Clave en el Prado</span>
          </div>
          <span class="badge-gold">Laboratorio Táctico Manya</span>
        </div>

        <div class="duelos-grid" id="duelos-tacticos-container">
          <div class="duel-item">
            <div class="duel-title-bar">
              <span class="duel-zone">Zona 14 / Eje Central</span>
              <span class="duel-headline">El Duelo de Motores: Generación vs. Circulación</span>
            </div>
            <div class="duel-sides-wrap">
              <div class="duel-side is-penarol">
                <div class="duel-player-header">
                  <span class="duel-num">8</span>
                  <div>
                    <strong class="duel-player-name">Leonardo Fernández</strong>
                    <div class="duel-player-role">Enganche / Conductor Aurinegro</div>
                  </div>
                </div>
                <p class="duel-player-desc">Visión panorámica, pegada quirúrgica de balón parado y latigazo teledirigido.</p>
              </div>
              <div class="duel-vs-divider">VS</div>
              <div class="duel-side is-rival">
                <div class="duel-player-header">
                  <span class="duel-num rival">10</span>
                  <div>
                    <strong class="duel-player-name">Bruno Veglio</strong>
                    <div class="duel-player-role">Eje y Gestor de Wanderers</div>
                  </div>
                </div>
                <p class="duel-player-desc">Buen pie, distribución rápida y manejo de los ritmos del partido.</p>
              </div>
            </div>
            <div class="duel-verdict">
              <strong>Clave del Duelo:</strong> Si Leo Fernández tiene libertad para girar, romperá la zaga bohemia con asistencias milimétricas a las espaldas de los laterales.
            </div>
          </div>

          <div class="duel-item">
            <div class="duel-title-bar">
              <span class="duel-zone">Área de Wanderers</span>
              <span class="duel-headline">La Fiera del Gol vs. La Zaga Bohemia</span>
            </div>
            <div class="duel-sides-wrap">
              <div class="duel-side is-penarol">
                <div class="duel-player-header">
                  <span class="duel-num">11</span>
                  <div>
                    <strong class="duel-player-name">Maximiliano Silvera</strong>
                    <div class="duel-player-role">Centrodelantero de Presión</div>
                  </div>
                </div>
                <p class="duel-player-desc">Presión asfixiante sobre la salida rival, diagonales y olfato goleador.</p>
              </div>
              <div class="duel-vs-divider">VS</div>
              <div class="duel-side is-rival">
                <div class="duel-player-header">
                  <span class="duel-num rival">2/3</span>
                  <div>
                    <strong class="duel-player-name">Emiliano García &amp; Zaga Central</strong>
                    <div class="duel-player-role">Defensa Central de Wanderers</div>
                  </div>
                </div>
                <p class="duel-player-desc">Oficio, anticipo terrestre y cobertura de espacios reducidos.</p>
              </div>
            </div>
            <div class="duel-verdict">
              <strong>Clave del Duelo:</strong> Silvera forzará el error bohemio presionando la salida corta ordenada por Pacheco, abriendo caminos para Cabrera y Báez.
            </div>
          </div>
        </div>
      </div>

      <!-- HISTORIAL OFICIAL FRENTE A FRENTE CONTRA WANDERERS (1891 BD) -->
      <div class="match-h2h-bar" id="match-h2h-box" aria-label="Historial Oficial Frente a Frente contra Wanderers" style="margin-top:20px;">
        <div class="match-h2h-header">
          <div class="match-h2h-title">
            <span>📜 Historial Oficial Verificado: Peñarol vs Montevideo Wanderers</span>
          </div>
          <span class="match-h2h-source">Fuente Oficial: <strong>1891 BD</strong> (Comisión de Historia y Patrimonio)</span>
        </div>

        <div class="match-h2h-stats">
          <div class="match-h2h-stat">
            <div class="match-h2h-stat-num" id="h2h-pj">204</div>
            <div class="match-h2h-stat-lbl">Partidos Jugados</div>
          </div>
          <div class="match-h2h-stat">
            <div class="match-h2h-stat-num gold" id="h2h-pg">132</div>
            <div class="match-h2h-stat-lbl">Ganados Peñarol</div>
          </div>
          <div class="match-h2h-stat">
            <div class="match-h2h-stat-num" id="h2h-pe">48</div>
            <div class="match-h2h-stat-lbl">Empates</div>
          </div>
          <div class="match-h2h-stat">
            <div class="match-h2h-stat-num" id="h2h-pp">24</div>
            <div class="match-h2h-stat-lbl">Derrotas</div>
          </div>
          <div class="match-h2h-stat">
            <div class="match-h2h-stat-num gold" id="h2h-gf">412 - 188</div>
            <div class="match-h2h-stat-lbl">Goles (Dif: +224)</div>
          </div>
          <div class="match-h2h-stat">
            <div class="match-h2h-stat-num gold" id="h2h-eff">73.2%</div>
            <div class="match-h2h-stat-lbl">Efectividad Aurinegra</div>
          </div>
        </div>

        <div class="match-h2h-recent">
          <span class="match-h2h-pill">★ +108 victorias a favor del Decano</span>
          <span><strong>Supremacía histórica aurinegra:</strong> Peñarol lidera el historial con más de un siglo de ventaja sobre el conjunto del Prado en todas las competencias oficiales.</span>
          <a href="https://www.servicioti.com.uy/p/penarol-proximo-partido-radiografia.html" target="_blank" rel="noopener noreferrer" class="dynamic-blogger-link" style="color:var(--manya-gold);text-decoration:underline;margin-left:auto;font-size:11.5px;font-weight:700;">Ver Radiografía Completa en ServicioTI ↗</a>
        </div>
      </div>"""

    # Nuevo Cajón Colapsable del Partido Anterior (PASADO EN CAJÓN DE 1-CLICK)
    nuevo_cajon_historico = f"""      <!-- ============================================================== -->
      <!-- PASADO: CAJÓN HISTÓRICO COLAPSABLE DEL PARTIDO ANTERIOR (JUVENTUD) -->
      <!-- ============================================================== -->
      <div class="historico-drawer-container" id="historico-partido-anterior" style="margin:24px 0;">
        <button type="button" class="historico-drawer-toggle" id="btn-toggle-historico" aria-expanded="false" aria-controls="historico-drawer-content" style="width:100%;background:linear-gradient(135deg,#18181d 0%,#09090b 100%);border:2px solid rgba(255,209,0,0.5);border-radius:12px;padding:14px 20px;cursor:pointer;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;transition:all 0.25s ease;text-align:left;">
          <div style="display:flex;align-items:center;gap:12px;flex-wrap:wrap;">
            <span style="background:#27272a;color:#ffd100;font-size:11px;font-weight:900;padding:4px 10px;border-radius:999px;border:1px solid rgba(255,209,0,0.4);letter-spacing:0.04em;">
              ★ ÚLTIMO RESULTADO OFICIAL • HISTÓRICO
            </span>
            <span style="color:#ffffff;font-weight:900;font-size:15px;">
              Juventud 0 - 0 Peñarol • Torneo Clausura (Fecha 11)
            </span>
          </div>
          <div style="display:flex;align-items:center;gap:10px;">
            <span id="historico-toggle-label" style="font-size:13px;color:var(--manya-gold);font-weight:800;">
              📂 Ver Minuto a Minuto, Estadísticas y Mapa Táctico
            </span>
            <span id="historico-toggle-icon" style="font-size:14px;color:var(--manya-gold);transition:transform 0.3s ease;">
              ▼
            </span>
          </div>
        </button>

        <!-- CONTENIDO DEL PARTIDO ANTERIOR (OCULTO POR DEFECTO PARA NO SATURAR) -->
        <div id="historico-drawer-content" style="display:none;margin-top:14px;animation:fadeIn 0.3s ease;">
          <div style="background:rgba(255,209,0,0.06);border:1px solid rgba(255,209,0,0.3);border-radius:10px;padding:12px 18px;margin-bottom:14px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px;">
            <span style="font-size:13px;color:#e4e4e7;">
              Este encuentro concluyó 0-0. Peñarol sumó un punto y se mantiene como <strong>líder solitario de la Tabla Anual con 64 unidades</strong>.
            </span>
            <a href="https://www.servicioti.com.uy/2026/10/penarol-en-vivo-juventud-vs-penarol.html" target="_blank" rel="noopener noreferrer" class="btn-manya" style="font-size:12px;padding:6px 14px;text-decoration:none;">
              📖 Ver Crónica de Fondo Sellada en Blogger ↗
            </a>
          </div>

          <!-- Componente Completo del Partido Anterior -->
          {live_card_block}
        </div>
      </div>"""

    # Reemplazar dentro de #match-center:
    # Retirar la antigua ubicación del live card y del scouting
    # E insertar en orden: Scout Wanderers + Cajón Histórico Juventud
    if live_card_block and scout_block:
        # En el texto original, live_card_block estaba arriba y scout_block abajo
        # Vamos a reemplazar live_card_block por el nuevo scout + cajón histórico
        # Y eliminar scout_block de la parte inferior para que no quede duplicado!
        
        index_content = index_content.replace(scout_block, "")
        index_content = index_content.replace(live_card_block, nuevo_scout_wanderers + "\n\n" + nuevo_cajon_historico)
        print("[OK] Match Center reestructurado: Futuro (Wanderers) en primera plana, Pasado (Juventud) en cajón colapsable.")
    else:
        print("[!] No se pudieron extraer con exactitud los bloques de live_card y scout.")

    # 3. Actualizar Portada Visual
    old_portada_head = "⚡ ¡EN VIVO! Juventud vs Peñarol en el Estadio Centenario • Torneo Clausura 2026"
    new_portada_head = "⚡ PRÓXIMO PARTIDO: Peñarol vs Montevideo Wanderers • Torneo Clausura 2026 (Fecha 12)"
    if old_portada_head in index_content:
        index_content = index_content.replace(old_portada_head, new_portada_head)

    old_portada_caption = """          <p id="hero-post-text" class="ig-post-text">
            <strong>🔜 ¡PRÓXIMO PARTIDO CONFIRMADO!</strong><br>
            🆚 <strong>Juventud</strong><br>
            🏟️ <strong>Estadio Centenario</strong><br>
            🏆 <strong>Torneo Clausura 2026</strong><br>
            🗓️ <strong>Viernes 23 de octubre</strong><br>
            🕗 <strong>20:00 horas</strong><br><br>
            El club pedrense fijó el mítico <strong>Estadio Centenario</strong> para recibir a Peñarol. Venta y canje de entradas habilitados para toda la parcialidad carbonera en TickAntel y locales Redpagos (Tribunas Ámsterdam, Olímpica y América).
          </p>"""

    new_portada_caption = """          <p id="hero-post-text" class="ig-post-text">
            <strong>🔜 ¡PRÓXIMO PARTIDO CONFIRMADO!</strong><br>
            🆚 <strong>Montevideo Wanderers</strong><br>
            🏟️ <strong>Estadio Saroldi / Parque Alfredo Víctor Viera (Prado)</strong><br>
            🏆 <strong>Torneo Clausura 2026 • Fecha 12</strong><br>
            🗓️ <strong>Sábado 31 de octubre</strong><br>
            🕟 <strong>16:30 horas</strong><br><br>
            El Decano visita el Prado para enfrentar al conjunto bohemio dirigido tácticamente por Antonio Pacheco. Duelo trascendental por la Tabla Anual. Venta y canje de entradas habilitados vía TickAntel para toda la parcialidad aurinegra.
          </p>"""

    if old_portada_caption in index_content:
        index_content = index_content.replace(old_portada_caption, new_portada_caption)
        print("[OK] Portada visual actualizada para Wanderers.")

    # 4. Actualizar Pizarra Táctica
    old_pizarra_header = """          <h2 class="section-title">👕 Pizarra Táctica: <span>Armá tu 11 Titular</span></h2>
          <p class="section-sub">Elige el sistema táctico, haz clic en un jugador de la cancha y luego en un suplente para hacer cambios, y descarga tu 11 en PNG</p>"""

    new_pizarra_header = """          <h2 class="section-title">👕 Pizarra Táctica: <span>Armá tu 11 vs Montevideo Wanderers</span></h2>
          <p class="section-sub">Armá tu alineación ideal para visitar el Prado en la Fecha 12 del Torneo Clausura (Sábado 31/10 16:30 hs)</p>"""

    if old_pizarra_header in index_content:
        index_content = index_content.replace(old_pizarra_header, new_pizarra_header)
        print("[OK] Pizarra táctica enfocada en Wanderers.")

    # Guardar index.html
    INDEX_HTML.write_text(index_content, encoding="utf-8")
    print("[OK] index.html guardado exitosamente.")

    # 5. Actualizar app.js con initHistoricoDrawer()
    drawer_js = """
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
"""

    if "function initHistoricoDrawer()" not in app_content:
        # Insertar antes de DOMContentLoaded listener o al final de funciones
        insert_marker = "  function renderRivalIntelligence(rival) {"
        if insert_marker in app_content:
            app_content = app_content.replace(insert_marker, drawer_js + "\n" + insert_marker)
        
        # Invocar en initApp()
        init_marker = "initStandingsTabs();"
        if init_marker in app_content and "initHistoricoDrawer();" not in app_content:
            app_content = app_content.replace(init_marker, "initHistoricoDrawer();\n    " + init_marker)

        APP_JS.write_text(app_content, encoding="utf-8")
        print("[OK] app.js actualizado con initHistoricoDrawer().")

if __name__ == "__main__":
    reestructurar()
