from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import os
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.file']
DEFAULT_FOLDER_ID = '1FhWY4_mWZcdrmeUbSy2dKDL5cCyMSloj'

def get_google_drive_service():
    """Get or create Google Drive API service"""
    creds = None
    
    # The file token.pickle stores the user's access and refresh tokens
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # If there are no (valid) credentials available, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            try:
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError(
                        "\nError: credentials.json not found!\n"
                        "Please follow the setup instructions in README.md to:\n"
                        "1. Create a Google Cloud project\n"
                        "2. Enable the Drive API\n"
                        "3. Create OAuth credentials\n"
                        "4. Download and rename the credentials file to 'credentials.json'\n"
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    'credentials.json', SCOPES)
                print("\nOpening browser for Google Drive authorization...")
                print("Note: You may see an 'unverified app' warning - this is normal for personal-use apps.")
                print("Click 'Advanced' and then 'Go to [Project Name] (unsafe)' to proceed.")
                creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open('token.pickle', 'wb') as token:
                    pickle.dump(creds, token)
                    
            except Exception as e:
                if "Access blocked" in str(e):
                    raise Exception(
                        "\nGoogle Drive access was blocked. This is likely because:\n"
                        "1. You haven't completed the authorization process, or\n"
                        "2. You didn't proceed through the 'unverified app' warning\n\n"
                        "Please try again and follow the browser prompts:\n"
                        "- Click 'Advanced'\n"
                        "- Click 'Go to [Project Name] (unsafe)'\n"
                        "- Click 'Continue' to grant access\n"
                    ) from e
                raise

    # Return Google Drive API service
    return build('drive', 'v3', credentials=creds)

def create_folder(service, folder_name, parent_id=None):
    """Create a folder in Google Drive"""
    file_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder'
    }
    
    if parent_id:
        file_metadata['parents'] = [parent_id]
        
    file = service.files().create(
        body=file_metadata,
        fields='id'
    ).execute()
    
    return file.get('id')

def upload_file(service, filename, folder_id=DEFAULT_FOLDER_ID):
    """Upload a file to Google Drive to the specified folder"""
    file_metadata = {
        'name': os.path.basename(filename),
        'parents': [folder_id]
    }
        
    media = MediaFileUpload(
        filename,
        resumable=True
    )
    
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    return file.get('id')

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python google_drive_uploader.py <file_path>")
        print("Example:")
        print("  python google_drive_uploader.py myfile.zip")
        sys.exit(1)
        
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"Error: File '{file_path}' not found")
        sys.exit(1)
    
    try:
        # Get the Drive service
        service = get_google_drive_service()
        
        # Upload the file
        file_id = upload_file(service, file_path)
        print(f"Successfully uploaded file. File ID: {file_id}")
        print(f"File uploaded to folder with ID: {DEFAULT_FOLDER_ID}")
            
    except Exception as e:
        print(f"Error uploading file: {str(e)}")
        sys.exit(1)
