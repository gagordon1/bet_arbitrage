from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from TradingOpportunities import BetDataManager, BetArbitrageAnalyzer


# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Instantiate Data Manager & Analyzer
data_manager = BetDataManager()
analyzer = BetArbitrageAnalyzer()

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

# ----------------------------- API Endpoints -----------------------------

@app.route('/refresh_bet_opportunities', methods=['POST'])
def refresh_bet_opportunity_data():
    """Refreshes bet opportunities and returns the count of updated opportunities."""
    bet_opportunities = data_manager.refresh_bet_opportunities()
    return jsonify({"message": "Bet opportunities refreshed successfully", "total_opportunities": len(bet_opportunities)}), 201


@app.route('/bet_opportunity/<string:bet_id>', methods=['GET'])
def get_bet_opportunity(bet_id):
    """Retrieves a specific bet opportunity and its orderbooks."""
    try:
        bo, obs = analyzer.get_bet_opportunity_orderbooks(bet_id)
        return jsonify({"bet_opportunity": bo.to_json(), "orderbooks": obs.to_json()}), 200
    except Exception as e:
        logging.error(f"Error fetching bet opportunity {bet_id}: {e}")
        return jsonify({"error": "Bet opportunity not found"}), 404


@app.route('/bet_opportunities', methods=['GET'])
def bet_opportunities():
    """Returns a paginated list of bet opportunities, sorted if specified."""
    try:
        page_index = int(request.args.get('page_index', 0))
        results_per_page = int(request.args.get('results_per_page', 10))
        sort = request.args.get('sort')
        all_opportunities = analyzer.get_bet_opportunities(sort = sort) #type: ignore
        total_opportunities = len(all_opportunities)

        # Pagination
        start_index = page_index * results_per_page
        end_index = start_index + results_per_page
        paginated_opportunities = [x.to_json() for x in all_opportunities[start_index:end_index]]

        next_page_index = page_index + 1 if end_index < total_opportunities else None

        return jsonify({
            "results": len(paginated_opportunities),
            "data": paginated_opportunities,
            "next_page_index": next_page_index
        }), 200
    except Exception as e:
        logging.error(f"Error fetching bet opportunities: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route('/bet_opportunities/<string:bet_id>', methods=['DELETE'])
def delete_bet_opportunities(bet_id):
    """Deletes a bet opportunity by its ID."""
    try:
        found, remaining_opportunities = analyzer.delete_bet_opportunity(bet_id)

        if not found:
            return jsonify({"message": "Bet opportunity not found"}), 404

        return jsonify({"message": f"Bet opportunity with id {bet_id} deleted successfully",
                        "remaining_opportunities": len(remaining_opportunities)}), 200
    except Exception as e:
        logging.error(f"Error deleting bet opportunity {bet_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


# ----------------------------- Run Flask App -----------------------------
if __name__ == '__main__':
    app.run(debug=True)
