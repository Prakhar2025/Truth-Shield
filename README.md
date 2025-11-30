# Truth Shield - Deepfake Detection System

A comprehensive deep learning-based application for detecting deepfakes in both images and videos using state-of-the-art neural networks.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Flask](https://img.shields.io/badge/Flask-2.0+-green.svg)
![TensorFlow](https://img.shields.io/badge/TensorFlow-2.0+-orange.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎯 Overview

Truth Shield is an intelligent deepfake detection system that leverages advanced deep learning models to identify manipulated media content. It supports both **image** and **video** deepfake detection with a user-friendly web interface.

### Key Features
- ✅ **Image Deepfake Detection** - Detect manipulated images using XceptionNet
- ✅ **Video Deepfake Detection** - Analyze video frames using CNN-LSTM architecture
- ✅ **Real-time Processing** - Process media files with instant results
- ✅ **Confidence Scoring** - Get detailed confidence levels for predictions
- ✅ **User-friendly Web Interface** - Intuitive UI for easy interaction
- ✅ **Frame-by-Frame Analysis** - Detailed analysis for video content
- ✅ **Prediction Logs** - Track and review all predictions

## 📋 Table of Contents

- [Installation](#installation)
- [Project Structure](#project-structure)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Models](#models)
- [Technologies](#technologies)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- 4GB RAM (minimum)
- 5GB free disk space

### Step 1: Clone the Repository

```bash
git clone https://github.com/Prakhar2025/Truth-Shield.git
cd Truth-Shield
```

### Step 2: Create Virtual Environment

```bash
# On Windows
python -m venv venv
venv\Scripts\activate

# On macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Download Pre-trained Models

The models are pre-trained and should be placed in the `model/` directory:
- `new_xception.h5` - For image deepfake detection
- `deepfake_detection_model.h5` - For video deepfake detection

**Note:** Due to size limitations, models are not included in the repository. Download them from [Google Drive Link] or train your own using the notebooks in `colab files/`

### Step 5: Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

## 📁 Project Structure

```
Truth-Shield/
├── app.py                          # Main Flask application
├── requirements.txt                # Python dependencies
├── .gitignore                      # Git ignore file
├── README.md                       # Project documentation
├── LICENSE                         # License file
│
├── model/                          # Pre-trained models directory
│   ├── new_xception.h5            # Image detection model
│   └── deepfake_detection_model.h5 # Video detection model
│
├── static/                         # Static files
│   ├── css/                        # Stylesheets
│   │   ├── index.css               # Home page styles
│   │   ├── image_detection.css     # Image detection styles
│   │   ├── video_styles.css        # Video detection styles
│   │   └── styles.css              # Global styles
│   │
│   ├── js/                         # JavaScript files
│   │   ├── script.js               # Main script
│   │   ├── home.js                 # Home page logic
│   │   ├── image_detection.js      # Image detection logic
│   │   └── video_detection.js      # Video detection logic
│   │
│   ├── uploads/                    # Upload directory (git ignored)
│   │   ├── images/                 # Uploaded images
│   │   └── videos/                 # Uploaded videos
│   │
│   └── frames/                     # Extracted video frames
│
├── templates/                      # HTML templates
│   ├── index.html                  # Home page
│   ├── image_detection.html        # Image detection page
│   └── video_detection.html        # Video detection page
│
├── logs/                           # Application logs
│   └── predictions.json            # Prediction history
│
└── colab files/                    # Training notebooks
    ├── image notebook/
    │   └── new_xception (1).ipynb
    └── video notebook/
        ├── final.ipynb
        └── usinglstmcnn.ipynb
```

## 💻 Usage

### Image Deepfake Detection

1. Navigate to the home page
2. Click on "Detect Image Deepfakes"
3. Upload an image (PNG, JPG, JPEG, WEBP, BMP, TIFF)
4. View the prediction results with confidence score

**Supported Formats:** PNG, JPG, JPEG, WEBP, BMP, TIFF

### Video Deepfake Detection

1. Navigate to the home page
2. Click on "Detect Video Deepfakes"
3. Upload a video (MP4, AVI, MOV, MKV, WMV)
4. Wait for frame extraction and analysis
5. View frame-by-frame results with confidence scores

**Supported Formats:** MP4, AVI, MOV, MKV, WMV

## 🔌 API Endpoints

### Image Detection

**POST** `/api/detect-image`

Request:
```json
{
  "file": "<image-file>"
}
```

Response:
```json
{
  "success": true,
  "prediction": "REAL/FAKE",
  "confidence": 0.95,
  "timestamp": "2024-01-01T12:00:00"
}
```

### Video Detection

**POST** `/api/detect-video`

Request:
```json
{
  "file": "<video-file>"
}
```

Response:
```json
{
  "success": true,
  "frames_analyzed": 30,
  "overall_prediction": "REAL/FAKE",
  "average_confidence": 0.92,
  "frame_results": [...]
}
```

## 🧠 Models

### Image Detection Model (XceptionNet)
- **Architecture:** Xception (Transfer Learning)
- **Input Shape:** (299, 299, 3)
- **Output:** Binary classification (Real/Fake)
- **Training Dataset:** Combined face manipulation datasets
- **Accuracy:** ~95%

### Video Detection Model (CNN-LSTM)
- **Architecture:** CNN (ResNet50) + LSTM
- **Frame Extraction:** Every 2nd frame
- **Temporal Analysis:** LSTM for sequence learning
- **Output:** Binary classification with confidence scores
- **Accuracy:** ~92%

## 🛠 Technologies Used

- **Backend:** Flask (Python web framework)
- **Deep Learning:** TensorFlow, Keras
- **Computer Vision:** OpenCV
- **Frontend:** HTML5, CSS3, JavaScript
- **Data Processing:** NumPy, Matplotlib
- **Logging:** Python logging module

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
FLASK_ENV=development
FLASK_DEBUG=False
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=500000000  # 500MB max file size
```

### Model Configuration

Edit `app.py` to modify:
- Upload limits
- Allowed file extensions
- Model paths
- Logging settings

```python
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'bmp', 'tiff'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv'}
```

## 🐛 Troubleshooting

### Models Not Loading
```
Error: Image model file not found at model/new_xception.h5
```
**Solution:** Ensure model files are downloaded and placed in the `model/` directory.

### Out of Memory Error
```
Error: Resource exhausted while executing GPU operations
```
**Solution:** 
- Reduce batch size in configuration
- Use CPU instead: Set `CUDA_VISIBLE_DEVICES=''`

### Video Processing Issues
```
Error: Failed to extract frames from video
```
**Solution:**
- Ensure video format is supported
- Check video file integrity
- Reduce video resolution/length

### Port Already in Use
```
Error: Address already in use
```
**Solution:**
```bash
# Change port in app.py or use:
python app.py --port 5001
```

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/Truth-Shield.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dev dependencies
pip install -r requirements.txt

# Make your changes and test
python app.py
```

## 📊 Performance Metrics

| Metric | Image Detection | Video Detection |
|--------|-----------------|-----------------|
| Accuracy | ~95% | ~92% |
| Processing Time (avg) | 2-3 seconds | 10-30 seconds |
| Input Size | Up to 500MB | Up to 500MB |
| Supported Formats | 6 formats | 5 formats |

## 🔐 Security Considerations

- Uploaded files are temporarily stored and deleted after processing
- Models run locally - no data sent to external servers
- Input validation for all file uploads
- Secure filename handling

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Prakhar Sharma**
- GitHub: [@Prakhar2025](https://github.com/Prakhar2025)
- Repository: [Truth-Shield](https://github.com/Prakhar2025/Truth-Shield)

## 🙏 Acknowledgments

- Dataset creators and researchers in deepfake detection
- TensorFlow and OpenCV communities
- Contributors and testers

## 📞 Support

For issues, questions, or suggestions:
- Open an issue on [GitHub Issues](https://github.com/Prakhar2025/Truth-Shield/issues)
- Contact: [your-email@example.com]

## 🚀 Future Enhancements

- [ ] Deploy on cloud (AWS/Google Cloud/Azure)
- [ ] Add real-time webcam detection
- [ ] Improve model accuracy with ensemble methods
- [ ] Add audio deepfake detection
- [ ] Mobile app integration
- [ ] Batch processing support
- [ ] API authentication and rate limiting

---

**Made with ❤️ for safer digital media**
