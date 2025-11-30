from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
import cv2
import numpy as np
import tensorflow as tf
import os
import uuid
import json
from datetime import datetime
import time
import logging
import base64
from werkzeug.utils import secure_filename
# Add this import at the top with other imports
from tensorflow.keras.layers import LSTM
import matplotlib.pyplot as plt
import matplotlib.cm as cm

# Set TensorFlow to be deterministic for consistent results
os.environ['TF_DETERMINISTIC_OPS'] = '1'
os.environ['TF_CUDNN_DETERMINISTIC'] = '1'
tf.config.experimental.enable_op_determinism()

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    handlers=[logging.FileHandler("app.log"), logging.StreamHandler()])
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'static/uploads'
FRAMES_FOLDER = 'static/frames'
IMAGE_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'images')
VIDEO_UPLOAD_FOLDER = os.path.join(UPLOAD_FOLDER, 'videos')
app.config['IMAGE_UPLOAD_FOLDER'] = IMAGE_UPLOAD_FOLDER
app.config['VIDEO_UPLOAD_FOLDER'] = VIDEO_UPLOAD_FOLDER
app.config['FRAMES_FOLDER'] = FRAMES_FOLDER
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv'}

# Create necessary directories
os.makedirs(IMAGE_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(VIDEO_UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FRAMES_FOLDER, exist_ok=True)
os.makedirs('model', exist_ok=True)
os.makedirs('logs', exist_ok=True)

# Model paths - Updated to match your actual model files
IMAGE_MODEL_PATH = os.path.join('model', 'new_xception.h5')
VIDEO_MODEL_PATH = os.path.join('model', 'deepfake_detection_model.h5')

# Global variables to store the models
image_model = None
video_model = None

# Add this custom LSTM class after the imports and before the model loading functions
class CustomLSTM(LSTM):
    """Custom LSTM class to handle deprecated time_major parameter"""
    def __init__(self, *args, **kwargs):
        # Remove the deprecated time_major parameter if present
        kwargs.pop('time_major', None)
        super().__init__(*args, **kwargs)

def load_image_model():
    global image_model
    if os.path.exists(IMAGE_MODEL_PATH):
        try:
            # Try loading with custom objects if needed
            logger.info(f"Attempting to load image model from {IMAGE_MODEL_PATH}")
            
            # First try normal loading
            image_model = tf.keras.models.load_model(IMAGE_MODEL_PATH)
            logger.info("Image model loaded successfully!")
            
            # Test the model with a dummy input to ensure it works
            dummy_input = np.random.random((1, 299, 299, 3)).astype(np.float32)
            test_prediction = image_model.predict(dummy_input, verbose=0)
            logger.info(f"Model test successful. Output shape: {test_prediction.shape}")
            
            return True
        except Exception as e:
            logger.error(f"Error loading image model: {e}")
            try:
                # Fallback: Load with compile=False
                logger.info("Trying to load with compile=False...")
                image_model = tf.keras.models.load_model(IMAGE_MODEL_PATH, compile=False)
                
                # Test the model
                dummy_input = np.random.random((1, 299, 299, 3)).astype(np.float32)
                test_prediction = image_model.predict(dummy_input, verbose=0)
                logger.info(f"Image model loaded with compile=False. Output shape: {test_prediction.shape}")
                return True
            except Exception as e2:
                logger.error(f"Failed to load image model even with fallback: {e2}")
                return False
    else:
        logger.warning(f"Image model file not found at {IMAGE_MODEL_PATH}. Using demo mode.")
        return False

def load_video_model():
    global video_model
    if os.path.exists(VIDEO_MODEL_PATH):
        try:
            logger.info(f"Attempting to load video model from {VIDEO_MODEL_PATH}")
            # Define custom objects to handle deprecated parameters
            custom_objects = {
                'LSTM': CustomLSTM,
                'CustomLSTM': CustomLSTM
            }
            # First try loading with custom objects
            video_model = tf.keras.models.load_model(VIDEO_MODEL_PATH, custom_objects=custom_objects)
            logger.info("Video model loaded successfully with custom objects!")
            # Test the model with a dummy input
            dummy_input = np.random.random((1, 224, 224, 3)).astype(np.float32)
            test_prediction = video_model.predict(dummy_input, verbose=0)
            logger.info(f"Video model test successful. Output shape: {test_prediction.shape}")
            return True
        except Exception as e:
            logger.error(f"Error loading video model with custom objects: {e}")
            try:
                # Fallback: Load with compile=False and custom objects
                logger.info("Trying to load video model with compile=False and custom objects...")
                custom_objects = {
                    'LSTM': CustomLSTM,
                    'CustomLSTM': CustomLSTM
                }
                video_model = tf.keras.models.load_model(VIDEO_MODEL_PATH, compile=False, custom_objects=custom_objects)
                # Test the model
                dummy_input = np.random.random((1, 224, 224, 3)).astype(np.float32)
                test_prediction = video_model.predict(dummy_input, verbose=0)
                logger.info(f"Video model loaded with compile=False and custom objects. Output shape: {test_prediction.shape}")
                return True
            except Exception as e2:
                logger.error(f"Failed to load video model even with custom objects fallback: {e2}")
                try:
                    # Final fallback: Try to load and rebuild the model
                    logger.info("Attempting final fallback: loading model architecture and weights separately...")
                    # Load model without compilation
                    video_model = tf.keras.models.load_model(VIDEO_MODEL_PATH, compile=False)
                    # Rebuild the model to fix compatibility issues
                    logger.info("Rebuilding model to fix compatibility...")
                    # Get the model's configuration
                    config = video_model.get_config()
                    # Recursively remove time_major from all LSTM layers
                    def clean_lstm_config(layer_config):
                        if layer_config.get('class_name') == 'LSTM':
                            if 'time_major' in layer_config.get('config', {}):
                                del layer_config['config']['time_major']
                                logger.info("Removed time_major from LSTM layer config")
                        # Recursively clean nested layers (e.g., inside Bidirectional, wrappers, etc.)
                        if 'config' in layer_config:
                            for key in ['layer', 'cell']:
                                if key in layer_config['config'] and isinstance(layer_config['config'][key], dict):
                                    clean_lstm_config(layer_config['config'][key])
                        return layer_config
                    if 'layers' in config:
                        for layer in config['layers']:
                            clean_lstm_config(layer)
                    # Rebuild model from cleaned config
                    rebuilt_model = tf.keras.Model.from_config(config)
                    # Copy weights from original model
                    rebuilt_model.set_weights(video_model.get_weights())
                    video_model = rebuilt_model
                    # Test the rebuilt model
                    dummy_input = np.random.random((1, 224, 224, 3)).astype(np.float32)
                    test_prediction = video_model.predict(dummy_input, verbose=0)
                    logger.info(f"Rebuilt video model test successful. Output shape: {test_prediction.shape}")
                    return True
                except Exception as e3:
                    logger.error(f"All fallback methods failed: {e3}")
                    return False
    else:
        logger.warning(f"Video model file not found at {VIDEO_MODEL_PATH}. Using demo mode.")
        return False

# Try to load the models at startup
logger.info("Loading models at startup...")
image_model_loaded = load_image_model()
video_model_loaded = load_video_model()

# Log the final status
if image_model_loaded:
    logger.info("✅ IMAGE MODEL: Successfully loaded and ready for predictions")
else:
    logger.error("❌ IMAGE MODEL: Failed to load - will use demo mode")

if video_model_loaded:
    logger.info("✅ VIDEO MODEL: Successfully loaded and ready for predictions")
else:
    logger.error("❌ VIDEO MODEL: Failed to load - will use demo mode")

def allowed_image_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def allowed_video_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_VIDEO_EXTENSIONS

def preprocess_image_for_model(image, target_size=(299, 299)):
    """
    Preprocess image for model prediction with proper normalization
    """
    try:
        # Ensure image is in the right format
        if image is None:
            raise ValueError("Input image is None")
        # Convert to RGB if needed
        if len(image.shape) == 3:
            if image.shape[2] == 4:  # RGBA
                image = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
            elif image.shape[2] == 3:  # BGR
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        elif len(image.shape) == 2:  # Grayscale
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
        # Resize to target size
        image = cv2.resize(image, target_size)
        # Ensure the image is float32 and normalized to [0, 1]
        image = image.astype(np.float32)
        if image.max() > 1.0:
            image = image / 255.0
        # Add batch dimension
        image = np.expand_dims(image, axis=0)
        logger.info(f"Preprocessed image shape: {image.shape}, dtype: {image.dtype}, range: [{image.min():.3f}, {image.max():.3f}]")
        return image
    except Exception as e:
        logger.error(f"Error preprocessing image: {e}")
        return None

def predict_image(image):
    global image_model, image_model_loaded
    
    # Log whether we're using real model or demo mode
    if image_model_loaded and image_model is not None:
        logger.info("Using REAL deepfake detection model for prediction")
        logger.info(f"Model type: {type(image_model).__name__}")
        print("🔍 Using REAL deepfake detection model for prediction")
    else:
        logger.warning("WARNING: No real model loaded, will use demo mode!")
        logger.info("Using DEMO mode for prediction (no real model loaded)")
        print("⚠️  WARNING: Using DEMO mode (no real model loaded)")
    
    # If model is not loaded, try to load it again
    if not image_model_loaded:
        logger.info("Attempting to reload image model...")
        image_model_loaded = load_image_model()
        
    if not image_model_loaded or image_model is None:
        # If we don't have a real model, use a demo mode with simulated results
        logger.warning("No image model loaded, using demo mode with simulated results")
        return simulate_prediction(image)
    
    try:
        processed_image = preprocess_image_for_model(image)
        if processed_image is None:
            return "Error", 0.0, "Failed to preprocess image"
            
        # Add a small delay to simulate processing time
        time.sleep(0.5)
        
        logger.info("Running REAL model prediction...")
        print("🤖 Running REAL model prediction...")
        
        # Get prediction from the model
        raw_prediction = image_model.predict(processed_image, verbose=0)
        logger.info(f"Raw prediction from REAL model: {raw_prediction}")
        print(f"📊 Raw prediction: {raw_prediction}")
        
        # Handle different output formats
        if len(raw_prediction.shape) > 1 and raw_prediction.shape[1] > 1:
            # Multi-class output
            fake_prob = raw_prediction[0][1] if raw_prediction.shape[1] > 1 else raw_prediction[0][0]
        else:
            # Binary output
            fake_prob = raw_prediction[0][0]
        
        # Determine result
        result = "Fake" if fake_prob > 0.5 else "Real"
        confidence = fake_prob * 100 if result == "Fake" else (1 - fake_prob) * 100
        confidence = max(50.0, min(95.0, confidence))
        
        # Log the result prominently
        logger.info("=" * 50)
        logger.info(f"REAL MODEL PREDICTION RESULT: {result}")
        logger.info(f"CONFIDENCE: {confidence:.1f}%")
        logger.info(f"Fake probability: {fake_prob:.4f}")
        logger.info(f"Real probability: {1-fake_prob:.4f}")
        logger.info("=" * 50)
        
        # Also print to terminal immediately
        print("=" * 50)
        print(f"🎯 REAL MODEL PREDICTION RESULT: {result}")
        print(f"📈 CONFIDENCE: {confidence:.1f}%")
        print(f"🔴 Fake probability: {fake_prob:.4f}")
        print(f"🟢 Real probability: {1-fake_prob:.4f}")
        print("=" * 50)
        
        # Force flush the logging buffer
        import sys
        sys.stdout.flush()
        
        return result, confidence, f"Analysis completed with {confidence:.1f}% confidence"
        
    except Exception as e:
        error_msg = f"Error during prediction: {str(e)}"
        logger.error(error_msg)
        print(f"❌ ERROR: {error_msg}")
        return "Error", 0.0, error_msg

def simulate_prediction(image):
    """Simulate a prediction when no model is available"""
    try:
        # Calculate image characteristics for more realistic simulation
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Calculate various image quality metrics
        blur_variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        brightness = np.mean(gray)
        contrast = gray.std()
        
        # Normalize metrics
        blur_factor = min(blur_variance / 1000, 1.0)
        brightness_factor = abs(brightness - 128) / 128
        contrast_factor = min(contrast / 50, 1.0)
        
        # Calculate a deterministic probability (remove random component)
        # Use a hash of the image characteristics for consistent results
        image_hash = hash((int(blur_variance), int(brightness), int(contrast)))
        
        # Combine factors to determine if image appears fake
        manipulation_score = (
            (1 - blur_factor) * 0.3 +
            (1 - brightness_factor) * 0.3 +
            contrast_factor * 0.2 +
            (image_hash % 100) / 100 * 0.2  # Deterministic instead of random
        )
        
        # Determine result
        if manipulation_score > 0.6:
            result = "Real"
            confidence = 60 + (manipulation_score - 0.6) * 100
        else:
            result = "Fake"
            confidence = 60 + (0.6 - manipulation_score) * 100
        
        confidence = min(confidence, 95)
        
        logger.info(f"Demo mode - Result: {result}, Confidence: {confidence:.1f}%")
        return result, confidence, "Demo mode: analysis based on image characteristics"
    except Exception as e:
        logger.error(f"Error in simulation: {e}")
        return "Real", 75.0, "Demo mode: fallback result"

def frame_capture(video_path):
    """Extract all frames from a video file"""
    frames = []
    frame_paths = []
    # Clear previous frames
    frames_dir = app.config['FRAMES_FOLDER']
    if os.path.exists(frames_dir):
        for f in os.listdir(frames_dir):
            if f.endswith(('.jpg', '.jpeg', '.png')):
                file_path = os.path.join(frames_dir, f)
                try:
                    os.remove(file_path)
                    logger.info(f"Removed old frame: {file_path}")
                except Exception as e:
                    logger.error(f"Error removing old frame {file_path}: {e}")
    try:
        vid_obj = cv2.VideoCapture(video_path)
        if not vid_obj.isOpened():
            logger.error(f"Could not open video file: {video_path}")
            return frames, frame_paths
        fps = vid_obj.get(cv2.CAP_PROP_FPS)
        count = 0
        success = True
        while success:
            success, img = vid_obj.read()
            if not success:
                break
            # Save one frame per second
            if int(count % fps) == 0:
                frame_filename = f"frame_{uuid.uuid4().hex}_{count:06d}.jpg"
                frame_path = os.path.join(frames_dir, frame_filename)
                if cv2.imwrite(frame_path, img):
                    frames.append(img)
                    frame_paths.append(frame_path)
                    logger.info(f"Saved frame {count}: {frame_path}")
                else:
                    logger.error(f"Failed to save frame: {frame_path}")
            count += 1
        vid_obj.release()
        logger.info(f"Extracted {len(frames)} frames from video")
        return frames, frame_paths
    except Exception as e:
        logger.error(f"Error during frame extraction: {e}")
        return [], []

def evaluate_video_frames(frames, frame_paths):
    """Analyze extracted video frames for deepfake detection"""
    global video_model, video_model_loaded
    if not video_model_loaded:
        logger.info("Attempting to reload video model...")
        video_model_loaded = load_video_model()
    results = []
    total_fake_score = 0
    num_frames = len(frames)
    if num_frames == 0:
        return [], "Error", 0
    if not video_model_loaded or video_model is None:
        logger.warning("No video model loaded, using demo mode for video analysis")
        # Simulate results if no model is available
        for i, (frame, path) in enumerate(zip(frames, frame_paths)):
            result, confidence, _ = simulate_prediction(frame)
            # Convert path to web-accessible URL
            web_path = url_for('static', filename=f'frames/{os.path.basename(path)}')
            frame_result = {
                'frame': f"frame{i}",
                'path': web_path,
                'result': result,
                'confidence': confidence
            }
            results.append(frame_result)
            # For simulation, convert percentage to 0-1 scale for averaging
            fake_score = confidence / 100 if result == "Fake" else (100 - confidence) / 100
            total_fake_score += fake_score
    else:
        # Use actual model for prediction
        for i, (frame, path) in enumerate(zip(frames, frame_paths)):
            try:
                # Resize to (224, 224) for video model
                processed_frame = preprocess_image_for_model(frame, target_size=(224, 224))
                if processed_frame is None:
                    logger.error(f"Failed to preprocess frame {i}")
                    continue
                raw_prediction = video_model.predict(processed_frame, verbose=0)
                logger.info(f"Frame {i} raw prediction: {raw_prediction}")
                # Handle different output formats
                if len(raw_prediction.shape) > 1 and raw_prediction.shape[1] > 1:
                    if raw_prediction.shape[1] == 2:
                        fake_prob = float(raw_prediction[0][1])
                    else:
                        fake_prob = float(raw_prediction[0][-1])
                else:
                    fake_prob = float(raw_prediction[0][0])
                result = "Fake" if fake_prob > 0.5 else "Real"
                confidence = fake_prob * 100 if result == "Fake" else (1 - fake_prob) * 100
                confidence = max(50.0, min(95.0, confidence))
                logger.info(f"Frame {i}: {result}, Confidence: {confidence:.1f}%")
                # Convert path to web-accessible URL
                web_path = url_for('static', filename=f'frames/{os.path.basename(path)}')
                frame_result = {
                    'frame': f"frame{i}",
                    'path': web_path,
                    'result': result,
                    'confidence': confidence
                }
                results.append(frame_result)
                # Use fake probability for overall calculation
                total_fake_score += fake_prob
            except Exception as e:
                logger.error(f"Error processing frame {i}: {e}")
                # Add a default result for failed frames
                web_path = url_for('static', filename=f'frames/{os.path.basename(path)}') if path else ''
                frame_result = {
                    'frame': f"frame{i}",
                    'path': web_path,
                    'result': "Error",
                    'confidence': 0.0
                }
                results.append(frame_result)
                total_fake_score += 0.5  # Neutral score for failed frames
    # Calculate average fake score
    avg_fake_score = total_fake_score / num_frames if num_frames > 0 else 0.5
    # Overall result based on average fake score
    if avg_fake_score > 0.5:
        overall_result = "Fake"
        overall_confidence = avg_fake_score * 100
    else:
        overall_result = "Real"
        overall_confidence = (1 - avg_fake_score) * 100
    # Ensure confidence is reasonable
    overall_confidence = max(50.0, min(95.0, overall_confidence))
    logger.info(f"Video analysis complete - Result: {overall_result}, Confidence: {overall_confidence:.1f}%")
    return results, overall_result, overall_confidence

def log_prediction(file_path, result, confidence, file_type="image"):
    """Log prediction to a file for analytics"""
    log_dir = 'logs'
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, 'predictions.json')
    
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'file_path': file_path,
        'file_type': file_type,
        'result': result,
        'confidence': float(confidence)
    }
    
    # Load existing logs
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
        except Exception as e:
            logger.error(f"Error reading log file: {e}")
            logs = []
    
    # Add new log
    logs.append(log_entry)
    
    # Keep only last 1000 entries
    if len(logs) > 1000:
        logs = logs[-1000:]
    
    # Save logs
    try:
        with open(log_file, 'w') as f:
            json.dump(logs, f, indent=2)
        logger.info(f"Logged prediction for {file_path}")
    except Exception as e:
        logger.error(f"Error writing to log file: {e}")

