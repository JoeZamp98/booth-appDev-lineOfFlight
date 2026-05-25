Rails.application.routes.draw do
  get "up" => "rails/health#show", as: :rails_health_check

  root "predictions#new"

  get "/predict",      to: "predictions#new",  as: :new_prediction
  get "/predict/:id",  to: "predictions#show", as: :prediction

  get "/trips",        to: "trips#index",      as: :trips
  get "/watchlist",    to: "watchlist#index",  as: :watchlist
  get "/patterns",     to: "patterns#index",   as: :patterns

end
