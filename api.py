from flask import Flask, jsonify, request
from datetime import datetime
from scripts import get_bet_opportunities


app = Flask(__name__)

# Simulating a storage for bet opportunities
bet_opportunities = []

# Endpoint to refresh the bet opportunities
@app.route('/refresh_bet_opportunities', methods=['POST'])
def refresh_bet_opportunities():
    return jsonify({"message": "Bet opportunities refreshed successfully", "total_opportunities": len(bet_opportunities)}), 201


# Endpoint to get the list of bet opportunities
@app.route('/bet_opportunities', methods=['GET'])
def bet_opportunities():
    page_index = int(request.args.get('page_index'))
    results_per_page = int(request.args.get('results_per_page'))
    data = [x.to_json() for x in get_bet_opportunities()]

    new_index = page_index + results_per_page
    to_return = data[page_index : new_index]
    
    if new_index >= len(data):
        new_index = False
    
    # Convert bet opportunities to dictionary format
    return jsonify({
        "results" : len(to_return),
        "data" : to_return,
        "next_page_index" : new_index
        }), 200

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
