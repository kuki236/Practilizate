"""Generate the Practilizate PBIR report from deterministic JSON builders."""

import hashlib
import json
import shutil
import sys
from pathlib import Path

REPORT_DIR = Path("powerbi/practilizate.Report")
PAGES_DIR = REPORT_DIR / "definition" / "pages"
THEMES_DIR = REPORT_DIR / "StaticResources" / "RegisteredResources"

SCHEMA_PAGE = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json"
SCHEMA_VISUAL = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/"
    "visualContainer/2.9.0/schema.json"
)
SCHEMA_REPORT = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.3.0/schema.json"

NAVY = "#1F4E79"
BLUE = "#2E75B6"
LIGHT_BLUE = "#EAF2FB"
GREEN = "#548235"
AMBER = "#BF8F00"
RED = "#C00000"
GREY = "#6B7280"
INK = "#1F2937"
PAGE_BG = "#F5F7FA"
WHITE = "#FFFFFF"
BORDER = "#E5E7EB"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:20]


def lit(value: str) -> dict:
    return {"expr": {"Literal": {"Value": value}}}


def text(value: str) -> dict:
    return lit("'" + value.replace("'", "''") + "'")


def number(value: int | float, unit: str = "D") -> dict:
    return lit(f"{value}{unit}")


def fill(color: str) -> dict:
    return {"solid": {"color": lit("'" + color + "'")}}


def field_ref(table: str, column: str, *, role: str = "Column") -> dict:
    return {
        "field": {role: {"Expression": {"SourceRef": {"Entity": table}}, "Property": column}},
        "queryRef": f"{table}.{column}",
        "nativeQueryRef": column,
    }


def column(table: str, name: str, *, active: bool = False) -> dict:
    projection = field_ref(table, name)
    if active:
        projection["active"] = True
    return projection


def measure(table: str, name: str) -> dict:
    return field_ref(table, name, role="Measure")


def aggregation(table: str, name: str, function: int = 0) -> dict:
    return {
        "field": {
            "Aggregation": {
                "Expression": {
                    "Column": {
                        "Expression": {"SourceRef": {"Entity": table}},
                        "Property": name,
                    }
                },
                "Function": function,
            }
        },
        "queryRef": f"Sum({table}.{name})" if function == 0 else f"Agg({table}.{name})",
        "nativeQueryRef": name,
    }


def query(*projections: tuple[str, dict | list[dict]], sort: dict | None = None) -> dict:
    state = {}
    for role, projection in projections:
        items = projection if isinstance(projection, list) else [projection]
        state[role] = {"projections": items}
    payload: dict = {"queryState": state}
    if sort:
        payload["sortDefinition"] = {"sort": [sort]}
    return payload


def sort_by_field(table: str, name: str, direction: str, *, role: str = "Column") -> dict:
    return {"field": field_ref(table, name, role=role)["field"], "direction": direction}


def vco(
    *,
    title: str | None = None,
    background: str = WHITE,
    border: bool = True,
    padding: int = 8,
    show_title: bool = True,
    alt_text: str | None = None,
) -> dict:
    result: dict = {
        "general": [
            {
                "properties": {
                    "altText": text(alt_text or title or "Visual informativo"),
                }
            }
        ],
        "background": [
            {
                "properties": {
                    "show": lit("true"),
                    "color": fill(background),
                    "transparency": lit("0D"),
                }
            }
        ],
        "border": [
            {
                "properties": {
                    "show": lit("true" if border else "false"),
                    "color": fill(BORDER),
                    "radius": lit("8D"),
                    "width": lit("1D"),
                }
            }
        ],
        "padding": [
            {
                "properties": {
                    "top": lit(f"{padding}D"),
                    "bottom": lit(f"{padding}D"),
                    "left": lit(f"{padding}D"),
                    "right": lit(f"{padding}D"),
                }
            }
        ],
    }
    result["subTitle"] = [{"properties": {"show": lit("false")}}]
    if title and show_title:
        result["title"] = [
            {
                "properties": {
                    "show": lit("true"),
                    "text": text(title),
                    "fontSize": number(11),
                    "fontFamily": text("Segoe UI Semibold"),
                    "fontColor": fill(INK),
                    "alignment": text("left"),
                }
            }
        ]
    else:
        result["title"] = [{"properties": {"show": lit("false")}}]
    return result


def position(x: int, y: int, width: int, height: int, order: int) -> dict:
    return {
        "x": x,
        "y": y,
        "z": 1000 + order,
        "height": height,
        "width": width,
        "tabOrder": 1000 + order,
    }


def card(
    visual_id: str,
    x: int,
    y: int,
    width: int,
    height: int,
    table: str,
    metric: str,
    title: str,
    *,
    order: int,
    color: str = NAVY,
    background: str = WHITE,
    message: bool = False,
    font_size: int | None = None,
    align: str | None = None,
) -> dict:
    value_style = {
        "fontSize": number(font_size or (12 if message else 20)),
        "bold": lit("true"),
        "fontColor": fill(color),
        "horizontalAlignment": text(align or ("left" if message else "center")),
        "textWrap": lit("true" if message else "false"),
    }
    return {
        "$schema": SCHEMA_VISUAL,
        "name": visual_id,
        "position": position(x, y, width, height, order),
        "visual": {
            "visualType": "cardVisual",
            "query": query(("Data", measure(table, metric))),
            "objects": {
                "value": [{"properties": value_style, "selector": {"id": "default"}}],
                "label": [
                    {
                        "properties": {
                            "show": lit("false"),
                            "transparency": number(100),
                        },
                        "selector": {"id": "default"},
                    }
                ],
                "divider": [{"properties": {"show": lit("false")}}],
                "layout": [
                    {
                        "properties": {"paddingUniform": number(0)},
                        "selector": {"id": "default"},
                    }
                ],
                "padding": [
                    {
                        "properties": {"paddingUniform": number(10 if not message else 12)},
                        "selector": {"id": "default"},
                    }
                ],
            },
            "visualContainerObjects": vco(
                title=title if not message else None,
                background=LIGHT_BLUE if message else background,
                border=not message,
                padding=8 if not message else 10,
                alt_text=title or "Mensaje ejecutivo",
            ),
        },
    }


