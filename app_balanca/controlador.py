"""Regras do fluxo de uso da balanca (sem tela).

As telas so chamam os metodos daqui e escutam os avisos. Assim o fluxo inteiro
pode ser testado no PC com pytest, sem abrir janela nenhuma.

Avisos enviados para a tela (avisar(tipo, info)):
  "conexao"      info = {"conectado": bool, "porta": str|None}
  "status"       info = evento status da ESP32 (wifi, fila...)
  "presenca"     info = {"perto": bool}
  "login"        info = {"uid", "nome"}
  "verificando"  info = {"uid"} (chaveiro fora da copia local: buscando cadastros novos)
  "desconhecido" info = {"uid"}
  "logout"       info = None
  "cadastros"    info = None (chegou um sync novo)
  "envio"        info = {"id", "status"} (um registro mudou de estado)
  "log"          info = {"msg"}
"""
import uuid

from dados_locais import DadosLocais, agora_iso
from contagem import conferir

SERVIDOR_AGORA = {".sv": "timestamp"}  # o Firebase troca pela hora do servidor


class Controlador:
    def __init__(self, config, dados: DadosLocais, enviar_esp32, avisar=None,
                 gerar_id=None, relogio=None):
        self.config = config
        self.dados = dados
        self.enviar_esp32 = enviar_esp32          # funcao(dict) -> bool
        self.avisar = avisar or (lambda tipo, info: None)
        self.gerar_id = gerar_id or (lambda: str(uuid.uuid4()))
        self.relogio = relogio or agora_iso
        self.id_balanca = config.get("id_balanca", "BAL-01")
        self.operador = None                       # {"uid", "nome"} de quem esta logado
        self.esp32_conectada = False
        self.status_esp32 = {}
        self.wifi = None                           # ultimo estado de Wi-Fi informado pela ESP32
        self._uid_aguardando_sync = None           # chaveiro desconhecido esperando cadastros novos

    # ================= eventos da ESP32 =================
    def ao_conexao(self, conectado, porta=None):
        self.esp32_conectada = conectado
        self.avisar("conexao", {"conectado": conectado, "porta": porta})
        if conectado:
            self.ao_ficar_pronta()

    def ao_ficar_pronta(self):
        """ESP32 conectou ou reiniciou: pede os cadastros e reenvia o que ficou pendente."""
        self.enviar_esp32({"c": "sync"})
        self.reenviar_pendentes()

    def tratar_evento(self, ev):
        tipo = ev.get("t")
        if tipo == "hello":
            self.ao_ficar_pronta()
        elif tipo == "rfid":
            self.identificar(ev.get("uid", ""))
        elif tipo == "presenca":
            self.avisar("presenca", {"perto": bool(ev.get("perto"))})
        elif tipo == "ack":
            self._tratar_ack(ev)
        elif tipo == "sync":
            self._tratar_sync(ev)
        elif tipo == "status":
            self.status_esp32 = ev
            wifi_agora = bool(ev.get("wifi"))
            if wifi_agora and not self.wifi:
                # a internet acabou de voltar: busca os cadastros mais novos
                self.enviar_esp32({"c": "sync"})
            self.wifi = wifi_agora
            self.avisar("status", ev)
        elif tipo == "log":
            self.avisar("log", {"msg": ev.get("msg", "")})

    def _tratar_sync(self, ev):
        if not ev.get("ok", True):
            self.avisar("log", {"msg": "Sem sync: %s (usando os dados guardados)" % ev.get("erro")})
        else:
            for tipo in ("operadores", "produtos", "pedidos"):
                self.dados.salvar_cadastros(tipo, ev.get(tipo) or {})
            self.wifi = True   # sync deu certo: a internet esta ok (evita pedir de novo)
            self.avisar("cadastros", None)
        # um chaveiro esperava os cadastros novos: decide agora (cadastrado ou desconhecido)
        uid = self._uid_aguardando_sync
        if uid:
            self._uid_aguardando_sync = None
            self._identificar_com_cadastro_atual(uid)

    def _tratar_ack(self, ev):
        id_ = ev.get("id")
        if not id_ or self.dados.registro(id_) is None:
            return
        if ev.get("ok"):
            status = "enviado"
        elif ev.get("fila"):
            status = "fila"
        else:
            status = "erro"
        self.dados.marcar(id_, status, ev.get("erro"))
        self.avisar("envio", {"id": id_, "status": status})

    # ================= operador (chaveiro) =================
    def identificar(self, uid):
        """Devolve True (logou), False (desconhecido) ou None (conferindo na nuvem).
        Chaveiro que nao esta na copia local: antes de recusar, pede os cadastros
        mais novos (alguem pode ter acabado de cadastra-lo no Firebase)."""
        if self._operador_valido(uid):
            return self._identificar_com_cadastro_atual(uid)
        if self.wifi and self._uid_aguardando_sync != uid:
            self._uid_aguardando_sync = uid
            self.enviar_esp32({"c": "sync"})
            self.avisar("verificando", {"uid": uid})
            return None
        # sem internet, ou encostou de novo enquanto esperava: decide com o que tem
        self._uid_aguardando_sync = None
        return self._identificar_com_cadastro_atual(uid)

    def _operador_valido(self, uid):
        operador = self.dados.cadastro("operadores", uid)
        if operador and operador.get("ativo", True) not in (False, "false"):
            return operador
        return None

    def _identificar_com_cadastro_atual(self, uid):
        operador = self._operador_valido(uid)
        if operador:
            self.operador = {"uid": uid, "nome": operador.get("nome", uid)}
            self.sinal("ok")
            self.avisar("login", self.operador)
            return True
        self.sinal("erro")
        self._operacao("put", "rfid_desconhecidos/" + uid,
                       {"uid": uid, "visto_em": SERVIDOR_AGORA, "balanca": self.id_balanca})
        self.avisar("desconhecido", {"uid": uid})
        return False

    def sair(self):
        self.operador = None
        self.sinal("ocioso")
        self.avisar("logout", None)

    def sinal(self, estado):
        self.enviar_esp32({"c": "sinal", "estado": estado})

    # ================= envio para a nuvem =================
    def _operacao(self, op, path, dados, id_=None):
        """Guarda no PC e manda para a ESP32. Se ela nao estiver ligada, fica pendente."""
        id_ = id_ or self.gerar_id()
        self.dados.novo_registro(id_, op, path, dados)
        self._mandar(id_, op, path, dados)
        return id_

    def _mandar(self, id_, op, path, dados):
        comando = "enviar" if op == "put" else "atualizar"
        return self.enviar_esp32({"c": comando, "id": id_, "path": path, "dados": dados})

    def reenviar_pendentes(self):
        for r in self.dados.pendentes():
            if not self._mandar(r["id"], r["op"], r["path"], r["dados"]):
                break  # ESP32 saiu de novo: tenta na proxima conexao

    # ================= cadastros =================
    def produtos(self):
        return self.dados.cadastros("produtos")

    def pedidos_pendentes(self):
        return {k: v for k, v in self.dados.cadastros("pedidos").items()
                if v.get("status", "pendente") == "pendente"}

    def salvar_peso_unitario(self, codigo, peso_unit_g):
        """'Usar e salvar no cadastro' da tela de amostra."""
        campos = {"peso_unit_g": round(peso_unit_g, 4)}
        self.dados.atualizar_cadastro("produtos", codigo, campos)
        self._operacao("patch", "produtos/" + codigo, campos)

    # ================= contagens =================
    def _montar_registro(self, id_, modo, codigo, contagem, peso_total_g, tara_g,
                         peso_unit_g, metodo, pedido_id=None, esperada=None, conferencia=None):
        produto = self.dados.cadastro("produtos", codigo) or {}
        return {
            "id": id_,
            "ts_balanca": self.relogio(),
            "ts_servidor": SERVIDOR_AGORA,
            "balanca": self.id_balanca,
            "operador_uid": self.operador["uid"] if self.operador else None,
            "operador_nome": self.operador["nome"] if self.operador else None,
            "modo": modo,
            "produto": codigo,
            "produto_nome": produto.get("nome", codigo),
            "pedido_id": pedido_id,
            "peso_total_g": peso_total_g,
            "tara_g": tara_g,
            "peso_unit_g": round(peso_unit_g, 4),
            "metodo_peso_unit": metodo,
            "quantidade": contagem.quantidade,
            "quantidade_esperada": esperada,
            "resultado": conferencia.resultado if conferencia else "OK",
            "diferenca": conferencia.diferenca if conferencia else 0,
            "contagem_incerta": contagem.incerta,
        }

    def confirmar_inventario(self, codigo, contagem, peso_total_g, tara_g, peso_unit_g,
                             metodo="cadastro"):
        """Registra a contagem e SUBSTITUI o estoque do produto pela quantidade contada."""
        id_ = self.gerar_id()
        registro = self._montar_registro(id_, "inventario", codigo, contagem, peso_total_g,
                                         tara_g, peso_unit_g, metodo)
        self._operacao("put", "contagens/" + id_, registro, id_=id_)
        estoque = {"estoque_atual": contagem.quantidade}
        self.dados.atualizar_cadastro("produtos", codigo, estoque)
        self._operacao("patch", "produtos/" + codigo, estoque)
        self.sinal("ok")
        return registro

    def conferir_item(self, pedido_id, codigo, contagem, esperada, peso_total_g, tara_g,
                      peso_unit_g, metodo="cadastro"):
        """Registra a contagem de UM item do pedido e devolve (registro, ResultadoConferencia)."""
        resultado = conferir(contagem.quantidade, esperada)
        id_ = self.gerar_id()
        registro = self._montar_registro(id_, "conferencia", codigo, contagem, peso_total_g,
                                         tara_g, peso_unit_g, metodo, pedido_id=pedido_id,
                                         esperada=esperada, conferencia=resultado)
        self._operacao("put", "contagens/" + id_, registro, id_=id_)
        self.sinal("ok" if resultado.resultado == "OK" else "erro")
        return registro, resultado

    def finalizar_conferencia(self, pedido_id, registros):
        """Recebe os registros de todos os itens. Se todos deram OK: desconta o estoque
        e marca o pedido como conferido. Devolve True se o pedido foi liberado."""
        if not registros or any(r["resultado"] != "OK" for r in registros):
            self.sinal("erro")
            return False
        for r in registros:
            produto = self.dados.cadastro("produtos", r["produto"]) or {}
            novo = max(0, int(produto.get("estoque_atual", 0)) - r["quantidade"])
            self.dados.atualizar_cadastro("produtos", r["produto"], {"estoque_atual": novo})
            self._operacao("patch", "produtos/" + r["produto"], {"estoque_atual": novo})
        campos = {"status": "conferido",
                  "conferido_por": self.operador["nome"] if self.operador else None,
                  "conferido_em": SERVIDOR_AGORA}
        self.dados.atualizar_cadastro("pedidos", pedido_id, {"status": "conferido"})
        self._operacao("patch", "pedidos/" + pedido_id, campos)
        self.sinal("ok")
        return True
