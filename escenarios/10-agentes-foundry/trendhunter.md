# Sistema Multi-Agente: FraSoHome TrendHunter
## Detección de tendencias y generación de propuestas para retail de hogar
### Diseño Completo para Foundry Agent Service

---

## 1. Análisis del Problema

**Empresa**: FraSoHome — cadena de tiendas de muebles y decoración B2C omnicanal
**Categorías**: Muebles, Iluminación, Textil hogar, Decoración
**Necesidad**: Detectar tendencias emergentes en interiorismo y hogar para anticipar la demanda, ajustar el surtido y crear colecciones cápsula que diferencien a FraSoHome de grandes superficies (IKEA, Maisons du Monde, Leroy Merlin).

**Desglose en sub-tareas**:
1. **Detectar** tendencias en diseño de interiores, materiales, colores y estilos de vida
2. **Cruzar** con datos internos de FraSoHome (qué se vende, qué se devuelve, qué stock hay)
3. **Generar** propuestas de producto o colección adaptadas al catálogo y posicionamiento
4. **Compilar** un brief de compras y merchandising accionable

---

## 2. Arquitectura Multi-Agente

### Patrón de Workflow: **Sequential**

```
┌────────────────┐     ┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│  TrendScout    │────>│  CatalogMatch  │────>│ CollectionArch │────>│  BuyingBrief   │
│    Agent       │     │    Agent       │     │    Agent       │     │    Agent       │
└────────────────┘     └────────────────┘     └────────────────┘     └────────────────┘
       │                      │                      │                      │
  Web Search             Code Interpreter        File Search           Code Interpreter
  File Search            File Search             Web Search            File Search

  KB: mercado hogar      KB: catálogo FraSoHome  KB: catálogo          KB: plantilla brief
  KB: competidores       KB: datos ventas        KB: proveedores       KB: calendario retail
```

La diferencia clave respecto al TrendHunter de Adidas: aquí el segundo agente (CatalogMatch) cruza tendencias con datos internos reales de ventas, stock y devoluciones de FraSoHome — no solo analiza el mercado externo, sino que busca el encaje con lo que ya funciona (y lo que no) en la empresa.

### Variables del Workflow

| Variable | Tipo | Descripción |
|----------|------|-------------|
| `trend_scan` | JSON | Tendencias detectadas por TrendScout |
| `catalog_fit` | JSON | Análisis de encaje tendencia ↔ catálogo/ventas por CatalogMatch |
| `collection_proposals` | JSON | Propuestas de colección/producto por CollectionArch |
| `buying_brief` | Markdown | Brief de compras final por BuyingBrief |

---

## 3. Bases de Conocimiento

### KB1: `frasohome_mercado_hogar.md`

```markdown
# Mercado de Muebles y Decoración — Datos de Referencia

## Tamaño de Mercado
- Muebles España 2025: ~9.200M€ (Observatorio Cetelem)
- Decoración y textil hogar España: ~3.800M€
- Canal online: 22% del total (creciendo +8% anual)
- CAGR 2025-2030: ~3.2% (muebles), ~5.1% (decoración online)

## Tendencias Macro en Interiorismo (últimos 18 meses)
- Japandi: fusión minimalismo japonés + diseño escandinavo. Madera clara, líneas limpias, funcionalidad
- Quiet luxury: materiales nobles, tonos neutros, ausencia de logos, acabados artesanales
- Biophilic design: plantas, materiales naturales, luz natural, conexión con la naturaleza
- Curvas y formas orgánicas: sofás curvos, mesas ovaladas, espejos irregulares
- Boucle y texturas táctiles: telas con textura (boucle, teddy, lino grueso) en tapicería y cojines
- Terracotta / earth tones: paleta cálida terrosa, cerámica, barro
- Sostenibilidad verificable: materiales reciclados, madera certificada, producción local
- Multifuncional / small spaces: muebles transformables, almacenaje oculto, modularidad
- Vintage revival: piezas de aspecto retro (70s, Art Deco), mercado segunda mano
- Smart home integrado: iluminación inteligente, carga inalámbrica en muebles, domótica discreta
- Maximalismo controlado: mezcla de patrones, color en paredes, galerías de arte personal
- Cocina como centro social: islas grandes, taburetes diseño, iluminación statement
- Home office permanente: escritorios integrados en salón, acústica, ergonomía estética

## Canales de Detección de Tendencias
- Pinterest: tableros de "home decor", "interior design 2026", "living room ideas"
- Instagram: #homedecor, #interiordesign, #scandinaviandesign, #midcenturymodern
- TikTok: #roomtransformation, #homedecortips, #ikeahack, #thriftedhome
- Ferias: Maison & Objet (París), IMM Cologne, Salone del Mobile (Milán), Hábitat Valencia
- Revistas/blogs: AD, Elle Decor, Architectural Digest, The Spruce, Apartment Therapy
- Influencers clave: @the_modern_house, @em_henderson, @studiomcgee

## Estacionalidad del Sector
- Enero-marzo: rebajas + renovación post-navidad (pico de búsquedas "decorar salón")
- Abril-junio: terraza y exterior, textil primavera
- Septiembre-octubre: vuelta a rutina, renovación dormitorios, iluminación (días más cortos)
- Noviembre-diciembre: regalos decoración, iluminación navideña, textil invierno
```

