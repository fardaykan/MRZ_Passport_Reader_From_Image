# src/cropper/crop.py

from ultralytics import YOLO
import cv2
import os
import numpy as np


class Cropper:
    def __init__(self, model_path):
        # Load the YOLO model
        self.model = YOLO(model_path)

    def crop_image_v1(self, image_path, output_directory):
        """
        Original v1 cropping logic.
        This will be used as a fallback if v2 fails to crop an image.
        """
        # Perform inference
        results = self.model(image_path)

        # Load the original image for cropping
        original_image = cv2.imread(image_path)

        # Initialize variables for book boxes
        smallest_book_box = None
        smallest_area = float("inf")  # Start with a very large area
        largest_book_box = None
        largest_area = 0  # Start with zero for the largest area

        # Iterate through results to find the smallest book bounding box including a person
        for result in results:
            boxes = result.boxes  # Access the detection boxes
            if boxes is not None and len(boxes) > 0:
                boxes_xyxy = boxes.xyxy.cpu().numpy()  # Convert to NumPy array
                classes = boxes.cls.cpu().numpy()  # Get class indices

                # Loop through boxes to find the smallest book that includes the person
                for i in range(len(boxes_xyxy)):
                    # Check if the current box is a book (ID 73)
                    if classes[i] == 73:
                        book_box = boxes_xyxy[i]
                        book_x1, book_y1, book_x2, book_y2 = book_box

                        # Calculate area of the book box
                        area = (book_x2 - book_x1) * (book_y2 - book_y1)

                        # Track the largest book box found
                        if area > largest_area:
                            largest_area = area
                            largest_book_box = book_box

                        # Check for any person (ID 0) boxes
                        for j in range(len(boxes_xyxy)):
                            if classes[j] == 0:  # Check if it's a person
                                person_box = boxes_xyxy[j]
                                person_x1, person_y1, person_x2, person_y2 = person_box

                                # Check if the book box includes the person box
                                if (
                                    book_x1 <= person_x2
                                    and book_x2 >= person_x1
                                    and book_y1 <= person_y2
                                    and book_y2 >= person_y1
                                ):

                                    # Check if this is the smallest area found
                                    if area < smallest_area:
                                        smallest_area = area
                                        smallest_book_box = book_box

        # Determine which box to save
        if smallest_book_box is not None:
            # Include padding to the smallest book box to ensure it includes the person
            padding = 20  # Adjust padding as needed
            x1, y1, x2, y2 = smallest_book_box
            x1 = max(int(x1) - padding, 0)
            y1 = max(int(y1) - padding, 0)
            x2 = min(int(x2) + padding, original_image.shape[1])
            y2 = min(int(y2) + padding, original_image.shape[0])

            # Crop the bounding box from the original image
            cropped_image = original_image[y1:y2, x1:x2]

            # Save the cropped image in the specified output directory
            result_cropped_path = os.path.join(output_directory, "result_cropped.jpg")
            cv2.imwrite(result_cropped_path, cropped_image)
            print(f"Cropped image saved as: {result_cropped_path}")
        elif largest_book_box is not None:
            # If no valid book box was found, save the largest book box instead
            x1, y1, x2, y2 = largest_book_box.astype(int)
            # Crop the largest book box from the original image
            cropped_image = original_image[y1:y2, x1:x2]

            # Save the cropped image in the specified output directory
            result_cropped_path = os.path.join(output_directory, "result_cropped.jpg")
            cv2.imwrite(result_cropped_path, cropped_image)
            print(
                f"No valid book detected that includes a person. Largest book cropped and saved as: {result_cropped_path}"
            )
        else:
            # If no book boxes are present, save the original image
            result_cropped_path = os.path.join(output_directory, "result_cropped.jpg")
            cv2.imwrite(result_cropped_path, original_image)
            print(
                "No books detected in the image. Original image saved as cropped image."
            )

    def crop_image_v2(self, image_path, output_directory):
        """
        New v2 cropping logic.
        """
        # Perform inference
        results = self.model(image_path)

        # Load the original image for cropping
        original_image = cv2.imread(image_path)

        # Initialize variables for person detection
        person_boxes = []

        # Detect persons
        for result in results:
            boxes = result.boxes  # Access the detection boxes
            if boxes is not None and len(boxes) > 0:
                boxes_xyxy = boxes.xyxy.cpu().numpy()  # Convert to NumPy array
                classes = boxes.cls.cpu().numpy()  # Get class indices

                # Loop through boxes to find all persons (ID 0)
                for i in range(len(boxes_xyxy)):
                    if classes[i] == 0:  # Person detected
                        person_boxes.append(boxes_xyxy[i])  # Store person bounding box

        # If no persons detected, print message and return
        if len(person_boxes) == 0:
            print("No persons detected in the image. Skipping contour adjustment.")
            return False

        # Select the person with the lowest y2 coordinate (the bottom-most person)
        person_boxes = sorted(
            person_boxes, key=lambda box: box[3]
        )  # Sort by the y2 coordinate (index 3)
        person_box = person_boxes[-1]  # The last one will be the bottom-most

        # Extract person box coordinates
        person_x1, person_y1, person_x2, person_y2 = map(int, person_box)

        # Detect contours to find the smallest contour that contains the person
        gray_image = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)
        blurred_image = cv2.GaussianBlur(gray_image, (5, 5), 0)
        edged_image = cv2.Canny(blurred_image, 50, 150)

        # Find contours in the image
        contours, _ = cv2.findContours(
            edged_image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        smallest_contour = None
        smallest_area = float("inf")  # Initialize to infinity for finding the minimum
        padding = 10  # Reduced padding to minimize background

        for contour in contours:
            # Get the bounding box of the contour
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = float(w) / h if h != 0 else 0

            # Check if the contour's bounding box contains the person box
            if (
                x <= person_x1
                and (x + w) >= person_x2
                and y <= person_y1
                and (y + h) >= person_y2
            ):
                if (
                    0.5 < aspect_ratio < 1.7
                ):  # Aspect ratio check for a rectangular page
                    # Calculate the area of the contour
                    area = cv2.contourArea(contour)

                    # Update the smallest contour if this one is smaller
                    if area < smallest_area:
                        smallest_area = area
                        smallest_contour = (x, y, w, h)

        if smallest_contour is not None:
            # Unpack the smallest contour's bounding box
            x, y, w, h = smallest_contour

            # Expand the bounding box slightly to include more of the page, but avoid too much background
            x = max(0, x - padding)
            y = max(0, y - padding)
            w = min(original_image.shape[1], x + w + padding) - x
            h = min(original_image.shape[0], y + h + padding) - y

            # Crop the bounding box from the original image
            cropped_image = original_image[y : y + h, x : x + w]

            # Save the cropped image in the specified output directory
            result_cropped_path = os.path.join(output_directory, "result_cropped.jpg")
            cv2.imwrite(result_cropped_path, cropped_image)
            print(
                f"Smallest contour containing the bottom-most person detected and cropped. Image saved as: {result_cropped_path}"
            )
            return True
        else:
            # If no contour contains the person, print a message and return False
            print("No contour containing the person found. Saving original image.")
            return False

    def crop_image(self, image_path, output_directory):
        # First, try to run v2 logic
        v2_success = self.crop_image_v2(image_path, output_directory)

        # If v2 fails (returns False), fall back to v1 logic
        if not v2_success:
            print("Falling back to v1 logic.")
            self.crop_image_v1(image_path, output_directory)
