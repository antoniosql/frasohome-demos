// Escenario 15 · administración de datos: usuarios y roles, rechazos de la carga, metadatos, outbox y auditoría.
// El administrador ve todo; el profesor solo los rechazos de la carga y los metadatos.
import { get, post } from "../api.js";
import { aviso, cargando, conAviso, corta, dialogo, fechaHora, h, insignia, montar, num, paginador, pestanas, secreto, selector, tabla, tablaDinamica, vacio } from "../ui.js";
import { soloRol } from "../sesion.js";

const ROLES = ["cliente", "cajero", "tienda", "atencion", "marketing", "rrhh", "manager", "empleado", "direccion", "profesor", "admin"];
const AMBITOS = [["customer", "Cliente (C0001)"], ["employee", "Empleado (FSH0001)"], ["store", "Tienda (S001 u ONLINE)"]];

export async function render(cont, ctx) {
  const admin = soloRol("admin");
  const tabs = [];
  if (admin) tabs.push({ id: "", titulo: "Usuarios" });
  tabs.push({ id: "calidad", titulo: "Calidad de la carga" }, { id: "metadatos", titulo: "Catálogo y diccionarios" });
  if (admin) tabs.push({ id: "outbox", titulo: "Outbox" }, { id: "auditoria", titulo: "Auditoría" });
  const [sub] = ctx.partes;
  const activa = sub || (admin ? "" : "calidad");
  const cuerpo = h("div", {}, cargando());
  montar(cont, pestanas("datos", tabs, activa), cuerpo);
  if (activa === "calidad") return calidad(cuerpo, ctx);
  if (activa === "metadatos") return metadatos(cuerpo, ctx);
  if (admin && activa === "outbox") return outbox(cuerpo);
  if (admin && activa === "auditoria") return auditoria(cuerpo, ctx);
  if (admin) return usuarios(cuerpo);
  return calidad(cuerpo, ctx);
}

// ------------------------------------------------------------------ usuarios

const entregaClave = (r) => secreto(`Contraseña temporal de ${r.login}`, "Se muestra una sola vez. La persona deberá cambiarla en el primer acceso.", r.contrasena_temporal);

async function usuarios(cuerpo) {
  const filas = await get("/admin/usuarios");
  const recargar = () => usuarios(cuerpo);
  montar(cuerpo,
    h("div", { class: "fila entre" }, h("h1", {}, "Usuarios"),
      h("button", { type: "button", class: "primary", onclick: () => dialogo("Nuevo usuario", [
        { k: "login", etiqueta: "Usuario", maxlength: 50, req: true, ayuda: "Minúsculas, números, punto, guion o guion bajo (3 a 50)." },
        { k: "nombre", etiqueta: "Nombre visible", maxlength: 200, req: true },
        { k: "roles", etiqueta: "Roles, separados por coma", req: true, ayuda: ROLES.join(", ") },
        { k: "cliente", etiqueta: "Ámbito: cliente", maxlength: 5, ayuda: "Obligatorio para el rol cliente (C0001)" },
        { k: "empleado", etiqueta: "Ámbito: empleado", maxlength: 7, ayuda: "Obligatorio para empleado y manager (FSH0001)" },
        { k: "tienda", etiqueta: "Ámbito: tienda", maxlength: 6, ayuda: "Obligatorio para cajero y tienda (S001 u ONLINE)" },
      ], async (v) => {
        const ambitos = {};
        if (v.cliente) ambitos.customer = [v.cliente.toUpperCase()];
        if (v.empleado) ambitos.employee = [v.empleado.toUpperCase()];
        if (v.tienda) ambitos.store = v.tienda.split(",").map((x) => x.trim().toUpperCase());
        const r = await post("/admin/usuarios", { login: v.login, nombre: v.nombre, roles: v.roles.split(",").map((x) => x.trim().toLowerCase()).filter(Boolean), ambitos });
        aviso(`Usuario ${r.login} creado.`); recargar();
        if (r.contrasena_temporal) entregaClave(r);
      }, { enviar: "Crear usuario" }) }, "Nuevo usuario")),
    h("p", { class: "ayuda" }, "Las contraseñas nunca se guardan en claro: aquí solo se ve la temporal, una vez, al crear o reiniciar."),
    tabla([
      { t: "Usuario", f: (u) => h("strong", {}, u.login) }, { t: "Nombre", k: "display_name" },
      { t: "Roles", f: (u) => (u.roles.length ? u.roles.map((r) => h("span", { class: "insignia" }, r)) : "—") },
      { t: "Ámbitos", f: (u) => Object.entries(u.ambitos).map(([k, v]) => `${k}: ${v.join(", ")}`).join(" · ") || "—" },
      { t: "Estado", f: (u) => h("span", {}, insignia(u.is_active ? "Activo" : "Inactivo"), u.must_change_password ? h("small", {}, " cambio pendiente") : null) },
      { t: "", f: (u) => h("div", { class: "fila" },
        h("button", { type: "button", onclick: conAviso(async () => { entregaClave(await post(`/admin/usuarios/${u.login}/reset`, {})); aviso("Contraseña reiniciada."); }) }, "Reiniciar"),
        h("button", { type: "button", onclick: conAviso(async () => { await post(`/admin/usuarios/${u.login}/activo`, { activo: !u.is_active }); aviso(u.is_active ? "Usuario desactivado." : "Usuario activado."); recargar(); }) }, u.is_active ? "Desactivar" : "Activar"),
        h("button", { type: "button", onclick: () => dialogo(`Rol de ${u.login}`, [
          { k: "rol", etiqueta: "Rol", tipo: "select", opciones: ROLES, valor: ROLES[0] },
          { k: "conceder", etiqueta: "Acción", tipo: "select", opciones: [["si", "Conceder"], ["no", "Quitar"]], valor: "si" }],
          async (v) => { await post(`/admin/usuarios/${u.login}/roles`, { rol: v.rol, conceder: v.conceder === "si" }); aviso("Rol actualizado."); recargar(); }) }, "Rol"),
        h("button", { type: "button", onclick: () => dialogo(`Ámbito de ${u.login}`, [
          { k: "tipo", etiqueta: "Tipo", tipo: "select", opciones: AMBITOS, valor: "store" }, { k: "valor", etiqueta: "Valor", req: true, maxlength: 7 },
          { k: "conceder", etiqueta: "Acción", tipo: "select", opciones: [["si", "Conceder"], ["no", "Quitar"]], valor: "si" }],
          async (v) => { await post(`/admin/usuarios/${u.login}/ambitos`, { tipo: v.tipo, valor: v.valor.toUpperCase(), conceder: v.conceder === "si" }); aviso("Ámbito actualizado."); recargar(); }) }, "Ámbito")) },
    ], filas));
}

