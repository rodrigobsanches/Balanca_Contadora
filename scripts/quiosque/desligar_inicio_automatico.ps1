# Desfaz o ligar_inicio_automatico: o app deixa de abrir sozinho no login da conta.
# Rodar pelo desligar_inicio_automatico.cmd.

param([string]$Conta = "")
$ErrorActionPreference = "Stop"
. (Join-Path $PSScriptRoot "_comum_inicio.ps1")

try {
    $usuario = Escolher-Conta $Conta
    No-RegistroDaConta $usuario {
        param($chave)
        Remove-ItemProperty -Path $chave -Name $NOME_ENTRADA -ErrorAction SilentlyContinue
    }
    Write-Host ""
    Write-Host "OK: o app nao abre mais sozinho na conta '$($usuario.Name)'." -ForegroundColor Green
}
catch {
    Write-Host "FALHOU: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
