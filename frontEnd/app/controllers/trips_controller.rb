class TripsController < ApplicationController
    def index
        @trips = DummyData::RECENT_TRIPS
    end
end