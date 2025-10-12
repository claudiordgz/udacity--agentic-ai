from __future__ import annotations

import os
from typing import TypedDict, List, Dict, Optional, Literal

import requests
from tavily import TavilyClient
from datetime import datetime

from .tooling import tool, Tool

class GOTCharacter(TypedDict):
    name: str
    slug: str
    house: Dict[str, str]


class GOTQuote(TypedDict):
    sentence: str
    character: GOTCharacter


class WeatherCoord(TypedDict):
    lon: float
    lat: float


class WeatherMain(TypedDict):
    temp: float
    feels_like: float
    temp_min: float
    temp_max: float
    pressure: int
    humidity: int
    sea_level: Optional[int]
    grnd_level: Optional[int]


class WeatherWind(TypedDict):
    speed: float
    deg: int
    gust: Optional[float]


class WeatherClouds(TypedDict):
    all: int


class WeatherSys(TypedDict):
    country: str
    sunrise: int
    sunset: int


class WeatherCondition(TypedDict):
    id: int
    main: str
    description: str
    icon: str


class OpenWeatherResponse(TypedDict):
    coord: WeatherCoord
    weather: List[WeatherCondition]
    base: str
    main: WeatherMain
    visibility: int
    wind: WeatherWind
    clouds: WeatherClouds
    dt: int
    sys: WeatherSys
    timezone: int
    id: int
    name: str
    cod: int


class ExchangeRateResponse(TypedDict, total=False):
    result: str
    documentation: str
    terms_of_use: str
    time_last_update_unix: int
    time_last_update_utc: str
    time_next_update_unix: int
    time_next_update_utc: str
    base_code: str
    conversion_rates: Dict[str, float]


class Post(TypedDict, total=False):
    userId: int
    id: int
    title: str
    body: str


# =================== Tavily Web Search ===================

class TavilyResultItem(TypedDict, total=False):
    url: str
    title: str
    content: str
    score: float
    raw_content: Optional[str]


class TavilySearchResponse(TypedDict, total=False):
    query: str
    follow_up_questions: Optional[List[str]]
    answer: Optional[str]
    images: List[str]
    results: List[TavilyResultItem]
    response_time: float
    request_id: str


class SearchMetadata(TypedDict):
    timestamp: str
    query: str


class WebSearchFormattedResponse(TypedDict):
    answer: str
    results: List[TavilyResultItem]
    search_metadata: SearchMetadata


def _get_tavily_client() -> TavilyClient:
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        raise RuntimeError("TAVILY_API_KEY is not set")
    return TavilyClient(api_key=api_key)


@tool
def get_got_quote() -> GOTQuote:
    """Get a random Game of Thrones quote.

    Inputs:
        None

    Returns:
        GOTQuote: {"sentence": str, "character": {"name": str, "slug": str, "house": {"name": str, ...}}}

    Notes:
        - Source: `https://api.gameofthronesquotes.xyz/v1/random`
        - Useful fields: `sentence`, `character.name`, `character.house.name`.
        - Timeout: 30s; raises for non-2xx responses.
    """
    url = "https://api.gameofthronesquotes.xyz/v1/random"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()  # type: ignore[return-value]


@tool
def get_city_weather(city: str) -> OpenWeatherResponse:
    """Get current weather for a city using OpenWeather (metric units).

    Inputs:
        city (str): City name, e.g., "São Paulo" or "London".

    Returns:
        OpenWeatherResponse: Includes keys such as
            - name (str): city name
            - weather[0].description (str): human-readable condition
            - main.temp (float): temperature in °C
            - wind.speed (float): wind speed in m/s
            - sys.country (str), dt (int epoch), timezone (int seconds)

    Units & Formatting:
        - Temperature: °C (units=metric)
        - Wind speed: m/s

    Environment:
        - Requires OPENWEATHER_API_KEY in environment.

    Errors:
        - Raises RuntimeError if the API key is missing.
        - Raises for non-2xx responses.
    """
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENWEATHER_API_KEY is not set")
    url = f"{base_url}?appid={api_key}&q={city}&units=metric"
    response = requests.get(url=url, timeout=30)
    response.raise_for_status()
    return response.json()  # type: ignore[return-value]


