import os
import time
import requests
from bs4 import BeautifulSoup
import pandas as pd
import matplotlib.pyplot as plt
from selenium.webdriver import Keys

# Explore all databases belonging to the 030401 statistical category
# and display the available tables with their descriptions

url = "https://www.pxweb.bfs.admin.ch/api/v1/de/px-x-0304010000_201"
response = requests.get(url)
data = response.json()
print(type(data))
print(len(data))
print(data[0])
for item in data:
    print(item)
for item in data:
    if "030401" in item["id"]:
        print(item)# Monatlicher Bruttolohn nach Grossregion!


url = ("https://www.pxweb.bfs.admin.ch/api/v1/de/""px-x-0304010000_201/""px-x-0304010000_201.px")

response_1 = requests.get(url)

print(response_1.status_code)

metadata = response_1.json()
print(metadata)
metadata.keys()
metadata['variables']

for variable in metadata["variables"]:
    print("Code:", variable["code"])
    print("Text:", variable["text"])
    print("Values:", variable["values"][:10])
    print("Value texts:", variable["valueTexts"][:10])#only 6 regions:['Schweiz', 'Région lémanique', 'Espace Mittelland', 'Nordwestschweiz', 'Zürich', 'Ostschweiz', 'Zentralschweiz', 'Ticino']
    print()


# Looked in the data base
base_url = "https://www.pxweb.bfs.admin.ch/api/v1/de/"

root = requests.get(base_url).json()

for db in root:
    dbid = db["dbid"]

    if "030401" in dbid:# checked the db with id containing "030401" for canton level data
        url = base_url + dbid
        tables = requests.get(url).json()

        for table in tables:
            print(dbid)
            print("   ", table["text"])
            print()

# Check for canton level salary data from ESTV direct federal tax statistics

url = "https://www.estv.admin.ch/de/statistiken-zur-direkten-bundessteuer"

response = requests.get(url)
response.raise_for_status()
soup = BeautifulSoup(response.content, "html.parser")
print(response.status_code)
print(soup.title.text)

for link in soup.find_all("a"):
    text = link.get_text(strip= True)
    if "2022" in text:
        print(text, "=", link.get("href"))
income_link = None
for link in soup.find_all("a"):
    text = link.get_text(strip = True)
    if "steuerbaren Einkommen" in text and "2022" in text:
        income_link = link.get("href")
        break
print(income_link)

income_response = requests.get(income_link)
income_response.raise_for_status()
income_response.status_code

from io import BytesIO
excel_file = BytesIO(income_response.content)
xls = pd.ExcelFile(excel_file)
print(xls.sheet_names)

excel_file.seek(0)

df_intro = pd.read_excel(
    excel_file,
    sheet_name="Einleitung",
    header=None
)

print(df_intro.head(30).to_string())
excel_file.seek(0)

df = pd.read_excel(
    excel_file,
    sheet_name="Kumulierte Werte von unten",
    header=None
)

print(df.shape)
print(df.head(25).to_string())
cantons = ["Bern", "Zürich", "Luzern", "Genf", "Tessin"]

for canton in cantons:
    found = df.astype(str).apply(
        lambda col: col.str.contains(canton, case=False, na=False)
    )

    print(canton, ":", found.any().any())

# using selenium to scrap the insuance premium data

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select
url = "https://www.priminfo.admin.ch/de/praemien"
driver = webdriver.Chrome()
driver.get(url)
wait = WebDriverWait(driver, 10)
location = wait.until(EC.element_to_be_clickable((By.ID,"form-typeahead-input")))
location.send_keys("Bern")
bern_option = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@role = 'option']//p[text()='3004 Bern']")))
bern_option.click()


year = 1988
birth_year = wait.until(EC.element_to_be_clickable((By.ID, "insured0-yob-input")))
birth_year.clear()
birth_year.send_keys(str(year))


Franchise_element = wait.until(EC.element_to_be_clickable((By.ID, "insured0-franchise-input")))
franchise = Select(Franchise_element)
franchise.select_by_value("300")

accident_yes = wait.until(EC.element_to_be_clickable((By.ID, "form-insured0-coverage-yes-input")))

# Click only if "Yes" is not already selected
if not accident_yes.is_selected():
    accident_yes.click()


model_ids = ["form-models-base-input","form-models-flex-input","form-models-praxis-input","form-models-tel_dig-input","form-models-pharm-input"]

