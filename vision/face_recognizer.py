import cv2
import os
import numpy as np
import json
import sys
from pathlib import Path

# Add root folder to sys.path to allow absolute imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.db_manager import DatabaseManager

VISION_DIR = Path(__file__).resolve().parent
DATASET_DIR = VISION_DIR / "dataset"
MODEL_PATH = VISION_DIR / "face_model.yml"

class FaceRecognizer:
    def __init__(self):
        # Create directories if they don't exist
        os.makedirs(DATASET_DIR, exist_ok=True)
        
        # Load local Haar Cascade face classifier
        cascade_path = str(VISION_DIR / "haarcascade_frontalface_default.xml")
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        
        # Initialize LBPH Face Recognizer
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.model_loaded = False
        
        # Load database to read name mappings
        self.db = DatabaseManager()
        self.load_model()

    def load_model(self):
        """Loads the trained face recognizer model weights if they exist."""
        if MODEL_PATH.exists():
            try:
                self.recognizer.read(str(MODEL_PATH))
                self.model_loaded = True
                print("[Face Vision] Loaded trained face model.")
            except Exception as e:
                print(f"[Face Vision Error] Failed to read face model: {e}")
                self.model_loaded = False
        else:
            self.model_loaded = False

    def detect_face(self, gray_img):
        """Returns coordinates (x, y, w, h) of the largest face detected in a grayscale image."""
        faces = self.face_cascade.detectMultiScale(
            gray_img, scaleFactor=1.2, minNeighbors=5, minSize=(100, 100)
        )
        if len(faces) == 0:
            return None
            
        # Return the largest face by area (w * h)
        largest_face = max(faces, key=lambda f: f[2] * f[3])
        return largest_face

    def save_sample(self, gray_img, rect, user_name, sample_num):
        """Crops, resizes, and saves a face sample for training."""
        x, y, w, h = rect
        face_crop = gray_img[y:y+h, x:x+w]
        # Resize to a consistent square dimension
        face_resized = cv2.resize(face_crop, (200, 200))
        
        user_dir = DATASET_DIR / user_name.lower().strip()
        os.makedirs(user_dir, exist_ok=True)
        
        filepath = user_dir / f"face.{sample_num}.jpg"
        cv2.imwrite(str(filepath), face_resized)
        return str(filepath)

    def train_classifier(self):
        """Trains the LBPH classifier on all captured user directories in datasets."""
        subdirs = [d for d in DATASET_DIR.iterdir() if d.is_dir()]
        if not subdirs:
            print("[Face Vision] No face datasets found to train on.")
            return False
            
        face_samples = []
        ids = []
        
        # Load or create integer-to-name mapping
        mappings = {}
        mapping_str = self.db.get_preference("face_mappings", "{}")
        try:
            mappings = json.loads(mapping_str)
        except Exception:
            mappings = {}
            
        current_id = len(mappings) + 1
        
        for user_dir in subdirs:
            name = user_dir.name.strip().lower()
            
            # Find or assign ID to this user
            user_id = None
            for key, val in mappings.items():
                if val.lower() == name:
                    user_id = int(key)
                    break
            
            if user_id is None:
                user_id = current_id
                mappings[str(user_id)] = name
                current_id += 1
                
            # Read all images in directory
            for img_file in user_dir.glob("face.*.jpg"):
                img_gray = cv2.imread(str(img_file), cv2.IMREAD_GRAYSCALE)
                if img_gray is not None:
                    face_samples.append(img_gray)
                    ids.append(user_id)
        
        if len(face_samples) == 0:
            print("[Face Vision] No valid training images found.")
            return False
            
        try:
            # Train the recognizer
            self.recognizer.train(face_samples, np.array(ids))
            self.recognizer.write(str(MODEL_PATH))
            self.model_loaded = True
            
            # Commit mappings to database preferences
            self.db.set_preference("face_mappings", json.dumps(mappings))
            print(f"[Face Vision] Model trained successfully! Registered mappings: {mappings}")
            return True
        except Exception as e:
            print(f"[Face Vision Error] Training failed: {e}")
            return False

    def predict(self, frame):
        """Analyzes a raw BGR frame and returns (name, confidence, face_rect).
        Confidence is the LBPH distance metric: lower is better (0 is perfect match).
        Returns (None, 0.0, None) if no face is recognized or no model is loaded.
        """
        if not self.model_loaded:
            return None, 0.0, None
            
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rect = self.detect_face(gray)
        if rect is None:
            return None, 0.0, None
            
        x, y, w, h = rect
        face_crop = gray[y:y+h, x:x+w]
        face_resized = cv2.resize(face_crop, (200, 200))
        
        try:
            # Run prediction
            label_id, confidence = self.recognizer.predict(face_resized)
            
            # Retrieve name from mappings
            mapping_str = self.db.get_preference("face_mappings", "{}")
            mappings = json.loads(mapping_str)
            name = mappings.get(str(label_id), "Unknown")
            
            return name, confidence, rect
        except Exception as e:
            print(f"[Face Vision Error] Prediction failed: {e}")
            return None, 0.0, None

if __name__ == "__main__":
    recognizer = FaceRecognizer()
    print("Haar Cascade Loaded:", recognizer.face_cascade is not None)
    print("Model Loaded:", recognizer.model_loaded)
    print("Training dataset present:")
    recognizer.train_classifier()