@tool
def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """Get the conversion rate between two currencies using ExchangeRate-API.

    Inputs:
        from_currency (str): ISO 4217 code (e.g., "USD").
        to_currency (str): ISO 4217 code (e.g., "BRL").

    Returns:
        float: Conversion rate for 1 from_currency → to_currency (e.g., 5.3717).

    Usage example:
        - To convert 100 USD to BRL: amount_brl = 100 * rate

    Environment:
        - Requires EXCHANGERATE_API_KEY in environment.

    Errors:
        - Raises RuntimeError if API key is missing.
        - Raises ValueError if API result is not "success".
        - Raises KeyError if `to_currency` is not in the returned rates.
        - Raises for non-2xx responses.
    """
    base_url = "https://v6.exchangerate-api.com/v6"
    api_key = os.getenv("EXCHANGERATE_API_KEY")
    if not api_key:
        raise RuntimeError("EXCHANGERATE_API_KEY is not set")
    url = f"{base_url}/{api_key}/latest/{from_currency}"
    response = requests.get(url=url, timeout=30)
    response.raise_for_status()
    data: ExchangeRateResponse = response.json()  # type: ignore[assignment]
    if data.get("result") != "success":
        raise ValueError(f"ExchangeRate API error: {data.get('result')}")
    rates = data.get("conversion_rates") or {}
    if to_currency not in rates:
        raise KeyError(f"Rate for {to_currency} not found")
    return rates[to_currency]


@tool
def get_post(post_id: int) -> Post:
    """Fetch a post by id from JSONPlaceholder.

    Inputs:
        post_id (int): Post identifier (1..100 in JSONPlaceholder sample).

    Returns:
        Post: {"userId": int, "id": int, "title": str, "body": str}

    Notes:
        - Source: `https://jsonplaceholder.typicode.com/posts/{id}`
        - JSONPlaceholder is a fake API; data is static/non-persistent.
        - Raises for non-2xx responses.
    """
    url = f"https://jsonplaceholder.typicode.com/posts/{post_id}"
    response = requests.get(url=url, timeout=30)
    response.raise_for_status()
    return response.json()  # type: ignore[return-value]


