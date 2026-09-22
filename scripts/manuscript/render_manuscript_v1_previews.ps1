param(
    [Parameter(Mandatory = $false)]
    [string]$RepoRoot = "."
)

$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Drawing

$repo = (Resolve-Path -LiteralPath $RepoRoot).Path
$specPath = Join-Path $repo "docs/manuscript/v1/figure_sources/figure_specs.json"
if (-not (Test-Path -LiteralPath $specPath -PathType Leaf)) {
    throw "Figure specification not found: $specPath"
}

$spec = Get-Content -Raw -Encoding UTF8 -LiteralPath $specPath | ConvertFrom-Json
$outputDirectory = Join-Path $repo "docs/manuscript/v1/figures"
New-Item -ItemType Directory -Force -Path $outputDirectory | Out-Null

function Convert-HexColor {
    param([Parameter(Mandatory = $true)][string]$Value)
    return [System.Drawing.ColorTranslator]::FromHtml($Value)
}

function New-RoundedRectanglePath {
    param(
        [float]$X,
        [float]$Y,
        [float]$Width,
        [float]$Height,
        [float]$Radius
    )
    $path = [System.Drawing.Drawing2D.GraphicsPath]::new()
    if ($Radius -le 0) {
        $path.AddRectangle([System.Drawing.RectangleF]::new($X, $Y, $Width, $Height))
        return $path
    }
    $diameter = [Math]::Min(2 * $Radius, [Math]::Min($Width, $Height))
    $path.AddArc($X, $Y, $diameter, $diameter, 180, 90)
    $path.AddArc($X + $Width - $diameter, $Y, $diameter, $diameter, 270, 90)
    $path.AddArc($X + $Width - $diameter, $Y + $Height - $diameter, $diameter, $diameter, 0, 90)
    $path.AddArc($X, $Y + $Height - $diameter, $diameter, $diameter, 90, 90)
    $path.CloseFigure()
    return $path
}

function New-LinePen {
    param(
        [string]$Color,
        [float]$Width,
        [bool]$Dashed
    )
    $pen = [System.Drawing.Pen]::new((Convert-HexColor $Color), $Width)
    $pen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
    $pen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
    if ($Dashed) {
        $pen.DashStyle = [System.Drawing.Drawing2D.DashStyle]::Dash
    }
    return $pen
}

