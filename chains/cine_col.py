import datetime
import time 
import requests
from zoneinfo import ZoneInfo
from browser.browser import get_auth_header  
from chains import _register
from chains.base import ChainScraper
from data_management.text_normalization import normalize_title
from data_management.data_types import FilmScraped, Showtime
from static_data.cine_col_data import CINE_COLOMBIA_IDS_BY_CITY, CINE_COLOMBIA_SITE_ID_NAMES


_API = "https://digital-api.cinecolombia.com/ocapi/v1"
_TOKEN : dict[str, float | str] = {}
_TOKEN_TTL = 1800
_COLOMBIA = ZoneInfo('America/Bogota')

def _site_ids(city : str) -> str:
    ids = CINE_COLOMBIA_IDS_BY_CITY[city]

    return '&'.join(f'siteIds={i}' for i in ids)

def _token(force : bool = False) -> str:
    now = time.time()

    if not force and _TOKEN.get('value') and now - float(_TOKEN['ts']) < _TOKEN_TTL:
        return str(_TOKEN['value'])
    
    value = get_auth_header('https://www.cinecolombia.com/', 'digital-api')
    
    if not value:
        raise RuntimeError('cine_col: could not capture API token')
    _TOKEN.update(value = value, ts = now)

    return value

def _get_json(url : str) -> dict:
    resp = requests.get(url, headers = {'Authorization': _token()})
    
    if resp.status_code != 200:
        resp = requests.get(url, headers = {'Authorization': _token(force = True)})
    
    # resp.raise_for_status()
    return resp.json()

class CineCol(ChainScraper):
    code = 'cine_col'

    def fetch_films_raw(self, city : str) -> dict:
        screening = _get_json(f'{_API}/film-screening-dates?{_site_ids(city)}')
        screenings = screening['filmScreeningDates'][0]['filmScreenings']
        
        ids = sorted({s['filmId'] for s in screenings})
        details = {str(i): _get_json(f'{_API}/films/{i}') for i in ids}

        return {'screening_dates' : screening, 'film_details' : details}

    def parse_films(self, raw : dict, city : str) -> list[FilmScraped]:
        screenings = raw["screening_dates"]["filmScreeningDates"][0]["filmScreenings"]
        ids = sorted({s["filmId"] for s in screenings})
        out: list[FilmScraped] = []
        for fid in ids:
            detail = raw["film_details"][str(fid)]
            title = normalize_title(detail["film"]["title"]["translations"][0]["text"])
            out.append(FilmScraped(chain=self.code, title=title, slug=str(fid)))

        return out

    def fetch_showtimes_raw(self, city : str, slug : str) -> dict:
        url = f"{_API}/showtimes/by-business-date/first?filmIds={slug}&{_site_ids(city)}"
        
        return {'date' : datetime.date.today().isoformat(), 'data' : _get_json(url)}

    def parse_showtimes(self, raw : dict, city : str, slug : str) -> list[Showtime]:
        out: list[Showtime] = []

        for show in raw['data'].get('showtimes',[]):
            dt = datetime.datetime.fromisoformat(show['schedule']['startsAt'])
            if dt.tzinfo is not None:
                dt = dt.astimezone(_COLOMBIA)
            
            name = CINE_COLOMBIA_SITE_ID_NAMES.get(str(show['siteId']))
            out.append(Showtime(city = city,
                                chain = self.code,
                                theater_name = name,
                                date= dt.date(),
                                start = dt.strftime("%H:%M")
                                )
                       )

        return out

_register(CineCol())
