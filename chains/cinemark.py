import datetime 
import json
import requests
from bs4 import BeautifulSoup

from chains import _register
from chains.base import ChainScraper
from data_management.text_normalization import city_slug, normalize_title, slugify
from data_management.data_types import FilmScraped, Showtime

_COMPANY_ID = '5db771be04daec00076df3f5' 
_BILLBOARD_URL = 'https://www.cinemark.com.co/cartelera/{city}'
_MOVIE_PAGE = 'https://www.cinemark.com.co/cartelera/{city}/{slug}'

_UA = "Mozilla/5.0 (X11; Linux x86_64; rv:128.0) Gecko/20100101 Firefox/128.0"

def _next_data(html : str) -> dict:
    tag = BeautifulSoup(html, 'html.parser').find('script', {'id' : '__NEXT_DATA__'})
    if tag is None:
        raise RuntimeError('cinemark: __NEXT_DATA__ script not found')

    return json.loads(tag.string)

class Cinemark(ChainScraper):
    code = 'cinemark'

    def fetch_films_raw(self, city : str) -> dict:
        return requests.get(_BILLBOARD_URL.format(city = city_slug(city)),
                            headers = {'User-Agent': _UA}
                            ).text

    def parse_films(self, raw : str, city : str) -> list[FilmScraped]:
        billboard = _next_data(raw)["props"]["pageProps"]["PremieresBillboard"]
        out : list[FilmScraped] = []
        
        for movie in billboard:
            title = normalize_title(movie.get('TitleAlt') or movie['Title'])
            out.append(FilmScraped(title = title,
                                   chain = self.code,
                                   slug = slugify(title)
                                   )
                       )
        return out

    
    def fetch_showtimes_raw(self, city : str, slug : str) -> dict:
        page = requests.get(_MOVIE_PAGE.format(city = city_slug(city), slug=slug), headers = {'User-Agent' : _UA})
        film_id = _next_data(page.text)["props"]["pageProps"]["movie"]["CorporateFilmId"]
        today = datetime.date.today()

        api = (
            f"https://api.cinemark-core.com/vista/country/co/city/{city_slug(city)}"
            f"/movie/{film_id}?date={today.isoformat()}&companyId={_COMPANY_ID}"
            f"&midnightSessionStart=22&midnightSessionEnd=02"
        )
        data = requests.get(api, headers={'connectapitoken' : 'a'}).json()
       
        return {'date' : today.isoformat(), 'data' : data}

    def parse_showtimes(self, raw : dict, city : str, slug : str) -> list[Showtime]:

        on = datetime.date.fromisoformat(raw['date'])
        out : list[Showtime] = []

        for theater in raw['data'].get('Theater', []):
            name = theater['Name']
            for fmt in theater.get('Format',[]):
                fmt_name = fmt.get('Name')
                for session in fmt.get('Sessions',[]):
                    if not session.get('IsVisible'):
                        continue
                    out.append(Showtime(city = city,
                                        chain = self.code,
                                        theater_name = name,
                                        date = on,
                                        start = session["Showtime"][:5],
                                        format = fmt_name,
                                        )
                               )
        
        return out


_register(Cinemark())
