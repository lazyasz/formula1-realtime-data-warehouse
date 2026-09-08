# Native PowerShell HTTP Server for serving dashboard
$port = 8000
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$port/")
$listener.Start()
Write-Output "PowerShell Web Server started on http://localhost:$port/"
Write-Output "Press Ctrl+C or stop the daemon task to exit."

$baseDir = "c:\Users\dhruv\.gemini\antigravity-ide\scratch\f1_dw"

try {
    while ($listener.IsListening) {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response
        
        $localPath = $request.Url.LocalPath
        if ($localPath -eq "/") {
            $localPath = "/dashboard.html"
        }
        
        # Sanitize path to prevent directory traversal
        $localPath = $localPath.Replace("/", "\").TrimStart("\")
        $filePath = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($baseDir, $localPath))
        
        # Verify the file is inside baseDir to secure traversal
        if ($filePath.StartsWith($baseDir, [System.StringComparison]::OrdinalIgnoreCase) -and (Test-Path $filePath -PathType Leaf)) {
            $content = [System.IO.File]::ReadAllBytes($filePath)
            $response.ContentLength64 = $content.Length
            
            # MIME Types
            if ($filePath.EndsWith(".html")) { $response.ContentType = "text/html" }
            elseif ($filePath.EndsWith(".js")) { $response.ContentType = "application/javascript" }
            elseif ($filePath.EndsWith(".css")) { $response.ContentType = "text/css" }
            elseif ($filePath.EndsWith(".png")) { $response.ContentType = "image/png" }
            elseif ($filePath.EndsWith(".jpg") -or $filePath.EndsWith(".jpeg")) { $response.ContentType = "image/jpeg" }
            elseif ($filePath.EndsWith(".svg")) { $response.ContentType = "image/svg+xml" }
            else { $response.ContentType = "text/plain" }
            
            $response.OutputStream.Write($content, 0, $content.Length)
        } else {
            $response.StatusCode = 404
            $msg = [System.Text.Encoding]::UTF8.GetBytes("File Not Found: $localPath")
            $response.ContentLength64 = $msg.Length
            $response.ContentType = "text/plain"
            $response.OutputStream.Write($msg, 0, $msg.Length)
        }
        
        $response.Close()
    }
} finally {
    $listener.Stop()
}
