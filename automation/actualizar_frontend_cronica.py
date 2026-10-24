# -*- coding: utf-8 -*-
"""
ACTUALIZACIÓN EDITORIAL DEL FRONTEND (INDEX.HTML Y APP.JS)
==========================================================
Reemplaza la antigua caja de 6 medios tradicionales por los 4 Prismas del Fútbol Uruguayo
con narrativa literaria, audacia táctica y cero menciones de marcas externas.
"""

from pathlib import Path
import json

BASE_DIR = Path(__file__).resolve().parent.parent
INDEX_HTML = BASE_DIR / "index.html"
APP_JS = BASE_DIR / "js" / "app.js"
DIGEST_FILE = BASE_DIR / "data" / "news_digest.json"

def actualizar_app_js():
    content = APP_JS.read_text(encoding="utf-8").replace("\r\n", "\n")

    old_block = """    if (art.parrafos && art.parrafos.length >= 3) {
      if (p1El) p1El.innerHTML = art.parrafos[0];
      if (p2El) p2El.innerHTML = art.parrafos[1];
      if (p3El) p3El.innerHTML = art.parrafos[2];
    }"""

    new_block = """    if (art.parrafos && art.parrafos.length >= 3) {
      if (p1El) p1El.innerHTML = art.parrafos[0];
      if (p2El) p2El.innerHTML = art.parrafos[1];
      if (p3El) p3El.innerHTML = art.parrafos[2];
    }

    const pullquoteEl = document.querySelector('.editorial-pullquote');
    if (pullquoteEl && art.cita_destacada) {
      pullquoteEl.innerHTML = `“${art.cita_destacada}” ${art.autor_cita ? `<span style="display:block;font-size:12px;margin-top:6px;color:var(--manya-gold);">— ${art.autor_cita}</span>` : ''}`;
    }"""

    old_prensa = """    const prensaGrid = document.getElementById('prensa-nacional-grid');
    if (prensaGrid && digest.periodistas_prensa) {
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
    }"""

    new_prensa = """    const prensaGrid = document.getElementById('prensa-nacional-grid');
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
    }"""

    if old_block in content:
        content = content.replace(old_block, new_block)

    if old_prensa in content:
        content = content.replace(old_prensa, new_prensa)
        print("[OK] app.js prensaGrid updated to support prismas_analisis")

    APP_JS.write_text(content, encoding="utf-8")
    print("[OK] app.js saved.")


