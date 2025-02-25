import json
from rasa_sdk import Action
from rasa_sdk.events import SlotSet

class ActionFetchHospitalInfo(Action):
    def name(self):
        return "action_fetch_hospital_info"

    def run(self, dispatcher, tracker, domain):
        user_message = tracker.latest_message.get("text")  # Get user message
        city = "Улаанбаатар"  # Default city (you can extract from user input)

        # Load hospital data from JSON file
        with open("data/hospital_data.json", "r", encoding="utf-8") as f:
            hospital_data = json.load(f)

        # Find hospitals with insurance contract in the requested city
        insured_hospitals = [
            h["name"] for h in hospital_data["hospitals"]
            if h["city"] == city and h["insurance_contract"]
        ]

        if insured_hospitals:
            hospitals_list = "\n".join(insured_hospitals)
            response_text = f"📢 Даатгалтай эмнэлгүүд ({city} хотод):\n{hospitals_list}"
        else:
            response_text = f"❌ {city} хотод даатгалтай эмнэлэг олдсонгүй."

        dispatcher.utter_message(text=response_text)
        return []
