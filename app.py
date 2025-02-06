from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, send, emit
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS
import stripe
import datetime
from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Configuration Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tsra.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecret'
db = SQLAlchemy(app)
CORS(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
socketio = SocketIO(app, cors_allowed_origins="*")
@app.route("/")
def home():
    return "Hello, API is working!"
    
# Clé API Stripe (à remplacer par ta clé réelle)
stripe.api_key = "sk_test_votre_cle_secrete"

# Géolocalisation
geolocator = Nominatim(user_agent="tsra-secours")

# Modèle Bénévole (Admin)
class Benevole(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return Benevole.query.get(int(user_id))

# Modèle Urgence
class Urgence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    lieu = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    animal = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    statut = db.Column(db.String(50), default="En attente")

# WebSocket pour le chat en direct
@socketio.on('message')
def handle_message(data):
    emit('message', {"expediteur": data['expediteur'], "message": data['message'], "date": datetime.datetime.utcnow().strftime('%H:%M:%S')}, broadcast=True)

# Route pour récupérer les urgences
@app.route('/urgences', methods=['GET'])
def voir_urgences():
    urgences = Urgence.query.all()
    return jsonify([{
        "id": u.id, "nom": u.nom, "lieu": u.lieu, "latitude": u.latitude,
        "longitude": u.longitude, "animal": u.animal, "description": u.description, "statut": u.statut
    } for u in urgences])

# Route pour signaler une urgence
@app.route('/urgence', methods=['POST'])
def signaler_urgence():
    data = request.json
    location = geolocator.geocode(data['lieu'])

    nouvelle_urgence = Urgence(
        nom=data['nom'],
        lieu=data['lieu'],
        latitude=location.latitude if location else None,
        longitude=location.longitude if location else None,
        animal=data['animal'],
        description=data['description']
    )
    db.session.add(nouvelle_urgence)
    db.session.commit()
    return jsonify({"message": "Urgence enregistrée avec géolocalisation"}), 201

# Démarrer Flask avec WebSocket
if __name__ == '__main__':
    db.create_all()
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)
