from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime
from scripts import get_bet_opportunities, delete_bet_opportunity, refresh_bet_opportunities, get_bet_opportunity_orderbooks


app = Flask(__name__)
CORS(app)


# Endpoint to refresh the bet opportunities
@app.route('/refresh_bet_opportunities', methods=['POST'])
def refresh_bet_opportunity_data():
    bet_opportunities = refresh_bet_opportunities()
    return jsonify({"message": "Bet opportunities refreshed successfully", "total_opportunities": len(bet_opportunities)}), 201

@app.route('/bet_opportunity/<string:bet_id>', methods=['GET'])
def get_bet_opportunity(bet_id):
    bo, obs = get_bet_opportunity_orderbooks(bet_id)

    
    return jsonify({
        "bet_opportunity" : bo.to_json(),
        "orderbooks" : obs.to_json()
    }), 200



# Endpoint to get the list of bet opportunities
@app.route('/bet_opportunities', methods=['GET'])
def bet_opportunities():
    page_index = int(request.args.get('page_index')) #type: ignore
    sort = request.args.get('sort')
    results_per_page = int(request.args.get('results_per_page')) #type: ignore
    data = [x.to_json() for x in get_bet_opportunities(sort)]
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

# Endpoint to delete a bet opportunity by id
@app.route('/bet_opportunities/<string:bet_id>', methods=['DELETE'])
def delete_bet_opportunities(bet_id):

    Found, bet_opportunities = delete_bet_opportunity(bet_id)
    print(Found)
    if not Found:
        return jsonify({"message": "Bet opportunity not found"}), 404

    return jsonify({"message": f"Bet opportunity with id {bet_id} deleted successfully", "remaining_opportunities": len(bet_opportunities)}), 200

# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
