class TripsController < ApplicationController
  def index
    @trips = current_user.trips.order(flight_date: :desc)
  end
end