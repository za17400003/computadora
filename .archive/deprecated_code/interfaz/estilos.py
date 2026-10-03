"""
Estilos visuales de Computadora — Tema oscuro con acentos ámbar.
"""

# Colores principales
NEGRO_FONDO = "#0a0a0a"
NEGRO_PANEL = "#111111"
NEGRO_INPUT = "#1a1a1a"
AMBAR_TEXTO = "#e0c878"
AMBAR_BORDE = "#8B6914"
AMBAR_BRILLANTE = "#FFB347"
ORO = "#FFD700"
GRIS_SISTEMA = "#666666"
BLANCO_USUARIO = "#f0f0f0"

ESTILO_GLOBAL = f"""
QMainWindow {{
    background-color: {NEGRO_FONDO};
}}

QWidget {{
    background-color: {NEGRO_FONDO};
    color: {AMBAR_TEXTO};
    font-family: 'Segoe UI', 'Consolas', monospace;
    font-size: 13px;
}}

QTextBrowser {{
    background-color: {NEGRO_PANEL};
    color: {AMBAR_TEXTO};
    border: 1px solid {AMBAR_BORDE};
    border-radius: 8px;
    padding: 12px;
    font-size: 14px;
    selection-background-color: {AMBAR_BORDE};
}}

QLineEdit {{
    background-color: {NEGRO_INPUT};
    color: {BLANCO_USUARIO};
    border: 1px solid {AMBAR_BORDE};
    border-radius: 6px;
    padding: 10px 14px;
    font-size: 14px;
}}

QLineEdit:focus {{
    border-color: {AMBAR_BRILLANTE};
}}

QLabel {{
    background-color: transparent;
    color: {GRIS_SISTEMA};
    font-size: 11px;
}}

QStatusBar {{
    background-color: {NEGRO_PANEL};
    color: {GRIS_SISTEMA};
    font-size: 10px;
}}
"""


