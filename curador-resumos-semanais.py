import feedparser
import requests
import smtplib
import ssl
import os
import json
import urllib.parse
import random
import time
from google import genai
from google.genai import types
from email.message import EmailMessage
from datetime import datetime, timedelta

# ==========================================
# CONFIGURAÇÕES DE API E VARIÁVEIS
# ==========================================
client = genai.Client(api_key=os.environ.get('GEMINI_API_KEY'))

LINKEDIN_ACCESS_TOKEN = os.environ.get('LINKEDIN_ACCESS_TOKEN')
LINKEDIN_URN_ID = os.environ.get('LINKEDIN_URN_ID') 
SENHA_APP_GMAIL = os.environ.get('SENHA_APP_GMAIL')

EMAIL_REMETENTE = "wellesmatias@gmail.com"
EMAIL_DESTINO = "wellesmatias@gmail.com"
AGENT_NAME = "Curador Orçamentário"

# Arquivos de memória do agente
ARQUIVO_HISTORICO_NOTICIAS = "historico_noticias.txt"
ARQUIVO_HISTORICO_IMAGENS = "historico_imagens.txt"
ARQUIVO_HISTORICO_TEMAS = "historico_temas_180dias.txt"

# ==========================================
# AGENDA DINÂMICA: SEGUNDA A DOMINGO
# ==========================================
url_b = "https://images.unsplash.com/photo-"
param = "?auto=format&fit=crop&w=800&q=80&fm=jpg"

