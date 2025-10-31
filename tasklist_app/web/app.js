const $ = (sel) => document.querySelector(sel);

const state = {
  limit: 10,
  offset: 0,
  status: "",
  order_by: "created_at",
  order_dir: "desc",
};

async function http(url, init) {
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`);
  }
  // 204 No Content
  if (res.status === 204) return null;
  return res.json();
}

function badge(text, color = "sky") {
  return `<span class="inline-block text-xs px-2 py-0.5 rounded-full bg-${color}-100 text-${color}-800">${text}</span>`;
}

function renderItems(items, meta) {
  const list = $("#list");
  list.innerHTML = items
    .map((t) => {
      const dim = t.status === "done" ? "line-through text-slate-500" : "";
      const tags = (t.tags || []).map((x) => {
        if (x.startsWith("#")) return badge(x, "violet");
        if (x.startsWith("@")) return badge(x, "amber");
        if (x.includes("://")) return badge("link", "emerald");
        if (x.includes("@")) return badge("email", "fuchsia");
        return badge(x, "sky");
      }).join(" ");

      return `
      <li class="bg-white rounded-2xl shadow p-4 flex items-start gap-3">
        <button data-action="toggle" data-id="${t.id}"
          class="mt-0.5 p-2 rounded-lg border border-slate-300 hover:bg-slate-100"
          title="Cambiar estado">
          ${t.status === "done" ? "✅" : "⬜️"}
        </button>
        <div class="flex-1">
          <div class="flex items-center gap-2">
            <span class="text-sm text-slate-400">#${t.id}</span>
            <span class="${dim} font-medium">${escapeHtml(t.text)}</span>
          </div>
          <div class="mt-1 space-x-1">${tags}</div>
          <div class="mt-1 text-xs text-slate-400">
            ${new Date(t.created_at).toLocaleString()} · ${t.status}
          </div>
        </div>
        <div class="flex items-center gap-2">
          <button data-action="delete" data-id="${t.id}"
            class="px-3 py-1 rounded-lg border border-rose-300 text-rose-700 hover:bg-rose-50">
            Eliminar
          </button>
        </div>
      </li>`;
    })
    .join("");

  $("#meta").textContent = meta
    ? `${meta.offset + 1}-${Math.min(meta.offset + meta.limit, meta.total)} / ${meta.total}`
    : "";

  $("#prev-btn").disabled = !meta || meta.offset <= 0;
  $("#next-btn").disabled = !meta || meta.offset + meta.limit >= meta.total;
}

function escapeHtml(s) {
  return s.replace(/[&<>"']/g, (c) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[c]);
}

async function load() {
  const q = new URLSearchParams();
  q.set("limit", String(state.limit));
  q.set("offset", String(state.offset));
  if (state.status) q.set("status", state.status);
  q.set("order_by", state.order_by);
  q.set("order_dir", state.order_dir);

  const data = await http(`/tasks?${q.toString()}`);
  // data == { items, meta }
  renderItems(data.items, data.meta);
}

async function onCreate(e) {
  e.preventDefault();
  const text = $("#text-input").value.trim();
  const status = $("#status-input").value;
  const err = $("#create-error");
  err.classList.add("hidden");
  if (!text) {
    err.textContent = "El texto es obligatorio.";
    err.classList.remove("hidden");
    return;
  }
  await http("/tasks", { method: "POST", body: JSON.stringify({ text, status }) });
  $("#text-input").value = "";
  $("#status-input").value = "pending";
  // recarga primera página para ver la recién creada
  state.offset = 0;
  await load();
}

async function onListClick(e) {
  const btn = e.target.closest("button[data-action]");
  if (!btn) return;
  const id = Number(btn.dataset.id);
  const action = btn.dataset.action;

  if (action === "toggle") {
    // consulta tarea, invierte estado
    const t = await http(`/tasks/${id}`);
    const next = t.status === "pending" ? "done" : "pending";
    await http(`/tasks/${id}`, {
      method: "PUT",
      body: JSON.stringify({ status: next })
    });
    await load();
  }

  if (action === "delete") {
    if (!confirm(`¿Eliminar la tarea #${id}?`)) return;
    await http(`/tasks/${id}`, { method: "DELETE" });
    // si borramos el último de la página, mueve offset atrás
    if (state.offset > 0 && $("#list").children.length === 1) {
      state.offset = Math.max(0, state.offset - state.limit);
    }
    await load();
  }
}

function bindUI() {
  $("#create-form").addEventListener("submit", onCreate);
  $("#list").addEventListener("click", onListClick);

  $("#prev-btn").addEventListener("click", () => {
    state.offset = Math.max(0, state.offset - state.limit);
    load();
  });
  $("#next-btn").addEventListener("click", () => {
    state.offset = state.offset + state.limit;
    load();
  });

  $("#status-filter").addEventListener("change", (e) => {
    state.status = e.target.value;
    state.offset = 0;
    load();
  });
  $("#order-by").addEventListener("change", (e) => {
    state.order_by = e.target.value;
    state.offset = 0;
    load();
  });
  $("#order-dir").addEventListener("change", (e) => {
    state.order_dir = e.target.value;
    state.offset = 0;
    load();
  });
}

bindUI();
load();
