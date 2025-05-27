import multiprocessing
import signal
import pandas as pd
import time
import random
from termcolor import colored
# Remova:
# import requests
# API_2CAPTCHA_KEY = "SUA_API_KEY_AQUI"  # Substitua pela sua chave de API do 2Captcha

def log(msg, color="white"):
    print(colored(msg, color))

def preencher_formulario(driver, uf):
    try:
        driver.get("https://portal.cfm.org.br/busca-medicos/")
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, 'buscaForm'))
        )
        # Situação "Ativo"
        Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'tipoSituacao'))
        )).select_by_value('A')
        log("Situação 'Ativo' selecionada.", "cyan")
        # Tipo de inscrição "Principal"
        Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'inscricao'))
        )).select_by_value('P')
        log("Tipo de inscrição 'Principal' selecionado.", "cyan")
        # UF
        Select(WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, 'uf'))
        )).select_by_value(uf)
        log(f"UF {uf} selecionada.", "cyan")
        # Botão pesquisar
        botao_pesquisar = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CLASS_NAME, 'btnPesquisar'))
        )
        driver.execute_script("arguments[0].scrollIntoView();", botao_pesquisar)
        botao_pesquisar.click()
        log("Formulário enviado.", "green")
        # Pequena pausa para garantir início do carregamento
        time.sleep(random.uniform(1, 2))
    except Exception as e:
        log(f"Erro ao preencher formulário: {e}", "red")
        raise

def fechar_aviso_lgpd(driver):
    try:
        aviso = WebDriverWait(driver, 3).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'aviso-lgpd'))
        )
        if aviso.is_displayed():
            driver.execute_script("arguments[0].style.display = 'none';", aviso)
            log("Aviso LGPD fechado.", "yellow")
    except Exception:
        pass

def exportar_cards_para_csv(driver):
    csv_data = []
    cards = driver.find_elements(By.CLASS_NAME, 'resultado-item')
    for card in cards:
        try:
            nome = card.find_element(By.TAG_NAME, 'h4').text.strip()
            detalhes = card.find_element(By.CLASS_NAME, 'card-body').text.strip().split('\n')
            detalhes_formatados = [d.replace(',', '').strip() for d in detalhes]
            csv_data.append([nome] + detalhes_formatados)
        except Exception as e:
            log(f"Erro ao processar um card: {e}", "magenta")
    return csv_data

def ir_para_pagina(driver, pagina):
    try:
        # Botão da página
        paginador = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'paginationjs'))
        )
        botao = paginador.find_element(By.XPATH, f".//li[@data-num='{pagina}']/a")
        driver.execute_script("arguments[0].scrollIntoView();", botao)
        botao.click()
        log(f"Página {pagina} selecionada.", "blue")
        time.sleep(random.uniform(1, 2))
    except Exception as e:
        log(f"Erro ao navegar para página {pagina}: {e}", "red")
        raise

def coletar_dados_das_paginas(uf, pagina_inicial, pagina_final, driver):
    dados = []
    try:
        tentativas_pagina1 = 0
        while tentativas_pagina1 < 3:
            try:
                preencher_formulario(driver, uf)
                log("Aguardando resultados...", "yellow")
                WebDriverWait(driver, 60).until(
                    EC.visibility_of_element_located((By.CLASS_NAME, 'resultado-item'))
                )
                log(f"Resultados carregados para a página 1 da UF {uf}", "green")
                dados.extend(exportar_cards_para_csv(driver))
                break
            except Exception as e:
                tentativas_pagina1 += 1
                log(f"Erro ao carregar resultados na página 1 da UF {uf}, tentativa {tentativas_pagina1}: {e}", "red")
                time.sleep(5)
        else:
            log(f"Falha ao carregar resultados na página 1 da UF {uf} após 3 tentativas.", "red")
            return dados

        for pagina in range(pagina_inicial + 1, pagina_final + 1):
            tentativas = 0
            while tentativas < 3:
                try:
                    fechar_aviso_lgpd(driver)
                    ir_para_pagina(driver, pagina)
                    WebDriverWait(driver, 30).until(
                        EC.presence_of_element_located((By.CLASS_NAME, 'resultado-item'))
                    )
                    log(f"Raspando página {pagina} da UF {uf}", "white")
                    dados.extend(exportar_cards_para_csv(driver))
                    log(f"Sucesso na raspagem da página {pagina} da UF {uf}", "green")
                    break
                except Exception as e:
                    tentativas += 1
                    log(f"Erro na página {pagina} da UF {uf}, tentativa {tentativas}: {e}", "red")
                    time.sleep(5)
            else:
                log(f"Falha na raspagem da página {pagina} da UF {uf} após 3 tentativas.", "red")
                break
    except Exception as e:
        log(f"Erro crítico durante a raspagem da UF {uf}: {e}", "red")
    return dados

def raspagem_uf(uf, paginas):
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select, WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    options = webdriver.ChromeOptions()
    # options.add_argument('--headless')  # Rode com interface gráfica
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36')
    options.binary_location = "/usr/bin/chromium-browser"
    service = Service("/snap/bin/chromium.chromedriver")
    driver = webdriver.Chrome(service=service, options=options)

    dados_medicos = []
    try:
        log(f"Iniciando raspagem para UF {uf} com {paginas} páginas.", "yellow")
        dados_medicos = coletar_dados_das_paginas(uf, 1, paginas, driver)
    except Exception as e:
        log(f"Erro crítico na UF {uf}: {e}", "red")
    finally:
        # Salva o que foi coletado até o momento
        if dados_medicos:
            df = pd.DataFrame(dados_medicos)
            df.to_csv(f'profissionais_{uf}.csv', index=False, encoding='utf-8-sig')
            log(f"Dados salvos em profissionais_{uf}.csv (UF {uf})", "green")
        else:
            log(f"Nenhum dado foi raspado para UF {uf}.", "red")
        driver.quit()

if __name__ == "__main__":
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import Select, WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC

    ufs_paginas = {
    'AC': 146, 
    'AL': 684,
    'AM': 643,
    #'AP': 109,
    #'BA': 3078,
    #'CE': 1976,
    #'DF': 1720,
    #'ES': 1348,
    #'GO': 1975,
    #'MA': 826,
    #'MG': 7004,
    #'MT': 831,
    #'MS': 768,
    #'PA': 1128,
    #'PB': 1039,
    #'PE': 2301,
    #'PI': 658,
    #'PR': 3717,
    #'RJ': 7429,
    #'RN': 788,
    #'RS': 3895,
    #'RO': 410,
    #'RR': 121,
    #'SC': 2318,
    #'SP': 17897,
    #'SE': 550,
    #'TO': 379,
}

    max_processes = 3
    pool = multiprocessing.Pool(processes=max_processes)
    args = [(uf, paginas) for uf, paginas in ufs_paginas.items()]

    try:
        pool.starmap(raspagem_uf, args)
    except KeyboardInterrupt:
        log("Interrompido pelo usuário.", "red")
        pool.terminate()
    finally:
        pool.close()
        pool.join()