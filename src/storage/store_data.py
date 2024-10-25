# src/storage/store_data.py

import json

class StoreData:
    def __init__(self, country, surname, given_names, dob, sex, passport_number, raw_mrz):
        """
        Initialize the data storage class with passport information.
        """
        self.country = country
        self.surname = surname
        self.given_names = given_names
        self.dob = dob
        self.sex = sex
        self.passport_number = passport_number
        self.raw_mrz = raw_mrz

    def create_json_object(self):
        """
        Create a JSON object with the passport details.
        """
        passport_data = {
            "Country": self.country,
            "Surname": self.surname,
            "Given Names": self.given_names,
            "Date of Birth": self.dob,
            "Sex": self.sex,
            "Passport Number": self.passport_number,
            "raw_mrz": self.raw_mrz
        }

        return json.dumps(passport_data, indent=4)

    def save_to_file(self, file_path):
        """
        Save the JSON object to a file.
        """
        passport_json = self.create_json_object()
        with open(file_path, 'w') as json_file:
            json_file.write(passport_json)
        print(f"Passport data saved to {file_path}")
