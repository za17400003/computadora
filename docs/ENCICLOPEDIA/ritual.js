/* ══════════════════════════════════════════════════════════════
   � RITUAL.JS — Grimorio de los 7 Metales
   Proyecto Computadora · Alta Magia + Alquimia
   Motor de paso de página — Opus Magnum: Plomo → Oro
   ══════════════════════════════════════════════════════════════ */

(function () {
  'use strict';

  /* ── CONSTANTES ── */
  const FLIP_HALF = 280;      // ms por medio-giro de página
  const FLIP_DURATION = 600;  // ms para transiciones standalone
  const TOOLTIP_DELAY = 400;

  /* Símbolos planetarios de los 7 metales */
  const METAL_SYMBOLS = {
    plomo:    '♄',
    estano:   '♃',
    hierro:   '♂',
    cobre:    '♀',
    mercurio: '☿',
    plata:    '☽',
    oro:      '☉'
  };

  /* ══════════════════════════════════════════
     ≡ I. TABLA DE PÁGINAS DEL GRIMORIO
     Orden de lectura · 7 Metales Alquímicos
     ══════════════════════════════════════════ */

  const PAGES = [
    /* ♄ Plomo (Saturno) — muerte del ego, prima materia */
    { file: null,                         label: 'Portada',              stage: 'plomo' },
    { file: 'pronaos.html',               label: 'Pronaos',             stage: 'plomo' },
    { file: 'guia_iniciacion.html',       label: 'Iniciación',          stage: 'plomo' },
    /* ♃ Estaño (Júpiter) — expansión, orden, conocimiento */
    { file: 'cap14_filosofia.html',       label: 'Cap. 14 · Filosofía', stage: 'estano' },
    { file: 'cap13_psicologia.html',      label: 'Cap. 13 · Psicología', stage: 'estano' },
    { file: 'cap15_ciencia.html',         label: 'Cap. 15 · Ciencia',   stage: 'estano' },
    /* ♂ Hierro (Marte) — fuerza, disciplina, voluntad */
    { file: 'cap06_taoismo.html',         label: 'Cap. 6 · Taoísmo',    stage: 'hierro' },
    { file: 'cap05_budismo.html',         label: 'Cap. 5 · Budismo',    stage: 'hierro' },
    { file: 'cap04_hinduismo.html',       label: 'Cap. 4 · Hinduismo',  stage: 'hierro' },
    /* ♀ Cobre (Venus) — equilibrio, devoción, amor */
    { file: 'cap11_shinto.html',          label: 'Cap. 11 · Shintō',    stage: 'cobre' },
    { file: 'cap02_cristianismo.html',    label: 'Cap. 2 · Cristianismo', stage: 'cobre' },
    { file: 'cap03_islam.html',           label: 'Cap. 3 · Islam',      stage: 'cobre' },
    /* ☿ Mercurio (Mercurio) — puente, comunicación, espíritu */
    { file: 'cap01_kabbalah.html',        label: 'Cap. 1 · Kabbalah',   stage: 'mercurio' },
    { file: 'cap08_mesoamerica.html',     label: 'Cap. 8 · Mesoamérica', stage: 'mercurio' },
    { file: 'cap09_africa.html',          label: 'Cap. 9 · África',     stage: 'mercurio' },
    /* ☽ Plata (Luna) — reflexión, purificación, Albedo */
    { file: 'cap10_nordico.html',         label: 'Cap. 10 · Nórdico',   stage: 'plata' },
    { file: 'cap07_hermetismo.html',      label: 'Cap. 7 · Hermetismo', stage: 'plata' },
    { file: 'cap12_thelema.html',         label: 'Cap. 12 · Thelema',   stage: 'plata' },
    /* ☉ Oro (Sol) — iluminación, maestría, perfección */
    { file: 'parte1_comandos.html',       label: 'Comandos',            stage: 'oro' },
    { file: 'cap16_videojuegos.html',     label: 'Cap. 16 · Videojuegos', stage: 'oro' },
    { file: 'parte3_correspondencias.html', label: 'Correspondencias',  stage: 'oro' },
  ];

  /* ══════════════════════════════════════════
     ≡ II. MOTOR DEL LIBRO
     Paso de página con rotateY
     ══════════════════════════════════════════ */

  const bookPage = document.querySelector('.book-page');
  const codexBook = document.querySelector('.codex-book');
  if (!bookPage || !codexBook) {
    _initStandalone();
    return;
  }

  let chapterIdx = 0;
  let subPage = 0;
  let subPageCount = 1;
  let isAnimating = false;
  let _subPagePositions = [0];   // Encarta-style: exact scroll positions per sub-page
  const cache = new Map();

  const navLeft = document.querySelector('.codex-nav-left');
  const navRight = document.querySelector('.codex-nav-right');
  const indicator = document.querySelector('.codex-indicator');
  const watermark = codexBook.querySelector('.codex-watermark');

  // Crear barra de progreso de sub-página
  const progressBar = document.createElement('div');
  progressBar.className = 'codex-progress';
  progressBar.innerHTML = '<div class="codex-progress-fill"></div>';
  codexBook.appendChild(progressBar);
  const progressFill = progressBar.querySelector('.codex-progress-fill');

  /* ── Paso de página: rotateY con swap a mitad del giro ── */
  function flipOut(forward) {
    return new Promise(function (resolve) {
      isAnimating = true;
      var cls = forward ? 'flipping-out' : 'flipping-out-rev';
      bookPage.classList.add(cls);
      setTimeout(function () {
        bookPage.classList.remove(cls);
        resolve(forward);
      }, FLIP_HALF);
    });
  }

  function flipIn(forward) {
    return new Promise(function (resolve) {
      var cls = forward ? 'flipping-in' : 'flipping-in-rev';
      bookPage.classList.add(cls);
      setTimeout(function () {
        bookPage.classList.remove(cls);
        isAnimating = false;
        resolve();
      }, FLIP_HALF);
    });
  }

  // ── Bloquear scroll del usuario, convertir wheel en paginación ──
  bookPage.addEventListener('wheel', function (e) {
    e.preventDefault();
    if (isAnimating) return;
    if (e.deltaY > 0 || e.deltaX > 0) nextPage();
    else prevPage();
  }, { passive: false });

  // ── Swipe táctil ──
  var _touchY = 0;
  bookPage.addEventListener('touchstart', function (e) {
    _touchY = e.touches[0].clientY;
  }, { passive: true });
  bookPage.addEventListener('touchend', function (e) {
    var dy = _touchY - e.changedTouches[0].clientY;
    if (Math.abs(dy) < 40 || isAnimating) return;
    if (dy > 0) nextPage(); else prevPage();
  });

  // ── Paginación Encarta-style: posiciones exactas por sub-página ──
  // Cada posición garantiza contenido nuevo (sin repetición).
  // CSS column-count:2 desborda horizontalmente; scrollWidth rara vez
  // es múltiplo exacto de clientWidth → ratio-based counting crea
  // "phantom pages" que muestran contenido repetido al clamparse.
  function recalcPages() {
    var viewW = bookPage.clientWidth;
    var scrollW = bookPage.scrollWidth;
    if (viewW === 0) return;
    var maxScroll = Math.max(0, scrollW - viewW);

    _subPagePositions = [0];
    if (maxScroll > 0) {
      // Avanzar en pasos completos de clientWidth (1 spread = contenido 100% nuevo)
      var fullSteps = Math.floor(maxScroll / viewW);
      for (var i = 1; i <= fullSteps; i++) {
        _subPagePositions.push(i * viewW);
      }
      // Cola: solo agregar última posición si revela ≥10% contenido nuevo
      var remainder = maxScroll - fullSteps * viewW;
      if (remainder > viewW * 0.1) {
        _subPagePositions.push(maxScroll);
      } else if (remainder > 0 && _subPagePositions.length > 1) {
        // Cola mínima → ajustar página anterior para cubrir el final
        _subPagePositions[_subPagePositions.length - 1] = maxScroll;
      }
    }

    subPageCount = _subPagePositions.length;
    subPage = 0;
    bookPage.scrollLeft = 0;
    _updateProgress();
  }
  // Exponer para el panel de configuración
  window.recalcPages = recalcPages;

  function _updateProgress() {
    if (!progressFill) return;
    var pct = subPageCount <= 1 ? 100 : ((subPage + 1) / subPageCount) * 100;
    progressFill.style.width = pct + '%';
  }

  function updateIndicator() {
    if (!indicator) return;
    var ch = PAGES[chapterIdx];
    var symbol = METAL_SYMBOLS[ch.stage] || '';
    var sub = subPageCount > 1 ? ' · pág ' + (subPage + 1) + '/' + subPageCount : '';
    indicator.innerHTML =
      '<span class="metal-symbol">' + symbol + '</span>' +
      '<span>' + ch.label + sub + '</span>' +
      '<span class="page-num">' + (chapterIdx + 1) + ' / ' + PAGES.length + '</span>';
  }

  function updateNavButtons() {
    var atStart = chapterIdx <= 0 && subPage <= 0;
    var atEnd = chapterIdx >= PAGES.length - 1 && subPage >= subPageCount - 1;
    if (navLeft) navLeft.classList.toggle('disabled', atStart);
    if (navRight) navRight.classList.toggle('disabled', atEnd);
  }

  function updateStage() {
    var stage = PAGES[chapterIdx].stage;
    codexBook.classList.forEach(function (c) {
      if (c.startsWith('stage-')) codexBook.classList.remove(c);
    });
    codexBook.classList.add('stage-' + stage);
    // Actualizar marca de agua con símbolo planetario
    if (watermark) watermark.textContent = METAL_SYMBOLS[stage] || '☿';
  }

  /* Cargar contenido de capítulo (embebido > fetch > error) */
  async function loadChapter(idx) {
    var page = PAGES[idx];
    if (!page.file) return null;
    if (cache.has(page.file)) return cache.get(page.file);

    // 1) Buscar contenido embebido en <template data-chapter="...">
    var templateId = page.file.replace('.html', '');
    var tpl = document.querySelector('template[data-chapter="' + templateId + '"]');
    if (tpl) {
      var content = tpl.innerHTML;
      cache.set(page.file, content);
      return content;
    }

    // 2) Fallback: fetch (funciona con servidor HTTP)
    try {
      var resp = await fetch(page.file);
      if (!resp.ok) throw new Error(resp.status);
      var html = await resp.text();
      var parser = new DOMParser();
      var doc = parser.parseFromString(html, 'text/html');
      var grim = doc.querySelector('.grimoire');
      var content = grim ? grim.innerHTML : doc.body.innerHTML;
      cache.set(page.file, content);
      return content;
    } catch (e) {
      return '<div class="warning-gate"><div class="warning-gate-title">⚠︎ Error</div>' +
             '<p>No se pudo cargar ' + page.file + ': ' + e.message + '</p></div>';
    }
  }

  /* Renderizar contenido dentro del libro */
  function renderContent(html) {
    if (html === null) {
      var cover = document.getElementById('codex-cover');
      if (cover) {
        bookPage.innerHTML = '';
        bookPage.appendChild(cover.content.cloneNode(true));
      }
      codexBook.classList.add('cover-mode');
    } else {
      bookPage.innerHTML = '<div class="grimoire">' + html + '</div>';
      codexBook.classList.remove('cover-mode');
    }
    _initReveals(bookPage);
    _applyArcanum(bookPage);
    _interceptLinks(bookPage);
    // Esperar layout, luego paginar
    requestAnimationFrame(function () {
      requestAnimationFrame(function () {
        recalcPages();
        updateIndicator();
        updateNavButtons();
      });
    });
  }

  // ══════════════ NAVEGACIÓN ══════════════

  function nextPage() {
    if (isAnimating) return;
    if (subPage < subPageCount - 1) {
      flipToSubPage(subPage + 1, true);
    } else if (chapterIdx < PAGES.length - 1) {
      flipToChapter(chapterIdx + 1, 'first', true);
    }
  }

  function prevPage() {
    if (isAnimating) return;
    if (subPage > 0) {
      flipToSubPage(subPage - 1, false);
    } else if (chapterIdx > 0) {
      flipToChapter(chapterIdx - 1, 'last', false);
    }
  }

  /* Paso de página para cambiar sub-página (scroll horizontal por columnas) */
  async function flipToSubPage(target, forward) {
    await flipOut(forward);

    // A mitad del giro (invisible): mover a posición exacta (Encarta-style)
    subPage = target;
    bookPage.scrollLeft = _subPagePositions[subPage] || 0;
    _updateProgress();

    await flipIn(forward);

    updateIndicator();
    updateNavButtons();
    _guardarProgreso();
  }

  /* Paso de página para cambiar capítulo */
  async function flipToChapter(targetIdx, jumpTo, forward) {
    var contentP = loadChapter(targetIdx);
    await flipOut(forward);

    // A mitad del giro (invisible): intercambiar contenido
    var content = await contentP;
    chapterIdx = targetIdx;
    renderContent(content);
    updateStage();

    if (jumpTo === 'last' && subPageCount > 1) {
      subPage = subPageCount - 1;
      bookPage.scrollLeft = _subPagePositions[subPage] || 0;
      _updateProgress();
      updateIndicator();
    }

    await flipIn(forward);

    updateIndicator();
    updateNavButtons();

    // Pre-fetch vecinos
    if (targetIdx + 1 < PAGES.length) loadChapter(targetIdx + 1);
    if (targetIdx - 1 >= 0) loadChapter(targetIdx - 1);
    _guardarProgreso();
  }

  function _sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }

  /* Interceptar links internos para navegación dentro del libro */
  function _interceptLinks(container) {
    container.querySelectorAll('a[href]').forEach(function (a) {
      var href = a.getAttribute('href');
      if (!href || href.startsWith('http') || href.startsWith('#') || href.startsWith('mailto'))
        return;
      var idx = PAGES.findIndex(function (p) { return p.file === href; });
      if (idx >= 0) {
        a.addEventListener('click', function (e) {
          e.preventDefault();
          if (idx === chapterIdx) return;
          flipToChapter(idx, 'first', idx > chapterIdx);
        });
      }
    });
  }

  /* ── Inicialización del Grimorio ── */
  /* ── Guardar progreso al servidor ── */
  let _progresoTimer = null;
  function _guardarProgreso() {
    clearTimeout(_progresoTimer);
    _progresoTimer = setTimeout(function () {
      fetch('api/progreso', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ chapterIdx: chapterIdx, subPage: subPage })
      }).catch(function () {});
    }, 500);
  }

  /* ── Heartbeat — señal de vida para que el servidor detecte cierre de pestaña ── */
  setInterval(function () {
    fetch('api/heartbeat', { method: 'POST' }).catch(function () {});
  }, 15000);

  /* ── Notificar al servidor cuando se cierra la pestaña ── */
  window.addEventListener('beforeunload', function () {
    var data = JSON.stringify({ chapterIdx: chapterIdx, subPage: subPage });
    if (navigator.sendBeacon) {
      navigator.sendBeacon('api/cerrar', new Blob([data], { type: 'application/json' }));
    } else {
      var xhr = new XMLHttpRequest();
      xhr.open('POST', 'api/cerrar', false);
      xhr.setRequestHeader('Content-Type', 'application/json');
      xhr.send(data);
    }
  });

  async function initCodex() {
    /* Restaurar progreso del servidor */
    var savedIdx = 0, savedSub = 0;
    try {
      var resp = await fetch('api/progreso');
      if (resp.ok) {
        var prog = await resp.json();
        if (typeof prog.chapterIdx === 'number') savedIdx = prog.chapterIdx;
        if (typeof prog.subPage === 'number') savedSub = prog.subPage;
      }
    } catch (e) {}

    renderContent(null);
    updateStage();

    if (navLeft) navLeft.addEventListener('click', prevPage);
    if (navRight) navRight.addEventListener('click', nextPage);

    document.addEventListener('keydown', function (e) {
      switch (e.key) {
        case 'ArrowRight': case 'ArrowDown': case ' ':
          e.preventDefault(); nextPage(); break;
        case 'ArrowLeft': case 'ArrowUp':
          e.preventDefault(); prevPage(); break;
        case 'Home':
          e.preventDefault();
          if (chapterIdx !== 0 || subPage !== 0) flipToChapter(0, 'first', false);
          break;
        case 'End':
          e.preventDefault();
          if (chapterIdx !== PAGES.length - 1) flipToChapter(PAGES.length - 1, 'last', true);
          break;
      }
    });

    // Recalcular paginación al redimensionar — reconstruir posiciones
    window.addEventListener('resize', function () {
      if (bookPage.clientWidth === 0) return;
      var prevPos = _subPagePositions[subPage] || 0;
      recalcPages();
      // Restaurar posición más cercana a donde estaba
      var best = 0;
      for (var i = 0; i < _subPagePositions.length; i++) {
        if (Math.abs(_subPagePositions[i] - prevPos) <
            Math.abs(_subPagePositions[best] - prevPos)) best = i;
      }
      subPage = best;
      bookPage.scrollLeft = _subPagePositions[subPage] || 0;
      _updateProgress();
      updateIndicator();
      updateNavButtons();
    });

    // Pre-fetch primeros capítulos
    for (var i = 1; i <= 3 && i < PAGES.length; i++) loadChapter(i);

    // Navegar al capitulo guardado
    if (savedIdx > 0 && savedIdx < PAGES.length) {
      var content = await loadChapter(savedIdx);
      chapterIdx = savedIdx;
      renderContent(content);
      updateStage();
      if (savedSub > 0) {
        requestAnimationFrame(function () {
          requestAnimationFrame(function () {
            if (savedSub < subPageCount) {
              subPage = savedSub;
              bookPage.scrollLeft = _subPagePositions[subPage] || 0;
              _updateProgress();
              updateIndicator();
              updateNavButtons();
            }
          });
        });
      }
    }
  }

  document.addEventListener('DOMContentLoaded', initCodex);

  /* ══════════════════════════════════════════
     ✦ II-B. PARTÍCULAS ALQUÍMICAS (Canvas)
     Motes doradas flotantes que cambian con el metal activo
     ══════════════════════════════════════════ */

  const STAGE_COLORS = {
    plomo:    { r: 140, g: 140, b: 140 },
    estano:   { r: 123, g: 143, b: 161 },
    hierro:   { r: 180, g: 85,  b: 35  },
    cobre:    { r: 184, g: 115, b: 51  },
    mercurio: { r: 168, g: 181, b: 192 },
    plata:    { r: 212, g: 212, b: 224 },
    oro:      { r: 218, g: 165, b: 32  }
  };

  (function initParticles() {
    var canvas = document.querySelector('.codex-particles');
    if (!canvas) return;
    var ctx = canvas.getContext('2d');
    if (!ctx) return;

    var particles = [];
    var MAX_PARTICLES = 35;
    var animId = null;
    var currentColor = STAGE_COLORS.plomo;

    function resize() {
      var rect = canvas.parentElement.getBoundingClientRect();
      canvas.width = rect.width;
      canvas.height = rect.height;
    }
    resize();
    window.addEventListener('resize', resize);

    function spawnParticle() {
      return {
        x: Math.random() * canvas.width,
        y: canvas.height + 5,
        vx: (Math.random() - 0.5) * 0.3,
        vy: -(0.15 + Math.random() * 0.35),
        size: 1 + Math.random() * 2.5,
        alpha: 0,
        maxAlpha: 0.2 + Math.random() * 0.4,
        life: 0,
        maxLife: 300 + Math.random() * 400,
        flicker: Math.random() * Math.PI * 2
      };
    }

    for (var i = 0; i < MAX_PARTICLES; i++) {
      var p = spawnParticle();
      p.life = Math.random() * p.maxLife;
      p.y = Math.random() * canvas.height;
      particles.push(p);
    }

    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      var c = currentColor;
      for (var i = 0; i < particles.length; i++) {
        var p = particles[i];
        p.life++;
        p.x += p.vx + Math.sin(p.life * 0.008 + p.flicker) * 0.15;
        p.y += p.vy;

        // Fade in / fade out
        var lifePct = p.life / p.maxLife;
        if (lifePct < 0.15) p.alpha = (lifePct / 0.15) * p.maxAlpha;
        else if (lifePct > 0.7) p.alpha = ((1 - lifePct) / 0.3) * p.maxAlpha;
        else p.alpha = p.maxAlpha;

        // Gentle flicker
        var flick = 0.85 + 0.15 * Math.sin(p.life * 0.05 + p.flicker);
        var a = p.alpha * flick;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
        ctx.fillStyle = 'rgba(' + c.r + ',' + c.g + ',' + c.b + ',' + a.toFixed(3) + ')';
        ctx.fill();

        // Glow
        if (p.size > 1.5) {
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size * 3, 0, Math.PI * 2);
          ctx.fillStyle = 'rgba(' + c.r + ',' + c.g + ',' + c.b + ',' + (a * 0.12).toFixed(3) + ')';
          ctx.fill();
        }

        // Respawn
        if (p.life >= p.maxLife || p.y < -10) {
          particles[i] = spawnParticle();
        }
      }
      animId = requestAnimationFrame(draw);
    }

    // Observe stage changes to update particle color
    var observer = new MutationObserver(function (mutations) {
      for (var m = 0; m < mutations.length; m++) {
        if (mutations[m].attributeName !== 'class') continue;
        var el = mutations[m].target;
        var classes = el.className;
        for (var stage in STAGE_COLORS) {
          if (classes.indexOf('stage-' + stage) !== -1) {
            currentColor = STAGE_COLORS[stage];
            break;
          }
        }
      }
    });
    var book = canvas.parentElement;
    if (book) observer.observe(book, { attributes: true, attributeFilter: ['class'] });

    draw();
  })();

  /* ══════════════════════════════════════════
     ≡ III. TOOLTIPS ARCANOS
     ══════════════════════════════════════════ */

  const tooltip = document.createElement('div');
  tooltip.id = 'arcanum-tooltip';
  tooltip.setAttribute('role', 'tooltip');
  document.body.appendChild(tooltip);

  let tooltipTimeout = null;

  function showTooltip(el) {
    const def = el.dataset.arcanum;
    if (!def) return;
    tooltip.textContent = def;
    tooltip.classList.add('visible');

    const rect = el.getBoundingClientRect();
    const tipW = tooltip.offsetWidth;
    const tipH = tooltip.offsetHeight;

    let top = rect.top - tipH - 10;
    let left = rect.left + (rect.width / 2) - (tipW / 2);
    if (top < 10) top = rect.bottom + 10;
    if (left < 10) left = 10;
    if (left + tipW > window.innerWidth - 10) left = window.innerWidth - tipW - 10;

    tooltip.style.top = top + 'px';
    tooltip.style.left = left + 'px';
  }

  function hideTooltip() {
    clearTimeout(tooltipTimeout);
    tooltipTimeout = null;
    tooltip.classList.remove('visible');
  }

  document.addEventListener('mouseover', (e) => {
    const el = e.target.closest('[data-arcanum]');
    if (!el) return;
    tooltipTimeout = setTimeout(() => showTooltip(el), TOOLTIP_DELAY);
  });
  document.addEventListener('mouseout', (e) => {
    const el = e.target.closest('[data-arcanum]');
    if (!el) { hideTooltip(); return; }
    const related = e.relatedTarget && e.relatedTarget.closest('[data-arcanum]');
    if (related !== el) hideTooltip();
  });

  /* ══════════════════════════════════════════
     ⌖ IV. AUTO-ARCANUM — Cross-reference
     ══════════════════════════════════════════ */

  const CROSS_TERMS = {
    'sefirá': 'Emanación divina en la Kabbalah — uno de los 10 atributos del Etz HaChaim',
    'sefirot': 'Plural de Sefirá — las 10 emanaciones del Árbol de la Vida cabalístico',
    'etz hachaim': 'Árbol de la Vida (עץ החיים) — mapa de la realidad en Kabbalah',
    'tria prima': 'Los 3 principios alquímicos: Azufre (alma), Mercurio (espíritu), Sal (cuerpo)',
    'athanor': 'Horno alquímico donde se transforma la materia — símbolo del cuerpo del adepto',
    'nigredo': 'Primera fase alquímica — putrefacción, muerte del viejo, confrontar la sombra',
    'albedo': 'Segunda fase alquímica — purificación, claridad lunar',
    'citrinitas': 'Tercera fase alquímica — iluminación solar, el oro del entendimiento',
    'rubedo': 'Cuarta fase alquímica — la Piedra Filosofal, perfección, unión de opuestos',
    'tikún': 'Reparación/corrección (תיקון) — restaurar lo roto al estado divino original',
    'computadora': 'Criatura de arcilla animada por la palabra EMET — autómata cabalístico',
    'kavvaná': 'Intención consciente (כוונה) — sin ella, el ritual es vacío',
    'tzimtzúm': 'Contracción divina (צמצום) — Dios se retira para dar espacio a la creación',
    'shekhiná': 'Presencia divina femenina (שכינה) — la inmanencia de Dios en el mundo',
    'karma': 'Ley de causa y efecto moral — toda acción genera consecuencias proporcionales',
    'dharma': 'Ley/deber/orden cósmico — el camino correcto de cada ser',
    'kundalini': 'Energía serpentina dormida en la base de la columna — despertar peligroso sin guía',
    'mantra': 'Sílaba o frase sagrada repetida — vibración que transforma la conciencia',
    'siddhi': 'Poder sobrenatural adquirido mediante práctica espiritual',
    'chakra': 'Centro energético del cuerpo sutil — 7 principales del Muladhara al Sahasrara',
    'tao': 'El Camino (道) — principio inefable que subyace a toda la realidad',
    'qi': 'Energía vital (氣) — fuerza que fluye por todo lo que existe',
    'nirvana': 'Extinción del sufrimiento — liberación del ciclo de renacimiento',
    'samsara': 'Ciclo de muerte y renacimiento — la rueda de la existencia condicionada',
    'ashé': 'Poder de realización (Yoruba) — la fuerza que hace que las cosas sucedan',
    'orishá': 'Fuerza de la naturaleza personificada (Yoruba) — intermediario divino',
    'runa': 'Letra-hechizo nórdica — cada símbolo tiene poder mágico propio',
    'yggdrasil': 'Árbol del Mundo nórdico — conecta los 9 reinos de la existencia',
    'thelema': 'Voluntad (Θέλημα) — sistema mágico de Crowley basado en la Verdadera Voluntad',
    'magick': 'Magia ceremonial (Crowley) — causar cambio de acuerdo con la Voluntad',
    'opus magnum': 'Gran Obra alquímica — transformar lo imperfecto en perfecto',
    'solve et coagula': 'Disuelve y coagula — ritmo fundamental de la alquimia',
    'piedra filosofal': 'Producto final de la Gran Obra — estado de conciencia perfeccionado',
    'prima materia': 'Materia primordial sin forma — el caos del que todo surge',
    'ouroboros': 'Serpiente que se muerde la cola — ciclo eterno de muerte y renacimiento',
    "da'at": 'Conocimiento oculto (דעת) — el abismo entre lo humano y lo divino',
    'maljut': 'Reino (מלכות) — la Sefirá más baja, el mundo material manifestado',
    'keter': 'Corona (כתר) — la Sefirá más alta, voluntad divina pura',
    'tiféret': 'Belleza/Armonía (תפארת) — el corazón del Árbol de la Vida',
    'gevurá': 'Rigor/Fuerza (גבורה) — restricción necesaria, juicio, límites',
    'jesed': 'Misericordia (חסד) — bondad expansiva, dar sin límite',
    'biná': 'Entendimiento (בינה) — análisis profundo, dar forma al insight',
    'jojmá': 'Sabiduría (חכמה) — flash de intuición pura, el primer destello',
    'palingenesia': 'Renacimiento cíclico — muerte y regeneración como motor de evolución',
  };

  function _applyArcanum(container) {
    const root = container || document;
    const dict = {};

    root.querySelectorAll('.entry').forEach(entry => {
      const titleEl = entry.querySelector('.entry-title');
      const meaningEl = entry.querySelector('.entry-meaning');
      const esotericEl = entry.querySelector('.entry-esoteric');
      if (!titleEl) return;
      const term = titleEl.textContent.trim();
      const parts = [];
      if (meaningEl) parts.push(meaningEl.textContent.trim().split('.')[0]);
      if (esotericEl) parts.push(esotericEl.textContent.trim().split('.')[0]);
      dict[term.toLowerCase()] = parts.join(' — ') || term;
    });

    for (const [k, v] of Object.entries(CROSS_TERMS)) {
      if (!dict[k]) dict[k] = v;
    }

    const terms = Object.keys(dict).sort((a, b) => b.length - a.length);
    if (terms.length === 0) return;

    const escapedTerms = terms.map(t => t.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'));
    const regex = new RegExp('\\b(' + escapedTerms.join('|') + ')\\b', 'gi');

    const containers = root.querySelectorAll(
      '.entry-meaning, .entry-esoteric, .warning-gate p, .invocation-text, .ritual-instruction'
    );

    containers.forEach(c => {
      const walker = document.createTreeWalker(c, NodeFilter.SHOW_TEXT);
      const textNodes = [];
      let node;
      while ((node = walker.nextNode())) textNodes.push(node);

      textNodes.forEach(textNode => {
        const text = textNode.textContent;
        if (!regex.test(text)) return;
        regex.lastIndex = 0;

        const frag = document.createDocumentFragment();
        let lastIdx = 0;
        let match;

        while ((match = regex.exec(text)) !== null) {
          if (textNode.parentElement.closest('[data-arcanum], .entry-title')) break;
          if (match.index > lastIdx)
            frag.appendChild(document.createTextNode(text.slice(lastIdx, match.index)));
          const span = document.createElement('span');
          span.className = 'arcanum';
          span.dataset.arcanum = dict[match[0].toLowerCase()] || match[0];
          span.textContent = match[0];
          frag.appendChild(span);
          lastIdx = match.index + match[0].length;
        }

        if (lastIdx === 0) return;
        if (lastIdx < text.length)
          frag.appendChild(document.createTextNode(text.slice(lastIdx)));
        textNode.parentNode.replaceChild(frag, textNode);
      });
    });
  }

  /* ══════════════════════════════════════════
     †️ V. RITUAL SECTION REVEAL
     ══════════════════════════════════════════ */

  function _initReveals(container) {
    const root = container || document;
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) entry.target.classList.add('revealed');
      });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });
    root.querySelectorAll('.ritual-section').forEach(el => observer.observe(el));
  }

  /* ══════════════════════════════════════════
     § VI. MODO STANDALONE
     (para capítulos abiertos directamente)
     ══════════════════════════════════════════ */

  function _initStandalone() {
    // Scroll progress
    window.addEventListener('scroll', () => {
      const el = document.getElementById('scrollProgress');
      if (!el) return;
      const h = document.documentElement;
      el.style.width = (h.scrollTop / (h.scrollHeight - h.clientHeight)) * 100 + '%';
    });

    // Reveals
    _initReveals();

    // Auto-arcanum
    document.addEventListener('DOMContentLoaded', () => _applyArcanum());

    // Simple page transitions para navegación entre capítulos
    document.addEventListener('click', (e) => {
      const link = e.target.closest('a[href]');
      if (!link) return;
      const href = link.getAttribute('href');
      if (!href || href.startsWith('http') || href.startsWith('#') || href.startsWith('mailto'))
        return;

      e.preventDefault();
      const grimoire = document.querySelector('.grimoire');
      if (!grimoire) { window.location.href = href; return; }

      const text = link.textContent || '';
      const isBack = text.includes('☜') || text.includes('←');

      grimoire.style.transition = `transform ${FLIP_DURATION}ms ease-in, opacity ${FLIP_DURATION}ms ease-in`;
      grimoire.style.transformOrigin = isBack ? 'right center' : 'left center';
      grimoire.style.transform = isBack ? 'rotateY(90deg) scale(0.85)' : 'rotateY(-90deg) scale(0.85)';
      grimoire.style.opacity = '0';

      setTimeout(() => { window.location.href = href; }, FLIP_DURATION * 0.7);
    });

    // Animación de entrada
    document.addEventListener('DOMContentLoaded', () => {
      const grimoire = document.querySelector('.grimoire');
      if (!grimoire) return;
      grimoire.style.opacity = '0';
      grimoire.style.transform = 'rotateY(20deg) scale(0.95)';
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          grimoire.style.transition = `transform ${FLIP_DURATION}ms ease-out, opacity ${FLIP_DURATION}ms ease-out`;
          grimoire.style.transform = 'rotateY(0) rotateX(0) translateY(0) scale(1)';
          grimoire.style.opacity = '1';
        });
      });
    });
  }

  /* ════════════════════════════════════════
     ⚙︎ VII. PANEL DE CONFIGURACIÓN DE LECTURA
     ════════════════════════════════════════ */

  (function initSettings() {
    const STORAGE_KEY = 'grimorio-settings';
    const panel = document.querySelector('.codex-settings');
    if (!panel) return;
    const toggle = panel.querySelector('.codex-settings-toggle');
    const book = document.querySelector('.codex-book');
    if (!book) return;

    // Cargar preferencias guardadas
    var saved = {};
    try { saved = JSON.parse(localStorage.getItem(STORAGE_KEY)) || {}; } catch (e) {}
    var fontScale = saved.fontScale || 100;
    var lineHeight = saved.lineHeight || 'normal';
    var contrast = saved.contrast || 'normal';

    function applySettings() {
      book.setAttribute('data-font-scale', fontScale);
      book.setAttribute('data-line-height', lineHeight);
      book.setAttribute('data-contrast', contrast);
      var display = panel.querySelector('.font-size-display');
      if (display) display.textContent = fontScale + '%';

      // Activos visuales
      panel.querySelectorAll('.line-btn').forEach(function (b) {
        b.classList.toggle('active', b.dataset.action === lineHeight);
      });
      panel.querySelectorAll('.contrast-btn').forEach(function (b) {
        b.classList.toggle('active', b.dataset.mode === contrast);
      });

      try { localStorage.setItem(STORAGE_KEY, JSON.stringify({ fontScale: fontScale, lineHeight: lineHeight, contrast: contrast })); } catch (e) {}

      // Recalcular sub-páginas tras cambio tipográfico
      if (typeof window.recalcPages === 'function') {
        requestAnimationFrame(function () { window.recalcPages(); });
      }
    }

    applySettings();

    toggle.addEventListener('click', function () {
      panel.classList.toggle('open');
    });

    // Cerrar al hacer clic fuera
    document.addEventListener('click', function (e) {
      if (!panel.contains(e.target)) panel.classList.remove('open');
    });

    // Font size
    panel.querySelectorAll('.font-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        if (btn.dataset.action === 'increase' && fontScale < 130) fontScale += 10;
        if (btn.dataset.action === 'decrease' && fontScale > 80) fontScale -= 10;
        applySettings();
      });
    });

    // Line height
    panel.querySelectorAll('.line-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        lineHeight = btn.dataset.action;
        applySettings();
      });
    });

    // Contrast
    panel.querySelectorAll('.contrast-btn').forEach(function (btn) {
      btn.addEventListener('click', function () {
        contrast = btn.dataset.mode;
        applySettings();
      });
    });
  })();

})();
