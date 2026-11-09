# firebase.py - fala com o Firebase Realtime Database pela API REST (HTTPS)
#  1. Faz login com e-mail e senha (Firebase Authentication) e recebe um "token".
#  2. Usa o token em cada leitura/gravacao: .../caminho.json?auth=TOKEN
#  3. O token vale 1 hora: antes de vencer, renova com o "refresh token".
# Cada chamada demora 1 a 3 segundos e, nesse tempo, o laco principal espera.
import json
import time

try:
    import requests
except ImportError:
    import urequests as requests

URL_LOGIN = "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key="
URL_RENOVAR = "https://securetoken.googleapis.com/v1/token?key="
TIMEOUT_S = 10
MARGEM_RENOVACAO_S = 300  # renova 5 minutos antes de vencer

# Pastas do banco em que a ESP32 pode mexer (protege contra caminho errado vindo da serial)
RAIZES_PERMITIDAS = ("contagens", "produtos", "pedidos", "operadores",
                     "rfid_desconhecidos", "dispositivos")
CARACTERES_PERMITIDOS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-:/"


class ErroFirebase(Exception):
    """permanente=True: o problema e da propria operacao (ex.: dados recusados pelas
    regras de validacao). Tentar de novo nao adianta, entao ela sai da fila."""
    def __init__(self, mensagem, permanente=False):
        super().__init__(mensagem)
        self.permanente = permanente


def caminho_valido(caminho):
    """Aceita so caminhos como 'contagens/abc-123' dentro das pastas permitidas."""
    if not isinstance(caminho, str) or not caminho or caminho.startswith("/"):
        return False
    if ".." in caminho or "//" in caminho:
        return False
    for c in caminho:
        if c not in CARACTERES_PERMITIDOS:
            return False
    return caminho.split("/")[0] in RAIZES_PERMITIDAS


class Firebase:
    def __init__(self, api_key, url_banco, email, senha):
        self.api_key = api_key
        self.url_banco = url_banco.rstrip("/")
        self.email = email
        self.senha = senha
        self.token = None
        self.refresh_token = None
        self.vence_em = 0  # time.ticks_ms() em que o token deve ser renovado

    # ---------- login e token ----------
    def _guardar_token(self, token, refresh, expira_s):
        self.token = token
        self.refresh_token = refresh
        validade_ms = (int(expira_s) - MARGEM_RENOVACAO_S) * 1000
        self.vence_em = time.ticks_add(time.ticks_ms(), validade_ms)

    def login(self):
        corpo = {"email": self.email, "password": self.senha, "returnSecureToken": True}
        r = requests.post(URL_LOGIN + self.api_key, data=json.dumps(corpo),
                          headers={"Content-Type": "application/json"}, timeout=TIMEOUT_S)
        try:
            if r.status_code != 200:
                raise ErroFirebase("login recusado (%d): %s" % (r.status_code, r.text[:120]))
            d = r.json()
        finally:
            r.close()
        self._guardar_token(d["idToken"], d["refreshToken"], d["expiresIn"])

    def _renovar(self):
        corpo = "grant_type=refresh_token&refresh_token=" + self.refresh_token
        r = requests.post(URL_RENOVAR + self.api_key, data=corpo,
                          headers={"Content-Type": "application/x-www-form-urlencoded"},
                          timeout=TIMEOUT_S)
        try:
            if r.status_code != 200:
                raise ErroFirebase("renovacao recusada (%d)" % r.status_code)
            d = r.json()
        finally:
            r.close()
        self._guardar_token(d["id_token"], d["refresh_token"], d["expires_in"])

    def _garantir_token(self):
        if self.token is None:
            self.login()
        elif time.ticks_diff(self.vence_em, time.ticks_ms()) <= 0:
            try:
                self._renovar()
            except Exception:
                self.login()  # se a renovacao falhar, faz login de novo

    # ---------- leitura e gravacao ----------
    def _chamar(self, metodo, caminho, dados=None, tentativa=1):
        if not caminho_valido(caminho):
            raise ErroFirebase("caminho nao permitido: %s" % caminho, permanente=True)
        self._garantir_token()
        url = "%s/%s.json?auth=%s" % (self.url_banco, caminho, self.token)
        corpo = None if dados is None else json.dumps(dados)
        r = requests.request(metodo, url, data=corpo,
                             headers={"Content-Type": "application/json"}, timeout=TIMEOUT_S)
        try:
            status = r.status_code
            if status == 401 and tentativa == 1:
                # token recusado: faz login de novo e tenta mais uma vez
                self.token = None
            elif status != 200:
                # 400 = dados invalidos para as regras: nao adianta reenviar.
                # 401/403/5xx podem ser passageiros (token, regras, servidor): fica na fila.
                raise ErroFirebase("%s %s recusado (%d): %s" % (metodo, caminho, status, r.text[:120]),
                                   permanente=(status == 400))
            else:
                return r.json()
        finally:
            r.close()
        return self._chamar(metodo, caminho, dados, tentativa=2)

    def ler(self, caminho):
        return self._chamar("GET", caminho)

    def gravar(self, caminho, dados):
        """PUT: substitui tudo no caminho (usado em contagens/<id>, evita duplicar)."""
        return self._chamar("PUT", caminho, dados)

    def atualizar(self, caminho, dados):
        """PATCH: muda so os campos enviados (ex.: estoque_atual de um produto)."""
        return self._chamar("PATCH", caminho, dados)
