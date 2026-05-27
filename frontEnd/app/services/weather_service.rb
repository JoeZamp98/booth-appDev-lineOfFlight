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
    
      key = api_key
      return fallback(airport) if key.nil? || key.empty?
    
      url = "/forecast/#{key}/#{coords[:lat]},#{coords[:lon]}"
      Rails.logger.info "Calling Pirate Weather: #{self.base_uri}#{url}"
    
      begin
        response = get(url, query: { units: "us", exclude: "minutely,hourly,daily,alerts" })
        Rails.logger.info "Pirate Weather response: #{response.code}"
    
        if response.success?
          parse(response.parsed_response, airport)
        else
          Rails.logger.error "Pirate Weather failed: #{response.code} #{response.body}"
          fallback(airport)
        end
    
      rescue => e
        Rails.logger.error "WeatherService exception: #{e.class} #{e.message}"
        fallback(airport)
      end
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