### KB2: `frasohome_competidores.md`

```markdown
# Competidores de FraSoHome

## Grandes Superficies
- **IKEA**: Líder volumen. Diseño democrático, precio bajo, rotación rápida. Debilidad: masificación, calidad percibida limitada.
- **Leroy Merlin**: Fuerte en bricolaje + decoración. Debilidad: imagen más "obra" que "hogar".
- **Maisons du Monde**: Estilo boho/colonial, decoración aspiracional a precio medio. Fuerte online.
- **Conforama**: Precio agresivo, mueble funcional. Débil en diseño y experiencia.

## Especialistas
- **Kenay Home**: Online-first, estilo nórdico-mediterráneo, precio medio-alto. Muy Instagram.
- **Kave Home**: Diseño propio, precio medio, fuerte crecimiento online. Showrooms selectos.
- **Banak Importa / Tikamoon**: Madera maciza, estilo colonial/natural, precio medio-alto.
- **Zara Home** (ahora integrado en Zara): Textil, vajilla, velas. No muebles grandes.
- **H&M Home**: Textil y decoración pequeña, tendencias fast-fashion aplicadas al hogar.

## Posicionamiento FraSoHome
- Precio: medio (entre IKEA y Kenay)
- Surtido: generalista pero curado (no catálogo infinito)
- Fortaleza: presencia física + online, programa de fidelización
- Oportunidad: colecciones cápsula temáticas que grandes superficies no pueden hacer rápido
- Target: 28-50 años, parejas y familias, interesados en un hogar "bonito pero asequible"
```

### KB3: `frasohome_catalogo_actual.md`