# Grad-CAM utility function

def generate_gradcam_heatmap(model, image_array, last_conv_layer_name=None, pred_index=None):
    """
    Generate a Grad-CAM heatmap for a given image and model.
    Args:
        model: The Keras model.
        image_array: Preprocessed image array (batch, h, w, c).
        last_conv_layer_name: Name of the last conv layer (if None, auto-detects).
        pred_index: Index of the class to visualize (if None, uses model prediction).
    Returns:
        heatmap: 2D numpy array (h, w) normalized to [0, 1].
    """
    import tensorflow as tf
    # Find the last conv layer if not provided
    if last_conv_layer_name is None:
        for layer in reversed(model.layers):
            if 'conv' in layer.name and len(layer.output_shape) == 4:
                last_conv_layer_name = layer.name
                break
        else:
            raise ValueError("No convolutional layer found in model.")
    last_conv_layer = model.get_layer(last_conv_layer_name)
    grad_model = tf.keras.models.Model(
        [model.inputs], [last_conv_layer.output, model.output]
    )
    with tf.GradientTape() as tape:
        conv_outputs, predictions = grad_model(image_array)
        if pred_index is None:
            pred_index = tf.argmax(predictions[0])
        class_channel = predictions[:, pred_index]
    grads = tape.gradient(class_channel, conv_outputs)
    pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2))
    conv_outputs = conv_outputs[0]
    heatmap = conv_outputs @ pooled_grads[..., tf.newaxis]
    heatmap = tf.squeeze(heatmap)
    heatmap = tf.maximum(heatmap, 0) / tf.math.reduce_max(heatmap)
    return heatmap.numpy()