for model_id in model_ids:
    model = wait.until(EC.presence_of_element_located((By.ID, model_id)))
    if not model.is_selected():
        model.click()
standard = wait.until(EC.element_to_be_clickable((By.ID,"form-models-base-input")))
if not standard.is_selected():
    standard.click()

calculate = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR,"button[name='display'][value='savings']")))
calculate.click()


table = wait.until(EC.presence_of_element_located((By.ID, "savingsTable")))

rows = table.find_elements(By.CSS_SELECTOR, "tbody tr")

print("Number of offers:", len(rows))

results = []

for row in rows:

    cells = row.find_elements(By.CSS_SELECTOR, "th, td")

    values = [
        cell.get_attribute("textContent").strip().replace("\xad", "")
        for cell in cells
    ]

    results.append(values)

print(results[:3])

import pandas as pd

df = pd.DataFrame(
    results,
    columns=[
        "insurer",
        "insurance_model",
        "monthly_premium",
        "monthly_reimbursement",
        "monthly_total",
        "yearly_premium",
        "yearly_reimbursement",
        "yearly_total"
    ]
)

print(df.head())
df["postal_code"] = "3004"
df["birth_year"] = 1988
df["franchise"] = 300
df["model_category"] = "Standard"
df["accident"] = True
df["premium_year"] = 2027

df = df[
    [
        "premium_year",
        "postal_code",
        "birth_year",
        "franchise",
        "accident",
        "model_category",
        "insurer",
        "insurance_model",
        "monthly_premium",
        "monthly_reimbursement",
        "monthly_total",
        "yearly_premium",
        "yearly_reimbursement",
        "yearly_total"
    ]
]

print(df.head())


# automated version

# ============================================================
# IMPORTS
# ============================================================

import pandas as pd

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select


# ============================================================
# SETUP SELENIUM
# ============================================================

url = "https://www.priminfo.admin.ch/de/praemien"

driver = webdriver.Chrome()
driver.get(url)

wait = WebDriverWait(driver, 10)


# ============================================================
# MODEL MAPPING
# ============================================================

models = {
    "Standard": "form-models-base-input",
    "FLEX": "form-models-flex-input",
    "PRAXIS": "form-models-praxis-input",
    "TEL_DIG": "form-models-tel_dig-input",
    "PHARM": "form-models-pharm-input"
}


# ============================================================
# FUNCTION TO GET PREMIUMS
# ============================================================