def actualizar_index_html():
    content = INDEX_HTML.read_text(encoding="utf-8").replace("\r\n", "\n")
    digest = json.loads(DIGEST_FILE.read_text(encoding="utf-8"))

    art = digest.get("articulo_principal", {})
    parrafos = art.get("parrafos", [])
    p1 = parrafos[0] if len(parrafos) > 0 else ""
    p2 = parrafos[1] if len(parrafos) > 1 else ""
    p3 = parrafos[2] if len(parrafos) > 2 else ""
    titular = art.get("titulo") or digest.get("titular_dia", "")
    cita = art.get("cita_destacada", "")
    autor = art.get("autor_cita", "Diego Aguirre / Balance Editorial")

    # Actualizar párrafos y pullquote
    old_article_body = """            <p class="editorial-paragraph drop-cap" id="editorial-p1">
              Bajo la histórica Torre de los Homenajes del <strong>Estadio Centenario</strong> y ante el aliento de más de 30.000 hinchas aurinegros, el <strong>Club Atlético Peñarol</strong> igualó 0-0 frente a un ordenado <strong>Juventud de Las Piedras</strong> por la 11ª fecha del Torneo Clausura. Como destacaron <em>Rodrigo Romano</em> en <strong>Telemundo (Canal 12)</strong> y la crónica de <em>Ovación (El País)</em>, el equipo de <strong>Diego Aguirre</strong> asumió la iniciativa desde el pitazo inicial con un monólogo territorial y más del 68% de tenencia del balón, pero se estrelló contra una muralla pedrense que resistió con bravura en su tercio defensivo.
            </p>
            <p class="editorial-paragraph" id="editorial-p2">
              En el pizarrón táctico analizado por <em>Juan Carlos Scelza</em> y <em>Martín Charquero</em> en <strong>Tenfield</strong>, junto al informe de <em>Referí (El Observador)</em>, el <code>4-2-3-1</code> carbonero extrañó la aceleración repentina en los metros decisivos. Juventud se replegó con un <code>4-4-2</code> ultracompacto en apenas 25 metros, duplicando marcas sobre <strong>Leonardo Fernández</strong> y aislando a <strong>Maximiliano Silvera</strong> entre los zagueros. Aunque <strong>Guzmán Rodríguez</strong> y <strong>Damián García</strong> brindaron absoluta solidez en los anticipos para neutralizar las contras de Gastón Pereiro, la posesión careció de desborde limpio por las bandas.
            </p>

            <blockquote class="editorial-pullquote">
              “El empate nos deja con bronca porque vinimos a buscar los tres puntos, pero la entrega del equipo fue total. Seguimos en la punta de la Tabla Anual y el objetivo final sigue dependiendo exclusivamente de nosotros.” — Diego Aguirre en conferencia de prensa
            </blockquote>

            <p class="editorial-paragraph" id="editorial-p3">
              En zona mixta, a través de <strong>Montevideo Portal (FútbolUy)</strong> y las cámaras de <strong>Telenoche (Canal 4)</strong> con <em>Eduardo Rivas</em> y <em>Federico Buysan</em>, se ratificó el balance: Peñarol sostiene el liderazgo absoluto de la Tabla Anual con 64 puntos y da vuelta la página de inmediato en Los Aromos para preparar la trascendental 12ª fecha frente a <strong>Montevideo Wanderers</strong>.
            </p>"""

    new_article_body = f"""            <p class="editorial-paragraph drop-cap" id="editorial-p1">
              {p1}
            </p>
            <p class="editorial-paragraph" id="editorial-p2">
              {p2}
            </p>

            <blockquote class="editorial-pullquote">
              “{cita}” <span style="display:block;font-size:12px;margin-top:6px;color:var(--manya-gold);">— {autor}</span>
            </blockquote>

            <p class="editorial-paragraph" id="editorial-p3">
              {p3}
            </p>"""

    if old_article_body in content:
        content = content.replace(old_article_body, new_article_body)
        print("[OK] index.html article paragraphs and pullquote updated.")

    # Actualizar titular si coincide el anterior
    old_head = "El cerrojo que frenó al Decano: Crónica, pizarrón táctico y el debate nacional tras el 0-0 ante Juventud"
    if old_head in content:
        content = content.replace(old_head, titular)
        print("[OK] index.html headline updated.")

    # Actualizar 4 claves estáticas del sidebar
    claves = digest.get("claves_60_segundos", [])
    if claves and len(claves) >= 4:
        old_keys_block = """          <div class="claves-editorial-list" id="claves-editorial-container">
            <div class="clave-item">
              <div class="clave-item-title">⚽ Laboratorio en Los Aromos</div>
              <p class="clave-item-desc">Diego Aguirre ajusta la presión alta y la pelota quieta con Leo Fernández como eje conductor pensando en sumar de a tres.</p>
            </div>
            <div class="clave-item">
              <div class="clave-item-title">📊 Fortaleza en la Tabla Anual</div>
              <p class="clave-item-desc">El Carbonero sostiene un rendimiento superlativo como local en el Campeón del Siglo, liderando las métricas de goles a favor y valla menos vencida.</p>
            </div>
            <div class="clave-item">
              <div class="clave-item-title">🎟️ Operativo Campeón del Siglo</div>
              <p class="clave-item-desc">Canje y venta de entradas habilitados vía TickAntel y TuApp para las tribunas Cataldi, Damiani, Güelfi y Henderson.</p>
            </div>
            <div class="clave-item">
              <div class="clave-item-title">🔥 ADN Copero y Juveniles</div>
              <p class="clave-item-desc">La combinación de referentes de jerarquía y talento formado en las juveniles aurinegras mantiene al plantel competitivo en todos los frentes.</p>
            </div>
          </div>"""

        new_items = []
        for c in claves:
            icon = c.get("icono", "⚡")
            title = c.get("titulo", "")
            desc = c.get("detalle", "")
            new_items.append(f"""            <div class="clave-item">
              <div class="clave-item-title">{icon} {title}</div>
              <p class="clave-item-desc">{desc}</p>
            </div>""")

        new_keys_block = '          <div class="claves-editorial-list" id="claves-editorial-container">\n' + '\n'.join(new_items) + '\n          </div>'
        if old_keys_block in content:
            content = content.replace(old_keys_block, new_keys_block)
            print("[OK] index.html 4 static keys updated.")

    INDEX_HTML.write_text(content, encoding="utf-8")
    print("[OK] index.html saved.")


if __name__ == "__main__":
    actualizar_app_js()
    actualizar_index_html()
