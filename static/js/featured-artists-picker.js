(function () {
  function initPicker(root) {
    const select = root.querySelector(".artist-tag-picker__native");
    const input = root.querySelector(".artist-tag-picker__input");
    const chipsEl = root.querySelector(".artist-tag-picker__chips");
    const suggestionsEl = root.querySelector(".artist-tag-picker__suggestions");
    if (!select || !input || !chipsEl || !suggestionsEl) return;

    const catalog = Array.from(select.options)
      .filter((o) => o.value)
      .map((o) => ({ id: o.value, name: o.textContent.trim() }));

    const selected = new Set(
      Array.from(select.selectedOptions).map((o) => o.value)
    );

    function syncSelect() {
      Array.from(select.options).forEach((o) => {
        o.selected = selected.has(o.value);
      });
    }

    function hideSuggestions() {
      suggestionsEl.hidden = true;
      suggestionsEl.innerHTML = "";
    }

    function renderChips() {
      chipsEl.innerHTML = "";
      catalog.forEach((artist) => {
        if (!selected.has(artist.id)) return;
        const chip = document.createElement("span");
        chip.className = "artist-tag-picker__chip";
        chip.setAttribute("role", "listitem");
        chip.textContent = artist.name;

        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "artist-tag-picker__chip-remove";
        remove.setAttribute("aria-label", "Retirer " + artist.name);
        remove.textContent = "×";
        remove.addEventListener("click", () => {
          selected.delete(artist.id);
          syncSelect();
          renderChips();
        });

        chip.appendChild(remove);
        chipsEl.appendChild(chip);
      });
    }

    function addArtist(id) {
      if (!id || selected.has(id)) return false;
      selected.add(id);
      syncSelect();
      renderChips();
      input.value = "";
      hideSuggestions();
      input.focus();
      return true;
    }

    function showSuggestions(query) {
      const q = query.trim().toLowerCase();
      if (!q) {
        hideSuggestions();
        return;
      }
      const matches = catalog
        .filter(
          (a) =>
            !selected.has(a.id) && a.name.toLowerCase().includes(q)
        )
        .slice(0, 10);

      suggestionsEl.innerHTML = "";
      if (!matches.length) {
        hideSuggestions();
        return;
      }

      matches.forEach((artist) => {
        const li = document.createElement("li");
        const btn = document.createElement("button");
        btn.type = "button";
        btn.className = "artist-tag-picker__suggestion";
        btn.textContent = artist.name;
        btn.addEventListener("click", () => addArtist(artist.id));
        li.appendChild(btn);
        suggestionsEl.appendChild(li);
      });
      suggestionsEl.hidden = false;
    }

    function addFromInput() {
      const q = input.value.trim();
      if (!q) return;
      const exact = catalog.find(
        (a) =>
          !selected.has(a.id) && a.name.toLowerCase() === q.toLowerCase()
      );
      if (exact) {
        addArtist(exact.id);
        return;
      }
      const partial = catalog.filter(
        (a) =>
          !selected.has(a.id) && a.name.toLowerCase().includes(q.toLowerCase())
      );
      if (partial.length === 1) {
        addArtist(partial[0].id);
      }
    }

    input.addEventListener("input", () => showSuggestions(input.value));
    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        const first = suggestionsEl.querySelector(
          ".artist-tag-picker__suggestion"
        );
        if (first && !suggestionsEl.hidden) {
          const name = first.textContent.trim();
          const artist = catalog.find((a) => a.name === name);
          if (artist) addArtist(artist.id);
        } else {
          addFromInput();
        }
      } else if (e.key === "Escape") {
        hideSuggestions();
      }
    });

    document.addEventListener("click", (e) => {
      if (!root.contains(e.target)) hideSuggestions();
    });

    renderChips();
  }

  function initAll() {
    document.querySelectorAll(".artist-tag-picker").forEach(initPicker);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initAll);
  } else {
    initAll();
  }
})();
