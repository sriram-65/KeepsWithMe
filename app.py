#KEEPSWITHME 
from flask import Flask , render_template , request , redirect , jsonify , session , url_for
from pymongo import MongoClient
from werkzeug.security import generate_password_hash , check_password_hash
import datetime
from bson.objectid import ObjectId
from flask_mail import Mail , Message
import uuid

app = Flask(__name__)


app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'sriram65raja@gmail.com'
app.config['MAIL_PASSWORD'] = 'akio rluw wwup kfbc'  
app.config['MAIL_DEFAULT_SENDER'] = 'sriram65raja@gmail.com'

mail = Mail(app)


app.secret_key = "@Keepswithme1324fromIndia"

client = MongoClient("mongodb+srv://sriram65raja:1324sriram@cluster0.lhsvjbx.mongodb.net/")
DB = client["mmhss"]
Users_Register_KEEPSWITHME = DB["Users_Register_KEEPSWITHME"]
User_Selected = DB["User_Selected"]
USER_NOTES = DB["USER_NOTES"]
TRASH = DB['TRASH']
RESET_TOKEN = DB["RESET_TOKEN"]

@app.route("/")
def home():
    if not session.get("id"):
        return render_template("index.html")
    
    return redirect("/dash")

@app.route("/register" , methods=["POST" , "GET"])
def Register():
    if request.method == "POST":
        
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        hass_pw = generate_password_hash(password)
        
        if Users_Register_KEEPSWITHME.find_one({"email":email}):
            return render_template("register.html" , err="Email Id Already Exits")
        
        DATA = {
            "name":name,
            "email":email,
            "password":hass_pw , 
            "UserCreated_at":datetime.datetime.utcnow()
        }
        
        Users_Register_KEEPSWITHME.insert_one(DATA)
        return redirect("/login")
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("id"):
        return redirect("/dash")

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        user = Users_Register_KEEPSWITHME.find_one({"email": email})
        if not user:
             return render_template("login.html" , err="Wrong Email")

        if not check_password_hash(user["password"], password):
             return render_template("login.html" , err="Password Wrong ")

        session["id"] = str(user["_id"])
        session["email"] = user["email"]
     
        return redirect("/dash")
                
    return render_template("login.html")
    


@app.route("/dash")
def dash():
    if not session.get("id"):
       return redirect("/")
   
    userid = session.get("id")
    
    user = Users_Register_KEEPSWITHME.find_one({"_id":ObjectId(userid)})
    
    existing_data = User_Selected.find_one({"user_email": user["email"]})
    
    show_form = None
    
    if existing_data is None:
        show_form = True
    else:
        show_form = False
    
    User_notes = list(USER_NOTES.find({"Email":session.get("email")}).sort("_id" , -1))
    return render_template("dash.html" , username=user["name"] , show_form = show_form , Notes=User_notes ) 
   

@app.route("/select" , methods=["POST"])
def select():
    yes = request.form.get("yes")
    search = request.form.get("search")
    server = request.form.get("server")
    
    user = Users_Register_KEEPSWITHME.find_one({"_id":ObjectId(session.get("id"))})
    DATA = {
        "username":user["name"],
        "user_email":user["email"],
        "USER_use_AI":yes,
        "User_Hear_about":search,
        "User_Selected_Server_Region":server
    }
    User_Selected.insert_one(DATA)
    return redirect("/dash")


@app.route("/take-notes")
def take_notes():
    user = Users_Register_KEEPSWITHME.find_one({"_id":ObjectId(session.get("id"))})
    return render_template("take-notes.html" , username=user["name"])

@app.route("/takeanotes" , methods=["POST"])
def upload_notes():
    title = request.form.get("title")
    content = request.form.get("content")
    user = Users_Register_KEEPSWITHME.find_one({"_id":ObjectId(session.get("id"))})
    DATA = {
        "username":user["name"],
        "Email":user["email"],
        "title":title,
        "content":content,
        "Created_at":datetime.datetime.now()
    }
    USER_NOTES.insert_one(DATA)
    return redirect("/")


@app.route("/logout")
def log_out():
    session.clear()
    return redirect("/")

@app.route("/profile")
def profile():
    number = USER_NOTES.count_documents({"Email":session.get("email")})
    user_info = Users_Register_KEEPSWITHME.find_one({"email":session.get("email")})
    trash_notes = TRASH.find({"Email":session.get("email")})
    
    return render_template("profile.html" , notes_per_user = number , user_info=user_info , t_notes = trash_notes)

@app.route("/view-note/<Notes_id>" , methods=["GET"])
def View_Notes(Notes_id):
    Notes = USER_NOTES.find_one({"_id":ObjectId(Notes_id)})
    return render_template("view.html" , N = Notes)

@app.route("/update-note/<note_id>" , methods=["POST"])
def update_note(note_id):
    title = request.form.get("title")
    content = request.form.get("content")
    color = request.form.get("color")
    USER_NOTES.find_one_and_update({"_id":ObjectId(note_id)} , {"$set":{
        "title":title,
        "content":content,
        
    }})
    return redirect("/dash")

@app.route("/del/<note_id>" , methods=["POST"])
def del_note(note_id):
    notes = USER_NOTES.find_one({"_id":ObjectId(note_id)})
    if notes:
        TRASH.insert_one(notes)
        USER_NOTES.find_one_and_delete({"_id":ObjectId(note_id)})
        return redirect("/")
    return jsonify("NOTE NOT FOUND") , 404


@app.route("/Auth/user/for-got-pass-word" , methods=["POST" , "GET"])
def for_got():
    if request.method == "POST":
        email = request.form.get("email")
        user = Users_Register_KEEPSWITHME.find_one({"email":email})
        if not user:
            return render_template("forgot.html" , err="User Not Found")
        
        token = str(uuid.uuid4())
        expriy_date = datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        DATA = {
            "email":email,
            "token":token,
            "ex":expriy_date
        }
        RESET_TOKEN.insert_one(DATA)
        link = url_for("reset_token" , token=token , _external=True)
        msg = Message(
            subject="Reset Your Password - KeepsWithMe",
            recipients=[email],
            body=f"Click the link to reset your password:\n{link}\n\nThis link expires in 30 minutes."
        )
        mail.send(msg)
        return "Password reset link sent to your email."
    return render_template("forgot.html")

@app.route("/Auth/user/reset-password/<token>" , methods=["POST" , "GET"])
def reset_token(token):
    token_data = RESET_TOKEN.find_one({"token":token})
    if not token_data:
        return render_template("err.html" , err="Invalid Token")
    
    if datetime.datetime.utcnow() > token_data["ex"]:
        return render_template("err.html" , err="Token Experid")
    
    if request.method == "POST":
        new_pw = request.form.get("new_pw")
        hased_pw = generate_password_hash(new_pw)
        
        Users_Register_KEEPSWITHME.find_one_and_update({"email":token_data["email"]} , {"$set":{
            "password":hased_pw
        }})
        
        RESET_TOKEN.delete_one({"token":token})
        return redirect("/login")
    return render_template("reset-password.html")


if __name__ == "__main__":
    app.run(debug=True)