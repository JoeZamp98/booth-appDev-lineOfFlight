class Trip < ApplicationRecord
    belongs_to :user
  
    scope :recent, -> { order(flight_date: :desc).limit(10) }
  
    def delay_class
      return "early"  if delay_min < 0
      return "ontime" if delay_min == 0
      "late"
    end
  
    def formatted_date
      flight_date.strftime("%b %-d")
    end
  end