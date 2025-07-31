from kafka import KafkaProducer
from faker import Faker
import json
import time
import random

fake = Faker()

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Ajoute quelques noms blacklistés dans la génération
blacklist_noms = ["ALI", "SMITH", "IVANOV", "NGUYEN", "YAMAMOTO"]

def generate_client():
    nom = fake.last_name().upper()
    # On injecte un blacklisté de temps en temps
    if random.random() < 0.1:
        nom = random.choice(blacklist_noms)
    return {
        "id": fake.uuid4(),
        "nom": nom,
        "prenom": fake.first_name(),
        "pays": fake.country(),
        "naissance": fake.date_of_birth(minimum_age=18, maximum_age=75).isoformat()
    }

print("🚀 Envoi massif de clients en cours...\n")

for _ in range(100):  # Tu peux augmenter ce nombre
    client = generate_client()
    print(f"📤 Client : {client}")
    producer.send("clients", client)
    time.sleep(0.2)  # Envoie rapide mais réaliste

producer.flush()
