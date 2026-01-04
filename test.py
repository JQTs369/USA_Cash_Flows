from datetime import datetime, timedelta
import os

path  = r"C:\Users\Jacque Trahan\Documents\USA_Cash_Flows\AmericanRealityClasses\resources\debt_backup.json"
file_time = os.path.getmtime(path)
last_update = datetime.fromtimestamp(file_time)

print(datetime.now() - last_update < timedelta(days=350))
print(datetime.now() - last_update )

# if os.path.exists(storage_path) and os.path.getsize(storage_path):
#     file_time = os.path.getmtime(storage_path)
#     last_updated = datetime.fromtimestamp(file_time)
#     # use csv files until end of year
#     if datetime.now() - last_updated > timedelta(days=350):
#         with open(storage_path, 'r') as f:
#             json_data = json.load(f)
#         debt_df = pd.DataFrame(json_data['data'])
#         data_flag = 'Back Up'