/* ── mermaid zoom / pan / fullscreen ─────────────────────────────────────
 * Zoom controls for mermaid diagram wraps in kami-flavor HTML reports.
 * Inserted as an external script alongside the generated HTML.
 * ─────────────────────────────────────────────────────────────────────── */

(function () {
  'use strict';

  var MIN_SCALE = 0.5;
  var MAX_SCALE = 5;
  var BUTTON_ZOOM_STEP = 1.4;
  var WHEEL_ZOOM_SPEED = 0.001;

  document.addEventListener('DOMContentLoaded', function () {
    var wraps = document.querySelectorAll('.md-mermaid-wrap');

    wraps.forEach(function (wrap) {
      var scale = 1;
      var translateX = 0;
      var translateY = 0;
      var isDragging = false;
      var dragStartX = 0;
      var dragStartY = 0;
      var dragOriginX = 0;
      var dragOriginY = 0;
      var mermaidEl = wrap.querySelector('.mermaid');
      if (!mermaidEl) return;

      var viewport = wrap.querySelector('.md-mermaid-viewport') || wrap;
      var zoomIn = wrap.querySelector('.zoom-in');
      var zoomOut = wrap.querySelector('.zoom-out');
      var fullscreenBtn = wrap.querySelector('.zoom-fullscreen');

      viewport.style.touchAction = 'none';

      if (zoomIn) {
        zoomIn.addEventListener('click', function (e) {
          e.stopPropagation();
          zoomAtViewportCenter(BUTTON_ZOOM_STEP);
        });
      }

      if (zoomOut) {
        zoomOut.addEventListener('click', function (e) {
          e.stopPropagation();
          zoomAtViewportCenter(1 / BUTTON_ZOOM_STEP);
        });
      }

      viewport.addEventListener('wheel', function (e) {
        if (e.deltaY === 0) return;

        e.preventDefault();
        e.stopPropagation();

        var rect = viewport.getBoundingClientRect();
        var pointerX = e.clientX - rect.left;
        var pointerY = e.clientY - rect.top;
        var factor = Math.exp(-e.deltaY * WHEEL_ZOOM_SPEED);

        zoomAtPoint(factor, pointerX, pointerY);
      }, { passive: false });

      viewport.addEventListener('pointerdown', function (e) {
        if (scale === 1) return;
        if (e.button !== undefined && e.button !== 0) return;

        isDragging = true;
        dragStartX = e.clientX;
        dragStartY = e.clientY;
        dragOriginX = translateX;
        dragOriginY = translateY;
        viewport.classList.add('dragging');

        if (viewport.setPointerCapture) {
          viewport.setPointerCapture(e.pointerId);
        }
      });

      viewport.addEventListener('pointermove', function (e) {
        if (!isDragging) return;

        translateX = dragOriginX + e.clientX - dragStartX;
        translateY = dragOriginY + e.clientY - dragStartY;
        applyZoom();
      });

      viewport.addEventListener('pointerup', endDrag);
      viewport.addEventListener('pointercancel', endDrag);
      viewport.addEventListener('pointerleave', function (e) {
        if (!isDragging || viewport.hasPointerCapture && viewport.hasPointerCapture(e.pointerId)) {
          return;
        }
        endDrag(e);
      });

      if (fullscreenBtn) {
        fullscreenBtn.addEventListener('click', function (e) {
          e.stopPropagation();
          if (wrap.requestFullscreen) {
            wrap.requestFullscreen();
          } else if (wrap.webkitRequestFullscreen) {
            wrap.webkitRequestFullscreen();
          }
        });
      }

      function zoomAtViewportCenter(factor) {
        var rect = viewport.getBoundingClientRect();
        zoomAtPoint(factor, rect.width / 2, rect.height / 2);
      }

      function zoomAtPoint(factor, pointerX, pointerY) {
        var nextScale = clamp(scale * factor, MIN_SCALE, MAX_SCALE);
        if (nextScale === scale) return;

        var contentX = (pointerX - translateX) / scale;
        var contentY = (pointerY - translateY) / scale;

        translateX = pointerX - contentX * nextScale;
        translateY = pointerY - contentY * nextScale;
        scale = nextScale;

        normalizeZoomState();
        applyZoom();
      }

      function normalizeZoomState() {
        if (Math.abs(scale - 1) < 0.01) {
          scale = 1;
          translateX = 0;
          translateY = 0;
        }
      }

      function applyZoom() {
        if (scale !== 1) {
          wrap.setAttribute('data-zoom', 'true');
          mermaidEl.style.transform = 'translate(' + translateX + 'px, ' + translateY + 'px) scale(' + scale + ')';
        } else {
          wrap.removeAttribute('data-zoom');
          mermaidEl.style.transform = '';
        }
      }

      function endDrag(e) {
        if (!isDragging) return;

        isDragging = false;
        viewport.classList.remove('dragging');

        if (viewport.releasePointerCapture && viewport.hasPointerCapture && viewport.hasPointerCapture(e.pointerId)) {
          viewport.releasePointerCapture(e.pointerId);
        }
      }

      function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
      }

      document.addEventListener('fullscreenchange', function () {
        if (!document.fullscreenElement) {
          wrap.classList.remove('fullscreen');
        }
      });
    });
  });
})();
