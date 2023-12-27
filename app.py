from flask import Flask,render_template,request,flash,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'our_realy_realy_secret_key'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)

class User(UserMixin,db.Model):
    id = db.Column(db.Integer,unique=True,primary_key=True)
    is_user = db.Column(db.Boolean,nullable=False)
    username = db.Column(db.String(50),unique=True,nullable=False)
    password = db.Column(db.String(120), nullable=False)
    adresse = db.Column(db.String(150), nullable=False)
    plz = db.Column(db.Integer, nullable=False)

class Restaurant(UserMixin,db.Model):
    id = db.Column(db.Integer,unique=True,primary_key=True)
    is_user = db.Column(db.Boolean,nullable=False)
    username = db.Column(db.String(50),unique=True,nullable=False)
    password = db.Column(db.String(120), nullable=False)
    adresse = db.Column(db.String(150), nullable=False)
    plz = db.Column(db.String, nullable=True)


    def set_plz(self, plz_list):
        self.plz = json.dumps(plz_list)

    def get_plz(self):
        return json.loads(self.plz) if self.plz else []


with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/loginForCustomer",methods=['POST','GET'])
def loginForCustomer():
    if request.method == 'POST':
        if "register" in request.form:
            username = request.form["register_username"]
            password = request.form["register_password"]
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            adresse = request.form["register_adresse"]
            plz = request.form["register_plz"]

            new_customer = User(username=username,password=hashed_password,adresse=adresse,plz=plz,is_user=True)
            db.session.add(new_customer)
            db.session.commit()

            flash('You are successfully registered. Now you can log in !', 'success')

        elif "login" in request.form:
            username= request.form["login_username"]
            password = request.form["login_password"]
            
            user = User.query.filter_by(username=username).first()

            if user and bcrypt.check_password_hash(user.password, password):
                login_user(user)
                flash('You are successfully log in. Now you can order something !', 'success')
                return redirect(url_for('home'))
            else:
                flash('Please check your id or password again. !', 'danger')

    return render_template("loginForCustomer.html")

@app.route("/loginForRestaurant",methods=['POST','GET'])
def loginForRestaurant():
    if request.method == 'POST':
        if "register" in request.form:
            username = request.form["register_username"]
            password = request.form["register_password"]
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            adresse = request.form["register_adresse"]
            plz = request.form["register_plz"]

            new_customer = Restaurant(username=username,password=hashed_password,adresse=adresse,plz=plz,is_user=False)
            db.session.add(new_customer)
            db.session.commit()

            flash('You are successfully registered. Now you can log in !', 'success')

        elif "login" in request.form:
            username= request.form["login_username"]
            password = request.form["login_password"]
            
            restaurant = Restaurant.query.filter_by(username=username).first()

            if restaurant and bcrypt.check_password_hash(restaurant.password, password):
                login_user(restaurant)
                flash('You are successfully log in. Now you can order something !', 'success')
                return redirect(url_for('home'))
            else:
                flash('Please check your id or password again. !', 'danger')

    return render_template("loginForRestaurant.html")



@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)