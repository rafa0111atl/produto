from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re
import unicodedata

def remover_acentos(txt):
    return ''.join(c for c in unicodedata.normalize('NFD', txt)
                   if unicodedata.category(c) != 'Mn')

def arredondar_valores(dados, casas_decimais=2):
    """
    Arredonda todos os valores numéricos em um dicionário ou lista de dicionários.
    
    Args:
        dados (dict | list): Dicionário ou lista de dicionários com valores numéricos.
        casas_decimais (int): Número de casas decimais para o arredondamento.
    
    Returns:
        dict | list: Dicionário ou lista com valores arredondados.
    """
    if isinstance(dados, dict):
        for key, value in dados.items():
            if isinstance(value, (int, float)):
                dados[key] = round(value, casas_decimais)
            elif isinstance(value, dict):
                dados[key] = arredondar_valores(value, casas_decimais)
            elif isinstance(value, list):
                dados[key] = [arredondar_valores(v, casas_decimais) if isinstance(v, (dict, list)) else v for v in value]
    elif isinstance(dados, list):
        dados = [arredondar_valores(item, casas_decimais) for item in dados]
    
    return dados

app = Flask(__name__)

# Função para avaliar Critério 1 de 16 - Qualidade da Página de Vendas
def qualidade_pagina(url):
    try:
        print(f"Verificando qualidade da página para URL: {url}")
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print("Página não carregou corretamente.")
            return 0

        soup = BeautifulSoup(response.text, 'html.parser')
        # Adicione aqui o código da meta descrição
        meta_description_tag = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_description_tag["content"] if meta_description_tag and "content" in meta_description_tag.attrs else ""

        # Normaliza a meta descrição para comparação
        meta_description_normalizado = normalizar_texto_para_comparacao(meta_description)


        copy_text = soup.get_text(separator=" ").lower()
        pontuacao = 0

        # Subcritérios e seus pesos ajustados
        subcriterios = {
            "responsivo_mobile": 2.30,
            "testemunhos": 2.07,
            "cores_impactantes": 1.38,
            "headline_persuasiva": 2.30,
            "video_vendas": 1.84,
            "preco_opcoes_pagamento": 1.61,
            "multiplos_botoes": 1.38,
            "bonus_ou_brindes": 1.38,
            "garantia": 2.30,
            "certificacao": 0.92,
            "contato_disponivel": 1.38,
            "faq": 1.15
        }

        # 1. Responsividade Mobile
        if soup.find("meta", {"name": "viewport"}):
            pontuacao += subcriterios["responsivo_mobile"]

        # 2. Presença de Reviews/Testemunhos
        if re.search(r"\b(testimonials|reviews)\b", copy_text):
            pontuacao += subcriterios["testemunhos"]

        # 3. Cores Impactantes e Design Atraente (CTA com cores fortes)
        botoes_cta = soup.find_all('a')
        if any('style' in btn.attrs and 'color' in btn.attrs['style'].lower() for btn in botoes_cta):
            pontuacao += subcriterios["cores_impactantes"]

        # 4. Headline e Subheadline Persuasivas
        headline = soup.find('h1')
        if headline and len(headline.text) > 5:
            pontuacao += subcriterios["headline_persuasiva"]

        # 5. Vídeo de Vendas na Página
        if soup.find("iframe") or soup.find("video"):
            pontuacao += subcriterios["video_vendas"]

        # 6. Preço e Opções de Pagamento Visíveis
        if re.search(r"\b(price|payment options|\$|purchase)\b", copy_text):
            pontuacao += subcriterios["preco_opcoes_pagamento"]

        # 7. Múltiplos Botões de Compra (CTAs)
        if len(botoes_cta) > 2:
            pontuacao += subcriterios["multiplos_botoes"]

        # 8. Ofertas de Bônus ou Brindes Extras
        if re.search(r"\b(bonus|free gift|freebie)\b", copy_text):
            pontuacao += subcriterios["bonus_ou_brindes"]

        # 9. Garantia na Página
        if re.search(r"\b(guarantee|refund|money-back)\b", copy_text):
            pontuacao += subcriterios["garantia"]

        # 10. Certificações e Selos de Confiança
        if re.search(r"\b(certified|authentic|official)\b", copy_text):
            pontuacao += subcriterios["certificacao"]

        # 11. Informações de Contato Disponíveis
        if re.search(r"\b(contact|support|help|email|phone)\b", copy_text):
            pontuacao += subcriterios["contato_disponivel"]

        # 12. Seção de FAQ ou Dúvidas Frequentes
        if re.search(r"\b(faq|questions|help)\b", copy_text):
            pontuacao += subcriterios["faq"]

        print(f"Pontuação de qualidade da página: {pontuacao} / 20")
        return round(pontuacao, 2)

    except requests.RequestException as e:
        print(f"Erro ao acessar a página: {e}")
        return 0

# Função para avaliar Critério 2 de 16 - Copywriting (clareza e persuasão)
def copywriting_pontuacao(url):
    try:
        print(f"Analisando copywriting para URL: {url}")
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print("Página não carregou corretamente.")
            return 0

        soup = BeautifulSoup(response.text, 'html.parser')
        # Adicione aqui o código da meta descrição
        # Extração de meta descrição
        meta_description_tag = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_description_tag["content"] if meta_description_tag and "content" in meta_description_tag.attrs else ""

        # Normaliza a meta descrição para comparação
        meta_description_normalizado = normalizar_texto_para_comparacao(meta_description)


        copy_text = soup.get_text(separator=" ").lower()

        # Lista de palavras persuasivas em inglês
        palavras_persuasivas = [
            "guarantee", "offer", "exclusive", "discount", "free", 
            "limited time", "best", "save", "you", "order now"
        ]
        pontuacao = 0

        # Subcritério 1: Título Persuasivo e Claro
        titulo = soup.find('title').get_text() if soup.find('title') else ""
        pontuacao += min(pontuacao_titulo(titulo), 4)

        # Subcritério 2: Exploração de Dores e Desejos
        pontuacao += min(pontuacao_dores_desejos(copy_text), 4)

        # Subcritério 3: Benefícios Explícitos
        pontuacao += min(pontuacao_beneficios_explicitios(copy_text), 1)

        # Subcritério 4: Chamada para Ação (CTA) Clara e Urgente
        pontuacao += min(pontuacao_cta(copy_text), 2)

        # Subcritério 5: Prova Social (Depoimentos Incluídos no Texto)
        pontuacao += min(prova_social(copy_text), 2)

        # Subcritério 6: Garantia de Satisfação
        pontuacao += min(pontuacao_garantia(copy_text), 2)

        # Subcritério 7: Ofertas e Escassez
        pontuacao += min(pontuacao_ofertas_escassez(copy_text), 2)

        # Subcritério 8: História ou Narrativa Relatável
        pontuacao += min(pontuacao_historia_narrativa(copy_text), 0.5)

        # Subcritério 9: Evocação de Emoções Positivas
        pontuacao += min(pontuacao_emocoes_positivas(copy_text), 3)

        # Limita a pontuação final ao peso máximo de 20
        pontuacao_final = min(pontuacao, 20)
        print(f"Pontuação de copywriting: {pontuacao_final}")
        return pontuacao_final

    except requests.RequestException as e:
        print(f"Erro ao acessar a página: {e}")
        return 0

# Subcritério 1: Título Persuasivo e Claro
# Função para pontuar o título com base em categorias específicas de palavras-chave
def pontuacao_titulo(titulo):
    categorias = {
        "Saúde e Bem-Estar": ["healthy", "wellness", "improve health", "better life", "vitality", "energy"],
        "Conforto e Praticidade": ["easy", "convenient", "comfortable", "stress-free", "no hassle", "simple"],
        "Economia e Tempo": ["save money", "affordable", "cut costs", "save time", "fast results", "efficiency"],
        "Segurança e Confiança": ["guaranteed", "secure", "trusted", "reliable", "proven", "tested"],
        "Performance e Eficiência": ["optimize", "improve performance", "high efficiency", "max results", "best results"],
        "Perda de Peso": ["weight loss", "shed pounds", "fat burning", "slim down", "get fit"],
        "Relacionamento Feminino": ["find love", "relationship advice", "improve love life", "date successfully", "attract partner"],
        "Relacionamento Masculino": ["boost confidence", "become irresistible", "relationship success", "impress her", "build connection"],
        "Espiritualidade": ["inner peace", "spiritual journey", "self-discovery", "higher purpose", "awakening"],
        "Dores (Articulações e Outras)": ["pain relief", "reduce pain", "soothe discomfort", "joint support", "back relief"],
        "Negócios e Empreendedorismo": ["grow business", "entrepreneur tips", "success strategy", "profit growth", "business growth"],
        "Finanças Pessoais e Investimentos": ["financial freedom", "save money", "wealth building", "invest wisely", "secure future"],
        "Alimentos e Bebidas": ["organic", "delicious", "healthy eating", "natural ingredients", "gourmet"],
        "Bebidas Energéticas": ["boost energy", "stay alert", "enhance focus", "natural energy", "refreshed"],
        "Jardinagem": ["green thumb", "plant care", "grow garden", "home garden", "garden success"],
        "Casa e Decoração": ["modern decor", "home improvement", "cozy home", "stylish design", "interior inspiration"],
        "Jogos": ["level up", "game tips", "top scores", "win more", "become pro"],
        "Softwares e Apps": ["user-friendly", "easy to use", "powerful tools", "boost productivity", "smart features"],
        "Esporte e Lazer": ["get active", "boost fitness", "stay fit", "sports tips", "recreational fun"],
        "Nutrição Baseada em Plantas": ["plant-based", "vegan nutrition", "healthy lifestyle", "natural diet", "eco-friendly food"],
        "Autodesenvolvimento e Autoajuda": ["self-improvement", "personal growth", "mindset change", "achieve goals", "transform life"],
        "Cuidados com Animais de Estimação": ["pet care", "happy pet", "train pet", "pet health", "animal well-being"],
        "Marketing e Vendas": ["increase sales", "boost revenue", "effective marketing", "grow audience", "market strategy"],
        "Carreira e Desenvolvimento Pessoal": ["career growth", "job success", "networking tips", "personal branding", "leadership skills"],
        "Remédios Naturais e Bem-Estar": ["natural remedies", "herbal solutions", "no side effects", "safe relief", "nature's solution"],
        "Trabalho Remoto e Produtividade": ["work from home", "productivity tips", "manage time", "efficiently remote", "home office success"],
        "Sustentabilidade e Vida Ecológica": ["eco-friendly", "sustainable living", "green solutions", "reduce waste", "earth-friendly choices"]
    }

    pontuacao = 0
    for categoria, palavras in categorias.items():
        # Pontua com base em cada palavra encontrada nas categorias
        if any(palavra in titulo.lower() for palavra in palavras):
            pontuacao += 1
        # Limita a pontuação máxima ao peso definido (4)
        if pontuacao >= 4:
            break
    
    return pontuacao


# Subcritério 2: Exploração de Dores e Desejos
def pontuacao_dores_desejos(copy_text):
    categorias = {
        "Dores": ["pain", "problem", "struggle", "frustration", "issue", "stuck", "worry", "fear", "obstacle", "difficulty"],
        "Desejos": ["dream", "aspiration", "goal", "desire", "hope", "ambition", "freedom", "happiness", "success", "passion"],
        "Alívio e Solução": ["relief", "finally", "overcome", "beat", "achieve", "freedom from", "solution", "get rid of", "fix", "resolve"],
        "saúde_bem_estar": ["heal", "cure", "relief", "soothe", "improve health", "restore", "balance", "well-being", "vitality"],
        "conforto_praticidade": ["convenience", "ease", "comfort", "simple", "quick fix", "hassle-free", "stress-free"],
        "economia_tempo": ["save time", "effortless", "quick results", "affordable", "budget-friendly", "efficient", "time-saving"],
        "seguranca_confianca": ["safe", "secure", "proven", "trusted", "risk-free", "peace of mind", "certified", "reliable"],
        "performance_eficiencia": ["effective", "enhance", "optimize", "boost", "maximize", "high performance", "gain advantage"],
        "perda_peso": ["shed pounds", "burn fat", "lose weight", "slim down", "fit", "tone", "control cravings"],
        "relacionamento_feminino": ["self-love", "empower", "confidence", "communication", "understanding", "connect", "attract"],
        "relacionamento_masculino": ["strength", "assertive", "confidence", "power", "success", "attract", "respect", "understand"],
        "espiritualidade": ["inner peace", "balance", "mindfulness", "purpose", "alignment", "higher self", "transformation"],
        "dores": ["pain relief", "discomfort", "ease pain", "reduce inflammation", "joint relief", "mobility", "support"],
        "negocios_empreendedorismo": ["growth", "scale", "strategic", "achieve goals", "maximize profits", "innovation", "entrepreneurship"],
        "financas_pessoais_investimentos": ["financial freedom", "build wealth", "investment", "save money", "passive income", "secure future"],
        "alimentos_bebidas": ["healthy", "organic", "natural", "tasty", "nutritious", "fresh", "energy-boosting"],
        "bebidas_energeticas": ["boost energy", "natural energy", "refreshing", "enhance focus", "sustain energy", "hydration"],
        "jardinagem": ["growth", "easy to maintain", "low maintenance", "nurture", "healthy plants", "natural", "green"],
        "casa_decoracao": ["comfort", "style", "cozy", "elevate space", "modern", "functional", "unique touch"],
        "jogos": ["fun", "engaging", "strategic", "interactive", "competitive", "adventurous", "thrilling"],
        "softwares_apps": ["user-friendly", "efficient", "streamlined", "intuitive", "fast", "customizable", "productivity"],
        "esporte_lazer": ["fitness", "active", "improve skills", "outdoors", "training", "recreation", "energy"],
        "nutricao_plantas": ["plant-based", "natural", "organic", "sustainable", "cruelty-free", "energy-boosting", "nutrition"],
        "autodesenvolvimento_autoajuda": ["empower", "self-growth", "mindset", "confidence", "transform", "goal setting", "resilience"],
        "cuidados_animais": ["healthy pet", "safe", "natural", "affordable care", "pet-friendly", "love your pet", "nurturing"],
        "marketing_vendas": ["increase sales", "target audience", "convert", "engage", "growth", "optimize", "strategy"],
        "carreira_desenvolvimento": ["promotion", "job satisfaction", "new skills", "leadership", "confidence", "success"],
        "remedios_naturais_bem_estar": ["herbal", "natural remedy", "holistic", "cure", "healing", "balanced life", "no side effects"],
        "trabalho_remoto_produtividade": ["remote-friendly", "productivity boost", "flexibility", "time management", "effective", "balance"],
        "sustentabilidade_vida_ecologica": ["eco-friendly", "sustainable", "reduce waste", "natural resources", "earth-conscious", "recycle"]
    }
    
    pontuacao = 0
    for palavras in categorias.values():
        for palavra in palavras:
            if palavra in copy_text.lower():
                pontuacao += 0.5
            if pontuacao >= 4:
                return pontuacao
    return pontuacao

# Subcritério 3: Benefícios Explícitos
def pontuacao_beneficios_explicitios(copy_text):
    categorias_palavras_chave = {
        "saúde_bem_estar": ["better health", "more energy", "boost immunity", "vitality", "reduce stress", "improve sleep"],
        "conforto_praticidade": ["ease of use", "simple solution", "hassle-free", "quick setup", "portable", "convenient"],
        "economia_tempo": ["save time", "cost-effective", "affordable", "budget-friendly", "quick results", "time-saving"],
        "seguranca_confianca": ["safe", "reliable", "trusted", "secure", "peace of mind", "protection"],
        "performance_eficiencia": ["high performance", "boost productivity", "more efficient", "maximize output", "increase effectiveness"],
        "perda_peso": ["lose weight", "burn fat", "get fit", "healthy body", "slim down", "tone muscles"],
        "relacionamento_feminino": ["deepen connection", "improve communication", "feel valued", "emotional support", "romantic"],
        "relacionamento_masculino": ["confidence", "powerful presence", "attractiveness", "improve intimacy", "better relationships"],
        "espiritualidade": ["inner peace", "personal growth", "mindfulness", "balance", "higher purpose", "connect spiritually"],
        "dores": ["pain relief", "reduce discomfort", "improve mobility", "joint support", "muscle relaxation"],
        "negocios_empreendedorismo": ["grow business", "maximize profit", "scalable", "innovative", "competitive edge", "business growth"],
        "financas_pessoais_investimentos": ["build wealth", "financial security", "passive income", "save money", "invest smartly", "future-proof"],
        "alimentos_bebidas": ["tasty", "healthy", "natural", "organic", "energy-boosting", "delicious"],
        "bebidas_energeticas": ["energy boost", "stay alert", "refreshing", "natural energy", "hydration"],
        "jardinagem": ["easy to grow", "low maintenance", "nurturing", "healthy plants", "natural growth"],
        "casa_decoracao": ["style upgrade", "functional", "comfortable", "modern design", "elevate space", "unique decor"],
        "jogos": ["fun", "exciting", "interactive", "challenging", "enhance skills", "entertainment"],
        "softwares_apps": ["user-friendly", "efficient", "streamlined", "intuitive", "productive", "customizable"],
        "esporte_lazer": ["fitness", "improve skills", "enhance endurance", "outdoor activity", "build strength"],
        "nutricao_plantas": ["plant-based", "natural nutrition", "cruelty-free", "boost energy", "healthy diet", "sustainable"],
        "autodesenvolvimento_autoajuda": ["self-improvement", "confidence", "goal achievement", "positive mindset", "motivation", "empowerment"],
        "cuidados_animais": ["pet health", "safe for pets", "natural care", "affordable pet care", "love your pet"],
        "marketing_vendas": ["increase sales", "target audience", "optimize conversions", "engage customers", "expand reach"],
        "carreira_desenvolvimento": ["career growth", "gain skills", "leadership", "job satisfaction", "self-confidence"],
        "remedios_naturais_bem_estar": ["herbal", "natural remedy", "no side effects", "improve health", "balanced life", "holistic care"],
        "trabalho_remoto_produtividade": ["work-life balance", "productivity boost", "flexibility", "time management", "remote-friendly"],
        "sustentabilidade_vida_ecologica": ["eco-friendly", "reduce waste", "sustainable", "reusable", "environmentally conscious"]
    }
    
    pontuacao = 0
    for categoria, palavras in categorias_palavras_chave.items():
        if any(palavra in copy_text.lower() for palavra in palavras):
            pontuacao += 0.5
        if pontuacao >= 1:
            return 1
    return pontuacao

