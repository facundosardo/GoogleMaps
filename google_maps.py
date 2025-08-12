import time
import random
import pandas as pd
import re
import shutil
import os
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---------- Utilities ----------

def pause(minimum=0.2, maximum=0.6):
    time.sleep(random.uniform(minimum, maximum))

def log(msg):
    print(f"[INFO] {msg}")

def warn(msg):
    print(f"[WARN] {msg}")

def err(msg):
    print(f"[ERROR] {msg}")

def clean_text(text):
    if isinstance(text, str):
        return text.strip()
    return ""

def format_title(text):
    if isinstance(text, str):
        return ' '.join([word.capitalize() for word in text.strip().split()])
    return ""

def format_city(text):
    if isinstance(text, str):
        return ' '.join([p.capitalize() for p in text.strip().split()])
    return ""

def extract_city(address, allowed_cities):
    if not isinstance(address, str):
        return ""
    parts = address.lower().split(",")
    parts = [re.sub(r'[^a-z\s-]', '', p).strip() for p in parts]
    for part in parts:
        if part in allowed_cities:
            return part
    return ""

# ---------- Allowed cities ----------

allowed_cities_ct = {
    'stamford', 'norwalk', 'danbury', 'greenwich', 'new haven', 'hartford',
    'waterbury', 'bridgeport', 'meriden', 'milford', 'hamden', 'west haven',
    'wallingford', 'middletown', 'new britain', 'newington', 'bristol',
    'cheshire', 'shelton', 'stratford', 'southbury', 'derby', 'fairfield',
    'monroe', 'newtown', 'oxford', 'woodbridge'
}

allowed_cities_westchester = {
    'white plains', 'yonkers', 'new rochelle', 'mount vernon', 'peekskill',
    'rye', 'harrison', 'ossining', 'port chester', 'tarrytown', 'dobbs ferry',
    'hastings-on-hudson', 'bronxville', 'pelham', 'mamaroneck', 'scarsdale',
    'armonk', 'elmsford', 'chappaqua', 'larchmont', 'pound ridge', 'bedford',
    'eastchester', 'mount kisco'
}

allowed_cities_litchfield = {
    'bantam', 'barkhamsted', 'bethlehem', 'bridgewater', 'canaan', 'colebrook',
    'cornwall', 'goshen', 'harwinton', 'kent', 'litchfield', 'morris',
    'new hartford', 'new milford', 'norfolk', 'north canaan', 'plymouth',
    'roxbury', 'salisbury', 'sharon', 'thomaston', 'torrington', 'warren',
    'washington', 'watertown', 'winchester', 'woodbury'
}

# Manhattan acepta todo, así que no filtramos ciudad.

# ---------- Driver Initialization ----------

def start_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    driver.get('https://www.google.com/maps')
    log("Page loaded")
    pause(0.5, 1.5)

    try:
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for btn in buttons:
            text = btn.text.lower()
            if "accept" in text or "agree" in text:
                btn.click()
                log("Cookies button clicked")
                pause(0.3, 1.0)
                break
    except Exception:
        warn("Cookies button not found or not clickable")

    return driver

# ---------- Search and Extract ----------

def search_and_extract(driver, query, allowed_cities=None):
    log(f"Searching: {query}")

    try:
        search_box = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, "searchboxinput"))
        )
    except:
        err("Search box did not appear")
        return []

    search_box.clear()
    pause(0.2, 0.4)
    search_box.send_keys(query)
    search_box.send_keys(Keys.ENTER)

    try:
        panel = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]'))
        )
    except:
        err("No result panel found")
        return []

    # Scroll
    prev_count = 0
    same_count_retries = 0
    max_retries = 15
    while True:
        driver.execute_script('arguments[0].scrollBy(0, 1000);', panel)
        pause(0.25, 0.4)
        results = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK.tH5CWc.THOPZb')
        current_count = len(results)
        if current_count == prev_count:
            same_count_retries += 1
        else:
            same_count_retries = 0
        if same_count_retries >= max_retries:
            break
        prev_count = current_count

    log(f"Total found: {len(results)}")
    new_data = []

    for i in range(len(results)):
        try:
            # Re-localizar para evitar stale element
            results = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK.tH5CWc.THOPZb')
            if i >= len(results):
                break
            res = results[i]

            driver.execute_script("arguments[0].scrollIntoView(true);", res)
            pause(0.25, 0.45)

            try:
                res.click()
            except:
                # Retry una vez si falla el click
                pause(0.3, 0.5)
                res.click()

            pause(0.6, 1.0)

            name = address = web = phone = ""

            try:
                name = WebDriverWait(driver, 3).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.DUwDvf.lfPIob'))
                ).text
            except:
                pass

            try:
                address = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id="address"]').text
                address = re.sub(r'^\W+', '', address).strip()
            except:
                pass

            try:
                web = driver.find_element(By.CSS_SELECTOR, 'a[data-item-id="authority"]').get_attribute('href')
            except:
                pass

            try:
                phone_element = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id^="phone"] div.Io6YTe')
                phone = phone_element.text.strip()
            except:
                phone = ""

            # Filtrado
            if allowed_cities:
                city = extract_city(address, allowed_cities)
                if city not in allowed_cities:
                    warn(f"City not allowed '{city}', skipping result {i+1}")
                    continue
            else:
                city = ""  # Para Manhattan no filtramos

            new_data.append({
                "Name": format_title(name),
                "Address": format_title(address),
                "City": format_city(city),
                "Phone Number": phone,
                "Web": web
            })

        except Exception as e:
            err(f"Error on result {i+1}: {e}")

    return new_data

