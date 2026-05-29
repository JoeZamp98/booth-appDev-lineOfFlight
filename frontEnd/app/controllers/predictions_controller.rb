class PredictionsController < ApplicationController

  def new
    @origin       = params[:origin]&.upcase || "SFO"
    @dest         = params[:dest]&.upcase   || "JFK"
    @date         = params[:date]           || Date.today.to_s
    @recent_trips = current_user.trips.recent
    @weather      = WeatherService.current(@origin)
  
    api_flights = PredictionService.search_flights(
      origin: @origin,
      dest:   @dest,
      date:   @date
    )
    @flights = api_flights&.any? ? api_flights : DummyData.flights_for_route(@origin, @dest)
  end

  def show
    carrier, number = params[:id].split("-")
    dep_hour = params[:dep_hour]&.to_i || 12
  
    # Fetch weather for both airports
    origin     = params[:origin] || "SFO"
    dest       = params[:dest]   || "JFK"
    origin_wx  = WeatherService.current(origin)
    dest_wx    = WeatherService.current(dest)
  
    api_prediction = PredictionService.predict(
      carrier:        carrier,
      flight_number:  number,
      origin:         origin,
      dest:           dest,
      date:           Date.today.to_s,
      dep_hour:       dep_hour,
      origin_weather: origin_wx,
      dest_weather:   dest_wx
    )
  
    @source = api_prediction ? :api : :dummy
    @prediction =
      if api_prediction
        # The model endpoint omits itinerary fields (times, aircraft, seat);
        # backfill them from the known schedule so the page renders complete.
        DummyData.flight_details(carrier, number, origin, dest).merge(api_prediction)
      else
        DummyData.prediction_for(carrier, number)
      end
  end
end