# Subcritério 4: Chamada para Ação (CTA) Clara e Urgente
def pontuacao_cta(copy_text):
    cta_palavras_chave = {
        "Ação Imediata": ["buy now", "shop now", "order now", "act now", "get started", "sign up now", "start today"],
        "Oferta Limitada": ["limited time offer", "today only", "while supplies last", "don't miss out", "expires soon"],
        "Promoções e Descontos": ["get 50% off", "limited discount", "save today", "exclusive offer", "special deal"],
        "Exclusividade": ["only for members", "exclusive access", "only here", "only today", "available now"],
        "Apoio e Orientação": ["learn more", "find out more", "see how", "discover more"],
        "Convite para Agir": ["join us", "subscribe now", "get yours", "take advantage", "explore now"],
        "Urgência e Escassez": ["hurry", "last chance", "going fast", "don’t wait", "act fast"]
    }

    pontuacao = 0
    for categoria, palavras in cta_palavras_chave.items():
        if any(palavra in copy_text.lower() for palavra in palavras):
            pontuacao += 0.5
        if pontuacao >= 1:
            return 1  # Limita ao máximo de 1 ponto

    return pontuacao

# Subcritério 5: Prova Social (Depoimentos Incluídos no Texto)
def prova_social(copy_text):
    palavras_prova_social = [
        "testimonials", "reviews", "feedback", "opinions", "user experiences", "stories", "shared experiences",
        "rated", "5-star", "stars", "ranking", "customer satisfaction", "trusted by", "top-rated",
        "case study", "success stories", "before and after", "proven results", "results", "real stories",
        "popular choice", "most recommended", "top choice", "bestseller", "high demand", "customer favorite"
    ]
    
    pontuacao = 0
    for palavra in palavras_prova_social:
        if palavra in copy_text.lower():
            pontuacao += 0.5
        if pontuacao >= 2:
            return 2  # Limita a pontuação máxima a 2 pontos
    
    return pontuacao

# Subcritério 6: Garantia de Satisfação
def pontuacao_garantia(copy_text):
    palavras_chave_garantia = [
        "money-back guarantee", "refund", "satisfaction guarantee", "30-day guarantee", "full refund", 
        "hassle-free return", "risk-free", "no questions asked", "try risk-free", "100% satisfaction", 
        "secure purchase", "protected", "safe checkout", "encrypted", "privacy protection", "data security", 
        "secure payment", "trusted transaction", "trusted", "proven", "high-quality", "authentic", 
        "verified", "endorsed by", "backed by experts"
    ]
    
    pontuacao = 0
    for palavra in palavras_chave_garantia:
        if palavra in copy_text.lower():
            pontuacao += 0.5
        if pontuacao >= 2:
            return 2  # Limita a pontuação máxima ao peso definido (2)
    
    return pontuacao

# Subcritério 7: Ofertas e Escassez
def pontuacao_ofertas_escassez(copy_text):
    palavras_chave_ofertas_escassez = [
        "limited time", "limited time offer", "today only", "one-day sale", "special offer", "flash sale", "limited offer",
        "act now", "don’t miss out", "hurry", "ends soon", "last chance", "buy now",
        "only X left", "while supplies last", "low stock", "almost gone", "few left",
        "exclusive", "only available here", "unique offer", "VIP offer", "members only", "only for you",
        "save now", "discounted today", "instant savings", "price drop", "50% off", "huge savings",
        "wellness limited edition", "seasonal offer", "comfort deal", "limited supply for convenience",
        "weight loss special", "limited weight program", "financial plan discount", "exclusive rates today",
        "startup offer", "business deal", "mentor access limited", "eco-friendly special", "limited green supply",
        "marketing exclusive", "limited sales spots", "growth deal"
    ]
    
    pontuacao = 0
    for palavra in palavras_chave_ofertas_escassez:
        if palavra in copy_text.lower():
            pontuacao += 0.5
        if pontuacao >= 2:
            return 2  # Limita a pontuação máxima ao peso definido (2)
    
    return pontuacao

# Subcritério 8: História ou Narrativa Relatável
def pontuacao_historia_narrativa(copy_text):
    palavras_chave_narrativa = [
        "I", "my journey", "my story", "in my experience", "real-life", "first-hand", "I've been there",
        "changed my life", "transformed", "breakthrough", "overcame", "from X to Y", "reborn", "journey to success",
        "felt", "struggled with", "worried about", "passion", "hope", "dream", "fear", "joy",
        "like you", "just like us", "we all", "everyone", "common journey", "shared experience",
        "step-by-step", "from zero", "building up", "one step at a time", "growing", "learning process",
        "found peace", "wellness journey", "calm again", "eased my life", "made it simple", "effortless experience",
        "weight loss journey", "finally lost", "struggled with weight", "financial freedom", "built wealth", 
        "financial success", "startup story", "from failure to success", "entrepreneurial journey", "self-discovery", 
        "found purpose", "personal growth", "sales journey", "building a brand", "customer connection"
    ]
    
    pontuacao = 0
    for palavra in palavras_chave_narrativa:
        if palavra in copy_text.lower():
            pontuacao += 0.1
        if pontuacao >= 0.5:
            return 0.5  # Limita a pontuação máxima ao peso definido (0.5)
    
    return pontuacao

# Subcritério 9: Evocação de Emoções Positivas
def pontuacao_emocoes_positivas(copy_text):
    palavras_chave_emocoes_positivas = [
        "success", "achievement", "winner", "accomplished", "fulfilled", "happy", "joy", "peace", "well-being", 
        "satisfied", "delighted", "freedom", "independence", "control", "flexibility", "liberated", "safe", 
        "secure", "protected", "comfortable", "assured", "energy", "vibrant", "active", "healthy", "revitalized",
        "peace of mind", "serenity", "balanced", "relaxed", "calm", "ease", "effortless", "convenient", "simple", 
        "smooth", "efficient", "saves time", "cost-effective", "value", "bond", "connection", "relationship", "love",
        "support", "growth", "self-improvement", "personal development", "empowered", "happy pet", "bonding", 
        "healthy pet", "safe for pets", "career growth", "skill enhancement", "opportunity", "motivated", "eco-friendly", 
        "green", "sustainable", "positive impact", "feel better", "improve health", "reduce stress", "enhanced"
    ]
    
    pontuacao = 0
    for palavra in palavras_chave_emocoes_positivas:
        if palavra in copy_text.lower():
            pontuacao += 0.5
        if pontuacao >= 3:
            return 3  # Limita a pontuação máxima ao peso definido (3)
    
    return pontuacao

# Função para avaliar Critério 3 de 16 - Benefícios e Ofertas Especiais
def pontuacao_beneficios_ofertas_especiais(url):
    try:
        print(f"Analisando benefícios e ofertas para URL: {url}")
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print("Página não carregou corretamente.")
            return 0

        soup = BeautifulSoup(response.text, 'html.parser')
       # Extração de meta descrição
        meta_description_tag = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_description_tag["content"] if meta_description_tag and "content" in meta_description_tag.attrs else ""

        # Normaliza a meta descrição para comparação
        meta_description_normalizado = normalizar_texto_para_comparacao(meta_description)


        copy_text = soup.get_text(separator=" ").lower()
    

        # Dicionário de subcritérios e categorias
        subcriterios_palavras_chave = {
            "Explicit Benefits": {
                "health_wellness": ["energy boost", "well-being", "vitality", "reduce stress", "improve health", "immunity", "better sleep", "relaxation"],
                "comfort_convenience": ["easy to use", "hassle-free", "no setup", "quick and convenient", "low maintenance", "stress-free"],
                "savings_time": ["save money", "affordable", "cost-effective", "time-saving", "quick results", "budget-friendly"],
                "security_trust": ["safe", "trusted", "reliable", "secure", "certified", "trusted brand"],
                "performance_efficiency": ["high performance", "efficiency", "boost productivity", "optimized"],
                "weight_loss": ["lose weight", "fat burning", "slim down", "get fit", "tone muscles"],
                "female_relationship": ["improve connection", "enhance relationship", "romantic"],
                "male_relationship": ["confidence", "attractiveness", "strong connection"],
                "spirituality": ["inner peace", "mindfulness", "higher purpose", "spiritual growth"],
                "pain_relief": ["pain relief", "reduce discomfort", "improve mobility", "joint support"],
                "business_entrepreneurship": ["grow business", "maximize profit", "scalable", "innovative", "business growth"],
                "personal_finance_investments": ["build wealth", "financial security", "passive income", "save money", "smart investment"],
                "food_beverages": ["delicious", "organic", "healthy", "fresh", "natural ingredients"],
                "energy_drinks": ["energy boost", "refreshing", "sustain energy", "natural energy"],
                "gardening": ["easy to grow", "nurturing", "low maintenance", "garden success"],
                "home_decor": ["modern design", "stylish", "comfortable", "elevate space", "unique decor"],
                "gaming": ["fun", "interactive", "engaging", "entertaining"],
                "software_apps": ["user-friendly", "efficient", "streamlined", "boost productivity"],
                "sports_leisure": ["fitness", "active", "stay fit", "enhance endurance"],
                "plant_based_nutrition": ["plant-based", "cruelty-free", "eco-friendly", "healthy diet"],
                "self_improvement": ["self-improvement", "goal achievement", "positive mindset", "motivation", "empowerment"],
                "pet_care": ["pet health", "safe for pets", "natural care", "affordable pet care"],
                "marketing_sales": ["increase sales", "target audience", "convert", "growth"],
                "career_development": ["career growth", "gain skills", "leadership", "job satisfaction"],
                "natural_remedies_wellness": ["herbal remedy", "no side effects", "balanced life", "natural care"],
                "remote_work_productivity": ["work-life balance", "remote-friendly", "efficient work", "time management"],
                "sustainability_ecology": ["eco-friendly", "sustainable", "reduce waste", "earth-conscious"]
            },
            "Special Offers": {
                "general_offers": ["discount", "sale", "special offer", "limited time offer", "BOGO", "deal", "today only", "last chance", "50% off"],
                "health_wellness": ["wellness deal", "limited health offer", "immune boost sale"],
                "comfort_convenience": ["comfort deal", "limited-time convenience"],
                "savings_time": ["affordable deal", "save now", "today's discount", "instant savings"],
                "security_trust": ["trusted discount", "certified offer"],
                "performance_efficiency": ["efficiency deal", "boost performance sale"],
                "weight_loss": ["weight loss offer", "fat burning discount"],
                "business_entrepreneurship": ["business deal", "entrepreneur discount"],
                "personal_finance_investments": ["wealth-building offer", "financial security deal"],
                "home_decor": ["home decor sale", "limited-time interior deal"],
                "marketing_sales": ["increase sales discount", "conversion boost offer"],
                "sustainability_ecology": ["eco-friendly discount", "green living deal", "earth-conscious savings"]
            },
            "Free Shipping and Returns": {
                "shipping_returns": ["free shipping", "no shipping cost", "hassle-free return", "easy return", "refund policy", "30-day money-back guarantee"],
                "health_wellness": ["stress-free return", "wellness guarantee"],
                "comfort_convenience": ["no hassle return", "free delivery"],
                "business_entrepreneurship": ["risk-free trial", "no commitment return"],
                "personal_finance_investments": ["secure return policy", "money-back investment"],
                "pet_care": ["safe pet return", "hassle-free pet care return"],
                "sustainability_ecology": ["eco-friendly refund", "sustainable return policy"]
            }
        }

        pontuacao = 0

        # Avaliação dos subcritérios e categorias
        for subcriterio, categorias in subcriterios_palavras_chave.items():
            for categoria, palavras in categorias.items():
                for palavra in palavras:
                    if palavra in copy_text:
                        # Define pesos para cada subcritério
                        if subcriterio == "Explicit Benefits":
                            pontuacao += 0.4  # Máximo de 4.0 pontos
                        elif subcriterio == "Special Offers":
                            pontuacao += 0.3  # Máximo de 3.0 pontos
                        elif subcriterio == "Free Shipping and Returns":
                            pontuacao += 0.3  # Máximo de 3.0 pontos
                        print(f"Encontrado termo '{palavra}' para {subcriterio} - Incrementando pontuação para {pontuacao}")

                    # Limita a pontuação máxima para cada subcritério
                    if pontuacao >= 10:
                        print("Pontuação máxima para benefícios e ofertas atingida.")
                        return 10

        pontuacao_final = round(pontuacao, 1)
        print(f"Pontuação final de benefícios e ofertas para URL {url}: {pontuacao_final}")
        return pontuacao_final

    except requests.RequestException as e:
        print(f"Erro ao acessar a página: {e}")
        return 0

# Função para avaliar Critério 4 de 16 - Preço e Valor Percebido

from flask import Flask, render_template, request
import requests
from bs4 import BeautifulSoup
import re
from flask import Flask, render_template, request, jsonify
import unicodedata
from thefuzz import fuzz
import nltk

# Certifique-se de baixar os dados do NLTK
nltk.download('wordnet')

app = Flask(__name__)

# Ponderação dos subcritérios
SUBCRITERIA_WEIGHTS = {
    'economia_tempo': 3,
    'seguranca_confianca': 2,
    'desempenho_eficiencia': 3,
    'beneficios_valor_adicional': 1,
    'exclusividade_escassez': 1
}

# Função para normalizar texto
def normalizar_texto(texto):
    texto = texto.strip().lower()
    texto = unicodedata.normalize('NFKD', texto).encode('ASCII', 'ignore').decode('ASCII')
    texto = texto.replace('-', ' ')
    return texto

# Mapeamento das categorias do formulário para as categorias usadas nas funções
categoria_mapping = {
    'saúde e bem estar': 'health_wellness',
    'financas e negocios': 'finance_investment',
    'relacionamentos': 'relationships',
    'educacao': 'education',
    'casa e decoracao': 'home_decoration',
    'tecnologia e entretenimento': 'technology_entertainment',
    # Adicione outras categorias conforme necessário
}

# Função para correspondência aproximada
def fuzzy_match(text, keyword):
    score = fuzz.partial_ratio(normalizar_texto(keyword), normalizar_texto(text))
    return score >= 80

# Função para processar o produto
def processar_produto(index, nome_produto, url_produto, permissao_trafego_pago,
                      permissao_fundo_funil, form_data, tabela_ctr):
    produto = {}
    # Captura e normaliza a categoria do formulário
    categoria_produto_form = form_data.get(f"categoria_produto_{index}", "").strip()
    print(f"[DEBUG] Categoria recebida para produto {index}: '{categoria_produto_form}'")
    
    
    if not categoria_produto_form or categoria_produto_form.lower() == 'indefinida':
        print(f"[ERRO] Categoria não selecionada para produto {index}")
        return None

    # Normaliza a categoria
    categoria_normalizada = normalizar_texto(categoria_produto_form)
    
    # Mapeia a categoria para a chave usada nas funções
    categoria = categoria_mapping.get(categoria_normalizada, None)
    if not categoria:
        print(f"[ERRO] Categoria inválida ou não encontrada: '{categoria_produto_form}'")
        return None
    else:
        print(f"[DEBUG] Categoria mapeada para produto {index}: '{categoria}'")
        produto["categoria"] = categoria_produto_form  # Armazena a categoria original para exibição
        produto["categoria_chave"] = categoria         # Armazena a categoria mapeada para uso interno

    # Chamar a função preco_valor_percebido_pontuacao com a categoria correta
    pontuacao_preco_valor_percebido, feedback_preco_valor = preco_valor_percebido_pontuacao(url_produto, categoria)
    
    # Armazenar a pontuação e feedback no produto
    produto["pontuacao_preco_valor_percebido"] = pontuacao_preco_valor_percebido
    produto["feedback_preco_valor"] = feedback_preco_valor
    
    # Redes Sociais
    # Inicializar a pontuação total se ainda não estiver definida
    produto["pontuacao_total"] = produto.get("pontuacao_total", 0)

   


    return produto

# Função para avaliar Critério 4 de 16 - Preço e Valor Percebido
def preco_valor_percebido_pontuacao(url, categoria):
    try:
        print(f"Analisando Preço e Valor Percebido para URL: {url}")
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print("Página não carregou corretamente.")
            return 0, ["Página não carregada corretamente."]
        
        soup = BeautifulSoup(response.text, 'html.parser')
      # Extração de meta descrição
        meta_description_tag = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_description_tag["content"] if meta_description_tag and "content" in meta_description_tag.attrs else ""

        # Normaliza a meta descrição para comparação
        meta_description_normalizado = normalizar_texto_para_comparacao(meta_description)


        texto = normalizar_texto(soup.get_text())  # Normalizar o texto da página
        pontuacao = 0
        feedback = []

        # Avaliação dos subcritérios
        pont_economia_tempo, feedback_et = pontuacao_economia_tempo(texto)
        pontuacao += min(pont_economia_tempo, SUBCRITERIA_WEIGHTS['economia_tempo'])

        pont_seguranca_confianca, feedback_sc = pontuacao_seguranca_confianca(texto)
        pontuacao += min(pont_seguranca_confianca, SUBCRITERIA_WEIGHTS['seguranca_confianca'])

        pont_desempenho_eficiencia, feedback_de = pontuacao_desempenho_eficiencia(texto)
        pontuacao += min(pont_desempenho_eficiencia, SUBCRITERIA_WEIGHTS['desempenho_eficiencia'])

        pont_beneficios_valor_adicional, feedback_bva = pontuacao_beneficios_valor_adicional(texto)
        pontuacao += min(pont_beneficios_valor_adicional, SUBCRITERIA_WEIGHTS['beneficios_valor_adicional'])

        pont_exclusividade_escassez, feedback_ee = pontuacao_exclusividade_escassez(texto)
        pontuacao += min(pont_exclusividade_escassez, SUBCRITERIA_WEIGHTS['exclusividade_escassez'])


        # Limitar pontuação ao máximo permitido
        max_total = sum(SUBCRITERIA_WEIGHTS.values())
        pontuacao_final = min(pontuacao, max_total)
        print(f"Pontuação final de Preço e Valor Percebido: {pontuacao_final}")

        # Coletar feedback
        feedback.extend(feedback_et)
        feedback.extend(feedback_sc)
        feedback.extend(feedback_de)
        feedback.extend(feedback_bva)
        feedback.extend(feedback_ee)

        return pontuacao_final, feedback

    except requests.RequestException as e:
        print(f"Erro ao acessar a página: {e}")
        return 0, ["Erro ao acessar a página."]

