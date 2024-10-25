import json
import os

class DataManager:
    """
    Handles loading and saving of parsed data to prevent duplicates.
    """
    def __init__(self, output_folder):
        self.output_folder = output_folder
        self.documents_folder = os.path.join(output_folder, 'documents')
        self.faces_folder = os.path.join(output_folder, 'faces')
        self.parsed_data_file = os.path.join(output_folder, 'parsed_data.json')

        # Ensure the main output folder and subdirectories exist
        self._ensure_directories()

        # Load the parsed data from the JSON file
        self.parsed_data = self.load_parsed_data()

    def _ensure_directories(self):
        """
        Ensure that the output, documents, and faces directories exist.
        """
        os.makedirs(self.output_folder, exist_ok=True)
        os.makedirs(self.documents_folder, exist_ok=True)
        os.makedirs(self.faces_folder, exist_ok=True)

    def load_parsed_data(self):
        """
        Load existing parsed data from JSON file.
        """
        if os.path.exists(self.parsed_data_file):
            with open(self.parsed_data_file, 'r') as f:
                return json.load(f)
        else:
            return []

    def is_duplicate(self, passport_number):
        """
        Check if a passport number already exists in the parsed data.
        """
        return any(entry['Passport Number'] == passport_number for entry in self.parsed_data)

    def add_entry(self, entry):
        """
        Add a new entry to the parsed data.
        """
        self.parsed_data.append(entry)

    def save_parsed_data(self):
        """
        Save the parsed data to the JSON file.
        """
        with open(self.parsed_data_file, 'w') as f:
            json.dump(self.parsed_data, f, indent=4)

    def get_document_folder(self):
        """
        Return the path to the documents folder.
        """
        return self.documents_folder

    def get_faces_folder(self):
        """
        Return the path to the faces folder.
        """
        return self.faces_folder