```markdown
# Catálogo Actual FraSoHome

## Muebles (~45% de facturación)
### Salón
- Sofás: 3 plazas, chaise longue, modulares. Materiales: tela, piel sintética. Rango: 450-1.200€
- Mesas de centro: madera, cristal, mármol efecto. Rango: 80-350€
- Estanterías y aparadores: madera, metal+madera. Rango: 150-600€
- Muebles TV: suspendidos, con almacenaje. Rango: 120-400€

### Dormitorio
- Camas con canapé: 150cm, 160cm, 180cm. Madera, tapizadas. Rango: 300-900€
- Mesitas de noche: 1-2 cajones. Rango: 60-200€
- Cómodas: 3-5 cajones, madera. Rango: 150-450€
- Armarios: correderas, batientes, modulares. Rango: 400-1.500€

### Comedor
- Mesas de comedor: extensibles, fijas. 4-8 comensales. Rango: 200-800€
- Sillas: madera, tapizadas, metal. Rango: 40-180€ /ud

### Exterior (estacional)
- Conjuntos terraza: ratán sintético, aluminio. Rango: 300-1.200€
- Tumbonas y hamacas. Rango: 80-300€

## Iluminación (~15% de facturación)
- Lámparas de techo: plafones, colgantes, arañas. Rango: 30-350€
- Lámparas de pie y mesa: diseño, lectura, ambiente. Rango: 25-200€
- Tiras LED y iluminación funcional. Rango: 10-60€
- Apliques de pared. Rango: 20-120€

## Textil Hogar (~20% de facturación)
- Cortinas y estores: opacos, translúcidos, enrollables. Rango: 20-150€
- Ropa de cama: fundas nórdicas, sábanas, almohadas. Rango: 25-120€
- Alfombras: salón (160x230), pasillo, pie de cama. Rango: 40-300€
- Cojines y mantas: decorativos. Rango: 8-45€
- Toallas y textil baño. Rango: 5-30€

## Decoración (~20% de facturación)
- Cuadros y láminas: abstracto, botánico, fotografía. Rango: 15-120€
- Espejos: redondos, irregulares, con marco. Rango: 30-200€
- Jarrones y maceteros: cerámica, vidrio, cemento. Rango: 10-80€
- Velas y aromas: velas de soja, difusores. Rango: 8-40€
- Cestas y organizadores: fibra natural, tela. Rango: 10-50€
- Relojería y objetos decorativos: relojes pared, figuras. Rango: 15-80€

## Proveedores Principales
- Mueble tapizado: 3 fabricantes nacionales (Valencia, Yecla)
- Mueble madera: importación Europa del Este + Portugal
- Iluminación: importación China + diseño propio
- Textil: fabricantes Turquía + Portugal + India
- Decoración: mix importación (China, India) + artesanos locales

## Datos Operativos
- Margen medio bruto: 48% (muebles), 55% (iluminación), 60% (textil), 65% (decoración)
- Tasa de devolución media: 8% (muebles), 3% (decoración), 12% (textil online)
- Ticket medio tienda: 185€. Ticket medio online: 95€
- Lead time nuevo producto: 8-12 semanas (mueble), 4-6 semanas (decoración/textil)
```

### KB4: `frasohome_plantilla_brief_compras.md`

```markdown
# Plantilla de Brief de Compras — FraSoHome TrendHunter

## Para cada propuesta de colección o producto:

### Identidad de la Propuesta
- **Nombre de colección**: [nombre evocador, ej: "Tierra Calma"]
- **Categorías implicadas**: [Muebles / Iluminación / Textil / Decoración]
- **Nº de SKUs estimado**: [rango]
- **Tipo**: [Colección cápsula / Ampliación de línea / Producto individual / Colaboración]

### Tendencia Detectada
- **Tendencia base**: [nombre]
- **Nivel de madurez**: [Emergente / En crecimiento / Mainstream]
- **Ventana de oportunidad**: [meses estimados de relevancia]
- **Fuentes de señal**: [Pinterest, ferias, RRSS, revistas...]

### Propuesta de Producto
- **Piezas clave** (3-5): [descripción de cada pieza anchor]
- **Paleta de colores**: [Pantone o nombres descriptivos]
- **Materiales**: [madera, tela, metal, cerámica... + origen sostenible si aplica]
- **Estilo visual**: [descripción del mood en 2-3 frases]
- **Diferenciación vs. competencia**: [qué no encontrarás en IKEA/Maisons]

### Análisis Comercial
- **Encaje con ventas actuales**: [qué productos actuales son afines]
- **Productos de bajo rendimiento a sustituir**: [SKUs candidatos a descatalogar]
- **Rango de precios objetivo**: [€ por categoría]
- **Margen bruto esperado**: [%]
- **Canal prioritario**: [tienda / online / ambos]
- **Target cliente**: [perfil + nivel fidelización CRM]

### Calendario
- **Temporada sugerida**: [SS26 / FW26 / Permanente]
- **Deadline pedido a proveedor**: [fecha]
- **Lanzamiento estimado**: [fecha]
- **Acciones de marketing**: [3 bullet points]

### Viabilidad
- **Lead time producción**: [semanas]
- **Proveedores candidatos**: [existentes vs. nuevos]
- **Inversión estimada en stock**: [€]
- **Riesgo**: [Alto / Medio / Bajo + justificación]
- **Score total (1-10)**: [ponderación]
```

### KB5: `frasohome_calendario_retail.md`

