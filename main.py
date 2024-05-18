from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random
from termcolor import colored

# Configurações do Selenium
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Executar o Chrome em modo headless (sem interface gráfica)
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36')
driver = webdriver.Chrome(options=options)

def preencher_formulario(uf):
    driver.get("https://portal.cfm.org.br/busca-medicos/")
    
    try:
        # Aguarda o formulário ser carregado
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, 'buscaForm'))
        )

        # Selecionar situação "Ativo"
        situacao = Select(WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, 'tipoSituacao'))
        ))
        situacao.select_by_value('A')
        print("Situação 'Ativo' selecionada.")
        
        # Selecionar tipo de inscrição "Principal"
        tipo_inscricao = Select(WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, 'inscricao'))
        ))
        tipo_inscricao.select_by_value('P')
        print("Tipo de inscrição 'Principal' selecionado.")
        
        # Selecionar UF
        uf_select = Select(WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, 'uf'))
        ))
        uf_select.select_by_value(uf)
        print(f"UF {uf} selecionada.")

        # Scroll para o botão para garantir que está visível
        botao_pesquisar = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'btnPesquisar'))
        )
        driver.execute_script("arguments[0].scrollIntoView();", botao_pesquisar)

        # Movimentos aleatórios do mouse
        actions = webdriver.ActionChains(driver)
        actions.move_to_element(botao_pesquisar).perform()
        time.sleep(random.uniform(1, 3))

        # Aguarda o botão ser clicável
        WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'btnPesquisar'))
        )

        # Enviar formulário
        botao_pesquisar.click()
        print("Formulário enviado.")
        
        # Pausa para garantir que os resultados tenham tempo de carregar
        time.sleep(random.uniform(5, 10))
    except Exception as e:
        print(f"Erro ao preencher o formulário: {e}")

def exportar_cards_para_csv():
    csv_data = []
    cards = driver.find_elements(By.CLASS_NAME, 'resultado-item')
    
    for card in cards:
        try:
            nome = card.find_element(By.TAG_NAME, 'h4').text.strip()
            detalhes = card.find_element(By.CLASS_NAME, 'card-body').text.strip().split('\n')
            detalhes_formatados = [d.replace(',', '').strip() for d in detalhes]
            
            csv_data.append([nome] + detalhes_formatados)
        except Exception as e:
            print(f"Erro ao processar um card: {e}")
    
    return csv_data

def fechar_aviso_lgpd():
    try:
        aviso_lgpd = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'aviso-lgpd'))
        )
        if aviso_lgpd.is_displayed():
            driver.execute_script("arguments[0].style.display = 'none';", aviso_lgpd)
            print("Aviso LGPD fechado.")
    except Exception as e:
        print(f"Nenhum aviso LGPD encontrado ou erro ao fechar: {e}")

def coletar_dados_das_paginas(uf, pagina_inicial, pagina_final):
    csv_data = []
    retries = 3  # Número de tentativas em caso de erro
    
    for pagina in range(pagina_inicial, pagina_final + 1):
        success = False
        for attempt in range(retries):
            try:
                print(f"Raspando página {pagina} da UF {uf}, tentativa {attempt + 1}")
                if pagina == pagina_inicial:
                    preencher_formulario(uf)
                else:
                    fechar_aviso_lgpd()
                    next_button = WebDriverWait(driver, 20).until(
                        EC.element_to_be_clickable((By.XPATH, f"//li[@class='paginationjs-page J-paginationjs-page' and @data-num='{pagina}']/a"))
                    )
                    driver.execute_script("arguments[0].scrollIntoView();", next_button)
                    
                    # Esperar até que o iframe do reCAPTCHA desapareça
                    WebDriverWait(driver, 20).until(
                        EC.invisibility_of_element((By.XPATH, "//iframe[contains(@title, 'desafio reCAPTCHA')]"))
                    )
                    
                    # Clicar no botão usando JavaScript
                    driver.execute_script("arguments[0].click();", next_button)
                    time.sleep(random.uniform(10, 15))  # Aumentar o tempo de espera para garantir o carregamento da nova página

                WebDriverWait(driver, 30).until(  # Aumentar o tempo de espera
                    EC.presence_of_element_located((By.CLASS_NAME, 'resultado-item'))
                )
                csv_data.extend(exportar_cards_para_csv())
                print(colored(f"Sucesso na raspagem da página {pagina} da UF {uf}", 'green'))
                success = True
                break
            except Exception as e:
                print(colored(f"Erro ao carregar resultados na página {pagina} da UF {uf}: {e}", 'red'))
                time.sleep(5)  # Espera antes de tentar novamente

        if not success:
            print(colored(f"Falha na raspagem da página {pagina} da UF {uf} após {retries} tentativas.", 'red'))
            break
    
    return csv_data

# Lista de UFs e número de páginas
ufs_paginas = {
    #'AL': 636,
    #'RJ': 7124,
    #'AM': 611,
    #'AP': 101,
    #'BA': 2852,
    #'CE': 1869,
    #'DF': 1627,
    #'ES': 1269,
    #'GO': 1807,
    #'MA': 764,
    #'MG': 6601,
    #'MT': 776,
    #'MS': 727,
    #'PA': 1061,
    #'PB': 959,
    #'PE': 2151,
    #'PI': 604,
    #'PR': 3435,
    #'RN': 739,
    #'RS': 3756,
    #'RO': 371,
    #'RR': 115,
    #'SC': 2152,
    'SP': 17064,
    #'SE': 519,
    #'TO': 349,
}

try:
    for uf, paginas in ufs_paginas.items():
        print(f"Iniciando raspagem para UF {uf} com {paginas} páginas.")
        dados_medicos = coletar_dados_das_paginas(uf, 1, paginas)
        if dados_medicos:
            # Converter para DataFrame e salvar em CSV
            df = pd.DataFrame(dados_medicos)
            df.to_csv(f'profissionais_{uf}.csv', index=False, encoding='utf-8-sig')
            print(f"Raspagem completa para UF {uf}. Dados salvos em profissionais_{uf}.csv")
        else:
            print(f"Nenhum dado foi raspado para UF {uf}.")
except Exception as e:
    print(f"Erro crítico: {e}")
finally:
    driver.quit()
