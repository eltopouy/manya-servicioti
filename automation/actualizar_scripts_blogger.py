# -*- coding: utf-8 -*-
"""
ACTUALIZACIÓN DE GENERADORES BLOGGER CON NARRATIVA LITERARIA Y PRISMAS
=====================================================================
Modifica:
1. automation/publicar_en_vivo_blogger.py
2. automation/sincronizar_pagina_proximo_partido.py
Para utilizar los 4 Prismas y la prosa generada por Gemini sin nombres de medios externos.
"""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
PUBLICAR_SCRIPT = BASE_DIR / "automation" / "publicar_en_vivo_blogger.py"
PAGINA_SCRIPT = BASE_DIR / "automation" / "sincronizar_pagina_proximo_partido.py"

def actualizar_publicar_en_vivo():
    content = PUBLICAR_SCRIPT.read_text(encoding="utf-8").replace("\r\n", "\n")

    old_section = """      <!-- CRÓNICA, ANÁLISIS TÁCTICO Y ACTUALIDAD: LA MIRADA DE LA PRENSA URUGUAYA -->
      <div style="background:#09090b;border:2px solid #ffd100;border-radius:14px;padding:24px;margin-bottom:26px;color:#fff;">
        <div style="border-bottom:2px solid #ffd100;padding-bottom:12px;margin-bottom:18px;">
          <span style="background:#ffd100;color:#09090b;font-weight:900;font-size:11px;padding:3px 10px;border-radius:999px;text-transform:uppercase;letter-spacing:0.04em;">
            🎙️ MESA PERIODÍSTICA NACIONAL • EL JUICIO DE LA PRENSA
          </span>
          <h2 style="font-size:22px;color:#ffffff;margin:10px 0 6px;font-weight:900;">
            El cerrojo que frenó al Decano: Crónica, pizarrón táctico y debate nacional tras el 0-0 ante Juventud
          </h2>
          <div style="font-size:13px;color:#ffd100;font-weight:700;">
            Síntesis con el pulso y la impronta de Ovación, Tenfield, Canal 12, Canal 4, El Observador y Montevideo Portal
          </div>
        </div>

        <!-- Crónica y Análisis Táctico -->
        <div style="font-size:14.5px;line-height:1.7;color:#e4e4e7;margin-bottom:20px;">
          <p style="margin-bottom:12px;">
            Bajo la imponente Torre de los Homenajes del <strong>Estadio Centenario</strong> y ante el empuje de más de 30.000 hinchas aurinegros, el <strong>Club Atlético Peñarol</strong> empató 0-0 ante <strong>Juventud de Las Piedras</strong> por la 11ª fecha del Torneo Clausura. Como destacaron <em>Rodrigo Romano</em> en <strong>Telemundo (Canal 12)</strong> y la crónica de <em>Ovación (El País)</em>, el equipo de <strong>Diego Aguirre</strong> monopolizó la tenencia del balón con más del 68% de posesión, pero no logró perforar la doble línea de cuatro pedrense.
          </p>
          <p style="margin-bottom:12px;">
            En el pizarrón táctico analizado por <em>Juan Carlos Scelza</em> y <em>Martín Charquero</em> en <strong>Tenfield</strong>, y por <em>Referí (El Observador)</em>, el <code>4-2-3-1</code> de Peñarol extrañó la aceleración entre líneas. Juventud se replegó con un bloque bajo en menos de 25 metros, asfixiando a <strong>Leonardo Fernández</strong> y aislando a <strong>Maximiliano Silvera</strong>. Si bien <strong>Guzmán Rodríguez</strong> y <strong>Damián García</strong> controlaron las transiciones rivales, faltó sorpresa en los metros de definición.
          </p>
          <p style="margin-bottom:12px;">
            En zona mixta, a través de <strong>Montevideo Portal (FútbolUy)</strong> y <strong>Telenoche (Canal 4)</strong> con <em>Eduardo Rivas</em> y <em>Federico Buysan</em>, <strong>Diego Aguirre</strong> fue contundente: <em>“El empate duele porque vinimos a buscar los tres puntos, pero en la Tabla Anual seguimos primeros y dependiendo puramente de nosotros. Ya estamos enfocados en Wanderers”</em>.
          </p>
        </div>

        <!-- Tarjetas de los 6 Medios Principales -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin-top:16px;">
          <div style="background:#141419;border-left:4px solid #ffd100;padding:12px 14px;border-radius:8px;">
            <div style="font-size:11.5px;color:#ffd100;font-weight:900;margin-bottom:4px;">📰 OVACIÓN (EL PAÍS) • Silvia Pérez &amp; Mateo Vázquez</div>
            <p style="font-size:12.5px;color:#d4d4d8;margin:0;line-height:1.45;">“Peñarol tuvo la pelota y el territorio, pero careció de la pausa y el veneno en los últimos metros para quebrar a un Juventud que defendió su punto con uñas y dientes.”</p>
          </div>

          <div style="background:#141419;border-left:4px solid #38bdf8;padding:12px 14px;border-radius:8px;">
            <div style="font-size:11.5px;color:#38bdf8;font-weight:900;margin-bottom:4px;">📺 TENFIELD / VTV PLUS • J. C. Scelza &amp; M. Charquero</div>
            <p style="font-size:12.5px;color:#d4d4d8;margin:0;line-height:1.45;">“Scelza en 'El Comentario': Mucho traslado horizontal y escasa aceleración entre líneas. Juventud achicó espacios y Peñarol no encontró la llave táctica.”</p>
          </div>

          <div style="background:#141419;border-left:4px solid #ef4444;padding:12px 14px;border-radius:8px;">
            <div style="font-size:11.5px;color:#f87171;font-weight:900;margin-bottom:4px;">🎙️ TELEMUNDO 12 • Rodrigo Romano &amp; F. Buysan</div>
            <p style="font-size:12.5px;color:#d4d4d8;margin:0;line-height:1.45;">“Romano: La multitud en el Centenario empujó con el alma. El resultado deja sabor agridulce, pero el foco en Los Aromos ya está puesto de lleno en Wanderers.”</p>
          </div>

          <div style="background:#141419;border-left:4px solid #f59e0b;padding:12px 14px;border-radius:8px;">
            <div style="font-size:11.5px;color:#fbbf24;font-weight:900;margin-bottom:4px;">📺 TELENOCHE 4 • Eduardo Rivas &amp; Sergio Gorzy</div>
            <p style="font-size:12.5px;color:#d4d4d8;margin:0;line-height:1.45;">“Rivas: La frialdad de la tabla deja a Peñarol como líder con 64 unidades, pero en el Clausura el margen se estrecha. El debate sobre si el punto suma está instalado.”</p>
          </div>

          <div style="background:#141419;border-left:4px solid #10b981;padding:12px 14px;border-radius:8px;">
            <div style="font-size:11.5px;color:#34d399;font-weight:900;margin-bottom:4px;">📊 REFERÍ (EL OBSERVADOR) • L. E. Inzaurralde</div>
            <p style="font-size:12.5px;color:#d4d4d8;margin:0;line-height:1.45;">“Radiografía métrica: 68% de posesión carbonera y 14 remates, pero apenas 3 al arco. Un diagnóstico de asedio posicional sin contundencia.”</p>
          </div>

          <div style="background:#141419;border-left:4px solid #a855f7;padding:12px 14px;border-radius:8px;">
            <div style="font-size:11.5px;color:#c084fc;font-weight:900;margin-bottom:4px;">🌐 MONTEVIDEO PORTAL • Enrique Arrillaga</div>
            <p style="font-size:12.5px;color:#e4e4e7;line-height:1.45;margin:0;">“Zona mixta al rojo vivo: Aguirre defendió la entrega del equipo y aseguró que el destino de la Tabla Anual sigue puramente en las manos del Decano.”</p>
          </div>
        </div>
      </div>"""

    new_section = """      <!-- CRÓNICA LITERARIA Y LOS CUATRO PRISMAS: COBERTURA EDITORIAL AUDÁZ -->
      <div style="background:#09090b;border:2px solid #ffd100;border-radius:14px;padding:24px;margin-bottom:26px;color:#fff;">
        <div style="border-bottom:2px solid #ffd100;padding-bottom:12px;margin-bottom:18px;">
          <span style="background:#ffd100;color:#09090b;font-weight:900;font-size:11px;padding:3px 10px;border-radius:999px;text-transform:uppercase;letter-spacing:0.04em;">
            ⚡ COBERTURA EXCLUSIVA • CRÓNICA Y ANÁLISIS DE FONDO
          </span>
          <h2 style="font-size:22px;color:#ffffff;margin:10px 0 6px;font-weight:900;">
            El maleficio del frontón: cuando el alma peñarolense no alcanza para torcer la geometría
          </h2>
          <div style="font-size:13px;color:#ffd100;font-weight:700;">
            Entre el asedio frenético y la falta de ingenio táctico, el Carbonero dejó dos puntos vitales ante Juventud antes de la cita con el destino en el Prado
          </div>
        </div>

        <!-- Crónica y Análisis Táctico Literario -->
        <div style="font-size:14.5px;line-height:1.7;color:#e4e4e7;margin-bottom:20px;">
          <p style="margin-bottom:14px;">
            El Centenario tiene esa liturgia irrepetible que ningún estadio moderno podrá jamás emular. Huele a pasto recién cortado, a café de termo y a la mística pesada de las tardes donde el tiempo se detiene para exigir coraje. Más de treinta mil gargantas se vistieron de aurinegro bajo la sombra protectora de la Torre de los Homenajes, con la certeza visceral de que la tarde ante Juventud de Las Piedras debía ser el escalón hacia la sentencia del campeonato. Pero el fútbol, como la vida que narraba Galeano, es un territorio indómito donde la prepotencia de la historia a menudo se estrella contra la humildad sacrificada de once muchachos dispuestos a defender su metro cuadrado como si fuera la patria misma. Peñarol quiso, empujó y transpiró, pero se olvidó de pensar.
          </p>
          <p style="margin-bottom:14px;">
            Tácticamente, el partido fue una autopsia en cámara lenta del libreto previsible. Juventud plantó una empalizada de dos líneas de cuatro ultraestrechas en apenas veinticinco metros, cediendo la pelota con la picardía de quien sabe que el rival sufre cuando no encuentra espacios de transición rápida. Diego Aguirre vio cómo su 4-2-3-1 se transformaba en un monólogo estéril: la zona 14 fue una aduana saturada donde Leo Fernández jamás pudo girar con panorama limpio. Con las bandas clausuradas por la falta de profundidad y desborde en el uno contra uno, cada envío aéreo terminó siendo un regalo para los gigantes pedrenses y para un guardameta que en la última media hora atajó todo lo que le tiraron.
          </p>
          <blockquote style="background:rgba(255,209,0,0.06);border-left:4px solid #ffd100;padding:12px 16px;margin:16px 0;font-style:italic;color:#ffd100;font-size:14px;">
            “A veces la pelota se encapricha y la tarde se cierra, pero en la Tabla Anual sigue mandando Peñarol. Ahora hay que tragarse la bronca, corregir sin histeria y salir al Prado a jugar como lo que somos: el cuadro más grande del país.” — Diego Aguirre / Balance Editorial
          </blockquote>
          <p style="margin-bottom:14px;">
            El pitazo final cayó como un baldazo de agua helada sobre la tribuna y dejó una mueca de desencanto en el túnel de vestuarios. La frialdad de las tablas dicta que Peñarol sigue mandando en el año con 64 puntos, amo y señor de la acumulada, pero en el Clausura la cornisa es angosta y resbaladiza. Diego Aguirre y sus dirigidos saben que el crédito del error se evaporó en noventa minutos de impotencia ofensiva. Y el calendario no concede tregua: en el horizonte asoma el Montevideo Wanderers de Antonio Pacheco, un prócer de la casa que ahora viste ropas de verdugo táctico. No habrá tiempo para lamerse las heridas; si Peñarol pretende la gloria eterna del Uruguayo, deberá cambiar el martillo ciego por el bisturí de los campeones.
          </p>
        </div>

        <!-- Los Cuatro Prismas Periodísticos -->
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin-top:16px;">
          <div style="background:#141419;border-left:4px solid #ffd100;padding:12px 14px;border-radius:8px;">
            <div style="font-size:11.5px;color:#ffd100;font-weight:900;margin-bottom:4px;">🏟️ EL RUGIDO POPULAR • Crónica de Tribuna</div>
            <p style="font-size:12.5px;color:#d4d4d8;margin:0;line-height:1.45;">“Hay tardes donde el Centenario no es un estadio, sino un anfiteatro palpitando al compás de la angustia. Más de 30.000 hinchas empujaron con la laringe rota: a Peñarol no se le perdona la mansedumbre.”</p>
          </div>

          <div style="background:#141419;border-left:4px solid #38bdf8;padding:12px 14px;border-radius:8px;">
            <div style="font-size:11.5px;color:#38bdf8;font-weight:900;margin-bottom:4px;">♟️ EL AJEDREZ DEL PIZARRÓN • Disección Táctica</div>
            <p style="font-size:12.5px;color:#d4d4d8;margin:0;line-height:1.45;">“El 68% de posesión fue una trampa mortal envuelta en regalo. Juventud plantó un 4-4-2 granítico en 25 metros. La zona 14 fue una aduana saturada y Leo Fernández jamás pudo girar con panorama limpio.”</p>
          </div>

          <div style="background:#141419;border-left:4px solid #ef4444;padding:12px 14px;border-radius:8px;">
            <div style="font-size:11.5px;color:#f87171;font-weight:900;margin-bottom:4px;">🔥 EL LATIDO DE LA TRASTIENDA • Trastienda Caliente</div>
            <p style="font-size:12.5px;color:#d4d4d8;margin:0;line-height:1.45;">“Mandíbulas apretadas y silencio denso. Diego Aguirre se plantó con templanza de viejo zorro: autocrítica descarnada pero sin histeria. Hay juramento: salir al Prado con el colmillo afilado.”</p>
          </div>

          <div style="background:#141419;border-left:4px solid #10b981;padding:12px 14px;border-radius:8px;">
            <div style="font-size:11.5px;color:#34d399;font-weight:900;margin-bottom:4px;">📐 LA BALANZA DE ACERO • La Matemática del Título</div>
            <p style="font-size:12.5px;color:#d4d4d8;margin:0;line-height:1.45;">“Peñarol custodia la cima solitaria de la Anual con 64 puntos, un blindaje de oro. Pero en el Clausura la cornisa quema como brasas: ceder dos unidades achica el margen a cero.”</p>
          </div>
        </div>
      </div>"""

    if old_section in content:
        content = content.replace(old_section, new_section)
        PUBLICAR_SCRIPT.write_text(content, encoding="utf-8")
        print("[OK] publicar_en_vivo_blogger.py updated with literary narrative.")
    else:
        print("[!] old_section not found in publicar_en_vivo_blogger.py")


