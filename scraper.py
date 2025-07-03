import sqlite3
import base64
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# 要查的 companyId 清單
company_ids = [
    "5838", "2762", "6919", "3708", "3018",
    "2002", "1314", "2891", "1718", "0001"
]
BASE_URL = "https://mops.twse.com.tw/mops/#/web/t146sb05?companyId={}"

# 初始化 SQLite
def init_db(db_path="mops.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS basic_info (
      company_id TEXT, item_key TEXT, item_value TEXT,
      PRIMARY KEY(company_id, item_key)
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS revenue (
      company_id TEXT, period TEXT, this_year REAL,
      last_year REAL, growth_rate TEXT,
      PRIMARY KEY(company_id, period)
    )""")
    cur.execute("""
    CREATE TABLE IF NOT EXISTS financial (
      company_id TEXT, section TEXT, period TEXT,
      item TEXT, value REAL,
      PRIMARY KEY(company_id, section, period, item)
    )""")
    conn.commit()
    return conn

# 寫入 DB
def store_to_db(conn, cid, tables):
    cur = conn.cursor()
    # basic_info
    for row in tables.get("basic_info") or []:
        if len(row)==2:
            key,val = row
            cur.execute("""
              INSERT OR REPLACE INTO basic_info
              (company_id,item_key,item_value) VALUES(?,?,?)""",
              (cid, key.rstrip("："), val))
    # revenue
    rows = tables.get("revenue_information") or []
    for i in range(0, len(rows), 2):
        if i+1>=len(rows): break
        header, data = rows[i], rows[i+1]
        if len(data)==3:
            period = header[0]
            ty, ly, gr = data
            try: ty_f=float(ty.replace(",",""))
            except: ty_f=None
            try: ly_f=float(ly.replace(",",""))
            except: ly_f=None
            cur.execute("""
              INSERT OR REPLACE INTO revenue
              (company_id,period,this_year,last_year,growth_rate)
              VALUES(?,?,?,?,?)""",
              (cid,period,ty_f,ly_f,gr))
    # financial
    rows = tables.get("financial_report_information") or []
    if rows:
        periods = rows[0][1:]
        section=None
        for row in rows[1:]:
            if len(row)==1:
                section=row[0]; continue
            item=row[0]
            for idx,val in enumerate(row[1:]):
                try: num=float(val.replace(",",""))
                except: continue
                cur.execute("""
                  INSERT OR REPLACE INTO financial
                  (company_id,section,period,item,value)
                  VALUES(?,?,?,?,?)""",
                  (cid,section,periods[idx],item,num))
    conn.commit()

# 抓取三張 table
def fetch_tables(driver, cid):
    url = BASE_URL.format(cid)
    driver.get(url)
    WebDriverWait(driver,10).until(
      EC.visibility_of_element_located((By.CSS_SELECTOR,".basic_info table"))
    )
    time.sleep(1)
    soup = BeautifulSoup(driver.page_source,"html.parser")
    result={}
    for cls in ("basic_info","revenue_information","financial_report_information"):
        tbls = soup.select(f".{cls} table")
        if not tbls:
            result[cls]=[]
        else:
            rows=[]
            for tr in tbls[0].select("tr"):
                cols=[td.get_text(strip=True) for td in tr.select("th,td")]
                if cols: rows.append(cols)
            result[cls]=rows
    return result

def save_pdf(driver, cid):
    # 點列印按鈕（觸發可能的 JS）
    try:
        btn = driver.find_element(By.CSS_SELECTOR,'span[data-name="列印網頁"]')
        btn.click()
        time.sleep(1)
    except:
        pass
    # 呼叫 CDP 生成 PDF
    pdf = driver.execute_cdp_cmd("Page.printToPDF", {
        "printBackground":True,
        "marginTop":0.4,"marginBottom":0.4,
        "marginLeft":0.4,"marginRight":0.4
    })
    data = base64.b64decode(pdf['data'])
    fn = f"mops_{cid}.pdf"
    with open(fn,"wb") as f: f.write(data)
    print(f"PDF: {fn}")

def main():
    conn = init_db()
    # Chrome headless with CDP
    chrome_opts = Options()
    chrome_opts.add_argument("--headless=new")
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--no-sandbox")
    chrome_opts.add_argument("--disable-dev-shm-usage")
    service = Service(ChromeDriverManager().install())

    for cid in company_ids:
        print(f"=== 處理 companyId={cid} ===")
        driver = webdriver.Chrome(service=service, options=chrome_opts)
        try:
            tables = fetch_tables(driver,cid)
            # 印 debug
            for cls,rows in tables.items():
                print(f"  [{cls}] {len(rows)} rows")
            # 寫入 SQLite
            store_to_db(conn,cid,tables)
            print("資料寫入完成")
            # 產生 PDF
            save_pdf(driver,cid)
        except Exception as e:
            print("失敗：", e)
        finally:
            driver.quit()

    conn.close()

if __name__=="__main__":
    main()