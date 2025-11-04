# Web Scraper OLX

Este projeto é um web scraper que monitora anúncios de produtos na OLX em estados específicos do Brasil. O sistema verifica novos anúncios, anúncios removidos e reduções de preço, enviando notificações via Telegram.

## Funcionalidades

- Busca anúncios de qualquer produto na OLX
- Filtra por estados específicos (PE, BA, CE, RN, PB, AL, SE, MA, SP, RJ, MG, PR, SC, RS, etc..)
- Detecta novos anúncios e anúncios removidos
- Identifica reduções de preço nos anúncios
- Envia notificações via Telegram
- Executa automaticamente a cada 30 minutos em um container Docker, pode alterar em ```schedule.every(30).minutes.do(processar_anuncios) ```

## Requisitos

- Python 3.8+
- Docker e Docker Compose (para execução containerizada)
- Conta no Telegram e um bot configurado

## Configuração

1. Clone este repositório
2. Crie um arquivo `.env` na raiz do projeto com as seguintes variáveis:

```
TELEGRAM_BOT_TOKEN=seu_token_do_bot_aqui
TELEGRAM_CHAT_ID=seu_chat_id_aqui
```

3. Personalize a busca no arquivo `scraper.py`:
   - Modifique a variável `URL` para buscar a URL desejada e coloque Brasil na hora de pesquisar na OLX, por exemplo:
   ```python
   URL = "https://www.olx.com.br/brasil?q=carros"
   ```
   - Ajuste `ESTADOS` para filtrar por regiões específicas
   - Configure `PAGINAS` para definir quantas páginas serão analisadas

4. Instale as dependências (se for executar localmente):

```bash
pip install -r requirements.txt
```

## Execução

### Local

```bash
python scraper.py
```

### Docker (Recomendado)

```bash
docker-compose up -d
```

O container será executado automaticamente a cada 30 minutos, mantendo o navegador aberto entre as execuções para maior eficiência.

## GPU NVIDIA (Opcional)

Para aproveitar a GPU NVIDIA dentro do container (melhorando estabilidade de renderização no Chrome headless), siga estes passos:

- Pré-requisitos no host (Linux):
  - Instale os drivers NVIDIA oficiais.
  - Instale o NVIDIA Container Toolkit: `sudo apt-get install -y nvidia-container-toolkit`.
  - Configure o runtime: `sudo nvidia-ctk runtime configure --runtime=docker && sudo systemctl restart docker`.

- Compose e variáveis:
  - O `docker-compose.yml` já está configurado com `gpus: all` e as variáveis `NVIDIA_VISIBLE_DEVICES=all` e `NVIDIA_DRIVER_CAPABILITIES=compute,utility,graphics`.
  - O scraper lê `USE_GPU=true` para habilitar flags de GPU no Chrome (EGL, rasterização por GPU).

- Executar:
  - Inicie com `docker-compose up -d`. Garanta que o host veja a GPU com `nvidia-smi`.

- Observações:
  - Em ambientes sem GPU, deixe `USE_GPU=false` (padrão) e o scraper desativa o GPU no Chrome.
  - Em Docker, é recomendado aumentar `shm_size` (ex.: 1GB) caso enfrente timeouts do renderer.

## Estrutura do Projeto

- `scraper.py`: Script principal do web scraper
- `requirements.txt`: Dependências do projeto
- `Dockerfile`: Configuração para criar a imagem Docker
- `docker-compose.yml`: Configuração para orquestrar o container
- `.env`: Arquivo de variáveis de ambiente (não versionado)
- `anuncios.json`: Arquivo com os anúncios atuais
- `anuncios_anterior.json`: Arquivo com os anúncios da execução anterior

## Como Funciona

1. O script acessa a OLX e busca pelo produto configurado na URL
2. Filtra os anúncios pelos estados configurados
3. Salva os anúncios encontrados em um arquivo JSON
4. Compara com a execução anterior para identificar:
   - Novos anúncios
   - Anúncios removidos
   - Anúncios com redução de preço
5. Envia notificações via Telegram para cada evento
6. Repete o processo a cada 30 minutos, definido em ```schedule.every(30).minutes.do(processar_anuncios) ```

## Notificações Telegram

O sistema envia quatro tipos de notificações:

- **🚗 ANÚNCIO ENCONTRADO**: Na primeira execução, todos os anúncios são enviados
- **🚗 NOVO ANÚNCIO**: Quando um novo anúncio é detectado
- **❌ ANÚNCIO REMOVIDO**: Quando um anúncio não está mais disponível
- **💰 PREÇO REDUZIDO**: Quando um anúncio teve seu preço reduzido

## Personalização

Para adaptar o scraper para outros produtos:

1. Modifique a URL de busca no arquivo `scraper.py`:
   ```python
   URL = "https://www.olx.com.br/brasil?q=seu+produto+aqui"
   ```

2. Ajuste os estados de interesse:
   ```python
   ESTADOS = {"SP", "RJ", "MG"}  # Exemplo para região sudeste
   ```

3. Configure o número de páginas a serem analisadas:
   ```python
   PAGINAS = 5  
   ```

## Solução de Problemas

- **Erro de conexão**: Verifique sua conexão com a internet
- **Notificações não chegam**: Confirme as credenciais do Telegram no arquivo `.env`
- **Falha no Docker**: Verifique se o Docker está instalado e em execução

## Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para abrir issues ou enviar pull requests.