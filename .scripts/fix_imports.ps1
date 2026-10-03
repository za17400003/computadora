# Fix all golem imports to computadora in the computadora/ package
$counter = 0
Get-ChildItem computadora -Recurse -Include *.py -File | ForEach-Object {
  $content = [System.IO.File]::ReadAllText($_.FullName, [Text.Encoding]::UTF8)
  $original = $content
  
  $content = $content -replace 'from golem\.', 'from computadora.'
  $content = $content -replace 'import golem\.', 'import computadora.'
  
  if ($content -ne $original) {
    [System.IO.File]::WriteAllText($_.FullName, $content, [Text.Encoding]::UTF8)
    Write-Host "[OK]" $_.FullName
    $counter++
  }
}
Write-Host "Total archivos actualizados: $counter"
