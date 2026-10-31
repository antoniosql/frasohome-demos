// Escenario 4 · inventario y reposición: stock vivo, ajustes, tránsito, mínimos, alertas y cierre diario.
import { get, post } from "../api.js";
import { aviso, cargando, confirmar, conAviso, dialogo, ficha, fechaHora, h, hoy, insignia, montar, num, paginador, pestanas,
  selector, tabla } from "../ui.js";
import { ambito, soloRol } from "../sesion.js";

const TAMANO = 50;

export async function render(cont, ctx) {
  const [sub] = ctx.partes;
  const admin = soloRol("admin");
  const propias = ambito("store");
  let tienda = ctx.params.get("tienda") || (propias.length === 1 && !admin ? propias[0] : "");
  const cuerpo = h("div", {}, cargando());

  let selectorTienda = null;
  if (admin || propias.length > 1) {
    const lista = admin ? ["ONLINE", ...(await get("/catalogo/tiendas")).map((t) => t.store_id)] : propias;
    tienda = tienda || lista[0];
    selectorTienda = selector(lista, tienda, { "aria-label": "Tienda", onchange: (ev) => ctx.ir(`/inventario${sub ? "/" + sub : ""}?tienda=${ev.target.value}`) });
  }
  const tabs = [{ id: "", titulo: "Stock" }, { id: "alertas", titulo: "Alertas" }, { id: "movimientos", titulo: "Movimientos" }];
  if (admin) tabs.push({ id: "cierre", titulo: "Cierre diario" });
  montar(cont,
    h("div", { class: "fila entre" }, h("h1", {}, tienda ? `Inventario · ${tienda}` : "Inventario"), selectorTienda),
    pestanas("inventario", tabs, sub || "", tienda && selectorTienda ? `?tienda=${tienda}` : ""), cuerpo);
  const q = { tienda: tienda || undefined };
  if (sub === "alertas") return alertas(cuerpo, ctx, q);
  if (sub === "movimientos") return movimientos(cuerpo, ctx, q);
  if (sub === "cierre" && admin) return cierre(cuerpo);
  return stock(cuerpo, ctx, q);
}

// ------------------------------------------------------------------ operaciones sobre una línea de stock

function acciones(p, q, alTerminar) {
  const enviar = (ruta, cuerpo, ok) => async () => { await post(ruta, { tienda: q.tienda, product_id: p.product_id, ...cuerpo }); aviso(ok); alTerminar(); };
  return h("div", { class: "fila" },
    h("button", { type: "button", onclick: () => dialogo(`Ajustar stock · ${p.product_name}`, [
      { k: "delta", etiqueta: "Variación (+/−)", tipo: "number", step: 1, min: -500, max: 500, req: true, ayuda: `Hay ${num(p.on_hand_qty)} en mano.` },
      { k: "motivo", etiqueta: "Motivo", maxlength: 300, req: true }],
      (v) => enviar("/inventario/ajustes", { delta: v.delta, motivo: v.motivo }, "Stock ajustado.")(), { enviar: "Ajustar" }) }, "Ajustar"),
    h("button", { type: "button", onclick: () => dialogo(`Pedir reposición · ${p.product_name}`, [
      { k: "cantidad", etiqueta: "Unidades", tipo: "number", step: 1, min: 1, max: 500, req: true }],
      (v) => enviar("/inventario/reposiciones", { cantidad: v.cantidad }, "Reposición en tránsito.")(),
      { enviar: "Pedir", intro: "La mercancía queda «en tránsito» hasta que se recibe." }) }, "Reponer"),
    p.in_transit_qty > 0 ? h("button", { type: "button", onclick: () => dialogo(`Recibir · ${p.product_name}`, [
      { k: "cantidad", etiqueta: "Unidades recibidas", tipo: "number", step: 1, min: 1, max: p.in_transit_qty, valor: p.in_transit_qty, req: true }],
      (v) => enviar("/inventario/recepciones", { cantidad: v.cantidad }, "Mercancía recibida.")(),
      { enviar: "Recibir", intro: `En tránsito: ${num(p.in_transit_qty)}.` }) }, "Recibir") : null,
    h("button", { type: "button", onclick: () => dialogo(`Stock mínimo · ${p.product_name}`, [
      { k: "minimo", etiqueta: "Mínimo", tipo: "number", step: 1, min: 0, max: 500, valor: p.minimum_qty, req: true }],
      (v) => enviar("/inventario/minimos", { minimo: v.minimo }, "Mínimo actualizado.")()) }, "Mínimo"));
}

// ------------------------------------------------------------------ stock

