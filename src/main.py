# src/main.py

import os
from mrz_reader.reader import MRZReader
from cropper.crop import Cropper
from storage.data_manager import DataManager
from processing.passport_processor import PassportProcessor

def main():
    # Define the project root directory (one level up from src/)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Define the weights directory
    weights_dir = os.path.join(os.path.dirname(__file__), 'weights')

    # Initialize the MRZReader with updated paths
    reader = MRZReader(
        facedetection_protxt=os.path.join(weights_dir, "face_detector/deploy.prototxt"),
        facedetection_caffemodel=os.path.join(weights_dir, "face_detector/res10_300x300_ssd_iter_140000.caffemodel"),
        segmentation_model=os.path.join(weights_dir, "mrz_detector/mrz_seg.tflite"),
        easy_ocr_params={"lang_list": ["en"], "gpu": False}
    )

    # Initialize the Cropper with the YOLO model path
    cropper = Cropper(os.path.join(weights_dir, 'yolo/yolo11n.pt'))

    # Input and output directories
    input_folder = os.path.join(project_root, 'inputs')
    output_folder = os.path.join(project_root, 'outputs')
    os.makedirs(output_folder, exist_ok=True)

    # Initialize DataManager
    data_manager = DataManager(output_folder)

    # Initialize PassportProcessor
    processor = PassportProcessor(reader, cropper, data_manager, weights_dir)

    # Loop through each image in the input folder
    for image_file in os.listdir(input_folder):
        if image_file.lower().endswith(('.png', '.jpg', '.jpeg')):
            print(f"Processing image: {image_file}")
            processor.process_image(image_file, input_folder)

if __name__ == "__main__":
    main()
