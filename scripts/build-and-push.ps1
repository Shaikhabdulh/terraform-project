param(
    [Parameter(Mandatory = $false)]
    [string]$Token = $env:DOCKER_PUSH_TOKEN,

    [string]$Username = "sah1",
    [string]$ImageTag = "sah1/practice:monitor-app"
)

$ErrorActionPreference = "Stop"

# Refresh PATH from Machine and User environment
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

$repoRoot = Resolve-Path "$PSScriptRoot\.."
$appDir = "$repoRoot\monitor-app"

if (-not $Token) {
    Write-Error "Docker Push Token required. Provide via -Token parameter or `$env:DOCKER_PUSH_TOKEN."
    exit 1
}

Write-Host "==> Authenticating with Docker Hub non-interactively as '$Username'..." -ForegroundColor Cyan
$Token | docker login -u $Username --password-stdin

Write-Host "==> Building '$ImageTag' from $appDir..." -ForegroundColor Cyan
docker build -t $ImageTag $appDir

Write-Host "==> Pushing '$ImageTag' to Docker Hub..." -ForegroundColor Cyan
docker push $ImageTag

Write-Host "==> Successfully pushed $ImageTag to Docker Hub!" -ForegroundColor Green
