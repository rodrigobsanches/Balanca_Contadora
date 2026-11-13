# Faz o app da balanca abrir sozinho no login da conta escolhida (padrao: a do login
# automatico). Nao troca o shell: so acrescenta uma entrada de inicializacao nessa conta.
# Rodar pelo ligar_inicio_automatico.cmd. Desfazer: desligar_inicio_automatico.cmd.

param([string]$Conta = "")
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_comum_inicio.ps1")

try {
    $Raiz = Split-Path $PSScriptRoot -Parent
    $pythonw = Join-Path $Raiz "python\pythonw.exe"
    $main = Join-Path $Raiz "app\main.py"
    foreach ($f in @($pythonw, $main)) { if (-not (Test-Path $f)) { throw "nao achei $f" } }
    $comando = "`"$pythonw`" -s `"$main`""

    $usuario = Escolher-Conta $Conta
    No-RegistroDaConta $usuario {
        param($chave)
        if (-not (Test-Path $chave)) { New-Item -Path $chave -Force | Out-Null }
        New-ItemProperty -Path $chave -Name $NOME_ENTRADA -Value $comando -PropertyType String -Force | Out-Null
    }
    Write-Host ""
    Write-Host "OK: o app abre sozinho no login da conta '$($usuario.Name)'." -ForegroundColor Green
    Write-Host "    $comando"
    Write-Host "Reinicie a balanca para testar."
}
catch {
    Write-Host "FALHOU: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
