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

FAST_PAUSE = (0.05, 0.12)
STABLE_PAUSE = (0.15, 0.25)

def pause(fast=True):
    t = FAST_PAUSE if fast else STABLE_PAUSE
    time.sleep(random.uniform(*t))

def log(msg): print(f"[INFO] {msg}")
def warn(msg): print(f"[WARN] {msg}")
def err(msg): print(f"[ERROR] {msg}")

def format_title(text):
    return ' '.join([w.capitalize() for w in str(text).strip().split()]) if isinstance(text, str) else ""

def extract_city(address, allowed_cities):
    if not isinstance(address, str): return ""
    parts = address.lower().split(",")
    parts = [re.sub(r'[^a-z\s-]', '', p).strip() for p in parts]
    for part in parts:
        if part in allowed_cities:
            return part
    return ""

# ---------- Driver Initialization ----------

def start_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-gpu")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })

    driver.get("https://www.google.com/maps")
    log("Google Maps loaded")
    time.sleep(2)

    # --- Manejo del banner de cookies ---
    try:
        iframe = WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='consent']"))
        )
        driver.switch_to.frame(iframe)
        accept_btn = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, "//button//*[text()='Accept all']/.."))
        )
        accept_btn.click()
        driver.switch_to.default_content()
        log("✅ Cookies accepted (via iframe)")
        time.sleep(1)
    except Exception:
        try:
            for btn in driver.find_elements(By.TAG_NAME, "button"):
                if any(x in btn.text.lower() for x in ["accept", "agree", "got it"]):
                    btn.click()
                    log("✅ Cookies accepted (simple mode)")
                    break
        except:
            warn("⚠ Cookies banner not found")

    return driver

# ---------- Search and Extract ----------

def search_and_extract(driver, query, allowed_cities, progress=""):
    log(f"🔎 {query} ({progress})")

    try:
        sb = WebDriverWait(driver, 8).until(EC.presence_of_element_located((By.ID, "searchboxinput")))
    except:
        err("Search box issue.")
        return []

    sb.clear(); pause()
    sb.send_keys(query); sb.send_keys(Keys.ENTER)
    pause(False)

    try:
        panel = WebDriverWait(driver, 8).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="feed"]'))
        )
    except:
        err("Result panel not found")
        return []

    prev_count, stable_loops = 0, 0
    max_loops = 60

    for _ in range(max_loops):
        try:
            driver.execute_script('arguments[0].scrollBy(0, 1500);', panel)
        except:
            break
        pause()
        results = driver.find_elements(By.CSS_SELECTOR, 'div.Nv2PK.tH5CWc.THOPZb')
        count = len(results)
        if count == prev_count:
            stable_loops += 1
        else:
            stable_loops = 0
        if stable_loops >= 6:
            break
        prev_count = count

    data = []
    for i, res in enumerate(results):
        try:
            driver.execute_script("arguments[0].scrollIntoView(true);", res)
            pause()
            res.click()
            WebDriverWait(driver, 3.5).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'h1.DUwDvf.lfPIob'))
            )

            name = driver.find_element(By.CSS_SELECTOR, 'h1.DUwDvf.lfPIob').text
            address = ""
            try:
                address = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id=\"address\"]').text
                address = re.sub(r'^\W+', '', address).strip()
            except: pass

            web = ""
            try:
                web = driver.find_element(By.CSS_SELECTOR, 'a[data-item-id=\"authority\"]').get_attribute('href')
            except: pass

            phone = ""
            try:
                phone = driver.find_element(By.CSS_SELECTOR, 'button[data-item-id^=\"phone\"] div.Io6YTe').text.strip()
            except: pass

            city = extract_city(address, allowed_cities)
            if city in allowed_cities:
                data.append({
                    "Name": format_title(name),
                    "Address": format_title(address),
                    "City": city.title(),
                    "Phone Number": phone,
                    "Web": web
                })
        except Exception:
            continue

    log(f"🧭 Finished {query} — got {len(data)} results")
    return data

# ---------- Save CSV ----------

