import datetime 
from dataclasses import dataclass, field

@dataclass
class FilmScraped:
    title : str 
    slug : str 
    chain : str 

@dataclass
class Showtime:
    city : str 
    theater_name : str 
    date : datetime.date
    start : str
    chain : str
    format : str | None = None
    language : str | None = None

@dataclass
class Film:
    title : str 
    slugs : dict[str,str] = field(default_factory=dict)
    chains : list[str] = field(default_factory=list)

@dataclass
class ChainFilmData:
    chain : str
    showtimes : list[Showtime]
    ticket_url : str | None = None
