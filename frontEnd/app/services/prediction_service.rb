class PredictionService
  include HTTParty

  def self.base_uri
    ENV.fetch("FASTAPI_URL", "http://localhost:8000")
  end

  def self.predict(
    carrier:,
    flight_number:,
    origin:,
    dest:,
    date:
  )

    response = post("/predictions/predict",
    headers: { "Content-Type" => "application/json" },
    body: {
      carrier: carrier,
      flight_number: flight_number,
      origin: origin,
      dest: dest,
      date: date
    }.to_json
    )

    if response.success?
      return response.parsed_response.deep_symbolize_keys
    else
      Rails.logger.error("PredictionService: Error predicting flight: #{response.code} #{response.message}")
      return nil

    end

  rescue HTTParty::Error, SocketError => e
    Rails.logger.error("FastAPI service was not reachable: #{e.message}")
    nil
  end

  def self.flights_for_route(origin:, dest:)
    response = HTTParty.get(
      "#{base_url}/predictions/flights",
      query: { origin: origin, dest: dest }
    )
    if response.success?
      response.parsed_response.map(&:deep_symbolize_keys)
    else
      nil
    end
  rescue => e
    Rails.logger.error "PredictionService unreachable: #{e.message}"
    nil
  end
  

end