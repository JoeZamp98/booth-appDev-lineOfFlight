class User < ApplicationRecord
    has_secure_password
    has_many :trips,           dependent: :destroy
    has_many :watchlist_items, dependent: :destroy
  
    validates :username, presence: true, uniqueness: { case_sensitive: false }
    validates :name,     presence: true
  
    before_save { self.username = username.downcase }
end