param(
    [string]$Asm = "t_sum.asm",
    [string]$Login = "506278",
    [string]$Password = "ce9478b3-17b1-4137-a401-4af8bd1466d7"
)

$ErrorActionPreference = "Stop"

# Switch to script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

$Manager = "./Portable.RemoteTasks.Manager.exe"

# 1) Assemble
$assemble = & $Manager `
    -ul $Login `
    -up $Password `
    -s AssembleDebug `
    definitionFile "stack16.target.pdsl" `
    archName "stack16" `
    asmListing $Asm `
    sourcesDir "C:\Users\User\Downloads\parsing_grammar\architecture\"

$assembleText = $assemble | Out-String
Write-Host $assembleText

# Extract GUID
$guidRegex = [regex]"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
$guidMatch = $guidRegex.Match($assembleText)
if (-not $guidMatch.Success) {
    throw "GUID not found in assemble output"
}
$guid = $guidMatch.Value
Write-Host "GUID: $guid"

# 2) Download result
$download = & $Manager `
    -ul $Login `
    -up $Password `
    -g $guid `
    -r "out.ptptb" `
    -o "out_local.ptptb"

Write-Host $download
