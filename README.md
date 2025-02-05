# API TSR (Transport de Secours Rapide)

Cette API a été conçue pour gérer les opérations du Transport de Secours Rapide Animaliers (TSRA), y compris la gestion des données, des missions de secours, et des communications entre différents services.

## Fonctionnalités

- Gestion des utilisateurs (authentification et autorisation)
- Gestion des missions de secours
- Génération de rapports en PDF
- Traitement des paiements avec Stripe
- Gestion des données géographiques pour les trajets de secours

## Technologies utilisées

- Flask
- Flask-SQLAlchemy
- Flask-SocketIO
- Flask-Bcrypt
- Flask-Login
- Flask-CORS
- Stripe
- Pandas
- OpenPyXL
- ReportLab
- Gunicorn
- Geopy

## Installation

1. Clonez ce dépôt :
   ```bash
   git clone https://github.com/babram2/tsra-api.git
   cd tsra-api
