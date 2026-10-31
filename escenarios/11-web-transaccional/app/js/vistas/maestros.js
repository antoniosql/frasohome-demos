// Escenario 5 · catálogo y tiendas (administración): alta, precios y baja de productos; ficha de tienda.
import { get, post, put } from "../api.js";
import { aviso, cargando, dialogo, eur, fecha, h, insignia, montar, num, pestanas, selector, tabla } from "../ui.js";

const TAMANO = 50;
const CATEGORIAS = ["Muebles", "Decoración", "Iluminación", "Textil hogar"];

export async function render(cont, ctx) {
  const [sub] = ctx.partes;
  const cuerpo = h("div", {}, cargando());
  montar(cont, h("h1", {}, "Catálogo y tiendas"),
    pestanas("maestros", [{ id: "", titulo: "Productos" }, { id: "tiendas", titulo: "Tiendas" }, { id: "alias", titulo: "Alias de producto" }], sub || ""), cuerpo);
  if (sub === "tiendas") return tiendas(cuerpo);
  if (sub === "alias") return alias(cuerpo);
  return productos(cuerpo, ctx);
}

// ------------------------------------------------------------------ productos

function camposProducto(p = {}) {
  const n = (v) => (v === null || v === undefined ? "" : v);
  return [
    { k: "nombre", etiqueta: "Nombre", valor: p.product_name, maxlength: 255, req: true },
    { k: "categoria", etiqueta: "Categoría", tipo: "select", opciones: CATEGORIAS, valor: p.category || CATEGORIAS[0] },
    { k: "subcategoria", etiqueta: "Subcategoría", valor: n(p.subcategory), maxlength: 100 },
    { k: "marca", etiqueta: "Marca", valor: n(p.brand), maxlength: 100 },
    { k: "proveedor", etiqueta: "Proveedor", valor: n(p.supplier), maxlength: 100 },
    { k: "material", etiqueta: "Material", valor: n(p.material), maxlength: 100 },
    { k: "color", etiqueta: "Color", valor: n(p.color), maxlength: 100 },
    { k: "precio", etiqueta: "Precio de venta (€, IVA incl.)", tipo: "number", min: 0.01, step: 0.01, valor: n(p.sale_price), req: true },
    { k: "coste", etiqueta: "Coste unitario (€)", tipo: "number", min: 0, step: 0.01, valor: n(p.unit_cost) },
    { k: "iva", etiqueta: "IVA (%)", tipo: "number", min: 0, max: 21, step: 0.01, valor: p.vat_pct ?? 21, req: true },
    { k: "peso_kg", etiqueta: "Peso (kg)", tipo: "number", min: 0, step: 0.001, valor: n(p.weight_kg) },
    { k: "largo_cm", etiqueta: "Largo (cm)", tipo: "number", min: 0, step: 0.1, valor: n(p.length_cm) },
    { k: "ancho_cm", etiqueta: "Ancho (cm)", tipo: "number", min: 0, step: 0.1, valor: n(p.width_cm) },
    { k: "alto_cm", etiqueta: "Alto (cm)", tipo: "number", min: 0, step: 0.1, valor: n(p.height_cm) },
    { k: "estado", etiqueta: "Estado", tipo: "select", opciones: ["Activo", "Descatalogado"], valor: p.product_status || "Activo" },
    { k: "ean", etiqueta: "EAN", valor: n(p.ean), maxlength: 13 },
  ];
}