// ------------------------------------------------------------------ calidad de la carga

async function calidad(cuerpo, ctx) {
  const p = ctx.params;
  const pagina = Number(p.get("pagina") || 1);
  const f = { tabla: p.get("tabla") || "", gravedad: p.get("gravedad") || "", tipo: p.get("tipo") || "" };
  const [resumen, det] = await Promise.all([get("/admin/calidad/resumen"), get("/admin/calidad", { ...f, pagina, tamano: 50 })]);
  const ir = (n, g = f) => {
    const s = new URLSearchParams();
    for (const [k, v] of Object.entries(g)) if (v) s.set(k, v);
    if (n > 1) s.set("pagina", n);
    ctx.ir("/datos/calidad" + (s.toString() ? "?" + s : ""));
  };
  const tabla_ = h("input", { value: f.tabla, placeholder: "Tabla (customer…)", "aria-label": "Tabla" });
  const grav = selector([["", "Cualquier gravedad"], "alta", "media", "baja"], f.gravedad, { "aria-label": "Gravedad" });
  montar(cuerpo, h("h1", {}, "Calidad de la carga"),
    h("p", { class: "ayuda" }, "Lo que la carga inicial corrigió o rechazó al pasar los CSV a Azure SQL, agrupado por fichero y tipo."),
    resumen.length ? tabla([{ t: "Fichero", k: "source_file" }, { t: "Tabla", f: (r) => `${r.source_schema}.${r.source_table}` }, { t: "Gravedad", f: (r) => r.issue_severity },
      { t: "Tipo", k: "issue_type" }, { t: "Filas", f: (r) => num(r.filas), cls: "num" }],
      resumen, { alClic: (r) => ir(1, { tabla: r.source_table, gravedad: r.issue_severity, tipo: r.issue_type }) }) : vacio("No hay incidencias de calidad."),
    h("h2", {}, `Incidencias (${num(det.total)})`),
    h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); ir(1, { tabla: tabla_.value.trim(), gravedad: grav.value, tipo: f.tipo }); } }, tabla_, grav, h("button", { type: "submit" }, "Filtrar")),
    tabla([{ t: "Id", k: "issue_id" }, { t: "Tabla", k: "source_table" }, { t: "Clave", f: (i) => i.source_key || "—" }, { t: "Gravedad", f: (i) => i.issue_severity }, { t: "Tipo", k: "issue_type" },
      { t: "Descripción", f: (i) => corta(i.issue_description, 120) }, { t: "Fila de origen", f: (i) => corta(i.source_row, 60) }], det.incidencias, { sinDatos: "No hay incidencias con esos filtros." }),
    paginador(pagina, det.total, 50, (n) => ir(n)));
}