@tool
def create_post(title: str, body: str, user_id: int) -> Post:
    """Create a post in JSONPlaceholder (fake API returns the created object).

    Inputs:
        title (str): Post title.
        body (str): Post body/content.
        user_id (int): Author user id.

    Returns:
        Post: Echoed post with an `id` assigned by the API.

    Notes:
        - Source: `POST https://jsonplaceholder.typicode.com/posts`
        - JSONPlaceholder is fake; posts are not persisted server-side.
        - Payload is sent as JSON; raises for non-2xx responses.
    """
    url = "https://jsonplaceholder.typicode.com/posts"
    payload = {"title": title, "body": body, "userId": user_id}
    response = requests.post(url=url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()  # type: ignore[return-value]


@tool
def update_post(post_id: int, title: Optional[str] = None, body: Optional[str] = None) -> Post:
    """Update a post in JSONPlaceholder via PUT; returns the updated object.

    Inputs:
        post_id (int): Post identifier to update.
        title (str, optional): New title.
        body (str, optional): New body.

    Returns:
        Post: The updated post object.

    Notes:
        - Source: `PUT https://jsonplaceholder.typicode.com/posts/{id}`
        - Partial updates supported here by sending only provided fields.
        - JSONPlaceholder is fake; updates are not persisted.
        - Payload is sent as JSON; raises for non-2xx responses.
    """
    url = f"https://jsonplaceholder.typicode.com/posts/{post_id}"
    payload: Dict[str, str] = {}
    if title is not None:
        payload["title"] = title
    if body is not None:
        payload["body"] = body
    response = requests.put(url=url, json=payload, timeout=30)
    response.raise_for_status()
    return response.json()  # type: ignore[return-value]


@tool
def web_search(query: str,
               search_depth: Literal["basic", "advanced"] = "basic",
               max_results: int = 5) -> WebSearchFormattedResponse:
    """Search the web using Tavily with teacher-style formatting.

    Inputs:
        query (str): Natural-language query (e.g., "what is solana").
        search_depth ("basic"|"advanced"): Depth of search; "advanced" may be slower.
        max_results (int): Number of results to return (1–10 recommended; default 5).

    Returns:
        WebSearchFormattedResponse: {"answer": str, "results": [...], "search_metadata": {"timestamp", "query"}}
        - results: [{url, title, content, score, raw_content?}]

    Notes:
        - API key: set TAVILY_API_KEY in the environment.
        - Errors: raises RuntimeError if API key is missing; other client errors propagate.
    """
    client = _get_tavily_client()
    safe_max = max(1, min(int(max_results), 10))
    search_result: TavilySearchResponse = client.search(
        query=query,
        search_depth=search_depth,          # teacher-style
        include_answer=True,
        include_raw_content=False,
        include_images=False,
        max_results=safe_max,
    )  # type: ignore[assignment]

    formatted: WebSearchFormattedResponse = {
        "answer": search_result.get("answer", "") or "",
        "results": search_result.get("results", []) or [],
        "search_metadata": {
            "timestamp": datetime.now().isoformat(),
            "query": query,
        },
    }
    return formatted

# =================== Comparison Tool ===================

class ComparisonHighlight(TypedDict, total=False):
    title: str
    url: str
    snippet: str


class ComparisonReport(TypedDict):
    common_terms: List[str]
    unique_terms_by_source: Dict[str, List[str]]
    highlights: List[ComparisonHighlight]


def _tokenize(text: str) -> List[str]:
    tokens = []
    word = []
    for ch in text.lower():
        if ch.isalnum():
            word.append(ch)
        else:
            if word:
                tokens.append("".join(word))
                word = []
    if word:
        tokens.append("".join(word))
    return tokens


_STOPWORDS = {
    "the","a","an","and","or","of","to","in","on","for","with","by","from","is","are","as","at","this","that","it","be","was","were","has","have","had","will","can","not","but","than","then","so","such","via"
}


@tool
def compare_sources(items: List[TavilyResultItem], top_n: int = 3) -> ComparisonReport:
    """Compare multiple source snippets to extract common and unique terms and quick highlights.

    Inputs:
        items (List[TavilyResultItem]): Each item should include at least {title, url, content}.
        top_n (int): Number of highlights to include (default 3).

    Returns:
        ComparisonReport: {
          "common_terms": [str],
          "unique_terms_by_source": {title: [str]},
          "highlights": [{"title", "url", "snippet"}]
        }

    Notes:
        - Heuristic, lightweight comparison; not semantic entailment.
        - Use to create a quick synthesis after web_search.
    """
    if not items:
        return {"common_terms": [], "unique_terms_by_source": {}, "highlights": []}

    token_sets: Dict[str, set] = {}
    for item in items:
        title = item.get("title", "") or item.get("url", "source")
        content = item.get("content", "") or ""
        tokens = [t for t in _tokenize(content) if t not in _STOPWORDS and len(t) > 2]
        token_sets[title] = set(tokens)

    # Common terms across all sources
    common_terms: List[str] = []
    if token_sets:
        iter_sets = iter(token_sets.values())
        common = next(iter_sets).copy()
        for s in iter_sets:
            common &= s
        common_terms = sorted(list(common))[:20]

    # Unique terms per source (subtract union of others)
    all_titles = list(token_sets.keys())
    unique_terms_by_source: Dict[str, List[str]] = {}
    for t in all_titles:
        others_union = set().union(*[token_sets[o] for o in all_titles if o != t]) if len(all_titles) > 1 else set()
        unique = sorted(list(token_sets[t] - others_union))[:20]
        unique_terms_by_source[t] = unique

    # Highlights: first sentence/snippet of each, up to top_n
    highlights: List[ComparisonHighlight] = []
    for item in items[: max(1, top_n)]:
        content = (item.get("content") or "").strip()
        first_break = min([i for i in [content.find(". "), content.find("\n")] if i != -1] or [120])
        snippet = content[: first_break + 1] if content else ""
        highlights.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "snippet": snippet,
        })

    return {
        "common_terms": common_terms,
        "unique_terms_by_source": unique_terms_by_source,
        "highlights": highlights,
    }

def get_all_tools() -> List[Tool]:
    """Return all available tool instances defined in this module."""
    return [
        get_got_quote,
        get_city_weather,
        get_exchange_rate,
        get_post,
        create_post,
        update_post,
        web_search,
        compare_sources,
    ]

