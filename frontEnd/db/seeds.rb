# Safe to re-run — finds or creates each user
daniel = User.find_or_initialize_by(username: "daniel")
daniel.update!(
  password:     "fly123",
  name:         "Daniel Park",
  initials:     "DP",
  tier:         "Diamond Medallion",
  home_airport: "JFK"
)

# Only seed trips if none exist for this user
if daniel.trips.empty?
  [
    { flight: "DL 412",  carrier: "DL", origin: "BOS", dest: "SFO",
      flight_date: "2026-04-12", delay_min: 8,   predicted_prob: 0.34 },
    { flight: "AS 321",  carrier: "AS", origin: "SFO", dest: "SEA",
      flight_date: "2026-03-28", delay_min: 2,   predicted_prob: 0.28 },
    { flight: "UA 1834", carrier: "UA", origin: "SFO", dest: "ORD",
      flight_date: "2026-03-03", delay_min: 47,  predicted_prob: 0.55 },
    { flight: "DL 40",   carrier: "DL", origin: "LHR", dest: "SFO",
      flight_date: "2026-02-19", delay_min: -12, predicted_prob: 0.21 },
    { flight: "B6 421",  carrier: "B6", origin: "JFK", dest: "LAX",
      flight_date: "2026-01-30", delay_min: 0,   predicted_prob: 0.30 },
  ].each { |t| daniel.trips.create!(t) }

  daniel.watchlist_items.find_or_create_by!(
    flight: "DL 1221", carrier: "DL",
    origin: "SFO",     dest: "JFK"
  ) do |w|
    w.dep_display = "May 30 · 17:10"
    w.delay_prob  = 0.64
  end
end

sarah = User.find_or_initialize_by(username: "sarah")
sarah.update!(
  password:     "fly123",
  name:         "Sarah Chen",
  initials:     "SC",
  tier:         "Platinum Pro",
  home_airport: "ORD"
)

if sarah.trips.empty?
  [
    { flight: "UA 2282", carrier: "UA", origin: "ORD", dest: "LAX",
      flight_date: "2026-05-01", delay_min: 22, predicted_prob: 0.42 },
    { flight: "AA 1183", carrier: "AA", origin: "LAX", dest: "ORD",
      flight_date: "2026-04-15", delay_min: 0,  predicted_prob: 0.26 },
    { flight: "AA 300",  carrier: "AA", origin: "ORD", dest: "JFK",
      flight_date: "2026-04-02", delay_min: 11, predicted_prob: 0.40 },
    { flight: "B6 914",  carrier: "B6", origin: "JFK", dest: "BOS",
      flight_date: "2026-03-20", delay_min: -5, predicted_prob: 0.19 },
  ].each { |t| sarah.trips.create!(t) }

  sarah.watchlist_items.find_or_create_by!(
    flight: "UA 2282", carrier: "UA",
    origin: "ORD",     dest: "JFK"
  ) do |w|
    w.dep_display = "May 31 · 10:30"
    w.delay_prob  = 0.19
  end
end

marcus = User.find_or_initialize_by(username: "marcus")
marcus.update!(
  password:     "fly123",
  name:         "Marcus Webb",
  initials:     "MW",
  tier:         "Gold",
  home_airport: "ATL"
)

if marcus.trips.empty?
  [
    { flight: "DL 1055", carrier: "DL", origin: "ATL", dest: "DEN",
      flight_date: "2026-05-10", delay_min: 5,  predicted_prob: 0.30 },
    { flight: "DL 1056", carrier: "DL", origin: "DEN", dest: "ATL",
      flight_date: "2026-04-28", delay_min: 0,  predicted_prob: 0.27 },
    { flight: "AA 577",  carrier: "AA", origin: "ATL", dest: "LAX",
      flight_date: "2026-04-10", delay_min: 33, predicted_prob: 0.49 },
  ].each { |t| marcus.trips.create!(t) }
end

puts "Done — #{User.count} users, #{Trip.count} trips, #{WatchlistItem.count} watchlist items"