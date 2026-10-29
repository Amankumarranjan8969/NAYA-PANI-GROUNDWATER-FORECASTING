# Run Verification Test Suite in PowerShell
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[ERROR] Virtual environment not found. Please run START_NAYA_PANI.ps1 first!" -ForegroundColor Red
    exit 1
}
& $venvPython (Join-Path $PSScriptRoot "test_digital_twin_and_rag.py")
