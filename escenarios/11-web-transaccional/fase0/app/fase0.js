// FraSoHome Live · fase 0 · comprobaciones desde el navegador (sin dependencias).
const $ = (id) => document.getElementById(id);

function mark(id, ok) {
  $(id).textContent = ok ? "Correcto" : "Falla";
  $(id).className = "state " + (ok ? "ok" : "ko");
}

$("btn-health").addEventListener("click", async () => {
  $("out-health").textContent = "Comprobando…";
  try {
    const r = await fetch("/api/health", { cache: "no-store" });
    const body = await r.json();
    $("out-health").textContent = JSON.stringify(body, null, 2);
    mark("st-health", r.ok && body.ok);
  } catch (e) {
    $("out-health").textContent = String(e);
    mark("st-health", false);
  }
});

$("btn-cookie").addEventListener("click", async () => {
  try {
    const set = await (await fetch("/api/cookie", { method: "POST", headers: { "X-FSH-CSRF": "1" } })).json();
    const visible = document.cookie.includes("fsh_fase0");
    const back = await (await fetch("/api/cookie", { cache: "no-store" })).json();
    const ok = set.ok && back.ok && back.received === set.sent && !visible;
    $("out-cookie").textContent = JSON.stringify({ enviada: set.sent, recibida: back.received,
      visible_para_javascript: visible }, null, 2);
    mark("st-cookie", ok);
  } catch (e) {
    $("out-cookie").textContent = String(e);
    mark("st-cookie", false);
  }
});

$("btn-auth").addEventListener("click", async () => {
  const results = {};
  for (const p of ["/.auth/login/github", "/.auth/login/aad"]) {
    const r = await fetch(p, { redirect: "manual", cache: "no-store" });
    results[p] = r.type === "opaqueredirect" ? "redirige (MAL)" : r.status;
  }
  // /.auth/me es interno de SWA y no se puede bloquear: debe decir que no hay nadie identificado.
  const me = await fetch("/.auth/me", { cache: "no-store" });
  let meOk = me.status === 404;
  if (me.status === 200) { const b = await me.json(); meOk = b.clientPrincipal === null; results["/.auth/me"] = b; }
  else { results["/.auth/me"] = me.status; }
  $("out-auth").textContent = JSON.stringify(results, null, 2);
  mark("st-auth", results["/.auth/login/github"] === 404 && results["/.auth/login/aad"] === 404 && meOk);
});
