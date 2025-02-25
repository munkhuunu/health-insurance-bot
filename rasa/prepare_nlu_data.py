import json
import yaml
import os

# ✅ Check if file exists before loading
def load_json(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    return []

hospitals = load_json("data/hospital_data.json")
medicines = load_json("data/medicine_data.json")

# ✅ Prepare Rasa training format
nlu_data = {"version": "3.1", "nlu": []}

# ✅ Prepare hospital intent
intent_hospitals = {"intent": "ask_insurance_hospital", "examples": []}
for row in hospitals:
    example = f"Ханиад хүрчихлээ. {row['hospital_name']} эмнэлэг даатгалтай гэрээтэй юу?"
    intent_hospitals["examples"].append(f"- {example}")

nlu_data["nlu"].append(intent_hospitals)

# ✅ Prepare medicine intent
intent_medicines = {"intent": "ask_medicine", "examples": []}
for row in medicines:
    example = f"{row['tablet_name_mon']} эмийг {row['icd10_name']} өвчний үед хэрэглэх боломжтой юу?"
    intent_medicines["examples"].append(f"- {example}")

nlu_data["nlu"].append(intent_medicines)

# ✅ Save as `nlu.yml`
with open("data/nlu.yml", "w", encoding="utf-8") as file:
    yaml.dump(nlu_data, file, allow_unicode=True, default_flow_style=False)

print("✅ Rasa NLU training data successfully generated in `data/nlu.yml`")