def textbox(
    visual_id: str,
    x: int,
    y: int,
    width: int,
    height: int,
    paragraphs: list[dict],
    *,
    order: int,
    background: str = WHITE,
    border: bool = False,
    padding: int = 12,
    alt_text: str | None = None,
) -> dict:
    return {
        "$schema": SCHEMA_VISUAL,
        "name": visual_id,
        "position": position(x, y, width, height, order),
        "visual": {
            "visualType": "textbox",
            "objects": {
                "general": [{"properties": {"paragraphs": paragraphs}}],
            },
            "visualContainerObjects": vco(
                background=background,
                border=border,
                padding=padding,
                show_title=False,
                alt_text=alt_text or "Texto informativo",
            ),
        },
    }


def text_run(value: str, *, size: int = 12, color: str = INK, bold: bool = False) -> dict:
    return {
        "value": value,
        "textStyle": {
            "fontFamily": "Segoe UI Semibold" if bold else "Segoe UI",
            "fontSize": f"{size}px",
            "color": color,
        },
    }


def paragraph(*runs: dict, align: str = "left") -> dict:
    return {"textRuns": list(runs), "horizontalTextAlignment": align}


def header(visual_id: str, title: str, subtitle: str) -> dict:
    return textbox(
        visual_id,
        0,
        0,
        1280,
        72,
        [
            paragraph(text_run(title, size=22, color=WHITE, bold=True)),
            paragraph(text_run(subtitle, size=10, color="#D6E4F0")),
        ],
        order=0,
        background=NAVY,
        border=False,
        padding=10,
    )


def footer(visual_id: str) -> dict:
    return textbox(
        visual_id,
        24,
        684,
        940,
        28,
        [
            paragraph(
                text_run(
                    "Fuente: practicas.pe · Practilizate no está afiliado · Datos agregados del snapshot",
                    size=8,
                    color=GREY,
                )
            )
        ],
        order=0,
        background=WHITE,
        border=False,
        padding=0,
    )


def clear_button(visual_id: str) -> dict:
    return {
        "$schema": SCHEMA_VISUAL,
        "name": visual_id,
        "position": position(1088, 16, 168, 40, 90),
        "visual": {
            "visualType": "actionButton",
            "objects": {
                "text": [
                    {"properties": {"show": lit("true")}},
                    {
                        "properties": {
                            "text": text("Limpiar filtros"),
                            "fontSize": number(9),
                            "bold": lit("true"),
                            "fontColor": fill(NAVY),
                            "horizontalAlignment": text("center"),
                        },
                        "selector": {"id": "default"},
                    },
                    {
                        "properties": {"fontColor": fill(RED)},
                        "selector": {"id": "hover"},
                    },
                ],
                "fill": [
                    {"properties": {"show": lit("true")}},
                    {
                        "properties": {"fillColor": fill(WHITE)},
                        "selector": {"id": "default"},
                    },
                    {
                        "properties": {"fillColor": fill(LIGHT_BLUE)},
                        "selector": {"id": "hover"},
                    },
                ],
                "outline": [{"properties": {"show": lit("false")}}],
                "shape": [
                    {
                        "properties": {
                            "tileShape": text("rectangleRounded"),
                            "roundEdge": lit("6L"),
                        }
                    },
                    {
                        "properties": {"tileShape": text("rectangleRounded")},
                        "selector": {"id": "default"},
                    },
                ],
            },
            "visualContainerObjects": {
                "general": [
                    {"properties": {"altText": text("Limpiar todos los filtros de la página")}}
                ],
                "background": [{"properties": {"show": lit("false")}}],
                "border": [{"properties": {"show": lit("false")}}],
                "visualLink": [
                    {
                        "properties": {
                            "show": lit("true"),
                            "type": text("ClearAllSlicers"),
                            "tooltip": text("Limpiar todas las segmentaciones de esta página"),
                        }
                    }
                ],
            },
        },
        "howCreated": "InsertVisualButton",
    }


def language_slicer(visual_id: str) -> dict:
    return {
        "$schema": SCHEMA_VISUAL,
        "name": visual_id,
        "position": position(1088, 84, 168, 80, 91),
        "visual": {
            "visualType": "slicer",
            "query": query(("Values", column("Idioma", "Idioma"))),
            "objects": {
                "data": [{"properties": {"mode": text("Dropdown")}}],
                "header": [
                    {
                        "properties": {
                            "show": lit("true"),
                            "text": text("Idioma / Language"),
                            "textSize": number(9),
                            "fontColor": fill(GREY),
                        }
                    }
                ],
            },
            "visualContainerObjects": vco(padding=8, alt_text="Selector de idioma"),
        },
    }


