from flask import Flask, render_template, request, jsonify
import re
import random
from flask import (
    Flask,
    Response,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    jsonify,
)
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, validators
import numpy as np
import cv2

app = Flask(__name__)
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SECRET_KEY"] = "your_secret_key"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)


class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    message = db.Column(db.String(500), nullable=False)


class ContactForm(FlaskForm):
    name = StringField("Name", [validators.Length(min=1, max=50)])
    email = StringField("Email", [validators.Length(min=6, max=50)])
    message = StringField("Message", [validators.Length(min=1, max=500)])
    submit = SubmitField("Submit")


# Create the database tables
with app.app_context():
    db.create_all()


class RegistrationForm(FlaskForm):
    username = StringField("Username", [validators.Length(min=4, max=25)])
    password = PasswordField(
        "Password",
        [
            validators.DataRequired(),
            validators.EqualTo("confirm", message="Passwords must match"),
        ],
    )
    confirm = PasswordField("Repeat Password")
    submit = SubmitField("Register")


class LoginForm(FlaskForm):
    username = StringField("Username", [validators.Length(min=4, max=25)])
    password = PasswordField("Password", [validators.DataRequired()])
    submit = SubmitField("Login")


@app.route("/home")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()

    if form.validate_on_submit():
        new_user = User(username=form.username.data, password=form.password.data)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for("login"))

    return render_template("register.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            username=form.username.data, password=form.password.data
        ).first()

        if user:
            # Redirect to the desired page after successful login
            return redirect(url_for("home"))
        else:
            return "Invalid login credentials"

    return render_template("login.html", form=form)


@app.route("/users")
def display_users():
    users = User.query.all()
    return render_template("users.html", users=users)


