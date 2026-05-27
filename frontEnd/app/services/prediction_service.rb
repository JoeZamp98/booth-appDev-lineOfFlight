class PredictionService
  def self.base_url
    ENV.fetch("FASTAPI_URL", "http://localhost:8000")
  end

  def self.predict(carrier:, flight_number:, origin:, dest:, date:,
    dep_hour: nil, origin_weather: nil, dest_weather: nil)

    response = HTTParty.post(
    "#{self.base_url}/predictions/predict",
    headers: { "Content-Type" => "application/json" },
    body: {
    carrier:        carrier,
    flight_number:  flight_number,
    origin:         origin,
    dest:           dest,
    date:           date,
    dep_hour:       dep_hour,
    origin_weather: origin_weather ? {
    precip_prob:  origin_weather[:precip],
    wind_speed:   origin_weather[:wind].to_f,
    wind_gust:    origin_weather[:wind].to_f,
    visibility:   origin_weather[:vis].to_f,
    cloud_cover:  origin_weather[:cloud],
    temperature:  origin_weather[:temp_f]
    } : nil,
    dest_weather: dest_weather ? {
    precip_prob:  dest_weather[:precip],
    wind_speed:   dest_weather[:wind].to_f,
    wind_gust:    dest_weather[:wind].to_f,
    visibility:   dest_weather[:vis].to_f,
    cloud_cover:  dest_weather[:cloud],
    temperature:  dest_weather[:temp_f]
    } : nil
    }.to_json,
    timeout: 10
    )

    if response.success?
    response.parsed_response.deep_symbolize_keys
    else
    nil
    end

    rescue => e
    Rails.logger.error "PredictionService error: #{e.message}"
    nil
  end

  def self.flights_for_route(origin:, dest:)
    response = HTTParty.get(
      "#{self.base_url}/predictions/flights",
      query: { origin: origin, dest: dest },
      timeout: 10
    )

    if response.success?
      response.parsed_response.map(&:deep_symbolize_keys)
    else
      nil
    end

  rescue => e
    Rails.logger.error "PredictionService error: #{e.message}"
    nil
  end
end