def topn_filter(table: str, column_name: str, top: int = 10, alias: str = "c") -> dict:
    token = hashlib.sha256(f"topn:{table}.{column_name}".encode()).hexdigest()[:24]
    return {
        "name": "Filter" + token,
        "field": {
            "Column": {
                "Expression": {"SourceRef": {"Entity": table}},
                "Property": column_name,
            }
        },
        "type": "TopN",
        "filter": {
            "Version": 2,
            "From": [
                {
                    "Name": "subquery",
                    "Expression": {
                        "Subquery": {
                            "Query": {
                                "Version": 2,
                                "From": [{"Name": alias, "Entity": table, "Type": 0}],
                                "Select": [
                                    {
                                        "Column": {
                                            "Expression": {"SourceRef": {"Source": alias}},
                                            "Property": column_name,
                                        },
                                        "Name": "field",
                                    }
                                ],
                                "OrderBy": [
                                    {
                                        "Direction": 2,
                                        "Expression": {
                                            "Aggregation": {
                                                "Expression": {
                                                    "Column": {
                                                        "Expression": {
                                                            "SourceRef": {"Source": alias}
                                                        },
                                                        "Property": "offer_id",
                                                    }
                                                },
                                                "Function": 2,
                                            }
                                        },
                                    },
                                    {
                                        "Direction": 1,
                                        "Expression": {
                                            "Column": {
                                                "Expression": {"SourceRef": {"Source": alias}},
                                                "Property": column_name,
                                            }
                                        },
                                    },
                                ],
                                "Top": top,
                            }
                        }
                    },
                    "Type": 2,
                },
                {"Name": "outer", "Entity": table, "Type": 0},
            ],
            "Where": [
                {
                    "Condition": {
                        "In": {
                            "Expressions": [
                                {
                                    "Column": {
                                        "Expression": {"SourceRef": {"Source": "outer"}},
                                        "Property": column_name,
                                    }
                                }
                            ],
                            "Table": {"SourceRef": {"Source": "subquery"}},
                        }
                    }
                }
            ],
        },
        "howCreated": "User",
    }


def bar_chart(
    visual_id: str,
    x: int,
    y: int,
    width: int,
    height: int,
    title: str,
    table: str,
    category: str,
    value_table: str,
    value_name: str,
    *,
    order: int,
    color: str = BLUE,
    sort_desc: bool = True,
    category_size: int = 9,
    horizontal: bool = True,
    top_n_table: str | None = None,
    top_n_column: str | None = None,
    top_n: int = 10,
) -> dict:
    visual_type = "barChart" if horizontal else "columnChart"
    visual_payload = {
        "$schema": SCHEMA_VISUAL,
        "name": visual_id,
        "position": position(x, y, width, height, order),
        "visual": {
            "visualType": visual_type,
            "query": query(
                ("Category", column(table, category, active=True)),
                ("Y", measure(value_table, value_name)),
                sort=sort_by_field(
                    value_table,
                    value_name,
                    "Descending" if sort_desc else "Ascending",
                    role="Measure",
                ),
            ),
            "objects": {
                "dataPoint": [{"properties": {"fill": fill(color)}}],
                "labels": [
                    {
                        "properties": {
                            "show": lit("true"),
                            "fontSize": number(8),
                            "color": fill(INK),
                            "labelPrecision": number(0, ""),
                        }
                    }
                ],
                "categoryAxis": [
                    {
                        "properties": {
                            "show": lit("true"),
                            "fontSize": number(category_size),
                            "labelColor": fill(GREY),
                        }
                    }
                ],
                "valueAxis": [
                    {
                        "properties": {
                            "show": lit("true"),
                            "fontSize": number(8),
                            "labelColor": fill(GREY),
                            "gridlineShow": lit("false"),
                        }
                    }
                ],
                "legend": [{"properties": {"show": lit("false")}}],
            },
            "visualContainerObjects": vco(title=title),
        },
    }
    if top_n_table and top_n_column:
        visual_payload["filterConfig"] = {
            "filters": [topn_filter(top_n_table, top_n_column, top_n)]
        }
    return visual_payload


