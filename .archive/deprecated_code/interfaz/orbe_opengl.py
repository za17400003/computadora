"""
FP-156 CITRINITAS - RUBEDO: Orbe OpenGL.

Render del orbe 4D con aceleracion GPU via QOpenGLWidget.
Soporta 3 estados visuales: NUCLEO, FERROFLUIDO, METATRON.

Overlay: Cubo de Metatron (13 esferas + 53 lineas) con shaders GLSL.
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

import numpy as np
from PyQt6.QtCore import Qt, QTimer, QTime
from PyQt6.QtGui import QSurfaceFormat, QColor
try:
    from PyQt6.QtOpenGLWidgets import QOpenGLWidget
except ImportError:
    from PyQt6.QtWidgets import QOpenGLWidget  # fallback
from loguru import logger

try:
    from OpenGL import GL
    _OPENGL_AVAILABLE = True
except ImportError:
    _OPENGL_AVAILABLE = False
    logger.warning("PyOpenGL no instalado. Usar QPainter fallback.")


def _init_opengl_format():
    fmt = QSurfaceFormat()
    fmt.setVersion(3, 3)
    fmt.setProfile(QSurfaceFormat.OpenGLContextProfile.CoreProfile)
    fmt.setSamples(4)
    fmt.setSwapInterval(1)
    QSurfaceFormat.setDefaultFormat(fmt)


class OrbeOpenGL(QOpenGLWidget):
    ESTADO_NUCLEO = 0
    ESTADO_FERROFLUIDO = 1
    ESTADO_METATRON = 2
    
    def __init__(self, parent=None):
        _init_opengl_format()
        super().__init__(parent)
        
        self.estado_actual = self.ESTADO_NUCLEO
        self.tiempo = QTime()
        self.tiempo.start()
        
        self.num_particulas = 400
        self._pos = np.zeros((self.num_particulas, 3), dtype=np.float32)
        self._colores = np.ones((self.num_particulas, 4), dtype=np.float32)
        self._tamanos = np.ones(self.num_particulas, dtype=np.float32) * 3.0
        
        # QFT
        self._carga = np.zeros(self.num_particulas, dtype=np.float32)
        self._es_antiparticula = np.zeros(self.num_particulas, dtype=bool)
        self._energia = np.ones(self.num_particulas, dtype=np.float32)
        
        # Overlay Metatron
        self._metatron_vertices: Optional[np.ndarray] = None
        self._metatron_aristas: Optional[np.ndarray] = None
        self._metatron_alpha = 0.0
        
        self.rotacion_x = 0.0
        self.rotacion_y = 0.0
        self._morph = 0.0
        
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.actualizar)
        self._timer.start(16)
        
        # Buffers OpenGL
        self._vbo_pos = None
        self._vbo_color = None
        self._vao = None
        self._shader = None
        self._shader_line = None
        self._metatron_vao = None
        self._metatron_vbo_verts = None
        self._metatron_vbo_lines = None
        self._cubo_metatron = None
        
        self._inicializado = False
        
        # Inicializar MetatronCube
        try:
            from computadora.geometria.metatron import MetatronCube
            self._cubo_metatron = MetatronCube(tamano=150.0)
            self._metatron_vertices = self._cubo_metatron.obtener_vertices_numpy()
            self._metatron_aristas = self._cubo_metatron.obtener_aristas_pares()
            logger.debug(f"MetatronCube: {len(self._metatron_vertices)} vertices, {len(self._metatron_aristas)} aristas")
        except Exception as e:
            logger.warning(f"MetatronCube no disponible: {e}")
    
    def initializeGL(self):
        if not _OPENGL_AVAILABLE:
            return
        
        GL.glClearColor(0.02, 0.02, 0.05, 1.0)
        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glEnable(GL.GL_PROGRAM_POINT_SIZE)
        
        vs_point = '''#version 330 core
        layout (location = 0) in vec3 pos;
        layout (location = 1) in vec4 color;
        layout (location = 2) in float size;
        uniform mat4 proj;
        uniform mat4 view;
        out vec4 vColor;
        void main() {
            gl_Position = proj * view * vec4(pos, 1.0);
            gl_PointSize = size;
            vColor = color;
        }'''
        fs_point = '''#version 330 core
        in vec4 vColor;
        out vec4 fragColor;
        void main() {
            vec2 coord = gl_PointCoord - vec2(0.5);
            float dist = length(coord);
            if (dist > 0.5) discard;
            float alpha = 1.0 - smoothstep(0.0, 0.5, dist);
            fragColor = vec4(vColor.rgb, vColor.a * alpha);
        }'''
        vs_line = '''#version 330 core
        layout (location = 0) in vec3 pos;
        uniform mat4 proj;
        uniform mat4 view;
        uniform vec4 lineColor;
        void main() {
            gl_Position = proj * view * vec4(pos, 1.0);
        }'''
        fs_line = '''#version 330 core
        uniform vec4 lineColor;
        out vec4 fragColor;
        void main() {
            fragColor = lineColor;
        }'''
        
        def compilar(vs_src, fs_src):
            vs = GL.glCreateShader(GL.GL_VERTEX_SHADER)
            GL.glShaderSource(vs, vs_src)
            GL.glCompileShader(vs)
            fs = GL.glCreateShader(GL.GL_FRAGMENT_SHADER)
            GL.glShaderSource(fs, fs_src)
            GL.glCompileShader(fs)
            prog = GL.glCreateProgram()
            GL.glAttachShader(prog, vs)
            GL.glAttachShader(prog, fs)
            GL.glLinkProgram(prog)
            GL.glDeleteShader(vs)
            GL.glDeleteShader(fs)
            return prog
        
        self._shader = compilar(vs_point, fs_point)
        self._shader_line = compilar(vs_line, fs_line)
        
        self._vao = GL.glGenVertexArrays(1)
        self._vbo_pos = GL.glGenBuffers(1)
        self._vbo_color = GL.glGenBuffers(1)
        self._vbo_size = GL.glGenBuffers(1)
        
        self._metatron_vao = GL.glGenVertexArrays(1)
        self._metatron_vbo_verts = GL.glGenBuffers(1)
        self._metatron_vbo_lines = GL.glGenBuffers(1)
        
        self._inicializado = True
        logger.debug("OpenGL inicializado")
    
    def resizeGL(self, w: int, h: int):
        if not _OPENGL_AVAILABLE:
            return
        GL.glViewport(0, 0, w, h)
    
    def paintGL(self):
        if not _OPENGL_AVAILABLE or not self._inicializado:
            return
        
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        
        w = self.width()
        h = self.height()
        aspect = w / h if h > 0 else 1.0
        scale = 200.0
        left, right = -scale * aspect, scale * aspect
        bottom, top = -scale, scale
        near, far = 0.1, 1000.0
        
        # Matriz de proyección ortogonal COMPLETA (FIX: incluir z-clipping)
        proj = np.eye(4, dtype=np.float32)
        proj[0,0] = 2.0 / (right - left)
        proj[1,1] = 2.0 / (top - bottom)
        proj[2,2] = -2.0 / (far - near)
        proj[0,3] = -(right + left) / (right - left)
        proj[1,3] = -(top + bottom) / (top - bottom)
        proj[3,3] = 1.0
        proj[2,3] = -(far + near) / (far - near)
        
        cos_x = math.cos(self.rotacion_x)
        sin_x = math.sin(self.rotacion_x)
        cos_y = math.cos(self.rotacion_y)
        sin_y = math.sin(self.rotacion_y)
        
        view = np.eye(4, dtype=np.float32)
        view[1,1] = cos_x; view[1,2] = -sin_x
        view[2,1] = sin_x; view[2,2] = cos_x
        vr = np.eye(4, dtype=np.float32)
        vr[0,0] = cos_y; vr[0,2] = sin_y
        vr[2,0] = -sin_y; vr[2,2] = cos_y
        view = view @ vr
        
        # ── Dibujar particulas ──
        GL.glUseProgram(self._shader)
        loc_proj = GL.glGetUniformLocation(self._shader, "proj")
        loc_view = GL.glGetUniformLocation(self._shader, "view")
        GL.glUniformMatrix4fv(loc_proj, 1, GL.GL_TRUE, proj)
        GL.glUniformMatrix4fv(loc_view, 1, GL.GL_TRUE, view)
        
        GL.glBindVertexArray(self._vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vbo_pos)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self._pos.nbytes, self._pos, GL.GL_DYNAMIC_DRAW)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glEnableVertexAttribArray(0)
        
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vbo_color)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self._colores.nbytes, self._colores, GL.GL_DYNAMIC_DRAW)
        GL.glVertexAttribPointer(1, 4, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glEnableVertexAttribArray(1)
        
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vbo_size)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, self._tamanos.nbytes, self._tamanos, GL.GL_DYNAMIC_DRAW)
        GL.glVertexAttribPointer(2, 1, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glEnableVertexAttribArray(2)
        
        GL.glDrawArrays(GL.GL_POINTS, 0, self.num_particulas)
        GL.glBindVertexArray(0)
        GL.glUseProgram(0)
        
        # ── Dibujar overlay MetatronCube (si activo) ──
        if self._metatron_alpha > 0.01 and self._cubo_metatron is not None:
            self._dibujar_metatron_cube(proj, view)
    
    def _dibujar_metatron_cube(self, proj: np.ndarray, view: np.ndarray):
        """Dibuja el Cubo de Metatron como overlay."""
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
        
        GL.glUseProgram(self._shader_line)
        loc_proj = GL.glGetUniformLocation(self._shader_line, "proj")
        loc_view = GL.glGetUniformLocation(self._shader_line, "view")
        loc_color = GL.glGetUniformLocation(self._shader_line, "lineColor")
        GL.glUniformMatrix4fv(loc_proj, 1, GL.GL_TRUE, proj)
        GL.glUniformMatrix4fv(loc_view, 1, GL.GL_TRUE, view)
        
        # Color dorado con alpha
        alpha = self._metatron_alpha * 0.6
        GL.glUniform4f(loc_color, 0.9, 0.7, 0.2, alpha)
        
        if self._metatron_vertices is None or self._metatron_aristas is None:
            GL.glUseProgram(0)
            return
        
        # Calcular posiciones de las lineas (cada arista -> 2 vertices)
        verts = self._metatron_vertices
        aristas = self._metatron_aristas
        
        # Crear buffer de lineas: para cada arista, 2 posiciones
        num_aristas = len(aristas)
        line_data = np.zeros((num_aristas * 2, 3), dtype=np.float32)
        for i, (a, b) in enumerate(aristas):
            if a < len(verts) and b < len(verts):
                line_data[i*2] = verts[a]
                line_data[i*2+1] = verts[b]
        
        GL.glBindVertexArray(self._metatron_vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._metatron_vbo_lines)
        GL.glBufferData(GL.GL_ARRAY_BUFFER, line_data.nbytes, line_data, GL.GL_DYNAMIC_DRAW)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glEnableVertexAttribArray(0)
        
        GL.glDrawArrays(GL.GL_LINES, 0, num_aristas * 2)
        GL.glBindVertexArray(0)
        GL.glUseProgram(0)
        GL.glDisable(GL.GL_BLEND)
    
    def actualizar(self):
        t = self.tiempo.elapsed() / 1000.0
        n = self.num_particulas
        
        if self.estado_actual == self.ESTADO_NUCLEO:
            self._actualizar_nucleo(t, n)
            self._metatron_alpha = max(0.0, self._metatron_alpha - 0.02)
        elif self.estado_actual == self.ESTADO_FERROFLUIDO:
            self._actualizar_ferrofluido(t, n)
            self._metatron_alpha = max(0.0, self._metatron_alpha - 0.01)
        else:
            self._actualizar_metatron(t, n)
            self._metatron_alpha = min(1.0, self._metatron_alpha + 0.02)
        
        self.rotacion_x += 0.005
        self.rotacion_y += 0.008
        self.update()
    
    def _actualizar_nucleo(self, t: float, n: int):
        """ESTADO_NUCLEO: esfera estable."""
        sqrt_n = int(math.sqrt(n * 2))
        theta = np.linspace(0, 2 * np.pi, max(sqrt_n, 1), dtype=np.float32)[:n]
        phi = np.arccos(1 - 2 * np.linspace(0.01, 0.99, n, dtype=np.float32))
        r = 80.0
        
        self._pos[:, 0] = r * np.sin(phi) * np.cos(theta) + np.random.randn(n).astype(np.float32) * 2.0
        self._pos[:, 1] = r * np.sin(phi) * np.sin(theta) + np.random.randn(n).astype(np.float32) * 2.0
        self._pos[:, 2] = r * np.cos(phi) + np.random.randn(n).astype(np.float32) * 2.0
        
        azul = np.array([0.4, 0.6, 0.9, 0.8], dtype=np.float32)
        self._colores[:] = azul + np.random.randn(n, 4).astype(np.float32) * 0.05
        self._tamanos[:] = 3.0
    
    def _actualizar_ferrofluido(self, t: float, n: int):
        """ESTADO_FERROFLUIDO: orbitas con QFT."""
        angulos = np.linspace(0, 2 * np.pi * 3, n, dtype=np.float32) + t * 0.5
        a = 50.0 + 30.0 * np.sin(angulos * 0.7 + t)
        b = 50.0 + 30.0 * np.cos(angulos * 0.5 + t * 0.3)
        c = 40.0 + 20.0 * np.sin(angulos * 0.3 + t * 0.7)
        
        cos_ang = np.cos(angulos)
        sin_ang = np.sin(angulos)
        
        self._pos[:, 0] = a * cos_ang * np.cos(angulos * 0.5)
        self._pos[:, 1] = b * sin_ang
        self._pos[:, 2] = c * cos_ang * np.sin(angulos * 0.5)
        
        # QFT: excitaciones
        excitacion = np.random.random(n) < 0.01
        self._es_antiparticula = np.where(excitacion, ~self._es_antiparticula, self._es_antiparticula)
        self._carga = np.where(self._es_antiparticula, -1.0, 1.0)
        
        self._colores[:, :3] = np.where(
            self._es_antiparticula[:, np.newaxis],
            np.array([0.9, 0.3, 0.3], dtype=np.float32),
            np.array([0.3, 0.5, 0.9], dtype=np.float32),
        )
        self._colores[:, 3] = 0.7 + 0.3 * np.sin(angulos + t)
        self._colores = np.clip(self._colores, 0.0, 1.0)
        self._tamanos = 2.0 + 3.0 * np.abs(np.sin(angulos * 2 + t))
    
    def _actualizar_metatron(self, t: float, n: int):
        """ESTADO_METATRON: ferrofluido + overlay Metatron."""
        self._actualizar_ferrofluido(t, n)
        
        # Forzar 13 particulas a los vertices del MetatronCube
        if self._metatron_vertices is not None:
            n_metatron = min(13, n // 10)
            verts = self._metatron_vertices
            for i in range(n_metatron):
                vi = i % len(verts)
                self._pos[i] = verts[vi].astype(np.float32) + np.random.randn(3).astype(np.float32) * 5.0
                self._colores[i] = np.array([0.9, 0.7, 0.2, 1.0], dtype=np.float32)
                self._tamanos[i] = 6.0
    
    def establecer_estado(self, estado: int):
        self.estado_actual = estado
        logger.debug(f"Orbe estado: {['NUCLEO','FERROFLUIDO','METATRON'][estado]}")
    
    def establecer_morph(self, morph: float):
        self._morph = max(0.0, min(1.0, morph))


if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication, QMainWindow
    import sys
    
    app = QApplication(sys.argv)
    win = QMainWindow()
    win.setWindowTitle("Orbe OpenGL - FP-156 Metatron")
    win.resize(800, 800)
    
    orbe = OrbeOpenGL()
    win.setCentralWidget(orbe)
    win.show()
    
    # Ciclo de estados
    import time
    def ciclo():
        for estado in [OrbeOpenGL.ESTADO_NUCLEO, OrbeOpenGL.ESTADO_FERROFLUIDO, OrbeOpenGL.ESTADO_METATRON]:
            orbe.establecer_estado(estado)
            QTimer.singleShot(3000, lambda e=estado: None)
            time.sleep(3)
    
    QTimer.singleShot(1000, ciclo)
    sys.exit(app.exec())


