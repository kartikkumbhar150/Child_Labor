from flask import Flask, render_template, request, jsonify
import mysql.connector
from twilio.rest import Client

app = Flask(__name__)

# Twilio setup
account_sid = ''
auth_token = ''
twilio_number = ''
client = Client(account_sid, auth_token)

# MySQL connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="kartik123",
    database="my_database_name"
)
cursor = db.cursor(dictionary=True)

@app.route('/admin')
def admin_page():
    return render_template('admin.html')

@app.route('/api/ngosdataa')
def get_ngos_data():
    cursor.execute("SELECT * FROM ngosdataa")
    return jsonify(cursor.fetchall())

@app.route('/api/verify', methods=['POST'])
def verify():
    data = request.json
    complaint_id = data['id']

    cursor.execute("UPDATE ngosdataa SET is_verified = TRUE WHERE id = %s", (complaint_id,))
    db.commit()

    cursor.execute("SELECT name, phone FROM ngosdataa WHERE id = %s", (complaint_id,))
    user = cursor.fetchone()

    if user:
        client.calls.create(
            twiml=f'<Response><Say>Hello {user["name"]}, your complaint has been verified. Thank you for your contribution.</Say></Response>',
            to=user['phone'],
            from_=twilio_number
        )
        return jsonify({"message": "Verified and call placed successfully."})
    else:
        return jsonify({"error": "User not found"}), 404

if __name__ == '__main__':
    app.run(port=5002)
