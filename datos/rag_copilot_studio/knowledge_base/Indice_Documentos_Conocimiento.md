# FraSoHome — Índice y clasificación de documentos de conocimiento (Knowledge)

Este documento clasifica los archivos de la carpeta `Documentos_Knowledge`
y sugiere cómo usarlos en los laboratorios y en un escenario de producción.

---

## 📅 Última actualización

2026-02-26

---

## 🎯 Uso

Referencia rápida para:

- Seleccionar fuentes de conocimiento (RAG)
- Evitar mezclar versiones
- No subir documentos de prueba en producción

---

# 1️⃣ Clasificación por dominio

---

## 01_Politicas

- **FS-KB-01_Politica_Devoluciones_v1.3_Vigente.docx**  
  Estado: **VIGENTE**  
  Política oficial de devoluciones (plazos, excepciones, reembolsos).  
  ✔ Usar en respuestas a empleados / atención.

- **FS-KB-02_Politica_Devoluciones_v1.2_Obsoleta.docx**  
  Estado: **OBSOLETA** (solo formación).  
  Versión anterior para practicar control de versiones.  
  ❌ No usar en producción.

---

## 02_KPI_y_Datos

- **FS-KB-03_Diccionario_KPI_Reglas_Calculo_v1.0.docx**  
  Estado: **VIGENTE**  
  Definiciones y fórmulas KPI:
  - Ventas netas
  - Stock disponible
  - Tasa de devolución
  - Etc.

---

## 03_Operaciones

- **FS-KB-04_Manual_Tienda_Caja_y_Pagos_Mixtos_v2.1.docx**  
  Estado: **VIGENTE**  
  Procedimientos de tienda:
  - Cierre de caja
  - Pagos mixtos
  - Incidencias

- **FS-KB-05_Guia_Conciliacion_Pagos_Ecommerce_v1.4.docx**  
  Estado: **VIGENTE**  
  Conciliación e-commerce:
  - Cobros
  - Reembolsos
  - Cupones

- **FS-KB-09_FAQ_Operaciones_y_Atencion_v1.0.docx**  
  Estado: **VIGENTE**  
  FAQ operacional:
  - Respuestas rápidas
  - Pautas

---

## 04_Catalogo

- **FS-KB-06_Taxonomia_Catalogo_y_Reglas_SKU_v1.2.docx**  
  Estado: **VIGENTE**  
  Reglas de SKU, categorías y naming para catálogo.

---

## 05_CRM

- **FS-KB-07_Guia_Fidelizacion_CRM_v1.1.docx**  
  Estado: **VIGENTE**  
  Programa de fidelización:
  - Tiers
  - Beneficios
  - Condiciones

---

## 06_Gobierno_y_Seguridad

- **FS-KB-08_Politica_Datos_y_Permisos_Asistente_v1.0.docx**  
  Estado: **VIGENTE**  
  Política de datos:
  - Qué puede / no puede responder
  - PII
  - Permisos

---

## 07_Test_Security

- **FS-KB-10_Documento_Prueba_Prompt_Injection_NO_PROD.docx**  
  Estado: **NO_PROD** (solo pruebas).  
  Texto simulado de prompt injection para red teaming.  
  ⚠ Debe retirarse tras el LAB 3.

---

# 2️⃣ Recomendación de carga por laboratorio

---

## LAB 2 (Base RAG)

Subir SOLO documentos **VIGENTES**:

- FS-KB-01
- FS-KB-03
- FS-KB-04
- FS-KB-05
- FS-KB-06
- FS-KB-07
- FS-KB-08
- FS-KB-09

Al final, subir **FS-KB-02** para provocar conflicto controlado.

---

## LAB 3 (Prompting y seguridad)

- Subir temporalmente **FS-KB-10** para pruebas de inyección.
- Luego retirarlo.
- Mantener FS-KB-02 para probar regla de versionado.

---

## LAB 4 (Dataverse)

Sin cambios en documentos.  
Se preparan tablas y CSV.

---

## LAB 5 (Híbrido)

- Asegurar FS-KB-03 para definiciones KPI.
- Mantener FS-KB-08 por reglas de permisos al usar datos.

---

## LAB 6 (Evaluación y gobierno)

Preparar "modo producción":

- Retirar FS-KB-02
- Retirar FS-KB-10
- Dejar solo documentos **VIGENTES**

---

# 3️⃣ Regla práctica de versionado

Mantener patrón en nombres de archivo: FS-KB-XX_<Tema>vX.Y<Estado>.docx 

Estados recomendados:

- Vigente
- Obsoleta
- NO_PROD

---

## 📌 Regla operativa

- Cuando se publique una nueva versión:
  - Subir la nueva
  - Retirar la anterior (o moverla a repositorio histórico fuera de Knowledge)

- Si por formación conviven versiones:
  - El agente debe incluir una regla de priorización:
    - Documento **Vigente**
    - Versión mayor
