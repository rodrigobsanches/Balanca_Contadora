"""Dados guardados no proprio PC da balanca (SQLite).

1. Copia local dos cadastros (operadores, produtos, pedidos), vinda do comando "sync".
   Assim o app funciona mesmo se a ESP32 ficar sem internet.
2. Registro de cada operacao enviada a nuvem, com o estado:
     pendente -> ainda sem resposta da ESP32 (o app reenvia quando ela voltar)
     fila     -> a ESP32 guardou na fila dela e cuida do reenvio
     enviado  -> gravado no Firebase
     erro     -> recusado (dados invalidos); nao e reenviado
"""
import json
import sqlite3
import threading
from datetime import datetime

TIPOS_CADASTRO = ("operadores", "produtos", "pedidos")


def agora_iso():
    return datetime.now().isoformat(timespec="seconds")


class DadosLocais:
    def __init__(self, arquivo="dados_locais.db"):
        # a thread da serial e a da tela usam o banco: uma trava evita conflito
        self._trava = threading.Lock()
        self._con = sqlite3.connect(arquivo, check_same_thread=False)
        self._con.row_factory = sqlite3.Row
        self._criar_tabelas()

    def _criar_tabelas(self):
        with self._trava, self._con:
            self._con.execute("""
                CREATE TABLE IF NOT EXISTS cadastros (
                    tipo TEXT NOT NULL, chave TEXT NOT NULL, dados TEXT NOT NULL,
                    PRIMARY KEY (tipo, chave))""")
            self._con.execute("""
                CREATE TABLE IF NOT EXISTS registros (
                    id TEXT PRIMARY KEY, op TEXT NOT NULL, path TEXT NOT NULL,
                    dados TEXT NOT NULL, status TEXT NOT NULL, erro TEXT,
                    criado_em TEXT NOT NULL, atualizado_em TEXT NOT NULL)""")

    def fechar(self):
        self._con.close()

    # ---------- cadastros ----------
    def salvar_cadastros(self, tipo, itens):
        """Substitui todos os cadastros de um tipo pelos que vieram do Firebase."""
        if tipo not in TIPOS_CADASTRO:
            raise ValueError("tipo de cadastro desconhecido: %s" % tipo)
        with self._trava, self._con:
            self._con.execute("DELETE FROM cadastros WHERE tipo = ?", (tipo,))
            self._con.executemany(
                "INSERT INTO cadastros (tipo, chave, dados) VALUES (?, ?, ?)",
                [(tipo, chave, json.dumps(valor, ensure_ascii=False))
                 for chave, valor in (itens or {}).items()])

    def cadastros(self, tipo):
        """Devolve {chave: dados} de um tipo."""
        with self._trava:
            linhas = self._con.execute(
                "SELECT chave, dados FROM cadastros WHERE tipo = ? ORDER BY chave", (tipo,)).fetchall()
        return {l["chave"]: json.loads(l["dados"]) for l in linhas}

    def cadastro(self, tipo, chave):
        with self._trava:
            linha = self._con.execute(
                "SELECT dados FROM cadastros WHERE tipo = ? AND chave = ?", (tipo, chave)).fetchone()
        return json.loads(linha["dados"]) if linha else None

    def atualizar_cadastro(self, tipo, chave, campos):
        """Muda alguns campos de um cadastro local (ex.: estoque depois de contar)."""
        atual = self.cadastro(tipo, chave) or {}
        atual.update(campos)
        with self._trava, self._con:
            self._con.execute(
                "INSERT OR REPLACE INTO cadastros (tipo, chave, dados) VALUES (?, ?, ?)",
                (tipo, chave, json.dumps(atual, ensure_ascii=False)))

    # ---------- registros enviados a nuvem ----------
    def novo_registro(self, id_, op, path, dados):
        agora = agora_iso()
        with self._trava, self._con:
            self._con.execute(
                "INSERT OR REPLACE INTO registros "
                "(id, op, path, dados, status, erro, criado_em, atualizado_em) "
                "VALUES (?, ?, ?, ?, 'pendente', NULL, ?, ?)",
                (id_, op, path, json.dumps(dados, ensure_ascii=False), agora, agora))

    def marcar(self, id_, status, erro=None):
        with self._trava, self._con:
            self._con.execute(
                "UPDATE registros SET status = ?, erro = ?, atualizado_em = ? WHERE id = ?",
                (status, erro, agora_iso(), id_))

    def registro(self, id_):
        with self._trava:
            linha = self._con.execute("SELECT * FROM registros WHERE id = ?", (id_,)).fetchone()
        return self._linha_para_dict(linha) if linha else None

    def pendentes(self):
        """Registros que a ESP32 ainda nao confirmou, na ordem em que foram criados."""
        with self._trava:
            linhas = self._con.execute(
                "SELECT * FROM registros WHERE status = 'pendente' "
                "ORDER BY criado_em, rowid").fetchall()
        return [self._linha_para_dict(l) for l in linhas]

    def contar_por_status(self):
        with self._trava:
            linhas = self._con.execute(
                "SELECT status, COUNT(*) AS n FROM registros GROUP BY status").fetchall()
        return {l["status"]: l["n"] for l in linhas}

    @staticmethod
    def _linha_para_dict(linha):
        d = dict(linha)
        d["dados"] = json.loads(d["dados"])
        return d
