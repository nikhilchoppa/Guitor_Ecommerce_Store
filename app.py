from flask import Flask, render_template, request, redirect, flash
from flaskext.mysql import MySQL

app = Flask(__name__, static_folder='styles')

app.config['MYSQL_DATABASE_HOST'] = 'final-db-205.cwokmtfympzg.us-east-1.rds.amazonaws.com'
app.config['MYSQL_DATABASE_USER'] = 'admin205'
app.config['MYSQL_DATABASE_PASSWORD'] = 'software'
app.config['MYSQL_DATABASE_DB'] = 'mktdata'
mysql = MySQL(app)
mysql.init_app(app)

#User class to store information about active user
class User:
    def __init__(self, is_logged_in, id):
        self.is_logged_in = is_logged_in
        self.id = id

#create global instance of class for client
active_user = User(False, None)

def data():
    cur = mysql.get_db().cursor()
    cur.execute("DROP TABLE CART_ITEM")
    cur.execute("DROP TABLE CART")
    cur.execute("DROP TABLE GUITAR")
    cur.execute("DROP TABLE COMPANY")
    cur.execute("DROP TABLE USER")
    cur.execute("CREATE TABLE COMPANY(ID INT, Name VARCHAR(150), PRIMARY KEY (ID))")
    cur.execute("CREATE TABLE GUITAR(ID INT, Name VARCHAR(150), Picture VARCHAR(150), Description VARCHAR(150), Price DECIMAL(7, 2), companyID INT, PRIMARY KEY (ID),FOREIGN KEY (companyID) REFERENCES COMPANY(ID))")
    cur.execute("CREATE TABLE USER(ID INT, FName VARCHAR(150), LName VARCHAR(150), Username VARCHAR(150), Password VARCHAR(150), Balance DECIMAL(7,2), PRIMARY KEY (ID))")
    cur.execute("CREATE TABLE CART(ID INT NOT NULL, User_ID INT, Date_made DATE, PRIMARY KEY (ID), FOREIGN KEY (User_ID) REFERENCES USER(ID))")
    cur.execute("CREATE TABLE CART_ITEM(ID INT NOT NULL, Item_ID INT, Quantity INT, Date_made DATE, Cart_ID INT, PRIMARY KEY (ID), FOREIGN KEY (Item_ID) REFERENCES GUITAR(ID), FOREIGN KEY (Cart_ID) REFERENCES CART(ID))")



    # cur.execute("CREATE TABLE PURCHASE(ID INT, User_ID INT, User_balance DECIMAL(7,2), Item_ID INT, PRIMARY KEY (ID))")

    fd = open('SQL/start_data.sql', 'r')
    sqlFile = fd.read()
    fd.close()
    sqlCommands = sqlFile.split(';')
    for i in sqlCommands:
        i = i.strip('\n')
        try:
            cur.execute(i)
            print(i)
            # print(i)
        except:
            print("")
    mysql.get_db().commit()
    cur.close()

@app.route('/login', methods=['GET', 'POST'])
@app.route('/templates/login.html', methods=['GET', 'POST'])
def login():
    return render_template('login.html')

@app.route('/checklogin', methods=['GET', 'POST'])
def checklogin():
    #query for username and password from USERS
    #if credentials pass, render index
    #else if username doesn't exist

    if request.method == "POST":
        # getting input from name tag HTML form
        username = request.form.get("name")
        password = request.form.get("password")
        cur = mysql.get_db().cursor()
        try:
            cur.execute("SELECT Username, Password FROM USER WHERE Username = %s AND Password = %s", (username, password))

            if not cur.fetchone():
                print('error')
                error_message = "Invalid credentials. Try again or register to proceed."
                return render_template('login.html', message = error_message)
            else:
                # successful login - get id and update active_user
                cur.execute("SELECT ID FROM USER WHERE Username = %s", (username))
                id_for_active_user = cur.fetchall()
                print("id for active user follows: ")
                print(id_for_active_user[0][0])

                active_user.is_logged_in = True
                active_user.id = id_for_active_user

                return render_template('index.html')

        except:
            print('doesnt exist \n')
            # return render_template('index.html')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
