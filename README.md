# 🛡️ KYC & AML Screening – Real-Time Client Filtering

Projet personnel simulant une architecture de filtrage client (KYC/AML) en temps réel, inspirée des environnements bancaires.

## 🚀 Objectif

Filtrer automatiquement des profils clients (noms, pays sensibles, etc.) via une chaîne de traitement distribuée.

## ⚙️ Stack technique

- Python : Génération et traitement de clients
- Kafka :Transmission des données (topic `clients`)
- MongoDB : Stockage des profils
- Docker Compose : Orchestration locale

## ▶️ Lancer le projet

```bash
git clone https://github.com/ziguieva/kyc-aml-screening.git
cd kyc-aml-screening
docker compose up -d
python app/producer.py

🗂️ Structure

kyc-aml-screening/
├── app/
│   ├── producer.py
│   └── consumer.py
├── docker-compose.yml
└── README.md

🛠️ Extensions possibles

✅ Intégration d’un moteur de règles ou d’IA pour scoring AML
✅ Mise en place de tests unitaires et CI
✅ API REST (Flask/FastAPI) pour interagir avec MongoDB
✅ Export vers ElasticSearch ou DataLake
✅ Tableau de bord de supervision avec Grafana/Prometheus