async function stock(cuerpo, ctx, q) {
  const prm = ctx.params;
  const pagina = Number(prm.get("pagina") || 1);
  const filtro = { q: prm.get("q") || "", categoria: prm.get("categoria") || "", bajo: prm.get("bajo") === "1" };
  const [cats, r] = await Promise.all([get("/catalogo/categorias"), get("/inventario/stock", { ...q, q: filtro.q, categoria: filtro.categoria,
    bajo_minimo: filtro.bajo ? "1" : undefined, pagina, tamano: TAMANO })]);
  const texto = h("input", { type: "search", value: filtro.q, placeholder: "Producto o código", "aria-label": "Buscar" });
  const cat = selector([["", "Todas las categorías"], ...new Set(cats.map((c) => c.categoria))], filtro.categoria, { "aria-label": "Categoría" });
  const bajo = h("input", { type: "checkbox", checked: filtro.bajo, id: "bajo" });
  const ir = (n) => {
    const s = new URLSearchParams();
    if (q.tienda) s.set("tienda", q.tienda);
    if (texto.value.trim()) s.set("q", texto.value.trim());
    if (cat.value) s.set("categoria", cat.value);
    if (bajo.checked) s.set("bajo", "1");
    if (n > 1) s.set("pagina", n);
    ctx.ir("/inventario" + (s.toString() ? "?" + s : ""));
  };
  montar(cuerpo,
    h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); ir(1); } }, texto, cat,
      h("label", { for: "bajo", class: "inline" }, bajo, " Solo bajo mínimo"), h("button", { type: "submit" }, "Filtrar")),
    tabla([
      { t: "Producto", f: (p) => h("span", {}, h("strong", {}, p.product_name), h("small", {}, ` ${p.product_id} · ${p.category}`)) },
      { t: "En mano", k: "on_hand_qty", cls: "num" }, { t: "Reservado", k: "reserved_qty", cls: "num" }, { t: "Tránsito", k: "in_transit_qty", cls: "num" },
      { t: "Disponible", f: (p) => h("span", { class: p.disponible <= p.minimum_qty ? "ko" : "" }, num(p.disponible)), cls: "num" },
      { t: "Mínimo", k: "minimum_qty", cls: "num" }, { t: "", f: (p) => acciones(p, q, () => stock(cuerpo, ctx, q)) },
    ], r.stock, { sinDatos: "No hay productos con esos filtros." }),
    paginador(pagina, r.total, TAMANO, ir));
}

// ------------------------------------------------------------------ alertas, movimientos y cierre

async function alertas(cuerpo, ctx, q) {
  const lista = await get("/inventario/alertas", q);
  montar(cuerpo, h("p", { class: "ayuda" }, "Productos activos con disponible por debajo del mínimo. Prioridad alta: sin unidades."),
    tabla([
      { t: "Prioridad", f: (a) => insignia(a.prioridad) }, { t: "Producto", f: (a) => `${a.product_id} · ${a.product_name}` },
      { t: "Disponible", k: "disponible", cls: "num" }, { t: "Mínimo", k: "minimum_qty", cls: "num" }, { t: "En tránsito", k: "in_transit_qty", cls: "num" },
      { t: "Vendidas 7 días", k: "vendidas_7d", cls: "num" },
      { t: "", f: (a) => h("button", { type: "button", onclick: () => dialogo(`Pedir reposición · ${a.product_name}`, [
        { k: "cantidad", etiqueta: "Unidades", tipo: "number", step: 1, min: 1, max: 500, valor: Math.max(a.minimum_qty * 2 - a.disponible, 1), req: true }],
        async (v) => { await post("/inventario/reposiciones", { tienda: q.tienda, product_id: a.product_id, cantidad: v.cantidad });
          aviso("Reposición en tránsito."); alertas(cuerpo, ctx, q); }, { enviar: "Pedir" }) }, "Reponer") },
    ], lista, { sinDatos: "Sin alertas: todo el stock está por encima del mínimo." }));
}

async function movimientos(cuerpo, ctx, q) {
  const producto = (ctx.params.get("producto") || "").toUpperCase();
  const lista = await get("/inventario/movimientos", { ...q, product_id: producto || undefined, tamano: 100 });
  const f = h("input", { value: producto, placeholder: "Producto (P1020)", maxlength: "5", "aria-label": "Producto" });
  montar(cuerpo,
    h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault();
      ctx.ir(`/inventario/movimientos?${new URLSearchParams({ ...(q.tienda ? { tienda: q.tienda } : {}), ...(f.value.trim() ? { producto: f.value.trim().toUpperCase() } : {}) })}`); } },
      f, h("button", { type: "submit" }, "Filtrar")),
    tabla([
      { t: "Fecha", f: (m) => fechaHora(m.moved_at) }, { t: "Producto", k: "product_id" }, { t: "Tipo", k: "movement_type" },
      { t: "En mano", f: (m) => signo(m.on_hand_delta), cls: "num" }, { t: "Reservado", f: (m) => signo(m.reserved_delta), cls: "num" },
      { t: "Tránsito", f: (m) => signo(m.in_transit_delta), cls: "num" },
      { t: "Documento", f: (m) => [m.document_type, m.document_id].filter(Boolean).join(" ") || "—" }, { t: "Usuario", f: (m) => m.user_login || "—" },
      { t: "Notas", f: (m) => m.notes || "—" },
    ], lista, { sinDatos: "Sin movimientos." }));
}
const signo = (n) => (n ? (n > 0 ? `+${num(n)}` : num(n)) : "—");

function cierre(cuerpo) {
  const dia = h("input", { type: "date", value: hoy(), "aria-label": "Fecha" });
  const salida = h("div", {});
  montar(cuerpo,
    h("p", { class: "ayuda" }, "Fotografía el stock vivo de todas las tiendas en el histórico de stock diario."),
    h("div", { class: "fila" }, dia, h("button", { type: "button", class: "primary", onclick: conAviso(async () => {
      if (!confirmar(`¿Cerrar el día ${dia.value}?`)) return;
      const r = await post("/inventario/cierre", { fecha: dia.value });
      aviso("Cierre diario hecho.");
      montar(salida, ficha(Object.entries(r).map(([k, v]) => [k, String(v)])));
    }) }, "Cerrar el día")), salida);
}
