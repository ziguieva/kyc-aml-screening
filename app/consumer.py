from kafka import KafkaConsumer
from rapidfuzz import fuzz
from datetime import datetime
from pymongo import MongoClient, ASCENDING
import json
import os
import sys
import traceback

# ------------- Config -------------
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "localhost:9092")
KAFKA_TOPIC = os.getenv("KAFKA_TOPIC", "clients")
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "aml")
COLL_NAME = os.getenv("COLL_NAME", "screenings")
FUZZY_THRESHOLD = int(os.getenv("FUZZY_THRESHOLD", "90"))

# Liste noire simplifiée (noms de famille ou noms complets)
BLACKLIST = [
    "ALI", "SMITH", "IVANOV", "NGUYEN", "YAMAMOTO",
    "OSAMA BIN LADEN", "JOHN DOE SANCTION"
]

# ------------- Helpers -------------
def best_match_score(client_fullname: str) -> tuple[int, str]:
    """Retourne (score, nom_blacklist) du meilleur match fuzzy sur le nom complet."""
    best_score = 0
    best_entry = ""
    for banned in BLACKLIST:
        score = fuzz.token_set_ratio(client_fullname.upper(), banned.upper())
        if score > best_score:
            best_score = score
            best_entry = banned
    return best_score, best_entry

def decide_status(client: dict) -> dict:
    """Décide si le client est OK ou ALERTE (exacte ou fuzzy)."""
    nom = (client.get("nom") or "").upper()
    prenom = (client.get("prenom") or "").upper()
    fullname = (prenom + " " + nom).strip()

    # 1) correspondance exacte sur le nom de famille
    exact_hit = nom in BLACKLIST

    # 2) fuzzy sur le nom complet
    fuzzy_score, matched = best_match_score(fullname)

    alert = exact_hit or (fuzzy_score >= FUZZY_THRESHOLD)
    reason = []
    if exact_hit:
        reason.append(f"exact_lastname:{nom}")
    if fuzzy_score >= FUZZY_THRESHOLD:
        reason.append(f"fuzzy_fullname:{matched}:{fuzzy_score}")

    return {
        "status": "ALERT" if alert else "OK",
        "score": max(fuzzy_score, 100 if exact_hit else 0),
        "reason": ", ".join(reason) if reason else "none"
    }

# ------------- Connexions -------------
print("🧩 Connexion à MongoDB...")
mongo = MongoClient(MONGO_URI)
coll = mongo[DB_NAME][COLL_NAME]
# Index utiles
coll.create_index([("client.id", ASCENDING)], unique=False)
coll.create_index([("status", ASCENDING)])
coll.create_index([("screened_at", ASCENDING)])

print("🔗 Connexion à Kafka...")
consumer = KafkaConsumer(
    KAFKA_TOPIC,
    bootstrap_servers=KAFKA_BOOTSTRAP,
    value_deserializer=lambda m: json.loads(m.decode("utf-8")),
    auto_offset_reset="earliest",
    enable_auto_commit=True,
    group_id="aml-screening-v1"
)

print("🕵️ Démarrage du screening AML (MongoDB + fuzzy)...\n")

# ------------- Boucle principale -------------
for message in consumer:
    try:
        client = message.value  # dict
        decision = decide_status(client)

        doc = {
            "client": client,
            "status": decision["status"],        # OK / ALERT
            "score": decision["score"],          # 0..100
            "reason": decision["reason"],        # explications
            "kafka_meta": {
                "partition": message.partition,
                "offset": message.offset,
                "timestamp": message.timestamp
            },
            "screened_at": datetime.utcnow()
        }

        coll.insert_one(doc)

        if decision["status"] == "ALERT":
            print(f"🚨 ALERTE [{decision['score']}] → {client} | {decision['reason']}")
        else:
            print(f"✅ OK [{decision['score']}] → {client['prenom']} {client['nom']} ({client.get('pays','')})")

    except Exception as e:
        print("❌ Erreur de traitement :", e)
        traceback.print_exc(file=sys.stdout)
