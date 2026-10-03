# FP-156 — Ajuste de Balance de la Atmósfera en Maljut

## Contexto
Durante la animación del orbe 4D en Maljut, el halo de atmósfera y las partículas interiores podían expandirse demasiado al moverse, generando una apariencia desbalanceada y un aura excesivamente amplia.

## Cambios realizados
- `computadora/interfaz/animador_orbe_4d.py`
  - Reduje el radio de la aura para que dependa del tamaño del núcleo (`radio_ferrofluido`) y no del viewport completo.
  - Añadí un factor de aura (`factor_aura_radio`) para mantener el glow ajustado al orbe.
  - Pasé el límite de `radio_max_particulas` al `FerrofluidoRubedo`.

- `computadora/geometria/ferrofluido_rubedo.py`
  - Agregué un límite radial de partículas para evitar crecimiento descontrolado en movimiento.
  - Clampeé la posición de cada partícula a `radio_max_particulas` tras aplicar fuerzas.

## Resultado esperado
- Atmósfera más contenida alrededor del core de Maljut.
- Menos expansión visual de partículas cuando el orbe se desplaza.
- Mejor balance visual entre core, spikes, particles y aura.
