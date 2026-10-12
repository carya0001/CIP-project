"""Shared lookup tables for the income data: cantons and BFS large regions."""

# BFS canton number -> (abbreviation, German name)
CANTONS = {
    1: ("ZH", "Zürich"),
    2: ("BE", "Bern"),
    3: ("LU", "Luzern"),
    4: ("UR", "Uri"),
    5: ("SZ", "Schwyz"),
    6: ("OW", "Obwalden"),
    7: ("NW", "Nidwalden"),
    8: ("GL", "Glarus"),
    9: ("ZG", "Zug"),
    10: ("FR", "Freiburg"),
    11: ("SO", "Solothurn"),
    12: ("BS", "Basel-Stadt"),
    13: ("BL", "Basel-Landschaft"),
    14: ("SH", "Schaffhausen"),
    15: ("AR", "Appenzell Ausserrhoden"),
    16: ("AI", "Appenzell Innerrhoden"),
    17: ("SG", "St. Gallen"),
    18: ("GR", "Graubünden"),
    19: ("AG", "Aargau"),
    20: ("TG", "Thurgau"),
    21: ("TI", "Tessin"),
    22: ("VD", "Waadt"),
    23: ("VS", "Wallis"),
    24: ("NE", "Neuenburg"),
    25: ("GE", "Genf"),
    26: ("JU", "Jura"),
}

# BFS Grossregion code (as used in the PxWeb API) -> name
GROSSREGIONS = {
    1: "Genferseeregion",
    2: "Espace Mittelland",
    3: "Nordwestschweiz",
    4: "Zürich",
    5: "Ostschweiz",
    6: "Zentralschweiz",
    7: "Tessin",
}

# Canton abbreviation -> Grossregion code
CANTON_TO_GROSSREGION = {
    "VD": 1, "VS": 1, "GE": 1,
    "BE": 2, "FR": 2, "SO": 2, "NE": 2, "JU": 2,
    "BS": 3, "BL": 3, "AG": 3,
    "ZH": 4,
    "GL": 5, "SH": 5, "AR": 5, "AI": 5, "SG": 5, "GR": 5, "TG": 5,
    "LU": 6, "UR": 6, "SZ": 6, "OW": 6, "NW": 6, "ZG": 6,
    "TI": 7,
}
