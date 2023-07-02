from typing import List, Dict, Optional

from classes.Card import Card


class ImageUris:
    small: str
    normal: str
    large: str
    png: str
    art_crop: str
    border_crop: str


class Legalities:
    standard: str
    future: str
    historic: str
    gladiator: str
    pioneer: str
    explorer: str
    modern: str
    legacy: str
    pauper: str
    vintage: str
    penny: str
    commander: str
    oathbreaker: str
    brawl: str
    historicbrawl: str
    alchemy: str
    paupercommander: str
    duel: str
    oldschool: str
    premodern: str
    predh: str


class Preview:
    source: str
    source_uri: str
    previewed_at: str


class Prices:
    usd: str
    usd_foil: str
    usd_etched: Optional[str]
    eur: str
    eur_foil: str
    tix: str


class RelatedUris:
    gatherer: str
    tcgplayer_infinite_articles: str
    tcgplayer_infinite_decks: str
    edhrec: str


class PurchaseUris:
    tcgplayer: str
    cardmarket: str
    cardhoarder: str


class ScryfallResponse:
    object: str
    total_cards: int
    has_more: bool
    next_page: Optional[str]
    data: List[Card]

    def __init__(self, data) -> None:
        self.data = data
        pass