def status_donut(visual_id: str) -> dict:
    return {
        "$schema": SCHEMA_VISUAL,
        "name": visual_id,
        "position": position(654, 288, 602, 388, 12),
        "visual": {
            "visualType": "donutChart",
            "query": query(
                ("Category", column("Estado", "label_es", active=True)),
                ("Y", measure("Ofertas", "Total Ofertas")),
                sort=sort_by_field("Estado", "orden", "Ascending"),
            ),
            "objects": {
                "dataPoint": [
                    {
                        "properties": {"fill": fill(GREEN)},
                        "selector": {
                            "data": [
                                {
                                    "scopeId": {
                                        "Comparison": {
                                            "ComparisonKind": 0,
                                            "Left": {
                                                "Column": {
                                                    "Expression": {
                                                        "SourceRef": {"Entity": "Estado"}
                                                    },
                                                    "Property": "label_es",
                                                }
                                            },
                                            "Right": {"Literal": {"Value": "'Vigente'"}},
                                        }
                                    }
                                }
                            ]
                        },
                    },
                    {
                        "properties": {"fill": fill(AMBER)},
                        "selector": {
                            "data": [
                                {
                                    "scopeId": {
                                        "Comparison": {
                                            "ComparisonKind": 0,
                                            "Left": {
                                                "Column": {
                                                    "Expression": {
                                                        "SourceRef": {"Entity": "Estado"}
                                                    },
                                                    "Property": "label_es",
                                                }
                                            },
                                            "Right": {"Literal": {"Value": "'Por vencer'"}},
                                        }
                                    }
                                }
                            ]
                        },
                    },
                    {
                        "properties": {"fill": fill(RED)},
                        "selector": {
                            "data": [
                                {
                                    "scopeId": {
                                        "Comparison": {
                                            "ComparisonKind": 0,
                                            "Left": {
                                                "Column": {
                                                    "Expression": {
                                                        "SourceRef": {"Entity": "Estado"}
                                                    },
                                                    "Property": "label_es",
                                                }
                                            },
                                            "Right": {"Literal": {"Value": "'Vencida'"}},
                                        }
                                    }
                                }
                            ]
                        },
                    },
                    {
                        "properties": {"fill": fill(GREY)},
                        "selector": {
                            "data": [
                                {
                                    "scopeId": {
                                        "Comparison": {
                                            "ComparisonKind": 0,
                                            "Left": {
                                                "Column": {
                                                    "Expression": {
                                                        "SourceRef": {"Entity": "Estado"}
                                                    },
                                                    "Property": "label_es",
                                                }
                                            },
                                            "Right": {"Literal": {"Value": "'Sin fecha'"}},
                                        }
                                    }
                                }
                            ]
                        },
                    },
                ],
                "labels": [
                    {
                        "properties": {
                            "show": lit("true"),
                            "fontSize": number(9),
                            "color": fill(INK),
                        }
                    }
                ],
                "legend": [
                    {
                        "properties": {
                            "show": lit("true"),
                            "position": text("Right"),
                            "fontSize": number(9),
                            "labelColor": fill(INK),
                        }
                    }
                ],
            },
            "visualContainerObjects": vco(title="Estado de las ofertas"),
        },
    }


def table_visual(
    visual_id: str,
    x: int,
    y: int,
    width: int,
    height: int,
    title: str,
    projections: list[dict],
    *,
    order: int,
    sort: dict | None = None,
    font_size: int = 9,
    filter_config: dict | None = None,
) -> dict:
    payload = {
        "$schema": SCHEMA_VISUAL,
        "name": visual_id,
        "position": position(x, y, width, height, order),
        "visual": {
            "visualType": "tableEx",
            "query": query(("Values", projections), sort=sort),
            "objects": {
                "columnHeaders": [
                    {
                        "properties": {
                            "columnAdjustment": text("growToFit"),
                            "autoSizeColumnWidth": lit("true"),
                            "fontSize": number(font_size),
                            "bold": lit("true"),
                            "fontColor": fill(NAVY),
                        }
                    }
                ],
                "values": [
                    {
                        "properties": {
                            "fontSize": number(font_size),
                            "fontColor": fill(INK),
                        }
                    }
                ],
            },
            "visualContainerObjects": vco(title=title),
        },
    }
    if filter_config is not None:
        payload["filterConfig"] = filter_config
    return payload


def slicer(
    visual_id: str, x: int, y: int, width: int, height: int, table: str, name: str, title: str
) -> dict:
    return {
        "$schema": SCHEMA_VISUAL,
        "name": visual_id,
        "position": position(x, y, width, height, 95),
        "visual": {
            "visualType": "slicer",
            "query": query(("Values", column(table, name))),
            "objects": {
                "data": [{"properties": {"mode": text("Dropdown")}}],
                "header": [
                    {
                        "properties": {
                            "show": lit("true"),
                            "text": text(title),
                            "textSize": number(9),
                            "fontColor": fill(GREY),
                        }
                    }
                ],
            },
            "visualContainerObjects": vco(padding=8, alt_text=title),
        },
    }


def page_payload(page_id: str, display_name: str) -> dict:
    return {
        "$schema": SCHEMA_PAGE,
        "name": page_id,
        "displayName": display_name,
        "displayOption": "FitToPage",
        "height": 720,
        "width": 1280,
        "objects": {
            "background": [
                {
                    "properties": {
                        "color": fill(PAGE_BG),
                        "transparency": lit("0D"),
                    }
                }
            ]
        },
    }


