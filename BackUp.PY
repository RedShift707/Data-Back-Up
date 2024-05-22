import os
import shutil
import argparse
import logging
from datetime import datetime
import zipfile
import tempfile
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def parse_arguments():
    parser = argparse.ArgumentParser(description="Data Backup Tool for Windows 10 and 11")
    parser.add_argument('source', nargs='?', help="Source directory to back up")
    parser.add_argument('destination', help="Destination directory for the backup or restore")
    parser.add_argument('--restore', help="Zip file to restore from", default=None)
    parser.add_argument('--email', help="Email address to send notifications")
    return parser.parse_args()

def verify_paths(source, destination, restore):
    if restore:
        if not os.path.exists(restore):
            raise FileNotFoundError(f"Zip file '{restore}' does not exist.")
    else:
        if not os.path.exists(source):
            raise FileNotFoundError(f"Source path '{source}' does not exist.")
    if not os.path.exists(destination):
        os.makedirs(destination)

def backup_files(source, temp_backup_dir):
    for root, dirs, files in os.walk(source):
        for dir_name in dirs:
            source_dir = os.path.join(root, dir_name)
            relative_path = os.path.relpath(source_dir, source)
            temp_dir = os.path.join(temp_backup_dir, relative_path)
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
                logging.info(f"Created directory: {temp_dir}")

        for file_name in files:
            source_file = os.path.join(root, file_name)
            relative_path = os.path.relpath(source_file, source)
            temp_file = os.path.join(temp_backup_dir, relative_path)
            shutil.copy2(source_file, temp_file)
            logging.info(f"Copied file: {source_file} to {temp_file}")

def compress_backup(temp_backup_dir, destination):
    zip_filename = os.path.join(destination, f"backup_{datetime.now().strftime('%Y%m%d%H%M%S')}.zip")
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(temp_backup_dir):
            for file in files:
                file_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_path, temp_backup_dir)
                zipf.write(file_path, relative_path)
                logging.info(f"Compressed file: {file_path} as {relative_path}")
    logging.info(f"Backup compressed to: {zip_filename}")
    return zip_filename

def restore_backup(zip_filename, destination):
    with zipfile.ZipFile(zip_filename, 'r') as zipf:
        zipf.extractall(destination)
        for file in zipf.namelist():
            logging.info(f"Extracted file: {file} to {destination}")
    logging.info(f"Backup restored from: {zip_filename}")

def send_email(subject, body, to_email):
    from_email = "your-email@example.com"
    smtp_server = "smtp.example.com"
    smtp_port = 587
    smtp_user = "your-email@example.com"
    smtp_password = "your-email-password"

    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, to_email, msg.as_string())
        server.quit()
        logging.info(f"Email sent to {to_email}")
    except Exception as e:
        logging.error(f"Failed to send email: {e}")

def main():
    args = parse_arguments()
    source = args.source
    destination = args.destination
    restore = args.restore
    email = args.email

    # Configure logging
    log_file = os.path.join(destination, f"log_{datetime.now().strftime('%Y%m%d%H%M%S')}.log")
    logging.basicConfig(filename=log_file, level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    try:
        verify_paths(source, destination, restore)
        if restore:
            restore_backup(restore, destination)
            logging.info("Restore completed successfully.")
            message = f"Restore completed successfully from {restore} to {destination}."
            print(message)
        else:
            with tempfile.TemporaryDirectory() as temp_backup_dir:
                backup_files(source, temp_backup_dir)
                zip_filename = compress_backup(temp_backup_dir, destination)
            logging.info("Backup completed successfully.")
            message = f"Backup completed successfully. Compressed file: {zip_filename}"
            print(message)
        if email:
            send_email("Backup Notification", message, email)
    except Exception as e:
        logging.error(f"Error during operation: {e}")
        error_message = f"Error during operation: {e}"
        print(error_message)
        if email:
            send_email("Backup Error Notification", error_message, email)

if __name__ == "__main__":
    main()
