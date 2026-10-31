// FraSoHome Live · cliente de la API. Cookie de sesión HttpOnly + cabecera CSRF en las escrituras.

export class ApiError extends Error {
  constructor(estado, mensaje, codigo) {
    super(mensaje);
    this.estado = estado;
    this.codigo = codigo || null;
  }
}

// Una operación que mueve dinero o stock lleva Idempotency-Key. Si el usuario reintenta la misma petición
// (por un corte de red, por ejemplo) se reutiliza la clave; si cambia algo, la clave es otra.
const claves = new Map();
const huella = (ruta, cuerpo) => ruta + "\n" + JSON.stringify(cuerpo ?? null);
function claveDe(ruta, cuerpo) {
  const h = huella(ruta, cuerpo);
  if (!claves.has(h)) claves.set(h, crypto.randomUUID());
  return claves.get(h);
}

export function consulta(parametros) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(parametros || {})) {
    if (v !== null && v !== undefined && v !== "") q.set(k, v);
  }
  const s = q.toString();
  return s ? "?" + s : "";
}

export async function api(metodo, ruta, { cuerpo, idem = false, params } = {}) {
  const url = "/api" + ruta + consulta(params);
  const cabeceras = { Accept: "application/json" };
  if (metodo !== "GET") cabeceras["X-FSH-CSRF"] = "1";
  if (cuerpo !== undefined) cabeceras["Content-Type"] = "application/json";
  if (idem) cabeceras["Idempotency-Key"] = claveDe(ruta, cuerpo);
  let r;
  try {
    r = await fetch(url, { method: metodo, headers: cabeceras, credentials: "same-origin", cache: "no-store",
      body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo) });
  } catch (e) {
    throw new ApiError(0, "No se pudo conectar con el servicio. Comprueba la red y vuelve a intentarlo.", "red");
  }
  let datos = null;
  try { datos = await r.json(); } catch (e) { datos = null; }
  if (!r.ok) {
    const e = new ApiError(r.status, (datos && datos.error) || `Error ${r.status}.`, datos && datos.codigo);
    if (r.status === 401 && ruta !== "/auth/me" && ruta !== "/auth/login") document.dispatchEvent(new CustomEvent("fsh:sin-sesion"));
    if (e.codigo === "cambiar_contrasena") document.dispatchEvent(new CustomEvent("fsh:sin-sesion"));
    throw e;
  }
  if (idem) claves.delete(huella(ruta, cuerpo));
  return datos;
}

export const get = (ruta, params) => api("GET", ruta, { params });
export const post = (ruta, cuerpo = {}, opciones = {}) => api("POST", ruta, { cuerpo, ...opciones });
export const put = (ruta, cuerpo = {}) => api("PUT", ruta, { cuerpo });
export const borrar = (ruta) => api("DELETE", ruta);
