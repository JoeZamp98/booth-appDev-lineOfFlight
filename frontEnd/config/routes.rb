Rails.application.routes.draw do
  get "up" => "rails/health#show", as: :rails_health_check

  root "predictions#new"

  get    "/login",  to: "sessions#new",     as: :login
  post   "/login",  to: "sessions#create"
  delete "/logout", to: "sessions#destroy", as: :logout

  get "/predict",      to: "predictions#new",  as: :new_prediction # this is the search page that allows someone to query a flight
  get "/predict/:id",  to: "predictions#show", as: :prediction #This is the full prediction detail page

  get "/trips",        to: "trips#index",      as: :trips #This is a log of all of the users past flights (hardcoded for now as a demo)
  get "/flights",      to: "flights#index",    as: :flights #This is the flight board page that shows the upcoming 72 hour schedule

end
