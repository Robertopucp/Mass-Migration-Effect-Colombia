import pandas as pd

from selenium import webdriver  
import time   
from selenium.webdriver.support.ui import Select  
from selenium.webdriver.common.by import By  
from selenium.webdriver.common.keys import Keys 
from selenium.common.exceptions import NoSuchElementException
from tqdm import tqdm
from selenium.webdriver.common.action_chains import ActionChains

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as E
from selenium.common import exceptions
from selenium.common.exceptions import StaleElementReferenceException
from seleniumbase import Driver
 
from webdriver_manager.chrome import ChromeDriverManager

import requests
import pandas as pd
import os 
from io import BytesIO
from PIL import Image

import warnings
warnings.filterwarnings('ignore')

#%%

options_chrome = Options()

options_chrome.add_argument('--disable-blink-features=AutomationControlled')

driver = Driver(browser="chrome", headless=False)
url = 'https://www2.cne.gob.ve/rm2021'

driver.get(url)
driver.maximize_window()

fichaframes = {}
total_votos_desagregado = {}
time_file = "Elecciones_2021"
period = 2021
link_text = "Alcaldesa o Alcalde de Municipio"

# Create a folder to save the electoral outcomes 2021

os.makedirs(fr"data/raw/Datasets/Electoral_municipal/{time_file}",
            exist_ok=True)

# Loop through the states and municipalities, extract the electoral outcomes, 
# and save the results in a .dta file for each municipality.
            
for i in tqdm(range(0,26)):
    
    Estados = driver.find_element(By.XPATH,"//select[@formcontrolname='state']")
    Estado_txt = Select(Estados).options[i].text
    Select(Estados).options[i].click()  
    time.sleep(10)
    print(Estado_txt)
    
    Municipios = driver.find_element(By.XPATH,"//select[@formcontrolname='municipio']")
    len_mun = len(Select(Municipios).options)
    
    os.makedirs(fr"data/raw/Datasets/Electoral_municipal/{time_file}/{Estado_txt}", exist_ok=True)
    
    for j in range(2,len_mun):

            Municipios_txt = Select(Municipios).options[j].text
            Select(Municipios).options[j].click() 
            time.sleep(10)
            print(Municipios_txt)
            os.makedirs(fr"data/raw/Datasets/Electoral_municipal/{time_file}/{Estado_txt}/{Municipios_txt}", exist_ok=True)
            
            try:
                driver.find_element(By.XPATH,"//button[@class='btn btn-primary']").click()
                time.sleep(5)
                link_element = driver.find_element(By.LINK_TEXT, link_text)
                link_element.click()
                time.sleep(5)
                
                fichas_tecnica = driver.find_elements(By.XPATH,"//body")
            
                try:
                    ficha = pd.concat(pd.read_html(fichas_tecnica[0].get_attribute('innerHTML'))[1:]).reset_index( drop = True )
                    ficha = ficha.iloc[:,1:]
                    ficha.columns = ['categoria_ficha','votos_ficha','percent_ficha']
                    
                except Exception as e:
                    print(e)
                    print(f"NO FICHA TECNICA IN {Estado_txt} {Municipios_txt}")
                    
                df = pd.read_html(fichas_tecnica[0].get_attribute('innerHTML'))[0]
                grupos = []
                grupo = 0
                            
                for i in range(len(df)):
                    
                    if pd.isna(df.iloc[i, 0]):
                            grupos.append(grupo)
                    else:
                        grupo+=1
                        grupos.append(grupo)

                # add the group number to the dataframe and split the data into two dataframes:
                # one for candidates and another for parties. 
                # Then, merge the two dataframes on the group number and save the results in a .dta file for each municipality.
                
                df['Grupo'] = grupos
                
                df1 = df[~df.iloc[:,0].isna()]
                df1 = df1.iloc[:,[0,2,3,4]]
                df1.columns = ['candidato','votos_candidato','percent_candidato','Grupo']
                df2= df[df.iloc[:,0].isna()]
                df2 = df2.iloc[:,[2,3,4]]
                df2.columns = ['votos_partido','percent_partido','Grupo']
                
                dftot = pd.merge(df1, df2, on = 'Grupo', how = 'left')
                del dftot['Grupo']
                
                try: 
                    partidos = driver.find_elements(By.XPATH,"//td/img")
                    
                    link1 = [link.get_attribute("src") for link in partidos]
                    link2 = [link.split("?")[0] for link in link1 if "partidos" in link]
                    link3 = [link.split("/")[-1] for link in link2]
                    link_clean = [link[:-4] for link in link3]
                    dftot['link_partido']=link_clean
                    
                except Exception as e:
                    print(e)
                    print(f"NO COLUMN PARTIDOS IN {Estado_txt} {Municipios_txt}")
                    
                    
                ficha['Estado'] = Estado_txt
                ficha['Municipio'] = Municipios_txt
                ficha['year']=period
                
                dftot['Estado'] = Estado_txt
                dftot['Municipio'] = Municipios_txt
                dftot['year']=period
                
                fichaframes[f'{Estado_txt}_{Municipios_txt}']=ficha
                total_votos_desagregado[f'{Estado_txt}_{Municipios_txt}']=dftot
                    
                for link in link2:
                    
                    try:
                        res = requests.get(link, timeout=10
                                        , verify=False)
                        image = Image.open(BytesIO(res.content))
                        link_str = link.split("/")[-1]
                        image.save(fr"data/raw/Datasets/Electoral_municipal/{time_file}/{Estado_txt}/{Municipios_txt}/{link_str}")
                    except Exception as e:
                    
                        print(e)
                        print(f"NO DOWNLOAD IMG PARDITO {link_str} - {Estado_txt} {Municipios_txt}")
                    

            
            except Exception as e:
                print(e)
                print(f"NO ALCALDIA ELECCIONES {Estado_txt} {Municipios_txt}")
    
    time.sleep(2)     
    
    
total_raw = pd.concat( total_votos_desagregado.values() ).reset_index( drop = True )
total_raw_ficha = pd.concat( fichaframes.values() ).reset_index( drop = True )

total_raw.to_stata(r"..\..\4_output\Datasets\Electoral_municipal\Votos_por_candidato_2021.dta", write_index=False)
total_raw_ficha.to_stata(r"..\..\4_output\Datasets\Electoral_municipal\Votos_agregada_2021.dta", write_index=False)