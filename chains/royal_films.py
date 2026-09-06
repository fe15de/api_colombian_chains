import datetime
import re
import requests
import urllib3
import warnings

from chains import _register
from chains.base import ChainScraper
from data_management.text_normalization import city_slug, normalize_title, slugify
from data_management.data_types import FilmScraped, Showtime

from static_data.royal_films_data import ROYAL_FILMS_CITY_IDS


_FORMAT_SUFFIX = re.compile(r"\s*\((2D|3D|4DX|IMAX|XD|DBOX|D-BOX|4D)\)\s*$", re.IGNORECASE)
_UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

class RoyalFilms(ChainScraper):
    code = 'royal_films'

    def fetch_films_raw(self, city : str):
        cid = ROYAL_FILMS_CITY_IDS[city]
        
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', urllib3.exceptions.InsecureRequestWarning)
            resp = requests.get(f'https://cinemasroyalfilms.com/api/billboard/city/{cid}', headers = {'User-Agent' : _UA}, verify = False)
        resp.raise_for_status()

        return {'date' : datetime.date.today().isoformat(), 'data' : resp.json()}

    def parse_films(self, raw : dict, city : str) -> list[FilmScraped]:
        out : list[FilmScraped] = []

        for film in raw['data'].get('data', []):
            film = film['pelicula']
            title = normalize_title(film['pelicula_nombre_formato'])
            title = _FORMAT_SUFFIX.sub('', title).strip()
            out.append(FilmScraped(title = title,
                                   slug = str(film['pelicula_id']),
                                   chain = self.code
                                   )
                       )
        return out

    def fetch_showtimes_raw(self, city : str, slug : str) -> dict:
        cid = ROYAL_FILMS_CITY_IDS[city]

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", urllib3.exceptions.InsecureRequestWarning)
            resp = requests.get(f"https://cinemasroyalfilms.com/api/movies/functions/{slug}/city/{cid}", headers={"User-Agent": _UA}, verify=False)
        resp.raise_for_status()

        return {"date": datetime.date.today().isoformat(), "data": resp.json()}

    def parse_showtimes(self, raw : dict, city : str, slug : str) -> list[FilmScraped]:
        out : list[FilmScraped] = []

        for show in raw['data'].get('data', []):
            if show["funcion_fecha"] != raw["date"]:
                continue
            start = datetime.datetime.fromisoformat(show["funcion_hora_inicio"].replace("Z", "+00:00")).strftime("%H:%M")
            out.append(Showtime(city=city,
                                chain=self.code,
                                theater_name=show["multicine"]["multicine_nombre"],
                                date=datetime.date.fromisoformat(show["funcion_fecha"]),
                                start=start,
                            )
                        )
        return out

_register(RoyalFilms())
