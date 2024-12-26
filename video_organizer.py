import os
import shutil
from pathlib import Path
from collections import defaultdict
import concurrent.futures
import zipfile
from tqdm import tqdm
from google_drive_uploader import get_google_drive_service, create_folder, upload_file

# Default folder ID in Google Drive where all uploads will go
DEFAULT_FOLDER_ID = '1FhWY4_mWZcdrmeUbSy2dKDL5cCyMSloj'

def get_size_in_gb(file_path):
    """Get file size in gigabytes"""
    return os.path.getsize(file_path) / (1024 * 1024 * 1024)

def zip_folder(folder_path):
    """Zip a folder and its contents with progress tracking"""
    folder = Path(folder_path)
    zip_path = folder.parent / f"{folder.name}.zip"
    
    # Calculate total size of all files
    total_size = sum(file.stat().st_size for file in folder.rglob('*') if file.is_file())
    processed_size = 0
    
    print(f"\nStarting compression of {folder.name}...")
    print(f"Total size to compress: {total_size / (1024*1024*1024):.2f} GB")
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file in folder.rglob('*'):
            if file.is_file():
                # Calculate relative path for the file inside the zip
                relative_path = file.relative_to(folder)
                zipf.write(file, relative_path)
                
                # Update progress
                processed_size += file.stat().st_size
                progress = (processed_size / total_size) * 100
                print(f"\rCompression progress: {progress:.1f}% - {file.name}     ", end='', flush=True)
                if progress >= 100:
                    print()  # New line after completion
    
    print(f"\nCompleted zip archive: {zip_path.name}")
    return zip_path

def organize_videos(source_dir, upload_to_drive=False):
    """Organize video files into subfolders of max 20GB each"""
    source_path = Path(source_dir)
    source_folder_name = source_path.name
    MAX_SIZE_GB = 20.0  # Strict 20GB limit
    
    # For tracking folder statistics
    folder_stats = defaultdict(list)
    total_files_processed = 0
    created_folders = []
    
    # Validate source directory
    if not source_path.exists() or not source_path.is_dir():
        print(f"Error: '{source_dir}' is not a valid directory")
        return
    
    # Get all MP4 files (case insensitive)
    video_files = []
    for file in source_path.glob('**/*.mp4'):
        if file.is_file():  # Ensure it's a file, not a directory
            video_files.append(file)
    for file in source_path.glob('**/*.MP4'):
        if file.is_file():
            video_files.append(file)
    
    if not video_files:
        print("No MP4 files found in the specified directory")
        return
    
    # Sort files by size (largest first) for better distribution
    video_files.sort(key=lambda x: os.path.getsize(x), reverse=True)
    total_files_processed = len(video_files)
    
    # Create subfolders and distribute files
    current_folder_num = 0
    current_folder_size = 0
    current_folder_files = []
    current_folder = None
    
    for video_file in video_files:
        file_size = get_size_in_gb(video_file)
        
        # Skip files larger than 20GB (should be handled separately)
        if file_size > MAX_SIZE_GB:
            print(f"Warning: {video_file.name} is larger than {MAX_SIZE_GB}GB and will be skipped")
            total_files_processed -= 1
            continue
            
        # If adding this file would exceed or exactly hit 20GB, create new folder
        if current_folder is None or (current_folder_size + file_size) >= MAX_SIZE_GB:
            # If there was a previous folder, rename it with final file count
            if current_folder is not None:
                final_name = f"{source_folder_name}_{current_folder_num}_{len(current_folder_files)}Files"
                final_folder = source_path / final_name
                current_folder.rename(final_folder)
                # Store folder statistics and path
                folder_stats[final_name] = len(current_folder_files)
                created_folders.append(final_folder)
            
            # Create new folder
            current_folder_num += 1
            temp_folder_name = f"temp_{current_folder_num}"  # Temporary name
            current_folder = source_path / temp_folder_name
            current_folder.mkdir(exist_ok=True)
            current_folder_size = 0
            current_folder_files = []
        
        # Move file to current folder
        destination = current_folder / video_file.name
        shutil.move(str(video_file), str(destination))
        current_folder_size += file_size
        current_folder_files.append(video_file.name)
        print(f"Moved {video_file.name} to folder (Current size: {current_folder_size:.2f}GB)")
    
    # Rename the last folder with final file count
    if current_folder is not None and current_folder.exists():
        final_name = f"{source_folder_name}_{current_folder_num}_{len(current_folder_files)}Files"
        final_folder = source_path / final_name
        current_folder.rename(final_folder)
        # Store folder statistics and path
        folder_stats[final_name] = len(current_folder_files)
        created_folders.append(final_folder)
    
    print("\nOrganization Summary:")
    print(f"Total MP4 files processed: {total_files_processed}")
    print("\nFiles per subfolder:")
    for folder_name, file_count in sorted(folder_stats.items()):
        print(f"{folder_name}: {file_count} files")
    
    # Generate detailed report
    generate_report(source_path, folder_stats)
    
    # Sequential zip processing for clearer progress display
    total_folders = len(created_folders)
    print(f"\nStarting compression of {total_folders} folders...")
    
    zip_files = []
    for i, folder in enumerate(created_folders, 1):
        print(f"\nProcessing folder {i}/{total_folders}:")
        try:
            zip_path = zip_folder(folder)
            zip_files.append(zip_path)
            print(f"Successfully compressed: {folder.name}")
        except Exception as e:
            print(f"Error compressing {folder.name}: {str(e)}")
    
    # Upload to Google Drive if requested
    if upload_to_drive and zip_files:
        try:
            print("\nConnecting to Google Drive...")
            service = get_google_drive_service()
            
            # Create a folder with source name in the default folder
            print(f"\nCreating folder '{source_folder_name}' in Google Drive...")
            folder_id = create_folder(service, source_folder_name, DEFAULT_FOLDER_ID)
            
            # Upload each zip file to the created folder
            print("\nUploading zip files to Google Drive...")
            for zip_file in tqdm(zip_files, desc="Uploading", unit="file"):
                upload_file(service, str(zip_file), folder_id)
                print(f"\nUploaded {zip_file.name} to Google Drive")
            
            print("\nAll files uploaded successfully!")
            
        except Exception as e:
            print(f"\nError uploading to Google Drive: {str(e)}")
            print("Files were compressed but not uploaded.")

def generate_report(source_path, folder_stats):
    """Generate a detailed report file in the source folder"""
    report_path = Path(source_path) / "organization_report.txt"
    total_files = sum(folder_stats.values())
    
    with open(report_path, 'w') as f:
        f.write("Video File Organization Report\n")
        f.write("===========================\n\n")
        f.write(f"Source Folder: {Path(source_path).name}\n")
        f.write(f"Total Files Processed: {total_files}\n\n")
        f.write("Files per Subfolder:\n")
        f.write("-----------------\n")
        for folder_name, file_count in sorted(folder_stats.items()):
            f.write(f"{folder_name}: {file_count} files\n")
    
    print(f"\nDetailed report generated: {report_path}")

def main():
    print("Video File Organizer")
    print("===================")
    source_dir = input("Enter the folder path containing video files: ").strip()
    
    # Remove quotes if user copied path with quotes
    source_dir = source_dir.strip('"\'')
    
    # Ask if user wants to upload to Google Drive
    upload_to_drive = input("Upload compressed files to Google Drive? (y/n): ").strip().lower() == 'y'
    
    organize_videos(source_dir, upload_to_drive)
    print("\nOrganization and compression complete!")

if __name__ == "__main__":
    main()
