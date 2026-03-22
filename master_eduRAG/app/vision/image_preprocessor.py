"""
Image preprocessing and vision initialization for EduSum.
"""

import cv2
import numpy as np
from PIL import Image
from pathlib import Path
from typing import Tuple, Optional


class ImagePreprocessor:
    """Preprocesses images for vision extraction."""

    @staticmethod
    def validate_image(image_path: str) -> bool:
        """
        Validate if file is a valid image.
        
        Args:
            image_path: Path to image file.
            
        Returns:
            True if valid image.
        """
        valid_extensions = {".jpg", ".jpeg", ".png", ".webp", ".heic"}
        ext = Path(image_path).suffix.lower()
        return ext in valid_extensions

    @staticmethod
    def correct_orientation(image_path: str) -> np.ndarray:
        """
        Correct image orientation using EXIF metadata.
        
        Args:
            image_path: Path to image.
            
        Returns:
            Corrected image array.
        """
        try:
            image = Image.open(image_path)
            # Try to get EXIF orientation
            exif_data = image._getexif()
            if exif_data is not None:
                for tag, value in exif_data.items():
                    if tag == 274:  # Orientation tag
                        if value == 3:
                            image = image.rotate(180, expand=True)
                        elif value == 6:
                            image = image.rotate(270, expand=True)
                        elif value == 8:
                            image = image.rotate(90, expand=True)
            return cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"Error correcting orientation: {e}")
            return cv2.imread(image_path)

    @staticmethod
    def resize_image(image: np.ndarray, max_size: Tuple[int, int] = (2000, 2000)) -> np.ndarray:
        """
        Resize image to max size while preserving aspect ratio.
        
        Args:
            image: Image array.
            max_size: Maximum dimensions (width, height).
            
        Returns:
            Resized image.
        """
        height, width = image.shape[:2]
        if width > max_size[0] or height > max_size[1]:
            scale = min(max_size[0] / width, max_size[1] / height)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height))
        return image

    @staticmethod
    def enhance_contrast(image: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast for better visibility (especially for low-contrast scans).
        
        Args:
            image: Image array.
            
        Returns:
            Enhanced image.
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        
        # Merge back
        lab = cv2.merge([l, a, b])
        return cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    @staticmethod
    def preprocess(image_path: str) -> np.ndarray:
        """
        Apply all preprocessing steps.
        
        Args:
            image_path: Path to image.
            
        Returns:
            Preprocessed image array.
        """
        if not ImagePreprocessor.validate_image(image_path):
            raise ValueError(f"Invalid image format: {image_path}")
        
        # Correct orientation
        image = ImagePreprocessor.correct_orientation(image_path)
        
        # Resize
        image = ImagePreprocessor.resize_image(image)
        
        # Enhance contrast
        image = ImagePreprocessor.enhance_contrast(image)
        
        return image