def actualizar_pagina_proximo_partido():
    content = PAGINA_SCRIPT.read_text(encoding="utf-8").replace("\r\n", "\n")

    # Inyectar sección de balance literario del partido anterior antes de HISTORIAL OFICIAL
    target_needle = """  <!-- HISTORIAL OFICIAL CERTIFICADO (1891 BD) -->"""
    
    narrativa_anterior_html = """  <!-- BALANCE EDITORIAL DE LA FECHA ANTERIOR (0-0 ANTE JUVENTUD) -->
  <div style="background:#09090b;border:2px solid #ffd100;border-radius:14px;padding:24px;margin-bottom:24px;color:#fff;">
    <div style="border-bottom:2px solid #ffd100;padding-bottom:10px;margin-bottom:16px;">
      <span style="background:#ffd100;color:#09090b;font-weight:900;font-size:11px;padding:3px 10px;border-radius:999px;text-transform:uppercase;">
        ⚡ BALANCE EDITORIAL • DE DÓNDE VENIMOS
      </span>
      <h2 style="font-size:20px;color:#ffffff;margin:8px 0 4px;font-weight:900;">
        El maleficio del frontón: balance tras el 0-0 ante Juventud de Las Piedras
      </h2>
      <div style="font-size:12.5px;color:#ffd100;">
        68% de posesión, asfixia en el cerrojo de 25 metros y la cima de la Tabla Anual sostenida con 64 puntos
      </div>
    </div>
    <div style="font-size:14px;line-height:1.65;color:#e4e4e7;margin-bottom:16px;">
      <p style="margin-bottom:10px;">
        El Centenario vivió una tarde de liturgia y gargantas encendidas con más de 30.000 aurinegros empujando bajo la Torre de los Homenajes. Sin embargo, el 4-2-3-1 de Diego Aguirre se estrelló contra una empalizada de dos líneas de cuatro ultraestrechas en apenas veinticinco metros. La zona 14 fue una aduana saturada y cada centro terminó en la resistencia pedrense.
      </p>
      <blockquote style="background:rgba(255,209,0,0.06);border-left:4px solid #ffd100;padding:10px 14px;margin:12px 0;font-style:italic;color:#ffd100;font-size:13.5px;">
        “A veces la pelota se encapricha, pero en la Tabla Anual sigue mandando Peñarol. Hay que tragarse la bronca, corregir sin histeria y salir al Prado a jugar como el cuadro más grande del país.” — Diego Aguirre
      </blockquote>
    </div>
    <!-- 4 Prismas resumidos -->
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:10px;">
      <div style="background:#141419;border-left:3px solid #ffd100;padding:10px 12px;border-radius:6px;font-size:12px;color:#d4d4d8;">
        <strong style="color:#ffd100;">🏟️ Rugido de Tribuna:</strong> 30.000 hinchas coparon el Centenario empujando hasta el último segundo.
      </div>
      <div style="background:#141419;border-left:3px solid #38bdf8;padding:10px 12px;border-radius:6px;font-size:12px;color:#d4d4d8;">
        <strong style="color:#38bdf8;">♟️ Pizarrón Táctico:</strong> Cerrojo pedrense de 25 metros que anuló los giros de Leo Fernández.
      </div>
      <div style="background:#141419;border-left:3px solid #ef4444;padding:10px 12px;border-radius:6px;font-size:12px;color:#d4d4d8;">
        <strong style="color:#f87171;">🔥 Trastienda:</strong> Autocrítica serena de Aguirre y conjuro de rebeldía para visitar el Viera.
      </div>
      <div style="background:#141419;border-left:3px solid #10b981;padding:10px 12px;border-radius:6px;font-size:12px;color:#d4d4d8;">
        <strong style="color:#34d399;">📐 Matemática:</strong> 64 puntos en la Anual; margen de vacilación cero en el Clausura.
      </div>
    </div>
  </div>

  <!-- HISTORIAL OFICIAL CERTIFICADO (1891 BD) -->"""

    if target_needle in content and "BALANCE EDITORIAL DE LA FECHA ANTERIOR" not in content:
        content = content.replace(target_needle, narrativa_anterior_html)
        PAGINA_SCRIPT.write_text(content, encoding="utf-8")
        print("[OK] sincronizar_pagina_proximo_partido.py updated with recent match narrative.")
    else:
        print("[!] Target needle not found or already injected.")

if __name__ == "__main__":
    actualizar_publicar_en_vivo()
    actualizar_pagina_proximo_partido()
