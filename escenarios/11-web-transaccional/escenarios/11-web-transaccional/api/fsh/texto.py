"""FraSoHome Live · clasificación sencilla de textos de clientes (sentimiento y tema).

Reglas de palabras clave, deterministas y fáciles de explicar. Sirven para etiquetar
reseñas y casos nuevos igual que vienen etiquetados los datos de origen; la clase puede
compararlas después con un modelo de lenguaje.
"""
from __future__ import annotations

import unicodedata


def _fold(text: str) -> str:
    s = unicodedata.normalize("NFKD", (text or "").lower())
    return "".join(c for c in s if not unicodedata.combining(c))


POSITIVE = ["genial", "encant", "perfect", "excelente", "muy bien", "buen", "sorprend", "recomiend", "rapido", "comodo",
            "bonit", "calidad correcta", "feliz", "gracias", "solucion"]
NEGATIVE = ["mal", "roto", "rota", "defect", "tarde", "retraso", "problema", "no funciona", "decepcion", "peor", "nunca",
            "falta", "faltan", "danad", "queja", "enfad", "mancha", "devolver", "no transmite", "mejorable", "lento", "caro"]
TOPICS = {
    "entrega_servicio": ["entrega", "envio", "transport", "llego", "repartidor", "retraso", "seguimiento", "paquete"],
    "precio_promocion": ["precio", "oferta", "descuento", "cupon", "promocion", "caro", "barato", "rebaja"],
    "medidas_ajuste": ["medida", "tamano", "encaja", "dimension", "grande", "pequen", "ajuste", "espacio"],
    "tienda_experiencia": ["tienda", "dependient", "atencion en", "probador", "caja", "visita"],
    "calidad_producto": ["calidad", "material", "acabado", "roto", "defect", "resistente", "tela", "madera"],
}


def sentiment(text: str) -> str:
    t = _fold(text)
    pos = sum(t.count(w) for w in POSITIVE)
    neg = sum(t.count(w) for w in NEGATIVE)
    if neg > pos:
        return "Negativo"
    if pos > neg:
        return "Positivo"
    return "Neutral"


def topic(text: str, default: str = "calidad_producto") -> str:
    t = _fold(text)
    scores = {name: sum(t.count(w) for w in words) for name, words in TOPICS.items()}
    best = max(scores, key=lambda k: scores[k])
    return best if scores[best] > 0 else default
