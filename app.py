from datetime import datetime
from flask import Flask,render_template,request,flash,redirect,url_for
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import json
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'our_realy_realy_secret_key'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
app.config['SQLALCHEMY_ECHO'] = True


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
    restaurant_id = db.Column(db.Integer, nullable=False)



shopping_cart_products = db.Table('shopping_cart_products',
    db.Column('shopping_cart_id', db.Integer, db.ForeignKey('shopping_cart.id')),
    db.Column('product_id', db.Integer, db.ForeignKey('product.id')),
    db.Column('quantity', db.Integer, nullable=False, default=1),
    db.Column('restaurant_id', db.Integer, nullable=False)

)


class Order(db.Model):
    id = db.Column(db.Integer, unique=True, primary_key=True)
    order_date = db.Column(db.DateTime, default=db.func.current_timestamp())
    total_amount = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    products = db.relationship('Product', secondary='order_products', backref='orders', lazy='dynamic')
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=True)
    quantities = db.relationship('OrderProduct', backref='order', lazy='dynamic')
    status = db.Column(db.String(20), nullable=False, default='Pending')  
    note = db.Column(db.String(255), nullable=True)


class OrderProduct(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    quantity = db.Column(db.Integer, nullable=False, default=1)
    product = db.relationship('Product', backref='order_products', lazy=True)



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
    opening_hour = db.Column(db.Time, nullable=False)
    closing_hour = db.Column(db.Time, nullable=False)
    photo_path = db.Column(db.String(255), nullable=True)

    def add_plz(self, plz):
        plz_list = self.get_plz()
        plz_list.append(str(plz))
        self.set_plz(plz_list)

    def set_plz(self, plz_list):
        self.plz_list = json.dumps(plz_list)

    def get_plz(self):
        return json.loads(self.plz_list) if self.plz_list else []
    
    def set_photo_path(self, photo_path):
        self.photo_path = photo_path.replace('\\', '/')



class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurant.id'), nullable=False)
    photo_path = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), nullable=True)
    description = db.Column(db.String(70), nullable=True)

    def set_photo_path(self, photo_path):
        self.photo_path = photo_path.replace('\\', '/')

    
with app.app_context():
    db.create_all()



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
                logout_user()
                login_user(user)
                flash('You are successfully log in. Now you can order something !', 'success')
                return redirect(url_for('home'))
            else:
                flash('Please check your id or password again. !', 'danger')

    return render_template("loginForCustomer.html")

def get_next_restaurant_id():
    
    last_restaurant = Restaurant.query.order_by(Restaurant.id.desc()).first()

    if last_restaurant:
        return last_restaurant.id + 1
    else:
        return 1000 


@app.route("/loginForRestaurant", methods=['POST', 'GET'])
def loginForRestaurant():
    if request.method == 'POST':
        if "register" in request.form:
            username = request.form["register_username"]
            password = request.form["register_password"]
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            address = request.form["register_address"]
            description = request.form["description"]
            opening_hour = request.form["opening_hour"]
            closing_hour = request.form["closing_hour"]

            if 'restaurant_photo' in request.files:
                file = request.files['restaurant_photo']

                if file:
                    upload_folder = 'uploads'
                    
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)

                    file_path = os.path.join(upload_folder, file.filename)
                    file.save(file_path)

            opening_hour = datetime.strptime(opening_hour, "%H:%M").time()
            closing_hour = datetime.strptime(closing_hour, "%H:%M").time()

            file_path = file_path.replace('\\', '/')
            new_restaurant = Restaurant(
                opening_hour=opening_hour,
                closing_hour=closing_hour,
                username=username,
                password=hashed_password,
                address=address,
                description=description,
                is_user=False
            )

            if 'file_path' in locals():
                new_restaurant.photo_path = file_path
            new_restaurant.id = get_next_restaurant_id()
            db.session.add(new_restaurant)
            db.session.commit()

            flash('You are successfully registered. Now you can log in!', 'success')

        elif "login" in request.form:
            username= request.form["login_username"]
            password = request.form["login_password"]   
            
            restaurant = Restaurant.query.filter_by(is_user=False,username=username).first()

            if restaurant and bcrypt.check_password_hash(restaurant.password, password):
                logout_user()
                login_user(restaurant)
                flash('You are successfully log in. Now you can order something !', 'success')
                return redirect(url_for('home'))
            else:
                flash('Please check your id or password again. !', 'danger')
    return render_template("loginForRestaurant.html")

