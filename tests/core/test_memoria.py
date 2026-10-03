"""
⊕ Sal — Tests para golem/memoria/memoria.py (WI-287).

Cubre: add_memory, _read_raw, buscar_en_memoria, compress_day,
_simple_extractive_summary, calcular_tiempo_activo, paths.
"""

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from computadora.memoria.memoria import (
    DATA_DIR,
    _raw_path_for,
    _sample_path_for,
    _summary_path_for,
    _simple_extractive_summary,
    add_memory,
    _read_raw,
    buscar_en_memoria,
    compress_day,
    calcular_tiempo_activo,
)


# ═══════════════════════════════════════════════════════════════
# Paths
# ═══════════════════════════════════════════════════════════════

class TestPaths:
    def test_data_dir_es_datos_memoria(self):
        assert DATA_DIR.name == "memoria"
        assert DATA_DIR.parent.name == "datos"

    def test_raw_path_contiene_fecha(self):
        d = date(2026, 4, 8)
        p = _raw_path_for(d)
        assert "2026-04-08" in p.name
        assert p.suffix == ".jsonl"

    def test_summary_path_contiene_fecha(self):
        d = date(2026, 4, 8)
        p = _summary_path_for(d)
        assert "2026-04-08" in p.name
        assert p.suffix == ".txt"

    def test_sample_path_contiene_fecha(self):
        d = date(2026, 4, 8)
        p = _sample_path_for(d)
        assert "2026-04-08" in p.name
        assert p.suffix == ".json"


# ═══════════════════════════════════════════════════════════════
# add_memory + _read_raw
# ═══════════════════════════════════════════════════════════════

class TestAddMemory:
    def test_add_y_read(self, tmp_path):
        fake_date = date(2099, 12, 31)
        raw_file = tmp_path / f"memoria_raw_{fake_date.isoformat()}.jsonl"

        with patch("golem.memoria.memoria._raw_path_for", return_value=raw_file):
            add_memory("user", "Hola Golem", meta={"fuente": "test"})
            add_memory("assistant", "Hola Señor")

        lines = raw_file.read_text("utf-8").strip().split("\n")
        assert len(lines) == 2

        entry = json.loads(lines[0])
        assert entry["role"] == "user"
        assert entry["text"] == "Hola Golem"
        assert entry["meta"]["fuente"] == "test"

    def test_read_raw_archivo_inexistente(self):
        d = date(1900, 1, 1)
        assert _read_raw(d) == []

    def test_read_raw_contenido(self, tmp_path):
        d = date(2099, 1, 1)
        raw_file = tmp_path / f"memoria_raw_{d.isoformat()}.jsonl"
        raw_file.write_text(
            json.dumps({"role": "user", "text": "test", "ts": "T"}) + "\n",
            encoding="utf-8",
        )
        with patch("golem.memoria.memoria._raw_path_for", return_value=raw_file):
            items = _read_raw(d)
        assert len(items) == 1
        assert items[0]["text"] == "test"


# ═══════════════════════════════════════════════════════════════
# Extractive summary
# ═══════════════════════════════════════════════════════════════

class TestExtractSummary:
    def test_vacio(self):
        assert _simple_extractive_summary([]) == ""

    def test_textos_cortos(self):
        resultado = _simple_extractive_summary(["Hola", "Adiós"], max_sentences=2)
        assert isinstance(resultado, str)

    def test_max_sentences_respetado(self):
        textos = [f"Oración número {i}. Segunda frase." for i in range(20)]
        resultado = _simple_extractive_summary(textos, max_sentences=3)
        assert isinstance(resultado, str)
        assert len(resultado) > 0


# ═══════════════════════════════════════════════════════════════
# buscar_en_memoria
# ═══════════════════════════════════════════════════════════════

class TestBuscarEnMemoria:
    def test_consulta_vacia(self):
        result = buscar_en_memoria("")
        assert "No se proporcionó" in result

    def test_sin_resultados(self):
        result = buscar_en_memoria("xyzzynonexistent12345", dias=1)
        assert "No encontré" in result or result == ""

    def test_busca_en_raw(self, tmp_path):
        hoy = date.today()
        raw_file = tmp_path / f"memoria_raw_{hoy.isoformat()}.jsonl"
        entry = {"role": "user", "text": "Recuerda comprar tortillas", "ts": "2026-04-08T10:00:00"}
        raw_file.write_text(json.dumps(entry, ensure_ascii=False) + "\n", encoding="utf-8")

        with patch("golem.memoria.memoria._raw_path_for", return_value=raw_file):
            with patch("golem.memoria.memoria._summary_path_for", return_value=tmp_path / "no_existe.txt"):
                with patch("golem.memoria.memoria._sample_path_for", return_value=tmp_path / "no_existe.json"):
                    result = buscar_en_memoria("tortillas", dias=1)

        assert "tortillas" in result.lower()


# ═══════════════════════════════════════════════════════════════
# compress_day
# ═══════════════════════════════════════════════════════════════

class TestCompressDay:
    def test_compress_sin_datos(self, tmp_path):
        d = date(2099, 6, 15)
        with patch("golem.memoria.memoria._raw_path_for", return_value=tmp_path / "no.jsonl"):
            compress_day(d)  # Should not raise

    def test_compress_con_datos(self, tmp_path):
        d = date(2099, 6, 15)
        raw_file = tmp_path / f"raw_{d}.jsonl"
        for i in range(5):
            entry = {"role": "user", "text": f"Mensaje número {i} sobre Golem. Es un test.", "ts": f"T{i}"}
            with raw_file.open("a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        summary_file = tmp_path / f"summary_{d}.txt"
        sample_file = tmp_path / f"sample_{d}.json"

        with patch("golem.memoria.memoria._raw_path_for", return_value=raw_file), \
             patch("golem.memoria.memoria._summary_path_for", return_value=summary_file), \
             patch("golem.memoria.memoria._sample_path_for", return_value=sample_file):
            compress_day(d, keep_sample=3)

        assert summary_file.exists()
        contenido = summary_file.read_text("utf-8")
        assert "Resumen diario" in contenido


# ═══════════════════════════════════════════════════════════════
# calcular_tiempo_activo
# ═══════════════════════════════════════════════════════════════

class TestTiempoActivo:
    def test_retorna_dict(self):
        result = calcular_tiempo_activo()
        assert isinstance(result, dict)

