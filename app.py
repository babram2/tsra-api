from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
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
bcrypt = Bcrypt(app)
CORS(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
socketio = SocketIO(app, cors_allowed_origins="*")

# Clé API Stripe (https://api.render.com/deploy/srv-cui1d2hu0jms7398vthg?key=UU9xpkgjJTc)
stripe.api_key = "sk_test_votre_cle_secrete"

# Initialisation Geopy pour géolocalisation
geolocator = Nominatim(user_agent="tsra-secours")
location = geolocator.geocode("10 Rue de Nantes")
print(location.latitude, location.longitude)

# Modèles de base de données
class Cagnotte(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    objectif = db.Column(db.Float, nullable=False)
    collecte = db.Column(db.Float, default=0.0)
    date_creation = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Contribution(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cagnotte_id = db.Column(db.Integer, db.ForeignKey('cagnotte.id'), nullable=False)
    nom_donateur = db.Column(db.String(100), nullable=False)
    montant = db.Column(db.Float, nullable=False)
    date_don = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Benevole(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Urgence(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    lieu = db.Column(db.String(200), nullable=False)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    animal = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    statut = db.Column(db.String(50), default="En attente")

# Gestion des utilisateurs avec LoginManager
@login_manager.user_loader
def load_user(user_id):
    return Benevole.query.get(int(user_id))

# Création de la base de données
with app.app_context():
    db.create_all()

# Routes principales
@app.route('/')
def home():
    return "Bienvenue sur l'API T.S.R.A - Service opérationnel !"

@app.route('/cagnottes', methods=['GET'])
def obtenir_cagnottes():
    cagnottes = Cagnotte.query.all()
    return jsonify([{
        "id": c.id,
        "nom": c.nom,
        "objectif": c.objectif,
        "collecte": c.collecte
    } for c in cagnottes])

@app.route('/cagnotte', methods=['POST'])
def creer_cagnotte():
    data = request.json
    nouvelle_cagnotte = Cagnotte(
        nom=data['nom'],
        description=data['description'],
        objectif=data['objectif']
    )
    db.session.add(nouvelle_cagnotte)
    db.session.commit()
    return jsonify({"message": "Cagnotte créée avec succès !"}), 201

@app.route('/contribution', methods=['POST'])
def contribuer():
    data = request.json
    cagnotte = Cagnotte.query.get(data['cagnotte_id'])
    if not cagnotte:
        return jsonify({"error": "Cagnotte non trouvée"}), 404
    contribution = Contribution(
        cagnotte_id=data['cagnotte_id'],
        nom_donateur=data['nom_donateur'],
        montant=data['montant']
    )
    cagnotte.collecte += data['montant']
    db.session.add(contribution)
    db.session.commit()
    return jsonify({"message": "Contribution enregistrée avec succès !"}), 201

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

@app.route('/urgences', methods=['GET'])
def voir_urgences():
    urgences = Urgence.query.all()
    return jsonify([{
        "id": u.id,
        "nom": u.nom,
        "lieu": u.lieu,
        "latitude": u.latitude,
        "longitude": u.longitude,
        "animal": u.animal,
        "description": u.description,
        "statut": u.statut
    } for u in urgences])

# WebSocket pour le chat en direct
@socketio.on('message')
def handle_message(data):
    emit('message', {"expediteur": data['expediteur'], "message": data['message']}, broadcast=True)

# Lancer l'application
if __name__ == '__main__':
    socketio.run(app, debug=True)