@app.route('/templates/register.html', methods=['GET', 'POST'])
def register():
    return render_template('register.html')

@app.route('/registeruser', methods=['GET', 'POST'])
def registeruser():
    if request.method == "POST":
        # getting input from name tag HTML form
        username = request.form.get("name")
        password = request.form.get("password")
        cur = mysql.get_db().cursor()
        cur.execute("SELECT * FROM CART")
        print(cur.fetchall())
        try:
                #get the last userid
            cur.execute("SELECT ID FROM USER")
            last_id = cur.fetchall()
            for i in last_id:
                final_id = int(i[-1]) + 1
            print(final_id)

                #see if new username is in the db already
            cur.execute("SELECT Username FROM USER WHERE Username = %s", username)
            if not cur.fetchone():
                #username is unique - create account
                print('not in db')
                cur.execute("INSERT INTO USER (Username,Password, ID) VALUES (%s, %s, %s)", (username, password, final_id))
                cur.execute("INSERT INTO CART (ID,User_ID) VALUES (%s, %s)", (final_id,final_id))
                mysql.get_db().commit()

                #update active_user
                active_user.is_logged_in = True
                active_user.id = final_id

                account_created_message = "Account has been saved. "
                return render_template('index.html', message = account_created_message)
            else:
                #username is already in database
                print('in DB')
                failed_to_register = "Username already exists in databse. Enter new username or log in"
                return render_template('register.html', message = failed_to_register)
        except Exception:
            print('error')
            error_message = "Error"
            return render_template('register.html', message = error_message)

    #query to make sure username doesn't already exist
    #if username does not already exist, place new username and pass into database, redirect to index
    #if it does exist
    return render_template('index.html')

@app.route('/', methods=['GET', 'POST'])
@app.route('/templates/index.html', methods=['GET', 'POST'])
def origin():
    # data()
    #check if user is logged in. if so, direct to index, if not, redirect to login
    return render_template('index.html')

#we should move this code to a new function getProduct()
@app.route('/shop', methods=['GET', 'POST'])
@app.route('/templates/shop.html', methods=['GET', 'POST'])
def shop():
    cur = mysql.get_db().cursor()

    cur.execute("SELECT ID, Name, Price, Picture FROM GUITAR")
    products = cur.fetchall()

    #nested dictionary. Outer for each product, inner for products' keys and values
    products_dictionary = {}
    item_index = 1
    i = 0
    for elem in products:
       products_dictionary.update({
           item_index: {'id': products[i][0], 'title': products[i][1], 'price': products[i][2], 'image': products[i][3]}
        })
       item_index += 1
       i += 1

    #print(products_dictionary)
    return render_template('shop.html', products = products_dictionary)

@app.route('/loadproduct', methods=['GET', 'POST'])
def load_product_page():
    product_id = request.args.get('id')

    cur = mysql.get_db().cursor()
    cur.execute('SELECT ID, Name, Price, Picture, Description FROM GUITAR WHERE ID = "{}"'.format(product_id))
    product = cur.fetchall()

    #i'm a bit confused with the indexing here. will look into later
    #i would think 'product[0]' would return id, but it holds the whole dict
    product_dictionary = {'id': product[0][0], 'title': product[0][1], 'price': product[0][2],
                         'image': product[0][3], 'desc': product[0][4]}

    return render_template('product.html', product = product_dictionary)

@app.route('/product', methods=['GET', 'POST'])
@app.route('/templates/product.html', methods=['GET', 'POST'])
def product():
    return render_template('product.html')

