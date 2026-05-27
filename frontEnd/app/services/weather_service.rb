class WeatherService
  def self.current(airport)
    Rails.logger.info "Fetching weather for #{airport}..."
    base_url = ENV.fetch("FASTAPI_URL", "http://localhost:8000")

    response = HTTParty.get(
      "#{base_url}/weather/#{airport}",
      timeout: 10
    )

    if response.success?
      result = response.parsed_response.deep_symbolize_keys
      Rails.logger.info "Weather source: #{result[:source]}"
      result
    else
      Rails.logger.error "Weather API error: #{response.code}"
      fallback(airport)
    end

  rescue => e
    Rails.logger.error "WeatherService error: #{e.message}"
    fallback(airport)
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
      source:    "dummy"
    }
  end
end