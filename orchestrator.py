import datetime
import logging
import sys

from chains import CHAIN_REGISTRY
from static_data.cities import SUPPORTED_CITIES, chains_for_city
from data_management.deduplication import merge_films
from data_management.data_types import Film, ChainFilmData

log = logging.getLogger(__name__)

def list_films(city : str) -> list[Film]:
    scraped = []
    
    for code in chains_for_city(city):
        try:
            scraper = CHAIN_REGISTRY[code]
            raw = scraper.fetch_films_raw(city)
            scraped.extend(scraper.parse_films(raw, city))
        except Exception:
            log.exception('list_films: chain %s failed for %s', code , city)

    return merge_films(scraped)

def get_showtimes(city : str, film : Film, on: datetime.date | None = None) -> list[ChainFilmData]:
    if city not in SUPPORTED_CITIES:
        raise ValueError(city)
    
    results : list[ChainFilmData] = []
    for code in film.chains:
        try:
            scraper = CHAIN_REGISTRY[code]
            slug = film.slugs[code]
        except KeyError:
            log.exception('get_showtimes: no scraper/slug for chains %s (%s)', code, film.title)
            continue
        
        showtimes = []

        try:
            raw = scraper.fetch_showtimes_raw(city, slug)
            showtimes = scraper.parse_showtimes(raw, city, slug)
            if on is not None:
                showtimes = [s for s in showtimes if s.date == on]
        except Exception:
            log.exception('get_showtimes: chain %s failed for %s / %s', code , city, film.title)

        results.append(ChainFilmData(chain = code,
                                     showtimes = showtimes
                                     )
                       )
    return results


if __name__ == '__main__':
    logging.basicConfig(level = logging.INFO, format = '%(levelname)s %(message)s')

    city = sys.argv[1] if len(sys.argv) > 1 else 'Bogotá'
    if city not in SUPPORTED_CITIES:
        sys.exit(f'unknown city {city!r}\nsupported: {", ".join(SUPPORTED_CITIES)}')

    for film in list_films(city):
        print(f'\n{film.title}  [{", ".join(film.chains)}]')
        for cfd in get_showtimes(city, film):
            for s in cfd.showtimes:
                extra = " ".join(x for x in (s.format, s.language) if x)
                print(f'  {cfd.chain:12} {s.date} {s.start:>5}  {s.theater_name}  {extra}')

