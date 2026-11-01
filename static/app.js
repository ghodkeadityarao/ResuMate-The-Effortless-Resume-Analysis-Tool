/* ResuMate front end: upload without leaving the page, loading screen, score count-up,
   and the highlighted resume panel. The server also works without this script (plain form post). */
(function () {
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const app = $("#app");
  let pickedFile = null;

  // ---------- landing page ----------
  function setupForm() {
    const form = $("#form");
    if (!form) return;
    const input = $("#resume"), drop = $("#drop"), picked = $("#picked"), name = $("#pickedName"), error = $("#error");

    function show(file) {
      pickedFile = file;
      name.textContent = file ? file.name + " · " + Math.max(1, Math.round(file.size / 1024)) + " KB" : "";
      picked.classList.toggle("on", !!file);
    }
    input.addEventListener("change", () => show(input.files[0] || null));
    ["dragenter", "dragover"].forEach(e => drop.addEventListener(e, ev => { ev.preventDefault(); drop.classList.add("over"); }));
    ["dragleave", "drop"].forEach(e => drop.addEventListener(e, ev => { ev.preventDefault(); drop.classList.remove("over"); }));
    drop.addEventListener("drop", ev => {
      if (ev.dataTransfer.files.length) { input.files = ev.dataTransfer.files; show(input.files[0]); }
    });

    form.addEventListener("submit", async ev => {
      if (!window.fetch || !window.FormData) {                          // old browser: normal form post, button shows progress
        $("#go").disabled = true; $("#gotext").textContent = "Evaluating your resume…";
        return;
      }
      ev.preventDefault();
      error.hidden = true;
      const messages = ["Reading your resume", "Running 18 checks", "Matching skills and roles", "Finding your quick wins"];
      const status = $("#status"), overlay = $("#loading"), bar = $("#loadbar"), go = $("#go"), goText = $("#gotext");
      if (go.disabled) return;                                          // already evaluating
      let i = 0;
      status.textContent = messages[0] + "…";
      bar.style.width = "12%";
      overlay.classList.add("on");
      go.disabled = true; go.classList.add("busy"); goText.textContent = "Evaluating your resume…";
      const ticker = setInterval(() => {
        i = Math.min(i + 1, messages.length - 1);
        status.textContent = messages[i] + "…";
        bar.style.width = Math.min(90, 12 + 26 * (i + 1)) + "%";
      }, 550);
      const started = Date.now();
      try {
        const response = await fetch(form.action, { method: "POST", body: new FormData(form), headers: { "X-Requested-With": "fetch" } });
        bar.style.width = "100%";
        const wait = Math.max(0, 1800 - (Date.now() - started));       // let the loading animation be seen
        await new Promise(r => setTimeout(r, wait));
        if (!response.ok) {
          let message = "Something went wrong. Please try again.";
          try { message = (await response.json()).error || message; } catch (e) { /* keep the default */ }
          error.textContent = message; error.hidden = false;
        } else {
          app.innerHTML = await response.text();
          window.scrollTo({ top: 0 });
          setupReport();
        }
      } catch (e) {
        error.textContent = "Could not reach the server. Check your connection and try again."; error.hidden = false;
      } finally {
        clearInterval(ticker);
        overlay.classList.remove("on");
        go.disabled = false; go.classList.remove("busy"); goText.textContent = "Analyse my resume";
      }
    });
  }

  // ---------- report ----------
  function countUp(el) {
    const target = parseInt(el.dataset.count, 10), duration = 1500, start = performance.now();
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    (function frame(now) {
      const t = Math.min(1, (now - start) / duration), eased = 1 - Math.pow(1 - t, 3);
      el.textContent = Math.round(target * eased);
      if (t < 1) requestAnimationFrame(frame);
    })(start);
  }

  function setupReport() {
    const doc = $("#doc");
    if (!doc) return;
    $$("[data-count]").forEach(countUp);

    if (pickedFile && (pickedFile.type === "application/pdf" || /\.pdf$/i.test(pickedFile.name))) {
      $("#pdfview").src = URL.createObjectURL(pickedFile) + "#toolbar=0&navpanes=0";   // stays in this browser only
      $("#pdfTab").hidden = false;
    }
  }

  const body = () => $("#docbody");

  function clearFocus() {
    const b = body();
    if (!b) return;
    b.classList.remove("focusing");
    $$(".focus", b).forEach(n => n.classList.remove("focus"));
    $("#clearFocus").hidden = true;
  }

  function focusKey(key) {
    const b = body();
    if (!b) return;
    clearFocus();
    $("#doc").classList.remove("showpdf");
    $$("#tabs button").forEach(t => t.classList.toggle("on", t.dataset.tab === "text"));
    const lines = $$(".line", b).filter(l => (l.dataset.flags || "").split(" ").includes(key));
    if (!lines.length) return;
    b.classList.add("focusing");
    lines.forEach(l => l.classList.add("focus"));
    $$("mark", b).filter(m => m.dataset.f === key).forEach(m => m.classList.add("focus"));
    $("#clearFocus").hidden = false;
    b.scrollTo({ top: Math.max(0, lines[0].offsetTop - b.offsetTop - 80), behavior: "smooth" });
    if (window.innerWidth <= 1020) $("#doc").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  app.addEventListener("click", ev => {
    const open = ev.target.closest("[data-open]");
    if (open) {
      const f = $(`details.f[data-key="${open.dataset.open}"]`);
      if (f) { f.open = true; f.scrollIntoView({ behavior: "smooth", block: "center" }); }
      focusKey(open.dataset.open);
      return;
    }
    const show = ev.target.closest("[data-show]");
    if (show) { focusKey(show.dataset.show); return; }
    const summary = ev.target.closest("summary[data-key]");
    if (summary) {                                                      // opening a finding lights up its lines
      const details = summary.parentElement;
      if (!details.open) focusKey(summary.dataset.key); else clearFocus();
      return;
    }
    if (ev.target.id === "clearFocus") { clearFocus(); return; }
    const tab = ev.target.closest("#tabs button");
    if (tab) {
      $$("#tabs button").forEach(t => t.classList.toggle("on", t === tab));
      $("#doc").classList.toggle("showpdf", tab.dataset.tab === "pdf");
    }
  });

  setupForm();
  setupReport();
})();
