import re 
import unicodedata

chars_to_remove = {
    "‘": "",
    "’": "",
    "“": "",
    "”": "",
    "–": "-",
}

def _strip_accents(name : str) -> str:
    name = unicodedata.normalize('NFD', name)
    return "".join(ch for ch in name if unicodedata.category(ch) != 'Mn')

def normalize_title(name : str) -> str:
    name = _strip_accents(name)
    
    for src, dst in chars_to_remove.items():
        name = name.replace(src, dst)

    return name.strip()

def normalize_for_match(name : str) -> str:
    
    name = _strip_accents(name.lower())
    name = re.sub(r"[^a-z0-9\s]", " ", name)
    
    return re.sub(r"\s+", " ", name).strip()

def slugify(name : str) -> str:
    return re.sub(r"[:\s-]+", "-", name)

def city_slug(city : str) -> str:
    return _strip_accents(city)

