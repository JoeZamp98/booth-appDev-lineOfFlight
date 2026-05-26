class PredictionsController < ApplicationController
  def new
    @origin       = params[:origin]&.upcase || "SFO"
    @dest         = params[:dest]&.upcase   || "JFK"
    @flights      = DummyData.flights_for_route(@origin, @dest)
    @weather      = { temp_f: 62, condition: "Scattered clouds", wind: "12 kt", vis: "10 mi" }
    @recent_trips = DummyData::RECENT_TRIPS

    #Attempts to retrieve data from FastAPI service first, falls back to dummy data otherwise
    api_flights = PredictionService.flights_for_route(origin: @origin, dest: @dest)
    @flights = api_flights || DummyData.flights_for_route(@origin, @dest)
    @source = api_flights ? "FastAPI" : "Dummy Data"
  end

  def show
    carrier, number = params[:id].split("-")

    api_prediction = PredictionService.predict(
      carrier: carrier,
      flight_number: number,
      origin: params[:origin] || "SFO",
      dest: params[:dest] || "JFK",
      date: Date.today.to_s
    )

    @prediction = api_prediction || DummyData.prediction_for(carrier, number)
    @source = api_prediction ? :api : :dummy

  end
end