```markdown
# Calendario Retail FraSoHome

## Temporadas Comerciales
| Periodo | Foco | Deadline Pedido | Lanzamiento |
|---------|------|-----------------|-------------|
| SS26 (Primavera-Verano) | Exterior, textil ligero, colores claros | Diciembre 2025 | Marzo 2026 |
| FW26 (Otoño-Invierno) | Textil cálido, iluminación, comfort | Junio 2026 | Septiembre 2026 |
| Navidad 2026 | Decoración, velas, regalos, iluminación | Agosto 2026 | Noviembre 2026 |
| Rebajas Enero 2027 | Liquidación stock, impulso renovación | N/A | Enero 2027 |

## Eventos Clave del Sector
- Enero: IMM Cologne, Maison & Objet París (detección tendencias)
- Abril: Salone del Mobile Milán
- Septiembre: Maison & Objet París (colecciones FW)
- Octubre: Hábitat Valencia

## Campañas Marketing FraSoHome
- "Renueva tu hogar" (enero-febrero): post-rebajas, foco salón y dormitorio
- "Terraza lista" (abril-mayo): exterior + textil
- "Vuelta a casa" (septiembre): confort, iluminación, dormitorios
- "Regala hogar" (noviembre-diciembre): decoración, velas, textil regalo

## Lead Times por Categoría
- Mueble tapizado: 10-12 semanas
- Mueble madera: 8-10 semanas
- Iluminación: 6-8 semanas
- Textil: 4-6 semanas
- Decoración pequeña: 3-5 semanas
```

---

## 4. Definición de los Agentes

---

### AGENTE 1: TrendScout Agent

**Herramientas**: ✅ Web Search + ✅ File Search (KB1: mercado hogar, KB2: competidores)

**System Prompt**:

```
Eres TrendScout, un coolhunter especializado en interiorismo, muebles y decoración del hogar. Trabajas para FraSoHome, una cadena de tiendas de muebles y decoración B2C omnicanal en España.

## Tu misión
Detectar tendencias emergentes en diseño de interiores, materiales, colores, estilos de vida y hábitos de consumo doméstico que FraSoHome pueda capitalizar con nuevos productos o colecciones.

## Proceso de trabajo

1. Busca en la web tendencias actuales en estas categorías:
   - Estilos de interiorismo (japandi, maximalismo, coastal, wabi-sabi...)
   - Materiales y acabados (boucle, ratán, mármol, terrazo, madera reciclada...)
   - Paletas de color emergentes (Pantone del año, earth tones, dopamine decor...)
   - Formatos de mueble (modular, multifuncional, curvo, oversized...)
   - Iluminación (statement pieces, smart lighting, biophilic...)
   - Textil (texturas, estampados, sostenibilidad, performance fabrics...)
   - Lifestyle (home office, entertaining at home, small spaces, pet-friendly...)

2. Para cada tendencia, busca al menos 3 fuentes independientes que la confirmen
   (Pinterest trends, artículos de AD/Elle Decor, ferias, TikTok, tiendas online)

3. Clasifica cada tendencia:
   - EMERGENTE: señales incipientes, nichos creativos, influencers early adopter (<6 meses)
   - EN CRECIMIENTO: aparece en retailers de gama media, búsquedas Pinterest creciendo (6-18 meses)
   - MAINSTREAM: ya en IKEA o Maisons du Monde (>18 meses, riesgo de saturación)

4. Consulta los datos de competidores para identificar HUECOS: tendencias donde IKEA,
   Maisons du Monde o Kave Home aún no tienen oferta clara = oportunidad para FraSoHome

5. Prioriza tendencias EMERGENTES y EN CRECIMIENTO que encajen con el target de FraSoHome
   (28-50 años, parejas y familias, "bonito pero asequible")

## Formato de output
Devuelve EXCLUSIVAMENTE un JSON:
{
  "scan_date": "YYYY-MM-DD",
  "trends": [
    {
      "id": "TREND-001",
      "name": "nombre corto",
      "category": "Estilo | Material | Color | Formato | Iluminación | Textil | Lifestyle",
      "description": "descripción en 2-3 frases orientadas a producto",
      "maturity": "EMERGENTE | EN_CRECIMIENTO | MAINSTREAM",
      "signals": ["señal concreta 1", "señal 2", "señal 3"],
      "sources": ["fuente 1", "fuente 2"],
      "applicable_to": ["Muebles", "Iluminación", "Textil hogar", "Decoración"],
      "competitor_gap": "qué NO tiene la competencia en esta tendencia",
      "seasonality": "SS26 | FW26 | Permanente | Navidad",
      "target_fit": "por qué encaja con el cliente FraSoHome"
    }
  ]
}

## Reglas
- Detecta entre 6 y 10 tendencias
- Al menos 2 deben ser EMERGENTES (eso es lo que da ventaja competitiva)
- NO listes tendencias genéricas ("muebles bonitos") — sé específico y accionable
- Cada tendencia debe poder traducirse en al menos un producto concreto
- Piensa en el cliente real de FraSoHome: no ultra-lujo, no ultra-básico
- Busca combinaciones inesperadas que creen diferenciación (ej: "japandi + smart home")
```

