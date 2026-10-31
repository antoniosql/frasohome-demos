// FraSoHome Live · arranque: cabecera, menú por rol y enrutador por hash (#/seccion/subruta?param=valor).
import { post } from "./api.js";
import { SECCIONES, seccion, visible } from "./nav.js";
import { refrescar, sesion } from "./sesion.js";
import { aviso, cargando, conAviso, h, montar } from "./ui.js";
import { vistaAcceso, vistaPassword } from "./vistas/acceso.js";

const cuerpo = document.getElementById("vista");
let version = 0;

export function ir(ruta) {
  const destino = "#" + ruta;
  if (location.hash === destino) renderizar(); else location.hash = destino;
}

function leerHash() {
  const [ruta, q] = (location.hash.slice(1) || "/").split("?");
  const partes = ruta.split("/").filter(Boolean).map(decodeURIComponent);
  return { partes, params: new URLSearchParams(q || "") };
}

const ROLES_ES = { cliente: "Cliente", cajero: "Cajero", tienda: "Tienda", atencion: "Atención", marketing: "Marketing",
  rrhh: "RR. HH.", manager: "Manager", empleado: "Empleado", direccion: "Dirección", profesor: "Profesor", admin: "Administrador" };

function pintarCabecera(actual) {
  const u = sesion.usuario;
  const menu = document.getElementById("menu");
  montar(menu, SECCIONES.filter((s) => visible(s, u)).map((s) =>
    h("a", { href: `#/${s.id}`, "aria-current": s.id === actual ? "page" : null }, s.titulo)));
  montar(document.getElementById("usuario"), u
    ? [h("span", { class: "quien", title: u.roles.map((r) => ROLES_ES[r] || r).join(", ") }, u.nombre || u.login),
       h("a", { href: "#/password" }, "Contraseña"),
       h("button", { type: "button", onclick: conAviso(async () => { await post("/auth/logout", {}); await refrescar(); ir("/"); }) }, "Salir")]
    : [h("a", { class: "boton primary", href: "#/acceso" }, "Entrar")]);
}

function inicio(cont) {
  const u = sesion.usuario;
  const mias = SECCIONES.filter((s) => visible(s, u));
  montar(cont,
    h("section", { class: "portada" },
      h("h1", {}, u ? `Hola, ${u.nombre || u.login}` : "FraSoHome Live"),
      h("p", { class: "lead" }, u
        ? "Esto es lo que puedes hacer con tu rol."
        : "Tienda de hogar y decoración con datos vivos en Azure SQL y Cosmos DB. Mira el catálogo o entra con tu usuario para operar.")),
    h("div", { class: "rejilla" }, mias.map((s) =>
      h("a", { class: "tarjeta enlace", href: `#/${s.id}` },
        h("small", {}, `Escenario ${s.escenario}`), h("strong", {}, s.titulo), h("span", {}, s.descr)))),
    u ? null : h("p", {}, h("a", { class: "boton primary", href: "#/acceso" }, "Entrar")));
}

async function renderizar() {
  const mia = ++version;
  const { partes, params } = leerHash();
  const [primero, ...resto] = partes;
  const u = sesion.usuario;

  if (u && u.debe_cambiar_contrasena && primero !== "password") return ir("/password");

  const cont = h("div", { class: "contenido" });
  montar(cuerpo, cont);
  cuerpo.focus({ preventScroll: true });
  window.scrollTo(0, 0);

  const ctx = { partes: resto, params, ir, usuario: u };
  if (!primero) { pintarCabecera(null); document.title = "FraSoHome Live"; return inicio(cont); }
  if (primero === "acceso") { pintarCabecera(null); document.title = "Entrar · FraSoHome Live"; return vistaAcceso(cont, ctx); }
  if (primero === "password") {
    if (!u) return ir("/acceso");
    pintarCabecera(null); document.title = "Contraseña · FraSoHome Live";
    return vistaPassword(cont, ctx);
  }

  const s = seccion(primero);
  if (!s) { pintarCabecera(null); return montar(cont, h("section", { class: "tarjeta" }, h("h1", {}, "No existe esa página"), h("a", { href: "#/" }, "Volver al inicio"))); }
  pintarCabecera(s.id);
  document.title = `${s.titulo} · FraSoHome Live`;
  if (!s.publica && !u) return ir("/acceso?volver=" + encodeURIComponent(location.hash.slice(1)));
  if (!visible(s, u)) {
    return montar(cont, h("section", { class: "tarjeta" }, h("h1", {}, "Sin permiso"),
      h("p", {}, "Tu rol no permite entrar en esta sección."), h("a", { href: "#/" }, "Volver al inicio")));
  }
  montar(cont, cargando());
  try {
    const modulo = await s.vista();
    if (mia !== version) return;
    montar(cont);
    await modulo.render(cont, ctx);
  } catch (e) {
    if (mia !== version) return;
    montar(cont, h("section", { class: "tarjeta" }, h("h1", {}, "No se pudo cargar"), h("p", { class: "msg ko" }, e.message || String(e))));
  }
}

document.addEventListener("fsh:sin-sesion", async () => {
  await refrescar();
  if (!sesion.usuario) { aviso("Tu sesión ha caducado. Vuelve a entrar.", "ko"); ir("/acceso"); }
  else if (sesion.usuario.debe_cambiar_contrasena) ir("/password");
});
window.addEventListener("hashchange", renderizar);

await refrescar();
await renderizar();
