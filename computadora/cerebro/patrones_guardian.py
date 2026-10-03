"""
RF-226 (FP-077): Patrones regex del Shomer HaBáyit — extraídos de nlu.py.
Centraliza las regex de guardián (RF-210→RF-219/221) para equilibrar Tiféret.
"""

import re

# RF-210: Activar modo guardián explícitamente
RE_GUARDIAN_ON = re.compile(
    r"(?:ponte\s+en\s+modo\s+guardi[aá]n|vigila\s+(?:la\s+)?casa|activa\s+(?:el\s+)?guardi[aá]n|"
    r"modo\s+seguridad|cuida\s+(?:la\s+)?casa|pon\s+(?:el\s+)?modo\s+guardi[aá]n|"
    r"activa\s+(?:el\s+)?modo\s+(?:guardi[aá]n|seguridad|vigil[aá]ncia)|"
    r"empieza\s+a\s+vigilar|entra\s+en\s+modo\s+guardi[aá]n|"
    r"(?:entra|pasa|cambia|p[oó]n(?:te)?)\s+(?:a|en)\s+(?:modo\s+)?guardi[aá]n)",
    re.IGNORECASE,
)

# RF-211: Desactivar guardián
RE_GUARDIAN_OFF = re.compile(
    r"(?:desactiva\s+(?:el\s+)?guardi[aá]n|ya\s+no\s+vigiles|modo\s+normal|"
    r"deja\s+de\s+vigilar|quita\s+(?:el\s+)?modo\s+guardi[aá]n|"
    r"desactiva\s+(?:el\s+)?modo\s+(?:guardi[aá]n|seguridad)|ya\s+estoy\s+(?:aqu[ií]|en\s+casa))",
    re.IGNORECASE,
)

# RF-213/214: "ya me voy a dormir" + variante con "vigila"
RE_DORMIR = re.compile(
    r"(?:ya\s+me\s+voy\s+a\s+dormir|me\s+voy\s+a\s+(?:descansar|acostar)|buenas\s+noches.*duerme|"
    r"me\s+voy\s+a\s+la\s+cama|hora\s+de\s+dormir)",
    re.IGNORECASE,
)
RE_DORMIR_VIGILA = re.compile(
    r"(?:ya\s+me\s+voy\s+a\s+dormir.*vigila|duerme.*vigila|vigila.*dormir|"
    r"me\s+acuesto.*vigila|duerm(?:o|e).*cuida)",
    re.IGNORECASE,
)

# RF-215: "mejor duérmete" → Tzimtzum con mic activo
RE_DUERMETE = re.compile(
    r"(?:mejor\s+du[eé]rmete|du[eé]rmete\s+(?:t[uú])?|ponte\s+a\s+dormir|"
    r"descansa\s+(?:t[uú])?|du[eé]rmete\s+ya)",
    re.IGNORECASE,
)

# RF-217: "buenos días" post-vigía → reporte matutino
RE_BUENOS_DIAS = re.compile(
    r"(?:buenos?\s+d[ií]as?|ya\s+(?:despert[eé]|me\s+levant[eé]|estoy\s+despierto)|buen\s+d[ií]a)",
    re.IGNORECASE,
)

# RF-219: Smart restart
RE_REINICIAR_COMPUTADORA = re.compile(
    r"(?:rein[ií]ciate|reinicia\s+(?:el\s+)?(?:sistema|computadora|te)|"
    r"restart|rein[ií]ciate\s+(?:por\s+favor)?|haz\s+un\s+reinicio)",
    re.IGNORECASE,
)