**Variable de salida**: `trend_scan`

---

### AGENTE 2: CatalogMatch Agent

**Herramientas**: ✅ Code Interpreter + ✅ File Search (KB3: catálogo actual)

**System Prompt**:

```
Eres CatalogMatch, un agente de inteligencia comercial que cruza tendencias de mercado con los datos internos de FraSoHome para identificar oportunidades de negocio concretas.

## Tu misión
Tomar las tendencias detectadas por TrendScout y analizarlas contra el catálogo actual, los datos de ventas y el posicionamiento de FraSoHome para determinar cuáles tienen mayor potencial de retorno.

## Input
Tendencias detectadas: {{trend_scan}}

## Proceso de análisis

Para cada tendencia, evalúa 6 dimensiones (1-10):

1. **Catalog Affinity** (1-10): ¿Cuántos productos actuales de FraSoHome ya se acercan a esta
   tendencia? Si hay 15 sofás de línea recta y la tendencia es "formas curvas", la afinidad es
   baja pero la oportunidad alta. Si la afinidad es alta, puede ejecutarse con ajustes mínimos.

2. **Revenue Potential** (1-10): Basándote en el catálogo actual y los márgenes por categoría,
   ¿cuánto ingreso incremental podría generar? Decoración tiene margen alto (65%) pero ticket
   bajo. Muebles tiene margen menor (48%) pero ticket alto.

3. **Execution Speed** (1-10): ¿Puede FraSoHome ejecutar esto rápido? Textil y decoración = 4-6
   semanas (puntuación alta). Mueble tapizado = 10-12 semanas (puntuación media). Proveedor
   nuevo = puntuación baja.

4. **Differentiation** (1-10): ¿Esto diferencia a FraSoHome de IKEA, Maisons du Monde y Kave?
   Si la competencia ya lo tiene = 1. Si nadie lo hace en el segmento medio = 10.

5. **Customer Demand Signal** (1-10): ¿Hay señales en los datos de FraSoHome de que los clientes
   ya buscan esto? Considerar: categorías con alta tasa de devolución (insatisfacción con oferta
   actual), productos con alto descuento (no se venden a PVP), búsquedas en e-commerce.

6. **Risk Level** (invertido, 10=bajo riesgo): ¿Cuánto stock se queda si la tendencia no cuaja?
   Artículos pequeños de decoración = bajo riesgo. Sofás caros = alto riesgo.

## Cálculo del Score
Score = (Affinity × 0.10) + (Revenue × 0.25) + (Speed × 0.20) + (Differentiation × 0.20) + (Demand × 0.15) + (Risk × 0.10)

Usa Code Interpreter para:
- Calcular scores ponderados
- Generar ranking ordenado
- Crear scatter plot: eje X = Revenue Potential, eje Y = Execution Speed, tamaño = Score total
- Identificar las 3 tendencias con mejor balance score/riesgo

## Enriquecimiento con datos internos
Para cada tendencia top 3, identifica:
- 3-5 productos actuales del catálogo que podrían "pivotarse" hacia la tendencia
- Productos de bajo rendimiento (alto descuento, alta devolución) que podrían sustituirse
- Proveedores existentes capaces de producir la nueva propuesta

## Formato de output
{
  "analysis_date": "YYYY-MM-DD",
  "trends_scored": [
    {
      "trend_id": "TREND-001",
      "trend_name": "nombre",
      "scores": {
        "catalog_affinity": 7,
        "revenue_potential": 8,
        "execution_speed": 6,
        "differentiation": 9,
        "customer_demand": 5,
        "risk_inverted": 7
      },
      "total_score": 7.15,
      "recommendation": "DEVELOP | MONITOR | SKIP",
      "related_current_products": ["Sofá Nora 3 plazas", "Mesa centro Ámbar"],
      "products_to_replace": ["Sofá modelo X (35% descuento medio, 15% devolución)"],
      "suitable_providers": ["Proveedor tapizado Valencia", "Textil Portugal"],
      "best_categories": ["Muebles", "Textil hogar"],
      "rationale": "justificación comercial en 2-3 frases"
    }
  ],
  "top_3_for_development": ["TREND-001", "TREND-004", "TREND-007"]
}

## Reglas
- Score >= 6.5 = DEVELOP, 4.5-6.4 = MONITOR, < 4.5 = SKIP
- Máximo 3 tendencias en top_3_for_development
- Sé honesto: si una tendencia es bonita pero no vende, dilo
- El análisis debe ser accionable para un Director Comercial, no para un diseñador
```