# Ajuste nas funções de subcritérios
def fuzzy_match(text, keyword):
    # Correspondência aproximada com normalização
    score = fuzz.partial_ratio(normalizar_texto(keyword), normalizar_texto(text))
    return score >= 80

# Subcritério 1: Economia e Tempo
def pontuacao_economia_tempo(texto):
    categorias = {
        "Saúde e Bem-Estar": ["affordable cost", "health savings", "quick improvement", "proven efficacy", "reduced medical expenses"],
        "Finanças e Negócios": ["high return", "low investment", "cost-effective", "quick profit", "saves money"],
        "health_wellness": ["affordable cost", "health savings", "quick improvement", "proven efficacy", "reduced medical expenses"],
        "comfort_convenience": ["easy to use", "practical", "quick solution", "saves time", "immediate comfort", "daily use simplified"],
        "savings_time": ["accessible price", "excellent cost-benefit", "saves money", "cost reduction", "less time investment"],
        "safety_trust": ["quality guarantee", "assured protection", "safe and economical", "reliable approval", "risk-free"],
        "performance_efficiency": ["maximum efficiency", "quick performance", "effective solution", "high productivity", "fast results"],
        "weight_loss": ["easy to follow", "accelerates weight loss", "saves on diets", "reduces exercise time", "effective and quick"],
        "relationships": ["quality time", "affordable relationship", "cost-effective experiences", "quick improvement"],
        "spirituality": ["practical for daily life", "quick connection", "saves on spiritual guides", "affordable and effective"],
        "pain_relief": ["quick relief", "lower treatment cost", "effective for pain", "economic solution", "no additional expense"],
        "business_entrepreneurship": ["affordable investment", "quick return", "efficiency gain", "economic solution", "saves resources"],
        "finance_investment": ["high return", "low investment", "cost-effective", "quick profit", "saves money"],
        "food_beverage": ["economical ingredients", "quick preparation", "affordable cost", "saves on expenses", "efficient and healthy"],
        "energy_drinks": ["instant energy", "affordable price", "high yield", "economic power", "cost-effective energy"],
        "gardening": ["low cost", "quick maintenance", "easy to grow", "saves on gardening", "efficient growth"],
        "home_decoration": ["fair price", "easy installation", "saves on household expenses", "low cost", "practical for home"],
        "games": ["economical fun", "good cost-benefit", "play without spending much", "guaranteed entertainment time"],
        "software_apps": ["time-saving", "practical solution", "low cost", "affordable productivity", "quick results"],
        "sports_leisure": ["economical activity", "easy access", "reduced time", "efficient", "good cost-benefit"],
        "plant_based_nutrition": ["affordable ingredients", "economic benefits", "fair cost", "reduced preparation time", "practicality"],
        "self_development": ["affordable self-help", "quick development", "easy to implement", "rapid growth", "low investment"],
        "pet_care": ["low cost", "economic solution", "practical", "safe and accessible", "easy to use"],
        "marketing_sales": ["affordable strategy", "low implementation cost", "high return rate", "saves time on sales"],
        "career_development": ["accelerates growth", "affordable investment", "reduced time", "excellent cost-benefit", "maximum productivity"],
        "natural_remedies": ["natural and affordable", "reduces medicine costs", "easy to find", "quick effects"],
        "remote_work": ["practical tool", "economic productivity", "saves time and money", "easy to use", "low cost"],
        "sustainability_ecology": ["resource-saving", "practical and sustainable", "affordable cost", "conscious consumption", "eco-friendly"]
    }
    
    pontuacao = 0
    feedback = []

    for categoria, keywords in categorias.items():
        for palavra in keywords:
            if fuzzy_match(texto, palavra):
                pontuacao += 0.5
                feedback.append(f"Palavra-chave encontrada em '{categoria}': '{palavra}'")
                print(f"[DEBUG] Palavra-chave '{palavra}' encontrada em '{categoria}'. Pontuação atual: {pontuacao}")

    return pontuacao, feedback

# Subcritério 2: Segurança e Confiança
def pontuacao_seguranca_confianca(texto):
    categorias = {
         "health_wellness": ["quality certified", "clinically tested", "safe for health", "safety guaranteed", "trusted health solution"],
            "comfort_convenience": ["safe to use", "secure design", "comfort guarantee", "extra protection", "tested product"],
            "savings_time": ["safe investment", "return guarantee", "financially secure", "reliable and economical", "protected investment"],
            "safety_trust": ["100% safe", "protection guaranteed", "satisfaction guaranteed", "reliable product", "highly trusted"],
            "performance_efficiency": ["guaranteed effectiveness", "high reliability", "safe performance", "tested product", "maximum safety"],
            "weight_loss": ["tested for weight loss", "safe to use", "effective weight loss", "trustworthy results", "safe for diet"],
            "relationships": ["confidentiality guarantee", "emotional security", "relationship trust", "safe partner", "emotional protection"],
            "spirituality": ["safe guidance", "trusted environment", "reliable guide", "spiritual security", "secure support"],
            "pain_relief": ["safe relief", "trusted treatment", "reliable results", "safe product", "efficacy guaranteed"],
            "business_entrepreneurship": ["reliable investment", "certified product", "safety guarantee", "business trust", "secure support"],
            "finance_investment": ["guaranteed returns", "safe investment", "financial protection", "trustworthy returns", "safe and reliable"],
            "food_beverage": ["safe ingredients", "certified production", "trusted food", "quality control", "safe product"],
            "energy_drinks": ["quality certified", "food safety", "safe product", "trusted energy", "strict quality control"],
            "gardening": ["safe products", "quality control", "environmental safety", "certified source", "safe usage guaranteed"],
            "home_decoration": ["safe materials", "safety guarantee", "home protection", "quality certified", "safe and reliable"],
            "games": ["protection guarantee", "safe gameplay", "quality certified", "trusted reliability", "safe for all"],
            "software_apps": ["safe usage", "data protection", "security certified", "reliable system", "high security"],
            "sports_leisure": ["safe equipment", "safety certified", "reliable use", "protection guarantee", "safe product"],
            "plant_based_nutrition": ["safe ingredients", "vegan certified", "trusted product", "quality control", "safe for consumption"],
            "self_development": ["safe support", "trust guarantee", "reliable guidance", "emotional protection", "secure environment"],
            "pet_care": ["safe for pets", "tested and safe", "animal guarantee", "pet protection", "high safety"],
            "marketing_sales": ["secure transaction", "trusted product", "satisfaction guarantee", "reliable partnership", "return guarantee"],
            "career_development": ["safe environment", "reliable support", "quality guarantee", "secure growth", "process reliability"],
            "natural_remedies": ["safe product", "quality guarantee", "tested and natural", "safe usage", "natural trust"],
            "remote_work_productivity": ["secure system", "protection guarantee", "data protected", "reliable environment", "secure productivity"],
            "sustainability_ecology": ["environmental safety", "sustainable and safe", "eco protection", "certified green", "safe product"]
        }

    pontuacao = 0
    feedback = []

    for categoria, keywords in categorias.items():
        for palavra in keywords:
            if fuzzy_match(texto, palavra):
                pontuacao += 0.5
                feedback.append(f"Palavra-chave encontrada em '{categoria}': '{palavra}'")
                print(f"[DEBUG] Palavra-chave '{palavra}' encontrada em '{categoria}'. Pontuação atual: {pontuacao}")

    return pontuacao, feedback

# Subcritério 3: Desempenho e Eficiência
def pontuacao_desempenho_eficiencia(texto):
    categorias = {
        "health_wellness": ["high performance", "proven results", "effective solution", "health boost", "consistent performance"],
        "comfort_convenience": ["optimized for convenience", "effortless", "time-efficient", "consistent results", "designed for performance"],
        "savings_time": ["time-saving", "cost-efficient", "value-packed", "maximum efficiency", "optimized resources"],
        "safety_trust": ["reliable performance", "trusted solution", "safe and efficient", "proven reliability", "consistent effectiveness"],
        "performance_efficiency": ["highly efficient", "top performance", "effective use", "powerful results", "maximized efficiency"],
        "weight_loss": ["quick results", "efficient weight loss", "accelerated fat burn", "sustained results", "optimized for fitness"],
        "relationships": ["effective relationship building", "enhanced connection", "consistent improvement", "relationship boost", "strong impact"],
        "spirituality": ["spiritual enhancement", "consistent guidance", "efficient practices", "enhances focus", "boosts connection"],
        "pain_relief": ["effective relief", "quick pain reduction", "efficient treatment", "long-lasting results", "targeted performance"],
        "business_entrepreneurship": ["high ROI", "scalable efficiency", "business optimization", "enhanced productivity", "performance boost"],
        "finance_investment": ["effective investment", "high returns", "optimized for profit", "consistent earnings", "boosts financial results"],
        "food_beverage": ["nutrient-dense", "optimized nutrition", "highly effective", "quick energy", "power-packed ingredients"],
        "energy_drinks": ["boosts energy", "sustained energy", "quick acting", "high performance drink", "efficient energy supply"],
        "gardening": ["fast growth", "high yield", "optimized for nature", "plant performance", "efficient maintenance"],
        "home_decoration": ["easy maintenance", "long-lasting", "optimized for home", "high efficiency", "durable design"],
        "games": ["high score potential", "optimized gameplay", "boosts performance", "quick progress", "enhances skills"],
        "software_apps": ["user efficiency", "optimized performance", "high productivity", "quick processing", "reliable software"],
        "sports_leisure": ["boosts endurance", "enhanced performance", "quick recovery", "sustains energy", "optimizes fitness"],
        "plant_based_nutrition": ["efficient absorption", "high in nutrients", "energy-packed", "enhances health", "natural performance boost"],
        "self_development": ["rapid growth", "optimized learning", "high impact", "consistent improvement", "empowers personal development"],
        "pet_care": ["supports pet health", "consistent care", "optimized for pet needs", "boosts well-being", "effective solution"],
        "marketing_sales": ["high conversion rate", "efficient strategy", "boosts engagement", "optimized for sales", "effective outreach"],
        "career_development": ["fast track", "skill boost", "optimized career growth", "enhances productivity", "quick impact"],
        "natural_remedies": ["efficient remedy", "quick relief", "consistent effectiveness", "herbal potency", "natural performance"],
        "remote_work_productivity": ["boosts productivity", "time-efficient", "highly reliable", "quick setup", "optimized workflow"],
        "sustainability_ecology": ["eco-efficient", "maximizes sustainability", "long-lasting impact", "optimized for the planet", "resource-saving"]
    }

    pontuacao = 0
    feedback = []

    for categoria, keywords in categorias.items():
        for palavra in keywords:
            if fuzzy_match(texto, palavra):
                pontuacao += 0.5
                feedback.append(f"Palavra-chave encontrada em '{categoria}': '{palavra}'")
                print(f"[DEBUG] Palavra-chave '{palavra}' encontrada em '{categoria}'. Pontuação atual: {pontuacao}")

    return pontuacao, feedback


# Subcritério 4: Benefícios e Valor Adicional
def pontuacao_beneficios_valor_adicional(texto):
    categorias = {
        "health_wellness": ["health benefits", "well-being boost", "extra support", "immune enhancement", "additional wellness"],
        "comfort_convenience": ["added comfort", "extra convenience", "easy access", "immediate support", "enhanced usability"],
        "savings_time": ["cost-effective benefits", "time-saving extras", "value for money", "additional savings", "budget-friendly"],
        "safety_trust": ["guaranteed benefits", "extra protection", "added security", "trusted value", "enhanced trust"],
        "performance_efficiency": ["performance boost", "additional efficiency", "improved functionality", "extra power", "enhanced effectiveness"],
        "weight_loss": ["boosted weight loss", "additional fitness benefits", "accelerated results", "extra support for diet", "effective fat burn"],
        "relationships": ["relationship enhancement", "extra connection", "added bonding", "improved interaction", "value for relationships"],
        "spirituality": ["spiritual benefits", "extra guidance", "enhanced connection", "additional growth", "extra focus"],
        "pain_relief": ["pain relief benefits", "extra comfort", "additional relief", "long-lasting effects", "improved recovery"],
        "business_entrepreneurship": ["extra ROI", "additional revenue", "business growth benefits", "enhanced scalability", "value-added services"],
        "finance_investment": ["financial benefits", "extra income", "added profit", "increased earnings", "value for investment"],
        "food_beverage": ["enhanced flavor", "additional nutrients", "added health benefits", "extra energy", "value in nutrition"],
        "energy_drinks": ["energy boost", "extra stamina", "sustained energy", "enhanced focus", "additional vitality"],
        "gardening": ["growth enhancement", "extra yield", "value for gardening", "improved growth", "added natural benefits"],
        "home_decoration": ["extra durability", "added style", "long-lasting value", "enhanced comfort", "improved aesthetics"],
        "games": ["bonus features", "extra levels", "enhanced gameplay", "improved experience", "value for gamers"],
        "software_apps": ["additional functionality", "extra tools", "enhanced productivity", "improved efficiency", "value-added software"],
        "sports_leisure": ["performance benefits", "extra endurance", "added strength", "enhanced fitness", "improved stamina"],
        "plant_based_nutrition": ["extra nutrients", "enhanced health", "added vitamins", "value-packed", "additional benefits for wellness"],
        "self_development": ["personal growth benefits", "extra motivation", "enhanced learning", "added empowerment", "value in self-help"],
        "pet_care": ["extra pet care", "added safety", "improved health for pets", "enhanced well-being", "additional benefits for pets"],
        "marketing_sales": ["added reach", "extra engagement", "enhanced sales potential", "value for marketing", "increased conversions"],
        "career_development": ["career growth benefits", "extra learning", "enhanced productivity", "additional skills", "value in development"],
        "natural_remedies": ["extra natural benefits", "enhanced healing", "added relief", "increased effectiveness", "value in natural care"],
        "remote_work_productivity": ["additional tools", "extra efficiency", "enhanced productivity", "value-added features", "improved workflow"],
        "sustainability_ecology": ["eco benefits", "added sustainability", "enhanced environmental impact", "extra value for the planet", "resource-friendly"]
    }

    pontuacao = 0
    feedback = []

    for categoria, keywords in categorias.items():
        for palavra in keywords:
            if fuzzy_match(texto, palavra):
                pontuacao += 0.5
                feedback.append(f"Palavra-chave encontrada em '{categoria}': '{palavra}'")
                print(f"[DEBUG] Palavra-chave '{palavra}' encontrada em '{categoria}'. Pontuação atual: {pontuacao}")

    return pontuacao, feedback


# Subcritério 5: Exclusividade e Escassez
def pontuacao_exclusividade_escassez(texto):
    categorias = {
        "health_wellness": ["limited health offer", "exclusive wellness", "rare benefits", "only available here", "unique health boost"],
        "comfort_convenience": ["limited edition comfort", "exclusive convenience", "rare features", "unique access", "one-time offer"],
        "savings_time": ["limited time savings", "exclusive discount", "rare opportunity", "only for a short time", "one-time value"],
        "safety_trust": ["trusted exclusive", "limited trust offer", "rare security benefits", "exclusive safety assurance", "unique safety"],
        "performance_efficiency": ["highly exclusive performance", "limited efficiency boost", "one-of-a-kind results", "rarely available", "exclusive effectiveness"],
        "weight_loss": ["exclusive weight loss plan", "limited access", "only available here", "unique fat-burning offer", "rare diet solution"],
        "relationships": ["exclusive relationship benefits", "limited connection offer", "rare bonding experience", "unique relationship boost", "one-time access"],
        "spirituality": ["exclusive spiritual guidance", "rare enlightenment", "unique connection", "limited spiritual boost", "one-of-a-kind insight"],
        "pain_relief": ["exclusive pain relief", "rare solution", "only available here", "unique treatment", "limited time relief"],
        "business_entrepreneurship": ["exclusive business growth", "limited success offer", "rare opportunity", "only for entrepreneurs", "unique scalability"],
        "finance_investment": ["exclusive financial benefit", "limited investment opportunity", "rare returns", "unique profit potential", "one-time financial boost"],
        "food_beverage": ["limited edition flavor", "exclusive ingredients", "rarely available", "unique recipe", "one-time taste"],
        "energy_drinks": ["exclusive energy boost", "limited formula", "rare drink", "unique stamina solution", "one-of-a-kind energy"],
        "gardening": ["rare plant variety", "limited growth booster", "exclusive gardening offer", "unique plant enhancement", "one-time yield"],
        "home_decoration": ["exclusive decor", "limited home style", "rare design", "unique piece", "one-of-a-kind home improvement"],
        "games": ["exclusive game level", "limited edition", "rare feature", "unique gameplay", "one-time bonus"],
        "software_apps": ["exclusive software", "limited functionality", "rare app feature", "unique tools", "one-time access"],
        "sports_leisure": ["limited fitness access", "exclusive sports offer", "rare equipment", "unique endurance solution", "one-time activity"],
        "plant_based_nutrition": ["exclusive nutrients", "rare ingredients", "limited plant-based benefits", "unique diet offer", "one-time boost"],
        "self_development": ["exclusive growth opportunity", "limited self-improvement", "rare coaching", "unique learning path", "one-time development"],
        "pet_care": ["exclusive pet care", "limited availability", "rare health benefits for pets", "unique pet product", "one-time solution"],
        "marketing_sales": ["exclusive marketing strategy", "limited campaign", "rare sales offer", "unique engagement", "one-time access"],
        "career_development": ["exclusive career growth", "limited skill set", "rare opportunity", "unique career boost", "one-of-a-kind training"],
        "natural_remedies": ["exclusive natural remedy", "rare herbal solution", "limited edition wellness", "unique benefits", "one-time natural care"],
        "remote_work_productivity": ["exclusive productivity tool", "limited access", "rare work solution", "unique workflow", "one-time productivity boost"],
        "sustainability_ecology": ["exclusive eco benefit", "limited green resource", "rare sustainable product", "unique environmental impact", "one-of-a-kind sustainability"]
    }

    pontuacao = 0
    feedback = []

    for categoria, keywords in categorias.items():
        for palavra in keywords:
            if fuzzy_match(texto, palavra):
                pontuacao += 0.5
                feedback.append(f"Palavra-chave encontrada em '{categoria}': '{palavra}'")
                print(f"[DEBUG] Palavra-chave '{palavra}' encontrada em '{categoria}'. Pontuação atual: {pontuacao}")

    return pontuacao, feedback



