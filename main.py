from datetime import date, timedelta
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64

from data.entities.resource import Resource
from extensions import db
from data.repositories.resource_repository import ResourceRepository

app = Flask(__name__)
CORS(app)  # Enable CORS for all origins

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://trendyol:trendyol-bot-1234321@localhost:5432/exp_payroll'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

with app.app_context():
    db.create_all()     

resource_repository = ResourceRepository()

@app.route('/api/create-payroll', methods=['POST'])
def create_resource():
    content = request.json
    user_id = content.get('userid')
    pdf_base64 = content.get('pdf_base64')

    if user_id is None or pdf_base64 is None:
        return jsonify({"message": "Both 'userid' and 'pdf_base64' are required"}), 400

    try:
        # Decode the base64 string
        pdf_data = base64.b64decode(pdf_base64)
    except (TypeError, ValueError):
        return jsonify({"message": "Invalid base64 string"}), 400

    resource = {
        "userid": user_id,
        "pdf_data": pdf_data
    }

    resource_repository.create(resource)
    return jsonify({"message": "Payroll created successfully"}), 201

@app.route('/api/get-payroll', methods=['GET'])
def get_payroll():
    # Parse the userid parameter from the query string
    userid = request.args.get('userid')
    
    if userid is None:
        return jsonify({"message": "Parameter 'userid' is required"}), 400

    # Get the current month's start and end dates
    today = date.today()
    start_of_month = datetime(today.year, today.month, 1)
    end_of_month = datetime(today.year, today.month + 1, 1) - timedelta(days=1)

    print(f"today: {today}")
    print(f"start_of_month: {start_of_month}")
    print(f"end_of_month: {end_of_month}")

    # Query the database for records matching the criteria
    payroll_record = Resource.query.filter(
        Resource.userid == userid,
        Resource.created_at >= start_of_month,
        Resource.created_at <= end_of_month,
        Resource.is_read == False
    ).first()

    if payroll_record:
        pdf_base64 = base64.b64encode(payroll_record.pdf_data).decode('utf-8')
        
        response_data = {
            "userid": payroll_record.userid,
            "pdf_data": pdf_base64
        }
        return jsonify(response_data), 200
    else:
        return jsonify({"message": "No unread payroll record found for the specified userid"}), 404

@app.route('/api/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({"message": "OK"}), 200

if __name__ == '__main__':
    app.run(debug=True)
