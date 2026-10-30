import re

from practilizate.text import normalize_key

SKILL_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "SQL": ("sql",),
    "Power BI": ("power bi", "powerbi"),
    "Excel": ("excel", "hojas de calculo"),
    "SEO": ("seo", "posicionamiento web"),
    "Redes sociales": ("redes sociales", "social media"),
    "Redacción de contenidos": ("redaccion de contenidos", "copywriting"),
    "Soporte técnico": ("soporte tecnico", "soporte de ti"),
    "Windows": ("windows",),
    "Redes": ("redes", "networking"),
    "PLC": ("plc",),
    "Comunicación": ("comunicacion",),
    "Linux": ("linux",),
    "Seguridad informática": ("seguridad informatica", "ciberseguridad"),
    "SAP": ("sap",),
    "AutoCAD": ("autocad",),
    "Revit": ("revit",),
    "Contabilidad": ("contabilidad",),
    "Análisis financiero": ("analisis financiero",),
    "Estadística": ("estadistica",),
    "Automatización": ("automatizacion industrial", "automatizacion"),
    "Java": ("java",),
    "JavaScript": ("javascript",),
    "Git": ("git",),
    "Tableau": ("tableau",),
    "Machine Learning": ("machine learning",),
    "Power Query": ("power query",),
}


def _alias_pairs() -> list[tuple[str, str]]:
    pairs = [(alias, skill) for skill, aliases in SKILL_ALIASES.items() for alias in aliases]
    return sorted(pairs, key=lambda pair: len(pair[0]), reverse=True)


_ALIAS_PAIRS = _alias_pairs()


def extract_skills(text: str) -> list[str]:
    normalized = f" {normalize_key(text)} "
    consumed: list[tuple[int, int]] = []
    found: set[str] = set()
    for alias, skill in _ALIAS_PAIRS:
        pattern = re.compile(rf"(?<![\w]){re.escape(alias)}(?![\w])")
        for match in pattern.finditer(normalized):
            if any(start < match.end() and match.start() < end for start, end in consumed):
                continue
            consumed.append((match.start(), match.end()))
            found.add(skill)
    return sorted(found)
