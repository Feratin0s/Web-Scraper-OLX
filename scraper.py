import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
import traceback
import requests
from dotenv import load_dotenv
import schedule

# Carrega variáveis de ambiente
load_dotenv()

# === CONFIGURAÇÃO ===
ESTADOS = {"PE", "BA", "CE", "RN", "PB", "AL", "SE"}
ARQUIVO_ATUAL = "anuncios.json"
ARQUIVO_ANTERIOR = "anuncios_anterior.json"
URL = "https://www.olx.com.br/brasil?q=BYD+DOLPHIN+PLUS"
PAGINAS = 3
HEADLESS_ENV = os.getenv("HEADLESS", "true").strip().lower()
HEADLESS = HEADLESS_ENV in {"true", "1", "yes", "y"}

# === CONFIGURAÇÃO TELEGRAM ===
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def enviar_telegram(mensagem, imagem_url=None):
    """Envia mensagem para o Telegram, opcionalmente com uma imagem"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Configuração do Telegram incompleta. Verifique as variáveis de ambiente.")
        return False
    
    # Se tiver URL de imagem, envia como foto com legenda
    if imagem_url:
        url_api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": imagem_url,
            "caption": mensagem,
            "parse_mode": "HTML"
        }
    else:
        # Caso contrário, envia apenas texto
        url_api = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": mensagem,
            "parse_mode": "HTML"
        }
    
    try:
        response = requests.post(url_api, data=data)
        if response.status_code == 200:
            print("Mensagem enviada com sucesso para o Telegram!")
            return True
        else:
            print(f"Erro ao enviar mensagem: {response.text}")
            return False
    except Exception as e:
        print(f"Erro ao enviar mensagem para o Telegram: {str(e)}")
        return False

def extrair_valor_numerico(preco_texto):
    """Extrai o valor numérico de um texto de preço"""
    import re
    if not preco_texto or preco_texto == "Preço não informado":
        return 0
    
    # Remove todos os caracteres não numéricos, exceto ponto e vírgula
    numeros = re.sub(r'[^\d.,]', '', preco_texto)
    
    # Substitui vírgula por ponto para conversão
    numeros = numeros.replace('.', '').replace(',', '.')
    
    try:
        return float(numeros)
    except:
        return 0

def processar_anuncios():
    """Função principal que executa o scraper da OLX"""
    print(f"[{time.strftime('%d-%m-%Y %H:%M:%S')}] Iniciando processamento de anúncios...")
    
    estados_anuncios = []
    
    try:
        # Reutiliza o driver global
        global driver
        
        # Acessa a URL principal
        print(f"Acessando {URL}...")
        driver.get(URL)
        time.sleep(12)
        
        # Processamento das páginas
        for pagina in range(1, PAGINAS+1):
            print(f"\n=== Processando página {pagina} de {PAGINAS} ===")
            
            # Rola a página para carregar todos os anúncios
            height = driver.execute_script("return document.body.scrollHeight")
            scroll = height - 2000
            driver.execute_script(f"window.scrollTo(0, {scroll});")
            time.sleep(6)
            
            try:
                # Extração dos anúncios
                container = driver.find_element(By.CSS_SELECTOR, "div[class*='adListContainer']")
                anuncios = container.find_elements(By.CSS_SELECTOR, "section.olx-adcard")
                print(f"\nEncontrados {len(anuncios)} anúncios na página {pagina}!\n")
                
                # Processamento de cada anúncio
                for i, anuncio in enumerate(anuncios):
                    try:
                        titulo = anuncio.find_element(By.CSS_SELECTOR, "a[data-testid='adcard-link']").get_attribute("title")
                        
                        try:
                            preco = anuncio.find_element(By.CSS_SELECTOR, "h3[class*='olx-adcard__price']").text
                        except:
                            preco = "Preço não informado"
                        
                        link = anuncio.find_element(By.CSS_SELECTOR, "a[data-testid='adcard-link']").get_attribute("href")
                        
                        try:
                            local = link.split('/')[2].split('.')[0].upper()
                        except:
                            local = "DESCONHECIDO"
                        
                        # Tenta extrair a URL da imagem
                        try:
                            imagem_url = anuncio.find_element(By.CSS_SELECTOR, "img[class*='olx-adcard__image']").get_attribute("src")
                        except:
                            imagem_url = None
                            
                        if local in ESTADOS:
                            item = {
                                "titulo": titulo,
                                "preco": preco,
                                "estado": local,
                                "link": link,
                                "imagem_url": imagem_url,
                                "data_coleta": time.strftime("%d-%m-%Y %H:%M:%S")
                            }
                            estados_anuncios.append(item)
                            print(f"[Anuncio] {titulo} | {preco} | {local}")
                    except Exception as e:
                        print(f"Erro ao processar anúncio #{i+1}: {str(e)}")
                        continue
                
                # Navegação para próxima página
                if pagina < PAGINAS:
                    try:
                        selectors = [
                            "//a[contains(text(), 'Próxima página')]"
                        ]
                        
                        next_button = None
                        for selector in selectors:
                            try:
                                if selector.startswith("//"):
                                    next_button = driver.find_element(By.XPATH, selector)
                                else:
                                    next_button = driver.find_element(By.CSS_SELECTOR, selector)
                                if next_button:
                                    break
                            except:
                                continue
                        
                        if next_button:
                            print(f"Navegando para a página {pagina + 1}...")
                            next_button.click()
                            time.sleep(8)
                        else:
                            next_page_url = f"{URL}&o={pagina + 1}"
                            print(f"Navegando para a URL: {next_page_url}")
                            driver.get(next_page_url)
                            time.sleep(8)
                    except Exception as e:
                        print(f"Erro ao navegar para a próxima página: {str(e)}")
                        break
            except Exception as e:
                print(f"Erro ao processar a página {pagina}: {str(e)}")
                continue
        
        # Salva anúncios atuais
        with open(ARQUIVO_ATUAL, "w", encoding="utf-8") as f:
            json.dump(estados_anuncios, f, ensure_ascii=False, indent=2)
        print(f"\n{len(estados_anuncios)} anúncios salvos em '{ARQUIVO_ATUAL}'")
        
        # Compara com anúncios anteriores
        primeira_execucao = not os.path.exists(ARQUIVO_ANTERIOR) or os.path.getsize(ARQUIVO_ANTERIOR) == 0
        
        if primeira_execucao:
            print("\nPrimeira execução - enviando todos os anúncios encontrados...")
            # Envia todos os anúncios na primeira execução
            for anuncio in estados_anuncios:
                mensagem = f"<b>🚗 ANÚNCIO ENCONTRADO</b>\n\n" \
                          f"<b>Título:</b> {anuncio['titulo']}\n" \
                          f"<b>Preço:</b> {anuncio['preco']}\n" \
                          f"<b>Local:</b> {anuncio['estado']}\n" \
                          f"<b>Link:</b> {anuncio['link']}\n" \
                          f"<b>Data:</b> {anuncio['data_coleta']}"
                
                enviar_telegram(mensagem, anuncio.get('imagem_url'))
                time.sleep(1)  # Pequeno delay para não sobrecarregar a API do Telegram
            
            print(f"\nPrimeira execução — '{ARQUIVO_ANTERIOR}' criado.")
        else:
            try:
                with open(ARQUIVO_ANTERIOR, "r", encoding="utf-8") as f:
                    estados_anterior = json.load(f)
                
                # Links atuais e anteriores
                links_atuais = {item["link"] for item in estados_anuncios}
                links_anteriores = {item["link"] for item in estados_anterior}
                
                # NOVOS
                novos_links = links_atuais - links_anteriores
                novos = [item for item in estados_anuncios if item["link"] in novos_links]
                
                # REMOVIDOS - Verificar se realmente foram removidos (não apenas alterações na página)
                # Só considera removido se o link não estiver na lista atual E o anúncio anterior for do mesmo estado
                removidos_links = links_anteriores - links_atuais
                
                # Verificar se os anúncios realmente foram removidos (não apenas mudanças na paginação)
                # Só notifica se o número de anúncios diminuiu significativamente (mais de 30%)
                if len(links_anteriores) > 0 and len(links_atuais) < len(links_anteriores) * 0.7:
                    removidos = [item for item in estados_anterior if item["link"] in removidos_links]
                else:
                    removidos = []  # Não considera removidos se for apenas mudança na paginação
                
                # PREÇOS REDUZIDOS - Verificar anúncios que tiveram redução de preço
                precos_reduzidos = []
                links_comuns = links_atuais.intersection(links_anteriores)
                
                # Criar dicionários para facilitar a busca
                dict_atual = {item["link"]: item for item in estados_anuncios if item["link"] in links_comuns}
                dict_anterior = {item["link"]: item for item in estados_anterior if item["link"] in links_comuns}
                
                # Verificar reduções de preço
                for link in links_comuns:
                    preco_atual = extrair_valor_numerico(dict_atual[link]["preco"])
                    preco_anterior = extrair_valor_numerico(dict_anterior[link]["preco"])
                    
                    # Se o preço atual for menor que o anterior (e ambos forem válidos)
                    if preco_atual > 0 and preco_anterior > 0 and preco_atual < preco_anterior:
                        # Calcular a porcentagem de redução
                        reducao_percentual = ((preco_anterior - preco_atual) / preco_anterior) * 100
                        
                        # Adicionar informação de redução ao anúncio atual
                        anuncio_com_reducao = dict_atual[link].copy()
                        anuncio_com_reducao["preco_anterior"] = dict_anterior[link]["preco"]
                        anuncio_com_reducao["reducao_percentual"] = reducao_percentual
                        precos_reduzidos.append(anuncio_com_reducao)
                
                print(f"\nNOVOS ANÚNCIOS: {len(novos)}")
                
                # Envia notificações para novos anúncios
                for novo in novos:
                    print(f"   NOVO: {novo['titulo']} | {novo['preco']} | {novo['estado']}")
                    
                    mensagem = f"<b>🚗 NOVO ANÚNCIO</b>\n\n" \
                              f"<b>Título:</b> {novo['titulo']}\n" \
                              f"<b>Preço:</b> {novo['preco']}\n" \
                              f"<b>Local:</b> {novo['estado']}\n" \
                              f"<b>Link:</b> {novo['link']}\n" \
                              f"<b>Data:</b> {novo['data_coleta']}"
                    
                    enviar_telegram(mensagem, novo.get('imagem_url'))
                    time.sleep(1)  # Pequeno delay para não sobrecarregar a API do Telegram
                
                print(f"\nPREÇOS REDUZIDOS: {len(precos_reduzidos)}")
                
                # Envia notificações para anúncios com preços reduzidos
                for anuncio in precos_reduzidos:
                    print(f"   PREÇO REDUZIDO: {anuncio['titulo']} | {anuncio['preco_anterior']} → {anuncio['preco']} | {anuncio['reducao_percentual']:.1f}%")
                    
                    mensagem = f"<b>💰 PREÇO REDUZIDO!</b>\n\n" \
                              f"<b>Título:</b> {anuncio['titulo']}\n" \
                              f"<b>Preço anterior:</b> {anuncio['preco_anterior']}\n" \
                              f"<b>Novo preço:</b> {anuncio['preco']}\n" \
                              f"<b>Redução:</b> {anuncio['reducao_percentual']:.1f}%\n" \
                              f"<b>Local:</b> {anuncio['estado']}\n" \
                              f"<b>Link:</b> {anuncio['link']}\n" \
                              f"<b>Data:</b> {anuncio['data_coleta']}"
                    
                    enviar_telegram(mensagem, anuncio.get('imagem_url'))
                    time.sleep(1)  # Pequeno delay para não sobrecarregar a API do Telegram
                
                print(f"\nANÚNCIOS REMOVIDOS: {len(removidos)}")
                
                # Envia notificações para anúncios removidos
                for removido in removidos:
                    print(f"   REMOVIDO: {removido['titulo']} | {removido['preco']} | {removido['estado']}")
                    
                    mensagem = f"<b>❌ ANÚNCIO REMOVIDO</b>\n\n" \
                              f"<b>Título:</b> {removido['titulo']}\n" \
                              f"<b>Preço:</b> {removido['preco']}\n" \
                              f"<b>Local:</b> {removido['estado']}\n" \
                              f"<b>Link:</b> {removido['link']}\n" \
                              f"<b>Data coleta:</b> {removido['data_coleta']}"
                    
                    enviar_telegram(mensagem, removido.get('imagem_url'))
                    time.sleep(1)  # Pequeno delay para não sobrecarregar a API do Telegram
            except Exception as e:
                print(f"Erro ao comparar com arquivo anterior: {str(e)}")
                traceback.print_exc()
        
        # Salva cópia como anterior para próxima execução
        with open(ARQUIVO_ANTERIOR, "w", encoding="utf-8") as f:
            json.dump(estados_anuncios, f, ensure_ascii=False, indent=2)
        
        print(f"\n[{time.strftime('%d-%m-%Y %H:%M:%S')}] Processamento concluído com sucesso!")
        return True

    except Exception as e:
        print(f"Erro crítico: {str(e)}")
        traceback.print_exc()
        return False

# Inicializa o navegador uma única vez
print("Inicializando o navegador Chrome...")
options = uc.ChromeOptions()
if HEADLESS:
    options.add_argument("--headless=new")  # Modo headless (novo) para ambientes Linux/Docker
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--window-size=1920,1080")
options.add_argument("--lang=pt-BR")
options.add_argument("--disable-gpu")
options.add_argument(
    "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.5993.90 Safari/537.36"
)

# Inicializa o driver globalmente
driver = uc.Chrome(options=options)
driver.set_page_load_timeout(60)
try:
    # Reduz indícios de automação (uc já trata, mas reforçamos)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {
            "source": """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'languages', { get: () => ['pt-BR', 'pt'] });
            Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
            """,
        },
    )
except Exception:
    pass

# Executa imediatamente na primeira vez
processar_anuncios()

# Agenda execuções a cada 30 minutos
print("Configurando agendamento a cada 30 minutos...")
schedule.every(30).minutes.do(processar_anuncios)

# Loop principal de agendamento
print("Iniciando loop de monitoramento...")
while True:
    schedule.run_pending()
    time.sleep(1)
    #print("Esperando 30 minutos...")
