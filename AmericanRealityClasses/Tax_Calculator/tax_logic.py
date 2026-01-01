# TODO: FAQ links
    # main source
    #     Tax Foundation:
            # https://taxfoundation.org/data/all/federal/historical-income-tax-rates-brackets/ - income tax bracket by status
            # https://taxpolicycenter.org/sites/default/files/statistics/pdf/standard_deduction_4.pdf # standard deductions 1970 -2024
            # https://taxfoundation.org/research/all/federal/state-personal-exemptions-post-tcja/ # personal exemption
    # IRS :
        # https://www.irs.gov/statistics/soi-tax-stats-historic-table-2 # income tax brackets
        # https://www.irs.gov/statistics/soi-tax-stats-individual-statistical-tables-by-size-of-adjusted-gross-income # Standard deductions
        # https://www.irs.gov/pub/irs-soi/02inpetr.pdf # -Personal Exemptions and Individual Income Tax Rates
    # DRED:
        # - https://fred.stlouisfed.org/ - income taxes
        # https://fred.stlouisfed.org/series/IITPESP -FRED - Historical Personal Exemptions (Single)

import pandas as pd
import os
import json

class TaxDataManager:
    def __init__(self, income_bracket_file=None):
        # Establish the base directory relative to THIS file
        # Goes up from AmericanRealityClasses/Tax_Calculator/ to USA_Cash_Flows/
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        if income_bracket_file:
            self.income_bracket_file = income_bracket_file
        else:
            self.income_bracket_file = os.path.join(self.base_dir, 'resources', 'tax_foundation_tax_rates.xlsx')

        self.raw_bracket_df = self.load_bracket_data()

    def load_bracket_data(self):
        if os.path.exists(self.income_bracket_file):
            return pd.read_excel(self.income_bracket_file, skiprows=1)
        return pd.DataFrame()

    def get_standard_deduction(self, year, status='single'):
        path = os.path.join(self.base_dir, 'resources', 'standard_deductions.json')
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            # Your JSON structure: data["year"]["status"]
            return data.get(str(year), {}).get(status, 0)
        except Exception:
            return 0

    def get_personal_exemption(self, year, status='single', dependents=0):
        path = os.path.join(self.base_dir, 'resources', 'personal_exemption.json')
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            year_entry = data.get(str(year), {})

            # separate entries for visuals
            base_amt = year_entry.get(status, 0)
            dep_rate = year_entry.get('dependent', 0)
            note = year_entry.get('note', '')

            return base_amt, dep_rate, note
        except Exception:
            return 0, 0, ""

    def get_clean_income_tax_data(self, year=0, status='single'):
        # Matches your mapping: Joint=1, Separate=4, Single=7, HoH=10 - each status is 3 columns of data
        filing_status_map = {
            "single": 7,
            "married_joint": 1,
            "married_separate": 4,
            "head_of_household": 10
        }
        # Filter for the year first
        year_df = self.raw_bracket_df[self.raw_bracket_df.iloc[:, 0] == int(year)]
        start_col = filing_status_map.get(status, 7)

        clean_df = year_df.iloc[:, [0, start_col, start_col + 2]].copy()
        clean_df.columns = ['Year', 'Rate', 'Low']

        # Basic cleaning
        for col in ['Rate', 'Low']:
            clean_df[col] = clean_df[col].astype(str).str.replace('[$,%]', '', regex=True)
            clean_df[col] = pd.to_numeric(clean_df[col], errors='coerce')

        if clean_df['Rate'].max() > 1:
            clean_df['Rate'] = clean_df['Rate'] / 100

        clean_df['High'] = clean_df['Low'].shift(-1).fillna(float('inf'))
        return clean_df

