from flask import Flask, request,render_template, redirect,session, Response, jsonify
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import gunicorn
from camera import *

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)
app.secret_key = 'secret_key'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))

    def __init__(self,email,password,name):
        self.name = name
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self,password):
        return bcrypt.checkpw(password.encode('utf-8'),self.password.encode('utf-8'))

with app.app_context():
    db.create_all()



@app.route('/forgotpassword', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Query the database to find the user with the specified email
        user = User.query.filter_by(email=email).first()

        # Check if the user exists
        if user:
            # Check if the new password matches the confirm password
            if new_password == confirm_password:
                # Update the user's password in the database
                user.password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                db.session.commit()
                return redirect('/login')
            else:
                return redirect('/forgotpasswordpage')
        else:
            return 'Email not found in database!'

    return render_template('forgotpassword.html')

@app.route('/forgotpasswordpage')
def forgot_password1():

    return render_template('forgotpassword1.html')

headings = ("Movie","Song","Artist")
df1 = music_rec()
df1 = df1.head(15)

@app.route('/Recommended')
def Recommended():
    print(df1.to_json(orient='records'))
    
    return render_template('Recommended.html', headings=headings, data=df1)
    #return redirect('/Song')
@app.route('/about')
def about():
    return render_template('sampleabout.html')
    


def gen(camera):
    while True:
        global df1
        frame, df1 = camera.get_frame()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n\r\n')

@app.route('/video_feed')
def video_feed():
    return Response(gen(VideoCamera()),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/t')
def gen_table():
    return df1.to_json(orient='records')






@app.route('/Song')
def Song():
    return render_template('next.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register',methods=['GET','POST'])
def register():
    if request.method == 'POST':
        # handle request
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']

        new_user = User(name=name,email=email,password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')

    return render_template('register.html')


# Route to handle the form submission and update the password in the data

@app.route('/login',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/Recommended')
        else:
            return render_template('login.html',error='Invalid user')

    return render_template('login.html')




@app.route('/dashboard')
def dashboard():
    if session['email']:
        user = User.query.filter_by(email=session['email']).first()
        return render_template('dashboard.html',user=user)
    
    return redirect('/login')

@app.route('/logout')
def logout():
    session.pop('email',None)
    return redirect('/login')

if __name__ == '__main__':
    app.run(debug=True)
