# Script PowerShell para hacer push a GitHub usando la API REST
# Requiere: token de GitHub en variable $env:GITHUB_TOKEN

$owner = "pnavarro3"
$repo = "Proy_SistCiber"
$branch = "main"
$localPath = "c:\Users\pnavarro\Desktop\CodigoSC"

# Verificar token
if (-not $env:GITHUB_TOKEN) {
    Write-Host "Error: No se encontró GITHUB_TOKEN en variables de entorno"
    Write-Host "Configura: `$env:GITHUB_TOKEN = 'tu_token_aquí'"
    exit 1
}

# Función para hacer llamadas a GitHub API
function Invoke-GitHubAPI {
    param(
        [string]$Endpoint,
        [string]$Method = "GET",
        [object]$Body = $null
    )
    
    $headers = @{
        "Authorization" = "Bearer $env:GITHUB_TOKEN"
        "X-GitHub-Api-Version" = "2022-11-28"
        "Accept" = "application/vnd.github+json"
    }
    
    $uri = "https://api.github.com/repos/$owner/$repo/$endpoint"
    
    $params = @{
        Uri = $uri
        Method = $Method
        Headers = $headers
        ContentType = "application/json"
    }
    
    if ($Body) {
        $params.Body = $Body | ConvertTo-Json -Depth 10
    }
    
    Invoke-RestMethod @params
}

# Obtener el SHA del último commit (si existe)
try {
    $lastRef = Invoke-GitHubAPI "git/refs/heads/$branch" -ErrorAction SilentlyContinue
    $lastCommitSha = $lastRef.object.sha
    Write-Host "Último commit: $lastCommitSha"
} catch {
    $lastCommitSha = $null
    Write-Host "Primera vez, creando rama"
}

# Crear tree con todos los archivos
Write-Host "Preparando archivos..."
$treeItems = @()

Get-ChildItem -Path $localPath -Recurse -File | Where-Object {
    $_.FullName -notmatch "\.git" -and
    $_.FullName -notmatch "__pycache__" -and
    $_.FullName -notmatch "\.venv" -and
    $_.FullName -notmatch "\.pyc"
} | ForEach-Object {
    $content = [Convert]::ToBase64String([System.IO.File]::ReadAllBytes($_.FullName))
    $relativePath = $_.FullName.Replace($localPath, "").TrimStart("\")
    
    $treeItems += @{
        path = $relativePath
        mode = "100644"
        type = "blob"
        content = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($content))
    }
}

Write-Host "Total de archivos: $($treeItems.Count)"

if ($treeItems.Count -eq 0) {
    Write-Host "No hay archivos para subir"
    exit 1
}

# Crear tree
Write-Host "Creando tree..."
$treeBody = @{
    tree = $treeItems
    base_tree = $lastCommitSha
} | ConvertTo-Json -Depth 10

try {
    $tree = Invoke-GitHubAPI "git/trees" -Method POST -Body $treeBody
    $treeSha = $tree.sha
    Write-Host "Tree creado: $treeSha"
} catch {
    Write-Host "Error al crear tree: $_"
    exit 1
}

# Crear commit
Write-Host "Creando commit..."
$commitBody = @{
    message = "Initial commit: Reorganized project structure with documentation"
    tree = $treeSha
    parents = @()
} | ConvertTo-Json

if ($lastCommitSha) {
    $commitBody = @{
        message = "Initial commit: Reorganized project structure with documentation"
        tree = $treeSha
        parents = @($lastCommitSha)
    } | ConvertTo-Json
}

try {
    $commit = Invoke-GitHubAPI "git/commits" -Method POST -Body $commitBody
    $commitSha = $commit.sha
    Write-Host "Commit creado: $commitSha"
} catch {
    Write-Host "Error al crear commit: $_"
    exit 1
}

# Actualizar referencia de rama
Write-Host "Actualizando rama..."
$refBody = @{
    sha = $commitSha
    force = $false
} | ConvertTo-Json

try {
    Invoke-GitHubAPI "git/refs/heads/$branch" -Method PATCH -Body $refBody
    Write-Host "✓ Rama actualizada exitosamente"
} catch {
    try {
        Invoke-GitHubAPI "git/refs" -Method POST -Body @{
            ref = "refs/heads/$branch"
            sha = $commitSha
        }
        Write-Host "✓ Rama creada exitosamente"
    } catch {
        Write-Host "Error al actualizar rama: $_"
        exit 1
    }
}

Write-Host "Push completado!"
