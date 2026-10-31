// Escenario 1 · compra online: catálogo público, promociones, tiendas, carrito y finalizar compra.
import { get, post, put } from "../api.js";
import { aviso, campo, cargando, conAviso, eur, fecha, fechaHora, h, insignia, montar, num, paginador, selector, vacio } from "../ui.js";
import { soloRol } from "../sesion.js";

const TAMANO = 24;
const PAGOS = ["Tarjeta", "PayPal", "Bizum", "ApplePay", "Transferencia", "ContraReembolso"];

export async function render(cont, ctx) {
  const [sub, id] = ctx.partes;
  const pestana = { promociones: "promociones", tiendas: "tiendas", carrito: "carrito", finalizar: "carrito" }[sub] || "catalogo";
  const cuerpo = h("div", {}, cargando());
  const tabs = [["catalogo", "Catálogo", "/tienda"], ["promociones", "Promociones", "/tienda/promociones"], ["tiendas", "Tiendas", "/tienda/tiendas"]];
  if (soloRol("cliente")) tabs.push(["carrito", "Carrito", "/tienda/carrito"]);
  montar(cont,
    h("nav", { class: "pestanas", "aria-label": "Tienda" }, tabs.map(([t, titulo, ruta]) =>
      h("a", { href: "#" + ruta, "aria-current": t === pestana ? "page" : null }, titulo))),
    cuerpo);
  if (sub === "producto") return producto(cuerpo, id, ctx);
  if (sub === "promociones") return promociones(cuerpo);
  if (sub === "tiendas") return tiendas(cuerpo);
  if (sub === "carrito") return carrito(cuerpo, ctx);
  if (sub === "finalizar") return finalizar(cuerpo, ctx);
  return catalogo(cuerpo, ctx);
}

// ------------------------------------------------------------------ eventos de navegación (Cosmos)

function evento(tipo, extra = {}) {
  let sesion = null;
  try { sesion = sessionStorage.getItem("fsh_se"); } catch (e) { /* sin almacenamiento */ }
  post("/eventos", { tipo_evento: tipo, session_id: sesion, ...extra }).then((r) => {
    try { if (r && r.session_id) sessionStorage.setItem("fsh_se", r.session_id); } catch (e) { /* sin almacenamiento */ }
  }).catch(() => { /* la telemetría nunca molesta al usuario */ });
}

// ------------------------------------------------------------------ catálogo

async function catalogo(cuerpo, ctx) {
  const p = ctx.params;
  const pagina = Number(p.get("pagina") || 1);
  const filtros = { q: p.get("q") || "", categoria: p.get("categoria") || "", orden: p.get("orden") || "nombre" };
  const [cats, lista] = await Promise.all([
    get("/catalogo/categorias"),
    get("/catalogo/productos", { ...filtros, pagina, tamano: TAMANO }),
  ]);
  const nombres = [...new Set(cats.map((c) => c.categoria))];
  const q = h("input", { type: "search", name: "q", value: filtros.q, placeholder: "Nombre, marca o código", "aria-label": "Buscar" });
  const cat = selector([["", "Todas las categorías"], ...nombres], filtros.categoria, { "aria-label": "Categoría" });
  const orden = selector([["nombre", "Nombre"], ["precio", "Precio ascendente"], ["precio_desc", "Precio descendente"], ["novedad", "Novedades"]],
    filtros.orden, { "aria-label": "Ordenar por" });
  const ir = (n) => {
    const s = new URLSearchParams();
    if (q.value.trim()) s.set("q", q.value.trim());
    if (cat.value) s.set("categoria", cat.value);
    if (orden.value !== "nombre") s.set("orden", orden.value);
    if (n > 1) s.set("pagina", n);
    ctx.ir("/tienda" + (s.toString() ? "?" + s : ""));
  };
  if (filtros.q) evento("search", { search_term: filtros.q, page_type: "search_results" });
  else if (filtros.categoria) evento("category_view", { categoria: filtros.categoria, page_type: "category_listing" });
  else if (pagina === 1) evento("page_view", { page_type: "home" });

  montar(cuerpo,
    h("form", { class: "filtros", role: "search", onsubmit: (ev) => { ev.preventDefault(); ir(1); } },
      q, cat, orden, h("button", { type: "submit", class: "primary" }, "Buscar")),
    lista.productos.length
      ? h("div", { class: "productos" }, lista.productos.map(tarjetaProducto))
      : vacio("Ningún producto coincide con la búsqueda."),
    paginador(pagina, lista.total, TAMANO, ir));
}

