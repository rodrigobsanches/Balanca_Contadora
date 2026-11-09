"""Gera a linha de um usuario do dashboard para colar no secrets.toml.

    .venv\\Scripts\\python dashboard\\gerar_senha.py

A senha e digitada sem aparecer na tela e nunca e gravada: so o hash vai para a linha.
"""
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from autenticacao import PERFIS, gerar_hash  # noqa: E402


def main():
    nome = input("Usuario (ex.: rodrigo): ").strip().lower()
    perfil = input("Perfil (%s) [leitura]: " % " / ".join(PERFIS)).strip().lower() or "leitura"
    if not nome or perfil not in PERFIS:
        sys.exit("Usuario vazio ou perfil invalido.")
    senha = getpass.getpass("Senha: ")
    if len(senha) < 8:
        sys.exit("Use pelo menos 8 caracteres.")
    if senha != getpass.getpass("Repita a senha: "):
        sys.exit("As senhas nao conferem.")
    print("\nCole esta linha no [usuarios] do dashboard/.streamlit/secrets.toml:\n")
    print('%s = { perfil = "%s", senha = "%s" }' % (nome, perfil, gerar_hash(senha)))


if __name__ == "__main__":
    main()
