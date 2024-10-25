# src/formatter/format_mrz.py

import re
from datetime import datetime
import os

def parse_mrz(mrz_lines):
    """
    Parses MRZ lines using regular expressions to extract passport information.
    """
    mrz_data = {}

    # Combine MRZ lines
    mrz_text = ''.join(mrz_lines).replace('\n', '').replace('\r', '')
    mrz_text = mrz_text.strip()

    # Transform any characters that are not letters, numbers, or '<' to '<'
    mrz_text = re.sub(r'[^A-Z0-9<]', '<', mrz_text.upper())

    # Regular expression patterns based on MRZ structure
    pattern = (
        r'P[<A-Z]'                                   # Document code ('P<' or 'PA' or 'P[A-Z]')
        r'(?P<issuing_country>[A-Z]{3})'             # Issuing country
        r'(?P<names>[A-Z<]+)'                        # Names (surname<<given names)
        r'.*'                                        # Any characters in between
        r'(?P<passport_number>[A-Z0-9<]{9})'         # Passport number
        r'(?P<passport_number_cd>[0-9<])'            # Check digit (may be '<' if missing)
        r'(?P<nationality>[A-Z]{3})'                 # Nationality
        r'(?P<dob>[0-9<]{6})'                        # Date of birth (may contain '<')
        r'(?P<dob_cd>[0-9<])'                        # Check digit
        r'(?P<sex>[MF<])'                            # Sex
        r'(?P<personal_number>[A-Z0-9<]{14})'        # Personal number
        r'(?P<personal_number_cd>[0-9<])'            # Check digit
        r'(?P<final_cd>[0-9<])'                      # Final check digit
    )

    match = re.search(pattern, mrz_text)

    if match:
        # Extract data from named groups
        mrz_data['issuing_country'] = match.group('issuing_country')
        names_field = match.group('names')
        mrz_data['passport_number'] = match.group('passport_number').replace('<', '')
        mrz_data['nationality'] = match.group('nationality')
        mrz_data['date_of_birth'] = match.group('dob')
        mrz_data['sex'] = match.group('sex')
        mrz_data['personal_number'] = match.group('personal_number').replace('<', '')

        # Parse names
        surname, given_names = parse_names(names_field)
        mrz_data['surname'] = surname
        mrz_data['given_names'] = given_names
    else:
        mrz_data = handle_partial_mrz(mrz_text)
    return mrz_data

def handle_partial_mrz(mrz_text):
    """
    Handles the case when the MRZ does not fully match the pattern.
    This function tries to extract as much data as possible from a partial or corrupted MRZ string.
    """
    mrz_data = {
        'issuing_country': '',
        'surname': '',
        'given_names': [],
        'passport_number': '',
        'nationality': '',
        'date_of_birth': '',
        'sex': '',
        'personal_number': ''
    }

    # Try extracting basic fields with relaxed matching
    # Initialize all fields to empty strings or 'Unknown'
    try:
        issuing_country = mrz_text[2:5]
        mrz_data['issuing_country'] = issuing_country if issuing_country.isalpha() else ''
    except IndexError:
        pass

    try:
        # Surname and given names are harder to extract from partial data
        names_field = mrz_text[5:44]
        surname, given_names = parse_names(names_field)
        mrz_data['surname'] = surname
        mrz_data['given_names'] = given_names
    except IndexError:
        pass

    try:
        # Passport number (with defaulting for missing parts)
        passport_number = mrz_text[44:53].replace('<', '')
        mrz_data['passport_number'] = passport_number if passport_number else ''
    except IndexError:
        pass

    try:
        # Nationality code
        nationality = mrz_text[54:57]
        mrz_data['nationality'] = nationality if nationality.isalpha() else ''
    except IndexError:
        pass

    try:
        # Date of birth with relaxed pattern
        dob = mrz_text[57:63]
        mrz_data['date_of_birth'] = dob if dob else ''
    except IndexError:
        pass

    try:
        # Sex mapping
        sex_code = mrz_text[64]
        mrz_data['sex'] = map_sex(sex_code)
    except IndexError:
        mrz_data['sex'] = ''
    return mrz_data

def parse_names(names_field):
    """
    Parses the names field to extract surname and given names.
    """
    parts = names_field.split('<<', 1)
    surname = parts[0].replace('<', '').strip()
    given_names = ''
    if len(parts) > 1:
        given_names = parts[1].replace('<', ' ').strip()
    given_names_list = given_names.split()

    return surname, given_names_list

def convert_date(date_str):
    """
    Converts a date from YYMMDD format to YYYY-MM-DD format,
    determining the correct century.
    """
    date_str = date_str.replace('<', '0')  # Replace missing digits with '0'
    try:
        date_obj = datetime.strptime(date_str, '%y%m%d')
        current_year = datetime.now().year % 100
        century = datetime.now().year - current_year
        year = int(date_str[:2])
        if year > current_year:
            date_obj = date_obj.replace(year=century - 100 + year)
        else:
            date_obj = date_obj.replace(year=century + year)
        return date_obj.strftime('%Y-%m-%d')
    except ValueError:
        return 'Invalid Date'

def map_sex(sex_code):
    """
    Maps the sex code to a full description.
    """
    sex_map = {'M': 'Male', 'F': 'Female', '<': 'Unspecified'}
    return sex_map.get(sex_code, 'Unknown')
