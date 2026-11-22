<#
  Auto-dismiss "wxWidgets Debug Alert" pop-ups (from KiCad or KiCad Python scripts).
  It clicks [Cancel], which tells that process to suppress further warnings.

  Usage:  powershell -NoProfile -ExecutionPolicy Bypass -File dismiss-wx-alerts.ps1 [-Minutes 480] [-Once]
          -Once     dismiss whatever is open now and exit
          -Minutes  keep watching for this long (default 8 h), polling every 2 s
  Logs each dismissal to dismiss-wx-alerts.log next to this script.
#>
param([int]$Minutes = 480, [switch]$Once)

Add-Type @"
using System; using System.Text; using System.Runtime.InteropServices;
public static class WxAlert {
  public delegate bool EnumProc(IntPtr h, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumWindows(EnumProc f, IntPtr l);
  [DllImport("user32.dll")] static extern bool EnumChildWindows(IntPtr p, EnumProc f, IntPtr l);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetWindowText(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] static extern int GetClassName(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] static extern bool IsWindowVisible(IntPtr h);
  [DllImport("user32.dll")] static extern IntPtr SendMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
  [DllImport("user32.dll")] static extern uint GetWindowThreadProcessId(IntPtr h, out uint pid);
  static string Text(IntPtr h){ var s=new StringBuilder(256); GetWindowText(h,s,256); return s.ToString(); }
  static string Cls(IntPtr h){ var s=new StringBuilder(64); GetClassName(h,s,64); return s.ToString(); }
  // returns "pid:title" for each alert dismissed
  public static string[] DismissAll() {
    var hits = new System.Collections.Generic.List<string>();
    EnumWindows((h, l) => {
      if (!IsWindowVisible(h) || !Text(h).Contains("Debug Alert")) return true;
      IntPtr cancel = IntPtr.Zero, no = IntPtr.Zero;
      EnumChildWindows(h, (c, l2) => {
        if (Cls(c) == "Button") { var t = Text(c).Replace("&",""); if (t=="Cancel") cancel=c; else if (t=="No") no=c; }
        return true; }, IntPtr.Zero);
      IntPtr btn = cancel != IntPtr.Zero ? cancel : no;          // Cancel = suppress further warnings
      if (btn != IntPtr.Zero) SendMessage(btn, 0x00F5, IntPtr.Zero, IntPtr.Zero); // BM_CLICK
      else SendMessage(h, 0x0010, IntPtr.Zero, IntPtr.Zero);                        // WM_CLOSE fallback
      uint pid; GetWindowThreadProcessId(h, out pid);
      hits.Add(pid + ":" + Text(h));
      return true; }, IntPtr.Zero);
    return hits.ToArray();
  }
}
"@

$log = Join-Path $PSScriptRoot "dismiss-wx-alerts.log"
$deadline = (Get-Date).AddMinutes($Minutes)
do {
  foreach ($h in [WxAlert]::DismissAll()) {
    $pid_ = $h.Split(':')[0]
    $name = (Get-Process -Id $pid_ -ErrorAction SilentlyContinue).ProcessName
    "$(Get-Date -Format s)  dismissed alert in $name (pid $pid_)" | Tee-Object -FilePath $log -Append
  }
  if ($Once) { break }
  Start-Sleep -Seconds 2
} while ((Get-Date) -lt $deadline)
