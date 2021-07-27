from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_wtf import Form
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, DateField, SelectMultipleField
from wtforms.validators import DataRequired, Email
from wtforms.fields.html5 import EmailField
from wtforms.widgets import TextArea
from flask_pymongo import pymongo
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Cant_say'

class inputForm(Form):
    fname = StringField('fname', validators=[DataRequired()])
    lname = StringField('lname', validators=[DataRequired()])
    email = EmailField('email', validators=[DataRequired(), Email()])
    pass1 = PasswordField('pass1', validators=[DataRequired()])
    sub = SubmitField('Sign Up')

class inputFormlogin(Form):
    email = EmailField('email', validators=[DataRequired(), Email()])
    pass1 = PasswordField('pass1', validators=[DataRequired()])
    sub = SubmitField('Login')

class AddForm(Form):
    store = StringField('store', validators=[DataRequired()])
    code = StringField('code', validators=[DataRequired()])
    valid_upto = DateField('valid_upto', validators=[DataRequired()])
    valid_for = SelectMultipleField('valid_for', choices=[('Mobile', 'Mobile'), ('Footwear', 'Footwear'), ('Clothes', 'Clothes'), ('Pantry', 'Pantry'), ('Electronics', 'Electronics')],validators=[DataRequired()])
    additional = StringField('additional', widget=TextArea())
    sub = SubmitField('Add Coupon')

db_password = "pizza"# input("Password for database is:")
CONNECTION_STRING = f"mongodb+srv://VIT_Admin:{db_password}@vitdiaries.tpuku.mongodb.net/CouponShare?retryWrites=true&w=majority"
client = pymongo.MongoClient(CONNECTION_STRING)
db = client.get_database('CouponShare')
user_collection = pymongo.collection.Collection(db, 'Users')
code_collection = pymongo.collection.Collection(db, 'CouponCodes')


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    form = inputForm()
    if request.method=="POST":
        fname = form.fname.data
        lname = form.lname.data
        email = form.email.data
        pass1 = form.pass1.data
        print(fname, lname, email, pass1)
        if request.method == 'POST':
            if user_collection.count_documents({"Email": email}):
                flash('User already Exists!, Please login')
                return redirect(url_for('login'))
            else:
                cipher = generate_password_hash(pass1, method='sha256')
                user_collection.insert_one({'First Name': fname, 'Last Name': lname, 'Email': email, 'Password': cipher, 'Coupon_Redemptions' : 1})
                session['email'] = email
                return render_template('index.html', fname = fname, lname = lname, Coupon_Redemptions = 1)
        else:
            return redirect('signup')
    return render_template("signup.html", form=form)

@app.route('/login', methods=['POST', 'GET'])
def login():
    form_login = inputFormlogin()
    if request.method=="POST":
        email = form_login.email.data
        pass1 = form_login.pass1.data
        if request.method == 'POST':
            user = user_collection.find_one({"Email":email})
            if user == None:
                print("item does not exist")
                flash('User Does not Exist, Please Sign Up.')
                return redirect('/signup')

            if check_password_hash(user['Password'], pass1):
                print("item exists")
                session['email'] = email
                # Coupon_Redemptions = user['Coupon_Redemptions']
                # fname = user['First Name']
                return redirect(url_for('home'))
            else:
                print("Invalid Credentials")
                flash('Invalid Credentials')
                return redirect('/login')
    return render_template("login.html", form_login=form_login)

@app.route('/home')
def home():
    if 'email' in session:
        codes_all = code_collection.find()
        email = session['email']
        user = user_collection.find_one({"Email":email})
        return render_template('index.html', fname = user['First Name'], codes_all=codes_all, Coupon_Redemptions= user['Coupon_Redemptions'])
    else:
        return redirect(url_for('login'))

@app.route('/')
def landing():
    return render_template('landing.html')

@app.route('/about_us')
def About_us():
    return render_template('about_us.html')

@app.route('/contact')
def Contact():
    return render_template('contact.html')

@app.route('/logout')
def logout():
    if 'email' in session:
        session.pop('email', None)
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/about')
def about():
    if 'email' in session:
        email = session['email']
        user = user_collection.find_one({"Email":email})
        return render_template('about.html', fname=user['First Name'], Coupon_Redemptions=user['Coupon_Redemptions'])
    else:
        return redirect(url_for('login'))
        
@app.route('/add', methods=['POST', 'GET'])
def add():
    add_form = AddForm()
    if 'email' in session:
        email = session['email']
        user = user_collection.find_one({"Email":email})
        if request.method == "POST":
            store = add_form.store.data
            code = add_form.code.data
            valid_upto = add_form.valid_upto.data
            additional = add_form.additional.data
            valid_for = request.form.getlist('valid_for')
            now = datetime.date.today()
            now = now.strftime("%d/%m/%Y")
            print(store, code, valid_upto, additional, valid_for)
            if request.method=="POST":
                list1 = str(valid_upto).split("-")
                myDateObject = datetime.datetime(int(list1[0]),int(list1[1]),int(list1[2]))
                myDateObject = myDateObject.strftime('%d/%m/%Y')
                code_collection.insert_one({"Email":email, "Store":store, "Code":code, "Valid_Upto":myDateObject, "Added_By": (user['First Name']+" "+user['Last Name']), "Valid_For": valid_for, "Additional_Details": additional, "Used": 0, "Added_On":now})
                user = user_collection.find_one({"Email":session['email']})
                user['Coupon_Redemptions'] += 1
                user_collection.update_one({"Email":email},{"$set": {"Coupon_Redemptions" : user['Coupon_Redemptions']}});
                return redirect(url_for('home'))
            else:
                return redirect(url_for('login'))
        return render_template('add.html', add_form = add_form, fname=user['First Name'], Coupon_Redemptions=user['Coupon_Redemptions'])
    else:
        return redirect(url_for('login'))

@app.route('/CouponUsed')
def CouponUsed():
    if 'email' in session:
        user = user_collection.find_one({"Email":session['email']})
        email = session['email']
        user['Coupon_Redemptions'] -= 1
        if user['Coupon_Redemptions'] <= 0:
            user['Coupon_Redemptions'] = 0
            user_collection.update_one({"Email":email},{"$set": {"Coupon_Redemptions" : user['Coupon_Redemptions']}});
            flash('You need to add more coupons to get Coupon Redemption Points!')
        else:
            user_collection.update_one({"Email":email},{"$set": {"Coupon_Redemptions" : user['Coupon_Redemptions']}});
            flash('You have used a Coupon Redemption Point')
    else:
        return redirect(url_for('login'))
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
