class FlightsController < ApplicationController
    def index
      @meta    = FlightBoardService.meta
      @origin  = params[:origin]&.upcase
      @dest    = params[:dest]&.upcase
      @carrier = params[:carrier]&.upcase
      @risk    = params[:risk]
  
      result   = FlightBoardService.board(
        origin:  @origin,
        dest:    @dest,
        carrier: @carrier,
        risk:    @risk
      )
  
      @flights      = result[:flights] || []
      @flight_count = result[:count]   || 0
    end
  end