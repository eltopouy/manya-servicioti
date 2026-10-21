# -*- coding: utf-8 -*-
"""
Publica la Previa y Radiografía Táctica Oficial de Juventud vs Peñarol en Blogger (www.servicioti.com.uy)
y vincula la URL resultante en news_digest.json, index.html y live_status.json.
"""

import sys
import json
from pathlib import Path

if sys.stdout.encoding != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

# Cargar y actualizar news_digest.json con la previa y análisis actualizados
digest_file = DATA_DIR / "news_digest.json"
digest = json.loads(digest_file.read_text(encoding="utf-8"))

digest["titular_dia"] = "Previa Oficial: Peñarol ante Juventud en el Estadio Centenario para blindar la Tabla Anual"
digest["bajada_seo"] = "Radiografía táctica completa de Juventud vs Peñarol (Torneo Clausura 2026): duelos 1x1, el laboratorio de Diego Aguirre, historial 1891 BD y la venta de entradas en el Centenario."

digest["articulo_principal"] = {
    "titulo": "Radiografía Táctica: El laboratorio de Diego Aguirre y los duelos 1x1 para visitar a Juventud en el Centenario",
    "subtitulo": "Análisis exhaustivo del rival, el despliegue pedrense y las llaves tácticas del puntero de la Tabla Anual",
    "parrafos": [
        "El desenlace del Torneo Clausura 2026 ingresa en su fase culminante. El Club Atlético Peñarol asume la undécima fecha ante el Club Atlético Juventud de Las Piedras este viernes 23 de octubre a las 20:00 horas en el mítico Estadio Centenario, escenario fijado por el conjunto pedrense para albergar la multitudinaria parcialidad aurinegra. Con 63 unidades acumuladas, el Decano lidera la Tabla Anual y afronta este compromiso con la determinación de custodiar la ventaja deportiva que conduce al Campeonato Uruguayo 54.",
        "El informe de inteligencia deportiva revela que Juventud, bajo la conducción técnica de Christian 'Kily' González, estructura su propuesta en un bloque medio-bajo compacto (4-4-2 / 5-3-2), achicando espacios entre líneas para forzar errores en la circulación rival. Su principal peligro radica en las transiciones veloces y la pelota quieta ofensiva, donde el lateral zurdo Renzo Rabino exhibe una pegada envenenada y el delantero Fernando Mimbacas (quien ya convirtió en el 2-2 disputado en el Campeón del Siglo) aprovecha cualquier balón suelto en el área.",
        "En el laboratorio de Los Aromos, Diego 'La Fiera' Aguirre ha diagramado duelos tácticos 1x1 fundamentales. En la zona 14, la gravitación de Leonardo Fernández frente al pivote Agustín Rodríguez será el termómetro del partido: si el 'Zurdo de Oro' logra recibir perfilado y con dos metros de luz, destrabará el juego con pases filtrados milimétricos o remates de media distancia. Por las bandas, la explosión de Jaime Báez y Javier Cabrera buscará explotar los espacios a espaldas de los carrileros pedrenses, mientras que Maximiliano Silvera liderará la presión en la salida para desarticular la zaga rival.",
        "La historia y la mística respaldan al Carbonero: según la certificación oficial de la Comisión de Historia y Patrimonio (1891 BD), Peñarol domina el historial ante Juventud con 23 victorias en 33 partidos disputados, 67 goles a favor y una efectividad del 76.7%. Con las tribunas Ámsterdam, Olímpica y América colmadas por miles de hinchas aurinegros, Peñarol saldrá al Centenario a imponer su jerarquía y rubricar tres puntos de oro."
    ],
    "preguntas_frecuentes": [
        {
            "q": "¿Cuándo y a qué hora juegan Juventud vs Peñarol?",
            "a": "El partido se disputa este viernes 23 de octubre de 2026 a las 20:00 horas en el Estadio Centenario de Montevideo."
        },
        {
            "q": "¿Cómo y dónde comprar entradas para hinchas de Peñarol?",
            "a": "Las entradas están disponibles a través de TickAntel y en todos los locales Redpagos del país para las tribunas Ámsterdam, Olímpica y América."
        },
        {
            "q": "¿Cómo está el historial oficial entre Peñarol y Juventud según 1891 BD?",
            "a": "Se han enfrentado en 33 ocasiones con 23 triunfos de Peñarol, 7 empates y solo 3 caídas, con 67 goles a favor del Decano (+20 partidos de ventaja)."
        }
    ]
}

digest_file.write_text(json.dumps(digest, ensure_ascii=False, indent=2), encoding="utf-8")
print("✓ data/news_digest.json actualizado con la previa de Juventud vs Peñarol.")

# Ahora invocar el publicador de Blogger
from blogger_manya_publisher import publish_manya_article_to_blogger

post_url = publish_manya_article_to_blogger(post_type="PREVIA", match_id="401930317")
print("RESULTADO DE PUBLICACIÓN BLOGGER:")
print("URL del Post:", post_url)
