from dataclasses import dataclass
from typing import List, Optional


@dataclass
class UniverseStock:
    symbol: str
    yahoo: str
    name: str
    aliases: List[str]


UNIVERSE = [
    UniverseStock("RELIANCE", "RELIANCE.NS", "Reliance Industries",
                  ["ril", "reliance industries"]),

    UniverseStock("TCS", "TCS.NS", "Tata Consultancy Services",
                  ["tata consultancy"]),

    UniverseStock("INFY", "INFY.NS", "Infosys",
                  ["infosys"]),

    UniverseStock("HDFCBANK", "HDFCBANK.NS", "HDFC Bank",
                  ["hdfc", "hdfc bank"]),

    UniverseStock("ICICIBANK", "ICICIBANK.NS", "ICICI Bank",
                  ["icici"]),

    UniverseStock("SBIN", "SBIN.NS", "State Bank of India",
                  ["sbi"]),

    UniverseStock("BHARTIARTL", "BHARTIARTL.NS", "Bharti Airtel",
                  ["airtel", "bharti"]),

    UniverseStock("ITC", "ITC.NS", "ITC",
                  ["itc limited"]),

    UniverseStock("LT", "LT.NS", "Larsen & Toubro",
                  ["l&t", "larsen"]),

    UniverseStock("HINDUNILVR", "HINDUNILVR.NS", "Hindustan Unilever",
                  ["hul"]),

    UniverseStock("KOTAKBANK", "KOTAKBANK.NS", "Kotak Mahindra Bank",
                  ["kotak"]),

    UniverseStock("AXISBANK", "AXISBANK.NS", "Axis Bank",
                  ["axis"]),

    UniverseStock("BAJFINANCE", "BAJFINANCE.NS", "Bajaj Finance",
                  ["bajaj finance"]),

    UniverseStock("ASIANPAINT", "ASIANPAINT.NS", "Asian Paints",
                  ["asian paints"]),

    UniverseStock("MARUTI", "MARUTI.NS", "Maruti Suzuki",
                  ["maruti suzuki"]),

    UniverseStock("TITAN", "TITAN.NS", "Titan",
                  []),

    UniverseStock("SUNPHARMA", "SUNPHARMA.NS", "Sun Pharma",
                  ["sun pharma"]),

    UniverseStock("WIPRO", "WIPRO.NS", "Wipro",
                  []),

    UniverseStock("ULTRACEMCO", "ULTRACEMCO.NS", "UltraTech Cement",
                  ["ultratech"]),

    UniverseStock("NESTLEIND", "NESTLEIND.NS", "Nestlé India",
                  ["nestle"]),

    UniverseStock("TATAMOTORS", "TATAMOTORS.NS", "Tata Motors",
                  ["tata motors"]),

    UniverseStock("JSWSTEEL", "JSWSTEEL.NS", "JSW Steel",
                  ["jsw"]),

    UniverseStock("POWERGRID", "POWERGRID.NS", "Power Grid",
                  []),

    UniverseStock("NTPC", "NTPC.NS", "NTPC",
                  []),

    UniverseStock("ONGC", "ONGC.NS", "ONGC",
                  []),

    UniverseStock("COALINDIA", "COALINDIA.NS", "Coal India",
                  []),

    UniverseStock("ADANIENT", "ADANIENT.NS", "Adani Enterprises",
                  ["adani"]),

    UniverseStock("ADANIPORTS", "ADANIPORTS.NS", "Adani Ports",
                  []),

    UniverseStock("M&M", "M&M.NS", "Mahindra & Mahindra",
                  ["mahindra", "mm"]),

    UniverseStock("HCLTECH", "HCLTECH.NS", "HCL Tech",
                  ["hcl"]),

    UniverseStock("BSOFT", "BSOFT.NS", "Birlasoft",
                  ["birlasoft"]),
]


DEFAULT_WATCHLIST = [
    "RELIANCE",
    "TCS",
    "INFY",
    "HDFCBANK"
]


# -----------------------------------
# LOOKUP BY SYMBOL
# -----------------------------------

by_symbol = {
    stock.symbol: stock
    for stock in UNIVERSE
}


# -----------------------------------
# NORMALIZE SYMBOL
# -----------------------------------

def normalize_symbol(raw: str) -> str:
    """
    Examples:
        'reliance'      -> 'RELIANCE'
        'RELIANCE.NS'   -> 'RELIANCE'
        ' tcs.ns '      -> 'TCS'
    """
    return raw.strip().upper().removesuffix(".NS")


# -----------------------------------
# GET STOCK
# -----------------------------------

def get_stock(symbol: str) -> Optional[UniverseStock]:
    """
    Find a stock by its symbol.
    """

    normalized = normalize_symbol(symbol)

    return by_symbol.get(normalized)


# -----------------------------------
# RESOLVE TICKER
# -----------------------------------

def resolve_ticker(raw: str) -> Optional[UniverseStock]:

    q = raw.strip()

    if not q:
        return None

    upper = normalize_symbol(q)

    # 1. Exact symbol match
    exact = by_symbol.get(upper)

    if exact:
        return exact

    # 2. Alias or company-name match
    q_lower = q.lower()

    for stock in UNIVERSE:

        if any(alias.lower() == q_lower for alias in stock.aliases):
            return stock

        if stock.name.lower() == q_lower:
            return stock

    # 3. Allow a valid custom ticker
    #
    # JS:
    # /^[A-Z0-9.&-]{1,12}$/
    if (
        1 <= len(upper) <= 12
        and all(
            c.isalnum() or c in ".&-"
            for c in upper
        )
    ):
        return UniverseStock(
            symbol=upper,
            yahoo=f"{upper}.NS",
            name=upper,
            aliases=[]
        )

    return None