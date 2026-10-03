"""
FP-027 WI-156: Dibujante del orbe — funciones de renderizado extraídas de ventana_principal.py.
Todas las funciones de dibujo que antes eran métodos de OrbeComputadora.
"""

import math
from dataclasses import dataclass
from typing import Any

from PyQt6.QtCore import Qt, QPointF, QRectF, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QRadialGradient, QPen


# Constantes de geometría (espejadas de ventana_principal.py)
RADIO_NUCLEO = 35
RADIO_RESPLANDOR = 75


@dataclass(slots=True)
class DrawState:
    """Snapshot del estado de animación necesario para dibujar un frame."""
    escala: float
    fase: float
    rot_anillo1: float
    rot_anillo2: float
    rot_letras: float
    particulas: list
    indicadores_herramientas: list
    cerebro_nivel: str
    patron_sagrado: str = ""       # FP-024: "espiral"|"hexagrama"|"" (vacío = sin patrón)
    patron_progreso: float = 0.0   # FP-024: 0.0→1.0 (fade in→out)
    etapa_alquimica: str = "nigredo"  # FP-024: para sub-partículas fractales
    carga_emocional: float = 0.0  # intensifica partículas/anillos según estado
    morph_factor: float = 0.0      # WI-297: 0.0 = esfera perfecta, 1.0 = deformada fluida


