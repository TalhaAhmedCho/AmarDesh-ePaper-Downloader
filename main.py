import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import urllib.parse
import re
from PIL import Image, UnidentifiedImageError
import shutil
import time
import json
from telethon import TelegramClient, events

# Base URL of the website
base_url = "https://eamardesh.com/"

# Get today's date in the format "dd-Mmm-yyyy"
today_date = datetime.now().strftime("%d-%b-%Y")

# Replace these with your details
api_id = ''
api_hash = ''
phone_number = ''
channel_id =   # Use integer ID


# Function to clean and modify the URL
def clean_url(url):
    if url.startswith("https://eamardesh.com/_next/image?url="):
        url = url[len("https://eamardesh.com/_next/image?url="):]
    url = url.replace("%3A%2F%2F", "://").replace("%2F", "/").replace("compressedepaper", "epaper")
    url = re.sub(r'_compressed_[a-f0-9\-]+', '', url)
    url = re.sub(r'\.jpg.*$', '.jpg', url)
    return url

# Function to scrape image URLs from the page
def scrape_image_links(url):
    try:
        print(f"\033[1;32mScraping image links from {url}...\033[0m")
        response = requests.get(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            img_tags = soup.find_all("img")
            img_urls = []
            page_urls = {}
            for img in img_tags:
                img_src = img.get("src")
                if img_src and 'compressedepaper' in img_src:
                    if not img_src.startswith("http"):
                        img_src = base_url + img_src.lstrip("/")
                    clean_img_url = clean_url(img_src)
                    match = re.search(r'_page_(\d+)_', clean_img_url, re.IGNORECASE)
                    if match:
                        page_number = match.group(1)
                        if page_number not in page_urls:
                            page_urls[page_number] = clean_img_url
            img_urls = list(page_urls.values())
            print(f"\033[1;32mFound {len(img_urls)} unique image URLs containing 'compressedepaper'.\033[0m")
            for img_url in img_urls:
                print(f"Found image URL: {img_url}")
                time.sleep(0.2)
            return img_urls
        else:
            print(f"Failed to access {url}: Status {response.status_code}")
            return []
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

# Function to download images from the URLs with increased timeout and display download speed
def download_images(url_list, download_folder):
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    print(f"\033[1;34m{len(url_list)} unique images download started.\033[0m")
    for i, url in enumerate(url_list):
        try:
            start_time = time.time()
            response = requests.get(url, timeout=120, stream=True)
            if response.status_code == 200:
                img_name = os.path.basename(urllib.parse.urlparse(url).path)
                img_path = os.path.join(download_folder, img_name)
                total_length = int(response.headers.get('content-length', 0))
                downloaded = 0
                with open(img_path, "wb") as img_file:
                    for data in response.iter_content(chunk_size=4096):
                        img_file.write(data)
                        downloaded += len(data)
                        elapsed_time = time.time() - start_time
                        speed = downloaded / elapsed_time
                        print(f"\rDownloading {img_name}: {downloaded / (1024 * 1024):.2f}MB/{total_length / (1024 * 1024):.2f}MB [{downloaded / total_length:.2%}] at {speed / (1024 * 1024):.2f}MB/s", end='')
                print()
                color = "\033[1;32m" if i % 2 == 0 else "\033[1;31m"
                print(f"{color}Downloaded {img_name}\033[0m")
            else:
                print(f"Failed to download {url}: Status {response.status_code}")
        except Exception as e:
            print(f"Error downloading {url}: {e}")

# Function to extract page number from the image file name
def extract_page_number(file_name):
    match = re.search(r'page_(\d+)_', file_name, re.IGNORECASE)
    return int(match.group(1)) if match else float('inf')

# Function to convert images to a PDF
def convert_images_to_pdf(image_folder, output_pdf):
    try:
        image_files = [os.path.join(image_folder, f) for f in os.listdir(image_folder) if f.endswith(".jpg")]
        image_files.sort(key=lambda x: extract_page_number(os.path.basename(x)))
        images = []
        for img_file in image_files:
            try:
                if os.path.getsize(img_file) > 0:
                    img = Image.open(img_file).convert("RGB")
                    images.append(img)
                    print(f"Merging {os.path.basename(img_file)}")
                    time.sleep(0.2)
                else:
                    raise UnidentifiedImageError
            except UnidentifiedImageError:
                print(f"Error: Cannot identify image file {img_file}. Re-downloading...")
                url = f"https://eamardesh.com/{img_file}"
                download_images([url], image_folder)
                if os.path.getsize(img_file) > 0:
                    img = Image.open(img_file).convert("RGB")
                    images.append(img)
        if images:
            print("Merging images into PDF...")
            images[0].save(output_pdf, save_all=True, append_images=images[1:])
            print(f"\033[1;32mConverted {len(images)} images to {output_pdf}\033[0m")
        else:
            print("No images found to convert to PDF.")
    except Exception as e:
        print(f"Error converting images to PDF: {e}")
        print("Deleting all files in the download folder and re-downloading images...")
        clear_folder(image_folder)
        download_images(scrape_image_links(base_url + today_date), image_folder)
        convert_images_to_pdf(image_folder, output_pdf)

# Function to check if images already exist in the folder
def images_exist(image_urls, download_folder):
    existing_files = set(os.listdir(download_folder))
    for url in image_urls:
        img_name = os.path.basename(urllib.parse.urlparse(url).path)
        if img_name not in existing_files:
            return False
    return True

# Function to clear the download folder
def clear_folder(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f"Failed to delete {file_path}. Reason: {e}")

# Function to save URLs of page 1 and page 16 images to a text file
def save_page_urls(image_urls, file_path):
    page_urls = {}
    for url in image_urls:
        match = re.search(r'_page_(\d+)_', url, re.IGNORECASE)
        if match:
            page_number = match.group(1)
            if page_number in ["1", "16"]:
                page_urls[page_number] = url
    with open(file_path, "w") as file:
        for page_number, url in page_urls.items():
            file.write(f"{url}\n")

# Function to resize image to meet Telegram's requirements while maintaining quality
def resize_image(image_path):
    with Image.open(image_path) as img:
        max_size = (2560, 2560)
        img.thumbnail(max_size, Image.LANCZOS)
        img.save(image_path, quality=100)

# Function to upload images to Telegram
def upload_images_to_telegram(urls_file):
    base_url = "https://api.telegram.org/bot{token}/sendMediaGroup"
    media = []
    files = {}

    # Read URLs from the text file
    with open(urls_file, "r") as file:
        urls = [line.strip() for line in file.readlines()]

    # Download images and prepare media group
    for i, url in enumerate(urls):
        response = requests.get(url)
        if response.status_code == 200:
            file_name = f"image_{i}.jpg"
            with open(file_name, "wb") as file:
                file.write(response.content)
            
            # Resize the image to meet Telegram's requirements
            resize_image(file_name)
            
            # Ensure the image has valid dimensions
            with Image.open(file_name) as img:
                if img.width > 0 and img.height > 0:
                    media.append({
                        "type": "photo",
                        "media": f"attach://{file_name}"
                    })
                    files[file_name] = open(file_name, "rb")

    if media:
        parameters = {
            "chat_id": "",
            "media": json.dumps(media)
        }

        response = requests.post(base_url, data=parameters, files=files)
        if response.status_code == 200:
            print("Upload complete.")
        else:
            print(f"Upload failed. Status code: {response.status_code}, Response: {response.text}")

        # Clean up downloaded files
        for file_name, file in files.items():
            file.close()
            os.remove(file_name)
    else:
        print("No media to send.")

def handle_remove_error(func, path, exc_info):
    print(f"Error removing {path}. Retrying...")
    time.sleep(1)  # Wait briefly
    try:
        func(path)
    except Exception as e:
        print(f"Failed to remove {path}: {e}")

# Function to upload PDF to Telegram using Telethon with progress display
async def upload_pdf_to_telegram(client, channel_id, pdf_path):
    try:
        print(f"Uploading {pdf_path} to Telegram channel {channel_id}...")

        async def progress_callback(current, total):
            elapsed_time = time.time() - start_time
            speed = current / elapsed_time
            print(f"\rUploading {os.path.basename(pdf_path)}: {current / (1024 * 1024):.2f}MB/{total / (1024 * 1024):.2f}MB [{current / total:.2%}] at {speed / (1024 * 1024):.2f}MB/s", end='')

        start_time = time.time()
        await client.send_file(channel_id, pdf_path, progress_callback=progress_callback)
        print("\nPDF uploaded successfully.")
    except Exception as e:
        print(f"Error uploading PDF: {e}")

    # Create a folder with today's date
    date_folder = today_date
    if os.path.exists(date_folder):
        shutil.rmtree(date_folder, onerror=handle_remove_error)
    os.makedirs(date_folder)
    print(f"Created folder: {date_folder}")

    # Copy the Images folder to the new date folder
    shutil.copytree(download_folder, os.path.join(date_folder, "Images"))
    print(f"Copied Images folder to: {date_folder}")

    # Move the PDF to the new date folder
    shutil.move(pdf_path, os.path.join(date_folder, os.path.basename(pdf_path)))
    print(f"Moved PDF to: {date_folder}")

    # Move the date folder to the specified directory
    destination_path = r"C:\Users\tahch\Amar Desh\OneDrive - MSFT\ePaper"
    if os.path.exists(os.path.join(destination_path, date_folder)):
        shutil.rmtree(os.path.join(destination_path, date_folder), onerror=handle_remove_error)
    shutil.move(date_folder, destination_path)
    print(f"Moved folder {date_folder} to: {destination_path}")

# Function to check if 16 images are present in the folder
def check_images_count(download_folder):
    image_files = [f for f in os.listdir(download_folder) if f.endswith(".jpg")]
    return len(image_files) == 16

# Function to save unique page URLs to a text file
def save_unique_page_urls(image_urls, file_path):
    page_urls = {}
    for url in image_urls:
        match = re.search(r'_page_(\d+)_', url, re.IGNORECASE)
        if match:
            page_number = match.group(1)
            if page_number not in page_urls:
                page_urls[page_number] = url
    with open(file_path, "w") as file:
        for page_number, url in page_urls.items():
            file.write(f"{url}\n")

# Function to download unique images from the URLs
def download_unique_images(url_list, download_folder):
    if not os.path.exists(download_folder):
        os.makedirs(download_folder)
    print(f"\033[1;34m{len(url_list)} unique images download started.\033[0m")
    for i, url in enumerate(url_list):
        try:
            start_time = time.time()
            response = requests.get(url, timeout=120, stream=True)
            if response.status_code == 200:
                img_name = os.path.basename(urllib.parse.urlparse(url).path)
                img_path = os.path.join(download_folder, img_name)
                total_length = int(response.headers.get('content-length', 0))
                downloaded = 0
                with open(img_path, "wb") as img_file:
                    for data in response.iter_content(chunk_size=4096):
                        img_file.write(data)
                        downloaded += len(data)
                        elapsed_time = time.time() - start_time
                        speed = downloaded / elapsed_time
                        print(f"\rDownloading {img_name}: {downloaded / (1024 * 1024):.2f}MB/{total_length / (1024 * 1024):.2f}MB [{downloaded / total_length:.2%}] at {speed / (1024 * 1024):.2f}MB/s", end='')
                print()
                color = "\033[1;32m" if i % 2 == 0 else "\033[1;31m"
                print(f"{color}Downloaded {img_name}\033[0m")
            else:
                print(f"Failed to download {url}: Status {response.status_code}")
        except Exception as e:
            print(f"Error downloading {url}: {e}")

# Main execution
if __name__ == "__main__":
    url = base_url + today_date
    image_urls = scrape_image_links(url)
    download_folder = "Images"
    if image_urls:
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        
        if images_exist(image_urls, download_folder):
            print(f"\033[1;32mImages already exist in the folder. Skipping download.\033[0m")
        else:
            clear_folder(download_folder)
            download_unique_images(image_urls, download_folder)
        
        # Check if 16 images are present in the folder
        while not check_images_count(download_folder):
            print(f"\033[1;31m\033[1mNot all images downloaded. Retrying...\033[0m")
            image_urls = scrape_image_links(url)
            clear_folder(download_folder)
            download_unique_images(image_urls, download_folder)
        
        output_pdf = f"{today_date}.pdf"
        convert_images_to_pdf(download_folder, output_pdf)
        
        # Save all unique URLs to a text file
        save_unique_page_urls(image_urls, "urls.txt")
        
        # Save URLs of page 1 and page 16 images to a text file
        save_page_urls(image_urls, "page_urls.txt")
        
        # Upload images to Telegram
        upload_images_to_telegram("page_urls.txt")
        
        # Upload PDF to Telegram using Telethon
        client = TelegramClient('session_name', api_id, api_hash)

        async def main():
            if not await client.is_user_authorized():
                await client.start(phone_number)
            else:
                await client.connect()
            await upload_pdf_to_telegram(client, channel_id, output_pdf)

        with client:
            client.loop.run_until_complete(main())
    else:
        print("No images found containing 'compressedepaper' on the page.")
