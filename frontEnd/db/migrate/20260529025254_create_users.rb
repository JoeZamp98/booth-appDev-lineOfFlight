class CreateUsers < ActiveRecord::Migration[8.1]
  def change
    create_table :users do |t|
      t.string  :username,        null: false
      t.string  :name,            null: false
      t.string  :initials,        null: false
      t.string  :password_digest, null: false
      t.string  :tier,            default: "Member"
      t.string  :home_airport
      t.timestamps
    end
    add_index :users, :username, unique: true
  end
end