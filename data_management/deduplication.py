
from dataclasses import dataclass, field
from rapidfuzz import fuzz 
from data_management.text_normalization import normalize_for_match
from data_management.data_types import Film, FilmScraped

@dataclass
class _Group:
    title : str 
    norm : str 
    slugs : dict[str, str]

def _matches(a_title : str, a_norm : str, group : _Group, cutoff : int) -> bool:

    score = fuzz.token_set_ratio(a_norm, group.norm)
    if score >= cutoff:
        return True
    
    return False

def merge_films(scrapped : list[FilmScraped], cutoff : int = 90) -> list[Film]:
    
    groups : list[_Group] = []
    for film in scrapped:
        norm = normalize_for_match(film.title)
        for group in groups:
            if _matches(film.title, norm, group, cutoff):
                group.slugs.setdefault(film.chain, film.slug)
                break
        else:
            groups.append(_Group(title = film.title, norm = norm, slugs = {film.chain: film.slug}))

    return [Film(title = group.title, slugs = dict(group.slugs), chains = sorted(group.slugs)) for group in groups]