# Função para avaliar Critério 5 de 16 - Faixa de Preços
def faixa_precos_pontuacao(url):
    try:
        print(f"Analisando Faixa de Preços para URL: {url}")
        response = requests.get(url, timeout=5)
        if response.status_code != 200:
            print("Página não carregou corretamente.")
            return 0

        soup = BeautifulSoup(response.text, 'html.parser')
       # Extração de meta descrição
        meta_description_tag = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_description_tag["content"] if meta_description_tag and "content" in meta_description_tag.attrs else ""

        # Normaliza a meta descrição para comparação
        meta_description_normalizado = normalizar_texto_para_comparacao(meta_description)


        copy_text = soup.get_text(separator=" ").lower()

        # Dicionário de subcritérios e palavras-chave com pesos
        subcriterios_palavras_chave = {
            "Garantias de Reembolso": {
                "palavras": [
                    "100% money back guarantee", "satisfaction guarantee", "no questions asked refund",
                    "risk-free offer", "refund guarantee", "60-day money back guarantee",
                    "30 days guarantee", "180 days guarantee", "money back assurance"
                ],
                "peso": 3.0
            },
            "Ofertas Especiais e Promoções": {
                "palavras": [
                    "special introductory offer", "limited time offer", "exclusive pricing",
                    "discounted price", "special pricing available", "introductory price",
                    "limited-time pricing", "flash sale", "exclusive deal", "today only offer",
                    "special savings"
                ],
                "peso": 2.5
            },
            "Pacotes e Economias": {
                "palavras": [
                    "bundle offer", "value package", "money-saving package", "economy pack",
                    "discounted bundle", "package deal", "cost-effective pack", "value combo"
                ],
                "peso": 1.5
            },
            "Frete Grátis e Ofertas de Envio": {
                "palavras": [
                    "free shipping", "package gets free shipping", "shipping included",
                    "no shipping fees", "free delivery", "complimentary shipping"
                ],
                "peso": 1.5
            },
            "Incentivos de Compra": {
                "palavras": [
                    "order now for special price", "limited stock", "while supplies last",
                    "first time buyer discount", "order today, save more", "best price available"
                ],
                "peso": 1.5
            }
        }

        pontuacao = 0

        # Avaliação dos subcritérios e palavras-chave
        for subcriterio, dados in subcriterios_palavras_chave.items():
            encontrados = sum(1 for palavra in dados["palavras"] if palavra in copy_text)
            if encontrados > 0:
                pontuacao += dados["peso"]
                print(f"Encontrado '{subcriterio}' - Incrementando pontuação em {dados['peso']} para total de {pontuacao}")

        # Limita a pontuação final ao peso máximo de 10
        pontuacao_final = min(pontuacao, 10)
        print(f"Pontuação final de Faixa de Preços para URL {url}: {pontuacao_final}")
        return pontuacao_final

    except requests.RequestException as e:
        print(f"Erro ao acessar a página: {e}")
        return 0


# Função para avaliar Critério 6 de 16 - Volume de Buscas e Interesses - API GOOGLE TRENDS
from pytrends.request import TrendReq
from bs4 import BeautifulSoup
import requests
from functools import lru_cache

@lru_cache(maxsize=10)
def fetch_url_content(url):
    response = requests.get(url)
    return response.text if response.status_code == 200 else None

# Configura a conexão com o Google Trends para os EUA
pytrends = TrendReq(hl='en-US', tz=0, timeout=(10, 25))  # 10 segundos para conexão, 25 segundos para leitura

