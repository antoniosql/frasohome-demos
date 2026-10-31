// FraSoHome Live · consola de la API (fase 3). Sin dependencias.
const $ = (id) => document.getElementById(id);
const show = (id, on) => $(id).classList.toggle("hidden", !on);

async function api(method, path, body) {
  const headers = { "Accept": "application/json" };
  if (method !== "GET") headers["X-FSH-CSRF"] = "1";
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const r = await fetch(path, { method, headers, body: body === undefined ? undefined : JSON.stringify(body),
    credentials: "same-origin", cache: "no-store" });
  let data = null;
  try { data = await r.json(); } catch (e) { data = null; }
  return { status: r.status, data };
}

function message(id, text, ok) {
  $(id).textContent = text || "";
  $(id).className = "msg " + (ok ? "ok" : "ko");
}

async function refresh() {
  const r = await api("GET", "/api/auth/me");
  const user = r.status === 200 ? r.data.usuario : null;
  show("sec-login", !user);
  show("sec-me", !!user);
  show("sec-password", !!user && user.debe_cambiar_contrasena);
  show("sec-probe", !!user && !user.debe_cambiar_contrasena);
  $("out-me").textContent = user ? JSON.stringify(user, null, 2) : "";
}

$("form-login").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  message("msg-login", "Entrando…", true);
  const r = await api("POST", "/api/auth/login", { login: $("login").value, password: $("password").value });
  $("password").value = "";
  if (r.status === 200) { message("msg-login", "", true); await refresh(); }
  else { message("msg-login", (r.data && r.data.error) || "No se pudo entrar.", false); }
});

$("form-password").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const r = await api("POST", "/api/auth/password", { actual: $("actual").value, nueva: $("nueva").value });
  $("actual").value = ""; $("nueva").value = "";
  if (r.status === 200) { message("msg-password", "Contraseña cambiada.", true); await refresh(); }
  else { message("msg-password", (r.data && r.data.error) || "No se pudo cambiar.", false); }
});

$("btn-logout").addEventListener("click", async () => { await api("POST", "/api/auth/logout", {}); await refresh(); });

$("btn-probe").addEventListener("click", async () => {
  const path = $("ruta").value.trim();
  if (!path.startsWith("/api/")) { message("msg-probe", "La ruta debe empezar por /api/.", false); return; }
  const r = await api("GET", path);
  message("msg-probe", "HTTP " + r.status, r.status < 400);
  $("out-probe").textContent = JSON.stringify(r.data, null, 2);
});

$("btn-salud").addEventListener("click", async () => {
  $("out-salud").textContent = "Comprobando…";
  const r = await api("GET", "/api/salud");
  $("out-salud").textContent = "HTTP " + r.status + "\n" + JSON.stringify(r.data, null, 2);
});

refresh();