@app.route("/shopping-cart",methods=['POST','GET'])
def shoppingCart():
    shopping_cart = current_user.shopping_cart[0] if current_user.shopping_cart else None

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

    return render_template("shopping_cart.html",shoppingCart= products_in_cart,total_price=total_price)

@app.route("/orders")
@login_required
def my_orders():
    user = current_user

    orders = Order.query.filter_by(user_id=user.id).all()

    return render_template("orders.html", orders=orders)

@app.route("/restaurant/<int:restaurant_id>", methods=['POST', 'GET'])
def restaurant_page(restaurant_id):
    restaurant = Restaurant.query.get(restaurant_id)
    categories = set(product.category for product in restaurant.products)
    selected_category = request.args.get('category', None)

    if selected_category:
        filtered_products = [product for product in restaurant.products if product.category == selected_category]
    else:
        filtered_products = restaurant.products

    return render_template("restaurant.html", restaurant=restaurant, categories=categories, selected_category=selected_category, products=filtered_products)


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

    if not user.shopping_cart:
        shopping_cart = ShoppingCart(user=user)
        db.session.add(shopping_cart)
        db.session.commit()
    else:
        shopping_cart = user.shopping_cart[0] if user.shopping_cart else None

    itemAlready = ShoppingCartProduct.query.filter_by(shopping_cart_id=shopping_cart.id, product_id=product_id).first()

    product = Product.query.get(product_id)  

    if itemAlready:
        itemAlready.quantity += 1
    else:
        itemAlready = ShoppingCartProduct(shopping_cart_id=shopping_cart.id, product_id=product_id, quantity=1, restaurant_id=product.restaurant_id)
        db.session.add(itemAlready)

    product_restaurant_id = product.restaurant_id
    itemAlready.restaurant_id = product_restaurant_id

    db.session.commit()
    flash('The product has been added to the cart!', 'success')
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
            flash('Product quantity reduced!', 'success')
        else:
            flash('Product is not in your cart!', 'danger')
    else:
        flash('Your shopping cart is empty or not defined.', 'danger')


    return redirect(url_for('shoppingCart'))

@app.route("/increment_quantity/<int:product_id>", methods=['POST', 'GET'])
@login_required
def increment_quantity(product_id):

    user = current_user
    shopping_cart = user.shopping_cart[0] if user.shopping_cart else None

    if shopping_cart:
        cart_product = ShoppingCartProduct.query.filter_by(shopping_cart_id=shopping_cart.id, product_id=product_id).first()

        if cart_product:
            cart_product.quantity += 1

            db.session.commit()
            flash('Product quantity increased!', 'success')
        else:
            flash('Product is not in your cart!', 'danger')
    else:
        flash('Your shopping cart is empty or not defined.', 'danger')


    return redirect(url_for('shoppingCart'))

@app.route("/place_order", methods=['POST', 'GET'])
@login_required
def place_order():
    user = current_user
    shopping_cart = user.shopping_cart[0] if user.shopping_cart else None
    shopping_cart_product = ShoppingCartProduct.query.filter_by(shopping_cart_id=shopping_cart.id).first()

    if is_restaurant_open(shopping_cart_product.restaurant_id):
        if shopping_cart:
            if shopping_cart.quantities.count() > 0:
                order = Order(user_id=user.id, order_date=datetime.utcnow(), total_amount=calculate_total(shopping_cart))

                for cart_product in shopping_cart.quantities:
                    product = Product.query.get(cart_product.product_id)
                    order_product = OrderProduct(product_id=product.id, quantity=cart_product.quantity)
                    order.quantities.append(order_product)

                order.restaurant_id = shopping_cart_product.restaurant_id
                order_note = request.form.get('order_note')
                order.note = order_note
                db.session.add(order)
                db.session.commit()

                clear_shopping_cart(shopping_cart)

                flash('Your order has been received!', 'success')
                return redirect(url_for('home'))

    flash('The restaurant is already closed. Sorry :(', 'danger')
    return redirect(url_for('shoppingCart'))