// ------------------------------------------------------------------ metadatos

async function metadatos(cuerpo, ctx) {
  const fichero = ctx.params.get("fichero") || "";
  if (fichero) {
    const filas = await get("/admin/metadatos/filas", { fichero });
    return montar(cuerpo, h("p", {}, h("a", { href: "#/datos/metadatos" }, "‹ Catálogo")), h("h1", {}, fichero.split("/").pop()), h("p", { class: "ayuda" }, `${num(filas.length)} filas`), tablaDinamica(filas, { max: 120 }));
  }
  const lista = await get("/admin/metadatos");
  montar(cuerpo, h("h1", {}, "Catálogo y diccionarios"),
    h("p", { class: "ayuda" }, "Los ficheros de referencia (catálogo de datos, diccionarios, mapeos) viven en la base como tablas meta.*. Abre uno para ver sus filas."),
    tabla([{ t: "Fichero", k: "file_path" }, { t: "Descripción", f: (m) => corta(m.description, 90) }, { t: "Columnas", f: (m) => corta(m.column_list, 70) }, { t: "Filas", f: (m) => num(m.filas), cls: "num" }],
      lista, { alClic: (m) => ctx.ir(`/datos/metadatos?fichero=${encodeURIComponent(m.file_path)}`) }));
}

// ------------------------------------------------------------------ outbox y auditoría

async function outbox(cuerpo) {
  const r = await get("/admin/outbox");
  montar(cuerpo, h("h1", {}, "Outbox hacia Cosmos DB"),
    h("p", { class: "ayuda" }, "Cada escritura va primero a SQL y después a Cosmos DB. Si Cosmos falla, el evento espera aquí y se reintenta en la siguiente escritura."),
    h("div", { class: "kpis" }, h("div", { class: "tarjeta" }, h("small", {}, "Pendientes"), h("p", { class: "grande" }, num(r.pendientes)))),
    h("button", { type: "button", class: "primary", onclick: conAviso(async () => {
      const x = await post("/admin/outbox/reintentar", {});
      aviso(`Reintento hecho: ${Object.entries(x).map(([k, v]) => `${k} ${v}`).join(", ")}.`); outbox(cuerpo);
    }) }, "Reintentar pendientes"),
    h("h2", {}, "Con errores"),
    tabla([{ t: "Id", k: "outbox_id" }, { t: "Contenedor", k: "container_name" }, { t: "Operación", k: "operation" }, { t: "Creado", f: (o) => fechaHora(o.created_at) },
      { t: "Intentos", k: "attempts", cls: "num" }, { t: "Último error", f: (o) => corta(o.last_error, 120) }], r.fallidos, { sinDatos: "No hay eventos con errores." }));
}

async function auditoria(cuerpo, ctx) {
  const pagina = Number(ctx.params.get("pagina") || 1);
  const usuario = ctx.params.get("usuario") || "";
  const filas = await get("/admin/auditoria", { usuario: usuario || undefined, pagina, tamano: 50 });
  const f = h("input", { value: usuario, placeholder: "Usuario", "aria-label": "Usuario" });
  const ir = (n) => ctx.ir(`/datos/auditoria?${new URLSearchParams({ ...(usuario ? { usuario } : {}), pagina: n })}`);
  montar(cuerpo, h("h1", {}, "Auditoría"),
    h("form", { class: "filtros", onsubmit: (ev) => { ev.preventDefault(); ctx.ir("/datos/auditoria" + (f.value.trim() ? `?usuario=${encodeURIComponent(f.value.trim())}` : "")); } }, f, h("button", { type: "submit" }, "Filtrar")),
    tabla([{ t: "Fecha", f: (a) => fechaHora(a.logged_at) }, { t: "Usuario", f: (a) => a.user_login || "—" }, { t: "Acción", k: "action_name" }, { t: "Entidad", f: (a) => `${a.entity_name || ""} ${a.entity_id || ""}`.trim() || "—" },
      { t: "Detalle", f: (a) => corta(a.detail, 90) }], filas, { sinDatos: "Sin registros." }),
    h("div", { class: "paginador" }, h("button", { type: "button", disabled: pagina <= 1, onclick: () => ir(pagina - 1) }, "‹ Anterior"), h("span", {}, `Página ${pagina}`),
      h("button", { type: "button", disabled: filas.length < 50, onclick: () => ir(pagina + 1) }, "Siguiente ›")));
}
