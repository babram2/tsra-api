from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_cors import CORS
import stripe
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import datetime

# Configuration Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tsra.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'supersecret'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
socketio = SocketIO(app, cors_allowed_origins="*")
login_manager = LoginManager(app)
login_manager.login_view = "login"
CORS(app)

# Stripe API Key
stripe.api_key = "sk_test_your_secret_key"

# Geolocator
geolocator = Nominatim(user_agent="tsra")

# Modèles
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

# Gestion des bénévoles
@login_manager.user_loader
def load_user(user_id):
    return Benevole.query.get(int(user_id))

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    if Benevole.query.filter_by(username=data['username']).first():
        return jsonify({"error": "Utilisateur déjà existant"}), 400
    new_user = Benevole(username=data['username'], password=hashed_password)
    db.session.add(new_user)
    db.session.commit()
    return jsonify({"message": "Utilisateur enregistré"}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    user = Benevole.query.filter_by(username=data['username']).first()
    if user and bcrypt.check_password_hash(user.password, data['password']):
        login_user(user)
        return jsonify({"message": "Connexion réussie"}), 200
    return jsonify({"error": "Identifiants incorrects"}), 401

# Gestion des urgences
@app.route('/urgence', methods=['POST'])
def signaler_urgence():
    data = request.json
    location = geolocator.geocode(data['lieu'])
    if not location:
        return jsonify({"error": "Adresse invalide"}), 400

    urgence = Urgence(
        nom=data['nom'],
        lieu=data['lieu'],
        latitude=location.latitude,
        longitude=location.longitude,
        animal=data['animal'],
        description=data['description']
    )
    db.session.add(urgence)
    db.session.commit()
    return jsonify({"message": "Urgence enregistrée"}), 201

@app.route('/urgences', methods=['GET'])
def voir_urgences():
    urgences = Urgence.query.all()
    return jsonify([{
        "id": u.id, "nom": u.nom, "lieu": u.lieu, "latitude": u.latitude,
        "longitude": u.longitude, "animal": u.animal, "description": u.description, "statut": u.statut
    } for u in urgences])

# Gestion des cagnottes
@app.route('/cagnotte', methods=['POST'])
def creer_cagnotte():
    data = request.json
    cagnotte = Cagnotte(
        nom=data['nom'],
        description=data['description'],
        objectif=data['objectif']
    )
    db.session.add(cagnotte)
    db.session.commit()
    return jsonify({"message": "Cagnotte créée"}), 201

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
    return jsonify({"message": "Contribution enregistrée"}), 201

# Gestion du chat en temps réel
@socketio.on('message')
def handle_message(data):
    emit('message', data, broadcast=True)

# Démarrer le serveur
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    socketio.run(app, debug=True, host="0.0.0.0", port=5000)


