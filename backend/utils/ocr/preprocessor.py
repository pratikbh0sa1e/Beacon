"""
Image Preprocessor for OCR
Enhances image quality before OCR to improve accuracy
"""

import cv2
import numpy as np
from PIL import Image
import io


class ImagePreprocessor:
    """Preprocess images to improve OCR accuracy"""
    
    @staticmethod
    def preprocess(image_data, preprocessing_level='medium'):
        """
        Preprocess image for better OCR results
        
        Args:
            image_data: bytes or PIL Image or numpy array
            preprocessing_level: 'light', 'medium', 'heavy'
            
        Returns:
            tuple: (processed_image_bytes, preprocessing_applied_dict)
        """
        # Convert to numpy array
        if isinstance(image_data, bytes):
            img = Image.open(io.BytesIO(image_data))
            img_array = np.array(img)
        elif isinstance(image_data, Image.Image):
            img_array = np.array(image_data)
        else:
            img_array = image_data
            
        preprocessing_applied = {
            'grayscale': False,
            'denoised': False,
            'deskewed': False,
            'contrast_enhanced': False,
            'binarized': False
        }
        
        # Convert to grayscale if color
        if len(img_array.shape) == 3:
            img_gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
            preprocessing_applied['grayscale'] = True
        else:
            img_gray = img_array
            
        processed = img_gray.copy()
        
        # Apply preprocessing based on level
        if preprocessing_level in ['medium', 'heavy']:
            # Denoise
            processed = cv2.fastNlMeansDenoising(processed, None, 10, 7, 21)
            preprocessing_applied['denoised'] = True
            
            # Deskew (fix rotation)
            processed = ImagePreprocessor._deskew(processed)
            preprocessing_applied['deskewed'] = True
            
        if preprocessing_level == 'heavy':
            # Enhance contrast using CLAHE
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            processed = clahe.apply(processed)
            preprocessing_applied['contrast_enhanced'] = True
            
            # Binarization (black and white)
            _, processed = cv2.threshold(
                processed, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
            preprocessing_applied['binarized'] = True
            
        # Convert back to bytes
        success, encoded_image = cv2.imencode('.png', processed)
        if not success:
            raise ValueError("Failed to encode processed image")
            
        processed_bytes = encoded_image.tobytes()
        
        return processed_bytes, preprocessing_applied
    
    @staticmethod
    def _deskew(image):
        """Detect and correct skew in image"""
        # Calculate skew angle
        coords = np.column_stack(np.where(image > 0))
        if len(coords) == 0:
            return image
            
        angle = cv2.minAreaRect(coords)[-1]
        
        # Adjust angle
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        # Only deskew if angle is significant (> 0.5 degrees)
        if abs(angle) < 0.5:
            return image
            
        # Rotate image
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        return rotated
    
    @staticmethod
    def detect_and_correct_rotation(image_data, confidence_threshold=0.15):
        """
        Detect if image is rotated (90, 180, 270 degrees) and correct it
        Uses text orientation detection with confidence threshold
        
        Args:
            image_data: bytes or PIL Image or numpy array
            confidence_threshold: Minimum confidence difference to apply rotation (0-1)
            
        Returns:
            tuple: (corrected_image_bytes, rotation_angle_applied)
        """
        # Convert to numpy array
        if isinstance(image_data, bytes):
            img = Image.open(io.BytesIO(image_data))
            img_array = np.array(img)
        elif isinstance(image_data, Image.Image):
            img_array = np.array(image_data)
        else:
            img_array = image_data
            
        # Convert to grayscale if needed
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
            
        # Try to detect text orientation using edge detection
        # This is a heuristic approach - we'll test all 4 orientations
        best_angle = 0
        best_score = 0
        scores = {}
        
        for angle in [0, 90, 180, 270]:
            # Rotate image
            if angle == 0:
                rotated = gray
            elif angle == 90:
                rotated = cv2.rotate(gray, cv2.ROTATE_90_CLOCKWISE)
            elif angle == 180:
                rotated = cv2.rotate(gray, cv2.ROTATE_180)
            else:  # 270
                rotated = cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
            # Calculate "text-likeness" score using horizontal edges
            # Text typically has more horizontal edges when properly oriented
            edges = cv2.Canny(rotated, 50, 150)
            
            # Count horizontal edges (text lines)
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            horizontal_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, horizontal_kernel)
            horizontal_score = np.sum(horizontal_edges > 0)
            
            # Count vertical edges (should be less for normal text)
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            vertical_edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, vertical_kernel)
            vertical_score = np.sum(vertical_edges > 0)
            
            # Text should have more horizontal than vertical edges
            # Also consider aspect ratio (text documents are usually taller than wide)
            h, w = rotated.shape
            aspect_ratio = h / w if w > 0 else 1
            aspect_bonus = 1.2 if 1.2 < aspect_ratio < 1.8 else 1.0
            
            score = (horizontal_score - (vertical_score * 0.3)) * aspect_bonus
            scores[angle] = score
            
            if score > best_score:
                best_score = score
                best_angle = angle
        
        # Normalize scores
        max_score = max(scores.values()) if scores.values() else 1
        normalized_scores = {k: v / max_score for k, v in scores.items()}
        
        # Only apply rotation if confidence is high enough
        # (i.e., the best angle is significantly better than 0°)
        confidence = normalized_scores[best_angle] - normalized_scores[0]
        
        if best_angle != 0 and confidence < confidence_threshold:
            # Not confident enough, keep original orientation
            print(f"  → Rotation detection not confident enough ({confidence:.2f} < {confidence_threshold}), keeping original")
            best_angle = 0
        
        # Apply best rotation to original image
        if best_angle == 0:
            corrected = img_array
        elif best_angle == 90:
            corrected = cv2.rotate(img_array, cv2.ROTATE_90_CLOCKWISE)
        elif best_angle == 180:
            corrected = cv2.rotate(img_array, cv2.ROTATE_180)
        else:  # 270
            corrected = cv2.rotate(img_array, cv2.ROTATE_90_COUNTERCLOCKWISE)
        
        # Convert back to bytes
        success, encoded_image = cv2.imencode('.png', corrected)
        if not success:
            raise ValueError("Failed to encode corrected image")
            
        corrected_bytes = encoded_image.tobytes()
        
        return corrected_bytes, best_angle
    
    @staticmethod
    def detect_if_scanned(image_data):
        """
        Detect if an image is likely a scanned document
        Returns confidence score (0-1)
        """
        # Convert to numpy array
        if isinstance(image_data, bytes):
            img = Image.open(io.BytesIO(image_data))
            img_array = np.array(img)
        else:
            img_array = image_data
            
        # Convert to grayscale
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
            
        # Calculate metrics
        # 1. Edge density (scanned docs have more edges)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # 2. Noise level (scanned docs have more noise)
        noise = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        # 3. Contrast (scanned docs often have lower contrast)
        contrast = gray.std()
        
        # Simple heuristic (can be improved with ML)
        is_scanned_score = 0.0
        
        if edge_density > 0.1:
            is_scanned_score += 0.3
        if noise < 500:
            is_scanned_score += 0.3
        if contrast < 60:
            is_scanned_score += 0.4
            
        return is_scanned_score
