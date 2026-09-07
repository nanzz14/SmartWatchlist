export type UniverseStock = {
  symbol: string;
  yahoo: string;
  name: string;
  aliases: string[];
};

export const UNIVERSE: UniverseStock[] = [
  { symbol: "RELIANCE", yahoo: "RELIANCE.NS", name: "Reliance Industries", aliases: ["ril", "reliance industries"] },
  { symbol: "TCS", yahoo: "TCS.NS", name: "Tata Consultancy Services", aliases: ["tata consultancy"] },
  { symbol: "INFY", yahoo: "INFY.NS", name: "Infosys", aliases: ["infosys"] },
  { symbol: "HDFCBANK", yahoo: "HDFCBANK.NS", name: "HDFC Bank", aliases: ["hdfc", "hdfc bank"] },
  { symbol: "ICICIBANK", yahoo: "ICICIBANK.NS", name: "ICICI Bank", aliases: ["icici"] },
  { symbol: "SBIN", yahoo: "SBIN.NS", name: "State Bank of India", aliases: ["sbi"] },
  { symbol: "BHARTIARTL", yahoo: "BHARTIARTL.NS", name: "Bharti Airtel", aliases: ["airtel", "bharti"] },
  { symbol: "ITC", yahoo: "ITC.NS", name: "ITC", aliases: ["itc limited"] },
  { symbol: "LT", yahoo: "LT.NS", name: "Larsen & Toubro", aliases: ["l&t", "larsen"] },
  { symbol: "HINDUNILVR", yahoo: "HINDUNILVR.NS", name: "Hindustan Unilever", aliases: ["hul"] },
  { symbol: "KOTAKBANK", yahoo: "KOTAKBANK.NS", name: "Kotak Mahindra Bank", aliases: ["kotak"] },
  { symbol: "AXISBANK", yahoo: "AXISBANK.NS", name: "Axis Bank", aliases: ["axis"] },
  { symbol: "BAJFINANCE", yahoo: "BAJFINANCE.NS", name: "Bajaj Finance", aliases: ["bajaj finance"] },
  { symbol: "ASIANPAINT", yahoo: "ASIANPAINT.NS", name: "Asian Paints", aliases: ["asian paints"] },
  { symbol: "MARUTI", yahoo: "MARUTI.NS", name: "Maruti Suzuki", aliases: ["maruti suzuki"] },
  { symbol: "TITAN", yahoo: "TITAN.NS", name: "Titan", aliases: [] },
  { symbol: "SUNPHARMA", yahoo: "SUNPHARMA.NS", name: "Sun Pharma", aliases: ["sun pharma"] },
  { symbol: "WIPRO", yahoo: "WIPRO.NS", name: "Wipro", aliases: [] },
  { symbol: "ULTRACEMCO", yahoo: "ULTRACEMCO.NS", name: "UltraTech Cement", aliases: ["ultratech"] },
  { symbol: "NESTLEIND", yahoo: "NESTLEIND.NS", name: "Nestlé India", aliases: ["nestle"] },
  { symbol: "TATAMOTORS", yahoo: "TATAMOTORS.NS", name: "Tata Motors", aliases: ["tata motors"] },
  { symbol: "JSWSTEEL", yahoo: "JSWSTEEL.NS", name: "JSW Steel", aliases: ["jsw"] },
  { symbol: "POWERGRID", yahoo: "POWERGRID.NS", name: "Power Grid", aliases: [] },
  { symbol: "NTPC", yahoo: "NTPC.NS", name: "NTPC", aliases: [] },
  { symbol: "ONGC", yahoo: "ONGC.NS", name: "ONGC", aliases: [] },
  { symbol: "COALINDIA", yahoo: "COALINDIA.NS", name: "Coal India", aliases: [] },
  { symbol: "ADANIENT", yahoo: "ADANIENT.NS", name: "Adani Enterprises", aliases: ["adani"] },
  { symbol: "ADANIPORTS", yahoo: "ADANIPORTS.NS", name: "Adani Ports", aliases: [] },
  { symbol: "M&M", yahoo: "M&M.NS", name: "Mahindra & Mahindra", aliases: ["mahindra", "mm"] },
  { symbol: "HCLTECH", yahoo: "HCLTECH.NS", name: "HCL Tech", aliases: ["hcl"] },
  { symbol: "BSOFT", yahoo: "BSOFT.NS", name: "Birlasoft", aliases: ["birlasoft"] },
];

export const DEFAULT_WATCHLIST = ["RELIANCE", "TCS", "INFY", "HDFCBANK"];

const bySymbol = new Map(UNIVERSE.map((s) => [s.symbol, s]));

export function getStock(symbol: string) {
  return bySymbol.get(normalizeSymbol(symbol));
}

export function normalizeSymbol(raw: string) {
  return raw.trim().toUpperCase().replace(/\.NS$/i, "");
}

export function resolveTicker(raw: string): UniverseStock | null {
  const q = raw.trim();
  if (!q) return null;
  const upper = normalizeSymbol(q);
  const exact = bySymbol.get(upper);
  if (exact) return exact;
  const alias = UNIVERSE.find(
    (s) =>
      s.aliases.some((a) => a.toUpperCase() === q.toUpperCase()) ||
      s.name.toUpperCase() === q.toUpperCase(),
  );
  if (alias) return alias;
  if (/^[A-Z0-9.&-]{1,12}$/.test(upper)) {
    return {
      symbol: upper,
      yahoo: `${upper}.NS`,
      name: upper,
      aliases: [],
    };
  }
  return null;
}

export function searchUniverse(query: string, limit = 6) {
  const q = query.trim().toLowerCase();
  if (!q) return UNIVERSE.slice(0, limit);
  const scored = UNIVERSE.map((s) => {
    const hay = [s.symbol, s.name, ...s.aliases].join(" ").toLowerCase();
    let score = 0;
    if (s.symbol.toLowerCase() === q) score = 100;
    else if (s.symbol.toLowerCase().startsWith(q)) score = 80;
    else if (s.aliases.some((a) => a.toLowerCase() === q)) score = 75;
    else if (hay.includes(q)) score = 40;
    return { s, score };
  })
    .filter((x) => x.score > 0)
    .sort((a, b) => b.score - a.score);
  return scored.slice(0, limit).map((x) => x.s);
}
