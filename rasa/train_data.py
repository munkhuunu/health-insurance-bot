import psycopg2
import yaml
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "host": os.getenv("DB_HOST"),
    "port": os.getenv("DB_PORT"),
}

def get_db_connection():
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return None

# Fetch hospital data
def fetch_hospital_data():
    query = """
    SELECT DISTINCT ON (I.ICD10CODE, H.HOSPITAL_ID) 
       I.ICD10CODE, I.ICD10NAMEL, H.HS_NAME, H.HOSPITAL_ID 
    FROM ICD10CODE I 
    JOIN DRG_ICD_MAPPING IM ON I.ICD10CODE = IM.ICD10CODE
    JOIN DRGCODES D ON D.DRGCODE = IM.DRGCODE
    JOIN CONTRACT C ON D.DRGCODE = C.DRGCODE
    JOIN HOSPITAL H ON H.HOSPITAL_ID = C.HOSPITAL_ID
    LIMIT 10;  -- Limit for demo
    """
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return [{"icd10_code": row[0], "icd10_name": row[1], "hospital_name": row[2], "hospital_id": row[3]} for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching hospital data: {e}")
        return []

# Fetch medicine data
def fetch_medicine_data():
    query = """
    SELECT DISTINCT I.ICD10CODE, I.ICD10NAMEL, T.TBLT_NAME_MON, T.TBLT_ID
    FROM ICD10CODE I
    JOIN TABLET_ICD_MAPPING TM 
        ON SUBSTR(I.ICD10CODE, 1, 3) = SUBSTR(TM.ICD10CODE, 1, 3)
    JOIN TABLET T 
        ON TM.TBLT_ID = T.TBLT_ID
    LIMIT 10;  -- Limit for demo
    """
    conn = get_db_connection()
    if not conn:
        return []
    try:
        with conn:
            with conn.cursor() as cursor:
                cursor.execute(query)
                return [{"icd10_code": row[0], "icd10_name": row[1], "tablet_name": row[2], "tablet_id": row[3]} for row in cursor.fetchall()]
    except Exception as e:
        print(f"❌ Error fetching medicine data: {e}")
        return []

# Generate NLU and Responses
def generate_rasa_training_data():
    hospital_data = fetch_hospital_data()
    medicine_data = fetch_medicine_data()

    # NLU Data
    nlu_data = {
        "version": "3.1",
        "nlu": [
            {
                "intent": "ask_insurance",
                "examples": ["- Миний даатгал хүчинтэй юу?", "- Даатгалын талаар мэдээлэл өгнө үү?"]
            },
            {
                "intent": "ask_insurance_hospital",
                "examples": [f"- [{row['icd10_name']}](icd10_name)-г ямар эмнэлэг эмчилдэг вэ?" for row in hospital_data]
            },
            {
                "intent": "ask_medicine",
                "examples": [f"- [{row['icd10_name']}](icd10_name)-д ямар эм хэрэглэдэг вэ?" for row in medicine_data]
            }
        ]
    }

    # Responses Data (placeholders for dynamic responses)
    responses_data = {
        "version": "3.1",
        "responses": {
            "utter_insurance_info": [{"text": "Таны даатгалын талаар ерөнхий мэдээлэл: Даатгал нь эмнэлэг, эмийн зардлыг хамарна."}],
            "utter_hospital_info": [{"text": "🏥 {hospital_name} нь {icd10_name}-г эмчилдэг."}],
            "utter_medicine_info": [{"text": "💊 {tablet_name} нь {icd10_name}-д хэрэглэгддэг."}]
        }
    }

    # Save files
    os.makedirs("data", exist_ok=True)
    with open("data/nlu.yml", "w", encoding="utf-8") as f:
        yaml.dump(nlu_data, f, allow_unicode=True, default_flow_style=False)
    with open("data/responses.yml", "w", encoding="utf-8") as f:
        yaml.dump(responses_data, f, allow_unicode=True, default_flow_style=False)
    
    print("✅ Generated nlu.yml and responses.yml in 'data/' directory.")

if __name__ == "__main__":
    generate_rasa_training_data()