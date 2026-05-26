class WeatherService
    include HTTParty
    
    def self.base_uri
      ENV.fetch("PIRATE_WEATHER_URL", "https://api.pirateweather.net")
    end

    def self.api_key
      Rails.application.credentials.dig(:pirate_weather, :api_key) ||
        ENV["PIRATE_WEATHER_API_KEY"]
    end
  
    AIRPORTS = {
      "SFO" => { lat: 37.6213, lon: -122.379 },
      "JFK" => { lat: 40.6413, lon: -73.7781 },
      "ORD" => { lat: 41.9742, lon: -87.9073 },
      "LAX" => { lat: 33.9425, lon: -118.408 },
      "BOS" => { lat: 42.3656, lon: -71.0096 },
    }.freeze
  
    def self.current(airport)
      coords = AIRPORTS[airport]
      return fallback(airport) unless coords
  
      api_key  = Rails.application.credentials.pirate_weather[:api_key]
      lat, lon = coords[:lat], coords[:lon]
  
      response = get(
        "/forecast/#{api_key}/#{lat},#{lon}",
        query: { units: "us", exclude: "minutely,hourly,daily,alerts" }
      )
  
      if response.success?
        parse(response.parsed_response, airport)
      else
        fallback(airport)
      end
  
    rescue HTTParty::Error, SocketError => e
      Rails.logger.error "WeatherService error: #{e.message}"
      fallback(airport)
    end
  
    private
  
    def self.parse(data, airport)
      current = data["currently"] || {}
      {
        airport:   airport,
        temp_f:    current["temperature"]&.round,
        condition: current["summary"] || "Unknown",
        wind:      "#{current["windSpeed"]&.round} kt",
        vis:       "#{[current["visibility"]&.round, 10].compact.min} mi",
        precip:    current["precipProbability"] || 0,
        cloud:     current["cloudCover"] || 0,
        source:    :api
      }
    end
  
    def self.fallback(airport)
      {
        airport:   airport,
        temp_f:    62,
        condition: "Scattered clouds",
        wind:      "12 kt",
        vis:       "10 mi",
        precip:    0,
        cloud:     0.3,
        source:    :dummy
      }
    end
  end