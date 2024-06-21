from datetime import date, timedelta
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import base64
from flask_swagger_ui import get_swaggerui_blueprint

from data.entities.resource import Resource
from extensions import db
from data.repositories.resource_repository import ResourceRepository

app = Flask(__name__)
CORS(app)  # Enable CORS for all origins

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://align:mm9wYNPefPa3@212.64.220.180:5432/exp_payroll'
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
    return jsonify({"message": "Payroll created successfully"}), 200

@app.route('/api/get-payroll-by-userid', methods=['GET'])
def get_payroll_by_userid():
    userid = request.args.get('userid')
    
    if userid is None:
        return jsonify({"message": "Parameter 'userid' is required"}), 400

    today = date.today()
    start_of_month = datetime(today.year, today.month, 1)
    end_of_month = datetime(today.year, today.month + 1, 1) - timedelta(days=1)

    print(f"today: {today}")
    print(f"start_of_month: {start_of_month}")
    print(f"end_of_month: {end_of_month}")

    payroll_record = Resource.query.filter(
        Resource.userid == userid,
        Resource.created_at >= start_of_month,
        Resource.created_at <= end_of_month,
        Resource.is_read == False  # çalışan ekranından atılacak, eğer kullanıcının okunmamıs bordrosu var ise kayıt dönülecek #
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

@app.route('/api/get-sent-payrolls', methods=['GET'])
def get_sent_payrolls():
    today = date.today()
    start_of_month = datetime(today.year, today.month, 1)
    # Calculate the end of the current month
    next_month = today.month % 12 + 1
    next_month_year = today.year if today.month < 12 else today.year + 1
    end_of_month = datetime(next_month_year, next_month, 1) - timedelta(days=1)

    print(f"today: {today}")
    print(f"start_of_month: {start_of_month}")
    print(f"end_of_month: {end_of_month}")

    payroll_records = Resource.query.filter(
        Resource.created_at >= start_of_month,
        Resource.created_at <= end_of_month,
    ).all()

    if payroll_records:
        response_data = []
        for record in payroll_records:
            pdf_base64 = base64.b64encode(record.pdf_data).decode('utf-8')
            response_data.append({
                "userid": record.userid,
                "pdf_data": pdf_base64
            })
        return jsonify(response_data), 200
    else:
        return jsonify({"message": "No payroll records found for the specified period"}), 404

@app.route('/api/set-payroll-read', methods=['POST'])
def setPayrollRead():
    content = request.json
    user_id = content.get('userid')

    if user_id is None:
        return jsonify({"message": "userid is required"}), 400

    is_payroll_read = resource_repository.is_payroll_read(user_id=user_id)

    if is_payroll_read == True:
        return jsonify({"message": "payroll is already read"}), 403

    payroll = resource_repository.get_payroll_by_userId(user_id=user_id)

    updated_resource = resource_repository.update(resource_id=payroll.id, data={
        'userid': user_id,
        'pdf_data': payroll.pdf_data,
        'is_read': True
    })

    if updated_resource:
        return jsonify({"status": "success"}), 200
    else:
        return jsonify({"message": "update failed"}), 403

@app.route('/api/delete-payroll-by-userid', methods=['DELETE'])
def deletePayrollByUserId():
    userid = request.args.get('userid')

    if userid is None:
        return jsonify({"message": "Parameter 'userid' is required"}), 400

    payroll_records = Resource.query.filter(Resource.userid == userid).all()

    if not payroll_records:
        return jsonify({"message": "No payroll records found for the specified userid"}), 404

    for record in payroll_records:
        db.session.delete(record)
    db.session.commit()

    return jsonify({"message": "Payroll records deleted successfully"}), 200

@app.route('/api/delete-all', methods=['DELETE'])
def deleteAllPayrolls():

    payroll_records = Resource.query.all()

    if not payroll_records:
        return jsonify({"message": "No payroll records found for the specified userid"}), 404

    for record in payroll_records:
        db.session.delete(record)
    db.session.commit()

    return jsonify({"message": "All payrolls deleted successfully."}), 200

@app.route('/api/healthcheck', methods=['GET'])
def healthcheck():
    return jsonify({"message": "OK"}), 200

# Swagger UI setup
SWAGGER_URL = '/swagger'
API_URL = '/static/swagger.yaml'
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "Payroll API"
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

# Serve static files
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)

if __name__ == '__main__':
    app.run(debug=True)