def save_data(data):
    general_file = "data_general.csv"
    new_file = "data_new.csv"

    df_general = pd.read_csv(general_file, encoding='utf-8-sig') if os.path.exists(general_file) else \
                 pd.DataFrame(columns=["Name", "Address", "City", "Phone Number", "Web"])
    df_new = pd.DataFrame(data)

    df_new.drop_duplicates(inplace=True)
    df_general.drop_duplicates(inplace=True)

    new_unique = df_new[~df_new.apply(tuple, axis=1).isin(df_general.apply(tuple, axis=1))]
    updated = pd.concat([df_general, new_unique], ignore_index=True).drop_duplicates()

    updated.to_csv(general_file, index=False, encoding='utf-8-sig')
    new_unique.to_csv(new_file, index=False, encoding='utf-8-sig')

    log(f"🆕 New: {len(new_unique)} | Total: {len(updated)}")

# ---------- Allowed Cities ----------

allowed_cities_ct = {
    'stamford','norwalk','danbury','greenwich','new haven','hartford',
    'waterbury','bridgeport','meriden','milford','hamden','west haven',
    'wallingford','middletown','new britain','newington','bristol',
    'cheshire','shelton','stratford','southbury','derby','fairfield',
    'monroe','newtown','oxford','woodbridge'
}

allowed_cities_westchester = {
    'white plains','yonkers','new rochelle','mount vernon','peekskill',
    'rye','harrison','ossining','port chester','tarrytown','dobbs ferry',
    'hastings-on-hudson','bronxville','pelham','mamaroneck','scarsdale',
    'armonk','elmsford','chappaqua','larchmont','pound ridge','bedford',
    'eastchester','mount kisco'
}

allowed_cities_litchfield = {
    'bantam','barkhamsted','bethlehem','bethlehem village','bridgewater',
    'canaan','falls village','colebrook','cornwall','cornwall bridge',
    'west cornwall','goshen','harwinton','northwest harwinton','kent',
    'south kent','litchfield','east litchfield','northfield','morris',
    'new hartford','new hartford center','pine meadow','new milford',
    'gaylordsville','merryall','chimney point','new milford cdp',
    'northville','norfolk','north canaan','plymouth','east plymouth',
    'roxbury','salisbury','sharon','thomaston','torrington','warren',
    'washington','watertown','winchester','woodbury'
}

allowed_cities_manhattan = {'manhattan','new york'}

allowed_cities_middlesex = {
    'middletown','clinton','chester','deep river','durham','east haddam',
    'east hampton','essex','haddam','killingworth','middlefield','old saybrook',
    'portland','westbrook','cobalt','ivoryton','centerbrook'
}

allowed_cities_hartford = {
    'hartford','avon','berlin','bloomfield','bristol','east granby',
    'east hartford','east windsor','ellington','enfield','farmington',
    'glastonbury','granby','manchester','marion','new britain','newington',
    'plainville','rocky hill','simisbury','south windsor','southington',
    'suffield','vernon','weathersfield','west hartford','wethersfield',
    'windsor','windsor locks'
}

allowed_cities_putnam = {
    'brewster','carmel','cold spring','garrison','lake peekskill',
    'mahapac','mahapac falls','paterson','putnam valley'
}

# ---------- Main ----------

if __name__ == "__main__":
    driver = start_driver()
    all_data = []

    regions = [
        ("Connecticut, USA", allowed_cities_ct),
        ("Westchester County, New York, USA", allowed_cities_westchester),
        ("Litchfield County, Connecticut, USA", allowed_cities_litchfield),
        ("Manhattan, New York, USA", allowed_cities_manhattan),
        ("Middlesex County, Connecticut, USA", allowed_cities_middlesex),
        ("Hartford County, Connecticut, USA", allowed_cities_hartford),
        ("Putnam County, New York, USA", allowed_cities_putnam),
    ]

    professions = [
        "chiropractor","massage therapist","acupuncturist",
        "neuropathology","alternative medicine","physical therapist"
    ]

    # Lista ordenada de tareas
    tasks = [(prof, region_name, cities)
             for prof in professions
             for region_name, cities in regions]

    total = len(tasks)
    log(f"🧭 Starting full run: {total} tasks\n")

    for i, (prof, region_name, cities) in enumerate(tasks, start=1):
        progress = f"{i}/{total}"
        query = f"{prof} near {region_name}"
        log(f"[{progress}] 🔎 {query}")
        data = search_and_extract(driver, query, cities, progress)
        all_data.extend(data)
        time.sleep(random.uniform(1.2, 2.0))

    driver.quit()

    if all_data:
        save_data(all_data)
    else:
        warn("⚠ No data extracted.")

    print(f"\n✅ RUN COMPLETE | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")