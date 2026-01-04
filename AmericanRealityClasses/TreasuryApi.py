# here to get the info we need for our web app
# sources: 
    # https://fiscaldata.treasury.gov/api-documentation/
    # https://fiscaldata.treasury.gov/datasets/historical-debt-outstanding/historical-debt-outstanding
        # Historical Debt Outstanding is a dataset that provides a summary of the U.S. government's total outstanding debt at the end of each fiscal year
        #  from 1789 to the current year. Between 1789 and 1842, the fiscal year began in January. From January 1842 until 1977, the fiscal year began in July.
        #  From July 1977 onwards, the fiscal year has started in October. Between 1789 and 1919, debt outstanding was presented as of the first day of the next fiscal year.
        #  From 1920 onwards, debt outstanding has been presented as of the final day of the fiscal year. This is a high-level summary of historical public debt
        #  and does not contain a breakdown of the debt components.
    # https://taxpolicycenter.org/sites/default/files/statistics/spreadsheet/fed_receipt_funds_3.xlsx
    # https://taxpolicycenter.org/statistics/federal-receipt-and-outlay-summary-fund-group
        # treasury site does not have complete history only from 1995 to present -make it make sense


# imports
import requests
import json
import os
import pandas as pd
from datetime import datetime, timedelta


class Treasury:

    def __init__(self):
        # self.base_path = r'https://api.fiscaldata.treasury.gov/services/api/fiscal_service'
        self.ErrorLog = []

    def getHistoricalDebtAPIData(self,
                                 base_url=r'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_outstanding'):
        """
        Gets api data and all pages into a list of dicts. can be put into a pandas data frame if needed
        Built of this api. # TODO need to try other base urls to see if it is dynamic
        base_url = r'https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/debt_outstanding'
        """
        data = []
        data_flag = 'API'
        debt_df = pd.DataFrame()
        page_number = 1
        # setup file paths
        current_dir = os.path.dirname(os.path.abspath(__file__))
        storage_path = os.path.join(current_dir,'resources','debt_backup.json')
        # confirm path exists
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        # 1. Define the "Identity" (Headers) Try to tell the API as if I am a browser so it runs faster
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
        }
        try:
            # try to use stored file
            if os.path.exists(storage_path) and os.path.getsize(storage_path):
                file_time = os.path.getmtime(storage_path)
                last_updated = datetime.fromtimestamp(file_time)
                # use csv files until end of year
                if datetime.now() - last_updated > timedelta(days=350):
                    with open(storage_path,'r') as f:
                        json_data = json.load(f)
                    debt_df = pd.DataFrame(json_data['data'])
                    data_flag = 'Back Up'

            # gets API if JSON fails or is old
            if debt_df.empty:
                # get API if CSV is old or empty
                while True:
                    # try to call data with GET
                    response = requests.get(f"{base_url}?page[number]={page_number}&page[size]=100", headers=headers,timeout=5)
                    if response.status_code == 200:
                        # get out data to phrase
                        json_data = response.json()

                        # append the data from the current page to the list
                        data.extend(json_data['data'])

                        # get links next key for more pages
                        next_page = json_data['links'].get('next')
                        # increase page number if needed
                        if next_page:
                            page_number +=1
                        else:
                            break
                    else:
                        print(f"API ERROR: {response.status_code}")
                        break
                if data:
                    debt_df = pd.DataFrame(data)
                    with open(storage_path,'w') as f:
                        json.dump({"data":data},f)

        except Exception as e:
            print(f"API Connection Error: {e}")


        if not debt_df.empty:
            # Slight cleaning of df
            debt_df['record_fiscal_year'] = debt_df['record_fiscal_year'].astype(int)
            debt_df['debt_outstanding_amt'] = debt_df['debt_outstanding_amt'].astype(float)
            return debt_df, data_flag
        else:
            return pd.DataFrame(), data_flag

    def getTaxPolicyDownload(self,
                             tax_policy_save_location: str = r'resources/TaxPolicyCenterHistoricRevenues.xlsx'):
        df = pd.DataFrame()  # Initialize here so it's always in scope

        directory = os.path.dirname(tax_policy_save_location)
        if not os.path.exists(directory):
            os.makedirs(directory)

        # 1. Logic Gate: Only download if file is missing or older than 350 days
        should_download = True
        if os.path.exists(tax_policy_save_location):
            file_age = datetime.fromtimestamp(os.path.getmtime(tax_policy_save_location))
            if datetime.now() - file_age > timedelta(days=350):
                should_download = False
                print(f"✅ Using local Tax Policy file (Updated: {file_age.date()})")

        if should_download:
            base_url = r'https://taxpolicycenter.org/sites/default/files/statistics/spreadsheet/fed_receipt_funds_3.xlsx'
            try:
                response = requests.get(base_url, timeout=10)
                if response.status_code == 200:
                    with open(tax_policy_save_location, 'wb') as f:
                        f.write(response.content)
                        print(f"Tax Policy File was successfully saved at {tax_policy_save_location}")
                else:
                    print(f"Download failed (Status: {response.status_code}). Using old file...")
            except Exception as e:
                print(f"Connection error during download: {e}. Trying to use old file...")

        # 2. Process Data (This will now run even if the download above failed)
        if os.path.exists(tax_policy_save_location):
            try:
                df = pd.read_excel(tax_policy_save_location, skiprows=6)
                df = df.drop(0)

                df.rename(columns={
                    "Unnamed: 0": "Fiscal Year",
                    "Total": "Receipts Total",
                    "Total.1": "Outlays Total",
                    "Total.2": "Surplus or Deficit(-) Total"
                }, inplace=True)

                # Filter out estimates and clean types
                estimate_index = df[df['Fiscal Year'].str.contains('Estimates', case=False, na=False)].index[0]
                df = df.iloc[:estimate_index - 2]
                df = df[df['Fiscal Year'] != 'TQ']

                df['Fiscal Year'] = df['Fiscal Year'].astype(int)
                df['Surplus or Deficit(-) Total'] = df['Surplus or Deficit(-) Total'] * 1_000_000
            except Exception as e:
                print(f"Error processing the Excel file: {e}")
                df = pd.DataFrame()
        else:
            print("No local file found and download failed. Returning empty DataFrame.")

        return df



        
if __name__ == '__main__':
    # instance
    test = Treasury()
    df = test.getTaxPolicyDownload()
    print(df.tail)