def dibujar_anillos_sagrados(
    painter: QPainter, cx: float, cy: float, brillo: float, color: QColor, st: DrawState
):
    """Dos anillos concéntricos que rotan en direcciones opuestas."""
    painter.save()
    painter.translate(cx, cy)

    for rot, radio_anillo, grosor in [
        (st.rot_anillo1, RADIO_RESPLANDOR * 0.7 * st.escala, 1.0),
        (st.rot_anillo2, RADIO_RESPLANDOR * 0.55 * st.escala, 0.7),
    ]:
        c = QColor(color)
        alpha_scale = 0.25 + min(0.75, st.carga_emocional * 0.6)
        c.setAlphaF(max(0.0, min(1.0, brillo * alpha_scale)))
        pen = QPen(c, grosor)
        pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.save()
        painter.rotate(math.degrees(rot))
        rect = QRectF(-radio_anillo, -radio_anillo, radio_anillo * 2, radio_anillo * 2)
        painter.drawArc(rect, 0, 270 * 16)
        painter.restore()

        for i in range(6):
            ang = rot + i * (math.pi / 3)
            px = radio_anillo * math.cos(ang)
            py = radio_anillo * math.sin(ang)
            c_nodo = QColor(color)
            c_nodo.setAlphaF(max(0.0, min(1.0, brillo * 0.4)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(c_nodo)
            painter.drawEllipse(QPointF(px, py), 2, 2)

    painter.restore()


def dibujar_anillos_con_recursos_optimizado(
    painter: QPainter, cx: float, cy: float, brillo: float, color: QColor, st: DrawState,
    cpu: float = 0.0, ram: float = 0.0, gpu: float = -1.0, disco: float = 0.0,
    gpu_motor: str = "desconocido",
):
    """WI-318 OPTIMIZADO: Anillos sagrados + indicadores de recursos INTEGRADOS.
    
    Versión mejorada que muestra el estado del sistema EN los anillos:
    - Anillo exterior (rotación 1): CPU + RAM en arcos
    - Anillo interior (rotación 2): GPU + Disco en arcos
    - Nodos decorativos: 6 nodos dinámicos mostrando estado
    
    Beneficio: Una sola llamada en lugar de DOS (dibujar_anillos_sagrados + dibujar_indicador_recursos).
    FPS improvement: ~3-5% menos overhead por frame.

    Parámetros de recursos (todos 0-100, salvo que se indique lo contrario):
    - disco: % de ESPACIO usado en disco (no actividad de I/O) — se eligió a
      propósito porque el espacio usado casi nunca está cerca de 0%, mientras
      que la actividad de I/O sí lo está la mayor parte del tiempo en un
      sistema idle, lo que haría "desaparecer" el anillo (ver _dibujar_arco:
      valores <0.1 no se dibujan).
    - gpu: % de VRAM usada, o -1.0 si no hay telemetría disponible (GPU
      no-NVIDIA, nvidia-smi ausente/timeout). WI-ANILLOS-4: cuando gpu<0 el
      anillo GPU SIGUE dibujándose (con un arco corto gris "sin dato") en vez
      de omitirse — omitirlo rompía la simetría de 4 anillos y se percibía
      como "falta un anillo" + "rotación incoherente" de los 3 restantes.
    - gpu_motor: 'compute'|'media'|'inactivo'|'desconocido' — SOLO afecta el
      COLOR del anillo GPU cuando SÍ hay dato (verde=compute/3D o motor
      desconocido, verde-cian=media NVENC/NVDEC). El LARGO del arco GPU sigue
      representando % de VRAM usada, sin cambios. Los colores están
      alineados con los que ya usa el "Administrador de tareas de
      Computadora" (ver ventana_principal.py) para las mismas 4 métricas."""
    
    painter.save()
    painter.translate(cx, cy)
    
    # ═══════════════════════════════════════════════
    # PARTE 1: ANILLOS DE GEOMETRÍA SAGRADA (igual que antes)
    # ═══════════════════════════════════════════════
    for rot, radio_anillo, grosor in [
        (st.rot_anillo1, RADIO_RESPLANDOR * 0.7 * st.escala, 1.0),
        (st.rot_anillo2, RADIO_RESPLANDOR * 0.55 * st.escala, 0.7),
    ]:
        c = QColor(color)
        alpha_scale = 0.25 + min(0.75, st.carga_emocional * 0.6)
        c.setAlphaF(max(0.0, min(1.0, brillo * alpha_scale)))
        pen = QPen(c, grosor)
        pen.setStyle(Qt.PenStyle.DotLine)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        painter.save()
        painter.rotate(math.degrees(rot))
        rect = QRectF(-radio_anillo, -radio_anillo, radio_anillo * 2, radio_anillo * 2)
        painter.drawArc(rect, 0, 270 * 16)
        painter.restore()

        # 6 nodos decorativos (sin cambio)
        for i in range(6):
            ang = rot + i * (math.pi / 3)
            px = radio_anillo * math.cos(ang)
            py = radio_anillo * math.sin(ang)
            c_nodo = QColor(color)
            c_nodo.setAlphaF(max(0.0, min(1.0, brillo * 0.4)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(c_nodo)
            painter.drawEllipse(QPointF(px, py), 2, 2)

    # ═══════════════════════════════════════════════
    # PARTE 2: INDICADORES DE RECURSOS INTEGRADOS (optimizado)
    # ═══════════════════════════════════════════════
    # WI-325: ALWAYS draw resource rings (even in legacy mode with low brillo)
    if brillo > 0.001:  # FIX: Reducido de 0.02 a 0.001 para garantizar visibilidad
        # Radios: ligeramente más grandes que los anillos para no superponer
        r_cpu = int((RADIO_NUCLEO + 58) * st.escala)
        r_ram = int((RADIO_NUCLEO + 50) * st.escala)
        r_gpu = int((RADIO_NUCLEO + 42) * st.escala)
        r_disk = int((RADIO_NUCLEO + 34) * st.escala)
        _grosor = max(1.5, 2.0 * st.escala)  # FIX: Increased from 1.0 to 1.5 for visibility

        # Ángulo de inicio gira con fase (reacciona emocionalmente)
        ang_inicio = st.rot_anillo1  # Usar rotación del anillo 1 para coherencia

        def _dibujar_arco(valor: float, radio: int, color_arco: QColor, index: int, sin_dato: bool = False):
            """Dibuja un arco de porcentaje (0-100).

            sin_dato=True: WI-ANILLOS-4: la métrica no está disponible (p.ej.
            GPU sin telemetría — no-NVIDIA, o nvidia-smi falló/timeout en este
            frame). Antes esto hacía que el llamador se saltara el anillo por
            completo (ver más abajo), lo que: (a) dejaba solo 3 anillos
            visibles en vez de 4, y (b) rompía la simetría de 90° entre los 4
            arcos (CPU/RAM/GPU/Disco comparten el mismo ángulo de rotación
            `ang_inicio` con offsets fijos de 90°) — con GPU ausente, los 3
            arcos restantes giraban juntos pero ya NO en un patrón de 4 puntas
            parejo, lo que se percibe como "rotación incoherente". Ahora se
            dibuja siempre un 4º arco: corto, gris y atenuado — señala
            honestamente "sin dato" sin inventar un % de uso real, y mantiene
            la simetría/coherencia rotacional de los 4 anillos."""
            ang_offset = index * (360 / 4) if index < 4 else 0  # Distribuir 4 arcos

            if sin_dato:
                angulo_span = 22  # arco corto fijo, ni 0% real ni dato inventado
                c_arco = QColor(140, 140, 150)  # gris neutro: "sin telemetría"
                alpha = max(0.18, min(0.4, brillo * 0.5))
                pen_width = max(1.2, _grosor * 0.8)
            else:
                if valor < 0.1:  # Mostrar incluso valores bajos de CPU/memoria
                    return
                angulo_span = min(270, int(270 * (valor / 100.0)))  # 0→270° según porcentaje
                c_arco = QColor(color_arco)
                if index == 0:
                    # CPU debe responder visualmente al valor real (menos intrusivo)
                    alpha = max(0.20, min(1.0, brillo * 0.8 + valor / 140.0))
                    pen_width = max(1.6, _grosor + (valor / 100.0))
                else:
                    # Otros indicadores: aún más sutiles para no distraer
                    alpha = max(0.22, min(1.0, brillo * 0.7 + valor / 300.0))
                    pen_width = _grosor

            c_arco.setAlphaF(alpha)
            pen_arco = QPen(c_arco, pen_width)
            painter.setPen(pen_arco)
            painter.setBrush(Qt.BrushStyle.NoBrush)

            painter.save()
            painter.rotate(math.degrees(ang_inicio) + ang_offset)
            rect = QRectF(-radio, -radio, radio * 2, radio * 2)
            painter.drawArc(rect, 0, angulo_span * 16)
            painter.restore()

        # Colores para cada métrica — WI-ANILLOS-4: alineados con los colores
        # fijos que YA usa el "Administrador de tareas de Computadora"
        # (diálogo interno de la app, ver ventana_principal.py::_make_bar en
        # el método que abre "⚙ Administrador de tareas de Computadora") —
        # esa es la referencia real de "colores homónimos en la interfaz de
        # Computadora" para CPU/RAM/GPU/Disco, con la ventaja de que ahí ya
        # están elegidos para ser mutuamente distinguibles.
        # Antes CPU (100,200,255) y GPU en modo 'media' (90,220,255) eran
        # prácticamente el MISMO azul/cian — dos anillos de radios vecinos
        # con color casi idéntico se leen como "un solo anillo", lo cual es
        # otra causa real de que el usuario contara solo 3 en vez de 4.
        c_cpu = QColor(200, 80, 48)      # #c85030 — igual que la barra CPU del admin. de tareas
        c_ram = QColor(48, 168, 200)     # #30a8c8 — igual que la barra RAM
        # GPU: el LARGO del arco siempre representa % de VRAM usada (sin cambios).
        # El COLOR BASE es el verde de la barra GPU del admin. de tareas
        # (#40c870); cuando el motor dominante es NVENC/NVDEC ('media') se usa
        # una variante azul-verdosa para diferenciar codificación de video de
        # compute/3D sin perder la identidad "verde=GPU" ni volver a chocar
        # con el azul de CPU.
        if gpu_motor == "media":
            c_gpu = QColor(64, 190, 180)      # Verde-cian (codificación/decodificación de video)
        else:
            c_gpu = QColor(64, 200, 112)      # #40c870 (compute/3D, o motor desconocido — fallback honesto)
        c_disk = QColor(200, 160, 48)    # #c8a030 — igual que la barra "Disco C:"

        # Dibujar arcos en orden: CPU, RAM, GPU, Disco (de más externo a más
        # interno vía r_cpu > r_ram > r_gpu > r_disk ya definidos arriba).
        # WI-ANILLOS-4: GPU SIEMPRE se dibuja — con dato real si gpu>=0, o con
        # el arco "sin_dato" si no hay telemetría — para mantener los 4
        # anillos visibles y su simetría rotacional de 90°.
        _dibujar_arco(cpu, r_cpu, c_cpu, 0)
        _dibujar_arco(ram, r_ram, c_ram, 1)
        if gpu >= 0.0:
            _dibujar_arco(gpu, r_gpu, c_gpu, 2)
        else:
            _dibujar_arco(0.0, r_gpu, c_gpu, 2, sin_dato=True)
        _dibujar_arco(disco, r_disk, c_disk, 3)

    painter.restore()


def dibujar_particulas(
    painter: QPainter, cx: float, cy: float, color: QColor, st: DrawState
):
    """Dibuja partículas flotantes."""
    size_boost = 1.0 + st.carga_emocional * 0.8
    alpha_boost = 0.5 + min(0.5, st.carga_emocional * 0.7)
    for p in st.particulas:
        pos = p.pos
        if p.es_letra:
            c = QColor(color)
            c.setAlphaF(max(0.0, min(1.0, p.alpha * alpha_boost)))
            font = QFont("Segoe UI", int(8 * st.escala * size_boost))
            painter.setFont(font)
            painter.setPen(c)
            painter.drawText(
                QPointF(cx + pos.x() * st.escala, cy + pos.y() * st.escala),
                p.letra,
            )
        else:
            c = QColor(color)
            c.setAlphaF(max(0.0, min(1.0, p.alpha * 0.5 * alpha_boost)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(c)
            sz = p.tamano * st.escala * size_boost
            painter.drawEllipse(
                QPointF(cx + pos.x() * st.escala, cy + pos.y() * st.escala),
                sz, sz,
            )


def dibujar_letras_orbitantes(
    painter: QPainter, cx: float, cy: float, brillo: float, color: QColor, st: DrawState
):
    """7 letras del nombre divino orbitan el núcleo."""
    letras = "שם המפורש"
    n = len(letras)
    radio_letras = (RADIO_NUCLEO + 22) * st.escala

    font = QFont("Segoe UI", int(9 * st.escala))
    font.setBold(True)
    painter.setFont(font)

    for i, letra in enumerate(letras):
        if letra == " ":
            continue
        ang = st.rot_letras + i * (2 * math.pi / n)
        px = cx + radio_letras * math.cos(ang)
        py = cy + radio_letras * math.sin(ang)

        c = QColor(color)
        pulsacion = 0.3 + 0.4 * math.sin(st.fase * 0.8 + i * 0.7)
        c.setAlphaF(max(0.0, min(1.0, brillo * pulsacion)))
        painter.setPen(c)
        painter.drawText(QPointF(px - 4, py + 4), letra)


def dibujar_nucleo(
    painter: QPainter, cx: float, cy: float, brillo: float,
    color_pri: QColor, color_sec: QColor, st: DrawState,
):
    """Esfera central de obsidiana con reflejo — WI-297: Animación fluida mercurio-like."""
    radio = int(RADIO_NUCLEO * st.escala)

    # WI-297: Morphing fluido basado en estado
    morph_factor = getattr(st, 'morph_factor', 0.0)  # 0.0 = esfera perfecta, 1.0 = deformada
    pulsacion = 1.0 + morph_factor * 0.3 * math.sin(st.fase * 2.0)  # Pulsación fluida

    radio_x = radio * pulsacion
    radio_y = radio * (1.0 + morph_factor * 0.2)

    grad = QRadialGradient(cx - radio * 0.3, cy - radio * 0.3, radio * 1.5)
    c_centro = QColor(color_sec)
    c_centro.setAlphaF(min(1.0, max(0.35, brillo * 1.0)))
    c_medio = QColor(color_pri)
    c_medio.setAlphaF(min(1.0, max(0.25, brillo * 0.8)))
    c_borde = QColor(20, 20, 25)
    c_borde.setAlphaF(min(1.0, 0.75 + brillo * 0.25))

    grad.setColorAt(0.0, c_centro)
    grad.setColorAt(0.4, c_medio)
    grad.setColorAt(0.8, c_borde)
    grad.setColorAt(1.0, QColor(0, 0, 0, 0))

    painter.save()
    painter.setOpacity(max(0.35, min(1.0, brillo)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(grad)
    # WI-297: Dibujar elipse deformada para efecto mercurio
    painter.drawEllipse(QPointF(cx, cy), radio_x, radio_y)
    painter.restore()

    reflejo = QRadialGradient(cx - radio * 0.25, cy - radio * 0.25, radio * 0.4)
    c_ref = QColor(255, 255, 250)
    c_ref.setAlphaF(min(1.0, max(0.15, brillo * 0.6)))
    reflejo.setColorAt(0, c_ref)
    reflejo.setColorAt(1.0, QColor(0, 0, 0, 0))
    painter.setBrush(reflejo)
    painter.drawEllipse(
        QPointF(cx - radio * 0.25, cy - radio * 0.25),
        int(radio * 0.35), int(radio * 0.35),
    )


def dibujar_emet(
    painter: QPainter, cx: float, cy: float, brillo: float, color: QColor, st: DrawState
):
    """Dibuja אמת (Emet = verdad/vida) en el centro cuando está activo."""
    c = QColor(color)
    pulsacion = 0.5 + 0.5 * math.sin(st.fase * 1.2)
    c.setAlphaF(max(0.0, min(1.0, brillo * pulsacion * 0.7)))

    font = QFont("Segoe UI", int(12 * st.escala))
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(c)
    painter.drawText(QPointF(cx - 12 * st.escala, cy + 5 * st.escala), "אמת")


def _dibujar_icono_herramienta(
    painter: QPainter, x: float, y: float, escala: float, alpha: float, categoria: str
):
    """WI-245: Dibuja un ícono vectorial transparente según la categoría de herramienta."""
    s = 7 * escala  # tamaño base del ícono
    c = QColor(255, 255, 255)
    c.setAlphaF(max(0.0, min(1.0, alpha)))
    pen = QPen(c, max(1.0, 1.2 * escala))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    if categoria == "lectura":
        # Documento/scroll: rectángulo con líneas
        painter.drawRect(QRectF(x - s * 0.5, y - s * 0.7, s, s * 1.4))
        for i in range(3):
            _ly = y - s * 0.3 + i * s * 0.4
            painter.drawLine(QPointF(x - s * 0.25, _ly), QPointF(x + s * 0.25, _ly))
    elif categoria == "escritura":
        # Lápiz diagonal
        painter.drawLine(QPointF(x - s * 0.5, y + s * 0.5), QPointF(x + s * 0.3, y - s * 0.6))
        painter.drawLine(QPointF(x + s * 0.3, y - s * 0.6), QPointF(x + s * 0.5, y - s * 0.4))
    elif categoria == "busqueda":
        # Lupa: círculo + línea
        painter.drawEllipse(QPointF(x - s * 0.15, y - s * 0.15), s * 0.45, s * 0.45)
        painter.drawLine(QPointF(x + s * 0.2, y + s * 0.2), QPointF(x + s * 0.55, y + s * 0.55))
    elif categoria == "ejecucion":
        # Rayo/lightning
        painter.drawLine(QPointF(x, y - s * 0.7), QPointF(x - s * 0.2, y))
        painter.drawLine(QPointF(x - s * 0.2, y), QPointF(x + s * 0.15, y - s * 0.1))
        painter.drawLine(QPointF(x + s * 0.15, y - s * 0.1), QPointF(x - s * 0.05, y + s * 0.7))
    elif categoria == "copilot":
        # Estrella de 6 puntas simplificada (Menorá)
        for i in range(6):
            ang = i * math.pi / 3
            px = x + s * 0.55 * math.cos(ang)
            py = y + s * 0.55 * math.sin(ang)
            painter.drawLine(QPointF(x, y), QPointF(px, py))
    elif categoria == "agenda":
        # Checklist: cuadrado + check
        painter.drawRect(QRectF(x - s * 0.5, y - s * 0.5, s * 0.4, s * 0.4))
        painter.drawLine(QPointF(x + s * 0.05, y - s * 0.1), QPointF(x + s * 0.5, y - s * 0.1))
        painter.drawRect(QRectF(x - s * 0.5, y + s * 0.1, s * 0.4, s * 0.4))
        painter.drawLine(QPointF(x + s * 0.05, y + s * 0.3), QPointF(x + s * 0.5, y + s * 0.3))
    elif categoria == "meta":
        # Engranaje: círculo con dientes
        painter.drawEllipse(QPointF(x, y), s * 0.3, s * 0.3)
        for i in range(6):
            ang = i * math.pi / 3
            px1 = x + s * 0.35 * math.cos(ang)
            py1 = y + s * 0.35 * math.sin(ang)
            px2 = x + s * 0.55 * math.cos(ang)
            py2 = y + s * 0.55 * math.sin(ang)
            painter.drawLine(QPointF(px1, py1), QPointF(px2, py2))
    else:
        # Info: círculo con "i"
        painter.drawEllipse(QPointF(x, y), s * 0.5, s * 0.5)
        painter.drawLine(QPointF(x, y - s * 0.05), QPointF(x, y + s * 0.3))
        painter.drawEllipse(QPointF(x, y - s * 0.2), s * 0.06, s * 0.06)


def dibujar_indicadores_herramientas(
    painter: QPainter, cx: float, cy: float, brillo: float, st: DrawState
):
    """Dibuja indicadores flotantes de herramientas activas alrededor del orbe."""
    for ind in st.indicadores_herramientas:
        if ind.alpha <= 0.01:
            continue
        pos = ind.pos
        x = cx + pos.x() * st.escala
        y = cy + pos.y() * st.escala

        pulso = 0.7 + 0.3 * math.sin(st.fase * 3 + ind.angulo)
        alpha = ind.alpha * brillo * pulso

        if ind.estado == "ejecutando":
            glow = QColor(255, 200, 80)
        else:
            glow = QColor(80, 255, 120)
        glow.setAlphaF(max(0.0, min(1.0, alpha * 0.4)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(glow)
        painter.drawEllipse(QPointF(x, y), 10 * st.escala, 10 * st.escala)

        # WI-245: Ícono vectorial transparente en lugar de emoji
        _cat = getattr(ind, 'categoria', 'info')
        _dibujar_icono_herramienta(painter, x, y, st.escala, alpha, _cat)


def dibujar_indicador_nivel(
    painter: QPainter, cx: float, cy: float, brillo: float,
    st: DrawState, colores_nivel: dict, nombres_nivel: dict,
):
    """Dibuja el nombre de la Sefirá activa debajo del orbe."""
    nivel = st.cerebro_nivel
    color = colores_nivel.get(nivel, QColor(200, 150, 40))
    nombre = nombres_nivel.get(nivel, "")

    pulso = 0.6 + 0.4 * math.sin(st.fase * 2)
    c = QColor(color)
    c.setAlphaF(max(0.0, min(1.0, brillo * pulso * 0.8)))

    font = QFont("Segoe UI", int(8 * st.escala))
    font.setBold(True)
    painter.setFont(font)
    painter.setPen(c)
    painter.drawText(
        QPointF(cx - 14 * st.escala, cy - (RADIO_NUCLEO + 8) * st.escala), nombre
    )


# ═══════════════════════════════════════════════
# GEOMETRÍA SAGRADA — PATRONES TEMPORALES (FP-024 opcionales)
# ═══════════════════════════════════════════════

# Proporción áurea
_PHI = (1.0 + math.sqrt(5.0)) / 2.0


def dibujar_patron_sagrado(
    painter: QPainter, cx: float, cy: float, brillo: float,
    color: QColor, st: DrawState,
):
    """FP-024: Dibuja un patrón de geometría sagrada temporal sobre el orbe."""
    if not st.patron_sagrado or st.patron_progreso <= 0.0:
        return
    # Alpha envelope: fade in (0→0.2), sustain (0.2→0.8), fade out (0.8→1.0)
    t = st.patron_progreso
    if t < 0.2:
        alpha = t / 0.2
    elif t > 0.8:
        alpha = (1.0 - t) / 0.2
    else:
        alpha = 1.0
    alpha *= brillo * 0.5  # sutil, no dominante

    if st.patron_sagrado == "espiral":
        _dibujar_espiral_aurea(painter, cx, cy, alpha, color, st)
    elif st.patron_sagrado == "hexagrama":
        _dibujar_hexagrama(painter, cx, cy, alpha, color, st)


def _dibujar_espiral_aurea(
    painter: QPainter, cx: float, cy: float, alpha: float,
    color: QColor, st: DrawState,
):
    """Espiral logarítmica basada en φ (proporción áurea). Aparece al despertar."""
    painter.save()
    painter.translate(cx, cy)
    # Rotación lenta basada en fase de animación
    painter.rotate(math.degrees(st.fase * 0.1))

    c = QColor(color)
    c.setAlphaF(max(0.0, min(1.0, alpha * 0.6)))
    pen = QPen(c, max(0.5, 1.2 * st.escala))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Trazar espiral: r = a * φ^(θ/90°)
    a = 3.0 * st.escala
    puntos = 120
    prev = None
    for i in range(puntos):
        theta = i * (math.pi / 15)  # ~8 vueltas
        r = a * (_PHI ** (theta / (math.pi / 2)))
        if r > RADIO_RESPLANDOR * 1.2 * st.escala:
            break
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        pt = QPointF(x, y)
        if prev is not None:
            # Fade alpha por distancia al centro
            fade = max(0.1, 1.0 - r / (RADIO_RESPLANDOR * 1.2 * st.escala))
            c2 = QColor(color)
            c2.setAlphaF(max(0.0, min(1.0, alpha * 0.6 * fade)))
            pen2 = QPen(c2, max(0.5, 1.2 * st.escala * fade))
            painter.setPen(pen2)
            painter.drawLine(prev, pt)
        prev = pt

    painter.restore()


def _dibujar_hexagrama(
    painter: QPainter, cx: float, cy: float, alpha: float,
    color: QColor, st: DrawState,
):
    """Estrella de David (hexagrama). Aparece en conexión emocional."""
    painter.save()
    painter.translate(cx, cy)
    # Pulsación sutil
    pulso = 1.0 + 0.05 * math.sin(st.fase * 1.5)
    radio = RADIO_RESPLANDOR * 0.6 * st.escala * pulso

    c = QColor(color)
    c.setAlphaF(max(0.0, min(1.0, alpha * 0.5)))
    pen = QPen(c, max(0.5, 1.0 * st.escala))
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Dos triángulos superpuestos
    for offset_ang in (0.0, math.pi / 6):
        rot = st.fase * 0.08 + offset_ang
        pts = []
        for i in range(3):
            ang = rot + i * (2 * math.pi / 3)
            pts.append(QPointF(radio * math.cos(ang), radio * math.sin(ang)))
        # Cerrar triángulo
        for i in range(3):
            painter.drawLine(pts[i], pts[(i + 1) % 3])

    painter.restore()


# ═══════════════════════════════════════════════
# SUB-PARTÍCULAS FRACTALES (FP-024 — Hermetismo: Como arriba, como abajo)
# Solo visibles en Citrinitas+ — 2-3 micro-puntos por partícula principal
# ═══════════════════════════════════════════════

def dibujar_particulas_con_fractales(
    painter: QPainter, cx: float, cy: float, color: QColor, st: DrawState,
):
    """Dibuja partículas + sub-partículas fractales (Citrinitas/Rubedo)."""
    es_fractal = st.etapa_alquimica in ("citrinitas", "rubedo")
    _fractal_count = 0  # WI-243: Cap sub-partículas fractales para rendimiento

    for p in st.particulas:
        pos = p.pos
        sx = cx + pos.x() * st.escala
        sy = cy + pos.y() * st.escala

        if p.es_letra:
            c = QColor(color)
            c.setAlphaF(max(0.0, min(1.0, p.alpha)))
            font = QFont("Segoe UI", int(8 * st.escala))
            painter.setFont(font)
            painter.setPen(c)
            painter.drawText(QPointF(sx, sy), p.letra)
        else:
            c = QColor(color)
            c.setAlphaF(max(0.0, min(1.0, p.alpha * 0.6)))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(c)
            sz = p.tamano * st.escala
            painter.drawEllipse(QPointF(sx, sy), sz, sz)

        # Sub-partículas fractales: 3 micro-puntos orbitando cada partícula principal
        # WI-243: Cap a 15 partículas con fractales para evitar frame drops
        if es_fractal and p.alpha > 0.15 and not p.es_letra and _fractal_count < 15:
            _sub_sz = max(0.4, p.tamano * 0.3 * st.escala)
            _sub_r = max(2.0, p.tamano * 2.5 * st.escala)
            c_sub = QColor(color)
            c_sub.setAlphaF(max(0.0, min(1.0, p.alpha * 0.35)))
            painter.setBrush(c_sub)
            _fractal_count += 1
            for j in range(3):
                # Orbitar con fase basada en ángulo de partícula + offset por sub-partícula
                sub_ang = p.angulo * 3.0 + st.fase * 0.5 + j * (2.0 * math.pi / 3.0)
                sub_x = sx + _sub_r * math.cos(sub_ang)
                sub_y = sy + _sub_r * math.sin(sub_ang)
                painter.drawEllipse(QPointF(sub_x, sub_y), _sub_sz, _sub_sz)


def dibujar_indicador_recursos(
    painter: QPainter, cx: float, cy: float, brillo: float,
    st: DrawState, cpu: float, ram: float,
    gpu: float = -1.0, disco: float = 0.0,
    disco_io: float = 0.0,
    rot_mod: float = 1.0,  # WI-XXX: Modificador de rotación por humor
):
    """WI-242/WI-254/WI-261: Arcos giratorios mostrando CPU, RAM, GPU y Disco.
    cpu/ram/disco: 0-100 porcentaje. gpu: 0-100 o -1 si no disponible.
    disco_io: 0.0-1.0 I/O activity pulse (modula alpha del arco disco).
    Los arcos giran con la fase de animación multiplicada por rot_mod (humor)."""
    _esc = st.escala
    if brillo < 0.02:
        return

    # Radios concéntricos (de exterior a interior):
    #   GPU(56) > CPU(48) > RAM(40) > Disco(32)
    _r_gpu  = int((RADIO_NUCLEO + 56) * _esc)
    _r_cpu  = int((RADIO_NUCLEO + 48) * _esc)
    _r_ram  = int((RADIO_NUCLEO + 40) * _esc)
    _r_disk = int((RADIO_NUCLEO + 32) * _esc)
    _grosor = max(1.5, 2.5 * _esc)

    # Ángulo de inicio gira con la fase multiplicada por rot_mod (reacciona a emociones)
    _start_cpu  = int((st.fase * 60 * rot_mod) % 360) * 16  # QPainter usa 1/16 grados
    _start_ram  = int((st.fase * -45 * rot_mod + 180) % 360) * 16  # giro inverso
    _start_gpu  = int((st.fase * 90 * rot_mod) % 360) * 16   # giro rápido
    _start_disk = int((st.fase * 20 * rot_mod + 90) % 360) * 16  # giro lento

    # Extensión proporcional al porcentaje (mínimo 10° para visibilidad)
    _span_cpu  = int(max(10, cpu * 3.2)) * 16   # 0-100% → 10-320°
    _span_ram  = int(max(10, ram * 3.2)) * 16
    _span_gpu  = int(max(10, gpu * 3.2)) * 16 if gpu >= 0 else 0
    _span_disk = int(max(10, disco * 3.2)) * 16

    # Color: verde → amarillo → naranja → rojo según carga
    def _color_carga(pct: float, alpha: float) -> QColor:
        pct = max(0.0, min(100.0, pct))
        if pct < 50.0:
            r, g = int(pct * 5.1), 255
        elif pct < 70.0:
            # Verde a amarillo
            r, g = 255, int(255 - (pct - 50.0) * 12.75)
        elif pct < 90.0:
            # Amarillo a naranja
            r, g = 255, int(160 - (pct - 70.0) * 8.0)
        else:
            # Naranja a rojo
            r, g = 255, 0
        c = QColor(max(0, min(255, r)), max(0, min(255, g)), 0)
        c.setAlphaF(max(0.2, min(1.0, alpha * brillo)))
        return c

    rect_cpu  = QRectF(cx - _r_cpu,  cy - _r_cpu,  _r_cpu * 2,  _r_cpu * 2)
    rect_ram  = QRectF(cx - _r_ram,  cy - _r_ram,  _r_ram * 2,  _r_ram * 2)
    rect_gpu  = QRectF(cx - _r_gpu,  cy - _r_gpu,  _r_gpu * 2,  _r_gpu * 2)
    rect_disk = QRectF(cx - _r_disk, cy - _r_disk, _r_disk * 2, _r_disk * 2)

    painter.setBrush(Qt.BrushStyle.NoBrush)

    # GPU arc (outermost — solo si disponible)
    if gpu >= 0:
        pen_gpu = QPen(_color_carga(gpu, 0.5), _grosor)
        pen_gpu.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_gpu)
        painter.drawArc(rect_gpu, _start_gpu, _span_gpu)

    # CPU arc
    pen_cpu = QPen(_color_carga(cpu, 0.6), _grosor)
    pen_cpu.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen_cpu)
    painter.drawArc(rect_cpu, _start_cpu, _span_cpu)

    # RAM arc
    pen_ram = QPen(_color_carga(ram, 0.4), max(1.0, _grosor * 0.7))
    pen_ram.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen_ram)
    painter.drawArc(rect_ram, _start_ram, _span_ram)

    # Disco arc (innermost — alpha pulsa con actividad I/O)
    # WI-261: Base alpha 0.3 + I/O boost up to 0.7 (fade-in/fade-out)
    _disk_alpha = 0.3 + disco_io * 0.4
    pen_disk = QPen(_color_carga(disco, _disk_alpha), max(1.0, _grosor * (0.6 + disco_io * 0.4)))
    pen_disk.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen_disk)
    painter.drawArc(rect_disk, _start_disk, _span_disk)


# ═══════════════════════════════════════════════
# METATRÓN GEOMETRY INTEGRATION (FP-139 RUBEDO)
# ═══════════════════════════════════════════════

def dibujar_metatron(
    painter: QPainter, cx: float, cy: float, brillo: float,
    color: QColor, st: DrawState, metatron_cube: Any, demo_mode: bool = False
):
    """FP-139 RUBEDO: Dibuja geometría sagrada Metatrón como núcleo central. """
    if not metatron_cube or not hasattr(metatron_cube, 'vertices'):
        return

    painter.save()
    painter.translate(cx, cy)

    # Escala central, dentro de la esfera obsidiana, para mantener Metatron en el núcleo.
    base_radio = RADIO_NUCLEO * st.escala * 0.45
    escala_geom = base_radio / (RADIO_NUCLEO * 0.5)

    c_geom = QColor(color)
    pulsacion = 0.55 + 0.45 * math.sin(st.fase * 1.5)
    alpha = 1.0 if demo_mode else max(0.0, min(1.0, brillo * pulsacion * 0.6))
    c_geom.setAlphaF(alpha)

    pen = QPen(c_geom, max(0.5, 1.0 * escala_geom))
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)

    # Capas planetarias de Metatrón: círculos concéntricos y polígonos anidados.
    shell_radii = [base_radio * 0.95, base_radio * 1.35, base_radio * 1.75]
    for radio in shell_radii:
        painter.drawEllipse(QPointF(0, 0), radio, radio)

    def dibujar_poligono(lados: int, radio: float, rot_offset: float):
        if lados < 3:
            return
        puntos = []
        for i in range(lados):
            ang = rot_offset + i * (2 * math.pi / lados)
            puntos.append(QPointF(math.cos(ang) * radio, math.sin(ang) * radio))
        for i in range(len(puntos)):
            painter.drawLine(puntos[i], puntos[(i + 1) % len(puntos)])

    dibujar_poligono(3, base_radio * 0.75, st.fase * 0.9)
    dibujar_poligono(4, base_radio * 1.10, st.fase * 0.5 + math.pi / 12)
    dibujar_poligono(6, base_radio * 1.50, st.fase * 0.25 + math.pi / 8)

    # Refuerzo visual con puntos de anclaje alrededor del núcleo.
    punto_radio = max(1.0, 1.8 * escala_geom)
    c_punto = QColor(c_geom)
    c_punto.setAlphaF(1.0 if demo_mode else max(0.0, min(1.0, brillo * pulsacion * 0.9)))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(c_punto)
    for ang in [0, math.pi / 3, 2 * math.pi / 3, math.pi, 4 * math.pi / 3, 5 * math.pi / 3]:
        x = math.cos(ang) * base_radio * 1.35
        y = math.sin(ang) * base_radio * 1.35
        painter.drawEllipse(QPointF(x, y), punto_radio, punto_radio)

    # Núcleo interior de Metatrón.
    painter.drawEllipse(QPointF(0, 0), base_radio * 0.32, base_radio * 0.32)
    painter.restore()


