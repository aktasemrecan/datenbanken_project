from flask import Flask,render_template,request,flash,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'our_realy_realy_secret_key'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///customers.db"
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)

class Customer(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    username = db.Column(db.String(50),unique=True,nullable=False)
    password = db.Column(db.String(120), nullable=False)


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register",methods=['POST','GET'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

        new_customer = Customer(username=username,password=hashed_password)
        db.session.add(new_customer)
        db.session.commit()
        return redirect("/")

    return render_template("register.html")


if __name__ == '__main__':
    app.run(debug=True)