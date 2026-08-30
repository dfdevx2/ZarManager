import platform
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

def apply_mac_theme(app, theme_name):
    """
    Motor de renderização isolado para macOS.
    Garante o estilo nativo translúcido da Apple.
    """
    app.setStyle("macOS")
    
    tooltip_style = """
        QToolTip {
            background-color: #2c3e50;
            color: #ffffff;
            border: 1px solid #34495e;
            border-radius: 6px;
            padding: 6px 10px;
            font-family: -apple-system, "Segoe UI", Roboto, Arial;
            font-size: 13px;
        }
    """
    app.setStyleSheet(tooltip_style)
    
    palette = QPalette()
    
    if theme_name == "Sistema":
        try:
            is_dark = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
        except AttributeError:
            is_dark = app.style().standardPalette().color(QPalette.ColorRole.Window).lightness() < 128
        theme_name = "Preto" if is_dark else "Branco"

    if theme_name == "Preto":
        palette.setColor(QPalette.ColorRole.Window, QColor(12, 12, 12))          
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(6, 6, 6))            
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(16, 16, 16))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(44, 62, 80))
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(22, 22, 22))       
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(138, 43, 226))       
        palette.setColor(QPalette.ColorRole.Highlight, QColor(138, 43, 226))  
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        
    elif theme_name == "Branco":
        palette.setColor(QPalette.ColorRole.Window, QColor(245, 246, 248))       
        palette.setColor(QPalette.ColorRole.WindowText, QColor(30, 30, 30))      
        palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))         
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(238, 240, 242))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(44, 62, 80))
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.Button, QColor(230, 232, 235))       
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(30, 30, 30))
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(52, 152, 219))          
        palette.setColor(QPalette.ColorRole.Highlight, QColor(52, 152, 219))     
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
        
    elif theme_name == "Steam":
        palette.setColor(QPalette.ColorRole.Window, QColor(23, 29, 37))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(13, 19, 27))         
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(27, 40, 56))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(44, 62, 80))
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(42, 71, 94))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(102, 192, 244))      
        palette.setColor(QPalette.ColorRole.Highlight, QColor(102, 192, 244)) 
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

    elif theme_name == "Xbox":
        palette.setColor(QPalette.ColorRole.Window, QColor(16, 30, 18))
        palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Base, QColor(10, 20, 12))         
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 40, 25))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(44, 62, 80))
        palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.Button, QColor(26, 60, 32))
        palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
        palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
        palette.setColor(QPalette.ColorRole.Link, QColor(16, 124, 16))        
        palette.setColor(QPalette.ColorRole.Highlight, QColor(16, 124, 16))   
        palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)

    app.setPalette(palette)