function tarjetaProducto(p) {
  const agotado = !(p.disponible_online > 0);
  return h("a", { class: "producto", href: `#/tienda/producto/${p.product_id}` },
    h("div", { class: "foto", "aria-hidden": "true" }, p.category),
    h("strong", {}, p.product_name),
    h("span", { class: "de" }, [p.brand, p.color].filter(Boolean).join(" · ")),
    h("span", { class: "precio" }, eur(p.sale_price),
      p.promo_pct ? h("span", { class: "insignia aviso" }, `−${num(p.promo_pct)} %`) : null),
    h("span", { class: agotado ? "stock ko" : "stock ok" }, agotado ? "Agotado online" : `${num(p.disponible_online)} disponibles`));
}

// ------------------------------------------------------------------ ficha de producto

async function producto(cuerpo, id, ctx) {
  const p = await get(`/catalogo/productos/${encodeURIComponent(id)}`);
  evento("view_product", { product_id: p.product_id, categoria: p.category, subcategoria: p.subcategory, page_type: "product_detail" });
  const online = (p.stock.find((s) => s.store_id === "ONLINE") || {}).disponible || 0;
  const cantidad = h("input", { type: "number", min: "1", max: String(Math.min(20, Math.max(1, online))), value: "1", "aria-label": "Cantidad" });
  const comprar = soloRol("cliente")
    ? h("div", { class: "fila" }, cantidad, h("button", { type: "button", class: "primary", disabled: online < 1, onclick: conAviso(async () => {
        await anadirAlCarrito(p.product_id, Number(cantidad.value));
        evento("add_to_cart", { product_id: p.product_id, categoria: p.category, page_type: "product_detail" });
      }) }, online < 1 ? "Agotado online" : "Añadir al carrito"))
    : h("p", { class: "ayuda" }, h("a", { href: "#/acceso?volver=" + encodeURIComponent(`/tienda/producto/${p.product_id}`) }, "Entra como cliente"), " para comprar.");

  const op = p.opiniones;
  montar(cuerpo,
    h("p", {}, h("a", { href: "#/tienda" }, "‹ Volver al catálogo")),
    h("div", { class: "dos" },
      h("div", { class: "foto grande", "aria-hidden": "true" }, p.category),
      h("div", {},
        h("h1", {}, p.product_name),
        h("p", { class: "ayuda" }, [p.product_id, p.brand, p.subcategory].filter(Boolean).join(" · ")),
        h("p", { class: "precio grande" }, eur(p.sale_price), h("small", {}, ` IVA ${num(p.vat_pct)} % incluido`)),
        p.product_status !== "Activo" ? insignia(p.product_status) : null,
        h("p", { class: online > 0 ? "stock ok" : "stock ko" }, online > 0 ? `${num(online)} unidades disponibles online` : "Agotado online"),
        comprar,
        h("dl", { class: "ficha" },
          [["Material", p.material], ["Color", p.color], ["Peso", p.weight_kg ? `${num(p.weight_kg)} kg` : null],
           ["Medidas", p.length_cm ? `${num(p.length_cm)} × ${num(p.width_cm)} × ${num(p.height_cm)} cm` : null], ["EAN", p.ean]]
            .filter(([, v]) => v).map(([k, v]) => [h("dt", {}, k), h("dd", {}, v)])))),
    p.promociones.length ? h("section", {}, h("h2", {}, "Promociones vigentes"), h("ul", {}, p.promociones.map((x) =>
      h("li", {}, `${x.promo_name}: ${x.discount_pct ? `−${num(x.discount_pct)} %` : eur(x.discount_eur)} hasta ${fecha(x.ends_at)}`)))) : null,
    h("section", {}, h("h2", {}, "Disponibilidad por tienda"),
      p.stock.length ? h("ul", { class: "lista-plana" }, p.stock.map((s) =>
        h("li", {}, `${s.store_name}: `, h("span", { class: s.disponible > 0 ? "ok" : "ko" }, s.disponible > 0 ? `${num(s.disponible)} uds` : "sin stock")))) : vacio("Sin datos de stock.")),
    h("section", {}, h("h2", {}, "Opiniones"),
      op.total ? [h("p", {}, `Valoración media ${op.media ?? "—"} / 5 en ${num(op.total)} opiniones`),
        h("ul", { class: "opiniones" }, op.ultimas.map((o) => h("li", {},
          h("strong", {}, "★".repeat(o.rating_1_5 || 0)), " ", o.texto_feedback, o.respuesta_marca ? h("blockquote", {}, `FraSoHome: ${o.respuesta_marca}`) : null)))]
        : vacio("Todavía no hay opiniones publicadas.")));
}

