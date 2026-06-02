/* ── mermaid zoom / pan / fullscreen ─────────────────────────────────────
 * Zoom controls for mermaid diagram wraps in kami-flavor HTML reports.
 * Inserted as an external script alongside the generated HTML.
 * ─────────────────────────────────────────────────────────────────────── */

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var wraps = document.querySelectorAll('.md-mermaid-wrap');

    wraps.forEach(function (wrap) {
      var scale = 1;
      var mermaidEl = wrap.querySelector('.mermaid');
      if (!mermaidEl) return;

      var zoomIn = wrap.querySelector('.zoom-in');
      var zoomOut = wrap.querySelector('.zoom-out');
      var fullscreenBtn = wrap.querySelector('.zoom-fullscreen');

      if (zoomIn) {
        zoomIn.addEventListener('click', function (e) {
          e.stopPropagation();
          scale = Math.min(scale * 1.4, 5);
          applyZoom();
        });
      }

      if (zoomOut) {
        zoomOut.addEventListener('click', function (e) {
          e.stopPropagation();
          scale = Math.max(scale / 1.4, 0.5);
          applyZoom();
        });
      }

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

      function applyZoom() {
        if (scale !== 1) {
          wrap.setAttribute('data-zoom', 'true');
          mermaidEl.style.transform = 'scale(' + scale + ')';
        } else {
          wrap.removeAttribute('data-zoom');
          mermaidEl.style.transform = '';
        }
      }

      document.addEventListener('fullscreenchange', function () {
        if (!document.fullscreenElement) {
          wrap.classList.remove('fullscreen');
        }
      });
    });
  });
})();
