# Google Maps Healthcare Scraper

Python script to extract healthcare professional data from **Google Maps** using Selenium.

## 🔍 What it does

Searches for specific healthcare professions in **Connecticut**, **Westchester County (NY)**, **Litchfield County (CT)**, and **Manhattan (NY)**, extracting:

- **Name**
- **Address**
- **City** (filtered by allowed city lists)
- **Phone Number**
- **Website**

The script formats the data (capitalizing Name, Address, City), removes duplicates, and saves it into:

- `data_general.csv` → Full database with all professionals (last 10,000 entries max)
- `data_new.csv` → Only new entries from the current session
- `data_general_backup.csv` → Backup of the general database before update

At the end, it prints:  
`RUN COMPLETE ✅ | <timestamp>`

## 🚀 How to run

1. Make sure Python 3.11+ and Google Chrome are installed.
2. Install required packages:
   pip install -r requirements.txt
3. Run the script:
   python google_maps.py

> Uses `webdriver-manager` to auto-download the correct ChromeDriver and handles cookie popups automatically.

## 📁 Files

- `google_maps.py`: Main scraper script  
- `data_general.csv`: Full deduplicated dataset  
- `data_new.csv`: New entries from this run  
- `data_general_backup.csv`: Auto-backup before update  

## ✅ Features

- Works with multiple regions and allowed city filters  
- Scrolls and loads all Google Maps results  
- Uniform, fast execution speed across all searches  
- Automatic deduplication and CSV backup  
- Capitalizes text fields for consistency  

---

Built with ❤️ by [Facundo Sardo](https://github.com/facundosardo)