def get_premiums(postal_code, birth_year, franchise, model):

    driver.get(url)
    # --------------------------------------------------------
    # 1. LOCATION
    # --------------------------------------------------------

    location = wait.until(
        EC.element_to_be_clickable(
            (By.ID, "form-typeahead-input")
        )
    )

    location.clear()
    location.send_keys(str(postal_code))

    # Select first autocomplete option starting with postcode
    postal_option = wait.until(
        EC.presence_of_element_located(
            (
                By.XPATH,
                f"//div[@role='option']//p[starts-with(normalize-space(), '{postal_code}')]"
            )
        )
    )

    postal_option.click()


    # --------------------------------------------------------
    # 2. BIRTH YEAR
    # --------------------------------------------------------

    birth_year_element = wait.until(
        EC.element_to_be_clickable(
            (By.ID, "insured0-yob-input")
        )
    )

    birth_year_element.clear()
    birth_year_element.send_keys(str(birth_year))


    # --------------------------------------------------------
    # 3. FRANCHISE
    # --------------------------------------------------------

    franchise_element = wait.until(
        EC.element_to_be_clickable(
            (By.ID, "insured0-franchise-input")
        )
    )

    franchise_select = Select(franchise_element)

    franchise_select.select_by_value(str(franchise))


    # --------------------------------------------------------
    # 4. ACCIDENT COVERAGE
    # --------------------------------------------------------

    accident_yes = wait.until(
        EC.element_to_be_clickable(
            (By.ID, "form-insured0-coverage-yes-input")
        )
    )

    if not accident_yes.is_selected():
        accident_yes.click()


    # --------------------------------------------------------
    # 5. INSURANCE MODEL
    # --------------------------------------------------------

    # First uncheck ALL models
    for model_id in models.values():

        checkbox = wait.until(
            EC.element_to_be_clickable(
                (By.ID, model_id)
            )
        )

        if checkbox.is_selected():
            checkbox.click()


    # Then select only requested model
    selected_model = wait.until(
        EC.element_to_be_clickable(
            (By.ID, models[model])
        )
    )

    if not selected_model.is_selected():
        selected_model.click()


    # --------------------------------------------------------
    # 6. CALCULATE
    # --------------------------------------------------------

    calculate = wait.until(
        EC.element_to_be_clickable(
            (
                By.CSS_SELECTOR,
                "button[name='display'][value='savings']"
            )
        )
    )

    calculate.click()


    # --------------------------------------------------------
    # 7. WAIT FOR RESULTS TABLE
    # --------------------------------------------------------

    table = wait.until(
        EC.presence_of_element_located(
            (By.ID, "savingsTable")
        )
    )

    rows = table.find_elements(
        By.CSS_SELECTOR,
        "tbody tr"
    )


    # --------------------------------------------------------
    # 8. EXTRACT RESULTS
    # --------------------------------------------------------

    results = []

    for row in rows:

        cells = row.find_elements(
            By.CSS_SELECTOR,
            "th, td"
        )

        values = [
            cell.get_attribute("textContent")
                .strip()
                .replace("\xad", "")
            for cell in cells
        ]

        # Skip unexpected rows
        if len(values) < 8:
            continue

        results.append({
            "postal_code": str(postal_code),
            "birth_year": birth_year,
            "franchise": franchise,
            "accident": True,
            "model_category": model,

            "insurer": values[0],
            "insurance_model": values[1],

            "monthly_premium": values[2],
            "monthly_reimbursement": values[3],
            "monthly_total": values[4],

            "yearly_premium": values[5],
            "yearly_reimbursement": values[6],
            "yearly_total": values[7]
        })


    # --------------------------------------------------------
    # 9. CREATE DATAFRAME
    # --------------------------------------------------------

    df = pd.DataFrame(results)

    return df

df_be = get_premiums(
    postal_code="3004",
    birth_year=1988,
    franchise=300,
    model="Standard"
)

print(df_be.head())
print(df_be.shape)
print(df_be["insurance_model"].unique())
print(df_be[["insurer", "insurance_model", "monthly_premium"]])
model="Standard"

df_zh = get_premiums(
    postal_code="8001",
    birth_year=1988,
    franchise=300,
    model="Standard"
)

print(df_zh.head())
print(df_zh.shape)

print(df_zh["insurance_model"].unique())

# 26 cantons loop

canton_postcodes = {
    "ZH": "8001",
    "BE": "3004",
    "LU": "6003",
    "UR": "6460",
    "SZ": "6430",
    "OW": "6060",
    "NW": "6370",
    "GL": "8750",
    "ZG": "6300",
    "FR": "1700",
    "SO": "4500",
    "BS": "4001",
    "BL": "4410",
    "SH": "8200",
    "AR": "9100",
    "AI": "9050",
    "SG": "9000",
    "GR": "7000",
    "AG": "5000",
    "TG": "8500",
    "TI": "6500",
    "VD": "1003",
    "VS": "1950",
    "NE": "2000",
    "GE": "1201",
    "JU": "2800"
}

all_results = []

for canton, postal_code in canton_postcodes.items():

    print(f"Scraping {canton} - {postal_code}")

    df = get_premiums(
        postal_code=postal_code,
        birth_year=1988,
        franchise=300,
        model="Standard"
    )

    df["canton"] = canton

    all_results.append(df)

df_all = pd.concat(
    all_results,
    ignore_index=True
)

print(df_all.head())
print(df_all.shape)

print(df_all.groupby("canton").size())
from pathlib import Path

Path("data").mkdir(exist_ok=True)
df_all.to_csv(
    "data/priminfo_premiums_raw.csv",
    index=False
)

df_all["monthly_premium"] = (
    df_all["monthly_premium"]
    .str.replace("'", "", regex=False)
    .astype(float)
)

import matplotlib.pyplot as plt

canton_median = (
    df_all
    .groupby("canton")["monthly_premium"]
    .median()
    .sort_values()
)

plt.figure(figsize=(10, 8))

plt.barh(
    canton_median.index,
    canton_median.values
)

plt.xlabel("Median monthly premium (CHF)")
plt.ylabel("Canton")
plt.title("Median monthly health insurance premium by canton")

plt.tight_layout()
plt.show()