async function anadirAlCarrito(productId, cantidad) {
  const c = await get("/carrito");
  const lineas = c.lineas.map((l) => ({ ...l }));
  const l = lineas.find((x) => x.product_id === productId);
  if (l) l.cantidad = Math.min(20, l.cantidad + cantidad); else lineas.push({ product_id: productId, cantidad });
  await put("/carrito", { lineas, cupon: c.cupon });
  aviso("Añadido al carrito.");
}

// ------------------------------------------------------------------ promociones y tiendas

async function promociones(cuerpo) {
  const lista = await get("/catalogo/promociones");
  const ambito = { categoria: "Categoría", categoria_tienda: "Categoría en tienda", producto: "Producto", cesta: "Cesta" };
  montar(cuerpo, h("h1", {}, "Promociones vigentes"), lista.length ? h("div", { class: "rejilla" }, lista.map((x) =>
    h("article", { class: "tarjeta" },
      h("strong", {}, x.promo_name),
      h("span", {}, x.discount_pct ? `−${num(x.discount_pct)} %` : x.discount_eur ? `−${eur(x.discount_eur)}` : x.promo_type),
      h("small", {}, `${ambito[x.scope_type] || x.scope_type}: ${(x.scope_id || "").replace("|", " · ")}`),
      h("small", {}, `Canal ${x.channel || "todos"}${x.store_id ? ` · tienda ${x.store_id}` : ""}${x.basket_threshold_eur ? ` · desde ${eur(x.basket_threshold_eur)}` : ""}`),
      h("small", {}, `${x.combinable ? "Combinable" : "No combinable"} · hasta ${fecha(x.ends_at)}`)))) : vacio("No hay promociones activas ahora mismo."));
}

async function tiendas(cuerpo) {
  const lista = await get("/catalogo/tiendas");
  evento("store_locator", { page_type: "store_locator" });
  montar(cuerpo, h("h1", {}, "Nuestras tiendas"), h("div", { class: "rejilla" }, lista.map((t) =>
    h("article", { class: "tarjeta" },
      h("strong", {}, t.store_name), insignia(t.store_status),
      h("span", {}, [t.address_line, t.postal_code, t.city].filter(Boolean).join(", ")),
      h("small", {}, [t.province, t.region].filter(Boolean).join(" · ")),
      t.opening_hours ? h("small", {}, `Horario: ${t.opening_hours}`) : null,
      t.phone ? h("small", {}, `Tel. ${t.phone}`) : null))));
}

// ------------------------------------------------------------------ carrito

async function carrito(cuerpo, ctx) {
  if (!soloRol("cliente")) return montar(cuerpo, vacio("El carrito es para clientes. Entra con un usuario cliente."));
  const [c, cupones] = await Promise.all([get("/carrito"), get("/mis-cupones")]);
  const pintar = (datos) => carritoVista(cuerpo, datos, cupones, ctx, pintar);
  pintar(c);
}

