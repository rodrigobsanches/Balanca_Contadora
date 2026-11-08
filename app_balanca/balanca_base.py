"""Interface comum para qualquer balanca usada pelo app.

O app so conversa com esta interface. Assim ele funciona igual com:
- a balanca simulada (para desenvolver e testar no PC);
- o adaptador da balanca real, que fica em balanca_privada/ (fora do GitHub).
"""


class Balanca:
    nome = "balanca"

    def conectar(self):
        """Abre a comunicacao. Devolve True se deu certo."""
        raise NotImplementedError

    def desconectar(self):
        raise NotImplementedError

    def peso_estavel_g(self):
        """Peso em gramas quando estavel; None enquanto o peso esta mudando."""
        raise NotImplementedError

    def tarar(self):
        """Faz a tara com o que esta no prato. Devolve True se deu certo."""
        raise NotImplementedError

    def zerar(self):
        raise NotImplementedError

    def divisao_g(self):
        """Menor variacao que a balanca mostra, em gramas (ex.: 2 ou 5)."""
        raise NotImplementedError


def criar_balanca(config):
    """Escolhe a balanca conforme o config.

    config["balanca"] == "local"  -> tenta o adaptador privado (balanca_privada/adaptador.py)
    qualquer outro valor           -> balanca simulada
    """
    if config.get("balanca") == "local":
        try:
            from balanca_privada.adaptador import BalancaLocal
            return BalancaLocal(config)
        except ImportError:
            print("Adaptador local nao encontrado. Usando balanca simulada.")
    from balanca_simulada import BalancaSimulada
    return BalancaSimulada(divisao=config.get("divisao_simulada_g", 1))