async function productos(cuerpo, ctx) {
  const pagina = Number(ctx.params.get("pagina") || 1);
  const estado = ctx.params.get("estado") || "";
  const lista = await get("/admin/productos", { estado, pagina, tamano: TAMANO });
  const recargar = () => productos(cuerpo, ctx);
  const sel = selector([["", "Todos los estados"], "Activo", "Descatalogado"], estado, { "aria-label": "Estado" });
  const ir = (n, e = estado) => {
    const s = new URLSearchParams();
    if (e) s.set("estado", e);
    if (n > 1) s.set("pagina", n);
    ctx.ir("/maestros" + (s.toString() ? "?" + s : ""));
  };
  const margen = (p) => (p.sale_price && p.unit_cost ? `${num(Math.round((1 - p.unit_cost / (p.sale_price / (1 + p.vat_pct / 100))) * 100))} %` : "—");
  const guardar = (id) => async (v) => {
    const r = id ? await put(`/admin/productos/${id}`, v) : await post("/admin/productos", v);
    aviso(id ? `Producto ${r.product_id} actualizado.` : `Producto ${r.product_id} creado.`);
    recargar();
  };
  montar(cuerpo,
    h("div", { class: "fila entre" },
      h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); ir(1, sel.value); } }, sel, h("button", { type: "submit" }, "Filtrar")),
      h("button", { type: "button", class: "primary", onclick: () => dialogo("Nuevo producto", camposProducto(), guardar(null), { enviar: "Crear producto" }) }, "Nuevo producto")),
    tabla([
      { t: "Código", k: "product_id" }, { t: "Producto", k: "product_name" }, { t: "Categoría", k: "category" }, { t: "Marca", f: (p) => p.brand || "—" },
      { t: "Precio", f: (p) => eur(p.sale_price), cls: "num" }, { t: "Coste", f: (p) => eur(p.unit_cost), cls: "num" },
      { t: "Margen s/ neto", f: margen, cls: "num" }, { t: "Estado", f: (p) => insignia(p.product_status) },
      { t: "", f: (p) => h("button", { type: "button", onclick: () => dialogo(`Editar ${p.product_id}`, camposProducto(p), guardar(p.product_id)) }, "Editar") },
    ], lista, { sinDatos: "No hay productos." }),
    h("div", { class: "paginador" },
      h("button", { type: "button", disabled: pagina <= 1, onclick: () => ir(pagina - 1) }, "‹ Anterior"),
      h("span", {}, `Página ${pagina}`),
      h("button", { type: "button", disabled: lista.length < TAMANO, onclick: () => ir(pagina + 1) }, "Siguiente ›")));
}

// ------------------------------------------------------------------ tiendas

async function tiendas(cuerpo) {
  const lista = await get("/admin/tiendas");
  const editar = (t) => dialogo(`Tienda ${t.store_id}`, [
    { k: "nombre", etiqueta: "Nombre", valor: t.store_name, maxlength: 150, req: true },
    { k: "horario", etiqueta: "Horario", valor: t.opening_hours ?? "", maxlength: 100 },
    { k: "telefono", etiqueta: "Teléfono", valor: t.phone ?? "", maxlength: 50 },
    { k: "gerente", etiqueta: "Gerente", valor: t.manager_name ?? "", maxlength: 150 },
    { k: "estado", etiqueta: "Estado", tipo: "select", opciones: ["Activa", "Planificada", "Cerrada"], valor: t.store_status },
    { k: "apertura", etiqueta: "Fecha de apertura", tipo: "date", valor: t.opened_at ? String(t.opened_at).slice(0, 10) : "" },
  ], async (v) => { await put(`/admin/tiendas/${t.store_id}`, v); aviso("Tienda actualizada."); tiendas(cuerpo); });
  montar(cuerpo, tabla([
    { t: "Tienda", k: "store_id" }, { t: "Nombre", k: "store_name" }, { t: "Canal", k: "channel" }, { t: "Ciudad", f: (t) => t.city || "—" },
    { t: "Gerente", f: (t) => t.manager_name || "—" }, { t: "Horario", f: (t) => t.opening_hours || "—" }, { t: "Apertura", f: (t) => fecha(t.opened_at) },
    { t: "Estado", f: (t) => insignia(t.store_status) },
    { t: "", f: (t) => h("button", { type: "button", onclick: () => editar(t) }, "Editar") },
  ], lista));
}

// ------------------------------------------------------------------ alias

async function alias(cuerpo) {
  const lista = await get("/admin/alias-productos");
  montar(cuerpo, h("p", { class: "ayuda" }, "Equivalencias entre los códigos del escenario RAG y el catálogo de retail (solo lectura)."),
    tabla([
      { t: "Sistema", k: "source_system" }, { t: "Código origen", k: "source_product_id" }, { t: "Nombre origen", f: (a) => a.source_product_name || "—" },
      { t: "Producto canónico", f: (a) => [a.canonical_product_id, a.canonical_product_name].filter(Boolean).join(" · ") || "—" },
      { t: "Método", f: (a) => a.match_method || "—" }, { t: "Confianza", f: (a) => (a.confidence === null || a.confidence === undefined ? "—" : num(a.confidence)), cls: "num" },
    ], lista));
}
