// FraSoHome Live · estado de la sesión en el navegador. La verdad está en el servidor (cookie HttpOnly):
// esto solo guarda lo que devuelve /api/auth/me para pintar el menú.
import { get } from "./api.js";

export const sesion = { usuario: null };

export async function refrescar() {
  try { sesion.usuario = (await get("/auth/me")).usuario; }
  catch (e) { sesion.usuario = null; }
  return sesion.usuario;
}

/** ¿Tiene alguno de estos roles? El administrador pasa todas las comprobaciones, igual que en la API. */
export function tieneRol(...roles) {
  const u = sesion.usuario;
  return !!u && (u.roles.includes("admin") || roles.some((r) => u.roles.includes(r)));
}

export const soloRol = (rol) => !!sesion.usuario && sesion.usuario.roles.includes(rol);
export const ambito = (tipo) => (sesion.usuario && sesion.usuario.ambitos[tipo]) || [];
