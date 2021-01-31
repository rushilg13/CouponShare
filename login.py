from flask import Flask, render_template, request, redirect, url_for, flash
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
    added_by = StringField('added_by', validators=[DataRequired()])
    valid_for = SelectMultipleField('valid_for', choices=[('Mobile', 'Mobile'), ('Footwear', 'Footwear'), ('Clothes', 'Clothes')],validators=[DataRequired()])
    additional = StringField('additional', widget=TextArea())
    sub = SubmitField('Add Coupon')

db_password = input("Password for database is:")
CONNECTION_STRING = f"mongodb+srv://VIT_Admin:{db_password}@vitdiaries.tpuku.mongodb.net/CouponShare?retryWrites=true&w=majority"
client = pymongo.MongoClient(CONNECTION_STRING)
db = client.get_database('CouponShare')
user_collection = pymongo.collection.Collection(db, 'Users')
code_collection = pymongo.collection.Collection(db, 'CouponCodes')

logged_in = 0

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    form = inputForm()
    global logged_in
    global fname
    if request.method=="POST":
        fname = form.fname.data
        lname = form.lname.data
        email = form.email.data
        pass1 = form.pass1.data
        # print(fname, lname, email, pass1)
        if form.validate_on_submit():
            return("Submitted")
        else:
            if user_collection.count_documents({"Email": email}):
                logged_in = 0
                flash('User already Exists!, Please login')
                return redirect(url_for('signup'))

            else:
                logged_in = 1
                cipher = generate_password_hash(pass1, method='sha256')
                user_collection.insert_one({'First Name': fname, 'Last Name': lname, 'Email': email, 'Password': cipher, 'Coupon_Redemptions' : 1})
                return render_template('index.html', fname = fname, lname = lname, logged_in = logged_in, Coupon_Redemptions = 1)
    return render_template("signup.html", form=form)

@app.route('/login', methods=['POST', 'GET'])
def login():
    global logged_in
    global email
    logged_in = 0
    form_login = inputFormlogin()
    if request.method=="POST":
        email = form_login.email.data
        pass1 = form_login.pass1.data
        if form_login.validate_on_submit():
            return("Submitted")
        else:
            user = user_collection.find_one({"Email":email})
            if check_password_hash(user['Password'], pass1):
                print("item is existed")
                logged_in = 1
                global fname
                global Coupon_Redemptions
                Coupon_Redemptions = user['Coupon_Redemptions']
                fname = user['First Name']
                return redirect(url_for('home'))
            else:
                logged_in = 0
                print("item is not existed")
                flash('Invalid Credentials')
                return redirect('/login')
    return render_template("login.html", form_login=form_login)

@app.route('/home')
def home():
    global logged_in
    global fname
    global Coupon_Redemptions
    if logged_in == 1:
        codes_all = code_collection.find()
        return render_template('index.html', logged_in = logged_in, fname = fname, codes_all=codes_all, Coupon_Redemptions= Coupon_Redemptions)
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    global logged_in
    if logged_in == 1:
        logged_in = 0
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))

@app.route('/about')
def about():
    global logged_in
    global fname
    global Coupon_Redemptions
    if logged_in == 1:
        return render_template('about.html', fname=fname, logged_in = logged_in, Coupon_Redemptions=Coupon_Redemptions)
    else:
        return redirect(url_for('login'))
@app.route('/add', methods=['POST', 'GET'])
def add():
    global fname
    add_form = AddForm()
    global logged_in
    global Coupon_Redemptions
    if logged_in == 1:
        if request.method == "POST":
            store = add_form.store.data
            code = add_form.code.data
            valid_upto = add_form.valid_upto.data
            added_by = add_form.added_by.data
            additional = add_form.additional.data
            valid_for = request.form.getlist('valid_for')
            print(store, code, valid_upto, added_by, additional, valid_for)
            if add_form.validate_on_submit():
                return("Submitted")
            else:
                list1 = str(valid_upto).split("-")
                myDateObject = datetime.datetime(int(list1[0]),int(list1[1]),int(list1[2]), 0 , 0)
                code_collection.insert_one({"Email":email, "Store":store, "Code":code, "Valid_Upto":myDateObject, "Added_By": added_by, "Valid_For": valid_for, "Additional_Details": additional, "Not_Used": True})
                Coupon_Redemptions += 1
                user_collection.update_one({"Email":email},{"$set": {"Coupon_Redemptions" : Coupon_Redemptions}});
                return redirect(url_for('home'))
        return render_template('add.html', add_form = add_form, fname=fname, logged_in=logged_in, Coupon_Redemptions=Coupon_Redemptions)
    else:
        return redirect(url_for('login'))

@app.route('/CouponUsed')
def CouponUsed():
    global logged_in
    global Coupon_Redemptions
    global email
    if logged_in == 1:
        Coupon_Redemptions -= 1
        if Coupon_Redemptions <= 0:
            Coupon_Redemptions = 0
            user_collection.update_one({"Email":email},{"$set": {"Coupon_Redemptions" : Coupon_Redemptions, "Not_Used": True}});
            flash('You need to add more coupons to get Coupon_Redemption Points!')
        else:
            user_collection.update_one({"Email":email},{"$set": {"Coupon_Redemptions" : Coupon_Redemptions, "Not_Used": False}});
            flash('You have used a Coupon_Redemption Point')
    else:
        return redirect(url_for('login'))
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
