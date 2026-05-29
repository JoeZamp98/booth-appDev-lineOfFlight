class CreateWatchlistItems < ActiveRecord::Migration[8.1]
  def change
    create_table :watchlist_items do |t|
      t.references :user,   null: false, foreign_key: true
      t.string  :flight,    null: false
      t.string  :carrier,   null: false
      t.string  :origin,    null: false
      t.string  :dest,      null: false
      t.string  :dep_display
      t.float   :delay_prob
      t.timestamps
    end
  end
end