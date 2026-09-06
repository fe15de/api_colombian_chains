# api_chains

Aggregate **movie showtimes across Colombian cinema chains** into one normalized list.

Given a city, `api_chains` asks every chain that operates there for its current billboard,
merges the same film showing under slightly different titles into a single entry, and then
pulls per-theater showtimes for each film.

```
$ python orchestrator.py "Bogotá"

La Odisea  [cine_col, cinemark, cinepolis, royal_films]
  cine_col     2026-09-06 19:30  LUMINA
  cinemark     2026-09-05 22:00  Pacific Mall
  cinepolis    2026-09-05 21:10  Cinépolis VIP Plaza Claro  DOB
```

---

## Supported chains

| Logo | Code | Source | Auth | Status |
|------|------|--------|------|--------|
| <img src="https://upload.wikimedia.org/wikipedia/commons/8/8d/CineColombia.png" height="26" alt="Cine Colombia"> | `cine_col` | `digital-api.cinecolombia.com` JSON API | Bearer token captured from a headless browser session | ✅ working |
| <img src="https://upload.wikimedia.org/wikipedia/commons/c/cd/Cinemark_Logo.svg" height="20" alt="Cinemark"> | `cinemark` | `cinemark.com.co` Next.js pages + `api.cinemark-core.com` | Browser `User-Agent` only | ✅ working |
| <img src="https://upload.wikimedia.org/wikipedia/commons/4/44/Cin%C3%A9polis.svg" height="20" alt="Cinepolis"> | `cinepolis` | `cinepolis.com.co/Cartelera.aspx` billboard endpoint | none | ✅ working |
| <img src="https://upload.wikimedia.org/wikipedia/commons/f/f5/Royal_Films_logo.svg" height="26" alt="Royal Films"> | `royal_films` | `cinemasroyalfilms.com/api` JSON API | `GET` + browser `User-Agent` (POST is rejected `401`) | ✅ working |

> Logos are hotlinked from Wikimedia Commons.

---

## Install

Requires **Python 3.11+**.

```bash
python -m venv env
source env/bin/activate
pip install -r requirements.txt

# Cine Colombia needs a real browser to capture its API token
playwright install firefox
```

---

## Usage

```bash
python orchestrator.py "<City>"
```

- City name is the single argument. Quote names with spaces or accents: `"Santa Marta"`, `"Bogotá"`.
- No argument → defaults to `Bogotá`.
- Unknown city → prints the list of supported cities and exits.

### As a library

```python
from orchestrator import list_films, get_showtimes

films = list_films("Cali")                 # -> list[Film]
for film in films:
    for chain_data in get_showtimes("Cali", film):   # -> list[ChainFilmData]
        for s in chain_data.showtimes:
            print(chain_data.chain, s.date, s.start, s.theater_name)
```

`get_showtimes` accepts an optional `on=datetime.date(...)` to keep only showtimes on that day.

---

## How it works

```
orchestrator.list_films(city)
        │
        ├── chains_for_city(city)            static_data/cities.py  — which chains operate in this city
        │
        ├── for each chain code:
        │       scraper.fetch_films_raw(city)      → raw API payload / HTML
        │       scraper.parse_films(raw, city)     → list[FilmScraped]  (title, slug, chain)
        │
        └── merge_films(all_scraped)          data_management/deduplication.py
                fuzzy-matches titles (rapidfuzz token_set_ratio ≥ 90)
                → list[Film]  (title, slugs={chain: slug}, chains=[...])

orchestrator.get_showtimes(city, film)
        └── for each chain in film.chains:
                scraper.fetch_showtimes_raw(city, film.slugs[chain])
                scraper.parse_showtimes(raw, city, slug)   → list[Showtime]
                → ChainFilmData(chain, showtimes, ticket_url)
```

Each chain scraper is a subclass of `ChainScraper` (`chains/base.py`) and registers itself
in `CHAIN_REGISTRY` on import. `chains/__init__.py` imports every chain module so the
registry is populated as a side effect.

### Layout

| Path | Responsibility |
|------|----------------|
| `orchestrator.py` | Entry point + `list_films` / `get_showtimes` |
| `chains/base.py` | `ChainScraper` abstract base |
| `chains/<name>.py` | One scraper per chain, self-registering |
| `data_management/data_types.py` | `FilmScraped`, `Showtime`, `Film`, `ChainFilmData` dataclasses |
| `data_management/deduplication.py` | `merge_films` — fuzzy title grouping |
| `data_management/text_normalization.py` | Accent stripping, slugifying, match normalization |
| `static_data/cities.py` | Supported cities + city→chains map |
| `static_data/*_data.py` | Per-chain city/site ID lookup tables |
| `browser/browser.py` | Headless-browser auth-header capture (Playwright) for `cine_col` |

### Data model

```python
FilmScraped(title, slug, chain)
Showtime(city, theater_name, date, start, chain, format=None, language=None)
Film(title, slugs={chain: slug}, chains=[chain, ...])
ChainFilmData(chain, showtimes=[Showtime, ...], ticket_url=None)
```

---

## Adding a chain

1. Create `chains/mychain.py` with a `ChainScraper` subclass implementing
   `fetch_films_raw`, `parse_films`, `fetch_showtimes_raw`, `parse_showtimes`
   (and optionally `ticket_url`).
2. Call `_register(MyChain())` at the bottom of the module.
3. Add `from chains import mychain as _mychain` to `chains/__init__.py`.
4. Add the chain's city coverage to `_CHAIN_CITIES` in `static_data/cities.py`.

---

## Known issues

- **Cinépolis** returns `{"d": null}` for some cities (e.g. Cali) — the endpoint reports its
  own billboard as unavailable. Works for Bogotá and other large cities.
- **Sequential fetching.** A large city fans out to one HTTP request per film per chain, so a
  full run can take a couple of minutes. Parallelizing `get_showtimes` is the obvious next step.
- `merge_films` groups purely on title similarity; a very generic or heavily localized title
  can merge two different films or split one.
