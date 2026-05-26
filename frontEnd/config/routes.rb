Rails.application.routes.draw do
  get "up" => "rails/health#show", as: :rails_health_check

  root "predictions#new"

  get "/predict",      to: "predictions#new",  as: :new_prediction # this is the search page that allows someone to query a flight
  get "/predict/:id",  to: "predictions#show", as: :prediction #This is the full prediction detail page

  get "/trips",        to: "trips#index",      as: :trips #This is a log of all of the users past flights (hardcoded for now as a demo)
  get "/watchlist",    to: "watchlist#index",  as: :watchlist #List of all the flights the user wants to monitor (hardcoded for now)
  #get "/patterns",     to: "patterns#index",   as: :patterns #This would serve as a historical pattern explorer; not implemented just yet but considering

end