def write_page(display_name: str, visuals: list[dict]) -> str:
    page_id = digest(f"page:{display_name}")
    page_dir = PAGES_DIR / page_id
    if page_dir.exists():
        shutil.rmtree(page_dir)
    page_dir.mkdir(parents=True)
    (page_dir / "page.json").write_text(
        json.dumps(page_payload(page_id, display_name), ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    for visual in visuals:
        visual_dir = page_dir / "visuals" / visual["name"]
        visual_dir.mkdir(parents=True)
        (visual_dir / "visual.json").write_text(
            json.dumps(visual, ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )
    return page_id


def updated_card(page: str) -> dict:
    return card(
        digest(f"{page}:updated"),
        980,
        668,
        276,
        44,
        "Ofertas",
        "Actualizado",
        "",
        order=0,
        color=GREY,
        message=True,
        font_size=9,
        align="right",
        background=WHITE,
    )


def build_executive() -> list[dict]:
    page = "Resumen ejecutivo"
    return [
        header(
            digest(f"{page}:header"),
            "Resumen ejecutivo · Executive summary",
            "Ofertas de prácticas preprofesionales en Lima · Pre-professional internships in Lima",
        ),
        clear_button(digest(f"{page}:clear")),
        language_slicer(digest(f"{page}:language")),
        card(
            digest(f"{page}:message"),
            24,
            84,
            1048,
            56,
            "Ofertas",
            "Mensaje Ejecutivo",
            "",
            order=1,
            message=True,
        ),
        card(
            digest(f"{page}:kpi1"),
            24,
            176,
            196,
            84,
            "Ofertas",
            "Total Ofertas",
            "Ofertas · Offers",
            order=2,
        ),
        card(
            digest(f"{page}:kpi2"),
            228,
            176,
            196,
            84,
            "Ofertas",
            "Empresas",
            "Empresas · Companies",
            order=3,
        ),
        card(
            digest(f"{page}:kpi3"),
            432,
            176,
            196,
            84,
            "Ofertas",
            "Carreras",
            "Carreras · Careers",
            order=4,
        ),
        card(
            digest(f"{page}:kpi4"),
            636,
            176,
            196,
            84,
            "Ofertas",
            "Habilidades",
            "Habilidades · Skills",
            order=5,
        ),
        card(
            digest(f"{page}:kpi5"),
            840,
            176,
            196,
            84,
            "Calidad",
            "Calidad General",
            "Calidad · Quality",
            order=6,
            color=NAVY,
        ),
        card(
            digest(f"{page}:kpi6"),
            1044,
            176,
            196,
            84,
            "Ofertas",
            "Por Vencer",
            "Por vencer · Expiring",
            order=7,
            color=AMBER,
        ),
        bar_chart(
            digest(f"{page}:careers"),
            24,
            272,
            610,
            404,
            "Ofertas por carrera",
            "Carreras",
            "career_name",
            "Ofertas",
            "Total Ofertas",
            order=8,
        ),
        status_donut(digest(f"{page}:status")),
        updated_card(page),
        footer(digest(f"{page}:footer")),
    ]


def build_skills() -> list[dict]:
    page = "Habilidades"
    return [
        header(
            digest(f"{page}:header"),
            "Demanda de habilidades · Skills demand",
            "Qué piden las empresas y cómo cambia por carrera · What employers ask for, by career",
        ),
        clear_button(digest(f"{page}:clear")),
        language_slicer(digest(f"{page}:language")),
        card(
            digest(f"{page}:message"),
            24,
            84,
            1048,
            56,
            "Ofertas",
            "Mensaje Ejecutivo",
            "",
            order=1,
            message=True,
        ),
        bar_chart(
            digest(f"{page}:skills"),
            24,
            176,
            760,
            500,
            "Top habilidades por ofertas",
            "Habilidades",
            "skill",
            "Ofertas",
            "Total Ofertas",
            order=2,
            color=GREEN,
            category_size=8,
        ),
        slicer(
            digest(f"{page}:career"),
            800,
            176,
            456,
            80,
            "Carreras",
            "career_name",
            "Carrera / Career",
        ),
        table_visual(
            digest(f"{page}:coverage"),
            800,
            268,
            456,
            408,
            "Top 10 carreras por cobertura",
            [
                column("Carreras", "career_name"),
                measure("Ofertas", "Habilidades"),
                measure("Ofertas", "Total Ofertas"),
            ],
            order=3,
            sort=sort_by_field("Carreras", "career_name", "Ascending"),
            filter_config={"filters": [topn_filter("Carreras", "career_name", 10)]},
        ),
        updated_card(page),
        footer(digest(f"{page}:footer")),
    ]


def build_companies() -> list[dict]:
    page = "Empresas"
    return [
        header(
            digest(f"{page}:header"),
            "Empresas y subvenciones · Companies and compensation",
            "Concentración de ofertas y rango de subvención · Offer concentration and pay range",
        ),
        clear_button(digest(f"{page}:clear")),
        language_slicer(digest(f"{page}:language")),
        card(
            digest(f"{page}:message"),
            24,
            84,
            1048,
            56,
            "Ofertas",
            "Mensaje Ejecutivo",
            "",
            order=1,
            message=True,
        ),
        card(
            digest(f"{page}:kpi1"),
            24,
            176,
            196,
            84,
            "Ofertas",
            "Total Ofertas",
            "Ofertas · Offers",
            order=2,
        ),
        card(
            digest(f"{page}:kpi2"),
            228,
            176,
            196,
            84,
            "Ofertas",
            "Empresas",
            "Empresas · Companies",
            order=3,
        ),
        card(
            digest(f"{page}:kpi3"),
            432,
            176,
            196,
            84,
            "Ofertas",
            "Subvención Promedio",
            "Subvención · Compensation",
            order=4,
            color=GREEN,
        ),
        card(
            digest(f"{page}:kpi4"),
            636,
            176,
            196,
            84,
            "Calidad",
            "Calidad General",
            "Calidad · Quality",
            order=5,
        ),
        bar_chart(
            digest(f"{page}:companies"),
            24,
            272,
            610,
            404,
            "Empresas con más ofertas",
            "Ofertas",
            "company",
            "Ofertas",
            "Total Ofertas",
            order=6,
            color=BLUE,
            category_size=8,
        ),
        bar_chart(
            digest(f"{page}:salary"),
            654,
            272,
            602,
            404,
            "Subvención promedio por empresa",
            "Ofertas",
            "company",
            "Ofertas",
            "Subvención Promedio",
            order=7,
            color=GREEN,
            category_size=8,
        ),
        updated_card(page),
        footer(digest(f"{page}:footer")),
    ]


def build_deadlines() -> list[dict]:
    page = "Vencimientos"
    return [
        header(
            digest(f"{page}:header"),
            "Vencimientos y oportunidades · Deadlines and opportunities",
            "Prioriza las postulaciones por fecha límite · Prioritize applications by deadline",
        ),
        clear_button(digest(f"{page}:clear")),
        language_slicer(digest(f"{page}:language")),
        card(
            digest(f"{page}:message"),
            24,
            84,
            1048,
            56,
            "Ofertas",
            "Mensaje Ejecutivo",
            "",
            order=1,
            message=True,
        ),
        card(
            digest(f"{page}:kpi1"),
            24,
            176,
            196,
            84,
            "Ofertas",
            "Por Vencer",
            "Por vencer · Expiring",
            order=2,
            color=AMBER,
        ),
        card(
            digest(f"{page}:kpi2"),
            228,
            176,
            196,
            84,
            "Ofertas",
            "Vencidas",
            "Vencidas · Expired",
            order=3,
            color=RED,
        ),
        card(
            digest(f"{page}:kpi3"),
            432,
            176,
            196,
            84,
            "Ofertas",
            "Días Promedio para Vencer",
            "Días promedio · Avg days",
            order=4,
        ),
        table_visual(
            digest(f"{page}:table"),
            24,
            288,
            1216,
            388,
            "Ofertas ordenadas por vencimiento",
            [
                column("Ofertas", "title"),
                column("Ofertas", "company"),
                column("Ofertas", "deadline_at"),
                column("Ofertas", "days_to_deadline"),
                column("Estado", "label_es"),
                column("Ofertas", "salary_amount"),
            ],
            order=5,
            sort=sort_by_field("Ofertas", "deadline_at", "Ascending"),
            font_size=8,
        ),
        updated_card(page),
        footer(digest(f"{page}:footer")),
    ]


def build_quality() -> list[dict]:
    page = "Calidad"
    return [
        header(
            digest(f"{page}:header"),
            "Calidad de datos · Data quality",
            "Transparencia sobre vacíos y errores · Transparency about gaps and errors",
        ),
        clear_button(digest(f"{page}:clear")),
        language_slicer(digest(f"{page}:language")),
        card(
            digest(f"{page}:message"),
            24,
            84,
            1048,
            56,
            "Ofertas",
            "Mensaje Ejecutivo",
            "",
            order=1,
            message=True,
        ),
        card(
            digest(f"{page}:kpi1"),
            24,
            176,
            196,
            84,
            "Calidad",
            "Calidad General",
            "Calidad general · Overall",
            order=2,
        ),
        card(
            digest(f"{page}:kpi2"),
            228,
            176,
            196,
            84,
            "Calidad",
            "Reglas Fallidas",
            "Reglas fallidas · Failed rules",
            order=3,
            color=AMBER,
        ),
        card(
            digest(f"{page}:kpi3"),
            432,
            176,
            196,
            84,
            "Calidad",
            "Fallidas Totales",
            "Fallos totales · Total failures",
            order=4,
            color=RED,
        ),
        table_visual(
            digest(f"{page}:table"),
            24,
            288,
            760,
            388,
            "Resultado de las 17 reglas",
            [
                column("Calidad", "rule_id"),
                column("Calidad", "description_es"),
                column("Calidad", "severity_es"),
                column("Calidad", "checked"),
                column("Calidad", "failed"),
                column("Calidad", "pass_rate"),
                column("Calidad", "sample_failed_offer_ids"),
            ],
            order=5,
            sort=sort_by_field("Calidad", "rule_id", "Ascending"),
            font_size=8,
        ),
        bar_chart(
            digest(f"{page}:chart"),
            800,
            272,
            456,
            404,
            "Fallos por regla",
            "Calidad",
            "rule_id",
            "Calidad",
            "Fallidas Totales",
            order=6,
            color=RED,
            category_size=8,
        ),
        updated_card(page),
        footer(digest(f"{page}:footer")),
    ]


def build_help() -> list[dict]:
    page = "Cómo leer"
    paragraphs_intro = [
        paragraph(text_run("Qué es Practilizate", size=14, color=NAVY, bold=True)),
        paragraph(
            text_run(
                "Un observatorio reproducible de ofertas de prácticas preprofesionales en Lima. Los datos provienen de avisos públicos de practicas.pe y se publican agregados.",
                size=10,
            )
        ),
        paragraph(
            text_run(
                "Spanish primary, English toggle: usa el selector Idioma / Language para cambiar los mensajes dinámicos y el pie de actualización.",
                size=10,
            )
        ),
    ]
    paragraphs_how = [
        paragraph(text_run("Cómo usar el reporte", size=14, color=NAVY, bold=True)),
        paragraph(
            text_run("1. Filtra por carrera, empresa o estado con las segmentaciones.", size=10)
        ),
        paragraph(
            text_run(
                "2. Haz clic en una barra o sector para resaltar ofertas relacionadas.", size=10
            )
        ),
        paragraph(
            text_run("3. Usa Limpiar filtros para volver al estado inicial de la página.", size=10)
        ),
        paragraph(
            text_run(
                "4. Revisa Calidad para ver qué reglas fallaron y qué ofertas las originaron.",
                size=10,
            )
        ),
    ]
    paragraphs_glossary = [
        paragraph(text_run("Glosario", size=14, color=NAVY, bold=True)),
        paragraph(text_run("Oferta: convocatoria pública de prácticas.", size=10)),
        paragraph(
            text_run("Subvención: monto mensual publicado; puede no estar disponible.", size=10)
        ),
        paragraph(text_run("Por vencer: vence dentro de los próximos 7 días.", size=10)),
        paragraph(
            text_run(
                "Calidad: proporción de reglas aprobadas; las reglas críticas detienen la publicación.",
                size=10,
            )
        ),
    ]
    paragraphs_source = [
        paragraph(text_run("Fuente y límites", size=14, color=NAVY, bold=True)),
        paragraph(
            text_run("Fuente: practicas.pe. Practilizate no está afiliado a practicas.pe.", size=10)
        ),
        paragraph(
            text_run(
                "v0.1 cubre Lima y modalidad preprofesional. No se publican datos personales ni HTML crudo.",
                size=10,
            )
        ),
        paragraph(
            text_run(
                "Los promedios de subvención excluyen valores atípicos mayores a S/ 12,000.",
                size=10,
            )
        ),
    ]
    paragraphs_attribution = [
        paragraph(text_run("Atribución y reproducción", size=14, color=NAVY, bold=True)),
        paragraph(
            text_run(
                "Datos públicos de practicas.pe, usados con fines educativos y de investigación. El código es MIT; los datos derivados no están cubiertos por esa licencia. Consulta DATA_SOURCES.md y NOTICE.md en el repositorio.",
                size=10,
            )
        ),
    ]
    return [
        header(
            digest(f"{page}:header"),
            "Cómo leer · How to read",
            "Guía rápida, glosario y atribución · Quick guide, glossary and attribution",
        ),
        clear_button(digest(f"{page}:clear")),
        language_slicer(digest(f"{page}:language")),
        textbox(digest(f"{page}:intro"), 24, 96, 600, 148, paragraphs_intro, order=1, padding=16),
        textbox(digest(f"{page}:how"), 648, 96, 608, 180, paragraphs_how, order=2, padding=16),
        textbox(
            digest(f"{page}:glossary"), 24, 256, 600, 190, paragraphs_glossary, order=3, padding=16
        ),
        textbox(
            digest(f"{page}:source"), 648, 288, 608, 158, paragraphs_source, order=4, padding=16
        ),
        textbox(
            digest(f"{page}:attribution"),
            24,
            458,
            1232,
            158,
            paragraphs_attribution,
            order=5,
            padding=16,
        ),
        updated_card(page),
        footer(digest(f"{page}:footer")),
    ]


def theme() -> tuple[str, dict]:
    data_colors = [AMBER, GREY, RED, GREEN, NAVY, BLUE, "#8FAADC", "#A9D18E", "#F4B183", "#9E480E"]
    name_base = "PractilizateTheme"
    payload = {
        "$schema": "https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main/Report%20Theme%20JSON%20Schema/reportThemeSchema-2.159.json",
        "name": "",
        "dataColors": data_colors,
        "foreground": INK,
        "background": WHITE,
        "tableAccent": NAVY,
        "textClasses": {
            "callout": {"fontSize": 21, "fontFace": "Segoe UI Semibold", "color": INK},
            "title": {"fontSize": 12, "fontFace": "Segoe UI Semibold", "color": INK},
            "header": {"fontSize": 11, "fontFace": "Segoe UI Semibold", "color": NAVY},
            "label": {"fontSize": 10, "fontFace": "Segoe UI", "color": GREY},
        },
        "visualStyles": {
            "*": {
                "*": {
                    "background": [
                        {
                            "show": True,
                            "color": {"solid": {"color": WHITE}},
                            "transparency": 0,
                        }
                    ],
                    "border": [
                        {
                            "show": True,
                            "color": {"solid": {"color": BORDER}},
                            "radius": 8,
                        }
                    ],
                    "padding": [{"top": 8, "bottom": 8, "left": 8, "right": 8}],
                    "title": [
                        {
                            "show": True,
                            "fontColor": {"solid": {"color": INK}},
                            "fontSize": 11,
                            "alignment": "left",
                        }
                    ],
                }
            }
        },
    }
    serialized = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    suffix = hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:8]
    filename = f"{name_base}-{suffix}.json"
    payload["name"] = filename
    return filename, payload


def ensure_project_schemas() -> None:
    pbip_path = Path("powerbi/practilizate.pbip")
    if pbip_path.is_file():
        payload = json.loads(pbip_path.read_text(encoding="utf-8"))
        payload["$schema"] = (
            "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json"
        )
        pbip_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )
    pbir_path = REPORT_DIR / "definition.pbir"
    if pbir_path.is_file():
        payload = json.loads(pbir_path.read_text(encoding="utf-8"))
        payload["$schema"] = (
            "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json"
        )
        pbir_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )


