from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
import psycopg2
import os
from dotenv import load_dotenv
from datetime import datetime

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

class ActionGetHospitalInfo(Action):
    def name(self):
        return "action_get_hospital_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        icd10_name = tracker.get_slot("icd10_name")
        hospital_name = tracker.get_slot("hospital_name")
        conn = get_db_connection()
        if not conn:
            dispatcher.utter_message(text="Уучлаарай, датабейсэд холбогдох боломжгүй байна.")
            return []
        
        try:
            with conn:
                with conn.cursor() as cursor:
                    if icd10_name:
                        cursor.execute("""
                            SELECT I.ICD10NAMEL, H.HS_NAME, H.HS_ADDRESS 
                            FROM ICD10CODE I 
                            JOIN DRG_ICD_MAPPING IM ON I.ICD10CODE = IM.ICD10CODE
                            JOIN DRGCODES D ON D.DRGCODE = IM.DRGCODE
                            JOIN CONTRACT C ON D.DRGCODE = C.DRGCODE
                            JOIN HOSPITAL H ON H.HOSPITAL_ID = C.HOSPITAL_ID
                            WHERE I.ICD10NAMEL LIKE %s
                            LIMIT 5
                        """, (f'%{icd10_name}%',))
                        results = cursor.fetchall()
                        if results:
                            hospital_list = [f"🏥 {row[1]} - Хаяг: {row[2]}" for row in results]
                            response = f"{icd10_name}-г эмчилдэг гэрээт эмнэлгүүд:\n" + "\n".join(hospital_list)
                        else:
                            response = f"{icd10_name}-г эмчилдэг гэрээт эмнэлэг олдсонгүй."
                    elif hospital_name:
                        cursor.execute("""
                            SELECT HS_NAME, HAS_INSURANCE, HS_ADDRESS 
                            FROM HOSPITAL 
                            WHERE HS_NAME LIKE %s
                            LIMIT 1
                        """, (f'%{hospital_name}%',))
                        result = cursor.fetchone()
                        if result:
                            name, has_insurance, address = result
                            status = "гэрээт" if has_insurance else "гэрээтэй биш"
                            cursor.execute("""
                                SELECT C.DRGCODE 
                                FROM CONTRACT C 
                                WHERE C.HOSPITAL_ID = (SELECT HOSPITAL_ID FROM HOSPITAL WHERE HS_NAME LIKE %s) 
                                AND C.STATUS = 1
                                LIMIT 5
                            """, (f'%{hospital_name}%',))
                            contracts = cursor.fetchall()
                            contract_list = [contract[0] for contract in contracts] if contracts else []
                            response = f"{name} эмнэлэг {status}. Хаяг: {address}."
                            if has_insurance and contract_list:
                                response += f" Гэрээт DRG код: {', '.join(contract_list)}."
                            else:
                                response += " Гэрээтэй DRG код олдсонгүй."
                        else:
                            response = f"{hospital_name} эмнэлэг олдсонгүй."
                    else:
                        response = "Гэрээт эмнэлгийн мэдээлэл тодруулахын тулд онош эсвэл эмнэлгийн нэрийг зааж өгнө үү."

                    dispatcher.utter_message(text=response)
        except Exception as e:
            print(f"❌ Error fetching hospital info: {e}")
            dispatcher.utter_message(text="Уучлаарай, мэдээлэл татахад алдаа гарлаа.")
        finally:
            if conn:
                conn.close()
        return []

class ActionGetMedicineInfo(Action):
    def name(self):
        return "action_get_medicine_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        icd10_name = tracker.get_slot("icd10_name")
        tablet_name = tracker.get_slot("tablet_name")
        conn = get_db_connection()
        if not conn:
            dispatcher.utter_message(text="Уучлаарай, датабейсэд холбогдох боломжгүй байна.")
            return []
        
        try:
            with conn:
                with conn.cursor() as cursor:
                    if icd10_name:
                        cursor.execute("""
                            SELECT I.ICD10NAMEL, T.TBLT_NAME_MON, T.TBLT_UNIT_DISAMT, T.TBLT_UNIT_PRICE 
                            FROM ICD10CODE I
                            JOIN TABLET_ICD_MAPPING TM ON SUBSTR(I.ICD10CODE, 1, 3) = SUBSTR(TM.ICD10CODE, 1, 3)
                            JOIN TABLET T ON TM.TBLT_ID = T.TBLT_ID
                            WHERE I.ICD10NAMEL LIKE %s
                            LIMIT 5
                        """, (f'%{icd10_name}%',))
                        results = cursor.fetchall()
                        if results:
                            medicine_list = [f"💊 {row[1]} (Хөнгөлөлт: {row[2]}₮, Үнэ: {row[3]}₮)" for row in results]
                            response = f"{icd10_name}-д хэрэглэгдэх хөнгөлөлттэй эмийн жагсаалт:\n" + "\n".join(medicine_list)
                        else:
                            response = f"{icd10_name}-д хөнгөлөлттэй эм олдсонгүй."
                    elif tablet_name:
                        cursor.execute("""
                            SELECT TBLT_NAME_MON, TBLT_UNIT_DISAMT, TBLT_UNIT_PRICE 
                            FROM TABLET 
                            WHERE TBLT_NAME_MON LIKE %s
                            LIMIT 1
                        """, (f'%{tablet_name}%',))
                        result = cursor.fetchone()
                        if result:
                            name, discount, price = result
                            response = f"{name} эм хөнгөлөлттэй: {discount}₮ (Үнэ: {price}₮). Нөхцөл: ЭМД-тай гэрээт эмнэлэгт хандахад хөнгөлөлттэй."
                        else:
                            response = f"{tablet_name} эм олдсонгүй."
                    else:
                        response = "Хөнгөлөлттэй эмийн мэдээлэл тодруулахын тулд онош эсвэл эмийн нэрийг зааж өгнө үү."

                    dispatcher.utter_message(text=response)
        except Exception as e:
            print(f"❌ Error fetching medicine info: {e}")
            dispatcher.utter_message(text="Уучлаарай, мэдээлэл татахад алдаа гарлаа.")
        finally:
            if conn:
                conn.close()
        return []

