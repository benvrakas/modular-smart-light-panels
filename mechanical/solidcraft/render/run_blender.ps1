# Run Blender in the background at below-normal CPU priority (so video playback and other apps stay smooth).
# usage: powershell -NoProfile -ExecutionPolicy Bypass -File run_blender.ps1 -Log LOGFILE -BlenderArgs "<blender arguments as one string>"
# Pass Blender's arguments as one string, so PowerShell doesn't read -P, -b or -- as its own.
param([Parameter(Mandatory = $true)][string]$Log, [Parameter(Mandatory = $true)][string]$BlenderArgs)
$exe = 'C:\Program Files\Blender Foundation\Blender 4.3\blender.exe'
$p = Start-Process -FilePath $exe -ArgumentList $BlenderArgs -NoNewWindow -PassThru `
    -RedirectStandardOutput $Log -RedirectStandardError ($Log + '.err')
try { $p.PriorityClass = 'BelowNormal' } catch { }
$p.WaitForExit()
exit $p.ExitCode
