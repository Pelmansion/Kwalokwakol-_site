(function () {
  "use strict";

  var root = document.documentElement;

  function initSplash() {
    if (!root.classList.contains("kole-splash-pending")) return;

    var splash = document.getElementById("kole-splash");
    if (!splash) {
      root.classList.remove("kole-splash-pending");
      return;
    }

    var canvas = document.getElementById("kole-splash-canvas");
    var UNLOCK_MS = 1500;
    var MIN_VISIBLE_MS = 4000;
    var EXIT_MS = 1000;
    var startedAt = Date.now();
    var done = false;
    var exiting = false;
    var timer = null;
    var unlockTimer = null;
    var exitTimer = null;

    function burstParticles() {
      if (!canvas || !window.requestAnimationFrame) return;

      var rect = splash.querySelector(".kole-splash__logo-shell");
      if (!rect) return;

      var box = rect.getBoundingClientRect();
      var cx = box.left + box.width / 2;
      var cy = box.top + box.height / 2;

      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      var ctx = canvas.getContext("2d");
      if (!ctx) return;

      var colors = ["#C2410C", "#D4A24C", "#1F6B4A", "#DC2626", "#FFF8F1"];
      var particles = [];
      var i;

      for (i = 0; i < 56; i += 1) {
        var angle = (Math.PI * 2 * i) / 56 + Math.random() * 0.4;
        var speed = 2.5 + Math.random() * 5.5;
        particles.push({
          x: cx,
          y: cy,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed - 1.2,
          life: 1,
          size: 1.5 + Math.random() * 3.5,
          color: colors[i % colors.length],
        });
      }

      function frame() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        var alive = false;

        particles.forEach(function (p) {
          if (p.life <= 0) return;
          alive = true;
          p.x += p.vx;
          p.y += p.vy;
          p.vy += 0.07;
          p.vx *= 0.985;
          p.life -= 0.024;

          ctx.globalAlpha = Math.max(0, p.life);
          ctx.fillStyle = p.color;
          ctx.beginPath();
          ctx.arc(p.x, p.y, p.size * p.life, 0, Math.PI * 2);
          ctx.fill();

          if (p.size > 2.5) {
            ctx.save();
            ctx.translate(p.x, p.y);
            ctx.rotate(p.life * 6);
            ctx.fillRect(-p.size * 0.4, -p.size * 0.15, p.size * 0.8, p.size * 0.3);
            ctx.restore();
          }
        });

        if (alive) requestAnimationFrame(frame);
        else ctx.clearRect(0, 0, canvas.width, canvas.height);
      }

      requestAnimationFrame(frame);
    }

    function triggerUnlock() {
      splash.classList.add("is-unlocking");
      burstParticles();
    }

    function startExit() {
      if (done || exiting) return;
      exiting = true;

      if (timer) {
        clearTimeout(timer);
        timer = null;
      }
      if (unlockTimer) {
        clearTimeout(unlockTimer);
        unlockTimer = null;
      }

      splash.classList.add("is-exiting");
      splash.setAttribute("aria-hidden", "true");

      exitTimer = setTimeout(function () {
        done = true;
        root.classList.remove("kole-splash-pending");
        if (splash.parentNode) splash.parentNode.removeChild(splash);
      }, EXIT_MS);
    }

    function finish() {
      if (done || exiting) return;

      var elapsed = Date.now() - startedAt;
      var remaining = Math.max(0, MIN_VISIBLE_MS - elapsed);

      if (remaining > 0) {
        if (timer) clearTimeout(timer);
        timer = setTimeout(startExit, remaining);
        return;
      }

      startExit();
    }

    splash.setAttribute("aria-hidden", "false");
    splash.addEventListener("click", finish);

    document.addEventListener("keydown", function onKey(e) {
      if (e.key === "Escape" || e.key === "Enter" || e.key === " ") {
        finish();
        document.removeEventListener("keydown", onKey);
      }
    });

    unlockTimer = setTimeout(triggerUnlock, UNLOCK_MS);
    timer = setTimeout(startExit, MIN_VISIBLE_MS);
  }

  window.koleStartSplash = initSplash;
  initSplash();
})();