intents_data = {
    "intents": [
        {
            "tag": "natural_disasters_greetings",
            "patterns": [
                "hello",
                "hey",
                "hi",
                "good day",
                "greetings",
                "what's up?",
                "how is it going?",
            ],
            "responses": [
                "Hello! How can I assist you with information about natural disasters?",
                "Hey there! Interested in learning about earthquakes, floods, droughts, or landslides?",
                "Hi! Ready to explore information on natural disasters. What do you have in mind?",
                "Good day! If you have any questions about earthquakes, floods, droughts, or landslides, feel free to ask.",
                "Greetings! I'm here to provide information on natural disasters. What can I help you with?",
                "What's up? Interested in staying informed about natural disasters like earthquakes, floods, droughts, or landslides?",
                "How is it going? Curious about the latest updates on earthquakes, floods, droughts, or landslides?",
            ],
        },
        {
            "tag": "drought_info",
            "patterns": [
                "Tell me about droughts",
                "What is a drought?",
                "Drought facts",
                "Explain dry spells",
                "How do droughts occur?",
                "Give me drought information",
            ],
            "responses": [
                "A drought is an extended period of deficient rainfall relative to the statistical multi-year usual amount for a region.",
                "Droughts can result from a lack of precipitation, high temperatures, and increased evaporation.",
                "Dry spells can lead to water shortages, affecting agriculture, ecosystems, and communities.",
                "During droughts, water resources become scarce, impacting agriculture, water supply, and ecosystems.",
                "If you have specific questions about droughts or need information on current drought conditions, feel free to ask!",
            ],
        },
        {
            "tag": "landslide_info",
            "patterns": [
                "Tell me about landslides",
                "What is a landslide?",
                "Landslide facts",
                "Explain slope failures",
                "How do landslides happen?",
                "Give me landslide information",
            ],
            "responses": [
                "A landslide is the movement of rock, earth, or debris down a slope.",
                "Landslides can occur due to factors such as heavy rainfall, earthquakes, volcanic activity, or human activities.",
                "Slope failures can lead to the rapid downslope movement of material, posing risks to infrastructure and communities.",
                "Landslides can result in the loss of lives, damage to property, and disruption of transportation.",
                "If you have specific questions about landslides or need information on landslide-prone areas, feel free to ask!",
            ],
        },
        {
            "tag": "famine_info",
            "patterns": [
                "Tell me about famines",
                "What is a famine?",
                "Famine facts",
                "Explain food shortages",
                "How do famines occur?",
                "Give me famine information",
            ],
            "responses": [
                "A famine is an extreme scarcity of food in a particular geographic area or population.",
                "Famines can result from factors such as droughts, crop failures, conflicts, and economic instability.",
                "Food shortages during famines can lead to malnutrition, disease, and loss of life.",
                "Famines often require humanitarian aid to alleviate suffering and address food security issues.",
                "If you have specific questions about famines or need information on current food security issues, feel free to ask!",
            ],
        },
        {
            "tag": "earthquake_info",
            "patterns": [
                "Tell me about earthquakes",
                "What is an earthquake?",
                "Earthquake facts",
                "Explain seismic activity",
                "How do earthquakes happen?",
                "Give me earthquake information",
            ],
            "responses": [
                "An earthquake is the shaking of the surface of the Earth resulting from a sudden release of energy in the Earth's lithosphere that creates seismic waves.",
                "Earthquakes are caused by the movement of tectonic plates beneath the Earth's surface. This movement can result in the release of energy in the form of seismic waves.",
                "Seismic activity is the term used to describe the vibrations and movements in the Earth's crust that lead to earthquakes.",
                "During an earthquake, stress that has accumulated along geological faults is suddenly released, causing the ground to shake.",
                "Did you know? The Richter scale is commonly used to measure the magnitude of earthquakes, indicating their size and intensity.",
                "If you have specific questions about earthquakes or need information on recent seismic activity, feel free to ask!",
            ],
        },
        {
            "tag": "flood_info",
            "patterns": [
                "Tell me about floods",
                "What is a flood?",
                "Flood facts",
                "Explain inundation",
                "How do floods happen?",
                "Give me flood information",
            ],
            "responses": [
                "A flood is an overflow of water that submerges land and usually occurs due to heavy rainfall or rapid snowmelt.",
                "Floods can result in the inundation of low-lying areas, leading to property damage and displacement of communities.",
                "Inundation during floods can pose risks to human safety, agriculture, and infrastructure.",
                "Floods can be categorized as river floods, flash floods, coastal floods, and urban floods.",
                "If you have specific questions about floods or need information on flood-prone areas, feel free to ask!",
            ],
        },
        {
            "tag": "hailstorm_info",
            "patterns": [
                "Tell me about hailstorms",
                "What is a hailstorm?",
                "Hailstorm facts",
                "Explain hail formation",
                "How do hailstorms happen?",
                "Give me hailstorm information",
            ],
            "responses": [
                "A hailstorm is a weather phenomenon characterized by the falling of hailstones.",
                "Hailstones are formed when updrafts in thunderstorms carry raindrops into extremely cold areas of the atmosphere, causing them to freeze.",
                "Hailstorms can lead to damage to crops, vehicles, and structures due to the impact of hailstones.",
                "Hailstorm severity is often measured by the size and density of hailstones.",
                "If you have specific questions about hailstorms or need information on hailstorm-prone regions, feel free to ask!",
            ],
        },
        {
            "tag": "natural_disaster_help",
            "patterns": [
                "How can I help during a natural disaster?",
                "What can I do to assist in a disaster?",
                "How to provide aid during natural disasters?",
                "Ways to help in earthquakes, floods, droughts, and landslides",
                "Assistance options for disaster relief",
                "What actions can I take to support disaster victims?",
            ],
            "responses": [
                "During a natural disaster, you can help by donating to reputable relief organizations providing assistance on the ground.",
                "Consider volunteering your time and skills to organizations involved in disaster response and recovery efforts.",
                "Spread awareness about disaster preparedness and safety measures in your community.",
                "Offer shelter, food, and support to those affected by natural disasters in your local area.",
                "Stay informed about relief efforts and share verified information to combat misinformation during crises.",
                "Remember, every small contribution makes a difference in helping communities recover from natural disasters.",
            ],
        },
        {
            "tag": "government_schemes",
            "patterns": [
                "Tell me about government schemes",
                "What are the latest government initiatives?",
                "Government programs and schemes",
                "Can you provide information on public schemes?",
                "Details about welfare programs",
                "Any new government initiatives?",
            ],
            "responses": [
                "Government schemes are programs designed by the government to address specific social, economic, or environmental challenges.",
                "Some current government schemes include 'Pradhan Mantri Jan Dhan Yojana' for financial inclusion and 'Swachh Bharat Abhiyan' for sanitation.",
                "Welfare programs like 'Ayushman Bharat' aim to provide health coverage, while 'Skill India' focuses on skill development.",
                "Explore initiatives like 'Make in India' promoting manufacturing and 'Digital India' encouraging technology adoption.",
                "To stay updated on government schemes, visit official government websites or local government offices for detailed information.",
                "Government schemes play a crucial role in fostering development and improving the quality of life for citizens.",
            ],
        },
    ]
}


def get_intent_response(user_input):
    for intent in intents_data["intents"]:
        for pattern in intent["patterns"]:
            if re.search(pattern, user_input, re.IGNORECASE):
                return random.choice(intent["responses"])
    return "I'm sorry, I don't understand that question. Please ask something related to natural disasters or government schemes."


@app.route("/")
def index():
    return render_template("chat.html")


@app.route("/get_bot_response", methods=["POST"])
def get_bot_response():
    user_input = request.form["user_input"]
    bot_response = get_intent_response(user_input)
    return jsonify({"bot_response": bot_response})


if __name__ == "__main__":
    app.run(debug=True)
