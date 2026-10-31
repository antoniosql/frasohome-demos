// Escenario 6 · el cliente ve y edita su propia cuenta: contacto, consentimientos y puntos.
import { get, put } from "../api.js";
import { aviso, cargando, dialogo, eur, fecha, fechaHora, ficha, h, insignia, montar, num, sino } from "../ui.js";
import { camposCliente, cuerpoCliente } from "./clientes.js";

export async function render(cont) {
  montar(cont, cargando());
  await pintar(cont);
}

async function pintar(cont) {
  const c = await get("/mi-cuenta");
  const r = c.resumen;
  montar(cont,
    h("h1", {}, `Hola, ${c.first_name} `, insignia(c.customer_status)),
    h("div", { class: "dos" },
      h("section", { class: "tarjeta" }, h("h2", {}, "Fidelización"),
        h("p", { class: "grande" }, `${num(c.loyalty_points)} puntos`),
        ficha([["Nivel", c.loyalty_tier || "Sin nivel"], ["Socio desde", c.loyalty_joined_at ? fecha(c.loyalty_joined_at) : null],
          ["Cupones vigentes", num(r.cupones_vigentes)]]),
        h("a", { href: "#/pedidos/cupones" }, "Ver mis cupones")),
      h("section", { class: "tarjeta" }, h("h2", {}, "Tu actividad"),
        ficha([["Pedidos online", `${num(r.pedidos)} · ${eur(r.gasto_online)}`], ["Compras en tienda", `${num(r.tickets)} · ${eur(r.gasto_tienda)}`],
          ["Devoluciones", num(r.devoluciones)], ["Última compra", r.ultima_compra ? fechaHora(r.ultima_compra) : "Sin compras"]]))),
    h("section", {}, h("h2", {}, "Tus datos"),
      ficha([["Nombre", `${c.first_name} ${c.last_name}`], ["Email", c.email], ["Teléfono", c.phone],
        ["Ciudad", [c.postal_code, c.city, c.province].filter(Boolean).join(" · ")], ["Canal preferido", c.preferred_channel],
        ["Comunicaciones comerciales", sino(c.marketing_consent)]]),
      h("button", { type: "button", class: "primary", onclick: () => dialogo("Tus datos de contacto", camposCliente(c, { completo: false }), async (v) => {
        const { consentimiento_marketing, canal_preferido, ...datos } = cuerpoCliente(v);
        await put("/mi-cuenta", { ...datos, canal_preferido, consentimiento_marketing });
        aviso("Datos actualizados."); pintar(cont);
      }, { intro: "El nombre y el nivel solo los cambia el equipo de atención." }) }, "Editar mis datos")));
}