# Função para extrair o nome do produto da URL da página de vendas
def extrair_nome_produto(url):
    try:
        response = fetch_url_content(url)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
           # Extração de meta descrição
            meta_description_tag = soup.find("meta", attrs={"name": "description"})
            meta_description = meta_description_tag["content"] if meta_description_tag and "content" in meta_description_tag.attrs else ""

            # Normaliza a meta descrição para comparação
            meta_description_normalizado = normalizar_texto_para_comparacao(meta_description)

            
            # Tenta obter o título do produto na tag <title> ou <h1>
            titulo = soup.find('title').get_text() if soup.find('title') else None
            h1 = soup.find('h1').get_text() if soup.find('h1') else None
            
            # Se o título estiver presente, usa ele como o nome do produto
            nome_produto = h1 if h1 else titulo
            if nome_produto:
                return nome_produto.strip()
            else:
                print("Nome do produto não encontrado na página.")
                return None
        else:
            print(f"Erro ao acessar a página. Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"Erro ao extrair nome do produto: {e}")
        return None

# Função para obter o interesse médio do produto no Google Trends
def obter_interesse_produto(termo_busca):
    try:
        # Define o termo de busca e o período para os EUA
        termos_busca = [termo_busca]
        pytrends.build_payload(termos_busca, cat=0, timeframe='today 12-m', geo='US')  # Exemplo para EUA e últimos 12 meses

        # Obtenha dados de interesse ao longo do tempo
        interesse_tempo = pytrends.interest_over_time()

        # Verifica se o termo está nos dados e calcula o interesse médio
        if termo_busca in interesse_tempo.columns:
            interesse_medio = interesse_tempo[termo_busca].mean() # Calcula a média de interesse para o termo
            print(f"Interesse médio para '{termo_busca}': {interesse_medio}")
            return interesse_medio
        else:
            print(f"Termo '{termo_busca}' não encontrado nos dados.")
            return 0
    except Exception as e:
        print(f"Erro ao obter dados do Google Trends: {e}")
        return 0

# Função ajustada para calcular o volume de busca considerando o nome junto e separado
def calcular_pontuacao_volume_busca(nome_do_produto):
    pytrends = TrendReq(hl='en-US', tz=360)
    
    # Define os períodos
    periodos = {
        "12 meses": 'today 12-m',
        "6 meses": 'today 6-m',
        "3 meses": 'today 3-m',
        "30 dias": 'now 1-m'
    }
    
    # Pesos dos períodos
    pesos = {
        "12 meses": 0.3,
        "6 meses": 0.3,
        "3 meses": 0.2,
        "30 dias": 0.2
    }

    def calcular_interesse_ponderado(termo):
        """Calcula a média ponderada do interesse para um termo de busca específico."""
        pontuacao_total = 0
        try:
            for periodo, timeframe in periodos.items():
                pytrends.build_payload([termo], timeframe=timeframe, geo='US')
                interesse_tempo = pytrends.interest_over_time()
                
                if not interesse_tempo.empty and termo in interesse_tempo.columns:
                    interesse_medio = interesse_tempo[termo].mean()
                    pontuacao_periodo = interesse_medio * pesos[periodo]
                    pontuacao_total += pontuacao_periodo
                else:
                    print(f"Dados indisponíveis para o período {periodo} e termo '{termo}'.")
        except Exception as e:
            print(f"Erro ao calcular interesse ponderado para o termo '{termo}': {e}")
        return pontuacao_total

    # Calcula o interesse para o nome junto e separado
    nome_com_espaco = nome_do_produto
    nome_sem_espaco = nome_do_produto.replace(" ", "")
    pontuacao_com_espaco = calcular_interesse_ponderado(nome_com_espaco)
    pontuacao_sem_espaco = calcular_interesse_ponderado(nome_sem_espaco)

    # Retorna a pontuação mais alta entre as duas variações
    pontuacao_final = max(pontuacao_com_espaco, pontuacao_sem_espaco)
    return round(pontuacao_final, 1)


# Ativa o modo de teste para evitar requisições ao Google
modo_teste = True  # Mude para False para usar as requisições reais





# Função para avaliar Critério 7 de 16 - Sazonalidade - API GOOGLE TRENDS

# (tirar o comentario) from pytrends.request import TrendReq
import calendar

# Configura conexão com o Google Trends
pytrends = TrendReq(hl='en-US', tz=360)

# Lista dos meses em português
meses_portugues = [
    "", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
    "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
]

def analisar_sazonalidade(nome_do_produto):
    try:
        # Função para tentar coletar dados do Google Trends
        def buscar_trends(nome):
            pytrends.build_payload([nome], timeframe='today 12-m', geo='US')
            return pytrends.interest_over_time()

        # Primeiro, tenta com o nome original
        interesse_tempo = buscar_trends(nome_do_produto)

        # Se não encontrar dados, tenta sem espaços
        if interesse_tempo.empty or nome_do_produto not in interesse_tempo.columns:
            nome_sem_espacos = nome_do_produto.replace(" ", "")
            interesse_tempo = buscar_trends(nome_sem_espacos)
            if interesse_tempo.empty or nome_sem_espacos not in interesse_tempo.columns:
                return 0, "Nenhum dado de sazonalidade encontrado para o produto."

            nome_do_produto = nome_sem_espacos  # Atualiza para a versão encontrada

        # Calcula média por mês para identificar picos e quedas
        interesse_tempo['month'] = interesse_tempo.index.month
        media_por_mes = interesse_tempo.groupby('month')[nome_do_produto].mean()

        # Define limiares para alta e baixa com base na média e desvio padrão
        media_geral = media_por_mes.mean()
        desvio_padrao = media_por_mes.std()
        meses_alta = media_por_mes[media_por_mes > media_geral + desvio_padrao].index.tolist()
        meses_baixa = media_por_mes[media_por_mes < media_geral - desvio_padrao].index.tolist()

        # Identifica os últimos 3 e penúltimos 3 meses para ver tendência recente
        ultimos_3_meses = interesse_tempo[nome_do_produto].iloc[-3:].mean()
        penultimos_3_meses = interesse_tempo[nome_do_produto].iloc[-6:-3].mean()

        # Criação das mensagens de descrição
        if ultimos_3_meses > penultimos_3_meses:
            # Produto em alta
            meses_restantes = [mes for mes in meses_alta if mes > interesse_tempo.index[-1].month]
            if meses_restantes:
                meses_em_alta = ', '.join([meses_portugues[mes] for mes in meses_restantes[:2]])
                descricao = f"Este produto está em alta e deve continuar por mais {len(meses_restantes)} meses ({meses_em_alta})."
                pontuacao_sazonalidade = 2  # Alta sazonalidade
            elif not meses_restantes and meses_alta:
                descricao = "Este produto está em alta e deve continuar assim por algum tempo."
                pontuacao_sazonalidade = 2
            else:
                descricao = "Este produto está em alta, mas sem previsão de alta nos próximos meses."
                pontuacao_sazonalidade = 2
        elif ultimos_3_meses < penultimos_3_meses:
            # Produto em baixa
            if meses_alta:
                proximos_meses_alta = ', '.join([meses_portugues[mes] for mes in meses_alta[:2]])
                descricao = f"Este produto está em baixa no momento, mas tende a subir nos meses: {proximos_meses_alta}."
                pontuacao_sazonalidade = 0.5  # Baixa sazonalidade
            else:
                descricao = "Este produto está em baixa e deve continuar com interesse reduzido nos próximos meses."
                pontuacao_sazonalidade = 0.5
        else:
            descricao = "O interesse pelo produto está estável, sem grandes variações sazonais esperadas."
            pontuacao_sazonalidade = 1  # Interesse estável

        # Criação da mensagem detalhada de histórico
        meses_alta_nomes = [meses_portugues[mes] for mes in meses_alta]
        meses_baixa_nomes = [meses_portugues[mes] for mes in meses_baixa]
        descricao_detalhada = (
            f"Baseado nos últimos 12 meses, os meses de alta foram: {', '.join(meses_alta_nomes) if meses_alta else 'Nenhum mês específico'}. "
            f"Os meses de baixa foram: {', '.join(meses_baixa_nomes) if meses_baixa else 'Nenhum mês específico'}."
        )

        # Combina as mensagens para o usuário final
        descricao_final = f"{descricao} {descricao_detalhada}"
        
        return pontuacao_sazonalidade, descricao_final

    except Exception as e:
        return 0, f"Erro ao analisar sazonalidade: {e}"



# Função para avaliar Critério 8 de 16 - Permissão para Tráfego Pago
# Esse criterio vai ficar manual. O usuario usa dropbox para dizer ao algoritmo se o produto PODE ou NÃO tráfego Pago.
# O mesmo vai acontecer com SE produto PODE ou NÃO fundo de funil. O usuário vai colocar manual SIM ou NÃO no dropbox.




# Função para avaliar Critério 9 de 16 - SEO e PALAVRAS-CHAVE
# Função para calcular pontuação de SEO e palavras-chave de acordo com fundo e meio de funil.
# Está sendo calculado, Palavra-chave, Volume e CPC. Além disso, a intenção da Palavra-chave (transacional, informativa ou conscientização)

from flask import Flask, render_template, request, jsonify
import re
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

# Listas de palavras por categoria de intenção
PALAVRAS_TRANSACIONAL = ["buy", "purchase", "discount", "offer", "promotion", "where to buy", "price of",
                         "sale", "free shipping", "buy online", "order", "get now", "buy cheap",
                         "promo code", "buy with discount", "buy direct", "pay", "request", "place order"]
PALAVRAS_INFORMACIONAL = ["how it works", "which is better", "benefits of", "effects of", "advantages", "disadvantages",
                          "how to use", "recommendations", "comparisons", "analysis of", "guide to", "tutorial",
                          "best options", "how to choose", "tips for", "what's the difference", "reviews", "product review"]
PALAVRAS_CONSCIENTIZACAO = ["what is", "how to", "tips on", "guide to", "introduction to", "importance of",
                            "benefits of", "reasons for", "meaning of", "how it helps", "ways to", "basics of",
                            "information about", "learn more", "understand", "fundamentals", "overview of",
                            "how to start", "for beginners"]

# Pesos para cada categoria
PESO_TRANSACIONAL = 2.5
PESO_INFORMACIONAL = 1.0
PESO_CONSCIENTIZACAO = 0.3
PESO_NEUTRO = 0.7
PESO_INTENCAO_PALAVRA = 3.0
PESO_VOLUME_BUSCA = 4.0
PESO_CONCORRENCIA_CPC = 5.0

# Função para identificar a intenção da palavra-chave (primeira definição)
def identificar_intencao_sem_permissao(palavra_chave, nome_do_produto):
    palavra_chave = palavra_chave.lower()
    
    # Verifica se o nome do produto está na palavra-chave e aplica um peso alto
    if nome_do_produto and nome_do_produto.lower() in palavra_chave:
        return 'produto_fundo_funil', PESO_TRANSACIONAL  # Peso transacional para fundo de funil com nome do produto

    # Verifica categorias padrão
    for termo in PALAVRAS_TRANSACIONAL:
        if termo in palavra_chave:
            return 'transacional', PESO_TRANSACIONAL
    for termo in PALAVRAS_INFORMACIONAL:
        if termo in palavra_chave:
            return 'informacional', PESO_INFORMACIONAL
    for termo in PALAVRAS_CONSCIENTIZACAO:
        if termo in palavra_chave:
            return 'conscientizacao', PESO_CONSCIENTIZACAO
    return 'neutro', PESO_NEUTRO  # Peso padrão para palavras sem intenção específica

# Função para identificar a intenção da palavra-chave (segunda definição)
def identificar_intencao(palavra_chave, nome_do_produto, permissao_fundo_funil):
    palavra_chave = palavra_chave.lower()
    
    # Verifica se o nome do produto está na palavra-chave e se fundo de funil é permitido
    if permissao_fundo_funil and nome_do_produto and nome_do_produto.lower() in palavra_chave:
        return 'produto_fundo_funil', PESO_TRANSACIONAL  # Peso alto para fundo de funil com nome do produto
    
    # Verifica categorias padrão
    for termo in PALAVRAS_TRANSACIONAL:
        if termo in palavra_chave:
            return 'transacional', PESO_TRANSACIONAL if permissao_fundo_funil else PESO_NEUTRO  # Ajusta para neutro se fundo de funil não é permitido
    for termo in PALAVRAS_INFORMACIONAL:
        if termo in palavra_chave:
            return 'informacional', PESO_INFORMACIONAL
    for termo in PALAVRAS_CONSCIENTIZACAO:
        if termo in palavra_chave:
            return 'conscientizacao', PESO_CONSCIENTIZACAO
    return 'neutro', PESO_NEUTRO

# Função para normalizar o texto para comparação
def normalizar_texto_para_comparacao(texto):
    return re.sub(r"\s+", "", texto.lower().strip())

# Lista de termos para cada categoria
TERMS_BY_CATEGORY = {
    "Health and Wellness": ["well-being", "mental health", "balance", "self-care", "healthy lifestyle", "physical health", "quality of life"],
    "Comfort and Convenience": ["comfort", "convenience", "ergonomics", "practicality", "easy-to-use"],
    "Saving Time and Money": ["time-saving", "efficiency", "productivity", "time gain", "organization"],
    "Security and Trust": ["safe", "trusted", "protection", "guarantee", "fail-proof"],
    "Performance and Efficiency": ["high performance", "efficiency", "quick results", "productivity"],
    "Weight Loss": ["weight loss", "lose weight", "fat reduction", "metabolism boost"],
    "Female Relationships": ["relationship", "dating", "romance", "intimacy", "connection"],
    "Male Relationships": ["relationship", "dating", "confidence", "charisma"],
    "Spirituality": ["spiritual", "mindfulness", "meditation", "inner peace"],
    "Pain Relief": ["pain relief", "joint pain", "headache", "arthritis"],
    "Business and Entrepreneurship": ["entrepreneurship", "startups", "business growth"],
    "Personal Finance and Investments": ["personal finance", "investment", "budgeting"],
    "Food and Beverages": ["recipes", "snacks", "nutrition", "meals"],
    "Energy Drinks": ["energy boost", "caffeine", "stamina"],
    "Gardening": ["planting", "seeds", "gardening tools"],
    "Home and Decor": ["home decor", "interior design", "furniture"],
    "Games": ["gaming", "video games", "entertainment"],
    "Software and Apps": ["software", "application", "digital tool"],
    "Sports and Leisure": ["sports", "outdoor", "fitness"],
    "Plant-Based Nutrition": ["plant-based", "vegan", "organic"],
    "Self-Development and Self-Help": ["self-improvement", "motivation", "emotional health"],
    "Pet Care": ["pet care", "nutrition for pets", "vet recommended"],
    "Marketing and Sales": ["marketing", "sales strategies", "conversion rate"],
    "Career and Personal Development": ["career growth", "professional development"],
    "Natural Remedies and Wellness": ["natural remedies", "herbal medicine", "healing"],
    "Remote Work and Productivity": ["remote work", "collaboration", "virtual meetings"],
    "Sustainability and Eco-Friendly Living": ["sustainability", "eco-friendly", "recycling"],
}

# Função para verificar SEO básico
import requests
from bs4 import BeautifulSoup

# Função para verificar SEO básico com logs de depuração adicionais
def analisar_seo_basico(url, product_name, category):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        # Normaliza o nome do produto
        nome_normalizado = normalizar_texto_para_comparacao(product_name)
        print(f"[DEBUG] Nome do Produto (Original): {product_name}")
        print(f"[DEBUG] Nome do Produto (Normalizado): {nome_normalizado}")

        # Extrai o conteúdo de título, meta descrição, headers e parágrafos
        title = soup.title.string if soup.title else ""
        meta_description = soup.find("meta", attrs={"name": "description"})
        meta_description = meta_description["content"] if meta_description else ""
        headers = [h.get_text() for h in soup.find_all(["h1", "h2", "h1.title", "h2.title"])]
        paragraphs = [p.get_text() for p in soup.find_all('p')]

        # Normaliza conteúdo para comparação
        title_normalizado = normalizar_texto_para_comparacao(title)
        meta_description_normalizado = normalizar_texto_para_comparacao(meta_description)
        headers_normalizados = [normalizar_texto_para_comparacao(header) for header in headers]
        paragraphs_normalizados = [normalizar_texto_para_comparacao(p) for p in paragraphs]

        print(f"[DEBUG] Título Normalizado: {title_normalizado}")
        print(f"[DEBUG] Meta Descrição Normalizada: {meta_description_normalizado}")
        print(f"[DEBUG] Headers Normalizados: {headers_normalizados}")
        # Comentado para evitar logs muito extensos
        # print(f"[DEBUG] Parágrafos Normalizados: {paragraphs_normalizados}")

        # Lista de palavras relevantes da categoria
        palavras_categoria = TERMS_BY_CATEGORY.get(category, [])

        # Verifica presença do nome do produto no título
        pontuacao_nome_produto = 0
        if nome_normalizado in title_normalizado:
            pontuacao_nome_produto += 1  # Alterado de 2 para 1
            print("[DEBUG] Nome do produto encontrado no título. Incrementando 1 ponto.")
        else:
            print("[DEBUG] Nome do produto NÃO encontrado no título.")

        # Verifica presença do nome do produto na meta descrição
        if nome_normalizado in meta_description_normalizado:
            pontuacao_nome_produto += 1.5  # Mantido como 1.5
            print("[DEBUG] Nome do produto encontrado na meta descrição. Incrementando 1.5 pontos.")
        else:
            print("[DEBUG] Nome do produto NÃO encontrado na meta descrição.")

        # Verifica presença do nome do produto nos cabeçalhos
        header_score = sum(1 for header in headers_normalizados if nome_normalizado in header)
        pontuacao_nome_produto += header_score  # Mantido
        print(f"[DEBUG] Nome do produto encontrado em {header_score} cabeçalhos. Incrementando {header_score} pontos.")

        # Verifica presença do nome do produto nos parágrafos (limitado a 3 pontos)
        paragraph_matches = sum(1 for paragraph in paragraphs_normalizados if nome_normalizado in paragraph)
        paragraph_score = min(paragraph_matches * 0.15, 3)  # Alterado de 0.5 para 1.5
        pontuacao_nome_produto += paragraph_score
        print(f"[DEBUG] Nome do produto encontrado em {paragraph_matches} parágrafos. Incrementando {paragraph_score} pontos (máximo 3 pontos).")

        print(f"[DEBUG] Pontuação Nome do Produto Total: {pontuacao_nome_produto}")


        # Calcula pontuação de SEO básico
        pontuacao_seo_basico = round(pontuacao_nome_produto, 2)
        print(f"[DEBUG] Pontuação SEO Básico Final: {pontuacao_seo_basico}")

        return pontuacao_seo_basico
    except Exception as e:
        print(f"[ERRO] Ocorreu um erro na análise de SEO básico: {e}")
        return 0

# Função para calcular pontuação de SEO básico com limite de 5.0 pontos
def limitar_seo_basico(pontuacao_seo_basico):
    # Normaliza a pontuação para não exceder 5.0
    return min(pontuacao_seo_basico, 5.0)

# Função normalizadora de keywords
def calcular_pontuacao_normalizada(keywords):
    """
    Calcula a pontuação normalizada para as keywords com base no número de keywords.
    """
    if not keywords:  # Nenhuma keyword
        return 0
    pontuacao_total = sum([keyword['pontuacao'] for keyword in keywords])
    return pontuacao_total / len(keywords)  # Normaliza pela quantidade

# Função principal de cálculo da pontuação SEO
def calcular_pontuacao_seo(palavras_chave, permissao_trafego_pago, permissao_fundo_funil, nome_do_produto, url_produto, categoria):
    pontuacao_permissao = 1.0 if permissao_trafego_pago else 0.0
    if permissao_fundo_funil:
        pontuacao_permissao += 1.0

    pontuacao_volume_busca = 0.0
    pontuacao_concorrencia_cpc = 0.0
    pontuacao_keyword_total = 0.0

    # Lista de palavras-chave da categoria
    palavras_categoria = TERMS_BY_CATEGORY.get(categoria, [])

    cpc_alertas = []  # Lista para armazenar alertas de CPC alto

    # Chama a função para obter a pontuação de SEO básico
    pontuacao_seo_basico = analisar_seo_basico(url_produto, nome_do_produto, categoria)
    pontuacao_seo_basico = limitar_seo_basico(pontuacao_seo_basico)  # Aplica limite à pontuação de SEO básico

    for palavra in palavras_chave:
        volume = palavra.get('volume', 0)
        cpc = palavra.get('cpc', 0.0)
        termo = palavra.get('palavra', "")

        # Identificar intenção e ajustar peso com base em fundo de funil
        _, peso_intencao = identificar_intencao(termo, nome_do_produto, permissao_fundo_funil)
        ajuste_categoria = 1.5 if termo in palavras_categoria else 1.0  # Ajusta peso com base na categoria
        pontuacao_keyword_total += peso_intencao * ajuste_categoria  # Pontuação de intenção da palavra

        # Ajuste do volume
        if volume > 5000:
            pontuacao_volume_busca += PESO_VOLUME_BUSCA * peso_intencao * ajuste_categoria
        elif 1500 <= volume <= 4999:
            pontuacao_volume_busca += (PESO_VOLUME_BUSCA * 0.5) * peso_intencao * ajuste_categoria
        else:
            pontuacao_volume_busca += (PESO_VOLUME_BUSCA * 0.25) * peso_intencao * ajuste_categoria

        # Ajuste do CPC com maior sensibilidade para faixas de volume e CPC
        if 100 <= volume <= 999:  # Faixa de volume 100 a 999
            if cpc > 3.0:  # CPC alto
                pontuacao_concorrencia_cpc += (PESO_CONCORRENCIA_CPC * 1.2) * peso_intencao * ajuste_categoria
                cpc_alertas.append(f"⚠️ Palavra-chave '{termo}' possui CPC alto (${cpc:.2f}). Explore alternativas mais baratas.")
            elif 1.0 <= cpc <= 3.0:  # CPC médio
                pontuacao_concorrencia_cpc += PESO_CONCORRENCIA_CPC * peso_intencao * ajuste_categoria
            else:  # CPC baixo
                pontuacao_concorrencia_cpc += (PESO_CONCORRENCIA_CPC * 0.8) * peso_intencao * ajuste_categoria

        elif 1000 <= volume <= 1999:  # Faixa de volume 1000 a 1999
            if cpc > 4.0:  # CPC alto
                pontuacao_concorrencia_cpc += (PESO_CONCORRENCIA_CPC * 1.2) * peso_intencao * ajuste_categoria
                cpc_alertas.append(f"⚠️ Palavra-chave '{termo}' possui CPC alto (${cpc:.2f}). Explore alternativas mais baratas.")
            elif 1.5 <= cpc <= 4.0:  # CPC médio
                pontuacao_concorrencia_cpc += PESO_CONCORRENCIA_CPC * peso_intencao * ajuste_categoria
            else:  # CPC baixo
                pontuacao_concorrencia_cpc += (PESO_CONCORRENCIA_CPC * 0.8) * peso_intencao * ajuste_categoria

        elif 2000 <= volume <= 2999:  # Faixa de volume 2000 a 2999
            if cpc > 5.0:  # CPC alto
                pontuacao_concorrencia_cpc += (PESO_CONCORRENCIA_CPC * 1.2) * peso_intencao * ajuste_categoria
                cpc_alertas.append(f"⚠️ Palavra-chave '{termo}' possui CPC alto (${cpc:.2f}). Explore alternativas mais baratas.")
            elif 2.0 <= cpc <= 5.0:  # CPC médio
                pontuacao_concorrencia_cpc += PESO_CONCORRENCIA_CPC * peso_intencao * ajuste_categoria
            else:  # CPC baixo
                pontuacao_concorrencia_cpc += (PESO_CONCORRENCIA_CPC * 0.8) * peso_intencao * ajuste_categoria

        elif 3000 <= volume <= 3999:  # Faixa de volume 3000 a 3999
            if cpc > 6.0:  # CPC alto
                pontuacao_concorrencia_cpc += (PESO_CONCORRENCIA_CPC * 1.2) * peso_intencao * ajuste_categoria
                cpc_alertas.append(f"⚠️ Palavra-chave '{termo}' possui CPC alto (${cpc:.2f}). Explore alternativas mais baratas.")
            elif 2.5 <= cpc <= 6.0:  # CPC médio
                pontuacao_concorrencia_cpc += PESO_CONCORRENCIA_CPC * peso_intencao * ajuste_categoria
            else:  # CPC baixo
                pontuacao_concorrencia_cpc += (PESO_CONCORRENCIA_CPC * 0.8) * peso_intencao * ajuste_categoria

        elif 4000 <= volume <= 4999:  # Faixa de volume 4000 a 4999
            if cpc > 8.0:  # CPC alto
                pontuacao_concorrencia_cpc += (PESO_CONCORRENCIA_CPC * 1.2) * peso_intencao * ajuste_categoria
                cpc_alertas.append(f"⚠️ Palavra-chave '{termo}' possui CPC alto (${cpc:.2f}). Explore alternativas mais baratas.")
            elif 3.0 <= cpc <= 8.0:  # CPC médio
                pontuacao_concorrencia_cpc += PESO_CONCORRENCIA_CPC * peso_intencao * ajuste_categoria
            else:  # CPC baixo
                pontuacao_concorrencia_cpc += (PESO_CONCORRENCIA_CPC * 0.8) * peso_intencao * ajuste_categoria

        elif 5000 <= volume <= 6999:  # Faixa de volume 5000 a 6999
            if cpc > 9.0:  # CPC alto
                pontuacao_concorrencia_cpc += (PESO_CONCORRENCIA_CPC * 1.2) * peso_intencao * ajuste_categoria
                cpc_alertas.append(f"⚠️ Palavra-chave '{termo}' possui CPC alto (${cpc:.2f}). Explore alternativas mais baratas.")
            elif 3.5 <= cpc <= 9.0:  # CPC médio
                pontuacao_concorrencia_cpc += PESO_CONCORRENCIA_CPC * peso_intencao * ajuste_categoria
            else:  # CPC baixo
                pontuacao_concorrencia_cpc += (PESO_CONCORRENCIA_CPC * 0.8) * peso_intencao * ajuste_categoria

        elif 7000 <= volume <= 10000:  # Faixa de volume 7000 a 10000
            if cpc > 12.0:  # CPC alto
                pontuacao_concorrencia_cpc += (PESO_CONCORRENCIA_CPC * 1.2) * peso_intencao * ajuste_categoria
                cpc_alertas.append(f"⚠️ Palavra-chave '{termo}' possui CPC alto (${cpc:.2f}). Explore alternativas mais baratas.")
            elif 4.0 <= cpc <= 12.0:  # CPC médio
                pontuacao_concorrencia_cpc += PESO_CONCORRENCIA_CPC * peso_intencao * ajuste_categoria
            else:  # CPC baixo
                pontuacao_concorrencia_cpc += (PESO_CONCORRENCIA_CPC * 0.8) * peso_intencao * ajuste_categoria

   # Normalização da pontuação de keywords
    pontuacao_keyword_normalizada = calcular_pontuacao_normalizada(
        [{'pontuacao': peso_intencao * ajuste_categoria} for termo in palavras_chave]
    )

    # Cálculo total da pontuação SEO e palavras-chave incluindo pontuação de SEO básico
    pontuacao_total_seo_palavras = round(
        pontuacao_permissao +
        pontuacao_volume_busca +
        pontuacao_concorrencia_cpc +
        pontuacao_keyword_normalizada +  # Agora normalizada
        pontuacao_seo_basico,
        2
    )

    # Detalhes de pontuação para debug e ajuste visual
    detalhes_seo = {
        'pontuacao_permissao': pontuacao_permissao,
        'pontuacao_volume_busca': pontuacao_volume_busca,
        'pontuacao_concorrencia_cpc': pontuacao_concorrencia_cpc,
        'pontuacao_keyword': pontuacao_keyword_normalizada,  # Inclui a versão normalizada
        'pontuacao_seo_basico': pontuacao_seo_basico,
        'cpc_alertas': cpc_alertas
    }

    # Debug logs
    print(f"[DEBUG] Pontuação de Permissão: {pontuacao_permissao}")
    print(f"[DEBUG] Pontuação de Volume de Busca: {pontuacao_volume_busca}")
    print(f"[DEBUG] Pontuação de Concorrência CPC: {pontuacao_concorrencia_cpc}")
    print(f"[DEBUG] Pontuação de Keyword Normalizada: {pontuacao_keyword_normalizada}")
    print(f"[DEBUG] Pontuação de SEO Básico: {pontuacao_seo_basico}")
    print(f"[DEBUG] Alertas de CPC: {cpc_alertas}")
    print(f"[DEBUG] Pontuação Total SEO e Palavras-Chave: {pontuacao_total_seo_palavras}\n")

    return pontuacao_total_seo_palavras, detalhes_seo

# Rota para avaliar SEO (se necessário)
@app.route("/avaliar_seo", methods=["POST"])
def avaliar_seo():
    dados = request.json
    resultados = []

    for produto in dados['produtos']:
        resultado = calcular_pontuacao_seo(
            produto['palavras_chave'],
            produto['permissao_trafego_pago'],
            produto['permissao_fundo_funil'],
            produto['nome'],
            produto['url'],
            produto.get('categoria')
        )
        resultados.append({"pontuacao": resultado, "nome": produto['nome']})

    return jsonify({"produtos": resultados})


# CALCULO DOS CRITERIOS - Atualização da função home com a nova estrutura de pontuação
from flask import Flask, render_template, request

# app = Flask(__name__)  # Já definido anteriormente

# Existing functions remain the same
def calcular_qualidade_pagina(url):
    return qualidade_pagina(url)  # Chama a função já existente para análise

def calcular_copywriting(url):
    return copywriting_pontuacao(url)  # Chama a função já existente de copywriting

def calcular_beneficios_ofertas(url):
    return pontuacao_beneficios_ofertas_especiais(url)

def calcular_preco_valor_percebido(url):
    return preco_valor_percebido_pontuacao(url)

def calcular_faixa_precos(url):
    return faixa_precos_pontuacao(url)

def analisar_sazonalidade(nome_do_produto):
    pontuacao_sazonalidade = 1
    descricao_sazonalidade = "está assim pra nao puxar a api depois só comentar essa função. nao esquecer de colocar as frases da sazonalidade depois."
    return pontuacao_sazonalidade, descricao_sazonalidade

#def analisar_sazonalidade(nome_do_produto):
    try:
        # Simulação de análise real (o código completo já foi fornecido antes)
        pontuacao_sazonalidade = 1.0  # Exemplo de pontuação numérica (ajuste conforme necessário)
        descricao_final = "O produto apresenta interesse estável, sem grandes variações sazonais."

        # Certifique-se de que a pontuação é um número antes de retornar
        if not isinstance(pontuacao_sazonalidade, (int, float)):
            raise ValueError(f"Pontuação sazonalidade inválida: {pontuacao_sazonalidade}")

        return pontuacao_sazonalidade, descricao_final

    except Exception as e:
        # Log do erro e retorno seguro
        logging.error(f"Erro ao analisar sazonalidade: {e}")
        return 0.0, "Erro ao analisar sazonalidade."


import unicodedata

def remover_acentos(txt):
    return ''.join(c for c in unicodedata.normalize('NFD', txt)
                   if unicodedata.category(c) != 'Mn')



# FUNÇÃO % CTR COMEÇA AQUI

from flask import Flask, render_template, request

app = Flask(__name__)

# Tabela CTR com categorias principais, subcategorias e CTR médio
tabela_ctr = {
    "saúde e bem-estar": {
        "subcategorias": [
            "bem-estar", "conforto e praticidade", "perda de peso", "dores (articulações, etc.)",
            "remédios naturais e bem-estar", "nutrição baseada em plantas", "espiritualidade", "fitness"
        ],
        "ctr_medio": 3.27,
    },
    "finanças e negócios": {
        "subcategorias": [
            "negócios e empreendedorismo", "finanças pessoais e investimentos",
            "marketing e vendas", "carreira e desenvolvimento pessoal", "trabalho remoto e produtividade"
        ],
        "ctr_medio": 2.91,
    },
    "relacionamentos": {
        "subcategorias": [
            "relacionamento feminino", "relacionamento masculino", "autodesenvolvimento e autoajuda"
        ],
        "ctr_medio": 6.05,
    },
    "educação": {
        "subcategorias": [
            "cursos online", "e-books", "educação formal", "treinamentos profissionais"
        ],
        "ctr_medio": 3.78,
    },
    "casa e decoração": {
        "subcategorias": [
            "jardinagem", "casa e decoração", "sustentabilidade e vida ecológica",
            "economia e tempo", "segurança e confiança", "performance e eficiência"
        ],
        "ctr_medio": 2.44,
    },
    "tecnologia e entretenimento": {
        "subcategorias": [
            "jogos", "softwares e apps", "esporte e lazer", "alimentos e bebidas", "bebidas energéticas"
        ],
        "ctr_medio": 2.09,
    },
}


def analisar_ctr(pontuacao_ctr):
    """
    Analisa a pontuação de CTR e retorna a descrição correspondente com base nas faixas definidas.
    """
    # Dicionário de faixas de pontuação e descrições correspondentes
    descricao_ctr_dict = {
        (0, 10.99): "Muito Ruim: O CTR do produto está muito abaixo do esperado, sugerindo baixa atratividade. Produto com baixa otimização e potencial limitado. Indicativo de palavras-chave mal selecionadas, SEO insuficiente ou falta de alinhamento com a intenção de busca. Anúncios terão ROI baixo.",
        (11, 15.99): "Ruim a Moderado: Produto mediano, necessitando melhorias significativas. CTR sugere intenção fraca ou público-alvo mal definido. Pode funcionar, mas exige ajustes cuidadosos em palavras-chave e copy antes de campanhas maiores.",
        (16, 20.99): "Moderado a Bom: Produto razoável, com boa estrutura e otimização. Pode gerar resultados consistentes, mas ainda há espaço para melhorias, principalmente no alinhamento entre palavras-chave e oferta. Ideal para testes com tráfego pago.",
        (21, 25.99): "Bom: O CTR é bom, indicando uma boa relevância e engajamento. Produto sólido, otimizado para tráfego pago. SEO e palavras-chave transacionais são efetivos, gerando CTR consistente. Recomenda-se ajustes finais para maximizar desempenho em campanhas.",
        (26, 30.99): "Muito Bom: Produto forte, bem otimizado para conversão. CTR acima da média, indicando bom alinhamento com o público-alvo. Ótima escolha para campanhas de tráfego pago e escalabilidade.",
        (31, 40.99): "Excelente: O CTR está excelente, sugerindo alta atratividade e performance ideal. Produto de alta qualidade, com CTR elevado e potencial competitivo. SEO, copywriting e intenção de palavras-chave estão bem ajustados. Ótima performance esperada com tráfego pago. Ideal para campanhas agressivas.",
        (41, 50.99): "Potencial Top: Produto excepcional em nichos competitivos. CTR elevado reflete forte apelo ao público e alta taxa de cliques. Excelente opção para escalabilidade rápida e investimento agressivo em anúncios.",
        (51, 70.99): "Nicho Ouro (Raro): Produto com performance extraordinária, raramente encontrado em mercados competitivos. SEO, intenção e copywriting estão perfeitamente alinhados. Ótima oportunidade para explorar ao máximo o tráfego pago antes de saturação.",
        (71, 86.75): "Exclusivo / Fora da Curva: Produto de desempenho incomparável. Demanda de mercado, copy e oferta estão perfeitamente ajustados. Potencial de gerar resultados excepcionais, mas deve ser monitorado de perto para manter o alto desempenho. Ideal para campanhas de escala máxima."
    }

    # Encontrar a descrição com base na pontuação
    for faixa, descricao in descricao_ctr_dict.items():
        if faixa[0] <= pontuacao_ctr <= faixa[1]:
            return descricao

    return "Pontuação de CTR fora das faixas esperadas."

# Passar os valores calculados para o template
def gerar_resultados(nome_do_produto, pontuacao_ctr):
    pontuacao_sazonalidade, descricao_sazonalidade = analisar_sazonalidade(nome_do_produto)
    descricao_ctr = analisar_ctr(pontuacao_ctr)

    return {
        "descricao_sazonalidade": descricao_sazonalidade,
        "descricao_ctr": descricao_ctr,
        # Outras variáveis para o template
    }

# Funções auxiliares
def remover_acentos(txt):
    """
    Remove acentos de um texto para padronização.
    """
    import unicodedata
    return ''.join(c for c in unicodedata.normalize('NFD', txt) if unicodedata.category(c) != 'Mn')

def avaliar_ctr(categoria, tabela):
    """
    Retorna o CTR médio da categoria, com tratamento para normalização e erros.
    """
    categoria_normalizada = remover_acentos(categoria.lower())
    tabela_normalizada = {remover_acentos(key.lower()): value for key, value in tabela.items()}
    if categoria_normalizada in tabela_normalizada:
        ctr_medio = tabela_normalizada[categoria_normalizada]["ctr_medio"]
        print(f"[DEBUG] Categoria '{categoria}' encontrada com CTR médio: {ctr_medio}")
        return ctr_medio
    print(f"[ERRO] Categoria '{categoria}' não encontrada na tabela CTR.")
    return 0

def normalizar_valor(valor, minimo, maximo):
    """
    Normaliza um valor entre um intervalo (mínimo e máximo) para uma escala de 0 a 10.
    """
    if maximo == minimo:  # Evitar divisão por zero
        return 0
    if valor <= minimo:
        return 0
    if valor >= maximo:
        return 10
    return ((valor - minimo) / (maximo - minimo)) * 10

def identificar_intencao(palavra_chave, nome_do_produto, permissao_fundo_funil):
    """
    Identifica a intenção de uma palavra-chave e retorna seu peso.
    """
    palavra_chave = palavra_chave.lower()
    
    # Verifica se o nome do produto está na palavra-chave e se fundo de funil é permitido
    if permissao_fundo_funil and nome_do_produto and nome_do_produto.lower() in palavra_chave:
        return 'produto_fundo_funil', 2.5  # Peso transacional para fundo de funil

    # Verifica categorias padrão
    palavras_transacional = ["buy", "purchase", "discount", "offer", "sale"]
    palavras_informacional = ["how to", "benefits", "reviews", "comparison"]
    palavras_conscientizacao = ["what is", "importance", "overview"]

    for termo in palavras_transacional:
        if termo in palavra_chave:
            return 'transacional', 2.5
    for termo in palavras_informacional:
        if termo in palavra_chave:
            return 'informacional', 1.0
    for termo in palavras_conscientizacao:
        if termo in palavra_chave:
            return 'conscientizacao', 0.3
    return 'neutro', 0.7  # Peso padrão para palavras sem intenção específica


def validar_categoria(categoria, tabela):
    """
    Valida se uma categoria está presente na tabela CTR e retorna seu nome normalizado.
    """
    categoria_normalizada = remover_acentos(categoria.lower())
    tabela_normalizada = {remover_acentos(key.lower()): key for key in tabela.keys()}
    if categoria_normalizada in tabela_normalizada:
        return tabela_normalizada[categoria_normalizada]  # Retorna o nome original da categoria
    return None


def calcular_nota_final(produto, tabela):
    """
    Calcula a nota final do produto com base em suas pontuações e pesos.
    """
    # Defina pesos para cada critério, ajustáveis conforme o impacto desejado
    pesos = {
        "pontuacao_qualidade_pagina": 1.0,
        "pontuacao_copywriting": 1.0,
        "pontuacao_beneficios_ofertas": 1.0,
        "pontuacao_preco_valor_percebido": 1.0,
        "pontuacao_faixa_precos": 1.0,
        "pontuacao_sazonalidade": 1.0,
        "pontuacao_seo_palavras": 1.5,  # Exemplo: SEO tem peso maior
        "pontuacao_ctr": 2.0,          # Exemplo: CTR tem peso maior
        "pontuacao_redes_sociais": 1.0
    }

    # Soma ponderada das pontuações
    nota_final = sum(
        produto[key] * pesos.get(key, 1.0) for key in produto.keys() if key.startswith("pontuacao")
    )

    # Normaliza a nota final para uma escala de 0 a 10 (se necessário)
    nota_final_normalizada = normalizar_valor(nota_final, 0, 100)  # Ajuste os valores mínimos/máximos conforme necessário

    return round(nota_final_normalizada, 2)


def calcular_ctr_ponderado(categoria, palavras_chave, nome_do_produto, permissao_fundo_funil, pontuacao_seo_basico):
    """
    Calcula o CTR ponderado com base em múltiplas palavras-chave, categoria, volume, CPC e ajustes de SEO.
    """
    # Obter o CTR médio da categoria
    ctr_categoria = avaliar_ctr(categoria, tabela_ctr)
    if ctr_categoria == 0:
        return 0  # Se a categoria não for encontrada, o CTR não pode ser calculado

    ctr_total = 0
    peso_total = 0

    for palavra_chave in palavras_chave:
        # Extrair atributos da palavra-chave
        termo = palavra_chave.get('palavra', '').lower()
        volume = palavra_chave.get('volume', 0)
        cpc = palavra_chave.get('cpc', 0.0)

        # Determinar a intenção e peso da palavra-chave
        _, peso_intencao = identificar_intencao(termo, nome_do_produto, permissao_fundo_funil)

        # Normalizar volume e CPC
        minimo_volume, maximo_volume = 100, 10000  # Faixas ajustáveis
        minimo_cpc, maximo_cpc = 0.1, 15.0         # Faixas ajustáveis
        volume_normalizado = normalizar_valor(volume, minimo_volume, maximo_volume)
        cpc_normalizado = normalizar_valor(cpc, minimo_cpc, maximo_cpc)

        # Ajuste pelo SEO
        ajuste_seo = pontuacao_seo_basico

        # Cálculo do CTR individual para a palavra-chave
        ctr_individual = (
            (ctr_categoria * peso_intencao) *
            (volume_normalizado / (cpc_normalizado + 1)) +
            ajuste_seo
        )

        # Adicionar o CTR individual ao total, ponderado pelo volume
        ctr_total += ctr_individual * volume
        peso_total += volume

    # Calcular a média ponderada do CTR
    ctr_ponderado = (ctr_total / peso_total) if peso_total > 0 else 0

    # Normalização final para evitar valores extremos
    ctr_ponderado = min(max(ctr_ponderado, 0), 86.75)  # Limitar à escala máxima
    return round(ctr_ponderado, 2)








# FUNCAO CTR TERMINA AQUI




# CENÁRIOS DE Comparação Geral e Escolha Ideal DOS PRODUTOS
# DICIONÁRIO DE FRASES
from flask import Flask, render_template, request, redirect, url_for
import random
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.DEBUG)