# ---------- Save CSV ----------

def save_data(data):
    general_file = "data_general.csv"
    new_file = "data_new.csv"

    if os.path.exists(general_file):
        shutil.copy(general_file, general_file.replace(".csv", "_backup.csv"))
        df_general = pd.read_csv(general_file, encoding='utf-8-sig')
    else:
        df_general = pd.DataFrame(columns=["Name", "Address", "City", "Phone Number", "Web"])

    df_new = pd.DataFrame(data)
    for col in ["Name", "Address"]:
        df_new[col] = df_new[col].apply(format_title)
    df_new["City"] = df_new["City"].apply(format_city)

    df_general.drop_duplicates(inplace=True)
    df_new.drop_duplicates(inplace=True)
    df_new_unique = df_new[~df_new.apply(tuple, axis=1).isin(df_general.apply(tuple, axis=1))]

    df_general_updated = pd.concat([df_general, df_new_unique], ignore_index=True).drop_duplicates()

    if len(df_general_updated) > 10000:
        df_general_updated = df_general_updated.tail(10000)

    df_general_updated.to_csv(general_file, index=False, encoding='utf-8-sig')
    df_new_unique.to_csv(new_file, index=False, encoding='utf-8-sig')

    log(f"New: {len(df_new_unique)}, Total: {len(df_general_updated)}")

# ---------- Main ----------

if __name__ == "__main__":
    driver = start_driver()

    all_data = []
    # CT
    all_data.extend(search_and_extract(driver, "chiropractor near Connecticut, USA", allowed_cities_ct))
    all_data.extend(search_and_extract(driver, "massage therapist near Connecticut, USA", allowed_cities_ct))
    all_data.extend(search_and_extract(driver, "acupuncturist near Connecticut, USA", allowed_cities_ct))
    all_data.extend(search_and_extract(driver, "neuropathology near Connecticut, USA", allowed_cities_ct))
    all_data.extend(search_and_extract(driver, "alternative medicine near Connecticut, USA", allowed_cities_ct))
    all_data.extend(search_and_extract(driver, "physical therapist near Connecticut, USA", allowed_cities_ct))

    # Westchester
    all_data.extend(search_and_extract(driver, "chiropractor near Westchester County, New York, USA", allowed_cities_westchester))
    all_data.extend(search_and_extract(driver, "massage therapist near Westchester County, New York, USA", allowed_cities_westchester))
    all_data.extend(search_and_extract(driver, "acupuncturist near Westchester County, New York, USA", allowed_cities_westchester))
    all_data.extend(search_and_extract(driver, "neuropathology near Westchester County, New York, USA", allowed_cities_westchester))
    all_data.extend(search_and_extract(driver, "alternative medicine near Westchester County, New York, USA", allowed_cities_westchester))
    all_data.extend(search_and_extract(driver, "physical therapist near Westchester County, New York, USA", allowed_cities_westchester))

    # Litchfield
    all_data.extend(search_and_extract(driver, "chiropractor near Litchfield County, Connecticut, USA", allowed_cities_litchfield))
    all_data.extend(search_and_extract(driver, "massage therapist near Litchfield County, Connecticut, USA", allowed_cities_litchfield))
    all_data.extend(search_and_extract(driver, "acupuncturist near Litchfield County, Connecticut, USA", allowed_cities_litchfield))
    all_data.extend(search_and_extract(driver, "neuropathology near Litchfield County, Connecticut, USA", allowed_cities_litchfield))
    all_data.extend(search_and_extract(driver, "alternative medicine near Litchfield County, Connecticut, USA", allowed_cities_litchfield))
    all_data.extend(search_and_extract(driver, "physical therapist near Litchfield County, Connecticut, USA", allowed_cities_litchfield))

    # Manhattan (no filtramos)
    all_data.extend(search_and_extract(driver, "chiropractor near Manhattan, New York, USA"))
    all_data.extend(search_and_extract(driver, "massage therapist near Manhattan, New York, USA"))
    all_data.extend(search_and_extract(driver, "acupuncturist near Manhattan, New York, USA"))
    all_data.extend(search_and_extract(driver, "neuropathology near Manhattan, New York, USA"))
    all_data.extend(search_and_extract(driver, "alternative medicine near Manhattan, New York, USA"))
    all_data.extend(search_and_extract(driver, "physical therapist near Manhattan, New York, USA"))

    driver.quit()

    if all_data:
        save_data(all_data)
    else:
        warn("No data extracted.")

    log("RUN COMPLETE ✅")
    with open("run_complete.txt", "w") as f:
        f.write(f"OK {datetime.now().isoformat()}\n")