AGENDA = {
    0: { # SEGUNDA-FEIRA: IA e Governança Pública
        "tema": "Inteligência Artificial e Governança Pública",
        "busca_rss": '"inteligência artificial" AND ("governança pública" OR "gestão pública" OR governo) Brasil',
        "periodo_rss": "14d",
        "imagens": [f"{url_b}1518770660439-4636190af475{param}", f"{url_b}1523961131990-521072f16c58{param}", f"{url_b}1485827404703-89b55fcc595e{param}", f"{url_b}1550751827-4bd374c3f58b{param}", f"{url_b}1620712943543-bcc4688e7485{param}", f"{url_b}1507146426996-ef05306b995a{param}"]
    },
    1: { # TERÇA-FEIRA: PowerBI e Dados do Orçamento
        "tema": "PowerBI e Dados do Orçamento Público",
        "busca_rss": '("PowerBI" OR "Power BI" OR "análise de dados" OR "big data") AND ("orçamento público" OR "transparência" OR contas) Brasil',
        "periodo_rss": "14d",
        "imagens": [f"{url_b}1551288049-bebda4e38f71{param}", f"{url_b}1460925895917-afdab827c52f{param}", f"{url_b}1504868584819-f81d1136b69b{param}", f"{url_b}1543286386-2a6593b482bc{param}", f"{url_b}1555949963-ff9fe0c870eb{param}", f"{url_b}1590283603385-17ffb3a77196{param}"]
    },
    2: { # QUARTA-FEIRA: Ferramentas Ágeis
        "tema": "Ferramentas Ágeis para uso em Orçamento Público",
        "busca_rss": '("metodologias ágeis" OR scrum OR kanban OR agile) AND ("gestão pública" OR "orçamento público" OR governo) Brasil',
        "periodo_rss": "30d",
        "imagens": [f"{url_b}1531403009284-440f080d1e12{param}", f"{url_b}1512758117961-39a5ee0fcc53{param}", f"{url_b}1542744173-8e7e53415bb0{param}", f"{url_b}1611224885990-ab7363d1f2a9{param}", f"{url_b}1522071820081-009f0129c71c{param}", f"{url_b}1581291518852-f56f9a562479{param}"]
    },
    3: { # QUINTA-FEIRA: TBT Orçamentário
        "tema": "TBT: Resumo do Fato Orçamentário Mais Impactante da Semana", 
        "busca_rss": '"orçamento público" OR "política fiscal" Brasil', 
        "periodo_rss": "7d",
        "imagens": [f"{url_b}1501139083538-0139583c060f{param}", f"{url_b}1495364141860-b0d03dea4520{param}", f"{url_b}1506784901227-36bd224a6a0e{param}", f"{url_b}1435348773515-59c274d812ce{param}", f"{url_b}1584844697368-45b084931bc7{param}", f"{url_b}1517411032315-54ef2cb783bb{param}", f"{url_b}1509653087866-e1f51b0f16f5{param}", f"{url_b}1464013778559-00664e4ea754{param}", f"{url_b}1528659103823-356bcba14c40{param}", f"{url_b}1485601133034-722026526eb6{param}"]
    },
    4: { # SEXTA-FEIRA: Aplicações Práticas de IA no Orçamento
        "tema": "Exemplos de aplicações práticas com uso de IA na área de Orçamento Público",
        "busca_rss": '("inteligência artificial" OR "machine learning" OR algoritmo) AND "orçamento público" Brasil',
        "periodo_rss": "30d",
        "imagens": [f"{url_b}1677442136019-21780ecad995{param}", f"{url_b}1620825937374-87fc7d620c1c{param}", f"{url_b}1535223289027-5bf7e2a6c331{param}", f"{url_b}1451187580459-43490279c0fa{param}", f"{url_b}1504384308090-c894fdcc538d{param}"]
    },
    5: { # SÁBADO: Boletim Semanal - Top 10 Assuntos
        "tema": "Boletim Semanal: Os 10 principais assuntos da semana sobre Planejamento, Orçamento e Finanças Públicas",
        "busca_rss": '("planejamento governamental" OR "orçamento público" OR "finanças públicas") Brasil',
        "periodo_rss": "7d",
        "imagens": [f"{url_b}1585829365295-ab7cd400c167{param}", f"{url_b}1504711434969-e33886168f5c{param}", f"{url_b}1495020632543-9ed624ab822b{param}", f"{url_b}1450101499163-e587978d1844{param}", f"{url_b}1526628953301-3e589a6a8b74{param}", f"{url_b}1512314889357-e1a240ea0c5e{param}"]
    },
    6: { # DOMINGO: Perspectivas para a próxima semana
        "tema": "Perspectivas e Tendências: O que será destaque em Orçamento e Finanças Públicas na próxima semana",
        "busca_rss": '("orçamento público" OR "finanças públicas") (pauta OR congresso OR expectativa OR "próxima semana" OR tendência) Brasil',
        "periodo_rss": "7d",
        "imagens": [f"{url_b}1486406146926-c627a92ad1ab{param}", f"{url_b}1506485338023-6ce5f36692eb{param}", f"{url_b}1434030216411-0b793f4b4273{param}", f"{url_b}1518182170546-076616fd4aa7{param}", f"{url_b}1454165804606-c3d57bc86b40{param}", f"{url_b}1507925922837-3f500156d967{param}"]
    }
}

# ==========================================
# FUNÇÕES DE MEMÓRIA E DESIGN
# ==========================================
def ler_historico(arquivo):
    if os.path.exists(arquivo):
        with open(arquivo, "r", encoding="utf-8") as f:
            return [linha.strip() for linha in f.readlines() if linha.strip()]
    return []

def salvar_historico(novo_item, arquivo, limite=180):
    historico = ler_historico(arquivo)
    if novo_item and novo_item not in historico:
        historico.append(novo_item)
    
    if len(historico) > limite:
        historico = historico[-limite:]
        
    with open(arquivo, "w", encoding="utf-8") as f:
        for item in historico:
            f.write(f"{item}\n")

def aplicar_negrito(texto):
    resultado = ""
    for char in texto:
        if 'A' <= char <= 'Z': resultado += chr(ord(char) - ord('A') + 0x1D5D4)
        elif 'a' <= char <= 'z': resultado += chr(ord(char) - ord('a') + 0x1D5EE)
        elif '0' <= char <= '9': resultado += chr(ord(char) - ord('0') + 0x1D7EC)
        elif char in ['ç', 'Ç']: resultado += '𝗰̧'
        elif char in ['ã', 'Ã']: resultado += '𝗮̃'
        elif char in ['á', 'Á']: resultado += '𝗮́'
        elif char in ['é', 'É']: resultado += '𝗲́'
        elif char in ['í', 'Í']: resultado += '𝗶́'
        elif char in ['ó', 'Ó']: resultado += '𝗼́'
        elif char in ['ú', 'Ú']: resultado += '𝘂́'
        elif char in ['ê', 'Ê']: resultado += '𝗲̂'
        elif char in ['ô', 'Ô']: resultado += '𝗼̂'
        else: resultado += char
    return resultado

