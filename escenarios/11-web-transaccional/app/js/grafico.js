// FraSoHome Live · gráficos SVG sin dependencias: columnas apiladas y líneas.
// Colores de series en CSS (--serie-1, --serie-2), con pasos propios para el modo oscuro; cada gráfico lleva
// leyenda cuando hay más de una serie, información al pasar el ratón y, en quien lo use, una tabla equivalente.
import { h } from "./ui.js";

const NS = "http://www.w3.org/2000/svg";
const svg = (tag, attrs = {}, ...hijos) => {
  const el = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) if (v !== null && v !== undefined) el.setAttribute(k, v);
  for (const hijo of hijos.flat()) if (hijo) el.append(hijo);
  return el;
};

const COMPACTO = new Intl.NumberFormat("es-ES", { notation: "compact", maximumFractionDigits: 1 });
const W = 720, M = { i: 52, d: 8, s: 10, b: 26 };

function escala(max) {
  if (max <= 0) return { max: 1, marcas: [0, 1] };
  const paso0 = max / 4, pot = 10 ** Math.floor(Math.log10(paso0));
  const paso = [1, 2, 2.5, 5, 10].map((m) => m * pot).find((p) => p >= paso0);
  const tope = Math.ceil(max / paso) * paso;
  const marcas = [];
  for (let v = 0; v <= tope + 1e-9; v += paso) marcas.push(v);
  return { max: tope, marcas };
}

function armazon({ etiquetas, series, formato, alto, apilado, resumen }) {
  const H = alto;
  const n = etiquetas.length;
  const totales = etiquetas.map((_, i) => (apilado ? series.reduce((s, x) => s + (Number(x.valores[i]) || 0), 0) : Math.max(...series.map((x) => Number(x.valores[i]) || 0))));
  const maxVal = Math.max(0, ...totales, ...(apilado ? [] : series.flatMap((x) => x.valores.map(Number))));
  const { max, marcas } = escala(maxVal);
  const iw = W - M.i - M.d, ih = H - M.s - M.b;
  const y = (v) => M.s + ih - (v / max) * ih;
  const banda = iw / Math.max(n, 1);
  const x = (i) => M.i + banda * i + banda / 2;

  const raiz = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": resumen, class: "grafico-svg" });
  for (const m of marcas) {
    raiz.append(svg("line", { x1: M.i, x2: W - M.d, y1: y(m), y2: y(m), class: m === 0 ? "eje" : "rejilla" }));
    const t = svg("text", { x: M.i - 6, y: y(m) + 4, "text-anchor": "end", class: "marca-eje" });
    t.textContent = COMPACTO.format(m);
    raiz.append(t);
  }
  const cada = Math.max(1, Math.ceil(n / 7));
  etiquetas.forEach((e, i) => {
    if (i % cada) return;
    const t = svg("text", { x: x(i), y: H - 6, "text-anchor": "middle", class: "marca-eje" });
    t.textContent = e;
    raiz.append(t);
  });
  return { raiz, n, x, y, banda, totales, ih, iw };
}

function envoltorio(raiz, etiquetas, series, formato, apilado) {
  const tip = h("div", { class: "grafico-tip", role: "status", hidden: true });
  const caja = h("div", { class: "grafico" },
    series.length > 1 ? h("ul", { class: "leyenda" }, series.map((s, i) => h("li", {}, h("span", { class: "muestra", style: `background:var(--serie-${i + 1})` }), s.nombre))) : null,
    h("div", { class: "grafico-lienzo" }, raiz, tip));
  const mostrar = (i, px) => {
    tip.hidden = false;
    tip.replaceChildren(h("strong", {}, etiquetas[i]),
      ...series.map((s, k) => h("div", {}, h("span", { class: "muestra", style: `background:var(--serie-${k + 1})` }), `${s.nombre}: ${formato(s.valores[i])}`)),
      ...(apilado && series.length > 1 ? [h("div", { class: "total" }, `Total: ${formato(series.reduce((a, s) => a + (Number(s.valores[i]) || 0), 0))}`)] : []));
    const ancho = caja.querySelector(".grafico-lienzo").clientWidth;
    tip.style.left = `${Math.min(Math.max(px, 60), ancho - 60)}px`;
  };
  return { caja, mostrar, ocultar: () => { tip.hidden = true; } };
}