frases = {
    "custo_beneficio": {
        "cenario1": [ # CPC Alto (Afiliados Experientes)
            "{nome} é um produto com CPC alto ({cpcs}), ideal para afiliados experientes que sabem lidar com tráfego competitivo.",
            "{nome} apresenta um CPC elevado ({cpcs}), sendo mais lucrativo para quem possui maior expertise e orçamento robusto.",
            "Com CPC de {cpcs}, {nome} requer habilidade estratégica, mas oferece um retorno significativo para afiliados experientes.",
            "Afiliados com experiência e capacidade de gerenciar CPC alto ({cpcs}) podem aproveitar melhor {nome}.",
            "{nome} tem um CPC alto ({cpcs}), tornando-se vantajoso para quem busca explorar nichos lucrativos.",
            "Para afiliados com maior expertise, {nome}, com CPC alto ({cpcs}), pode ser uma escolha lucrativa.",
            "Se o afiliado tem habilidade com tráfego competitivo, {nome}, com CPC de {cpcs}, é altamente recomendável.",
            "{nome} é ideal para afiliados experientes que conseguem gerenciar custos altos ({cpcs}).",
            "Com CPC elevado ({cpcs}), {nome} oferece retorno para quem domina campanhas lucrativas.",
            "Afiliados experientes podem explorar o potencial de {nome}, mesmo com CPC alto ({cpcs})."
        ],
        "cenario2": [ # CPC Baixo (Afiliados Iniciantes)
            "{nome}, com CPC baixo ({cpcs}), é perfeito para iniciantes ou afiliados com orçamento limitado.",
            "Com um CPC acessível ({cpcs}), {nome} facilita a entrada para afiliados iniciantes no mercado.",
            "{nome} é uma escolha econômica ({cpcs}), ideal para quem quer minimizar custos iniciais.",
            "Para afiliados que buscam custos baixos ({cpcs}), {nome} é a opção mais acessível e segura.",
            "Afiliados iniciantes podem começar com confiança utilizando {nome}, que tem CPC baixo ({cpcs}).",
            "Com CPC acessível ({cpcs}), {nome} é ideal para quem deseja aprender sem grandes investimentos.",
            "{nome} oferece um ponto de entrada acessível ({cpcs}), ótimo para afiliados novos no mercado.",
            "Para quem prioriza custo-benefício inicial, {nome}, com CPC de {cpcs}, é uma ótima escolha.",
            "{nome} combina acessibilidade ({cpcs}) com facilidade de conversão, perfeito para iniciantes.",
            "Com CPC reduzido ({cpcs}), {nome} oferece segurança e acessibilidade para afiliados novos."
        ],
        "cenario3": [ # CPC Médio (Afiliados Intermediários)
            "Ambos os produtos, {nome_1} e {nome_2}, oferecem vantagens distintas, dependendo do perfil do afiliado.",
            "Enquanto {nome_1} exige mais expertise com CPC de {cpcs_1}, {nome_2}, com {cpcs_2}, é mais acessível.",
            "{nome_1} e {nome_2} atendem diferentes públicos: um para experientes, outro para iniciantes, equilibrando escolhas.",
            "Afiliados podem optar entre {nome_1}, com CPC elevado {cpcs_1}, e {nome_2}, com custos mais baixos ({cpcs_2}).",
            "Com CPCs distintos {cpcs_1} para {nome_1}; {cpcs_2} para {nome_2}, ambos oferecem benefícios únicos.",
            "{nome_1} é voltado para campanhas agressivas, enquanto {nome_2} se adapta a estratégias mais econômicas.",
            "Ambos os produtos podem ser explorados estrategicamente: {nome_1} para alto retorno, {nome_2} para menor risco.",
            "Para afiliados versáteis, {nome_1} e {nome_2} são complementares, abrangendo nichos de alta e baixa concorrência.",
            "Com CPC elevado ({cpcs_1}), {nome_1} oferece desafios e lucros; com {cpcs_2}, {nome_2} é uma aposta segura.",
            "A escolha entre {nome_1} e {nome_2} depende do nível de experiência e do orçamento disponível para campanhas."
        ]

    },
    "pontuacao_total": {
        "cenario1": [ # Produto com Maior Pontuação Total
            "{nome} lidera em pontuação total com {pontuacao_total:.1f} pontos, refletindo sua superioridade em várias métricas.",
            "{nome}, com uma pontuação de {pontuacao_total:.1f}, destaca-se como uma escolha vantajosa para afiliados experientes.",
            "{nome} apresenta {pontuacao_total:.1f} pontos, superando concorrentes e provando ser uma excelente opção.",
            "Com {pontuacao_total:.1f} pontos, {nome} confirma seu potencial para campanhas bem planejadas.",
            "{nome} lidera com uma pontuação de {pontuacao_total:.1f}, mostrando alta eficiência e resultados previsíveis.",
            "A pontuação total de {nome} ({pontuacao_total:.1f}) ressalta sua qualidade como produto competitivo.",
            "{nome} supera expectativas, atingindo {pontuacao_total:.1f} pontos e se destacando no mercado.",
            "{nome}, com {pontuacao_total:.1f} pontos, é ideal para afiliados que priorizam métricas bem avaliadas.",
            "Para quem busca altos padrões, {nome}, com {pontuacao_total:.1f} pontos, é a escolha certa.",
            "{nome} conquista {pontuacao_total:.1f} pontos, liderando em critérios de avaliação essenciais."
        ],
        "cenario2": [ # Produto com Menor Pontuação Total
            "{nome}, com pontuação de {pontuacao_total:.2f}, oferece uma combinação de custo e performance atraente.",
            "Com {pontuacao_total:.2f} pontos, {nome} se torna uma opção interessante para quem busca equilíbrio entre métricas.",
            "{nome} pontua {pontuacao_total:.2f}, ideal para afiliados que priorizam acessibilidade e performance.",
            "A pontuação total de {pontuacao_total:.2f} faz de {nome} uma escolha equilibrada para várias estratégias.",
            "Afiliados iniciantes podem confiar em {nome}, com {pontuacao_total:.2f} pontos, como uma opção consistente.",
            "Com {pontuacao_total:.2f} pontos, {nome} é ideal para quem busca métricas sólidas a um custo reduzido.",
            "{nome}, com {pontuacao_total:.2f} pontos, equilibra acessibilidade e facilidade de conversão.",
            "Pontuando {pontuacao_total:.2f}, {nome} prova ser uma opção segura e eficiente no mercado.",
            "{nome}, atingindo {pontuacao_total:.2f} pontos, pode ser uma escolha acertada para estratégias iniciais.",
            "Com uma pontuação total de {pontuacao_total:.2f}, {nome} oferece consistência para afiliados novos."
        ]
    },
    "conclusao": {
        "cenario1": [ # CPC Alto
            "Escolha recomendada: {nome}, ideal para afiliados experientes, devido ao CPC alto ({cpcs}) e ao potencial de retorno significativo.",
            "{nome} é a melhor opção para afiliados com experiência, oferecendo alto CPC ({cpcs}) e grandes margens de lucro.",
            "Recomenda-se {nome} para quem domina campanhas otimizadas, aproveitando ao máximo seu CPC elevado ({cpcs}).",
            "Para afiliados que sabem converter tráfego competitivo, {nome} é a escolha ideal, graças ao CPC alto ({cpcs}) e retorno atrativo.",
            "Afiliados experientes devem optar por {nome}, cuja lucratividade é destacada pelo CPC de {cpcs}.",
            "Com CPC elevado ({cpcs}), {nome} se destaca como a escolha preferida para quem busca maximizar lucros em campanhas competitivas.",
            "A recomendação do {nome} é para afiliados que possuem expertise no mercado e desejam explorar CPC alto ({cpcs}).",
            "{nome} é mais indicado para afiliados com orçamento robusto, que conseguem aproveitar seu CPC de {cpcs}.",
            "Afiliados dispostos a investir em campanhas otimizadas devem priorizar {nome}, com seu CPC elevado ({cpcs}).",
            "Entre os produtos analisados, {nome} é a melhor escolha para afiliados experientes, devido ao CPC de {cpcs} e potencial de alta conversão."
        ],
        "cenario2": [ # CPC Baixo
            "Escolha recomendada: {nome}, ideal para iniciantes ou quem busca minimizar custos, com CPC acessível ({cpcs}).",
            "Para quem está começando no mercado, {nome} é a melhor escolha, oferecendo baixo CPC ({cpcs}) e facilidade de entrada.",
            "{nome} é recomendado para afiliados com orçamento limitado, devido ao CPC de {cpcs} e sua acessibilidade.",
            "Afiliados que preferem campanhas econômicas devem optar por {nome}, com CPC reduzido ({cpcs}).",
            "Se seu objetivo é minimizar os custos iniciais, tabalhe com {nome} aproveitando seu CPC acessível ({cpcs}).",
            "Com CPC baixo ({cpcs}), {nome} é ideal para afiliados que priorizam menor risco e controle financeiro."

        ],
        "cenario3": [
            "Escolha recomendada: {nome}, com CPC médio ({cpcs}), é uma opção equilibrada para afiliados que desejam gerenciar custos e lucros.",
            "Para quem busca um meio-termo entre investimento e retorno, {nome}, com CPC médio ({cpcs}), é uma escolha inteligente.",
            "{nome}, com CPC médio ({cpcs}), permite campanhas mais controladas, sendo ideal para afiliados intermediários.",
            "Com CPC moderado ({cpcs}), {nome} combina acessibilidade com potencial de retorno consistente.",
            "Afiliados que desejam minimizar riscos sem abrir mão de retornos devem considerar {nome}, com CPC médio ({cpcs}).",
            "{nome} oferece flexibilidade para campanhas estratégicas, graças ao seu CPC médio ({cpcs}).",
            "Com CPC médio ({cpcs}), {nome} é uma escolha versátil para afiliados que procuram um equilíbrio financeiro.",
            "Para campanhas de médio alcance, {nome}, com CPC médio ({cpcs}), proporciona estabilidade e boas oportunidades de retorno.",
            "{nome} é uma escolha recomendável para quem busca campanhas com CPC moderado ({cpcs}) e margens consistentes.",
            "Com CPC médio ({cpcs}), {nome} atende tanto afiliados que buscam expandir quanto aqueles que desejam controlar custos."
]

    }
}