@app.route('/cart', methods=['GET', 'POST'])
@app.route('/templates/cart.html', methods=['GET', 'POST'])
def cart():
    #initialize mysql cursor
    cur = mysql.get_db().cursor()


    #check if user is logged in
    if not active_user.is_logged_in:
        #user is not logged in, redirect to previous page
        error_message = "You need to be logged in to have a cart. Please log in or create an account. "
        print(error_message)
        return redirect(request.referrer)


    #query for all the items in cart
    cur.execute("SELECT * FROM CART_ITEM JOIN CART ON CART.ID = CART_ID WHERE CART.User_ID = %s", (active_user.id))

    items = cur.fetchall()
    print(items)

    # nested dictionary. Outer for each product, inner for products' keys and values
    cart_items_dictionary = {}
    item_index = 1
    i = 0
    for item in items:
        cart_items_dictionary.update({
            item_index: {'id': items[i][0], 'title': items[i][1], 'price': items[i][2],
                         'image': items[i][3]}
        })
        item_index += 1
        i += 1

    # print(cart_items_dictionary)
    return render_template('cart.html', items=cart_items_dictionary)#return item details in items, and total price for subtotal

@app.route('/addtocart', methods=['GET', 'POST'])
def add_to_cart():
    print("add to cart function running ... ")
    product_id = request.args.get('product_id')
    print(product_id)

    # check if user is logged in
    if not active_user.is_logged_in:
        # user is not logged in, redirect to previous page
        error_message = "You need to be logged in to add to cart. Please log in or create an account. "
        print(error_message)
        return redirect(request.referrer)

    # user is logged in
    # initialize mysql cursor
    cur = mysql.get_db().cursor()


    #generate new id
    cur.execute("SELECT ID FROM USER")
    last_id = cur.fetchall()
    for i in last_id:
        final_id = int(i[-1])
    print(final_id)
    # check if user has cart
    #user_cart = cur.fetchall()
    #if user does not have cart:
        #create cart for user
    cur.execute('SELECT * FROM CART WHERE User_ID = (%s)', (active_user.id))
    if not cur.fetchone():
        cur.execute('SELECT ID FROM CART WHERE ID = (%s)', (final_id))
        if not cur.fetchone():
            cur.execute("INSERT INTO CART (ID,User_ID) VALUES (%s, %s)", (final_id, final_id))

    # cart exists - add item to cart
    # cur.execute("INSERT INTO CART_ITEM ...)
    else:
        # generate new id
        cur.execute("SELECT ID FROM CART_ITEM")
        last_id2 = cur.fetchall()
        for a in last_id2:
            final_id2 = int(a[-1]) + 1
        print(final_id2)

        # #check to make sure it isn't in table
        cur.execute('SELECT * FROM CART_ITEM WHERE ID = (%s)', (final_id2))
        if not cur.fetchone():
            cur.execute("INSERT INTO CART_ITEM (ID, Item_ID, Quantity, Cart_ID) VALUES (%s, %s, %s, %s)", (final_id2,product_id,1,final_id))

        else:
            print('already in table')

    mysql.get_db().commit()
    added_to_cart_message = "Item has been added to cart. "
    return render_template('index.html', message = added_to_cart_message)

@app.route('/removefromcart', methods=['GET', 'POST'])
def remove_from_cart():
    return render_template('/')

@app.route('/templates/about.html', methods=['GET', 'POST'])
@app.route('/about', methods=['GET', 'POST'])
def about():
    return render_template('about.html')


@app.route('/templates/purchased.html', methods=['GET', 'POST'])
def purchase():
    #query to check if any items are in user's cart before rendering purchased page
    return render_template('purchased.html')

@app.route('/product.html', methods=['GET', 'POST'])
def product2():
    return render_template('purchased.html')

@app.route('/query', methods=['GET', 'POST'])
def query():
    cur = mysql.get_db().cursor()
    # cur.execute("SELECT Name FROM GUITAR")
    # Name = cur.fetchall()
    # cur.execute("SELECT Price FROM GUITAR")
    # Price = cur.fetchone()
    # cur.execute("SELECT Description FROM GUITAR")
    # Desc = cur.fetchall()
    # cur.execute("SELECT * FROM CART_ITEM JOIN CART ON CART.ID = CART_ID WHERE CART.User_ID = %s", (123456791))
    cur.execute("SELECT * FROM CART")
    print(cur.fetchall())
    # cur.execute("SELECT * FROM CART_ITEM")
    # print(cur.fetchall())
    # for i in Price:
    #     print(i)
    return render_template('querytest.html')#, random_quote=Desc)


if __name__ == '__main__':
    # runs the simple app
    app.run()
