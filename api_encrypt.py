from flask import Flask, request, jsonify
import os
import boto3
import hashlib
import cv2
import numpy as np
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from flask_cors import CORS
from botocore.exceptions import ClientError

app = Flask(__name__)
CORS(app)

# S3 Configuration
BUCKET_NAME = "BUCKET NAME"

# AWS S3 Client
s3_client = boto3.client(
    "s3",
    aws_access_key_id= "AWS ACCESS KEY ID",
    aws_secret_access_key="AWS SECRET ACCESS KEY",
    region_name="REGION NAME"
)

# Function to encrypt video frames
def encrypt_data(data, key):
    cipher = AES.new(key, AES.MODE_CBC)
    encrypted_data = cipher.encrypt(pad(data, AES.block_size))
    return encrypted_data, cipher.iv

# Function to compare hashes
def compare_hashes(original_hashes, new_video_path):
    cap = cv2.VideoCapture(new_video_path)
    mismatches = []  # List of tampered frames
    missing_frames = []  # List of missing frames

    with open(original_hashes, 'r') as f:
        original_hash_list = [line.strip().split(": ")[1] for line in f.readlines()]

    frame_count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Check for missing frames beyond the length of the edited video
        if frame_count >= len(original_hash_list):
            missing_frames.extend(range(frame_count, len(original_hash_list)))
            break

        # Recompute the hash for the frame
        frame_bytes = frame.tobytes()
        new_hash = hashlib.sha256(frame_bytes).hexdigest()

        # Compare hash with original
        if new_hash != original_hash_list[frame_count]:
            mismatches.append(frame_count)

        frame_count += 1

    # If the edited video has fewer frames than the original
    if frame_count < len(original_hash_list):
        missing_frames.extend(range(frame_count, len(original_hash_list)))

    cap.release()
    return {
        "tampered_frames": mismatches,
        "missing_frames": missing_frames
    }

# API Endpoint: Upload and Process Video
@app.route('/upload', methods=['POST'])
def upload_video():
    try:
        # Get the uploaded file
        video = request.files.get('video')
        if not video:
            return jsonify({"error": "No video file uploaded"}), 400

        key = os.urandom(16)  # Generate AES Key

        # Create upload directory if it doesn't exist
        os.makedirs("uploads", exist_ok=True)

        # Save the file locally
        video_path = os.path.join("uploads", video.filename)
        video.save(video_path)

        # Check if the file already exists in S3
        hash_file_key = f"hashes/{video.filename}_hashes.txt"
        hash_file_path = os.path.join("uploads", f"{video.filename}_hashes.txt")

        try:
            # Attempt to download the hash file from S3
            s3_client.download_file(BUCKET_NAME, hash_file_key, hash_file_path)

            # If hash file exists, compare hashes
            tampering_info = compare_hashes(hash_file_path, video_path)

            if not tampering_info["tampered_frames"] and not tampering_info["missing_frames"]:
                return jsonify({
                    "message": "File hasn't changed",
                    "status": "unchanged"
                }), 200

            return jsonify({
                "message": "File has been tampered",
                "status": "modified",
                "missing_frames": tampering_info["missing_frames"],
                "tampered_frames": tampering_info["tampered_frames"],
            }), 200
        except ClientError as e:
            if e.response['Error']['Code'] != '404':
                raise e

        # If file doesn't exist, proceed with normal encryption and upload
        encrypted_video_path = os.path.join("uploads", f"encrypted_{video.filename}")
        process_video(video_path, encrypted_video_path, hash_file_path, key)

        # Upload encrypted video and hash file to S3
        upload_to_s3(encrypted_video_path, BUCKET_NAME, os.path.basename(encrypted_video_path), 'videos/')
        upload_to_s3(hash_file_path, BUCKET_NAME, os.path.basename(hash_file_path), 'hashes/')

        return jsonify({
            "message": "Video uploaded and processed successfully",
            "key": key.hex(),
            "status": "uploaded"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/download', methods=['GET'])
def download_video():
    try:
        # Get the filename from the request query parameter
        filename = request.args.get('filename')
        if not filename:
            return jsonify({"error": "Filename parameter is missing"}), 400

        # Generate a presigned URL for the encrypted video
        object_key = f"videos/{filename}"
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': object_key},
            ExpiresIn=3600  # URL expiration time in seconds
        )
        return jsonify({"url": presigned_url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
def process_video(video_path, output_encrypted_video_path, hash_file_path, key):
    cap = cv2.VideoCapture(video_path)
    frame_hashes = []

    # Set up video writer
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter(output_encrypted_video_path, fourcc, fps, (width, height))

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Ensure frame is valid
        if frame is None or frame.size == 0:
            continue

        try:
            # Flatten the frame to bytes
            frame_bytes = frame.tobytes()

            # Encrypt the frame
            encrypted_frame, _ = encrypt_data(frame_bytes, key)

            # Calculate frame hash
            frame_hash = hashlib.sha256(frame_bytes).hexdigest()
            frame_hashes.append(frame_hash)

            # Restore encrypted frame to original shape
            encrypted_frame_array = np.frombuffer(encrypted_frame, dtype=np.uint8)
            if len(encrypted_frame_array) != frame.size:
                # Pad or trim to match frame size
                encrypted_frame_array = np.resize(encrypted_frame_array, frame.size)
            encrypted_frame_reshaped = encrypted_frame_array.reshape(frame.shape)

            # Replace one channel of the frame with encrypted data
            encrypted_frame_visual = frame.copy()
            encrypted_frame_visual[:, :, 0] = encrypted_frame_reshaped[:, :, 0]

            # Write the modified frame
            out.write(encrypted_frame_visual)

        except Exception as e:
            print(f"Error processing frame: {e}")

    cap.release()
    out.release()

    # Write frame hashes to a file
    with open(hash_file_path, 'w') as f:
        for i, h in enumerate(frame_hashes):
            f.write(f"Frame {i}: {h}\n")

def upload_to_s3(file_path, bucket_name, object_name=None, folder_name=''):
    FILE_PATH = folder_name + object_name
    if object_name is None:
        object_name = os.path.basename(file_path)
    try:
        s3_client.upload_file(file_path, bucket_name, FILE_PATH)
        print(f"Uploaded {file_path} to s3://{bucket_name}/{FILE_PATH}")
    except Exception as e:
        print(f"Error uploading to S3: {e}")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
