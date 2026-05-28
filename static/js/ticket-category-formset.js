(function () {
  const form = document.getElementById("ticket-category-formset");
  const container = document.getElementById("ticket-category-rows");
  const addBtn = document.getElementById("ticket-category-add-row");
  if (!form || !container || !addBtn) return;

  const totalInput = form.querySelector('input[name$="-TOTAL_FORMS"]');
  const maxInput = form.querySelector('input[name$="-MAX_NUM_FORMS"]');
  if (!totalInput) return;

  const prefix = totalInput.name.replace("-TOTAL_FORMS", "");

  function renumberRow(row, index) {
    row.dataset.formIndex = String(index);
    const title = row.querySelector(".ticket-category-row__head strong");
    if (title) title.textContent = "Catégorie " + (index + 1);

    row.querySelectorAll("input, select, textarea").forEach((el) => {
      if (!el.name) return;
      el.name = el.name.replace(new RegExp(prefix + "-\\d+-"), prefix + "-" + index + "-");
      if (el.id) {
        el.id = el.id.replace(new RegExp(prefix + "-\\d+-"), prefix + "-" + index + "-");
      }
    });
    row.querySelectorAll("label[for]").forEach((label) => {
      const f = label.getAttribute("for");
      if (f) {
        label.setAttribute(
          "for",
          f.replace(new RegExp(prefix + "-\\d+-"), prefix + "-" + index + "-")
        );
      }
    });
  }

  function clearRow(row) {
    row.querySelectorAll("input, textarea, select").forEach((el) => {
      if (el.type === "hidden") return;
      if (el.type === "checkbox") {
        el.checked = true;
        return;
      }
      if (el.type === "color") {
        el.value = "#C2410C";
        return;
      }
      el.value = "";
    });
  }

  addBtn.addEventListener("click", () => {
    const max = maxInput ? parseInt(maxInput.value, 10) : 12;
    const total = parseInt(totalInput.value, 10);
    if (total >= max) return;

    const rows = container.querySelectorAll(".ticket-category-row");
    const template = rows[rows.length - 1];
    const clone = template.cloneNode(true);
    clearRow(clone);
    container.appendChild(clone);
    totalInput.value = String(total + 1);
    renumberRow(clone, total);
  });
})();
