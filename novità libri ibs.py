import time
import pandas as pd
import re
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# --- LINK DI RICERCA ---
URLS = [
    "https://www.ibs.it/libri/ultima-settimana?useAsn=True&filterDepartment=Storia+e+archeologia",
    "https://www.ibs.it/libri/ultima-settimana?useAsn=True&filterDepartment=Società%2c+politica+e+comunicazione",
    "https://www.ibs.it/libri/ultima-settimana?useAsn=True&filterDepartment=Scienze%2c+geografia%2c+ambiente",
    "https://www.ibs.it/libri/ultima-settimana?useAsn=True&filterDepartment=Salute%2c+famiglia+e+benessere+personale",
    "https://www.ibs.it/libri/ultima-settimana?useAsn=True&filterDepartment=Religione+e+spiritualità",
    "https://www.ibs.it/libri/ultima-settimana?useAsn=True&filterDepartment=Psicologia",
    "https://www.ibs.it/libri/ultima-settimana?useAsn=True&filterDepartment=Biografie"
]

def setup_driver():
    chrome_options = Options()
    # Lascia commentato headless per vedere il browser lavorare (utile per debug)
    # chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def get_single_book_description(driver, book_url):
    """
    FASE 2: Apre la pagina e cerca la descrizione dentro cc-em-content-body.
    """
    if not book_url: return "N/D"
    
    try:
        # 1. Navigazione
        driver.get(book_url)
        
        # 2. Check caricamento (Aspetta il titolo H1)
        try:
            WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((By.TAG_NAME, "h1"))
            )
        except:
            return "Errore Timeout Pagina"
        
        # Pausa per rendering completo
        time.sleep(random.uniform(1.0, 1.5))
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # 3. RICERCA SPECIFICA RICHIESTA
        # Cerca prima il contenitore padre: cc-em-content-body
        body_container = soup.find('div', class_='cc-em-content-body')
        
        if body_container:
            # Dentro il padre, cerca il div del testo (cc-content-text)
            # Usiamo lambda per trovarlo anche se ha classi aggiuntive come 'cc-clamp', 'cc-open' etc.
            text_div = body_container.find('div', class_=lambda x: x and 'cc-content-text' in x)
            
            if text_div:
                html_content = text_div.decode_contents()
                
                # Logica <br>: Prendi testo dopo l'ultimo <br> per saltare il titolo ripetuto
                if '<br' in html_content:
                    parts = re.split(r'<br\s*/?>', html_content)
                    raw_text = parts[-1] 
                    return BeautifulSoup(raw_text, 'html.parser').get_text(separator=' ', strip=True)
                else:
                    return text_div.get_text(separator=' ', strip=True)
        
        return "Descrizione non trovata (Selettore errato o assente)"

    except Exception as e:
        print(f"   Err: {e}")
        return "Errore generico"

def parse_list_page(driver, url):
    print(f"\n--- Analisi Lista: {url} ---")
    driver.get(url)
    
    try:
        # Cookie Banner
        try:
            accept_btn = WebDriverWait(driver, 4).until(
                EC.element_to_be_clickable((By.ID, "onetrust-accept-btn-handler"))
            )
            accept_btn.click()
            time.sleep(1)
        except:
            pass

        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "cc-product-list-item"))
        )
        
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
        time.sleep(1.5)
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        cards = soup.find_all('div', class_='cc-product-list-item')
        print(f"Libri trovati in lista: {len(cards)}")
        
        books_in_page = []
        for card in cards:
            try:
                # TITOLO
                title_tag = card.find('a', class_='title') or card.find('a', href=True)
                title = title_tag.get_text(strip=True) if title_tag else "N/D"
                if len(title) < 2: continue 
                
                link = "https://www.ibs.it" + title_tag['href'] if title_tag and title_tag.has_attr('href') else ""
                
                # IMMAGINE
                img_url = ""
                img_col = card.find('div', class_='cc-col-img')
                if img_col:
                    img_tag = img_col.find('img')
                    if img_tag:
                        img_url = img_tag.get('src') or img_tag.get('data-src') or ""

                # AUTORE
                author = "N/D"
                auth_tag = card.find(class_='cc-author')
                if auth_tag:
                    raw_auth = auth_tag.get_text(strip=True)
                    # Toglie "di" all'inizio
                    author = re.sub(r'^di\s*', '', raw_auth, flags=re.IGNORECASE)

                # EDITORE e ANNO
                publisher = "N/D"
                year = "N/D"
                pub_tag = card.find(class_='cc-publisher')
                if pub_tag:
                    pub_text = pub_tag.get_text(strip=True)
                    match_year = re.search(r'(\d{4})$', pub_text)
                    if match_year:
                        year = match_year.group(1)
                        # Toglie anno e virgola finale
                        publisher = pub_text[:match_year.start()].strip().rstrip(',').strip()
                    else:
                        publisher = pub_text.rstrip(',').strip()

                u_id = (title + author).lower()
                
                books_in_page.append({
                    'Copertina': img_url,
                    'Titolo': title,
                    'Autore': author,
                    'Editore': publisher,
                    'Anno': year,
                    'Link': link,
                    'id_univoco': u_id,
                    'Descrizione': '' # Placeholder per Fase 2
                })
            except Exception:
                continue
        return books_in_page

    except Exception as e:
        print(f"Errore parsing lista: {e}")
        return []


        
def main():
    driver = setup_driver()
    all_books_dict = {}
    
    try:
        # FASE 1
        print("=== FASE 1: RACCOLTA ELENCO ===")
        for url in URLS:
            found = parse_list_page(driver, url)
            for b in found:
                if b['id_univoco'] not in all_books_dict:
                    all_books_dict[b['id_univoco']] = b
            time.sleep(1)
        
        # FASE 2
        total = len(all_books_dict)
        print(f"\n=== FASE 2: SCARICO DESCRIZIONI ({total} libri) ===")
        counter = 1
        for uid, book in all_books_dict.items():
            print(f"[{counter}/{total}] {book['Titolo'][:20]}...", end="")
            desc = get_single_book_description(driver, book['Link'])
            all_books_dict[uid]['Descrizione'] = desc
            print(" -> OK")
            counter += 1
            
    finally:
        driver.quit()
    
    # EXPORT
    df = pd.DataFrame(list(all_books_dict.values()))
    if not df.empty:
        df = df.drop(columns=['id_univoco'])
        
        # Riordino colonne
        cols = ['Copertina', 'Titolo', 'Autore', 'Editore', 'Anno', 'Descrizione', 'Link']
        df = df[[c for c in cols if c in df.columns]]
        df = df.sort_values(by='Titolo')
        
        # 1. SALVIAMO IL CSV PER L'APP (Dati puri, link testuali)
        csv_filename = "dati_per_app.csv"
        df.to_csv(csv_filename, index=False)
        print(f"✅ File dati per App salvato: {csv_filename}")
        
        # 2. SALVIAMO L'EXCEL CON IMMAGINI (Per consultazione umana)
        save_excel_with_images(df, "novita_ibs_pro_images.xlsx")
        
    else:
        print("\n❌ Nessun risultato.")

if __name__ == "__main__":
    main()
