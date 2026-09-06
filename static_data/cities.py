from static_data.cine_col_data import CINE_COLOMBIA_IDS_BY_CITY, CINE_COLOMBIA_SITE_ID_NAMES
from static_data.royal_films_data import ROYAL_FILMS_CITY_IDS

SUPPORTED_CITIES: list[str] = [
    "Armenia", "Barranquilla", "Bogotá", "Bucaramanga", "Buenaventura", "Buga",
    "Cali", "Cartagena", "Cartago", "Caucasia", "Chía", "Cúcuta", "Dosquebradas",
    "Envigado", "Florencia", "Fusagasugá", "Girardot", "Guajira", "Ibagué",
    "Ipiales", "Itagüí", "Madrid", "Manizales", "Medellín", "Montería",
    "Mosquera", "Neiva", "Palmira", "Pasto", "Pereira", "Popayán", "Santa Marta",
    "Santo Tomás", "Sincelejo", "Soledad", "Tuluá", "Tunja", "Valledupar",
    "Villavicencio", "Yopal", "Yumbo",
]

_CINEMARK_CITIES = {
    "Armenia", "Bogotá", "Bucaramanga", "Cali", "Cúcuta", "Florencia", "Ibagué",
    "Ipiales", "Medellín", "Montería", "Neiva", "Palmira", "Pasto", "Pereira",
    "Santa Marta", "Soledad", "Villavicencio", "Yopal",
}
_CINEPOLIS_CITIES = {
    "Barranquilla", "Bogotá", "Cali", "Manizales", "Valledupar", "Chía", "Envigado",
}

_CHAIN_CITIES = {
    "cinemark": _CINEMARK_CITIES,
    "cinepolis": _CINEPOLIS_CITIES,
    "cine_col": CINE_COLOMBIA_IDS_BY_CITY,
    "royal_films": ROYAL_FILMS_CITY_IDS,
}

def _build() -> dict[str, list[str]]:
    out : dict[str, list[str]] = {}
    
    for city in SUPPORTED_CITIES:
        chains = sorted(c for c, cities in _CHAIN_CITIES.items() if city in cities)
        if chains:
            out[city] = chains
    
    return out

CHAINS_BY_CITY: dict[str, list[str]] = _build()

def chains_for_city(city : str) -> list[str]:
    if city not in SUPPORTED_CITIES:
        raise ValueError(city)

    return list(CHAINS_BY_CITY.get(city, []))
