# Encrypted Video Tampering Detection and Localization Through Cloud

## Overview
This project tackles the challenges of video security and integrity in cloud environments by developing a robust framework that combines **cryptographic algorithms** and **cloud storage technologies**. The system ensures the confidentiality of video data through encryption while enabling tampering detection and localization without compromising privacy.

## Key Features
- **Advanced Encryption**: Implements AES encryption to secure video content at a frame-by-frame level.
- **Tampering Detection**: Utilizes SHA-256 hashing to verify the integrity of each video frame.
- **Localization**: Identifies tampered or missing frames and pinpoints affected regions within the video.
- **Cloud Integration**: Stores encrypted videos and hash files on AWS S3, leveraging scalable and secure cloud storage.
- **Notifications**: Provides real-time feedback to users on tampering or successful uploads.

## System Workflow
1. **Upload**: Users upload video files via the interface.
2. **Encryption**: Each video frame is encrypted using AES.
3. **Hashing**: SHA-256 hashes are generated for each frame and stored alongside the video.
4. **Tampering Check**:
   - If the video exists in AWS S3, the system verifies its integrity by comparing stored hashes with recalculated ones.
   - If no hash file is found, the video is processed as a new upload.
5. **Results**: The system alerts users about tampering or confirms successful storage.

## Technology Stack
- **Programming Languages**: Python
- **Frameworks**: Flask
- **Cloud Platform**: AWS S3
- **Cryptography**: AES (Advanced Encryption Standard), SHA-256
- **Video Processing**: OpenCV
- **Development Tools**: Docker (optional), Postman (for API testing)

## Installation and Usage
### Prerequisites
- Python 3.x installed
- AWS account with S3 configured
- Required Python libraries: `boto3`, `flask`, `pycryptodome`, `opencv-python`

### Steps to Run the Project
1. Clone the repository:
   ```bash
   git clone https://github.com/SG2104/cryptoProj.git
   cd cryptoProj
2. Run the development server:
   ```bash
   npm -i
   npm run dev
   ```
3. Run a python File:
   ```bash
   python3 api_encrypt.py
   ```
4. Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

