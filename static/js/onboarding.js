(function () {
  "use strict";

  var STORAGE_KEY = "kole_onboarding_v2";
  var root = document.documentElement;
  if (!root.classList.contains("kole-onboarding-pending")) return;

  var overlay = document.getElementById("kole-onboarding");
  if (!overlay) {
    root.classList.remove("kole-onboarding-pending");
    return;
  }

  var track = document.getElementById("kole-onboarding-track");
  var progressEl = document.getElementById("kole-guide-progress");
  var nextBtn = document.getElementById("kole-onboarding-next");
  var prevBtn = document.getElementById("kole-guide-prev");
  var skipBtn = document.getElementById("kole-onboarding-skip");
  var slides = overlay.querySelectorAll(".kole-guide__slide");
  var total = slides.length;
  var current = 0;
  var done = false;
  var touchStartX = 0;

  function buildProgress() {
    if (!progressEl) return;
    progressEl.innerHTML = "";
    for (var i = 0; i < total; i += 1) {
      var bar = document.createElement("span");
      bar.innerHTML = "<i></i>";
      if (i === 0) bar.classList.add("is-active");
      progressEl.appendChild(bar);
    }
  }

  function updateProgress() {
    if (!progressEl) return;
    var bars = progressEl.querySelectorAll("span");
    bars.forEach(function (bar, i) {
      bar.classList.remove("is-active", "is-done");
      if (i < current) bar.classList.add("is-done");
      if (i === current) bar.classList.add("is-active");
    });
  }

  function updateNav() {
    if (prevBtn) prevBtn.hidden = current === 0;
    if (!nextBtn) return;
    if (current >= total - 1) {
      nextBtn.innerHTML =
        "Entrer sur Kolê Group" +
        '<svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
    } else {
      nextBtn.innerHTML =
        "Suivant" +
        '<svg width="18" height="18" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5" aria-hidden="true"><path d="M5 12h14M12 5l7 7-7 7"/></svg>';
    }
  }

  function goTo(index) {
    if (index < 0 || index >= total || index === current) return;

    slides[current].classList.remove("is-active");
    slides[current].classList.add("is-leaving");
    current = index;
    slides[current].classList.add("is-active");

    window.setTimeout(function () {
      slides.forEach(function (slide, i) {
        if (i !== current) slide.classList.remove("is-leaving");
      });
    }, 400);

    updateProgress();
    updateNav();
  }

  function markSeen() {
    try {
      localStorage.setItem(STORAGE_KEY, "1");
    } catch (e) {}
  }

  function close() {
    if (done) return;
    done = true;
    markSeen();

    overlay.classList.add("is-exiting");
    overlay.setAttribute("aria-hidden", "true");

    window.setTimeout(function () {
      root.classList.remove("kole-onboarding-pending");
      if (overlay.parentNode) overlay.parentNode.removeChild(overlay);
      root.classList.add("kole-splash-pending");
      if (typeof window.koleStartSplash === "function") {
        window.koleStartSplash();
      }
    }, 700);
  }

  function next() {
    if (current >= total - 1) {
      close();
      return;
    }
    goTo(current + 1);
  }

  buildProgress();
  updateNav();
  overlay.setAttribute("aria-hidden", "false");

  if (nextBtn) nextBtn.addEventListener("click", next);
  if (prevBtn) prevBtn.addEventListener("click", function () {
    if (current > 0) goTo(current - 1);
  });
  if (skipBtn) skipBtn.addEventListener("click", close);

  document.addEventListener("keydown", function onKey(e) {
    if (done) return;
    if (e.key === "Escape") close();
    if (e.key === "ArrowRight" || e.key === "Enter") next();
    if (e.key === "ArrowLeft" && current > 0) goTo(current - 1);
  });

  if (track) {
    track.addEventListener(
      "touchstart",
      function (e) {
        touchStartX = e.changedTouches[0].screenX;
      },
      { passive: true }
    );

    track.addEventListener(
      "touchend",
      function (e) {
        var diff = e.changedTouches[0].screenX - touchStartX;
        if (Math.abs(diff) < 50) return;
        if (diff < 0) next();
        else if (current > 0) goTo(current - 1);
      },
      { passive: true }
    );
  }
})();
