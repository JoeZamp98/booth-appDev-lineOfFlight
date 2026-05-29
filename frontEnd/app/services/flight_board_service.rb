class FlightBoardService
    def self.base_url
      ENV.fetch("FASTAPI_URL", "http://localhost:8000")
    end
  
    def self.board(origin: nil, dest: nil, carrier: nil, risk: nil)
      query = { hours_ahead: 72 }
      query[:origin]  = origin  if origin
      query[:dest]    = dest    if dest
      query[:carrier] = carrier if carrier
      query[:risk]    = risk    if risk
  
      response = HTTParty.get(
        "#{self.base_url}/flights/board",
        query:   query,
        timeout: 10
      )
  
      if response.success?
        parsed = response.parsed_response
        {
          flights: parsed["flights"].map(&:deep_symbolize_keys),
          count:   parsed["count"]
        }
      else
        { flights: [], count: 0 }
      end
  
    rescue => e
      Rails.logger.error "FlightBoardService error: #{e.message}"
      { flights: [], count: 0 }
    end
  
    def self.meta
      response = HTTParty.get(
        "#{self.base_url}/flights/meta",
        timeout: 10
      )
      response.success? ? response.parsed_response.deep_symbolize_keys : {}
    rescue => e
      {}
    end
  end