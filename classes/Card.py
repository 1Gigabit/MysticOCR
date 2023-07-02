from typing import List, Dict, Optional


class Card:
    object: str
    id: str
    oracle_id: str
    multiverse_ids: List[int]
    tcgplayer_id: int
    cardmarket_id: int
    name: str
    lang: str
    released_at: str
    uri: str
    scryfall_uri: str
    layout: str
    highres_image: bool
    image_status: str
    image_uris: Dict[str, str]
    mana_cost: str
    cmc: int
    type_line: str
    colors: List[str]
    color_identity: List[str]
    keywords: List[str]
    card_faces: List[Dict[str, str]]
    legalities: Dict[str, str]
    games: List[str]
    reserved: bool
    foil: bool
    nonfoil: bool
    finishes: List[str]
    oversized: bool
    promo: bool
    reprint: bool
    variation: bool
    set_id: str
    set: str
    set_name: str
    set_type: str
    set_uri: str
    set_search_uri: str
    scryfall_set_uri: str
    rulings_uri: str
    prints_search_uri: str
    collector_number: str
    digital: bool
    rarity: str
    card_back_id: str
    artist: str
    artist_ids: List[str]
    illustration_id: str
    border_color: str
    frame: str
    security_stamp: str
    full_art: bool
    textless: bool
    booster: bool
    story_spotlight: bool
    edhrec_rank: int
    penny_rank: int
    prices: Dict[str, Optional[str]]
    related_uris: Dict[str, str]
    purchase_uris: Dict[str, str]

    def __init__(self, card):
        self.object = card.get("object")
        self.id = card.get("id")
        self.oracle_id = card.get("oracle_id")
        self.multiverse_ids = card.get("multiverse_ids")
        self.tcgplayer_id = card.get("tcgplayer_id")
        self.cardmarket_id = card.get("cardmarket_id")
        self.name = card.get("name")
        self.lang = card.get("lang")
        self.released_at = card.get("released_at")
        self.uri = card.get("uri")
        self.scryfall_uri = card.get("scryfall_uri")
        self.layout = card.get("layout")
        self.highres_image = card.get("highres_image")
        self.image_status = card.get("image_status")
        self.image_uris = card.get("image_uris")
        self.mana_cost = card.get("mana_cost")
        self.cmc = card.get("cmc")
        self.type_line = card.get("type_line")
        self.colors = card.get("colors")
        self.color_identity = card.get("color_identity")
        self.keywords = card.get("keywords")
        self.card_faces = card.get("card_faces")
        self.legalities = card.get("legalities")
        self.games = card.get("games")
        self.reserved = card.get("reserved")
        self.foil = card.get("foil")
        self.nonfoil = card.get("nonfoil")
        self.finishes = card.get("finishes")
        self.oversized = card.get("oversized")
        self.promo = card.get("promo")
        self.reprint = card.get("reprint")
        self.variation = card.get("variation")
        self.set_id = card.get("set_id")
        self.set = card.get("set")
        self.set_name = card.get("set_name")
        self.set_type = card.get("set_type")
        self.set_uri = card.get("set_uri")
        self.set_search_uri = card.get("set_search_uri")
        self.scryfall_set_uri = card.get("scryfall_set_uri")
        self.rulings_uri = card.get("rulings_uri")
        self.prints_search_uri = card.get("prints_search_uri")
        self.collector_number = card.get("collector_number")
        self.digital = card.get("digital")
        self.rarity = card.get("rarity")
        self.card_back_id = card.get("card_back_id")
        self.artist = card.get("artist")
        self.artist_ids = card.get("artist_ids")
        self.illustration_id = card.get("illustration_id")
        self.border_color = card.get("border_color")
        self.frame = card.get("frame")
        self.security_stamp = card.get("security_stamp")
        self.full_art = card.get("full_art")
        self.textless = card.get("textless")
        self.booster = card.get("booster")
        self.story_spotlight = card.get("story_spotlight")
        self.edhrec_rank = card.get("edhrec_rank")
        self.penny_rank = card.get("penny_rank")
        self.prices = card.get("prices")
        self.related_uris = card.get("related_uris")
        self.purchase_uris = card.get("purchase_uris")


class OCRCard:
    id: int
    file_name: str
    ocr_result: str
    type: str
    location: str

    def __init__(self, id, file_name, ocr_result, type, location) -> None:
        self.id = id
        self.file_name = file_name
        self.ocr_result = ocr_result
        self.type = type
        self.location = location
