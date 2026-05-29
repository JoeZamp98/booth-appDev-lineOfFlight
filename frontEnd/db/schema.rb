# This file is auto-generated from the current state of the database. Instead
# of editing this file, please use the migrations feature of Active Record to
# incrementally modify your database, and then regenerate this schema definition.
#
# This file is the source Rails uses to define your schema when running `bin/rails
# db:schema:load`. When creating a new database, `bin/rails db:schema:load` tends to
# be faster and is potentially less error prone than running all of your
# migrations from scratch. Old migrations may fail to apply correctly if those
# migrations use external dependencies or application code.
#
# It's strongly recommended that you check this file into your version control system.

ActiveRecord::Schema[8.1].define(version: 2026_05_29_025318) do
  create_table "trips", force: :cascade do |t|
    t.string "carrier", null: false
    t.datetime "created_at", null: false
    t.string "delay_class"
    t.integer "delay_min", default: 0
    t.string "dest", null: false
    t.string "flight", null: false
    t.date "flight_date", null: false
    t.string "origin", null: false
    t.float "predicted_prob"
    t.datetime "updated_at", null: false
    t.integer "user_id", null: false
    t.index ["user_id"], name: "index_trips_on_user_id"
  end

  create_table "users", force: :cascade do |t|
    t.datetime "created_at", null: false
    t.string "home_airport"
    t.string "initials", null: false
    t.string "name", null: false
    t.string "password_digest", null: false
    t.string "tier", default: "Member"
    t.datetime "updated_at", null: false
    t.string "username", null: false
    t.index ["username"], name: "index_users_on_username", unique: true
  end

  create_table "watchlist_items", force: :cascade do |t|
    t.string "carrier", null: false
    t.datetime "created_at", null: false
    t.float "delay_prob"
    t.string "dep_display"
    t.string "dest", null: false
    t.string "flight", null: false
    t.string "origin", null: false
    t.datetime "updated_at", null: false
    t.integer "user_id", null: false
    t.index ["user_id"], name: "index_watchlist_items_on_user_id"
  end

  add_foreign_key "trips", "users"
  add_foreign_key "watchlist_items", "users"
end
