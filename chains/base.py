from abc import ABC, abstractmethod
from data_management.data_types import FilmScraped, Showtime

class ChainScraper(ABC):
    code: str 

    @abstractmethod
    def fetch_films_raw(self, city : str) -> dict | str:
        ...
    
    @abstractmethod
    def parse_films(self, raw : dict | str, city : str) -> list[FilmScraped]:
        ...

    @abstractmethod
    def fetch_showtimes_raw(self, city : str, slug : str) -> dict | str:
        ...

    @abstractmethod
    def parse_showtimes(self, raw : dict | str, city : str, slug : str) -> list[Showtime]:
        ...

    # @abstractmethod
    # def ticket_url(self, city : str, slug : str) -> str | None:
    #     ...

