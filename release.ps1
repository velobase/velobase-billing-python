param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("patch", "minor", "major")]
    [string]$bump
)

$ErrorActionPreference = "Stop"

python -m hatch version $bump
$version = python -m hatch version

git add src/velobase_billing/__init__.py
git commit -m "v$version"
git tag -a "v$version" -m "v$version"
git push origin main --follow-tags

Write-Host "Released v$version"