/** Columnas apiladas (o una sola serie). series: [{ nombre, valores }]. */
export function columnas({ etiquetas, series, formato = (v) => String(v), alto = 240, resumen = "Gráfico de columnas" }) {
  const g = armazon({ etiquetas, series, formato, alto, apilado: true, resumen });
  const { raiz, n, x, y, banda } = g;
  const ancho = Math.max(2, banda * 0.7);
  const guia = svg("rect", { class: "guia", x: 0, y: M.s, width: banda, height: g.ih, visibility: "hidden" });
  raiz.append(guia);
  for (let i = 0; i < n; i++) {
    let base = 0;
    series.forEach((s, k) => {
      const v = Number(s.valores[i]) || 0;
      if (v <= 0) return;
      const arriba = y(base + v), abajo = y(base);
      const alt = Math.max(0, abajo - arriba - (base > 0 ? 2 : 0));   // 2 px de hueco entre segmentos
      raiz.append(svg("rect", { x: x(i) - ancho / 2, y: arriba, width: ancho, height: alt, rx: Math.min(2, ancho / 2), fill: `var(--serie-${k + 1})` }));
      base += v;
    });
  }
  const { caja, mostrar, ocultar } = envoltorio(raiz, etiquetas, series, formato, true);
  for (let i = 0; i < n; i++) {
    const zona = svg("rect", { x: x(i) - banda / 2, y: M.s, width: banda, height: g.ih, fill: "transparent" });
    zona.addEventListener("mouseenter", () => { guia.setAttribute("x", x(i) - banda / 2); guia.setAttribute("visibility", "visible"); mostrar(i, (x(i) / W) * caja.querySelector(".grafico-lienzo").clientWidth); });
    zona.addEventListener("mouseleave", () => { guia.setAttribute("visibility", "hidden"); ocultar(); });
    raiz.append(zona);
  }
  return caja;
}

/** Líneas de una o varias series. */
export function linea({ etiquetas, series, formato = (v) => String(v), alto = 240, resumen = "Gráfico de líneas" }) {
  const g = armazon({ etiquetas, series, formato, alto, apilado: false, resumen });
  const { raiz, n, x, y, banda } = g;
  series.forEach((s, k) => {
    const puntos = s.valores.map((v, i) => (v === null || v === undefined ? null : [x(i), y(Number(v))]));
    let d = "", abierto = false;
    puntos.forEach((p) => { if (!p) { abierto = false; return; } d += `${abierto ? "L" : "M"}${p[0].toFixed(1)},${p[1].toFixed(1)}`; abierto = true; });
    raiz.append(svg("path", { d, fill: "none", stroke: `var(--serie-${k + 1})`, "stroke-width": 2, "stroke-linejoin": "round", "stroke-linecap": "round" }));
  });
  const cruz = svg("line", { class: "guia-linea", y1: M.s, y2: M.s + g.ih, visibility: "hidden" });
  const marcas = series.map((_, k) => svg("circle", { r: 4, fill: `var(--serie-${k + 1})`, class: "punto", visibility: "hidden" }));
  raiz.append(cruz, ...marcas);
  const { caja, mostrar, ocultar } = envoltorio(raiz, etiquetas, series, formato, false);
  for (let i = 0; i < n; i++) {
    const zona = svg("rect", { x: x(i) - banda / 2, y: M.s, width: banda, height: g.ih, fill: "transparent" });
    zona.addEventListener("mouseenter", () => {
      cruz.setAttribute("x1", x(i)); cruz.setAttribute("x2", x(i)); cruz.setAttribute("visibility", "visible");
      marcas.forEach((m, k) => {
        const v = series[k].valores[i];
        if (v === null || v === undefined) { m.setAttribute("visibility", "hidden"); return; }
        m.setAttribute("cx", x(i)); m.setAttribute("cy", y(Number(v))); m.setAttribute("visibility", "visible");
      });
      mostrar(i, (x(i) / W) * caja.querySelector(".grafico-lienzo").clientWidth);
    });
    zona.addEventListener("mouseleave", () => { cruz.setAttribute("visibility", "hidden"); marcas.forEach((m) => m.setAttribute("visibility", "hidden")); ocultar(); });
    raiz.append(zona);
  }
  return caja;
}
