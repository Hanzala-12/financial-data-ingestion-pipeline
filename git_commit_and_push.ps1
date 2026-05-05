<#
Usage: Open PowerShell in the repo root and run:
  .\git_commit_and_push.ps1
Or provide a path to a commit message file:
  .\git_commit_and_push.ps1 -MessagePath COMMIT_MESSAGE.txt
#>
param(
    [string]$MessagePath = "COMMIT_MESSAGE.txt",
    [switch]$Force
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

function Fail($msg){ Write-Error $msg; exit 1 }

# Check git available
try{ git --version > $null 2>&1 } catch { Fail "Git is not available in PATH. Install Git or run these commands locally." }

Write-Host "Repository: $scriptDir" -ForegroundColor Cyan

Write-Host "Current git status:" -ForegroundColor Yellow
git status --porcelain --branch

if (-not $Force) {
    $confirm = Read-Host "Proceed to stage, commit, and push? (y/N)"
    if ($confirm -notin @('y','Y','yes','Yes')) { Write-Host "Aborted by user."; exit 0 }
}

# Stage all changes
git add -A

# Determine commit message
$commitArgs = @()
if (Test-Path $MessagePath) {
    Write-Host "Using commit message file: $MessagePath" -ForegroundColor Green
    $commitArgs += "-F"; $commitArgs += $MessagePath
} else {
    $msg = Read-Host "Commit message (single-line)"
    if ([string]::IsNullOrWhiteSpace($msg)) { Fail "Empty commit message." }
    $commitArgs += "-m"; $commitArgs += $msg
}

# Commit
Write-Host "Committing changes..." -ForegroundColor Yellow
$commitExit = (& git commit @commitArgs).ExitCode
if ($commitExit -ne 0) {
    Write-Host "git commit returned non-zero exit code ($commitExit). There may be no changes to commit or an error occurred." -ForegroundColor Red
    exit $commitExit
}

# Determine current branch
$branch = (git rev-parse --abbrev-ref HEAD).Trim()
if (-not $branch) { Fail "Unable to determine current branch." }

Write-Host "Pushing to origin/$branch..." -ForegroundColor Yellow
git push origin $branch
$pushExit = $LASTEXITCODE
if ($pushExit -ne 0) {
    Fail "git push failed with exit code $pushExit"
}

Write-Host "Push completed to origin/$branch" -ForegroundColor Green
exit 0
