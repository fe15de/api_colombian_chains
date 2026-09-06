from chains.base import ChainScraper

CHAIN_REGISTRY : dict[str, ChainScraper] = {}

def _register(scraper : ChainScraper) -> None:
    CHAIN_REGISTRY[scraper.code] = scraper

def get_scraper(code : str) -> ChainScraper:    
    try:
        return CHAIN_REGISTRY[code]
    except KeyError:
        raise ValueError(code) 

from chains import cine_col as _cine_col
from chains import cinemark as _cinemark
from chains import cinepolis as _cinepolis
from chains import royal_films as _royal_films