function carritoVista(cuerpo, c, cupones, ctx, repintar) {
  if (!c.lineas.length) {
    return montar(cuerpo, h("h1", {}, "Tu carrito"), vacio("El carrito está vacío."), h("a", { class: "boton primary", href: "#/tienda" }, "Ver catálogo"));
  }
  const det = {};
  for (const l of (c.presupuesto && c.presupuesto.lineas) || []) det[l.product_id] = l;
  const t = c.presupuesto && c.presupuesto.totales;
  const guardar = async (lineas, cupon) => repintar(await put("/carrito", { lineas, cupon }));
  const cuponTxt = h("input", { value: c.cupon || "", placeholder: "FSH00000000", maxlength: "30", "aria-label": "Código de cupón" });
  const sinStock = c.lineas.some((l) => det[l.product_id] && det[l.product_id].available_qty < l.cantidad);
  const aplicables = cupones.filter((x) => x.coupon_status === "emitido");

  const filas = c.lineas.map((l) => {
    const d = det[l.product_id] || {};
    const cant = h("input", { type: "number", min: "1", max: "20", value: l.cantidad, "aria-label": `Cantidad de ${d.product_name || l.product_id}` });
    cant.addEventListener("change", conAviso(async () => guardar(c.lineas.map((x) => x.product_id === l.product_id
      ? { ...x, cantidad: Math.max(1, Math.min(20, Number(cant.value) || 1)) } : x), c.cupon)));
    return h("tr", {},
      h("td", {}, h("a", { href: `#/tienda/producto/${l.product_id}` }, d.product_name || l.product_id),
        d.available_qty < l.cantidad ? h("small", { class: "ko" }, ` Solo quedan ${num(d.available_qty)}`) : null),
      h("td", { class: "num" }, eur(d.unit_price)), h("td", {}, cant),
      h("td", { class: "num" }, (d.discount_amount || 0) + (d.coupon_share || 0) > 0 ? `−${eur((d.discount_amount || 0) + (d.coupon_share || 0))}` : "—"),
      h("td", { class: "num" }, eur(d.line_amount)),
      h("td", {}, h("button", { type: "button", "aria-label": `Quitar ${d.product_name || l.product_id}`, onclick: conAviso(async () =>
        guardar(c.lineas.filter((x) => x.product_id !== l.product_id), c.cupon)) }, "Quitar")));
  });

  montar(cuerpo,
    h("h1", {}, "Tu carrito"),
    c.aviso ? h("p", { class: "msg ko", role: "alert" }, c.aviso) : null,
    h("div", { class: "tabla-caja" }, h("table", {},
      h("thead", {}, h("tr", {}, ["Producto", "Precio", "Cantidad", "Descuento", "Importe", ""].map((x, i) => h("th", { class: i === 1 || i === 3 || i === 4 ? "num" : "" }, x)))),
      h("tbody", {}, filas))),
    h("div", { class: "dos" },
      h("section", {},
        h("h2", {}, "Cupón"),
        h("div", { class: "fila" }, cuponTxt,
          h("button", { type: "button", onclick: conAviso(async () => guardar(c.lineas, cuponTxt.value.trim() || null)) }, c.cupon ? "Cambiar" : "Aplicar"),
          c.cupon ? h("button", { type: "button", onclick: conAviso(async () => guardar(c.lineas, null)) }, "Quitar") : null),
        aplicables.length ? h("p", { class: "ayuda" }, "Tus cupones: ", aplicables.map((x) => h("button", { type: "button", class: "chip",
          title: `Válido hasta ${fecha(x.valid_to)}`, onclick: conAviso(async () => guardar(c.lineas, x.coupon_code)) },
          `${x.coupon_code} · ${x.discount_pct ? `${num(x.discount_pct)} %` : eur(x.discount_eur)}`))) : null),
      t ? h("section", { class: "tarjeta" },
        h("h2", {}, "Resumen"),
        h("dl", { class: "ficha total" },
          h("dt", {}, "Subtotal"), h("dd", {}, eur(t.gross_total)),
          h("dt", {}, "Promociones"), h("dd", {}, `−${eur(t.promo_discount)}`),
          t.coupon_discount ? [h("dt", {}, "Cupón"), h("dd", {}, `−${eur(t.coupon_discount)}`)] : null,
          h("dt", {}, "Envío"), h("dd", {}, eur(t.gastos_envio)),
          h("dt", {}, "Total"), h("dd", { class: "grande" }, eur(Number(t.net_total) + Number(t.gastos_envio || 0)))),
        h("a", { class: "boton primary" + (sinStock ? " desactivado" : ""), href: sinStock ? null : "#/tienda/finalizar",
          "aria-disabled": sinStock ? "true" : null }, "Finalizar compra")) : null));
}

