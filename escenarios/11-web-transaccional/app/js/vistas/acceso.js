// Acceso: inicio de sesión y cambio de contraseña (obligatorio en el primer acceso).
import { post } from "../api.js";
import { campo, conAviso, h, montar } from "../ui.js";
import { refrescar, sesion } from "../sesion.js";

export function vistaAcceso(cont, { ir, params }) {
  const login = h("input", { name: "login", autocomplete: "username", required: true, autocapitalize: "none", spellcheck: "false" });
  const clave = h("input", { name: "password", type: "password", autocomplete: "current-password", required: true });
  const msg = h("p", { class: "msg ko", role: "alert" });
  montar(cont,
    h("section", { class: "tarjeta estrecha" },
      h("h1", {}, "Entrar"),
      h("p", { class: "ayuda" }, "Los usuarios los crea el administrador. No hay registro abierto."),
      h("form", { onsubmit: conAviso(async (ev) => {
        ev.preventDefault();
        msg.textContent = "";
        try {
          await post("/auth/login", { login: login.value, password: clave.value });
        } catch (e) { msg.textContent = e.message; clave.value = ""; return; }
        clave.value = "";
        await refrescar();
        ir(sesion.usuario && sesion.usuario.debe_cambiar_contrasena ? "/password" : (params.get("volver") || "/"));
      }) },
        campo("Usuario", login), campo("Contraseña", clave), msg,
        h("button", { type: "submit", class: "primary" }, "Entrar"))));
  login.focus();
}

export function vistaPassword(cont, { ir }) {
  const obligatorio = sesion.usuario && sesion.usuario.debe_cambiar_contrasena;
  const actual = h("input", { type: "password", autocomplete: "current-password", required: true });
  const nueva = h("input", { type: "password", autocomplete: "new-password", required: true, minlength: "12" });
  const msg = h("p", { class: "msg ko", role: "alert" });
  montar(cont,
    h("section", { class: "tarjeta estrecha" },
      h("h1", {}, obligatorio ? "Cambia tu contraseña" : "Contraseña"),
      h("p", { class: "ayuda" }, (obligatorio ? "Es obligatorio en el primer acceso. " : "") +
        "Mínimo 12 caracteres, con al menos tres tipos (minúsculas, mayúsculas, números o símbolos), y sin tu usuario."),
      h("form", { onsubmit: conAviso(async (ev) => {
        ev.preventDefault();
        msg.textContent = "";
        try { await post("/auth/password", { actual: actual.value, nueva: nueva.value }); }
        catch (e) { msg.textContent = e.message; return; }
        actual.value = ""; nueva.value = "";
        await refrescar();
        ir("/");
      }) },
        campo("Contraseña actual", actual), campo("Contraseña nueva", nueva), msg,
        h("button", { type: "submit", class: "primary" }, "Cambiar contraseña"))));
  actual.focus();
}