$dpi = 300.0
$rendered = @()
foreach ($figure in $spec.figures) {
    $pixelWidth = [Math]::Max(1, [int][Math]::Round(([double]$figure.width_mm / 25.4) * $dpi))
    $pixelHeight = [Math]::Max(1, [int][Math]::Round(([double]$figure.height_mm / 25.4) * $dpi))
    $bitmap = [System.Drawing.Bitmap]::new($pixelWidth, $pixelHeight, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
    $bitmap.SetResolution($dpi, $dpi)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
        $graphics.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
        $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
        $graphics.Clear([System.Drawing.Color]::White)
        $scaleX = $pixelWidth / [double]$figure.width
        $scaleY = $pixelHeight / [double]$figure.height
        $graphics.ScaleTransform([single]$scaleX, [single]$scaleY)

        foreach ($item in $figure.primitives) {
            switch ([string]$item.type) {
                "rect" {
                    $path = New-RoundedRectanglePath -X ([single]$item.x) -Y ([single]$item.y) -Width ([single]$item.width) -Height ([single]$item.height) -Radius ([single]$item.radius)
                    try {
                        $brush = [System.Drawing.SolidBrush]::new((Convert-HexColor ([string]$item.fill)))
                        try { $graphics.FillPath($brush, $path) } finally { $brush.Dispose() }
                        if ([double]$item.stroke_width -gt 0) {
                            $pen = New-LinePen -Color ([string]$item.stroke) -Width ([single]$item.stroke_width) -Dashed ([bool]$item.dash)
                            try { $graphics.DrawPath($pen, $path) } finally { $pen.Dispose() }
                        }
                    } finally {
                        $path.Dispose()
                    }
                }
                "line" {
                    $pen = New-LinePen -Color ([string]$item.stroke) -Width ([single]$item.stroke_width) -Dashed ([bool]$item.dash)
                    try {
                        $graphics.DrawLine($pen, [single]$item.x1, [single]$item.y1, [single]$item.x2, [single]$item.y2)
                    } finally { $pen.Dispose() }
                }
                "arrow" {
                    $pen = New-LinePen -Color ([string]$item.stroke) -Width ([single]$item.stroke_width) -Dashed ([bool]$item.dash)
                    try {
                        $graphics.DrawLine($pen, [single]$item.x1, [single]$item.y1, [single]$item.x2, [single]$item.y2)
                    } finally { $pen.Dispose() }
                    $angle = [Math]::Atan2(([double]$item.y2 - [double]$item.y1), ([double]$item.x2 - [double]$item.x1))
                    $head = 18.0 + [double]$item.stroke_width
                    $wing = 0.48
                    $points = [System.Drawing.PointF[]]@(
                        [System.Drawing.PointF]::new([single]$item.x2, [single]$item.y2),
                        [System.Drawing.PointF]::new(
                            [single]([double]$item.x2 - $head * [Math]::Cos($angle - $wing)),
                            [single]([double]$item.y2 - $head * [Math]::Sin($angle - $wing))
                        ),
                        [System.Drawing.PointF]::new(
                            [single]([double]$item.x2 - $head * [Math]::Cos($angle + $wing)),
                            [single]([double]$item.y2 - $head * [Math]::Sin($angle + $wing))
                        )
                    )
                    $brush = [System.Drawing.SolidBrush]::new((Convert-HexColor ([string]$item.stroke)))
                    try { $graphics.FillPolygon($brush, $points) } finally { $brush.Dispose() }
                }
                "circle" {
                    $diameter = 2.0 * [double]$item.radius
                    $brush = [System.Drawing.SolidBrush]::new((Convert-HexColor ([string]$item.fill)))
                    try {
                        $graphics.FillEllipse($brush, [single]([double]$item.cx - [double]$item.radius), [single]([double]$item.cy - [double]$item.radius), [single]$diameter, [single]$diameter)
                    } finally { $brush.Dispose() }
                    if ([double]$item.stroke_width -gt 0) {
                        $pen = New-LinePen -Color ([string]$item.stroke) -Width ([single]$item.stroke_width) -Dashed $false
                        try {
                            $graphics.DrawEllipse($pen, [single]([double]$item.cx - [double]$item.radius), [single]([double]$item.cy - [double]$item.radius), [single]$diameter, [single]$diameter)
                        } finally { $pen.Dispose() }
                    }
                }
                "text" {
                    $style = if ([int]$item.weight -ge 600) { [System.Drawing.FontStyle]::Bold } else { [System.Drawing.FontStyle]::Regular }
                    $font = [System.Drawing.Font]::new("Arial", [single]$item.size, $style, [System.Drawing.GraphicsUnit]::Pixel)
                    $brush = [System.Drawing.SolidBrush]::new((Convert-HexColor ([string]$item.color)))
                    $format = [System.Drawing.StringFormat]::GenericTypographic.Clone()
                    try {
                        $format.FormatFlags = $format.FormatFlags -bor [System.Drawing.StringFormatFlags]::MeasureTrailingSpaces
                        $lineHeight = [double]$item.size * 1.25
                        $lines = ([string]$item.text) -split "`n", 0, "SimpleMatch"
                        for ($lineIndex = 0; $lineIndex -lt $lines.Count; $lineIndex++) {
                            $line = $lines[$lineIndex]
                            $size = $graphics.MeasureString($line, $font, [System.Drawing.PointF]::Empty, $format)
                            $x = [double]$item.x
                            if ([string]$item.anchor -eq "middle") { $x -= $size.Width / 2.0 }
                            elseif ([string]$item.anchor -eq "end") { $x -= $size.Width }
                            $baseline = [double]$item.y + $lineIndex * $lineHeight
                            $top = $baseline - [double]$item.size * 0.82
                            $graphics.DrawString($line, $font, $brush, [single]$x, [single]$top, $format)
                        }
                    } finally {
                        $format.Dispose()
                        $brush.Dispose()
                        $font.Dispose()
                    }
                }
                default { throw "Unsupported primitive type: $($item.type)" }
            }
        }

        $outputPath = Join-Path $outputDirectory (([string]$figure.filename) + ".png")
        $bitmap.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
        $rendered += [PSCustomObject]@{
            path = $outputPath
            pixels = "${pixelWidth}x${pixelHeight}"
            dpi = 300
        }
    } finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
}

$rendered | ForEach-Object { "Rendered $($_.path) [$($_.pixels), $($_.dpi) dpi]" }