// ------------------------------------------------------------------ finalizar compra

async function finalizar(cuerpo, ctx) {
  if (!soloRol("cliente")) return montar(cuerpo, vacio("Solo los clientes pueden comprar."));
  const c = await get("/carrito");
  if (!c.lineas.length) return montar(cuerpo, h("h1", {}, "Finalizar compra"), vacio("El carrito está vacío."), h("a", { href: "#/tienda" }, "Ver catálogo"));
  const t = c.presupuesto && c.presupuesto.totales;
  const f = {
    direccion: h("input", { required: true, maxlength: "255", autocomplete: "street-address" }),
    codigo_postal: h("input", { required: true, pattern: "\\d{5}", maxlength: "5", inputmode: "numeric", autocomplete: "postal-code" }),
    ciudad: h("input", { required: true, maxlength: "100", autocomplete: "address-level2" }),
    provincia: h("input", { required: true, maxlength: "100", autocomplete: "address-level1" }),
    metodo_pago: selector(PAGOS, "Tarjeta"),
  };
  const msg = h("p", { class: "msg ko", role: "alert" });
  montar(cuerpo,
    h("h1", {}, "Finalizar compra"),
    h("div", { class: "dos" },
      h("form", { onsubmit: conAviso(async (ev) => {
        ev.preventDefault();
        msg.textContent = "";
        const cuerpoPedido = Object.fromEntries(Object.entries(f).map(([k, el]) => [k, el.value.trim()]));
        let r;
        try { r = await post("/pedidos", cuerpoPedido, { idem: true }); }
        catch (e) { msg.textContent = e.message; return; }
        confirmacion(cuerpo, r);
      }) },
        h("h2", {}, "Dirección de envío"),
        campo("Dirección", f.direccion), campo("Código postal", f.codigo_postal),
        campo("Ciudad", f.ciudad), campo("Provincia", f.provincia),
        h("h2", {}, "Pago"), campo("Método de pago", f.metodo_pago,
          "Es una demo: no se cobra nada de verdad."),
        msg, h("button", { type: "submit", class: "primary" }, "Confirmar pedido")),
      t ? h("section", { class: "tarjeta" }, h("h2", {}, `${c.lineas.reduce((n, l) => n + l.cantidad, 0)} artículos`),
        h("dl", { class: "ficha total" },
          h("dt", {}, "Subtotal"), h("dd", {}, eur(t.gross_total)),
          h("dt", {}, "Descuentos"), h("dd", {}, `−${eur(Number(t.promo_discount) + Number(t.coupon_discount || 0))}`),
          h("dt", {}, "Envío"), h("dd", {}, eur(t.gastos_envio)),
          h("dt", {}, "Total"), h("dd", { class: "grande" }, eur(Number(t.net_total) + Number(t.gastos_envio || 0)))),
        h("a", { href: "#/tienda/carrito" }, "Volver al carrito")) : null));
  evento("begin_checkout", { page_type: "checkout" });
}

function confirmacion(cuerpo, o) {
  montar(cuerpo,
    h("section", { class: "tarjeta estrecha" },
      h("h1", {}, "Pedido confirmado"),
      h("p", {}, "Número ", h("strong", {}, o.order_id), " · ", insignia(o.order_status)),
      h("dl", { class: "ficha total" },
        h("dt", {}, "Total"), h("dd", { class: "grande" }, eur(o.order_total)),
        h("dt", {}, "Envío"), h("dd", {}, eur(o.shipping_amount)),
        h("dt", {}, "Fecha"), h("dd", {}, fechaHora(o.ordered_at))),
      h("div", { class: "fila" },
        h("a", { class: "boton primary", href: `#/pedidos/${o.order_id}` }, "Seguir el pedido"),
        h("a", { class: "boton", href: "#/tienda" }, "Seguir comprando"))));
}
