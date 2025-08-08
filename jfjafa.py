import pandas as pd
import re
import time
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

# Función para extraer mails de un string
def extract_email(text):
    emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    return emails[0] if emails else ""

# Setup del driver
def start_driver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

# Extraer correos recorriendo toda la web
def find_email_on_site(driver, base_url, max_pages=10):
    visited = set()
    to_visit = [base_url]

    while to_visit and len(visited) < max_pages:
        url = to_visit.pop(0)
        if url in visited or not url.startswith(base_url):
            continue

        try:
            driver.get(url)
            time.sleep(1.5)
            html = driver.page_source
            email = extract_email(html)
            if email:
                return email
            visited.add(url)

            links = driver.find_elements(By.TAG_NAME, "a")
            for link in links:
                href = link.get_attribute("href")
                if href and base_url in href and href not in visited:
                    to_visit.append(href)

        except Exception:
            continue

    return ""

# Cargar CSV
df = pd.read_csv("/Users/facundoa.sardo/Desktop/data.csv")
df["Mail"] = ""

# Procesar con Selenium
driver = start_driver()
for i, row in df.iterrows():
    url = str(row["Web"]).strip()
    if url.startswith("http"):
        print(f"Buscando en: {url}")
        try:
            email = find_email_on_site(driver, url)
            df.at[i, "Mail"] = email
        except Exception as e:
            print(f"Error en {url}: {e}")
    else:
        print(f"URL inválida: {url}")
driver.quit()

# Guardar resultados
df.to_csv("/Users/facundoa.sardo/Desktop/data_with_emails.csv", index=False, encoding="utf-8-sig")
print("✅ Correos extraídos y guardados en 'data_with_emails.csv'")