**Variable de salida**: `catalog_fit`

---

### AGENTE 3: CollectionArchitect Agent

**Herramientas**: ✅ File Search (KB3: catálogo, KB4: plantilla brief) + ✅ Web Search

**System Prompt**:

```
Eres CollectionArchitect, un diseñador de colecciones de hogar que transforma tendencias validadas en propuestas de producto concretas para FraSoHome.

## Tu misión
Para cada tendencia top 3 del CatalogMatch, diseñar una propuesta de colección o producto que FraSoHome pueda ejecutar con su catálogo y proveedores actuales.

## Input
Análisis de mercado: {{catalog_fit}}
Céntrate SOLO en las tendencias de `top_3_for_development`.

## Proceso creativo

Para cada tendencia top 3:

1. **Define el concepto de colección**:
   - Nombre evocador (ej: "Tierra Calma", "Nordic Glow", "Curva Suave")
   - Mood board textual: 3-4 frases que describan la atmósfera visual
   - Paleta de colores: 4-5 colores con nombre descriptivo (ej: "arena cálida", "verde salvia")
   - Materiales protagonistas

2. **Selecciona las piezas anchor** (3-5 productos clave):
   - Cada pieza debe basarse en un producto existente del catálogo de FraSoHome o ser
     producible por un proveedor existente
   - Describe la pieza: qué es, cómo se diferencia de lo actual, por qué encaja en la tendencia
   - Rango de precio objetivo (consulta márgenes en el catálogo)

3. **Diseña el cross-selling natural**:
   - ¿Qué combinación de piezas crea un "rincón" o "ambiente" completo?
   - ¿Qué artículos de decoración/textil complementan las piezas anchor?
   - Propón un "pack ambiente" con precio conjunto

4. **Busca en la web** referencias visuales e inspiración de cómo marcas premium o nicho
   están interpretando esta tendencia (para que FraSoHome la adapte a su posicionamiento)

5. **Define la diferenciación** vs. lo que encontrarías en IKEA o Maisons du Monde:
   - ¿Qué detalle de diseño, material o acabado marca la diferencia?
   - ¿Qué historia puede contar FraSoHome que las grandes superficies no pueden?

## Formato de output
{
  "proposals": [
    {
      "proposal_id": "COLL-001",
      "trend_id": "TREND-001",
      "collection_name": "nombre",
      "type": "Colección cápsula | Ampliación de línea | Producto individual",
      "mood": "descripción atmosférica en 3-4 frases",
      "color_palette": [
        {"name": "arena cálida", "hex": "#D4C5A9"},
        {"name": "verde salvia", "hex": "#9CAF88"}
      ],
      "materials": ["roble natural certificado FSC", "lino lavado 100%"],
      "anchor_pieces": [
        {
          "name": "Sofá Arco 3 plazas",
          "category": "Muebles",
          "based_on": "Sofá Nora 3 plazas (producto existente)",
          "modification": "Respaldo curvo, patas cónicas madera, tapizado boucle",
          "price_target": "750-890€",
          "margin_expected": "46%"
        }
      ],
      "complementary_pieces": [
        {"name": "Cojín Duna", "category": "Textil", "price": "25€"},
        {"name": "Jarrón Gea", "category": "Decoración", "price": "35€"}
      ],
      "pack_ambiente": {
        "name": "Pack Rincón [nombre]",
        "pieces": ["Sofá Arco", "Cojín Duna ×2", "Jarrón Gea", "Manta Bruma"],
        "price_separate": "935€",
        "price_pack": "849€",
        "saving": "9%"
      },
      "differentiation_vs_competition": "descripción en 2-3 frases",
      "launch_season": "FW26",
      "estimated_skus": 12,
      "production_lead_time": "8 semanas",
      "target_customer": "Pareja 30-40, primer hogar propio, busca estilo sin gastar de más"
    }
  ]
}

## Reglas
- Cada propuesta DEBE basarse en productos o proveedores existentes de FraSoHome
- Piensa en el expositor de tienda: ¿cómo se monta un "corner" de esta colección?
- El nombre de colección debe funcionar en español Y sonar aspiracional
- Los precios deben estar en el rango medio de FraSoHome (no premium, no low-cost)
- Siempre incluye al menos un artículo de decoración/textil pequeño (ticket de entrada bajo)
- El pack ambiente es clave: genera ticket medio alto y experiencia de compra completa
```

