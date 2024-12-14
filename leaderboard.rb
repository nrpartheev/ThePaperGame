require 'mongo'
require 'json'
require 'http'
require 'csv'
require 'dotenv/load'


MONGO_DB_URL = ""
USERS_COLLECTION = 'users'
CSV_FILE = ''


client = Mongo::Client.new(MONGO_DB_URL)
db = client.use('PaperProfit')
$users_collection = db[USERS_COLLECTION]

symbols = CSV.read(CSV_FILE, headers: true).map { |row| row['SYMBOL'] }.compact


$price_cache = {}

def fetch_live_price(stock)
  return $price_cache[stock] if $price_cache.key?(stock)

  response = HTTP.get("https://groww.in/v1/api/stocks_data/v1/tr_live_prices/exchange/NSE/segment/CASH/#{stock}/latest")
  if response.status.success?
    price = JSON.parse(response.body)['ltp']
    $price_cache[stock] = price
    price
  else
    raise "Failed to fetch live price for #{stock}"
  end
end

def leader_board
  begin
    leaderboard = []

    $users_collection.find.each do |user|
      user_name = user['name']
      wallet_amount = user['wallet_amount'] || 0
      stocks = user['stocks'] || []

      stock_worth = stocks.sum do |stock|
        stock_name = stock['stock']
        quantity = stock['quantity']
        begin
          live_price = fetch_live_price(stock_name)
          quantity * live_price
        rescue => e
          puts "Error fetching price for #{stock_name}: #{e.message}"
          0
        end
      end

      total_worth = wallet_amount + stock_worth

      leaderboard << {
        name: user_name,
        cash: wallet_amount,
        stock_worth: stock_worth,
        total_worth: total_worth
      }
    end

    leaderboard.sort_by! { |user| -user[:total_worth] }

    puts "| Rank | Name         | Cash Remaining | Stock Worth | Total Worth |"
    puts "|------|--------------|----------------|-------------|-------------|"
    leaderboard.each_with_index do |user_data, index|
      puts "| %-4d | u/%-12s | %-14.2f | %-11.2f | %-11.2f |" % [
        index + 1,
        user_data[:name],
        user_data[:cash],
        user_data[:stock_worth],
        user_data[:total_worth]
      ]
    end
  rescue => e
    puts "Error generating leaderboard: #{e.message}"
  end
end

leaderboard
