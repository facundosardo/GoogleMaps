# Google Maps Scraper

This Python script extracts professional data from Google Maps using Selenium.

## 🔍 What it does

It searches for specific professionals in allowed cities in Connecticut and Westchester County, NY, and extracts:

- **Name**
- **Address**
- **City**
- **Phone Number**
- **Website**

It then formats the data (capitalizing name, address, city), removes duplicates, and saves it into:

- `data_general.csv` → Full database with all professionals
- `data_new.csv` → Only new entries found in the current session
- `data_general_backup.csv` → Backup of the general database before the update

## 🚀 How to run

1. Make sure Python 3.11+ and Chrome are installed.
2. Install required packages:

   ```bash
   pip install -r requirements.txt
   ```

3. Run the script:

   ```bash
   python google_maps.py
   ```

> The script uses `webdriver-manager` to auto-download the correct ChromeDriver and handles cookie popups automatically.

## 📁 Files

- `google_maps.py`: Main scraper script
- `data_general.csv`: Full dataset (no duplicates)
- `data_new.csv`: Newly scraped entries from the current run
- `data_general_backup.csv`: Backup copy of the general CSV before the latest update

## ✅ Features

- Google Maps scraper using Selenium
- Handles cookie popups automatically
- Scrolls and loads all results
- Filters only allowed cities
- Removes duplicates across all outputs
- Capitalizes all text fields (Name, Address, City)
- CSV auto-backup before updating

---

Built with ❤️ by [Facundo Sardo](https://github.com/facundosardo)
