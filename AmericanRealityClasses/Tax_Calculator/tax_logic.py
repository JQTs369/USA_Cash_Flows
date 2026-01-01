# TODO: FAQ links
    # main source - https://taxfoundation.org/data/all/federal/historical-income-tax-rates-brackets/
    # IRS - https://www.irs.gov/statistics/soi-tax-stats-historic-table-2
    # DRED - https://fred.stlouisfed.org/


import json
import os


class TaxDataManager:

    def __init__(self,file_path='data/tax_brackets.json'): # TODO: path to file download
        self.file_path = file_path
        self.data = self.load_data()


    def load_data(self):
        if not os.path.exists(self.file_path):
            print(f'File {self.file_path} does not exist')
            return {}
        try:
            with open(self.file_path) as json_file:
                return json.load(json_file)

        except json.JSONDecodeError:
            print('Error: JSON file is corrupted or formatted incorrectly.')
            return {}
        except Exception as e:
            print(f'File {self.file_path} has an unexpected error occurred: {e}')
            return {}

    def get_year_data(self,year):
        return self.data[year]

    def api_call(selfself):
        pass