#!/usr/bin/env python
"""Servicio local MCP para Ollama y Continue.

Expone un endpoint HTTP simple que permite a un modelo local hacer
llamadas de herramienta seguras dentro del proyecto.

Endpoints:
  GET /health   - estado del servicio
  GET /tools    - lista de herramientas soportadas
  POST /tool    - ejecutar una herramienta
      payload: {"herramienta": "leer_archivo", "args": {"ruta": "README.md"}}
"""

import json
import sys
import traceback
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from loguru import logger
from computadora.habilidades.herramientas import HERRAMIENTAS, ejecutar_herramienta

HOST = '127.0.0.1'
PORT = 11888
MAX_BODY_BYTES = 1_000_000


class ContinueMCPHandler(BaseHTTPRequestHandler):
    def _set_headers(self, status: int = 200, content_type: str = 'application/json'):
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.end_headers()

    def _send_json(self, payload: dict, status: int = 200):
        self._set_headers(status)
        self.wfile.write(json.dumps(payload, ensure_ascii=False).encode('utf-8'))

    def _read_json(self):
        length = int(self.headers.get('Content-Length', '0'))
        if length < 1 or length > MAX_BODY_BYTES:
            raise ValueError('Payload inválido o demasiado grande')

        raw = self.rfile.read(length).decode('utf-8')
        return json.loads(raw)

    def do_GET(self):
        if self.path == '/health':
            return self._send_json({'ok': True, 'message': 'Continue MCP service alive'})

        if self.path == '/tools':
            return self._send_json({'ok': True, 'tools': sorted(list(HERRAMIENTAS))})

        self._send_json({'ok': False, 'error': 'Not found'}, status=404)

    def do_POST(self):
        if self.path != '/tool':
            return self._send_json({'ok': False, 'error': 'Not found'}, status=404)

        try:
            payload = self._read_json()
            herramienta = payload.get('herramienta')
            args = payload.get('args', {})

            if not herramienta:
                raise ValueError('Campo "herramienta" es obligatorio')
            if herramienta not in HERRAMIENTAS:
                raise ValueError(f'Herramienta desconocida: {herramienta}')
            if not isinstance(args, dict):
                raise ValueError('El campo "args" debe ser un objeto JSON')

            resultado = ejecutar_herramienta(herramienta, args)
            self._send_json({'ok': True, 'herramienta': herramienta, 'resultado': resultado})
        except Exception as exc:
            logger.exception('Error procesando /tool')
            self._send_json(
                {
                    'ok': False,
                    'error': str(exc),
                    'traceback': traceback.format_exc(),
                },
                status=500,
            )

    def log_message(self, format: str, *args):
        return


def run_server(host: str = HOST, port: int = PORT):
    server = HTTPServer((host, port), ContinueMCPHandler)
    logger.add(sys.stdout, level='INFO', format='<green>{time:HH:mm:ss}</green> <level>{message}</level>')
    logger.info('Continue MCP service running at http://%s:%d', host, port)
    logger.info('Available endpoints: GET /health, GET /tools, POST /tool')
    server.serve_forever()


if __name__ == '__main__':
    run_server()
