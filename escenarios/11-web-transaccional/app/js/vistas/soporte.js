// Escenario 9 · el cliente abre consultas a atención, sigue la conversación y valora la resolución (CSAT).
import { get, post } from "../api.js";
import { aviso, campo, cargando, conAviso, dialogo, fechaHora, ficha, h, insignia, montar, selector, tabla } from "../ui.js";
import { TIPOS, conversacion, sla } from "./atencion.js";

export async function render(cont, ctx) {
  const [id] = ctx.partes;
  const cuerpo = h("div", {}, cargando());
  montar(cont, cuerpo);
  if (id) return detalle(cuerpo, id, ctx);
  return lista(cuerpo, ctx);
}

async function lista(cuerpo, ctx) {
  const filas = await get("/mis-casos");
  const nuevo = () => dialogo("Nueva consulta", [
    { k: "tipo_caso", etiqueta: "Sobre qué es", tipo: "select", opciones: TIPOS, valor: "info_producto" },
    { k: "order_id", etiqueta: "Pedido (opcional)", maxlength: 11, ayuda: "Si tu consulta es sobre un pedido, escribe su número (O-…)." },
    { k: "texto", etiqueta: "Cuéntanos qué necesitas", tipo: "textarea", maxlength: 2000, req: true },
  ], async (v) => {
    const c = await post("/mis-casos", v);
    aviso("Consulta enviada.");
    ctx.ir(`/soporte/${c.id}`);
  }, { enviar: "Enviar consulta" });
  montar(cuerpo,
    h("div", { class: "fila entre" }, h("h1", {}, "Mis casos"), h("button", { type: "button", class: "primary", onclick: nuevo }, "Nueva consulta")),
    tabla([
      { t: "Caso", k: "id" }, { t: "Fecha", f: (c) => fechaHora(c.fecha_apertura) }, { t: "Tipo", k: "tipo_caso" },
      { t: "Estado", f: (c) => insignia(c.estado_resolucion) }, { t: "Valoración", f: (c) => (c.csat_1_5 ? "★".repeat(c.csat_1_5) : "—") },
    ], filas, { alClic: (c) => ctx.ir(`/soporte/${c.id}`), sinDatos: "No tienes consultas abiertas." }));
}

async function detalle(cuerpo, id, ctx) {
  const lista = await get("/mis-casos");
  const c = lista.find((x) => x.id === id.toUpperCase());
  if (!c) return montar(cuerpo, h("p", {}, h("a", { href: "#/soporte" }, "‹ Mis casos")), h("p", { class: "msg ko" }, "No encuentro ese caso."));
  const recargar = () => detalle(cuerpo, id, ctx);
  const texto = h("textarea", { rows: 3, maxlength: 2000 });
  const nota = selector([["", "Elige…"], ...[1, 2, 3, 4, 5].map((n) => [n, `${"★".repeat(n)} (${n})`])], "", { id: "nota-csat" });
  montar(cuerpo,
    h("p", {}, h("a", { href: "#/soporte" }, "‹ Mis casos")),
    h("h1", {}, `Caso ${c.id} `, insignia(c.estado_resolucion)),
    ficha([["Abierto", fechaHora(c.fecha_apertura)], ["Tipo", c.tipo_caso], ["Seguimiento", sla(c)], c.order_id ? ["Pedido", h("a", { href: `#/pedidos/${c.order_id}` }, c.order_id)] : null,
      c.cupon_compensacion ? ["Cupón de compensación", c.cupon_compensacion] : null]),
    conversacion(c),
    c.estado_resolucion !== "Resuelto"
      ? h("form", { onsubmit: conAviso(async (ev) => {
        ev.preventDefault();
        if (!texto.value.trim()) return;
        await post(`/mis-casos/${c.id}/mensajes`, { texto: texto.value }); aviso("Mensaje enviado."); recargar();
      }) }, campo("Añadir un mensaje", texto), h("button", { type: "submit" }, "Enviar"))
      : c.csat_1_5 ? h("p", { class: "msg ok" }, `Gracias por valorar la atención: ${"★".repeat(c.csat_1_5)}`)
        : h("form", { class: "fila", onsubmit: conAviso(async (ev) => {
          ev.preventDefault();
          if (!nota.value) return;
          await post(`/mis-casos/${c.id}/csat`, { csat: Number(nota.value) }); aviso("Gracias por tu valoración."); recargar();
        }) }, h("label", { for: "nota-csat" }, "¿Cómo valoras la atención recibida?"), nota, h("button", { type: "submit", class: "primary" }, "Valorar")));
}
