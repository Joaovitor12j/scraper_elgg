# scraper_elgg

Conjunto de scrapers que alimentam automaticamente a rede social de egressos com produções acadêmicas e científicas dos usuários. Cada script coleta publicações de uma fonte diferente e entrega um JSON padronizado que é consumido pela plataforma Elgg.

## Visão geral

A rede de egressos permite que cada usuário vincule seus perfis acadêmicos (LinkedIn, Google Scholar e Lattes). Este repositório contém os scripts que fazem a coleta periódica dessas publicações. O fluxo típico é:

```
GitHub Actions (agendado) → scraper → JSON → API da plataforma Elgg
```

Três scrapers estão disponíveis:

| Script | Fonte | Método |
|--------|-------|--------|
| `scrapingdog-linkedIn.py` | LinkedIn | API ScrapingDog (modo premium) |
| `scrapingdog-academico.py` | Google Scholar | API ScrapingDog |
| `lattes.py` | Lattes CNPq | Selenium + BeautifulSoup |

---

## Pré-requisitos

- **Python 3.10+**
- **Google Chrome** instalado (para o scraper do Lattes; o ChromeDriver é baixado automaticamente pelo `webdriver-manager`)
- **Conta no ScrapingDog** com créditos disponíveis — necessária para os scrapers de LinkedIn e Google Scholar
  - Crie sua conta em [scrapingdog.com](https://scrapingdog.com) e copie a API key

---

## Setup

### 1. Crie e ative o ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```

### 3. Configure as variáveis de ambiente

```bash
cp .env.exemple .env
```

Edite o arquivo `.env` com seus valores:

```dotenv
SCRAPING_API_KEY="sua_chave_da_api_aqui"
SCRAPING_RATE_LIMIT_MS=1000
```

---

## Como executar

Todos os scripts escrevem o resultado em JSON no stdout. Redirecione para um arquivo se precisar persistir.

### LinkedIn

Coleta publicações do perfil LinkedIn filtrando apenas itens com as palavras `artigo` ou `article` no título ou descrição.

```bash
python scrapingdog-linkedIn.py \
  --user-guid "abc-123" \
  --profile-url "https://www.linkedin.com/in/nome-do-usuario"
```

| Argumento | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `--user-guid` | sim | Identificador do usuário na plataforma Elgg |
| `--profile-url` | sim | URL completa do perfil LinkedIn |

### Google Scholar

Busca publicações pelo nome do autor usando a sintaxe `author:"Nome Completo"` da API do Google Scholar.

```bash
python scrapingdog-academico.py \
  --user-guid "abc-123" \
  --author "Maria da Silva Santos"
```

| Argumento | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `--user-guid` | sim | Identificador do usuário na plataforma Elgg |
| `--author` | sim | Nome completo do autor conforme cadastrado no Scholar |

### Lattes CNPq

Acessa o currículo Lattes via navegador headless, aguarda o carregamento completo da página (elemento `#identificacao`) e extrai artigos das seções de produção bibliográfica.

```bash
python lattes.py \
  --user-guid "abc-123" \
  --url "https://lattes.cnpq.br/1234567890123456"
```

| Argumento | Obrigatório | Descrição |
|-----------|-------------|-----------|
| `--user-guid` | sim | Identificador do usuário na plataforma Elgg |
| `--url` | sim | URL completa do currículo Lattes |

> **Nota:** O ChromeDriver é baixado automaticamente na primeira execução pelo `webdriver-manager`. Certifique-se de que o Google Chrome está instalado no sistema.

---

## Contrato de saída JSON

Todos os scripts produzem o mesmo formato de saída:

```json
{
  "user_guid": "abc-123",
  "source": "linkedin | google_scholar | lattes",
  "items": [
    {
      "title": "Título da publicação",
      "body": "Resumo ou descrição da publicação",
      "published_at": "2023",
      "source_url": "https://link-para-a-publicacao.com"
    }
  ]
}
```

### Exemplo real (Google Scholar)

```json
{
  "user_guid": "egresso-0042",
  "source": "google_scholar",
  "items": [
    {
      "title": "Aprendizado de máquina aplicado ao diagnóstico de doenças raras",
      "body": "Este artigo apresenta uma abordagem baseada em redes neurais convolucionais...",
      "published_at": "2022",
      "source_url": "https://scholar.google.com/scholar?cluster=123456"
    },
    {
      "title": "Revisão sistemática sobre NLP em português brasileiro",
      "body": "Revisamos 87 artigos publicados entre 2015 e 2022...",
      "published_at": "2023",
      "source_url": "https://scholar.google.com/scholar?cluster=789012"
    }
  ]
}
```

Em caso de falha, o script ainda retorna um JSON válido com `items` vazio e imprime o erro no stderr:

```json
{
  "user_guid": "egresso-0042",
  "source": "google_scholar",
  "items": []
}
```

---

## Variáveis de ambiente

| Variável | Obrigatória | Padrão | Descrição |
|----------|-------------|--------|-----------|
| `SCRAPING_API_KEY` | Sim (LinkedIn e Scholar) | — | Chave de API do ScrapingDog |
| `SCRAPING_RATE_LIMIT_MS` | Não | `1000` | Pausa em milissegundos aplicada após cada requisição para evitar bloqueios por rate limiting |

---

## Uso via GitHub Actions

Os scrapers são projetados para serem executados por workflows do GitHub Actions de forma agendada (cron). Um workflow típico:

1. Faz checkout do repositório
2. Configura Python e instala dependências
3. Lê a lista de usuários e seus perfis a partir de uma fonte de dados (ex: API da plataforma ou variável de ambiente)
4. Executa o scraper correspondente para cada usuário
5. Envia o JSON resultante para o endpoint da plataforma Elgg

As variáveis `SCRAPING_API_KEY` e `SCRAPING_RATE_LIMIT_MS` devem ser configuradas como **Secrets/Variables** no repositório GitHub (`Settings > Secrets and variables > Actions`).

Exemplo de step no workflow:

```yaml
- name: Coletar publicações do Scholar
  env:
    SCRAPING_API_KEY: ${{ secrets.SCRAPING_API_KEY }}
    SCRAPING_RATE_LIMIT_MS: 1500
  run: |
    python scrapingdog-academico.py \
      --user-guid "${{ matrix.user_guid }}" \
      --author "${{ matrix.author_name }}" \
      > output_${{ matrix.user_guid }}.json
```

Para o scraper do Lattes em ambiente CI, certifique-se de que o runner possui o Google Chrome instalado ou adicione o step de instalação no workflow:

```yaml
- name: Instalar Google Chrome
  run: |
    wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
    sudo apt-get update
    sudo apt-get install -y google-chrome-stable
```
