# Clear existing
WatchlistItem.destroy_all
Trip.destroy_all
User.destroy_all

# ── Daniel ──────────────────────────────────────────────────────
daniel = User.create!(
  username:  "daniel",
  password:  "fly123",
  name:      "Daniel Park",
  initials:  "DP",
  tier:       "Diamond Medallion",
  home_airport: "JFK"
)

[
  { flight: "DL 412",  carrier: "DL", origin: "BOS", dest: "SFO",
    flight_date: "2026-04-12", delay_min: 8   },
  { flight: "AS 321",  carrier: "AS", origin: "SFO", dest: "SEA",
    flight_date: "2026-03-28", delay_min: 2   },
  { flight: "UA 1834", carrier: "UA", origin: "SFO", dest: "ORD",
    flight_date: "2026-03-03", delay_min: 47  },
  { flight: "DL 40",   carrier: "DL", origin: "LHR", dest: "SFO",
    flight_date: "2026-02-19", delay_min: -12 },
  { flight: "B6 421",  carrier: "B6", origin: "JFK", dest: "LAX",
    flight_date: "2026-01-30", delay_min: 0   },
].each { |t| daniel.trips.create!(t) }

daniel.watchlist_items.create!(
  flight: "DL 1221", carrier: "DL",
  origin: "SFO",     dest: "JFK",
  dep_display: "May 30 · 17:10", delay_prob: 0.64
)

# ── Sarah ────────────────────────────────────────────────────────
sarah = User.create!(
  username:  "sarah",
  password:  "fly123",
  name:      "Sarah Chen",
  initials:  "SC",
  tier:       "Platinum Pro",
  home_airport: "ORD"
)

[
  { flight: "UA 2282", carrier: "UA", origin: "ORD", dest: "LAX",
    flight_date: "2026-05-01", delay_min: 22 },
  { flight: "AA 1183", carrier: "AA", origin: "LAX", dest: "ORD",
    flight_date: "2026-04-15", delay_min: 0  },
  { flight: "AA 300",  carrier: "AA", origin: "ORD", dest: "JFK",
    flight_date: "2026-04-02", delay_min: 11 },
  { flight: "B6 914",  carrier: "B6", origin: "JFK", dest: "BOS",
    flight_date: "2026-03-20", delay_min: -5 },
].each { |t| sarah.trips.create!(t) }

sarah.watchlist_items.create!(
  flight: "UA 2282", carrier: "UA",
  origin: "ORD",     dest: "JFK",
  dep_display: "May 31 · 10:30", delay_prob: 0.19
)

# ── Marcus ───────────────────────────────────────────────────────
marcus = User.create!(
  username:  "marcus",
  password:  "fly123",
  name:      "Marcus Webb",
  initials:  "MW",
  tier:       "Gold",
  home_airport: "ATL"
)

[
  { flight: "DL 1055", carrier: "DL", origin: "ATL", dest: "DEN",
    flight_date: "2026-05-10", delay_min: 5  },
  { flight: "DL 1056", carrier: "DL", origin: "DEN", dest: "ATL",
    flight_date: "2026-04-28", delay_min: 0  },
  { flight: "AA 577",  carrier: "AA", origin: "ATL", dest: "LAX",
    flight_date: "2026-04-10", delay_min: 33 },
].each { |t| marcus.trips.create!(t) }

puts "Seeded #{User.count} users, #{Trip.count} trips, #{WatchlistItem.count} watchlist items"