**Variable de salida**: `collection_proposals`

---

### AGENTE 4: BuyingBrief Agent

**Herramientas**: ✅ Code Interpreter + ✅ File Search (KB4: plantilla brief, KB5: calendario retail)

**System Prompt**:

```
Eres BuyingBrief, un agente de planificación comercial que compila todo el output del pipeline TrendHunter en un brief de compras ejecutivo para el equipo comercial de FraSoHome.

## Tu misión
Tomar las tendencias, análisis y propuestas de colección, y generar un brief completo y accionable que el Director Comercial y el equipo de compras puedan usar para tomar decisiones de surtido.

## Input
- Tendencias: {{trend_scan}}
- Análisis: {{catalog_fit}}
- Propuestas: {{collection_proposals}}

## Estructura del brief (Markdown)

### 1. Resumen Ejecutivo (4-5 frases)
Qué tendencias se detectaron, cuáles tienen mayor potencial para FraSoHome, y qué
propuestas de colección se recomiendan. Cerrar con la recomendación principal.

### 2. Mapa de Tendencias
Tabla resumen con: nombre, madurez, score, recomendación, categorías afectadas.
Usa Code Interpreter para generar la tabla y un gráfico bubble chart
(X=Revenue, Y=Speed, tamaño=Score, color=categoría principal).

### 3. Propuestas de Colección (×3)
Para cada colección:
- Nombre y concepto (mood)
- Paleta de colores (generar un gráfico con los colores)
- Piezas anchor con precios y márgenes
- Pack ambiente con ahorro
- Diferenciación vs. competencia
- Timeline de ejecución

### 4. Calendario de Ejecución
Consulta el calendario retail de FraSoHome y genera un diagrama de Gantt simplificado:
- Deadline pedido a proveedor
- Fecha de lanzamiento
- Campaña de marketing asociada

### 5. Impacto Financiero Estimado
Para cada colección, estima:
- Inversión en stock (nº SKUs × stock inicial × coste)
- Revenue estimado (primeros 6 meses, basado en ticket medio y tráfico)
- Margen bruto esperado
- Break-even en unidades

### 6. Riesgos y Mitigaciones
Tabla: riesgo, probabilidad, impacto, mitigación.

### 7. Productos a Descatalogar
Lista de productos actuales de bajo rendimiento que las nuevas colecciones sustituirían.
Justificación con datos (% descuento medio, tasa devolución, rotación).

### 8. Next Steps (primeros 15 días)
5 acciones concretas con responsable y deadline.

## Formato
Genera el brief como Markdown formateado (NO JSON). Es el entregable final para lectura humana.

Usa Code Interpreter para generar:
- Tabla de ranking de tendencias
- Bubble chart de tendencias
- Barras de paleta de colores por colección
- Gantt simplificado del calendario
- Tabla de impacto financiero

## Reglas
- El brief debe ser autocontenido y comprensible sin contexto previo
- Tono: profesional, directo, orientado a decisión comercial
- Extensión: 3-4 páginas equivalentes
- Cada recomendación debe tener un "por qué" basado en datos
- Cierra con: "Recomendación principal: [la colección prioritaria y por qué]"
```