def _title_text(visual: dict) -> str | None:
    title = visual.get("visual", {}).get("visualContainerObjects", {}).get("title", [])
    for entry in title:
        value = (
            entry.get("properties", {})
            .get("text", {})
            .get("expr", {})
            .get("Literal", {})
            .get("Value")
        )
        if isinstance(value, str):
            return value.strip("'")
    return None


def _set_title(visual: dict, value: str) -> None:
    title = (
        visual.setdefault("visual", {})
        .setdefault("visualContainerObjects", {})
        .setdefault("title", [])
    )
    if not title:
        title.append({"properties": {}})
    properties = title[0].setdefault("properties", {})
    properties["text"] = text(value)


def normalize_visuals() -> None:
    for visual_path in PAGES_DIR.glob("*/visuals/*/visual.json"):
        visual = json.loads(visual_path.read_text(encoding="utf-8"))
        content = visual.get("visual", {})
        visual_type = content.get("visualType")
        position_data = visual.get("position", {})
        if (
            visual_type == "cardVisual"
            and position_data.get("y") == 176
            and position_data.get("height") == 84
        ):
            position_data["height"] = 100
        if (
            visual_type in {"barChart", "donutChart", "tableEx"}
            and position_data.get("y") == 272
            and position_data.get("height") == 404
        ):
            position_data["y"] = 288
            position_data["height"] = 388

        title = _title_text(visual)
        if visual_type == "barChart" and title == "Ofertas por carrera":
            _set_title(visual, "Top 10 carreras por ofertas")
            visual.setdefault(
                "filterConfig", {"filters": [topn_filter("Carreras", "career_name", 10)]}
            )
        elif visual_type == "barChart" and title in {
            "Top habilidades por ofertas",
            "Top 10 habilidades por ofertas",
        }:
            _set_title(visual, "Top 10 habilidades por ofertas")
            visual.setdefault(
                "filterConfig", {"filters": [topn_filter("Habilidades", "skill", 10)]}
            )
        elif visual_type == "barChart" and title == "Empresas con más ofertas":
            _set_title(visual, "Top 10 empresas por ofertas")
            visual.setdefault("filterConfig", {"filters": [topn_filter("Ofertas", "company", 10)]})
        elif visual_type == "barChart" and title == "Subvención promedio por empresa":
            _set_title(visual, "Subvención promedio · Top 10 empresas")
            visual.setdefault("filterConfig", {"filters": [topn_filter("Ofertas", "company", 10)]})
        elif visual_type == "tableEx" and title == "Cobertura por carrera":
            _set_title(visual, "Top 10 carreras por cobertura")
            visual.setdefault(
                "filterConfig", {"filters": [topn_filter("Carreras", "career_name", 10)]}
            )

        for index, filter_definition in enumerate(
            visual.get("filterConfig", {}).get("filters", [])
        ):
            if filter_definition.get("type") == "TopN":
                filter_definition["name"] = (
                    "Filter"
                    + hashlib.sha256(f"topn:{visual['name']}:{index}".encode()).hexdigest()[:24]
                )

        visual_path.write_text(
            json.dumps(visual, ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )


def main() -> None:
    PAGES_DIR.mkdir(parents=True, exist_ok=True)
    THEMES_DIR.mkdir(parents=True, exist_ok=True)
    for stale in PAGES_DIR.iterdir():
        if stale.is_dir():
            shutil.rmtree(stale)

    pages = [
        ("Resumen ejecutivo", build_executive()),
        ("Habilidades", build_skills()),
        ("Empresas", build_companies()),
        ("Vencimientos", build_deadlines()),
        ("Calidad", build_quality()),
        ("Cómo leer", build_help()),
    ]
    page_ids = [write_page(name, visuals) for name, visuals in pages]
    (PAGES_DIR / "pages.json").write_text(
        json.dumps(
            {
                "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.1.0/schema.json",
                "pageOrder": page_ids,
                "activePageName": page_ids[0],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
        newline="\n",
    )

    theme_name, theme_payload = theme()
    for stale in THEMES_DIR.glob("PractilizateTheme-*.json"):
        stale.unlink()
    (THEMES_DIR / theme_name).write_text(
        json.dumps(theme_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )

    base_theme = {
        "baseTheme": {
            "name": "Fluent2-CY26SU10",
            "reportVersionAtImport": {"visual": "2.11.0", "report": "3.4.0", "page": "2.3.1"},
            "type": "SharedResources",
        },
        "customTheme": {
            "name": theme_name,
            "reportVersionAtImport": {"visual": "2.11.0", "report": "3.4.0", "page": "2.3.1"},
            "type": "RegisteredResources",
        },
    }
    report = {
        "$schema": SCHEMA_REPORT,
        "themeCollection": base_theme,
        "resourcePackages": [
            {
                "name": "SharedResources",
                "type": "SharedResources",
                "items": [
                    {
                        "name": "Fluent2-CY26SU10",
                        "path": "BaseThemes/Fluent2-CY26SU10.json",
                        "type": "BaseTheme",
                    }
                ],
            },
            {
                "name": "RegisteredResources",
                "type": "RegisteredResources",
                "items": [
                    {
                        "name": theme_name,
                        "path": theme_name,
                        "type": "CustomTheme",
                    }
                ],
            },
        ],
        "settings": {
            "useStylableVisualContainerHeader": True,
            "exportDataMode": "AllowSummarized",
            "defaultDrillFilterOtherVisuals": True,
            "allowChangeFilterTypes": True,
            "useEnhancedTooltips": True,
            "useDefaultAggregateDisplayName": True,
        },
    }
    (REPORT_DIR / "definition" / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
        newline="\n",
    )
    ensure_project_schemas()
    normalize_visuals()
    sys.stdout.write(f"pages={len(page_ids)} theme={theme_name}\n")


if __name__ == "__main__":
    main()