import re

def formatar_cpcs(cpcs):
    """
    Formata valores de CPC com base na entrada.
    Retorna até 7 valores válidos formatados como string.
    """
    try:
        cpcs_validos = []

        # Se a entrada for uma única string, dividir em múltiplos valores
        if isinstance(cpcs, str):
            cpcs = re.split(r"[e,]", cpcs)

        for cpc in cpcs:
            if isinstance(cpc, (int, float)):
                cpcs_validos.append(float(cpc))
            elif isinstance(cpc, str):
                # Remove símbolos e valida números
                cpc_limpo = cpc.replace("$", "").strip()
                if re.fullmatch(r"^\d+(\.\d{1,2})?$", cpc_limpo):
                    cpcs_validos.append(float(cpc_limpo))

        # Limita a 7 valores
        cpcs_validos = cpcs_validos[:7]

        # Formatação condicional baseada no número de CPCs válidos
        if len(cpcs_validos) == 0:
            return "CPC não informado"
        elif len(cpcs_validos) == 1:
            return f"${cpcs_validos[0]:.2f}"
        else:
            return ", ".join([f"${c:.2f}" for c in cpcs_validos[:-1]]) + f" e ${cpcs_validos[-1]:.2f}"
    except Exception as e:
        return "Erro ao formatar CPCs"


# Adicione um dicionário global para rastrear frases já usadas
frases_usadas = {
    "custo_beneficio": set(),
    "pontuacao_total": set(),
    "conclusao": set()
}

def selecionar_comparacao(bloco, cenario, **dados):
    """
    Seleciona uma frase do bloco e cenário especificados e substitui os placeholders pelos dados fornecidos.
    Evita a repetição de frases na mesma análise.
    """
    try:
        if bloco == "custo_beneficio" and cenario == "cenario3":
            produtos = dados.get("produtos", [])

            # Ordena produtos pela média de CPC
            produtos_ordenados = sorted(produtos, key=lambda x: x["avg_cpc"], reverse=True)

            # Seleciona dois produtos distintos
            produto_1 = produtos_ordenados[0]
            produto_2 = produtos_ordenados[-1] if len(produtos_ordenados) > 1 else produto_1

            # Evita repetição do mesmo produto
            if produto_1 == produto_2 and len(produtos_ordenados) > 1:
                produto_2 = produtos_ordenados[1]

            # Busca frases disponíveis que ainda não foram usadas
            frases_do_cenario = frases[bloco][cenario]
            frases_disponiveis = [f for f in frases_do_cenario if f not in frases_usadas[bloco]]

            # Se todas as frases já foram usadas, redefina o conjunto
            if not frases_disponiveis:
                frases_usadas[bloco].clear()
                frases_disponiveis = frases_do_cenario

            # Escolhe uma frase disponível
            frase = random.choice(frases_disponiveis)

            # Marca a frase como usada
            frases_usadas[bloco].add(frase)

            # Substitui os placeholders na frase
            frase = frase.format(
                nome_1=produto_1["nome"],
                nome_2=produto_2["nome"],
                cpcs_1=formatar_cpcs(produto_1.get("cpcs", [])),
                cpcs_2=formatar_cpcs(produto_2.get("cpcs", [])),
                nome=produto_1["nome"],
                cpcs=formatar_cpcs(produto_1.get("cpcs", []))
            )
            return frase

        # Recupera frases disponíveis para outros cenários
        frases_do_cenario = frases[bloco][cenario]
        frases_disponiveis = [f for f in frases_do_cenario if f not in frases_usadas[bloco]]

        # Se todas as frases já foram usadas, redefina o conjunto
        if not frases_disponiveis:
            frases_usadas[bloco].clear()
            frases_disponiveis = frases_do_cenario

        # Escolhe uma frase disponível
        frase = random.choice(frases_disponiveis)

        # Marca a frase como usada
        frases_usadas[bloco].add(frase)

        # Substitui os placeholders na frase
        frase = frase.format(**dados)

        return frase
    except Exception as e:
        return f"Erro ao formatar as frases: {e}"


def gerar_frases_custo_beneficio(produtos):
    phrases = []
    produtos_ordenados = sorted(produtos, key=lambda x: x['avg_cpc'], reverse=True)
    num_produtos = len(produtos_ordenados)

    for index, produto in enumerate(produtos_ordenados):
        if num_produtos == 1:
            cenario = 'cenario1'
        elif index == 0:
            cenario = 'cenario1'  # CPC Alto
        elif index == num_produtos - 1:
            cenario = 'cenario2'  # CPC Baixo
        else:
            cenario = 'cenario3'  # CPC Médio
        
        # Passar lista completa de produtos para o cenário 3
        if cenario == 'cenario3':
            frase = selecionar_comparacao('custo_beneficio', cenario, produtos=produtos)
        else:
            frase = selecionar_comparacao('custo_beneficio', cenario, **produto)
        
        phrases.append(frase)
    return phrases


def gerar_frases_pontuacao_total(produtos):
    """
    Gera frases para o bloco pontuação_total.
    """
    phrases = []
    produtos_ordenados = sorted(produtos, key=lambda x: x['pontuacao_total'], reverse=True)
    num_produtos = len(produtos_ordenados)

    for index, produto in enumerate(produtos_ordenados):
        if num_produtos == 1:
            cenario = 'cenario1'  # Apenas um produto
        elif index == 0:
            cenario = 'cenario1'  # Pontuação Alta
        elif index == num_produtos - 1:
            cenario = 'cenario2'  # Pontuação Baixa
        else:
            continue  # Ignorar caso intermediário

        # Gera a frase com base no cenário válido
        frase = selecionar_comparacao('pontuacao_total', cenario, **produto)
        phrases.append(frase)

    return phrases


def gerar_frases_conclusao(produtos):
    """
    Gera frases de conclusão.
    """
    phrases = []
    produtos_ordenados = sorted(produtos, key=lambda x: x['avg_cpc'], reverse=True)

    for produto in produtos_ordenados:
        # Formatar CPCs
        cpcs_formatados = formatar_cpcs(produto.get('cpcs', []))

        frase = selecionar_comparacao(
            "conclusao",
            "cenario1",
            nome=produto["nome"],
            cpcs=cpcs_formatados
        )
        phrases.append(frase)

    return phrases


@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

# Função analisar oficial
@app.route("/analisar", methods=["POST"])
def analisar():
    nome_produto = request.form.get('nome_produto')
    pontuacao_sazonalidade, descricao_final = analisar_sazonalidade(nome_produto)

    try:
        nicho = request.form.get("nicho", "Nicho Não Informado")
        logging.debug(f"Nicho recebido: {nicho}")

        produtos = []
        for i in range(1, 6):  # Até 5 produtos
            nome_produto = request.form.get(f"nome_produto_{i}", "").strip()
            if not nome_produto:
                continue

            url_produto = request.form.get(f"url_produto_{i}", "").strip()
            categoria_produto = request.form.get(f"categoria_produto_{i}", "").strip()

            # Calcular pontuação de Redes Sociais
            pontuacao_redes = calcular_redes_sociais(request.form, i)
            logging.debug(f"Pontuação Redes Sociais para produto {i}: {pontuacao_redes}")

            # Processar o produto
            produto = processar_produto(
                index=i,
                nome_produto=nome_produto,
                url_produto=url_produto,
                permissao_trafego_pago=True,
                permissao_fundo_funil=True,
                form_data=request.form,
                categoria_produto=categoria_produto,
                tabela_ctr=tabela_ctr,
                pontuacao_redes_sociais=pontuacao_redes  # Passa a pontuação das redes sociais
            )

            if produto:
                produtos.append(produto)

        # Ordenar produtos por pontuação total
        produtos = sorted(produtos, key=lambda p: p.get("pontuacao_total", 0), reverse=True)

        # Gerar frases e renderizar o template
        return render_template(
            "analisar.html",
            nicho=nicho,
            produtos=produtos,
            frases_custo_beneficio=gerar_frases_custo_beneficio(produtos),
            frases_pontuacao_total=gerar_frases_pontuacao_total(produtos),
            frases_conclusao=gerar_frases_conclusao(produtos),
            pontuacao_sazonalidade=pontuacao_sazonalidade, # frases sazonalidade
            descricao_final=descricao_final, # Ordenar prod
        )
    except Exception as e:
        logging.error(f"Erro ao processar a análise: {e}")
        return "Erro ao processar a análise.", 500





# FIM CENÁRIOS DE Comparação Geral e Escolha Ideal DOS PRODUTOS



# INÍCIO MELHORIA 4 - Refinar o Critério de Volume e Concorrência por Nicho Específico


# FIM MELHORIA 4 - Refinar o Critério de Volume e Concorrência por Nicho Específico


# Função para avaliar Presença nas Redes Sociais 10 de 16


# FIM CRITERIO 10 - REDES SOCIAIS





# INICIO CRITERIO 11 - ENGAJAMENTO SOCIAL - REDDIT
# Configuração do cliente Reddit
# Importações
# Importações

import praw
from flask import Flask, request, jsonify
import logging
import time

import concurrent.futures
from functools import lru_cache

# Configuração de logging
logging.basicConfig(level=logging.DEBUG)

# Configuração do Reddit
client_id = "iRmx3x5KWqB1cSkNDWLIWQ"
client_secret = "jyQU0Ek_FsR8PD6aVCg8X_TW1HzIuQ"
user_agent = "ViverDeGringa (by /u/Putrid-Low4692)"

# Configuração do servidor Flask
app = Flask(__name__)


def buscar_subreddit(subreddit_name, nome_produto):
    try:
        submissions = reddit.subreddit(subreddit_name).search(nome_produto, limit=5)
        resultados = []
        for submission in submissions:
            resultados.append({
                "subreddit": subreddit_name,
                "titulo": submission.title,
                "votos": submission.score,
                "comentarios": submission.num_comments
            })
        return resultados
    except Exception as e:
        return {"subreddit": subreddit_name, "erro": str(e)}

# Lista de subreddits para busca
subreddits = ["HealthTrendz", "diabetes", "newyorkknicks", "ApexDiscount", "WeReviewedIt"]

# Paralelismo
nome_produto = "Gluco trust"
with concurrent.futures.ThreadPoolExecutor() as executor:
    future_to_subreddit = {executor.submit(buscar_subreddit, sub, nome_produto): sub for sub in subreddits}

    resultados = []
    for future in concurrent.futures.as_completed(future_to_subreddit):
        subreddit_name = future_to_subreddit[future]
        try:
            data = future.result()
            resultados.extend(data)
        except Exception as exc:
            print(f"Erro no subreddit {subreddit_name}: {exc}")

print(resultados)


# Inicializa o Reddit
try:
    reddit = praw.Reddit(
        client_id=client_id,
        client_secret=client_secret,
        user_agent=user_agent,
    )
    logging.debug("Reddit inicializado com sucesso.")
except Exception as e:
    logging.error(f"Erro ao inicializar o Reddit: {e}")
    reddit = None

# Lista de subreddits fixos

# Subreddits organizados por categoria e subcategoria
subreddits_por_categoria = {
    "Saúde e Bem-Estar": {
        "Emagrecimento e Perda de Peso": [
            "HealthTrendz", "Diabetes", "NewYorkKnicks", "ApexDiscount", "WeReviewedIt", "HistoryNice7823", 
            "weightlossdiets", "ProServices", "healthyeating"
            
        ],
        "Beleza e Cuidados Pessoais": [
            "PCOSloseit", "FamilyMedicine"
        ]

    },
    "Finanças e Negócios": {
        "Negócios e Empreendedorismo": [
            "Entrepreneur", "smallbusiness", "startups", "sidehustle", 
            "Business_Ideas", "EntrepreneurRideAlong", "IndieBiz", "Business",
            "Consulting", "Marketing", "BlackOwnedBusiness", "WomenEntrepreneurs"
        ],
        "Finanças Pessoais e Investimentos": [
            "personalfinance", "investing", "FinancialIndependence", "povertyfinance",
            "leanfire", "FinancialPlanning", "Dividends", "StockMarket",
            "CryptoCurrency", "RealEstate", "FinancialCareers", "StudentLoans"
        ],
        "Marketing e Vendas": [
            "marketing", "digital_marketing", "SEO", "Entrepreneur", 
            "sales", "Advertising", "ContentMarketing", "SocialMediaMarketing",
            "Emailmarketing", "Copywriting", "MarketingResearch", "MarketingStrategy"
        ],
        "Carreira e Desenvolvimento Pessoal": [
            "careerguidance", "GetEmployed", "jobs", "resumes", "WorkOnline",
            "Productivity", "GetDisciplined", "DecidingToBeBetter", "SelfImprovement",
            "PersonalDevelopment", "AskHR", "WorkReform"
        ],
        "Trabalho Remoto e Produtividade": [
            "telecommuting", "WorkFromHome", "digitalnomad", "Productivity",
            "Notion", "GettingThingsDone", "Entrepreneur", "RemoteWork",
            "Freelance", "SideProject", "WorkRemotely", "RemoteJob"
        ]
    },
    "Relacionamentos": {
        "Relacionamento Feminino": [
            "TwoXChromosomes", "AskWomen", "FemaleDatingStrategy", "WomensHealth",
            "xxfitness", "Periods", "Women", "Endo", "PCOS", "AskFeminists",
            "WomenInSTEM", "SingleLadies"
        ],
        "Relacionamento Masculino": [
            "AskMen", "MensRights", "MensLib", "MensHealth", "NoFap", 
            "AskMenOver30", "AskMenOver40", "AskMenOver50", "Divorce_Men", 
            "MaleFashionAdvice", "Dads", "SingleDads"
        ],
        "Autodesenvolvimento e Autoajuda": [
            "SelfImprovement", "DecidingToBeBetter", "GetDisciplined", "Motivation",
            "Anxiety", "Depression", "meditation", "Mindfulness", "stoicism",
            "ZenHabits", "Therapy", "MentalHealthTips"
        ]
    },
    "Educação": {
        "Cursos Online e E-books": [
            "edX", "Coursera", "OnlineCourses", "learnprogramming", "ebooks",
            "FreeEBOOKS", "FreeCourses", "Skillshare", "udemyfreebies",
            "learnmachinelearning", "UdemyDeals", "OnlineLearning"
        ],
        "Educação Formal e Treinamentos Profissionais": [
            "Professors", "Teachers", "GradSchool", "college", "AskAcademia",
            "AcademicPsychology", "EngineeringStudents", "LawSchool", "medschool",
            "Accounting", "USColleges", "HighSchoolStudents"
        ]
    },
    "Casa e Decoração": {
        "Jardinagem e Sustentabilidade": [
            "gardening", "IndoorGarden", "Permaculture", "ZeroWaste",
            "composting", "UrbanGardening", "houseplants", "OrganicGardening",
            "Hydroponics", "Beekeeping", "AmericanGarden", "BackyardGardens"
        ],
        "Casa, Decoração e Vida Ecológica": [
            "HomeImprovement", "InteriorDesign", "DIY", "Minimalism", 
            "TinyHouses", "HomeDecorating", "Frugal", "HomeGardenIdeas",
            "AmericanInteriors"
        ]
    },
    "Tecnologia e Entretenimento": {
        "Jogos e Software": [
            "gaming", "technology", "pcgaming", "consoles", "boardgames",
            "IndieGames", "GameDesign", "Esports", "GameDeals", 
            "PlayStation", "XboxSeriesX", "AmericanGaming"
        ]
    }
}


import unicodedata

def remover_acentos(texto):
    """
    Remove acentos e normaliza o texto para comparações.
    """
    if not texto:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto)
        if unicodedata.category(c) != "Mn"
    )

def get_subreddits_por_categoria(categoria):
    if not isinstance(categoria, str):
        logging.warning(f"Categoria recebida não é uma string: {categoria}. Convertendo para string.")
        categoria = str(categoria)
    categoria_normalizada = remover_acentos(categoria.lower().strip())
    logging.debug(f"[DEBUG] Categoria normalizada recebida: {categoria_normalizada}")
    
    for categoria_principal, subcategorias in subreddits_por_categoria.items():
        categoria_principal_normalizada = remover_acentos(categoria_principal.lower())
        logging.debug(f"[DEBUG] Comparando com categoria principal: {categoria_principal_normalizada}")
        
        if categoria_principal_normalizada == categoria_normalizada:
            logging.debug(f"[DEBUG] Categoria principal encontrada: {categoria_principal}")
            return subcategorias
        
        for subcategoria, subreddits in subcategorias.items():
            subcategoria_normalizada = remover_acentos(subcategoria.lower())
            logging.debug(f"[DEBUG] Comparando com subcategoria: {subcategoria_normalizada}")
            
            if subcategoria_normalizada == categoria_normalizada:
                logging.debug(f"[DEBUG] Subcategoria encontrada: {subcategoria}")
                return {subcategoria: subreddits}
    
    logging.warning(f"[ERRO] Categoria '{categoria}' não encontrada no dicionário.")
    
    return {}



