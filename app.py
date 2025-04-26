import os
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re, pickle, torch, random
from flask_cors import CORS 
from twilio.rest import Client
from datetime import datetime, timedelta
from model_architecture import LSTMClassifier
from werkzeug.utils import secure_filename
import face_recognition
import os
import uuid

app = Flask(__name__)
app.secret_key = 'kartikk123'

################################################################
#missing code
UPLOAD_FOLDER = 'static/uploads'
MISSING_FOLDER = 'static/missing_db'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

################################################################
# CORS
CORS(app)

# MySQL Config
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'kartik123'
app.config['MYSQL_DB'] = 'my_database_name'

mysql = MySQL(app)

# Twilio Config
account_sid = ''
auth_token = ''
twilio_number = ''

# Load Tokenizer & Model
with open("model/tokenizer.pkl", "rb") as f:
    vocab = pickle.load(f)

model = LSTMClassifier(len(vocab), 64, 64, 3)
model.load_state_dict(torch.load("model/ml_model.pth"))
model.eval()

def tokenize(text):
    return re.findall(r'\b\w+\b', text.lower())

def text_to_tensor(text):
    return torch.tensor([vocab.get(token, vocab["<UNK>"]) for token in tokenize(text)])

def predict_severity(description):
    x = text_to_tensor(description).unsqueeze(0)
    with torch.no_grad():
        output = model(x)
        predicted = torch.argmax(output, dim=1).item()
    return predicted

# === OTP Functions ===
def generate_otp(length=6):
    return ''.join(str(random.randint(0, 9)) for _ in range(length))

def send_otp(phone_number, otp):
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=f'Your OTP is: {otp}',
        from_=twilio_number,
        to=phone_number
    )
    return message.sid

def store_otp(phone_number, otp, expires_minutes=5):
    expires_at = datetime.now() + timedelta(minutes=expires_minutes)
    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO otp_verification (phone_number, otp_code, expires_at) VALUES (%s, %s, %s)",
                   (phone_number, otp, expires_at))
    mysql.connection.commit()
    cursor.close()

def verify_otp(phone_number, otp_input):
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT otp_code, expires_at FROM otp_verification
        WHERE phone_number = %s ORDER BY id DESC LIMIT 1
    """, (phone_number,))
    result = cursor.fetchone()
    cursor.close()

    if not result:
        return False, "No OTP found"
    
    otp_stored, expires_at = result
    if datetime.now() > expires_at:
        return False, "OTP expired"
    if otp_input != otp_stored:
        return False, "Incorrect OTP"
    
    return True, "OTP verified"

# === Routes ===

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start', methods=['GET', 'POST'])
def phone_input():
    if request.method == 'POST':
        phone = request.form['phone']
        otp = generate_otp()
        send_otp(phone, otp)
        store_otp(phone, otp)
        session['phone'] = phone
        flash("OTP sent to your phone number.", "info")
        return redirect('/verify')
    return render_template('phone_input.html')

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if 'phone' not in session:
        return redirect('/start')
    if request.method == 'POST':
        otp_input = request.form['otp']
        phone = session['phone']
        is_valid, msg = verify_otp(phone, otp_input)
        if is_valid:
            session['otp_verified'] = True
            return redirect('/signup')
        else:
            flash(msg, "error")
    return render_template('otp_verify.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if not session.get('otp_verified'):
        return redirect('/start')
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        registration = request.form['registration']
        phone = session['phone']
        password = request.form['password']
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO ngos (username, password) VALUES (%s, %s)", (email, password))
        cursor.execute("INSERT INTO ngosdataa (name, email, registration, phone, password) VALUES (%s, %s, %s, %s, %s)", (name, email, registration, phone, password))
                       
        mysql.connection.commit()
        cursor.close()
        flash("Signup successful!", "success")
        session.clear()
        return redirect('/')
    return render_template('signup.html')

@app.route('/complain', methods=['GET'])
def complain():
    return render_template('complain.html')

@app.route('/contact', methods=['GET'])
def contact():
    return render_template('contact.html')

@app.route('/donation', methods=['GET'])
def donation():
    return render_template('donation.html')

@app.route('/submit', methods=['POST'])
def submit():
    name = request.form.get('name')
    email = request.form.get('email')
    description = request.form.get('description')
    location = request.form.get('location')
    num_children = request.form.get('num_children')
    gender = request.form.get('gender')
    age = request.form.get('age')
    photos = request.files.getlist('photos')

    photo_paths = []
    for photo in photos:
        if photo.filename != '':
            filename = secure_filename(photo.filename)
            photo_path = os.path.join('static/uploads', filename)
            photo.save(photo_path)
            photo_paths.append(photo_path)

    severity = predict_severity(description)

    cursor = mysql.connection.cursor()
    cursor.execute('''INSERT INTO complaints (name, email, description, location, num_children, gender, age, photo1, photo2, photo3, photo4, severity, status) 
                      VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)''',
                   (name, email, description, location, num_children, gender, age,
                    photo_paths[0] if len(photo_paths) > 0 else None,
                    photo_paths[1] if len(photo_paths) > 1 else None,
                    photo_paths[2] if len(photo_paths) > 2 else None,
                    photo_paths[3] if len(photo_paths) > 3 else None,
                    severity, 'unresolved'))
    mysql.connection.commit()
    cursor.close()

    return redirect(url_for('index'))

@app.route('/ngo-login', methods=['GET', 'POST'])
def ngo_login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM ngos WHERE username = %s AND password = %s', (username, password))
        account = cursor.fetchone()
        if account:
            session['loggedin'] = True
            session['username'] = account['username']
            return redirect(url_for('dashboard'))
        else:
            msg = 'Incorrect username or password!'
    return render_template('ngo_login.html', msg=msg)

@app.route('/dashboard')
def dashboard():
    if 'loggedin' in session:
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM complaints')
        complaints = cursor.fetchall()
        return render_template('dashboard.html', complaints=complaints)
    return redirect(url_for('ngo_login'))

@app.route('/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('username', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
