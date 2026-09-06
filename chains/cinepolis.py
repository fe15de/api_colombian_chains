import datetime
import json
import re
from zoneinfo import ZoneInfo
import requests

from chains import _register
from chains.base import ChainScraper
from data_management.text_normalization import city_slug, normalize_title, slugify
from data_management.data_types import FilmScraped, Showtime

_API = "https://cinepolis.com.co/Cartelera.aspx/GetNowPlayingByCity"
_COLOMBIA = ZoneInfo('America/Bogota')
_MS_DATE_RE = re.compile(r"/Date\((\d+)\)/")

def _city_key(city : str) -> str:
    return f'{city_slug(city).lower()}-colombia'

def _parse_billboard(text : str) -> dict:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        raise RuntimeError('cinepolis: billboard endpoint returned a non-json body')
    
    data = payload.get('d')
    if not data:
        raise RuntimeError('cinepolis: billboard unavailable for this city')
    
    return data

def _date_from_ms(ms_date : str) -> datetime.date:
    ms = int(_MS_DATE_RE.search(ms_date).group(1))
    return datetime.datetime.fromtimestamp(ms / 1000, tz = _COLOMBIA).date()

class Cinepolis(ChainScraper):
    code = 'cinepolis'

    def _fetch(self, city : str) -> dict:
        resp = requests.post(_API, json = {'claveCiudad' : _city_key(city), 'esVIP' : False}, headers = {'Content-Type' : 'application/json; charset=UTF-8'})
        resp.raise_for_status()
       
        return {'date' : datetime.date.today().isoformat(), 'data' : _parse_billboard(resp.text)}

    def fetch_films_raw(self, city : str) -> dict:
        return self._fetch(city)
        
    def fetch_showtimes_raw(self, city : str, slug : str) -> dict:
        return self._fetch(city)

    def parse_films(self, raw : dict, city : str) -> list[FilmScraped]:
        seen: set[str] = set()
        out : list[FilmScraped] = []

        for cinema in raw['data'].get('Cinemas', []):
            for day in cinema.get('Dates', []):
                for movie in day.get('Movies', []):
                    key = movie['Key']
                    if key in seen:
                        continue
                    seen.add(key)
                    out.append(FilmScraped(title = normalize_title(movie['Title']),
                                           chain = self.code,
                                           slug = key
                                           )
                               )
        return out

    def parse_showtimes(self, raw : dict, city : str, slug : str) -> list[Showtime]:
        on = datetime.date.fromisoformat(raw['date'])
        out : list[Showtime] = []

        for cinema in raw['data'].get('Cinemas', []):
            name = cinema['Name']
            for day in cinema.get('Dates', []):
                if _date_from_ms(day['FilterDate']) != on:
                    continue
                for movie in day.get('Movies', []):
                    if movie['Key'] != slug:
                        continue
                    for fmt in movie.get('Formats', []):
                        for show in fmt.get('Showtimes', []):
                            out.append(Showtime(city = city,
                                                chain = self.code,
                                                theater_name = name,
                                                date = on,
                                                start = show['Time'],
                                                format = fmt.get('Name'),
                                                language = fmt.get('language')
                                                )
                                       )

        return out

_register(Cinepolis())

