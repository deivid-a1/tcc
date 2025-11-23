import logging
import requests
import fitz
import io
import os
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

def _scrape_html(content: str) -> str:
    soup = BeautifulSoup(content, 'lxml')
    
    for tag in soup(['nav', 'footer', 'aside', 'script', 'style', 'header', 'form']):
        tag.decompose()
        
    main_content = soup.find('main') or soup.find('article') or soup.find("div", {"role": "main"}) or soup.body
    
    if main_content:
        text = ' '.join(main_content.get_text(separator=' ', strip=True).split())
        return text
    return ""

def _scrape_pdf(content: bytes) -> str:
    text = ""
    try:
        with io.BytesIO(content) as stream:
            with fitz.open(stream=stream, filetype="pdf") as doc:
                for page in doc:
                    text += page.get_text() + "\n"
        return ' '.join(text.split())
    except Exception as e:
        logger.error(f"Falha ao processar PDF: {e}", exc_info=True)
        return ""

def _scrape_dynamic(url: str) -> str:
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(user_agent=HEADERS['User-Agent'])
            page.goto(url, wait_until="networkidle", timeout=10000)
            content = page.content()
            browser.close()
            return _scrape_html(content)
    except Exception as e:
        logger.warning(f"[Playwright Falhou] Erro ao tentar extração dinâmica para {url}: {e}", exc_info=True)
        return ""

def fetch_url_content(url: str) -> str | None:
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '').lower()

        if 'application/pdf' in content_type:
            logger.debug(f"Extraindo (PDF - Web) de: {url}")
            return _scrape_pdf(response.content)
        
        elif 'text/html' in content_type:
            logger.debug(f"Extraindo (HTML) de: {url}")
            text = _scrape_html(response.text)
            
            if len(text.split()) < 50:
                logger.warning(f"HTML fraco detectado ({len(text)}B). Tentando extração dinâmica (Playwright) para: {url}")
                text = _scrape_dynamic(url)
            return text
            
        else:
            logger.warning(f"Tipo de conteúdo não suportado ({content_type}) para: {url}")
            return None

    except requests.exceptions.HTTPError as e:
        logger.warning(f"[Erro HTTP {e.response.status_code}] Falha ao buscar {url}")
        return None
    except requests.exceptions.RequestException as e:
        logger.warning(f"[Erro de Rede] Falha ao buscar {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"[Erro de Extração Inesperado] Falha em {url}: {e}", exc_info=True)
        return None

def read_local_file_content(filepath: str) -> str | None:
    try:
        if filepath.endswith('.pdf'):
            logger.debug(f"Extraindo (PDF - Local) de: {filepath}")
            with open(filepath, 'rb') as f:
                content_bytes = f.read()
            return _scrape_pdf(content_bytes)
            
        elif filepath.endswith('.txt') or filepath.endswith('.md'):
            logger.debug(f"Extraindo (TXT - Local) de: {filepath}")
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
                
        else:
            logger.warning(f"Tipo de ficheiro local não suportado: {filepath}. Pulando.")
            return None
            
    except Exception as e:
        logger.error(f"Falha ao ler ficheiro local {filepath}: {e}", exc_info=True)
        return None