def extrair_nome_fonte(titulo_rss):
    partes = titulo_rss.split(' - ')
    return partes[-1].strip() if len(partes) > 1 else "Fonte da Notícia"

def buscar_noticias(termo, periodo="7d", limite=25):
    termo_busca = urllib.parse.quote_plus(termo)
    url = f"https://news.google.com/rss/search?q={termo_busca}+when:{periodo}&hl=pt-BR&gl=BR&ceid=BR:pt-419"
    feed = feedparser.parse(url)
    return [{"titulo": e.title, "link": e.link, "fonte": extrair_nome_fonte(e.title)} for e in feed.entries[:limite]]

# ==========================================
# CÉREBRO CURADOR (LLM) E REGRAS
# ==========================================
def criar_conteudo_do_dia():
    dia_semana = datetime.now().weekday()
    
    if dia_semana not in AGENDA:
        print(f"Sem agendamento válido para o dia {dia_semana}.")
        return None

    config_dia = AGENDA[dia_semana]
    texto_contexto_noticias = ""
    
    periodo = config_dia.get("periodo_rss", "7d")
    noticias_brutas = buscar_noticias(config_dia["busca_rss"], periodo, limite=40) # Limite aumentado para suprir o Top 10
    historico_noticias = ler_historico(ARQUIVO_HISTORICO_NOTICIAS)
    noticias_validas = [n for n in noticias_brutas if n['link'] not in historico_noticias]
    
    if noticias_validas:
        for i, n in enumerate(noticias_validas[:20]):
            texto_contexto_noticias += f"[ID: {i}] {n['titulo']} | Fonte: {n['fonte']}\nLink: {n['link']}\n\n"
    else:
        texto_contexto_noticias = "Nenhuma notícia exata localizada. Crie um artigo autoral e aprofundado com base no Tema de hoje."

    historico_temas_gerados = ler_historico(ARQUIVO_HISTORICO_TEMAS)
    texto_historico_temas = "\n".join(historico_temas_gerados[-50:]) if historico_temas_gerados else "Nenhum histórico recente."

    schema = {
        "type": "OBJECT",
        "properties": {
            "id_noticia_selecionada": {"type": "INTEGER", "description": "ID da notícia base (-1 se compilação/teórico)."},
            "titulo_post": {"type": "STRING", "description": "Manchete atrativa para LinkedIn."},
            "corpo_post": {"type": "STRING", "description": "Texto do post, incluindo a menção sutil ao produto Amazon no último parágrafo."},
            "tema_especifico": {"type": "STRING", "description": "Resumo de 4 palavras do núcleo principal deste post (para evitar repetição)."},
            "termo_busca_amazon": {"type": "STRING", "description": "Termos exatos para jogar na barra de pesquisa da Amazon (Ex: 'Livro Inteligência Artificial Setor Público', 'Livro Finanças Públicas')."},
            "hashtags": {"type": "STRING"}
        },
        "required": ["id_noticia_selecionada", "titulo_post", "corpo_post", "tema_especifico", "termo_busca_amazon", "hashtags"]
    }

    for tentativa in range(5):
        prompt = (
            f"Assuma a persona do {AGENT_NAME}, um experiente Especialista em Governança Orçamentária "
            "e instrutor de escolas de governo. Sua audiência é técnica e de alto nível no LinkedIn.\n\n"
            f"A TAREFA DE HOJE: Escrever uma publicação sobre '{config_dia['tema']}'.\n\n"
            "⚠️ REGRA INSTITUCIONAL: É EXPRESSAMENTE PROIBIDO textos polêmicos ou críticas contra o Governo. Foco 100% técnico.\n"
            "⚠️ REGRA DE NOVIDADE: Você DEVE gerar uma abordagem original. NÃO REPITA assuntos já tratados.\n"
            f"TEMAS JÁ TRATADOS NOS ÚLTIMOS MESES (EVITE ESTES):\n{texto_historico_temas}\n\n"
            f"MATERIAL BASE DAS NOTÍCIAS:\n{texto_contexto_noticias}\n\n"
            "💸 MONETIZAÇÃO SUTIL (AMAZON):\n"
            "Dentro do último ou penúltimo parágrafo, debata sutilmente sobre a necessidade de capacitação, leitura ou ferramental, "
            "e sugira que buscar livros, equipamentos ou softwares sobre o tema fortalece o profissional. O texto deve preparar o leitor para clicar no link de produto da Amazon ao final do post. "
            "Forneça o 'termo_busca_amazon' ideal relacionado à sua sugestão (Ex: livro orcamento publico)."
        )
        
        # Ajustes de Regras Específicas por dia
        if dia_semana == 3: # Regra específica do TBT
            prompt += f"\nFORMATO EXIGIDO (TBT):\nEscolha a notícia de maior impacto, inicie com '#TBT da Governança'."
        elif dia_semana == 5: # Sábado - Boletim Top 10
            prompt += f"\nFORMATO EXIGIDO (SÁBADO - BOLETIM TOP 10):\nCrie um boletim informativo estruturado listando e resumindo de forma objetiva os 10 principais assuntos mais comentados da semana sobre planejamento, orçamento e finanças públicas. Use as notícias fornecidas como base e, se não houver 10 diferentes, complemente a lista com os temas estruturais e recorrentes de maior peso no momento atual."
        elif dia_semana == 6: # Domingo - Tendências
            prompt += f"\nFORMATO EXIGIDO (DOMINGO - PERSPECTIVAS DA SEMANA SEGUINTE):\nFaça uma análise preditiva em formato de 'Radar'. Discuta e aponte o que deverá ser pauta, os assuntos que estarão mais em voga ou as expectativas de movimentação na área de planejamento e finanças públicas na semana que se inicia (possíveis pautas de congresso, discussões de arrecadação, etc)."

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7 + (tentativa * 0.1),
                    response_mime_type="application/json",
                    response_schema=schema,
                )
            )
            dados_ia = json.loads(response.text)
            
            tema_atual = dados_ia.get('tema_especifico', '').strip().lower()
            if any(tema_atual in t.lower() for t in historico_temas_gerados) and tentativa < 4:
                print(f"Tentativa {tentativa+1}: Tema '{tema_atual}' já repetido. Refazendo...")
                time.sleep(2)
                continue
                
            link_origem = ""
            id_escolhido = int(dados_ia.get('id_noticia_selecionada', -1))
            if 0 <= id_escolhido < len(noticias_validas):
                link_origem = noticias_validas[id_escolhido]['link']
                salvar_historico(link_origem, ARQUIVO_HISTORICO_NOTICIAS)

            historico_imagens = ler_historico(ARQUIVO_HISTORICO_IMAGENS)
            imagens_disponiveis = [img for img in config_dia["imagens"] if img not in historico_imagens]
            
            if not imagens_disponiveis:
                imagens_disponiveis = config_dia["imagens"] 
            
            imagem_final = random.choice(imagens_disponiveis)
            salvar_historico(imagem_final, ARQUIVO_HISTORICO_IMAGENS, limite=40) 
            salvar_historico(dados_ia.get('tema_especifico', 'Tema Geral'), ARQUIVO_HISTORICO_TEMAS, limite=180)
            
            termo_amz_cru = dados_ia.get('termo_busca_amazon', 'livro orcamento publico')
            termo_amz = urllib.parse.quote_plus(termo_amz_cru)
            link_amazon = f"https://www.amazon.com.br/s?k={termo_amz}"

            return {
                "titulo": dados_ia['titulo_post'],
                "corpo": dados_ia['corpo_post'],
                "hashtags": dados_ia['hashtags'],
                "link_referencia": link_origem,
                "imagem_contextual": imagem_final,
                "link_amazon": link_amazon,
                "termo_amazon_limpo": termo_amz_cru
            }
        except Exception as e:
            print(f"Erro na geração de conteúdo (Tentativa {tentativa+1}): {e}")
            time.sleep(2)
            
    return None

