module DummyData

    AIRPORTS = {
      "SFO" => { name: "San Francisco Intl.",   lat: 37.6213, lon: -122.379 },
      "JFK" => { name: "John F. Kennedy Intl.", lat: 40.6413, lon: -73.7781 },
      "ORD" => { name: "Chicago O'Hare Intl.",  lat: 41.9742, lon: -87.9073 },
      "LAX" => { name: "Los Angeles Intl.",     lat: 33.9425, lon: -118.408 },
      "BOS" => { name: "Logan International",   lat: 42.3656, lon: -71.0096 },
    }.freeze
  
    AIRLINES = {
      "DL" => "Delta Air Lines",
      "UA" => "United Airlines",
      "AA" => "American Airlines",
      "B6" => "JetBlue Airways",
    }.freeze
  
    ROUTE_FLIGHTS = {
      "SFO-JFK" => [
        { flight: "UA 1549", carrier: "UA", dep: "07:00", arr: "15:28", aircraft: "B739", delay_prob: 0.23 },
        { flight: "B6 624",  carrier: "B6", dep: "10:25", arr: "18:48", aircraft: "A321", delay_prob: 0.18 },
        { flight: "AA 24",   carrier: "AA", dep: "13:45", arr: "22:08", aircraft: "77W",  delay_prob: 0.31 },
        { flight: "DL 1221", carrier: "DL", dep: "17:10", arr: "01:42", aircraft: "A339", delay_prob: 0.64, seat: "2A" },
      ],
    }.freeze
  
    PREDICTIONS = {
      "DL-1221" => {
        flight:       "DL 1221",
        carrier:      "DL",
        origin:       "SFO",
        dest:         "JFK",
        dep_time:     "17:10",
        arr_time:     "01:42",
        arr_plus_day: true,
        aircraft:     "Airbus A330-900neo",
        seat:         "2A",
        status:       "On time",
        delay_prob:   0.64,
        likely_delay: 42,
        drivers: [
          { label: "JFK arrival flow",      delta: "+38%", severity: :high,
            detail: "ZNY restricting east arrivals through 22:00 EDT." },
          { label: "SFO marine layer",      delta: "+22%", severity: :medium,
            detail: "200ft ceiling expected 19:30 PDT." },
          { label: "Inbound aircraft N828NW", delta: "+28%", severity: :medium,
            detail: "Currently DTW→SFO, projected wheels-down 16:42 — 12 min behind block." },
          { label: "Historical pattern",    delta: "+4%",  severity: :positive,
            detail: "DL 1221 on-time 71% of last 30 evenings." },
        ],
      },
    }.freeze
  
    RECENT_TRIPS = [
      { date: "Apr 12", origin: "BOS", dest: "SFO", delay_min: +8,  delay_class: "late"  },
      { date: "Mar 28", origin: "SFO", dest: "SEA", delay_min: +2,  delay_class: "late"  },
      { date: "Mar 03", origin: "SFO", dest: "ORD", delay_min: +47, delay_class: "late"  },
      { date: "Feb 19", origin: "LHR", dest: "SFO", delay_min: -12, delay_class: "early" },
    ].freeze
  
    def self.flights_for_route(origin, dest)
      ROUTE_FLIGHTS["#{origin}-#{dest}"] || ROUTE_FLIGHTS["SFO-JFK"]
    end
  
    def self.prediction_for(carrier, number)
      PREDICTIONS["#{carrier}-#{number}"] || PREDICTIONS["DL-1221"]
    end
  end