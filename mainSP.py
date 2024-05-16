from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import random
import os

# Configurações do Selenium
options = webdriver.ChromeOptions()
options.add_argument('--headless')  # Executar o Chrome em modo headless (sem interface gráfica)
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36')
driver = webdriver.Chrome(options=options)

def preencher_formulario(municipio):
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
        
        # Selecionar UF "SP"
        uf_select = Select(WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, 'uf'))
        ))
        uf_select.select_by_value('SP')
        print("UF 'SP' selecionada.")

        # Selecionar Município
        municipio_select = Select(WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.NAME, 'municipio'))
        ))
        municipio_select.select_by_value(municipio)
        print(f"Município {municipio} selecionado.")

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

def coletar_dados_das_paginas(municipio, pagina_inicial, pagina_final):
    csv_data = []
    
    for pagina in range(pagina_inicial, pagina_final + 1):
        print(f"Raspando página {pagina} do município {municipio}")
        if pagina == pagina_inicial:
            preencher_formulario(municipio)
        else:
            try:
                fechar_aviso_lgpd()
                next_button = WebDriverWait(driver, 20).until(
                    EC.element_to_be_clickable((By.XPATH, f"//li[@class='paginationjs-page J-paginationjs-page' and @data-num='{pagina}']/a"))
                )
                driver.execute_script("arguments[0].scrollIntoView();", next_button)
                next_button.click()
                time.sleep(random.uniform(5, 10))  # Aguarda o carregamento da nova página
            except Exception as e:
                print(f"Erro ao navegar para a próxima página: {e}")
                break
        
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'resultado-item'))
            )
            csv_data.extend(exportar_cards_para_csv())
        except Exception as e:
            print(f"Erro ao carregar resultados na página {pagina}: {e}")
    
    return csv_data

# Lista de municípios e número de páginas
cidades_paginas = {
    '8853': 3,   # Exemplo: Adamantina tem 3 páginas de resultados
    '8854': 2,   # Exemplo: Adolfo tem 2 páginas de resultados
    # Adicione os municípios restantes com o número de páginas correspondentes
}

output_file = 'profissionais_sp_municipio.csv'

try:
    for municipio, paginas in cidades_paginas.items():
        print(f"Iniciando raspagem para município {municipio} com {paginas} páginas.")
        dados_medicos = coletar_dados_das_paginas(municipio, 1, paginas)
        if dados_medicos:
            # Converter para DataFrame
            df_novo = pd.DataFrame(dados_medicos)
            
            if os.path.exists(output_file):
                # Se o arquivo já existir, ler e anexar os novos dados
                df_existente = pd.read_csv(output_file)
                df_combinado = pd.concat([df_existente, df_novo], ignore_index=True)
            else:
                # Se o arquivo não existir, os novos dados serão o DataFrame final
                df_combinado = df_novo
                
            # Salvar em CSV
            df_combinado.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"Dados adicionados ao arquivo {output_file} para município {municipio}.")
        else:
            print(f"Nenhum dado foi raspado para município {municipio}.")
except Exception as e:
    print(f"Erro crítico: {e}")
finally:
    driver.quit()
