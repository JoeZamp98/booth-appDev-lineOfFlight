class PredictionService
  def self.base_url
    ENV.fetch("FASTAPI_URL", "http://localhost:8000")
  end

  def self.predict(carrier:, flight_number:, origin:, dest:, date:)
    response = HTTParty.post(
      "#{self.base_url}/predictions/predict",
      headers: { "Content-Type" => "application/json" },
      body: {
        carrier:       carrier,
        flight_number: flight_number,
        origin:        origin,
        dest:          dest,
        date:          date
      }.to_json,
      timeout: 10
    )

    if response.success?
      response.parsed_response.deep_symbolize_keys
    else
      Rails.logger.error "FastAPI error: #{response.code}"
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