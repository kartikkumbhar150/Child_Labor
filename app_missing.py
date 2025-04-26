import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import mysql.connector
import face_recognition

app = Flask(__name__)
app.secret_key = 'kartik123'
UPLOAD_FOLDER = 'static/uploads'
MISSING_FOLDER = 'static/missing_db'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# MySQL Configuration
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    password="kartik123",
    database="my_database_name"
)
mycursor = mydb.cursor()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_to_db(name, age, description, location, contact, filename):
    sql = "INSERT INTO lost_children (name, age, description, location, contact, photo) VALUES (%s, %s, %s, %s, %s, %s)"
    val = (name, age, description, location, contact, filename)
    mycursor.execute(sql, val)
    mydb.commit()

def compare_faces(upload_path):
    known_faces = []
    known_names = []
    for file in os.listdir(MISSING_FOLDER):
        try:
            image_path = os.path.join(MISSING_FOLDER, file)
            image = face_recognition.load_image_file(image_path)
            encoding = face_recognition.face_encodings(image)[0]
            known_faces.append(encoding)
            known_names.append(file)
        except Exception as e:
            print(f"Error processing {file}: {e}")

    uploaded_image = face_recognition.load_image_file(upload_path)
    uploaded_encoding = face_recognition.face_encodings(uploaded_image)[0]
    results = face_recognition.compare_faces(known_faces, uploaded_encoding)
    matches = [known_names[i] for i, match in enumerate(results) if match]
    return matches

@app.route('/missing', methods=['GET', 'POST'])
def index_missing():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        description = request.form['description']
        location = request.form['location']
        contact = request.form['contact']
        file = request.files['photo']

        if file and allowed_file(file.filename):
            filename = secure_filename(str(uuid.uuid4()) + "_" + file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            save_to_db(name, age, description, location, contact, filename)
            matches = compare_faces(filepath)

            return render_template('index_missing.html', matches=matches, name=name)
        else:
            flash('Invalid file format')
            return redirect(request.url)

    return render_template('index_missing.html')

@app.route('/dashboard_missing')
def dashboard():
    mycursor.execute("SELECT * FROM lost_children ORDER BY id DESC")
    data = mycursor.fetchall()
    return render_template('dashboard_missing.html', cases=data)

if __name__ == '__main__':
    app.run(port=5003)
