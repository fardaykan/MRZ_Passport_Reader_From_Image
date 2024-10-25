import cv2
import os
import re
from formatter.format_mrz import parse_mrz, convert_date, map_sex
from storage.store_data import StoreData


class PassportProcessor:
    """
    Processes individual passport images.
    """

    def __init__(self, reader, cropper, data_manager, weights_dir):
        self.reader = reader
        self.cropper = cropper
        self.data_manager = data_manager
        self.weights_dir = weights_dir

    def process_image(self, image_file, input_folder):
        image_path = os.path.join(input_folder, image_file)

        # Perform MRZ reading with preprocessing and face detection
        text_results, segmented_image, detected_face = self.reader.predict(
            image_path,
            do_facedetect=True,
            preprocess_config={
                "do_preprocess": True,
                "skewness": True,
                "delete_shadow": True,
                "clear_background": True,
            },
        )

        # Extract the recognized text directly from the prediction results
        mrz_lines = [result[1] for result in text_results]  # Only keep the recognized text

        try:
            # Process and parse MRZ using regular expressions
            mrz_data = parse_mrz(mrz_lines)

            # Safely retrieve values from mrz_data, defaulting to an empty string if not found
            issuing_country = mrz_data.get("issuing_country", "")
            surname = mrz_data.get("surname", "")
            given_names = " ".join(mrz_data.get("given_names", []))  # Join given names
            passport_number = mrz_data.get("passport_number", "")
            dob = convert_date(mrz_data.get("date_of_birth", ""))
            sex = map_sex(mrz_data.get("sex", ""))

            # Skip duplicates
            if self.data_manager.is_duplicate(passport_number):
                print(
                    f"Duplicate entry detected for passport number {passport_number}. Skipping."
                )
                return

            # Print extracted passport information
            print("----- Extracted Passport Information -----")
            print(f"Country: {issuing_country}")
            print(f"Surname: {surname}")
            print(f"Given Names: {given_names}")
            print(f"Date of Birth: {dob}")
            print(f"Sex: {sex}")
            print(f"Passport Number: {passport_number}")

            # Clean up raw MRZ (remove newline, blank characters, and spaces)
            raw_mrz = (
                "".join(mrz_lines)
                .replace("\n", "")
                .replace("\r", "")
                .replace(" ", "")
                .strip()
            )
            raw_mrz = raw_mrz.upper()
            raw_mrz = re.sub(r"[^A-Z0-9]", "<", raw_mrz)

            # Store the extracted data using StoreData class and save it as a JSON object
            store_data = StoreData(
                country=issuing_country,
                surname=surname,
                given_names=given_names,
                dob=dob,
                sex=sex,
                passport_number=passport_number,
                raw_mrz=raw_mrz,
            )

            # Append the new data to the parsed data list
            self.data_manager.add_entry(
                {
                    "Country": issuing_country,
                    "Surname": surname,
                    "Given Names": given_names,
                    "Date of Birth": dob,
                    "Sex": sex,
                    "Passport Number": passport_number,
                    "raw_mrz": raw_mrz,
                }
            )

            # Save the updated parsed data to the file
            self.data_manager.save_parsed_data()

            # Save the segmented image and detected face with specific naming conventions
            if detected_face is not None:
                face_image_path = os.path.join(
                    self.data_manager.faces_folder,
                    f"{given_names}_{surname}_{passport_number}_face.jpg",
                )
                cv2.imwrite(face_image_path, detected_face)
                print(f"Face image saved as: {face_image_path}")

            # Perform cropping
            self.cropper.crop_image(image_path, self.data_manager.output_folder)

            # Save cropped document with a specific naming convention
            document_image_path = os.path.join(
                self.data_manager.documents_folder,
                f"{given_names}_{surname}_{passport_number}_document.jpg",
            )
            os.rename(
                os.path.join(self.data_manager.output_folder, "result_cropped.jpg"),
                document_image_path,
            )
            print(f"Cropped document image saved as: {document_image_path}")

        except ValueError as ve:
            print(f"Error parsing MRZ: {ve}")
        except FileNotFoundError:
            print(f"File not found: {image_path}")
