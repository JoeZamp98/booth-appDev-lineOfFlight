class SessionsController < ApplicationController

    skip_before_action :require_login
    layout "login"   # ← add this
  
    def new
      redirect_to root_path if current_user
    end
  
    def create
      user = User.find_by(username: params[:username].to_s.downcase.strip)
  
      if user&.authenticate(params[:password])
        session[:user_id] = user.id
        redirect_to root_path
      else
        @error = "Invalid username or password"
        render :new, status: :unprocessable_entity
      end
    end
  
    def destroy
      session.delete(:user_id)
      redirect_to login_path
    end
  end