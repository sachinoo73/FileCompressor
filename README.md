# Video File Organizer

A Python script that organizes large video files into 20GB chunks and optionally uploads them to Google Drive.

## Features

- Organizes video files into folders of maximum 20GB each
- Compresses each folder into a zip file
- Shows real-time compression progress
- Optional Google Drive upload with progress tracking
- Creates a dedicated folder in Google Drive for each batch of uploads

## Setup

1. Install required packages:
```bash
pip3 install google-auth-oauthlib google-auth-httplib2 google-api-python-client tqdm
```

2. Set up Google Drive API:
   1. Go to [Google Cloud Console](https://console.cloud.google.com/)
   2. Create a new project or select an existing one
   3. Enable the Google Drive API for your project
   4. Go to Credentials
   5. Click "Create Credentials" and select "OAuth client ID"
   6. Choose "Desktop app" as the application type
   7. Download the client configuration file
   8. Rename it to `credentials.json` and place it in the same directory as the script

## Usage

1. Run the script:
```bash
python3 video_organizer.py
```

2. Enter the path to the folder containing your video files when prompted

3. Choose whether to upload the compressed files to Google Drive

4. If uploading to Google Drive:
   - On first run, the script will open your browser for Google Drive authorization
   - You'll see a warning that the app isn't verified by Google
   - Click "Advanced" and then "Go to [Project Name] (unsafe)"
   - Click "Continue" to grant the requested permissions
   - The authorization token will be saved for future use

   Note: The "unverified app" warning appears because this is a personal-use application. 
   Since you're using your own Google Cloud project and credentials, it's safe to proceed 
   through this warning. If you plan to distribute this application to other users, you'll 
   need to go through Google's verification process.

## Notes

- Files larger than 20GB will be skipped and reported
- The script creates organized folders with format: `{source_folder}_{number}_{file_count}Files`
- Each folder is compressed into a zip file with the same name
- If Google Drive upload is enabled, all zip files are uploaded to a new folder named after the source folder

## Requirements

- Python 3.6 or higher
- Internet connection (for Google Drive upload)
- Sufficient disk space for temporary files during compression