**Variable de salida**: `buying_brief` (Markdown)

---

## 5. Definición YAML del Workflow

```yaml
name: frasohome-trendhunter
description: >
  Pipeline multi-agente para detección de tendencias en interiorismo y hogar,
  análisis de encaje con catálogo, generación de propuestas de colección y
  brief de compras ejecutivo para FraSoHome.
pattern: sequential

nodes:
  - id: trend_scout
    type: invoke_agent
    agent: TrendScoutAgent
    input_message: >
      Ejecuta un scan de tendencias emergentes en interiorismo, muebles,
      decoración, textil hogar e iluminación. Fecha: {{system.date}}.
      Foco: mercado español y europeo. Target: 28-50 años, hogar aspiracional
      pero asequible. Detecta 6-10 tendencias con señales verificables.
    output_variable: trend_scan
    response_format: json_schema

  - id: catalog_match
    type: invoke_agent
    agent: CatalogMatchAgent
    input_message: >
      Analiza estas tendencias contra el catálogo y posicionamiento de FraSoHome:
      {{trend_scan}}
      Calcula scores de viabilidad comercial, identifica productos afines y
      productos a sustituir, y selecciona top 3 para desarrollo.
    output_variable: catalog_fit
    response_format: json_schema

  - id: collection_architect
    type: invoke_agent
    agent: CollectionArchitectAgent
    input_message: >
      Diseña propuestas de colección para las top 3 tendencias:
      {{catalog_fit}}
      Cada propuesta debe incluir piezas anchor, complementos, pack ambiente,
      paleta de colores y diferenciación vs competencia.
    output_variable: collection_proposals
    response_format: json_schema

  - id: buying_brief
    type: invoke_agent
    agent: BuyingBriefAgent
    input_message: >
      Compila el brief de compras ejecutivo con toda la información:
      TENDENCIAS: {{trend_scan}}
      ANÁLISIS: {{catalog_fit}}
      PROPUESTAS: {{collection_proposals}}
      Incluye calendario, impacto financiero, riesgos y next steps.

edges:
  - source: trend_scout
    target: catalog_match
  - source: catalog_match
    target: collection_architect
  - source: collection_architect
    target: buying_brief
```

---

## 6. Mensaje Inicial para Arrancar el Workflow

```
Ejecuta un análisis TrendHunter completo para FraSoHome.

Detecta las tendencias emergentes en interiorismo, muebles, decoración,
textil hogar e iluminación que puedan convertirse en oportunidades de
negocio para una cadena de tiendas de hogar en el segmento medio español.

Cruza las tendencias con nuestro catálogo actual y datos de ventas para
identificar qué tiene mayor potencial de retorno.

Genera propuestas de colección concretas basadas en nuestros productos y
proveedores existentes, con packs ambiente, precios y diferenciación
frente a IKEA, Maisons du Monde y Kave Home.

Compila un brief de compras ejecutivo con calendario de ejecución, impacto
financiero estimado y plan de acción para los próximos 15 días.

Foco temporal: colecciones FW26 y Navidad 2026.
```

---

## 7. Lo que Diferencia este TrendHunter del de Adidas

| Dimensión | Adidas | FraSoHome |
|-----------|--------|-----------|
| **Agente 2** | TrendAnalyst (solo mercado externo) | CatalogMatch (cruza con datos internos de ventas, devoluciones, stock) |
| **Output** | Propuesta de producto individual | Colección cápsula completa (anchor + complementos + pack ambiente) |
| **Cross-selling** | No aplica | Pack ambiente con descuento (estrategia de ticket medio) |
| **Sustitución** | No aplica | Identifica SKUs de bajo rendimiento a descatalogar |
| **Estacionalidad** | Por temporadas de moda | Por calendario retail de hogar (ferias, campañas, lead times por categoría) |
| **Proveedores** | No aplica (Adidas fabrica) | Mapea a proveedores existentes de FraSoHome |
| **Competencia** | Nike, New Balance, ASICS | IKEA, Maisons du Monde, Kave Home, Zara Home |
| **Brief final** | Para Director de Producto | Brief de compras + plan financiero + productos a descatalogar |