@lru_cache(maxsize=128)
def calcular_pontuacao_reddit(nome_produto, categoria):
    """
    Calcula a pontuação de engajamento no Reddit para a categoria do produto.
    """
    if not reddit:
        logging.error("Reddit não está inicializado.")
        return {"erro": "Integração com Reddit indisponível.", "pontuacao_reddit": 0, "subreddits_avaliados": []}

    # Buscar subreddits pela categoria
    subcategorias = get_subreddits_por_categoria(categoria)
    if not subcategorias:
        logging.warning(f"[ERRO] Nenhuma subcategoria encontrada para a categoria: {categoria}")
        return {"erro": f"Nenhuma subcategoria encontrada para a categoria: {categoria}", "pontuacao_reddit": 0, "subreddits_avaliados": []}

    # Coletar subreddits dentro das subcategorias
    subreddits = []
    for subs in subcategorias.values():
        subreddits.extend(subs)

    if not subreddits:
        logging.warning(f"[ERRO] Nenhum subreddit associado à categoria: {categoria}")
        return {"erro": f"Nenhum subreddit associado à categoria: {categoria}", "pontuacao_reddit": 0, "subreddits_avaliados": []}

    # Inicializar variáveis para o cálculo
    pontuacao_total = 0
    subreddits_avaliados = []
    subreddits_com_pontuacao = []  # Lista de subreddits que pontuaram
    erros = []  # Lista para armazenar subreddits problemáticos

    try:
        for subreddit in subreddits:
            try:
                time.sleep(0.2)  # Evitar rate-limiting
                submissions = reddit.subreddit(subreddit).search(nome_produto, limit=5)

                for submission in submissions:
                    mencoes = 1 if nome_produto.lower() in submission.title.lower() else 0
                    votos = submission.score
                    comentarios = submission.num_comments
                    engajamento = (
                        5 if votos + comentarios > 50
                        else 3 if votos + comentarios > 25
                        else 1 if votos + comentarios > 10
                        else 0
                    )
                    pontuacao_item = mencoes + engajamento

                    # Somar pontuação ao total
                    pontuacao_total += pontuacao_item

                    # Adicionar subreddit à lista de pontuados se ganhou pontuação
                    if pontuacao_item > 0:
                        subreddits_com_pontuacao.append({
                            "subreddit": subreddit,
                            "titulo": submission.title,
                            "votos": votos,
                            "comentarios": comentarios,
                            "mencoes": mencoes,
                            "engajamento": engajamento,
                        })

                    # Adicionar à lista completa para exibição geral
                    subreddits_avaliados.append({
                        "subreddit": subreddit,
                        "titulo": submission.title,
                        "votos": votos,
                        "comentarios": comentarios,
                        "mencoes": mencoes,
                        "engajamento": engajamento,
                    })
            except Exception as e:
                # Registro do subreddit com problema
                erros.append(f"Erro no subreddit {subreddit}: {e}")
                logging.error(f"[ERRO] Subreddit {subreddit} falhou: {e}")
                continue

    except Exception as e:
        logging.error(f"[ERRO] Falha geral ao calcular pontuação no Reddit: {e}")
        return {"erro": f"Erro: {e}", "pontuacao_reddit": 0, "subreddits_avaliados": []}

    # Log dos erros
    if erros:
        logging.warning(f"[DEBUG] Subreddits com erro: {erros}")

    # Calcula a média apenas dos subreddits com engajamento > 1
    subreddits_validos = len([s for s in subreddits_com_pontuacao if s.get("engajamento", 0) > 1])
    pontuacao_media = round(pontuacao_total / subreddits_validos, 2) if subreddits_validos > 0 else 0

    return {
        "pontuacao_reddit": pontuacao_media,
        "subreddits_avaliados": subreddits_avaliados,
        "subreddits_com_pontuacao": subreddits_com_pontuacao,
        "subreddits_com_erro": erros
    }




# Rota de análise com Reddit
@app.route("/analisar_com_reddit", methods=["POST"])
def analisar_com_reddit():
    try:
        produtos = request.get_json().get("produtos", [])
        logging.debug(f"[DEBUG] Produtos recebidos para análise Reddit: {produtos}")

        if not produtos:
            logging.error("[ERRO] Nenhum produto fornecido na solicitação.")
            return jsonify({"erro": "Nenhum produto fornecido na solicitação."}), 400

        produtos_atualizados = []
        for produto in produtos:
            nome_produto = produto.get("nome")
            categoria = produto.get("categoria")
            
            # Validação de entrada
            if not nome_produto or not categoria:
                logging.warning(f"[ERRO] Produto incompleto: {produto}")
                produtos_atualizados.append({
                    "nome": nome_produto or "Desconhecido",
                    "erro": "Produto sem nome ou categoria especificada."
                })
                continue

            logging.debug(f"[DEBUG] Processando produto: Nome: {nome_produto}, Categoria: {categoria}")
            reddit_resultados = calcular_pontuacao_reddit(nome_produto, categoria)
            produtos_atualizados.append({
                "nome": nome_produto,
                "reddit_pontuacao":(reddit_resultados.get("pontuacao_reddit", 0)),
                "subreddits_avaliados": reddit_resultados.get("subreddits_avaliados", []),
                "subreddits_com_pontuacao": reddit_resultados.get("subreddits_com_pontuacao", []),
            })


        # Ordenar subreddits_com_pontuacao pelo critério 'engajamento', maior para menor
        for produto in produtos_atualizados:
            produto['subreddits_com_pontuacao'] = sorted(
                produto.get('subreddits_com_pontuacao', []),
                key=lambda x: x.get('engajamento', 0),
                reverse=True
            )

        logging.debug(f"[DEBUG] Produtos processados com sucesso: {produtos_atualizados}")
        return jsonify({"produtos": produtos_atualizados}), 200
    except Exception as e:
        logging.error(f"[ERRO] Falha ao processar análise com Reddit: {e}")
        return jsonify({"erro": "Erro ao processar análise com Reddit."}), 500







@app.route("/analisar", methods=["POST"])
def analisar():
    try:
        nicho = request.form.get("nicho", "Nicho Não Informado")
        logging.debug(f"Nicho recebido: {nicho}")

        # Coletar dados dos produtos
        produtos = []
        for i in range(1, 6):  # Até 5 produtos
            nome_produto = request.form.get(f"nome_produto_{i}", "").strip()
            if not nome_produto:
                continue
            url_produto = request.form.get(f"url_produto_{i}", "").strip()
            categoria_produto = request.form.get(f"categoria_produto_{i}", "").strip()

            # Calcular pontuação de Redes Sociais
            pontuacao_redes = calcular_redes_sociais(request.form, i)
            logging.debug(f"Pontuação Redes Sociais para produto {i}: {pontuacao_redes}")

            # Processar o produto
            produto = processar_produto(
                index=i,
                nome_produto=nome_produto,
                url_produto=url_produto,
                permissao_trafego_pago=True,
                permissao_fundo_funil=True,
                form_data=request.form,
                categoria_produto=categoria_produto,
                tabela_ctr=tabela_ctr,
                pontuacao_redes_sociais=pontuacao_redes  # Certifique-se de incluir este parâmetro
            )

            if produto:
                produtos.append(produto)

        if not produtos:
            logging.error("Nenhum produto fornecido.")
            return render_template("index.html", error="Nenhum produto fornecido.")

        # Ordenar produtos por pontuação
        produtos = sorted(produtos, key=lambda p: p.get("pontuacao_total", 0), reverse=True)

        # Gerar frases
        frases_custo_beneficio = gerar_frases_custo_beneficio(produtos)
        frases_pontuacao_total = gerar_frases_pontuacao_total(produtos)
        frases_conclusao = gerar_frases_conclusao(produtos)
        

        # Renderizar o template
        return render_template(
            "analisar.html",
            nicho=nicho,
            produtos=produtos,
            frases_custo_beneficio=frases_custo_beneficio,
            frases_pontuacao_total=frases_pontuacao_total,
            frases_conclusao=frases_conclusao,
        )
    except Exception as e:
        logging.error(f"Erro ao processar a análise: {e}")
        
        return "Erro ao processar a análise.", 500

# FIM CRITERIO 11 - ENGAJAMENTO SOCIAL - REDDIT







# INÍCIO CRITÉRIO 12 - REDES SOCIAIS - INSTAGRAM, FACEBOOK E YOUTUBE
# Função para calcular pontuação de Redes Sociais
def calcular_redes_sociais(form_data, produto_index):
    try:
        # Capturar dados das redes sociais do formulário
        instagram_presente = form_data.get(f"instagram_presente_{produto_index}", "nao") == "sim"
        facebook_presente = form_data.get(f"facebook_presente_{produto_index}", "nao") == "sim"
        youtube_presente = form_data.get(f"youtube_presente_{produto_index}", "nao") == "sim"

        instagram_postagem = form_data.get(f"instagram_postagem_{produto_index}", "nao") == "sim"
        facebook_postagem = form_data.get(f"facebook_postagem_{produto_index}", "nao") == "sim"
        youtube_postagem = form_data.get(f"youtube_postagem_{produto_index}", "nao") == "sim"

        engajamento = form_data.get(f"engajamento_{produto_index}", "baixo")



        # Inicializa a pontuação
        pontuacao = 0

        # Presença nas redes sociais (até 1.5 pontos)
        redes_presente = sum([
            0.5 if instagram_presente else 0,
            0.5 if facebook_presente else 0,
            0.5 if youtube_presente else 0
        ])
        pontuacao += redes_presente

        # Postagens recentes (até 1.0 ponto)
        postagens_recentes = sum([
            0.3 if instagram_postagem else 0,
            0.3 if facebook_postagem else 0,
            0.3 if youtube_postagem else 0
        ])
        pontuacao += postagens_recentes

        # Engajamento (até 1.5 pontos)
        if engajamento == "baixo":
            pontuacao += 0
        elif engajamento == "medio":
            pontuacao += 0.8
        elif engajamento == "alto":
            pontuacao += 1.5

        # Limita a pontuação máxima
        pontuacao = min(pontuacao, 4)

        return round(pontuacao, 2)


        logging.debug(f"Pontuação calculada para produto {produto_index}: {pontuacao}")
        return pontuacao

    except Exception as e:
        logging.error(f"Erro ao calcular pontuação de Redes Sociais: {e}")
        return 0





# FIM CRITERIO 12 - REDES SOCIAIS - INSTAGRAM, FACEBOOK E YOUTUBE





# FUNÇÃO BASE DO CODIGO
def processar_produto(index, nome_produto, url_produto, permissao_trafego_pago,
                      permissao_fundo_funil, form_data, categoria_produto, tabela_ctr,
                      pontuacao_redes_sociais):
    """
    Processa as informações de um produto, calculando pontuações e validando dados.
    """
    palavras = form_data.getlist(f'palavra-chave_{index}[]')
    volumes = form_data.getlist(f'volume_{index}[]')
    cpcs = form_data.getlist(f'cpc_{index}[]')

    palavras_chave = []
    cpcs_lista = []
    for palavra, volume, cpc in zip(palavras, volumes, cpcs):
        try:
            logging.debug(f"Processando palavra-chave: {palavra}, volume: {volume}, cpc: {cpc}")
            cpc = cpc.replace(',', '.')  # Substitui vírgulas por pontos
            cpc_value = float(cpc)
            volume_value = int(volume)
            palavras_chave.append({
                'palavra': palavra.strip(),
                'volume': volume_value,
                'cpc': cpc_value
            })
            if cpc_value > 0:
                cpcs_lista.append(cpc_value)
        except ValueError:
            logging.error(f"Erro ao converter cpc '{cpc}' ou volume '{volume}' para número.")
            continue

    # Cálculo dos CPCs
    cpcs_formatted = formatar_cpcs(cpcs_lista)
    avg_cpc = sum(cpcs_lista) / len(cpcs_lista) if cpcs_lista else 0

    # Calcular outros critérios
    pontuacao_qualidade_pagina = calcular_qualidade_pagina(url_produto)
    pontuacao_copywriting = calcular_copywriting(url_produto)
    pontuacao_beneficios_ofertas = calcular_beneficios_ofertas(url_produto)
    pontuacao_preco_valor_percebido, feedback_preco_valor = preco_valor_percebido_pontuacao(url_produto, categoria_produto)
    pontuacao_faixa_precos = calcular_faixa_precos(url_produto)
    pontuacao_sazonalidade, descricao_sazonalidade = analisar_sazonalidade(nome_produto)

    # Calcular pontuação de SEO e palavras-chave
    pontuacao_seo_palavras, detalhes_seo = calcular_pontuacao_seo(
        palavras_chave, permissao_trafego_pago, permissao_fundo_funil, nome_produto, url_produto, categoria_produto
    )

    # Validar categoria e calcular CTR ponderado
    categoria_valida = validar_categoria(categoria_produto, tabela_ctr)
    if not categoria_valida:
        logging.error(f"Produto {index} ignorado: Categoria inválida.")
        return None

    if not palavras_chave:
        logging.error("Nenhuma palavra-chave válida foi fornecida. O cálculo de CTR será ignorado.")
        nota_ctr_ponderado = 0
        descricao_ctr = "Nenhuma palavra-chave válida para análise de CTR."
    else:
        nota_ctr_ponderado = calcular_ctr_ponderado(
            categoria=categoria_valida,
            palavras_chave=palavras_chave,
            nome_do_produto=nome_produto,
            permissao_fundo_funil=permissao_fundo_funil,
            pontuacao_seo_basico=detalhes_seo['pontuacao_seo_basico']
        )
        descricao_ctr = analisar_ctr(nota_ctr_ponderado)

    # Monta o dicionário do produto
    produto = {
        "nome": nome_produto,
        "url": url_produto,
        "categoria": categoria_valida,
        "pontuacao_qualidade_pagina": round(pontuacao_qualidade_pagina, 2),
        "pontuacao_copywriting": round(pontuacao_copywriting, 2),
        "pontuacao_beneficios_ofertas": round(pontuacao_beneficios_ofertas, 2),
        "pontuacao_preco_valor_percebido": round(pontuacao_preco_valor_percebido, 2),
        "feedback_preco_valor": feedback_preco_valor,
        "pontuacao_faixa_precos": round(pontuacao_faixa_precos, 2),
        "pontuacao_sazonalidade": round(pontuacao_sazonalidade, 2),
        "descricao_sazonalidade": descricao_sazonalidade,
        "pontuacao_seo_palavras": round(pontuacao_seo_palavras, 2),
        "pontuacao_permissao": round(detalhes_seo['pontuacao_permissao'], 2),
        "pontuacao_volume_busca": round(detalhes_seo['pontuacao_volume_busca'], 2),
        "pontuacao_concorrencia_cpc": round(detalhes_seo['pontuacao_concorrencia_cpc'], 2),
        "pontuacao_keyword": round(detalhes_seo['pontuacao_keyword'], 2),
        "pontuacao_seo_basico": round(detalhes_seo['pontuacao_seo_basico'], 2),
        "pontuacao_ctr": round(nota_ctr_ponderado, 2),
        "descricao_ctr": descricao_ctr,
        "avg_cpc": round(avg_cpc, 2),
        "palavras_chave": palavras_chave,
        "permissao_trafego_pago": permissao_trafego_pago,
        "permissao_fundo_funil": permissao_fundo_funil,
        "cpc_alertas": detalhes_seo.get('cpc_alertas', []),
        "cpcs": cpcs_formatted,
        "instagram_presente": form_data.get(f"instagram_presente_{index}", "nao"),
        "facebook_presente": form_data.get(f"facebook_presente_{index}", "nao"),
        "youtube_presente": form_data.get(f"youtube_postagem_{index}", "nao"),
        "pontuacao_redes_sociais": pontuacao_redes_sociais
    }

    # Calcular pontuação total corretamente
    produto["pontuacao_total"] = round(
        produto["pontuacao_qualidade_pagina"] +
        produto["pontuacao_copywriting"] +
        produto["pontuacao_beneficios_ofertas"] +
        produto["pontuacao_preco_valor_percebido"] +
        produto["pontuacao_faixa_precos"] +
        produto["pontuacao_sazonalidade"] +
        produto["pontuacao_seo_palavras"] +
        produto["pontuacao_ctr"] +
        produto["pontuacao_redes_sociais"],
        2
    )

    # Calcula a nota final incluindo CTR
    produto["nota_final"] = calcular_nota_final(produto, tabela_ctr)

    logging.debug(f"Produto processado: {produto}")
    return produto




@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        nicho = request.form.get("nicho", "")
        produtos = []

        for i in range(1, 6):
            nome_produto = request.form.get(f"nome_produto_{i}", "").strip()
            if not nome_produto:
                    continue
            print(f"Produto {i} - Nome: {nome_produto}")

            url_produto = request.form.get(f"url_produto_{i}", "").strip()
            categoria_produto = request.form.get(f"categoria_produto_{i}", "").strip()

            # Calcular pontuação de Redes Sociais
            pontuacao_redes = calcular_redes_sociais(request.form, i)


            if nome_produto and url_produto:
                permissao_trafego_pago = request.form.get(f"permissao_trafego_pago_{i}", "true") == "true"
                permissao_fundo_funil = request.form.get(f"permissao_fundo_funil_{i}", "true") == "true"
                categoria_produto = request.form.get(f"categoria_produto_{i}", "").strip()

                produto = processar_produto(
                    index=i,
                    nome_produto=nome_produto,
                    url_produto=url_produto,
                    permissao_trafego_pago=True,
                    permissao_fundo_funil=True,
                    form_data=request.form,
                    categoria_produto=categoria_produto,
                    tabela_ctr=tabela_ctr,  # Certifique-se de que 'tabela_ctr' está definido
                    pontuacao_redes_sociais=pontuacao_redes  # Adicionado
                )


                if produto:  # Certifique-se de adicionar apenas produtos válidos
                    produtos.append(produto)

        # **Adicione aqui o filtro para remover produtos sem nome**
        produtos = [produto for produto in produtos if produto.get("nome")]

        # Aplica o arredondamento globalmente após o processamento
        produtos = [arredondar_valores(produto, 2) for produto in produtos]

        # Ordena os produtos com base na pontuação total antes de renderizar
        produtos = sorted(produtos, key=lambda x: x.get("pontuacao_total", 0), reverse=True)

        # Renderiza a página de resultados com os produtos processados
        return render_template("analisar.html", nicho=nicho, produtos=produtos)

    # Exibe a página inicial se o método for GET
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5001)


