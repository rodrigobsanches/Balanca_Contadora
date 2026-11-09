"""Login do dashboard: so entra quem tem usuario e senha.

As senhas NAO ficam guardadas: no secrets.toml fica so um "hash" (PBKDF2-SHA256 com sal),
uma impressao digital da senha da qual nao da para voltar a senha original.
Gere o hash com:  python dashboard/gerar_senha.py

secrets.toml:
    [usuarios]
    rodrigo = { perfil = "admin", senha = "pbkdf2_sha256$200000$<sal>$<hash>" }
    visitante = { perfil = "leitura", senha = "..." }

Perfis: "admin" ve tudo e altera Cadastros; "leitura" so consulta.
"""
import base64
import hashlib
import hmac
import os

ALGORITMO = "pbkdf2_sha256"
ITERACOES = 200_000
PERFIS = ("admin", "leitura")


def gerar_hash(senha, iteracoes=ITERACOES, sal=None):
    sal = sal or base64.b64encode(os.urandom(16)).decode()
    chave = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), sal.encode(), iteracoes)
    return "%s$%d$%s$%s" % (ALGORITMO, iteracoes, sal, base64.b64encode(chave).decode())


def conferir_senha(senha, guardado):
    """True se a senha bate com o hash guardado. Comparacao em tempo constante."""
    try:
        algoritmo, iteracoes, sal, _ = guardado.split("$", 3)
    except (AttributeError, ValueError):
        return False
    if algoritmo != ALGORITMO:
        return False
    return hmac.compare_digest(gerar_hash(senha, int(iteracoes), sal), guardado)


def autenticar(usuarios, nome, senha):
    """Devolve o perfil ('admin'/'leitura') se usuario e senha conferem; senao None."""
    dados = (usuarios or {}).get((nome or "").strip().lower())
    if not dados or not conferir_senha(senha or "", dados.get("senha", "")):
        return None
    perfil = dados.get("perfil", "leitura")
    return perfil if perfil in PERFIS else "leitura"
