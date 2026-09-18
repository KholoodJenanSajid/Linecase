const form = document.getElementById("form");
const dossier = document.getElementById("dossier");
const statusEl = document.getElementById("status");
const go = document.getElementById("go");

document.querySelectorAll("[data-demo]").forEach((btn) => {
  btn.addEventListener("click", () => run({ demo: btn.dataset.demo }));
});

form.addEventListener("submit", (e) => {
  e.preventDefault();
  run({});
});

async function run({ demo }) {
  const fd = new FormData();
  fd.append("notes", document.getElementById("notes").value);
  fd.append("language", document.getElementById("language").value);
  const file = document.getElementById("image").files[0];
  if (file) fd.append("image", file);
  if (demo) fd.append("demo", demo);
  go.disabled = true;
  statusEl.textContent = "Agents: see → retrieve → act…";
  try {
    const res = await fetch("/api/case", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || res.statusText);
    render(data);
    statusEl.textContent = "";
  } catch (err) {
    statusEl.textContent = String(err.message || err);
  } finally {
    go.disabled = false;
  }
}

function render(c) {
  const wo = c.work_order;
  const offline = c.mode === "offline"
    ? `<p class="offline">Offline fixture — no Gemini call. Set GOOGLE_API_KEY and restart for a real agent run.</p>`
    : "";
  const steps = (wo.steps || [])
    .map((s) => `<li>${esc(s.action)} <small>(${esc(s.owner)})</small></li>`)
    .join("");
  const parts = (wo.parts || [])
    .map((p) => `<li><code>${esc(p.sku)}</code> ${esc(p.name)} · ${esc(p.bin)}</li>`)
    .join("") || "<li>None pulled</li>";
  const cites = (wo.citations || [])
    .map((x) => `<p class="cite"><strong>${esc(x.source)}</strong> — ${esc(x.excerpt)}</p>`)
    .join("");
  const loto = (wo.loto || []).map((x) => `<li>${esc(x)}</li>`).join("");
  dossier.innerHTML = `
    <span class="stamp">${esc(wo.severity)}</span>
    <p class="case-id">${esc(c.case_id)} · ${esc(c.plant)}</p>
    ${offline}
    <h2>${esc(wo.title)}</h2>
    <p class="sev">${esc(wo.asset_id)} · first action ~${wo.time_to_first_action_minutes} min</p>
    <h3>Scene</h3>
    <p>${esc(c.scene)}</p>
    <h3>Root cause</h3>
    <p>${esc(wo.root_cause)}</p>
    <h3>LOTO</h3>
    <ol>${loto}</ol>
    <h3>Steps</h3>
    <ol>${steps}</ol>
    <h3>Parts</h3>
    <ul>${parts}</ul>
    <h3>Citations</h3>
    ${cites || "<p>None</p>"}
    <h3>Agent trace</h3>
    <p class="trace">${(c.agent_trace || []).map(esc).join(" → ")}</p>
    <h3>CMMS payload</h3>
    <pre>${esc(JSON.stringify(wo.cmms_payload, null, 2))}</pre>
  `;
}

function esc(s) {
  return String(s ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}