# Overlay heatmap on image

def overlay_heatmap_on_image(original_img, heatmap, alpha=0.4, colormap=cm.jet):
    """
    Overlay a heatmap onto an image.
    Args:
        original_img: Original image (H, W, 3), uint8 or float32.
        heatmap: 2D numpy array (H, W) normalized to [0, 1].
        alpha: Transparency factor.
        colormap: Matplotlib colormap.
    Returns:
        overlayed_img: uint8 image with heatmap overlay.
    """
    import cv2
    heatmap = cv2.resize(heatmap, (original_img.shape[1], original_img.shape[0]))
    heatmap = np.uint8(255 * heatmap)
    heatmap_color = colormap(heatmap)
    heatmap_color = np.uint8(heatmap_color[:, :, :3] * 255)
    overlayed_img = cv2.addWeighted(original_img, 1 - alpha, heatmap_color, alpha, 0)
    return overlayed_img

# Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/image-detection')
def image_detection():
    return render_template('image_detection.html')

@app.route('/video-detection')
def video_detection():
    return render_template('video_detection.html')

@app.route('/upload-image', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if not file or not file.filename:
        return jsonify({'error': 'No selected file'})
    if file and allowed_image_file(file.filename):
        try:
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
            filepath = os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], unique_filename)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            logger.info(f"Saved uploaded image to {filepath}")
            image = cv2.imread(filepath)
            if image is None:
                return jsonify({'error': 'Failed to read image'})
            result, confidence, message = predict_image(image)
            if result == "Error":
                return jsonify({'error': f'Analysis error: {message}'})
            log_prediction(filepath, result, confidence, "image")
            return jsonify({
                'result': result,
                'confidence': f"{confidence:.1f}%",
                'image_url': url_for('static', filename=f'uploads/images/{unique_filename}'),
                'message': message,
                'type': 'image'
            })
        except Exception as e:
            logger.error(f"Error processing image upload: {e}")
            return jsonify({'error': f'Processing error: {str(e)}'})
    return jsonify({'error': 'Invalid file format'})

