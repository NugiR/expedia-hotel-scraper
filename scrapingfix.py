import time
import random
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# === CONFIG ===
CHROMEDRIVER_PATH = "./chromedriver.exe"
START_URL = "https://www.expedia.co.id/en/All-Indonesia-Hotels.d81.Travel-Guide-City-All-Hotels"
HEADFUL = True
MAX_PAGES = 3   # batas halaman (ubah sesuai kebutuhan, misalnya 100 atau lebih)
# ==============

def setup_driver():
    options = Options()
    if HEADFUL:
        options.add_argument("--start-maximized")
    else:
        options.add_argument("--headless=new")

    # kurangi jejak automation
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service(CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def pause_for_captcha():
    print("\n⚠️ CAPTCHA terdeteksi. Silakan selesaikan di browser.")
    input("➡️ Tekan Enter di terminal setelah selesai...")

def scrape_page(driver, data, captcha_handled):
    # ambil semua link hotel
    hotel_links = WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, "a.uitk-link.uitk-link-align-left.uitk-link-layout-default.uitk-link-medium")
        )
    )

    for h in hotel_links:
        name = h.text.strip()
        link = h.get_attribute("href")

        if not name or not link or "login" in link or "support" in link:
            continue

        # buka tab baru untuk detail
        driver.execute_script("window.open(arguments[0]);", link)
        driver.switch_to.window(driver.window_handles[1])

        try:
            # cek captcha hanya sekali
            if not captcha_handled and (
                "captcha" in driver.current_url.lower() or "robot" in driver.page_source.lower()
            ):
                pause_for_captcha()
                captcha_handled = True

            # tunggu nama hotel
            hotel_name = WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "h1"))
            ).text.strip()

            # ambil stars
            try:
                stars = driver.find_element(By.CSS_SELECTOR, "span.is-visually-hidden").text.strip()
            except:
                stars = "N/A"

            # 🔽 SCROLL supaya address & breadcrumb muncul
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1.5)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)

            # ambil address
            try:
                address = driver.find_element(
                    By.CSS_SELECTOR,
                    "div.uitk-card-content-section-padded div.uitk-text.uitk-type-start.uitk-type-300.uitk-text-default-theme"
                ).text.strip()
            except:
                address = "N/A"

            # ambil breadcrumb
            try:
                breadcrumb = " > ".join(
                    [b.text.strip() for b in driver.find_elements(By.CSS_SELECTOR, "ol.uitk-breadcrumbs-list li") if b.text.strip()]
                )
            except:
                breadcrumb = "N/A"

            # simpan
            data.append({
                "Hotel Name": hotel_name,
                "Stars": stars,
                "Address": address,
                "Breadcrumb": breadcrumb,
                "Link": link
            })
            print(f"✅ {hotel_name} berhasil diambil")

        except Exception as e:
            print("❌ Gagal scrape:", link, e)

        # tutup tab detail
        driver.close()
        driver.switch_to.window(driver.window_handles[0])

        time.sleep(random.uniform(2, 4))  # delay biar aman

    return captcha_handled


def main():
    driver = setup_driver()
    driver.get(START_URL)

    data = []
    captcha_handled = False  # hanya sekali

    current_page = 1
    while current_page <= MAX_PAGES:
        print(f"\n=== Scraping halaman {current_page} ===")
        captcha_handled = scrape_page(driver, data, captcha_handled)

        # cek tombol Next
        try:
            next_button = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Next"))
            )
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(random.uniform(3, 6))  # tunggu halaman load
            current_page += 1
        except:
            print("🚫 Tidak ada tombol Next, berhenti di halaman terakhir.")
            break

    driver.quit()

    # simpan excel
    df = pd.DataFrame(data)
    df.to_excel("hotel_expedia_all.xlsx", index=False)
    print("\n🎉 Selesai. Data disimpan ke hotel_expedia_all.xlsx")

if __name__ == "__main__":
    main()
