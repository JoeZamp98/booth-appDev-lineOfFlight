class PredictionsController < ApplicationController

  def new
    @origin       = params[:origin]&.upcase || "SFO"
    @dest         = params[:dest]&.upcase   || "JFK"
    @date         = params[:date]           || Date.today.to_s
    @recent_trips = current_user.trips.recent
    @weather      = WeatherService.current(@origin)
    @route_stats  = PredictionService.route_stats(origin: @origin, dest: @dest)
  
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
    # Carry the flight's real date/distance from the schedule so the live
    # prediction reproduces the cached schedule.json value — the only
    # intended difference is live weather.
    date     = params[:date].presence     || Date.today.to_s
    distance = params[:distance].presence
  
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
      date:           date,
      dep_hour:       dep_hour,
      distance:       distance,
      origin_weather: origin_wx,
      dest_weather:   dest_wx
    )
  
    @source = api_prediction ? :api : :dummy
    @prediction =
      if api_prediction
        # The model endpoint returns only delay fields. Use the real departure
        # time carried over from the schedule; arrival/aircraft/seat aren't in
        # the live feed, so leave them blank rather than inventing them.
        { dep_time: params[:dep_disp].presence }.compact.merge(api_prediction)
      else
        DummyData.prediction_for(carrier, number)
      end
  end
end