@app.route('/upload-video', methods=['POST'])
def upload_video():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    file = request.files['file']
    if not file or not file.filename:
        return jsonify({'error': 'No selected file'})
    if file and allowed_video_file(file.filename):
        try:
            # Generate a unique filename
            file_ext = file.filename.rsplit('.', 1)[1].lower()
            unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
            filepath = os.path.join(app.config['VIDEO_UPLOAD_FOLDER'], unique_filename)
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            # Save the file
            file.save(filepath)
            logger.info(f"Saved uploaded video to {filepath}")
            # Extract frames from video
            frames, frame_paths = frame_capture(filepath)
            if not frames:
                return jsonify({'error': 'Failed to extract frames from video'})
            # Analyze frames
            frame_results, overall_result, overall_confidence = evaluate_video_frames(frames, frame_paths)
            # Log the prediction
            log_prediction(filepath, overall_result, overall_confidence, "video")
            return jsonify({
                'result': overall_result,
                'confidence': f"{overall_confidence:.1f}%",
                'video_url': url_for('static', filename=f'uploads/videos/{unique_filename}'),
                'frames': [{'path': res['path'], 'result': res['result'], 'confidence': f"{res['confidence']:.1f}%"} 
                          for res in frame_results],
                'type': 'video'
            })
        except Exception as e:
            logger.error(f"Error processing video upload: {e}")
            return jsonify({'error': f'Processing error: {str(e)}'})
    return jsonify({'error': 'Invalid file format'})

