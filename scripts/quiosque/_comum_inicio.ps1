# Funcoes usadas por ligar_inicio_automatico.ps1 e desligar_inicio_automatico.ps1.
# A entrada fica no "Run" DA CONTA (HKCU\...\Run): so essa conta abre o app no login.
# Nao mexe no shell da balanca (o do fabricante continua sendo o shell).
# (sem acentos de proposito: o PowerShell 5.1 le .ps1 sem BOM como ANSI)

$NOME_ENTRADA = "BalancaContadora"
$CHAVE_RUN = "Software\Microsoft\Windows\CurrentVersion\Run"

function Escolher-Conta([string]$Conta) {
    if ($Conta) { return Get-LocalUser -Name $Conta }
    $auto = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon").DefaultUserName
    Write-Host "Contas: $((Get-LocalUser | Where-Object Enabled).Name -join ', ')"
    $Conta = Read-Host "Conta [Enter = $auto, a do login automatico]"
    if (-not $Conta) { $Conta = $auto }
    return Get-LocalUser -Name $Conta
}

function No-RegistroDaConta($Usuario, [scriptblock]$Acao) {
    # Conta logada: o registro dela ja esta aberto em HKU\<SID>. Senao, abre o NTUSER.DAT.
    $sid = $Usuario.SID.Value
    $ramo = "HKU\$sid"
    $abriuAqui = $false
    if (-not (Test-Path "Registry::$ramo")) {
        $perfil = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\$sid" -ErrorAction SilentlyContinue).ProfileImagePath
        if (-not $perfil) { throw "a conta '$($Usuario.Name)' ainda nao tem perfil (entre nela uma vez)" }
        $ramo = "HKU\BalancaContadora_tmp"
        & reg.exe load $ramo (Join-Path $perfil "NTUSER.DAT") | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "nao consegui abrir o registro da conta '$($Usuario.Name)'" }
        $abriuAqui = $true
    }
    try { & $Acao "Registry::$ramo\$CHAVE_RUN" }
    finally {
        if ($abriuAqui) {
            [GC]::Collect(); [GC]::WaitForPendingFinalizers()   # solta o registro antes de fechar
            & reg.exe unload $ramo | Out-Null
        }
    }
}
