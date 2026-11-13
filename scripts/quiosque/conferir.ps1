# Confere a balanca ANTES de ligar o modo quiosque. SO LE: nao muda nada.
#
# Fica em <pasta do app>\manutencao\. Rodar pelo conferir.cmd (pede administrador).
# O resultado tambem vai para manutencao\conferir_resultado.txt.
#
# (sem acentos de proposito: o PowerShell 5.1 le .ps1 sem BOM como ANSI)

$ErrorActionPreference = "Continue"
$Raiz = Split-Path $PSScriptRoot -Parent
try { Start-Transcript -Path (Join-Path $PSScriptRoot "conferir_resultado.txt") -Force | Out-Null } catch { }

function Secao($t) { Write-Host ""; Write-Host "=== $t" -ForegroundColor Cyan }
function Item($t)  { Write-Host "  $t" }

try {
    Secao "1. Windows"
    $os = Get-CimInstance Win32_OperatingSystem
    Item "$($os.Caption)  build $($os.BuildNumber)"
    $ehAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
    Item "rodando como administrador: $ehAdmin   (conta atual: $env:USERNAME)"

    Secao "2. Recursos de quiosque do Windows"
    if ($ehAdmin) {
        foreach ($nome in @("Client-EmbeddedShellLauncher", "Client-KeyboardFilter")) {
            $r = Get-WindowsOptionalFeature -Online -FeatureName $nome -ErrorAction SilentlyContinue
            if ($r) { Item "$nome : $($r.State)" } else { Item "$nome : NAO EXISTE nesta edicao" }
        }
    }
    else { Item "(precisa de administrador para consultar)" }

    Secao "3. Login automatico e shell padrao"
    $wl = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Winlogon"
    Item "AutoAdminLogon : $($wl.AutoAdminLogon)"
    Item "DefaultUserName: $($wl.DefaultUserName)"
    Item "Shell (todas as contas): $($wl.Shell)"

    Secao "4. Contas locais"
    $admins = @(Get-LocalGroupMember -SID "S-1-5-32-544" -ErrorAction SilentlyContinue | ForEach-Object { ($_.Name -split "\\")[-1] })
    foreach ($u in Get-LocalUser) {
        $papel = if ($admins -contains $u.Name) { "administrador" } else { "comum" }
        Item ("{0,-16} habilitada={1,-5} {2}" -f $u.Name, $u.Enabled, $papel)
    }

    Secao "5. Shell Launcher ja configurado?"
    try {
        $hab = Invoke-CimMethod -Namespace root\standardcimv2\embedded -ClassName WESL_UserSetting -MethodName IsEnabled -ErrorAction Stop
        Item "habilitado: $($hab.Enabled)"
        $config = @(Get-CimInstance -Namespace root\standardcimv2\embedded -ClassName WESL_UserSetting -ErrorAction Stop)
        if ($config.Count -eq 0) { Item "nenhuma conta com shell proprio" }
        foreach ($c in $config) {
            $nome = try { (New-Object Security.Principal.SecurityIdentifier($c.Sid)).Translate([Security.Principal.NTAccount]).Value } catch { $c.Sid }
            Item "$nome -> $($c.Shell)  (acao ao fechar: $($c.DefaultAction))"
        }
    }
    catch { Item "nao configurado (ou recurso ainda nao habilitado)" }

    Secao "6. O que abre sozinho no login (deixa de abrir na conta do quiosque)"
    foreach ($chave in @("HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
                         "HKLM:\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Run",
                         "HKCU:\SOFTWARE\Microsoft\Windows\CurrentVersion\Run")) {
        $p = Get-ItemProperty $chave -ErrorAction SilentlyContinue
        if ($p) {
            $p.PSObject.Properties | Where-Object { $_.Name -notlike "PS*" } |
                ForEach-Object { Item "[$($chave.Split(':')[0])] $($_.Name) = $($_.Value)" }
        }
    }
    $pastas = @("$env:ProgramData\Microsoft\Windows\Start Menu\Programs\Startup") +
              (Get-ChildItem "$env:SystemDrive\Users" -Directory -ErrorAction SilentlyContinue |
               ForEach-Object { Join-Path $_.FullName "AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup" })
    foreach ($pasta in $pastas) {
        Get-ChildItem $pasta -File -ErrorAction SilentlyContinue | Where-Object { $_.Name -ne "desktop.ini" } |
            ForEach-Object { Item "[Inicializar] $($_.FullName)" }
    }

    Secao "7. Arquivos do app"
    foreach ($f in @("python\pythonw.exe", "app\main.py", "app\config.json")) {
        $caminho = Join-Path $Raiz $f
        Item ("{0,-22} {1}" -f $f, $(if (Test-Path $caminho) { "ok" } else { "FALTANDO" }))
    }
    Write-Host ""
    Write-Host "Nada foi alterado. Resultado salvo em manutencao\conferir_resultado.txt" -ForegroundColor Green
}
finally { try { Stop-Transcript | Out-Null } catch { } }