@app.route('/webcam', methods=['POST'])
def webcam_upload():
    try:
        data = request.get_json()
        if not data or 'image' not in data:
            return jsonify({'error': 'No image data'})
        
        # Decode base64 image
        img_data = base64.b64decode(data['image'].split(',')[1])
        nparr = np.frombuffer(img_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return jsonify({'error': 'Failed to decode image'})
        
        # Generate a unique filename
        unique_filename = f"{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(app.config['IMAGE_UPLOAD_FOLDER'], unique_filename)
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Save the image
        cv2.imwrite(filepath, image)
        logger.info(f"Saved webcam image to {filepath}")
        
        # Predict
        result, confidence, message = predict_image(image)
        
        if result == "Error":
            return jsonify({'error': f'Analysis error: {message}'})
        
        # Log the prediction
        log_prediction(filepath, result, confidence, "webcam")
        
        return jsonify({
            'result': result,
            'confidence': f"{confidence:.1f}%",
            'image_url': url_for('static', filename=f'uploads/images/{unique_filename}'),
            'message': message,
            'type': 'image'
        })
    except Exception as e:
        logger.error(f"Error processing webcam image: {e}")
        return jsonify({'error': f'Processing error: {str(e)}'})

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        'status': 'ok',
        'image_model_loaded': image_model_loaded,
        'video_model_loaded': video_model_loaded,
        'image_model_path': IMAGE_MODEL_PATH,
        'video_model_path': VIDEO_MODEL_PATH,
        'image_model_exists': os.path.exists(IMAGE_MODEL_PATH),
        'video_model_exists': os.path.exists(VIDEO_MODEL_PATH),
        'tensorflow_version': tf.__version__,
        'timestamp': datetime.now().isoformat()
    })

# Static file serving routes
@app.route('/static/<path:filename>')
def static_files(filename):
    """Serve static files"""
    return send_from_directory('static', filename)

@app.route('/static/frames/<filename>')
def serve_frame(filename):
    """Serve frame images"""
    return send_from_directory(app.config['FRAMES_FOLDER'], filename)

@app.route('/static/uploads/images/<filename>')
def serve_image(filename):
    """Serve uploaded images"""
    return send_from_directory(app.config['IMAGE_UPLOAD_FOLDER'], filename)

@app.route('/static/uploads/videos/<filename>')
def serve_video(filename):
    """Serve uploaded videos"""
    return send_from_directory(app.config['VIDEO_UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    logger.info("Starting DeepFake Detector application")
    logger.info(f"TensorFlow version: {tf.__version__}")
    logger.info(f"Image model path: {IMAGE_MODEL_PATH}")
    logger.info(f"Video model path: {VIDEO_MODEL_PATH}")
    logger.info(f"Image model exists: {os.path.exists(IMAGE_MODEL_PATH)}")
    logger.info(f"Video model exists: {os.path.exists(VIDEO_MODEL_PATH)}")
    app.run(debug=True, host='0.0.0.0', port=5000)
