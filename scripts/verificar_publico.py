"""Confere se algum arquivo que vai para o GitHub contém palavras proibidas.

As palavras ficam em privado/palavras_bloqueadas.txt (uma por linha), arquivo que
NÃO vai para o GitHub. Assim este script pode ser público sem revelar nada.

Uso (na raiz do projeto):  python scripts/verificar_publico.py
Rode sempre antes de cada commit.
"""
import pathlib
import subprocess
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
LISTA = RAIZ / "privado" / "palavras_bloqueadas.txt"


def arquivos_versionados():
    """Arquivos que o Git vai enviar (versionados + novos não ignorados)."""
    saida = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=RAIZ, capture_output=True, text=True, check=True,
    ).stdout
    return [RAIZ / linha for linha in saida.splitlines() if linha.strip()]


def main():
    if not LISTA.exists():
        print(f"Lista não encontrada: {LISTA}")
        return 1
    palavras = [p.strip().lower() for p in LISTA.read_text(encoding="utf-8").splitlines()
                if p.strip() and not p.startswith("#")]
    problemas = []
    for arquivo in arquivos_versionados():
        if not arquivo.is_file():
            continue
        try:
            texto = arquivo.read_text(encoding="utf-8", errors="ignore").lower()
        except OSError:
            continue
        nome = str(arquivo.relative_to(RAIZ)).lower()
        for palavra in palavras:
            if palavra in texto or palavra in nome:
                problemas.append((arquivo.relative_to(RAIZ), palavra))
    if problemas:
        print("ATENÇÃO: palavras proibidas encontradas em arquivos públicos:")
        for arquivo, palavra in problemas:
            print(f"  - {arquivo}: '{palavra}'")
        return 1
    print("OK: nenhum arquivo público contém palavras proibidas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