class ActionGetInsuranceFee(Action):
    def name(self):
        return "action_get_insurance_fee"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        year = tracker.get_slot("year") or "2025"  # Default 2025 он
        response = "Эрүүл мэндийн даатгалын шимтгэлийн хэмжээ: \n"
        if year == "2019":
            response += "- 2019 он: Сарын 3,200 төгрөг, жилийн 38,400 төгрөг"
        elif year == "2020" or year == "2021" or year == "2022":
            response += "- 2020-2022 он: Сарын 4,200 төгрөг, жилийн 50,400 төгрөг"
        elif year == "2023":
            response += "- 2023 он: Сарын 5,500 төгрөг, жилийн 66,000 төгрөг"
        elif year == "2024":
            response += "- 2024 он: Сарын 6,600 төгрөг, жилийн 79,200 төгрөг"
        elif year == "2025":
            response += "- 2025 он: 1-3 сарын хувьд сарын 13,200 төгрөг, 4 сараас эхлэн сарын 15,840 төгрөг"
        else:
            response += "Тодруулсан жилд мэдээлэл олдсонгүй. Хамгийн сүүлийн мэдээлэл: 2025 онд 1-3 сарын хувьд сарын 13,200 төгрөг, 4 сараас эхлэн сарын 15,840 төгрөг."
        dispatcher.utter_message(text=response)
        return []

class ActionGetServices(Action):
    def name(self):
        return "action_get_services"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        response = "Эрүүл мэндийн даатгалаар дараах тусламж, үйлчилгээг авах боломжтой: \n1. Хэвтүүлэн эмчлэх тусламж \n2. Амбулаторийн тусламж \n3. Өндөр өртөгтэй оношилгоо, шинжилгээ \n4. Яаралтай тусламж \n5. Түргэн тусламж \n6. Телемедицин \n7. Өдрийн эмчилгээ \n8. Диализын тусламж \n9. Хорт хавдрын хими, туяаны өдрийн эмчилгээ \n10. Сэргээн засах тусламж \n11. Хөнгөвчлөх тусламж \n12. Уламжлалт анагаах ухааны тусламж \n13. Эмийн үнийн хөнгөлөлт"
        dispatcher.utter_message(text=response)
        return []

class ActionGetInsuranceInfo(Action):
    def name(self):
        return "action_get_insurance_info"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        conn = get_db_connection()
        if not conn:
            response = "Таны даатгалын талаар ерөнхий мэдээлэл: Даатгал нь эмнэлэг, эмийн зардлыг хамарна."
        else:
            try:
                with conn:
                    with conn.cursor() as cursor:
                        cursor.execute("SELECT icd10namel, icd10code, covered FROM ICD10CODE LIMIT 1")
                        result = cursor.fetchone()
                        if result:
                            icd_name, icd_code, covered = result
                            status = "хүчинтэй" if covered else "хүчингүй"
                            response = f"Таны даатгалын талаар ерөнхий мэдээлэл: Даатгал нь эмнэлэг, эмийн зардлыг хамарна. Жишээ: {icd_name} (код: {icd_code}) нь ЭМД-д {status} байна."
                        else:
                            response = "Таны даатгалын мэдээлэл олдсонгүй."
            except Exception as e:
                print(f"❌ Error fetching insurance info: {e}")
                response = "Таны даатгалын талаар ерөнхий мэдээлэл: Даатгал нь эмнэлэг, эмийн зардлыг хамарна."
            finally:
                conn.close()
        dispatcher.utter_message(text=response)
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
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute("INSERT INTO unanswered_questions (question) VALUES (%s)", (question,))
                    conn.commit()
        except Exception as e:
            print(f"❌ Error saving unanswered question: {e}")
        finally:
            if conn:
                conn.close()
        dispatcher.utter_message(text="Уучлаарай, би энэ асуултад хариу өгч чадаагүй. Таны асуултыг бүртгелээ, бид илүү сайжруулна.")
        return []