# ==========================================
# EXECUÇÃO NO LINKEDIN E EMAIL
# ==========================================
def publicar_e_notificar(conteudo):
    titulo_negrito = aplicar_negrito(conteudo['titulo'])
    
    texto_final = f"📌 {titulo_negrito}\n\n"
    texto_final += f"{conteudo['corpo']}\n\n"
    
    # Textos adaptados de acordo com o dia e para monetização
    texto_final += "📚 Aprofunde-se no tema e reforce sua biblioteca técnica. "
    texto_final += f"Descubra as melhores opções relacionadas através deste link de parceiro: {conteudo['link_amazon']}\n\n"
    texto_final += f"Obs.: Conteúdo curado automaticamente, pautado em neutralidade e técnica em gestão.\n" 
        
    if conteudo['link_referencia']:
        texto_final += f"🔗 Fonte Base Analisada: {conteudo['link_referencia']}\n\n"
        
    texto_final += f"{conteudo['hashtags']}"

    # Forçando a imagem contextual do Unsplash a aparecer no card
    thumbnail_array = []
    if conteudo.get('imagem_contextual'):
        thumbnail_array = [{"resolvedUrl": conteudo['imagem_contextual']}]

    # 1. O Link (Clique) do Card vai direto para a busca do produto na Amazon
    link_destino = conteudo['link_amazon']

    content_entity = {"entityLocation": link_destino} 
    if thumbnail_array:
        content_entity["thumbnails"] = thumbnail_array

    body = {
        "owner": LINKEDIN_URN_ID,
        "text": {"text": texto_final},
        "content": {
            "contentEntities": [content_entity],
            # 2. O Título visual do Card mostrará o produto recomendado
            "title": f"📦 Recomendação: {conteudo['termo_amazon_limpo']}", 
            "shareMediaCategory": "ARTICLE"
        },
        "distribution": {"linkedInDistributionTarget": {"visibleToGuest": True}}
    }
    
    headers = {
        'Authorization': f'Bearer {LINKEDIN_ACCESS_TOKEN}', 
        'Content-Type': 'application/json',
        'X-Restli-Protocol-Version': '2.0.0'
    }
    
    # Descomente a linha abaixo em ambiente de produção
    res = requests.post("https://api.linkedin.com/v2/shares", headers=headers, json=body)
    sucesso_linkedin = res.status_code in [200, 201]
    
    try:
        msg = EmailMessage()
        status = "Sucesso" if sucesso_linkedin else f"Erro API {res.status_code} - {res.text}"
        msg['Subject'] = f'Relatório Automação Curador: {conteudo["titulo"]} - {status}'
        msg['From'] = EMAIL_REMETENTE
        msg['To'] = EMAIL_DESTINO
        msg.set_content(f"O script foi executado.\n\nConteúdo Postado:\n{texto_final}\n\nStatus Response: {status}")
        
        contexto = ssl.create_default_context()
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=contexto) as smtp:
            smtp.login(EMAIL_REMETENTE, SENHA_APP_GMAIL)
            smtp.send_message(msg)
    except Exception as erro_email:
        print(f"⚠️ Aviso: Falha de conexão com Gmail: {erro_email}")
        
    print(f"Processo finalizado. Status LinkedIn: {res.status_code}")

if __name__ == "__main__":
    dias_nome = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    hoje = datetime.now().weekday()
    
    print(f"Iniciando curadoria. Hoje é {dias_nome[hoje]}.")
    conteudo = criar_conteudo_do_dia()
    
    if conteudo:
        publicar_e_notificar(conteudo)
    else:
        print("Execução encerrada sem novas publicações.")
