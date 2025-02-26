from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import psycopg2
import os
from dotenv import load_dotenv

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

class ActionGetHospitalInfo(Action):
    def name(self):
        return "action_get_hospital_info"

    def run(self, dispatcher, tracker, domain):
        hospital_name = tracker.get_slot("hospital_name")
        conn = get_db_connection()
        
        if not conn:
            dispatcher.utter_message(text="Уучлаарай, датабейсэд холбогдох боломжгүй байна.")
            return []

        try:
            with conn.cursor() as cursor:
                cursor.execute("SELECT HS_NAME, HS_ADDRESS FROM HOSPITAL WHERE HS_NAME LIKE %s LIMIT 1", (f"%{hospital_name}%",))
                result = cursor.fetchone()
                
                if result:
                    name, address = result
                    response = f"🏥 {name} эмнэлэг. Хаяг: {address}"
                else:
                    response = f"{hospital_name} эмнэлэг олдсонгүй."

                dispatcher.utter_message(text=response)
        except Exception as e:
            print(f"❌ Error fetching hospital info: {e}")
            dispatcher.utter_message(text="Мэдээлэл татахад алдаа гарлаа.")
        finally:
            if conn:
                conn.close()
        return []

class ActionSaveUnansweredQuestion(Action):
    def name(self):
        return "action_save_unanswered_question"

    def run(self, dispatcher, tracker, domain):
        question = tracker.latest_message['text']
        conn = get_db_connection()
        
        if not conn:
            dispatcher.utter_message(text="Уучлаарай, датабейсэд холбогдох боломжгүй байна.")
            return []
        
        try:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO unanswered_questions (question) VALUES (%s)", (question,))
                conn.commit()
                dispatcher.utter_message(text="📌 Таны асуултыг бүртгэж авлаа, удахгүй хариу өгнө.")
        except Exception as e:
            print(f"❌ Error saving question: {e}")
            dispatcher.utter_message(text="Алдаа гарлаа, таны асуултыг хадгалах боломжгүй байна.")
        finally:
            if conn:
                conn.close()
        
        return []