def is_restaurant_open(restaurantId):
    restaurant = Restaurant.query.filter_by(id=restaurantId).first()
    current_time = datetime.now().time()
    opening_time = restaurant.opening_hour
    closing_time = restaurant.closing_hour
    return opening_time <= current_time <= closing_time


@app.route("/restaurant-orders")
@login_required
def restaurant_orders():
    if not current_user.is_user:
        restaurant = Restaurant.query.get(current_user.id)

        orders = Order.query.filter_by(restaurant_id=current_user.id).all()

        return render_template("restaurant_orders.html", restaurant=restaurant, orders=orders)
    else:
        flash('Access denied. You are not a restaurant user.', 'danger')
        return redirect(url_for('home'))

def calculate_total(shopping_cart):
    total = 0
    for cart_product in shopping_cart.quantities:
        product = Product.query.get(cart_product.product_id)
        total += product.price * cart_product.quantity
    return total

def clear_shopping_cart(shopping_cart):
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
            category = request.form.get("category")  
            description = request.form["description"]  

            if 'product_photo' in request.files:
                file = request.files['product_photo']

                if file:
                    upload_folder = 'uploads'
                    
                    if not os.path.exists(upload_folder):
                        os.makedirs(upload_folder)

                    file_path = os.path.join(upload_folder, file.filename)
                    file.save(file_path)

            file_path = file_path.replace('\\', '/')
            new_product = Product(name=product_name, price=price, restaurant_id=current_user.id, category=category, photo_path=file_path,description=description)
            db.session.add(new_product)
            db.session.commit()
        elif "add_plz" in request.form:
            plz = request.form["add_plz"]
            restaurant.add_plz(plz)
            db.session.commit()

    plz_list = restaurant.get_plz()
    products = Product.query.filter_by(restaurant_id=current_user.id)
    return render_template("my_restaurant.html",restaurant=restaurant,products=products,plz_list=plz_list)

@app.route("/change-order-status/<int:order_id>", methods=['POST'])
@login_required
def change_order_status(order_id):
    if not current_user.is_user:
        order = Order.query.get(order_id)

        if order and order.restaurant_id == current_user.id:
            new_status = request.form.get('status')
            order.status = new_status
            db.session.commit()
            flash(f'Order status changed to: {new_status}', 'success')
        else:
            flash('You are not authorized to update this order.', 'danger')
    else:
        flash('Access denied. You are not a restaurant user.', 'danger')

    return redirect(url_for('restaurant_orders'))


@app.route("/delete_product/<int:product_id>", methods=['POST'])
@login_required
def delete_product(product_id):
    if not current_user.is_user:
        product_to_delete = Product.query.get(product_id)

        if product_to_delete and product_to_delete.restaurant_id == current_user.id:
            db.session.delete(product_to_delete)
            db.session.commit()
            flash('Product deleted successfully!', 'success')
        else:
            flash('You are not authorized to delete this product.', 'danger')
    else:
        flash('Access denied. You are not a restaurant user.', 'danger')

    return redirect(url_for('my_restaurant'))


@app.route("/update_product/<int:product_id>", methods=['POST'])
@login_required
def update_product(product_id):
    if not current_user.is_user:
        updatedP = Product.query.get(product_id)

        if updatedP and updatedP.restaurant_id == current_user.id:
            updatedP.name = request.form["updated_product_name"]
            updatedP.price = request.form["updated_price"]
            updatedP.category = request.form["updated_category"]
            updatedP.description = request.form["updated_description"]

            db.session.commit()
            flash('Product updated successfully!', 'success')
        else:
            flash('You are not authorized to update this product.', 'danger')
    else:
        flash('Access denied. You are not a restaurant user.', 'danger')

    return redirect(url_for('my_restaurant'))

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