from datetime import datetime
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

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    is_user = db.Column(db.Boolean, nullable=False, default=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(150), nullable=False)
    plz = db.Column(db.String, nullable=False)
    shopping_cart = db.relationship('ShoppingCart', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

class ShoppingCart(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    products = db.relationship('Product', secondary='shopping_cart_products', backref=db.backref('shopping_carts', lazy='dynamic'))
    quantities = db.relationship('ShoppingCartProduct', backref='shopping_cart', lazy='dynamic')


class ShoppingCartProduct(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    shopping_cart_id = db.Column(db.Integer, db.ForeignKey('shopping_cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)


shopping_cart_products = db.Table('shopping_cart_products',
    db.Column('shopping_cart_id', db.Integer, db.ForeignKey('shopping_cart.id')),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id')),
    db.Column('quantity', db.Integer, nullable=False, default=1)
)


class Order(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    order_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    total_amount = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    products = db.relationship('Product', secondary='order_products', backref='orders', lazy='dynamic')

# Define a many-to-many relationship table between Order and Product
order_products = db.Table('order_products',
    db.Column('order_id', db.Integer, db.ForeignKey('order.id')),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id'))
)

class Restaurant(UserMixin, db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    is_user = db.Column(db.Boolean, nullable=False, default=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(150), nullable=False)
    products = db.relationship('Product', backref='restaurant', lazy=True)
    plz_list = db.Column(db.String, nullable=True)

    def add_plz(self, plz):
        plz_list = self.get_plz()
        plz_list.append(str(plz))
        self.set_plz(plz_list)

    def set_plz(self, plz_list):
        self.plz_list = json.dumps(plz_list)

    def get_plz(self):
        return json.loads(self.plz_list) if self.plz_list else []



class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    

    
with app.app_context():
    db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route("/")
def home():
    restaurants = Restaurant.query.all()
    if current_user.is_authenticated:
        if current_user.is_user:
            return render_template("index.html",restaurants=restaurants)
        else:
            return redirect(url_for('my_restaurant'))
    else:
        return render_template("index.html",restaurants=restaurants)


@app.route("/loginForCustomer",methods=['POST','GET'])
def loginForCustomer():
    if request.method == 'POST':
        if "register" in request.form:
            username = request.form["register_username"]
            password = request.form["register_password"]
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            address = request.form["register_address"]
            plz = request.form["register_plz"]

            new_customer = User(username=username,password=hashed_password,address=address,plz=plz,is_user=True)
            db.session.add(new_customer)
            db.session.commit()

            flash('You are successfully registered. Now you can log in !', 'success')

        elif "login" in request.form:
            username= request.form["login_username"]
            password = request.form["login_password"]
            
            user = User.query.filter_by(is_user=True,username=username).first()

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
            address = request.form["register_address"]
            description = request.form["description"]

            new_customer = Restaurant(username=username,password=hashed_password,address=address,description=description,is_user=False)
            db.session.add(new_customer)
            db.session.commit()

            flash('You are successfully registered. Now you can log in !', 'success')

        elif "login" in request.form:
            username= request.form["login_username"]
            password = request.form["login_password"]   
            
            restaurant = Restaurant.query.filter_by(is_user=False,username=username).first()

            if restaurant and bcrypt.check_password_hash(restaurant.password, password):
                login_user(restaurant)
                flash('You are successfully log in. Now you can order something !', 'success')
                return redirect(url_for('home'))
            else:
                flash('Please check your id or password again. !', 'danger')
    return render_template("loginForRestaurant.html")

@app.route("/shopping-cart",methods=['POST','GET'])
def shoppingCart():
    shopping_cart = current_user.shopping_cart[0] if current_user.shopping_cart else None

    # Eğer alışveriş sepeti varsa, ürünleri al
    products_in_cart = []
    if shopping_cart:
        for cart_product in shopping_cart.quantities:
            product = Product.query.get(cart_product.product_id)
            products_in_cart.append({
                'product': product,
                'quantity': cart_product.quantity
            })
        total_price = calculate_total(shopping_cart)
    else:
        total_price = 0
        print("Alışveriş sepetiniz boş veya tanımlı değil.")


    print(products_in_cart)

    return render_template("shopping_cart.html",shoppingCart= products_in_cart,total_price=total_price)

@app.route("/orders")
@login_required
def my_orders():
    user = current_user

    # Get the orders for the current user
    orders = Order.query.filter_by(user_id=user.id).all()

    return render_template("orders.html", orders=orders)

@app.route("/restaurant/<int:restaurant_id>", methods=['POST', 'GET'])
def restaurant_page(restaurant_id):
    restaurant = Restaurant.query.get(restaurant_id)

    return render_template("restaurant.html", restaurant=restaurant)

def calculate_total(shopping_cart):
    total = 0

    for cart_product in shopping_cart.quantities:
        product = Product.query.get(cart_product.product_id)
        total += product.price * cart_product.quantity

    return total


@app.route("/add_to_cart/<int:product_id>", methods=['POST','GET'])
@login_required
def add_to_cart(product_id):
    user = current_user

    # Kullanıcının alışveriş sepetini kontrol et veya oluştur
    if not user.shopping_cart:
        shopping_cart = ShoppingCart(user=user)
        db.session.add(shopping_cart)
        db.session.commit()
    else:
        # Kullanıcının alışveriş sepetini al
        shopping_cart = user.shopping_cart[0] if user.shopping_cart else None

    # Check if the product is already in the cart
    existing_item = ShoppingCartProduct.query.filter_by(shopping_cart_id=shopping_cart.id, product_id=product_id).first()

    if existing_item:
        # If the product is already in the cart, increase the quantity
        existing_item.quantity += 1
    else:
        # Otherwise, add a new item with quantity 1
        product = Product.query.get(product_id)
        shopping_cart_product = ShoppingCartProduct(shopping_cart_id=shopping_cart.id, product_id=product_id, quantity=1)
        db.session.add(shopping_cart_product)

    db.session.commit()
    flash('Ürün sepete eklendi!', 'success')
    return redirect(url_for('restaurant_page', restaurant_id=request.form.get('restaurant_id')))


@app.route("/reduce_quantity/<int:product_id>", methods=['POST', 'GET'])
@login_required
def reduce_quantity(product_id):

    user = current_user
    shopping_cart = user.shopping_cart[0] if user.shopping_cart else None

    if shopping_cart:
        cart_product = ShoppingCartProduct.query.filter_by(shopping_cart_id=shopping_cart.id, product_id=product_id).first()

        if cart_product:
            if cart_product.quantity > 1:
                cart_product.quantity -= 1
            else:
                db.session.delete(cart_product)

            db.session.commit()
            flash('Ürün miktarı azaltıldı!', 'success')
        else:
            flash('Ürün sepetinizde bulunmamaktadır!', 'danger')
    else:
        flash('Alışveriş sepetiniz boş veya tanımlı değil.', 'danger')


    return redirect(url_for('shoppingCart'))

@app.route("/increment_quantity/<int:product_id>", methods=['POST', 'GET'])
@login_required
def increment_quantity(product_id):

    user = current_user
    shopping_cart = user.shopping_cart[0] if user.shopping_cart else None

    if shopping_cart:
        # Check if the product is in the shopping cart
        cart_product = ShoppingCartProduct.query.filter_by(shopping_cart_id=shopping_cart.id, product_id=product_id).first()

        if cart_product:
            cart_product.quantity += 1

            db.session.commit()
            flash('Ürün miktarı arttirildi!', 'success')
        else:
            flash('Ürün sepetinizde bulunmamaktadır!', 'danger')
    else:
        flash('Alışveriş sepetiniz boş veya tanımlı değil.', 'danger')


    return redirect(url_for('shoppingCart'))

@app.route("/place_order", methods=['POST', 'GET'])
@login_required
def place_order():
    user = current_user
    shopping_cart = user.shopping_cart[0] if user.shopping_cart else None

    if shopping_cart:
        # Siparişi oluştur
        order = Order(user_id=user.id, order_date=datetime.utcnow(), total_amount=calculate_total(shopping_cart))

        for cart_product in shopping_cart.quantities:
            product = Product.query.get(cart_product.product_id)
            order.products.append(product)

        # Siparişi veritabanına kaydet
        db.session.add(order)
        db.session.commit()

        # Alışveriş sepetini temizle
        clear_shopping_cart(shopping_cart)

        flash('Siparişiniz başarıyla alındı!', 'success')
        return redirect(url_for('home'))
    else:
        flash('Alışveriş sepetiniz boş veya tanımlı değil.', 'danger')
        return redirect(url_for('shoppingCart'))

def calculate_total(shopping_cart):
    total = 0
    for cart_product in shopping_cart.quantities:
        product = Product.query.get(cart_product.product_id)
        total += product.price * cart_product.quantity
    return total

def clear_shopping_cart(shopping_cart):
    # Alışveriş sepetini temizle
    for cart_product in shopping_cart.quantities:
        db.session.delete(cart_product)
    db.session.commit()


@app.route("/my_restaurant",methods=['POST','GET'])
def my_restaurant():
    restaurant = Restaurant.query.get(current_user.id)
    if request.method == "POST":
        if "add_product" in request.form:
            product_name = request.form["product_name"]
            price = request.form["price"]

            new_product = Product(name=product_name,price=price,restaurant_id=current_user.id)
            db.session.add(new_product)
            db.session.commit()
        elif "add_plz" in request.form:
            plz = int(request.form["add_plz"])  # Convert the input value to an integer
            restaurant.add_plz(plz)
            db.session.commit()

    plz_list = restaurant.get_plz()
    products = Product.query.filter_by(restaurant_id=current_user.id)
    return render_template("my_restaurant.html",restaurant=restaurant,products=products,plz_list=plz_list)
    

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) or Restaurant.query.get(int(user_id))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)