# 第二題 

請找 10 個股票代號進行以下題目(須包含錯誤代號，如 0001) 公開資訊觀測站 (twse.com.tw)
- Q1 : 整理紅框資訊各頁籤並進行檔案梳理 (py)
- Q2 : 將梳理結果寫入 RDB (sql)
- Q3 : 留存藍框友善列印結果.pdf (py)

# MOPS 資料爬取與 PDF 匯出

這是一個用 Selenium + BeautifulSoup + SQLite + Chrome DevTools Protocol 
，自動化從臺灣證交所 MOPS 抓取公司基本資料、月營收、財報，並存入 SQLite 
及匯出 PDF 的範例專案。

## 專案結構

mops-scraper/  
├── .gitignore  
├── README.md  
├── requirements.txt  
└── scraper.py # 主程式  


- **scraper.py**  
  主程式，迴圈讀 `company_ids`，執行：  
  - 抓三張資料表 (`basic_info`, `revenue`, `financial`)  
  - 寫入本機 SQLite (`mops.db`)  
  - 產生 PDF (`mops_<companyId>.pdf`)  

- **requirements.txt**  
  列出專案相依套件，方便使用 `pip install -r requirements.txt` 一次安裝。  

- **.gitignore**  
  忽略資料庫檔、PDF、快取、虛擬環境等不必要上傳的檔案。

## 快速開始

1. Clone 到本地：

   ```bash
   git clone https://github.com/dog183729/mops-scraper.git
   cd mops-scraper
   ```
2. 建議建立並啟動 virtualenv：
    ```bash
    python -m venv venv
    source venv/bin/activate    # Linux / macOS
    venv\Scripts\activate       # Windows
    ```
3. 安裝相依套件：
    ```bash
    pip install -r requirements.txt
    ```
4. 執行爬蟲：
    ```bash
    python scraper.py
    ```
    完成後會在資料夾看到：  
    mops.db：SQLite 資料庫  
    mops_<companyId>.pdf：每間公司列印的 PDF  


