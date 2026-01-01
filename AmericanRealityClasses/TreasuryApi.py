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
        # treseury site does not have complete history only from 1995 to present -make it make sense


# imports
import requests
# import json
import os
import pandas as pd
# import time


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
        page_number = 1
        api_success = False
        current_dir = os.path.dirname(os.path.abspath(__file__))
        storage_path = os.path.join(current_dir,'resources','debt_backup.csv')
        # confirm path exists
        os.makedirs(os.path.dirname(storage_path), exist_ok=True)
        try:
            while True:
                # try to call data with GET
                response = requests.get(f"{base_url}?page[number]={page_number}&page[size]=100", timeout=5)
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
                        api_success = True
                        # no more pages
                        break
                else:
                    break
        except Exception as e:
            print(f"API Connection Error: {e}")

        if api_success:
            debt_df = pd.DataFrame(data)
            debt_df.to_csv(storage_path, index=False)
            print("Successfully updated local backup From API")
        else:
            print("⚠️ API Down. Attempting to load from local backup...")
            if os.path.exists(storage_path) and os.path.getsize(storage_path):
                debt_df = pd.read_csv(storage_path)
            else:
                return pd.DataFrame()
        # Slight cleaning of df
        debt_df['record_fiscal_year'] = debt_df['record_fiscal_year'].astype(int)
        debt_df['debt_outstanding_amt'] = debt_df['debt_outstanding_amt'].astype(float)
        return debt_df


    def getTaxPolicyDownload(self,
                tax_policy_save_location:str=r'AmericanRealityClasses/resources/TaxPolicyCenterHistoricRevenues.xlsx'):
        # get directory name sperate from file name
        directory = os.path.dirname(tax_policy_save_location)
        # if directory does not exit it'll be made
        if not os.path.exists(directory):
                os.makedirs(directory)

        # path to link of button on the tax policies page
        base_url = r'https://taxpolicycenter.org/sites/default/files/statistics/spreadsheet/fed_receipt_funds_3.xlsx'
        # Get our data and save it where user chose.
        response = requests.get(base_url)
        if response.status_code == 200:
            with open(tax_policy_save_location, 'wb') as f:
                f.write(response.content)
                print(f"Tax Policy File was successfully saved at {tax_policy_save_location}")
        else:
            print(f"Error getting download form url: {response.status_code}")
            return pd.DataFrame()
        # read in data to paras
        try:
            path = tax_policy_save_location
            #start on main headers
            df = pd.read_excel(path,skiprows=6)
            # drop first row is empty
            df = df.drop(0)
            # rename unnamed columns
            df.rename(columns={"Unnamed: 0":"Fiscal Year","Total":"Receipts Total","Total.1":"Outlays Total","Total.2":"Surplus or Deficit(-) Total"},inplace=True)
            # get rid of dat at the end of table dealing wiith estimating data
            estimate_index = df[df['Fiscal Year'].str.contains('Estimates',case=False,na=False)].index[0]
            df = df.iloc[:estimate_index-2]
            df = df[df['Fiscal Year']!='TQ']
            df['Fiscal Year'] = df['Fiscal Year'].astype(int)
            df['Surplus or Deficit(-) Total'] = df['Surplus or Deficit(-) Total'] * 1_000_000

        except Exception as e:
            print(f"Error loading TaxPolicy file: {e}")
            df = pd.DataFrame()
        return df
    


        
if __name__ == '__main__':
    # instance
    test = Treasury()
    df = test.getHistoricalDebtAPIData()
    print(df.columns.tolist())

