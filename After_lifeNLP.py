from flask import Flask, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from google.cloud import storage, speech_v1p1beta1 as speech_v1
from PIL import Image
from io import BytesIO
import face_recognition

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'jpg', 'jpeg', 'png'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def upload_blob(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_name)
    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

def download_blob(bucket_name, source_blob_name, destination_file_name):
    """Downloads a blob from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    blob.download_to_filename(destination_file_name)
    print(f"Blob {source_blob_name} downloaded to {destination_file_name}.")

def recognize_voice(file_path):
    """Transcribes a short audio file using the Google Cloud Speech API"""
    client = speech_v1.SpeechClient()
    with open(file_path, 'rb') as audio_file:
        content = audio_file.read()
    audio = speech_v1.RecognitionAudio(content=content)
    config = speech_v1.RecognitionConfig(
        encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
        sample_rate_hertz=16000,
        language_code='en-US',
        enable_automatic_punctuation=True,
    )
    response = client.recognize(config=config, audio=audio)
    for result in response.results:
        print('Transcript: {}'.format(result.alternatives[0].transcript))
    return response.results[0].alternatives[0].transcript

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files or 'voice_file' not in request.files:
            return redirect(request.url)

        file = request.files['file']
        voice_file = request.files['voice_file']

        if file and allowed_file(file.filename) and voice_file:
            filename = secure_filename(file.filename)
            voice_filename = secure_filename(voice_file.filename)

            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            voice_file_path = os.path.join(app.config['UPLOAD_FOLDER'], voice_filename)

            file.save(file_path)
            voice_file.save(voice_file_path)

            # Upload files to Google Cloud Storage
            upload_blob('your-bucket-name', file_path, filename)
            upload_blob('your-bucket-name', voice_file_path, voice_filename)

            # Transcribe voice file using Google Cloud Speech API
            transcript = recognize_voice(voice_file_path)

            return f"Transcript: {transcript}"

    return '''
    <!doctype html>
    <title>Upload new File</title>
    <h1>Upload new File</h1>
    <form method=post enctype=multipart