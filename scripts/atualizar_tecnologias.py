
import os
import json
import base64
import re
import urllib.request
import urllib.error
from pathlib import Path
from urllib.parse import quote

USUARIO = os.environ["GITHUB_REPOSITORY_OWNER"]
TOKEN = os.environ["GITHUB_TOKEN"]

HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}"
}

def api(caminho):
    req = urllib.request.Request(
        "https://api.github.com" + caminho,
        headers=HEADERS
    )
    try:
        with urllib.request.urlopen(req) as resposta:
            return json.load(resposta)
    except urllib.error.HTTPError as erro:
        if erro.code == 404:
            return None
        raise

def arquivo(repo, caminho):
    nome = quote(repo, safe="")
    dados = api(
        f"/repos/{USUARIO}/{nome}/contents/{caminho}"
    )
    if not isinstance(dados, dict):
        return ""
    if dados.get("encoding") != "base64":
        return ""
    return base64.b64decode(
        dados["content"]
    ).decode("utf-8", errors="replace")

def detectar_frameworks(repo):
    encontrados = set()

    conteudo = arquivo(repo, "package.json")
    if conteudo:
        try:
            pacote = json.loads(conteudo)
            deps = {
                **pacote.get("dependencies", {}),
                **pacote.get("devDependencies", {})
            }
            mapa = {
                "react": "React",
                "next": "Next.js",
                "vue": "Vue.js",
                "vite": "Vite",
                "express": "Express",
                "tailwindcss": "Tailwind CSS",
                "@angular/core": "Angular",
                "@nestjs/core": "NestJS",
                "prisma": "Prisma",
                "@prisma/client": "Prisma"
            }
            for dependencia, nome in mapa.items():
                if dependencia in deps:
                    encontrados.add(nome)
        except (ValueError, TypeError):
            pass

    requisitos = arquivo(repo, "requirements.txt")
    for pacote, nome in {
        "django": "Django",
        "flask": "Flask",
        "fastapi": "FastAPI"
    }.items():
        if re.search(
            rf"(?im)^\s*{pacote}(?:\W|$)",
            requisitos
        ):
            encontrados.add(nome)

    if arquivo(repo, "Dockerfile"):
        encontrados.add("Docker")

    return sorted(encontrados)

# Ícones disponíveis em https://skillicons.dev
MAPA_ICONES = {
    "HTML": "html",
    "CSS": "css",
    "JavaScript": "js",
    "TypeScript": "ts",
    "Python": "py",
    "Shell": "bash",
    "Java": "java",
    "C": "c",
    "C++": "cpp",
    "C#": "cs",
    "Go": "go",
    "Rust": "rust",
    "PHP": "php",
    "Ruby": "ruby",
    "Kotlin": "kotlin",
    "Swift": "swift",
    "Dart": "dart",
    "SCSS": "sass",
    "Sass": "sass",
    "Lua": "lua",
    "R": "r",
    "Vue.js": "vue",
    "React": "react",
    "Next.js": "nextjs",
    "Vite": "vite",
    "Express": "express",
    "Tailwind CSS": "tailwind",
    "Angular": "angular",
    "NestJS": "nestjs",
    "Prisma": "prisma",
    "Django": "django",
    "Flask": "flask",
    "FastAPI": "fastapi",
    "Docker": "docker",
}

def mostrar_icones(tecnologias, vazio="—"):
    icones = list(dict.fromkeys(
        MAPA_ICONES[nome] for nome in tecnologias if nome in MAPA_ICONES
    ))
    sem_icone = [nome.replace("|", "\\|") for nome in tecnologias
                 if nome not in MAPA_ICONES]
    if not icones:
        return ", ".join(sem_icone) or vazio
    descricao = ", ".join(nome for nome in tecnologias if nome in MAPA_ICONES)
    imagem = (
        '<img src="https://skillicons.dev/icons?i='
        + ",".join(icones)
        + '" height="28" alt="' + descricao + '" />'
    )
    return " ".join([imagem] + sem_icone)


linhas = [
    "| Projeto | Linguagens | Tecnologias adicionais |",
    "|---|---|---|"
]

pagina = 1

while True:
    repos = api(
        f"/users/{USUARIO}/repos"
        f"?type=owner&per_page=100&page={pagina}"
    )

    if not repos:
        break

    for repo in repos:
        if repo["fork"] or repo["archived"]:
            continue

        nome = repo["name"]
        linguagens = api(
            f"/repos/{USUARIO}/{quote(nome, safe='')}/languages"
        ) or {}

        frameworks = detectar_frameworks(nome)

        titulo = nome.replace("|", "\\|")
        langs = mostrar_icones(list(linguagens), "Não detectadas")
        techs = mostrar_icones(frameworks)

        linhas.append(
            f"| [{titulo}]({repo['html_url']}) "
            f"| {langs} | {techs} |"
        )

    if len(repos) < 100:
        break
    pagina += 1

inicio = "<!-- TECNOLOGIAS:INICIO -->"
fim = "<!-- TECNOLOGIAS:FIM -->"

caminho = Path("README.md")
readme = caminho.read_text(encoding="utf-8")
tabela = "\n".join(linhas)

bloco = f"{inicio}\n{tabela}\n{fim}"

if inicio in readme and fim in readme:
    antes = readme.split(inicio)[0]
    depois = readme.split(fim, 1)[1]
    readme = antes + bloco + depois
else:
    readme = readme.rstrip() + "\n\n" + bloco + "\n"

caminho.write_text(readme, encoding="utf-8")
print("Tecnologias atualizadas com sucesso!")
