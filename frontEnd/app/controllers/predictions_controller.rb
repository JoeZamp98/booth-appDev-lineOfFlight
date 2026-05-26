class PredictionsController < ApplicationController
    def new
      @origin       = params[:origin]&.upcase || "SFO"
      @dest         = params[:dest]&.upcase   || "JFK"
      @flights      = DummyData.flights_for_route(@origin, @dest)
      @weather      = { temp_f: 62, condition: "Scattered clouds", wind: "12 kt", vis: "10 mi" }
      @recent_trips = DummyData::RECENT_TRIPS
    end
  
    def show
      carrier, number = params[:id].split("-")
      @prediction     = DummyData.prediction_for(carrier, number)
    end
  end