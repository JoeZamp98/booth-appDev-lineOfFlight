class CreateTrips < ActiveRecord::Migration[8.1]
  def change
    create_table :trips do |t|
      t.references :user,    null: false, foreign_key: true
      t.string  :flight,     null: false
      t.string  :carrier,    null: false
      t.string  :origin,     null: false
      t.string  :dest,       null: false
      t.date    :flight_date, null: false
      t.integer :delay_min,  default: 0
      t.string  :delay_class # "early" | "late" | "ontime"
      t.float   :predicted_prob
      t.timestamps
    end
  end
end