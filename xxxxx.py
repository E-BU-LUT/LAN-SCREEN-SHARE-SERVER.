#!/usr/bin/env python3
"""
Yerel Ağ Ekran Paylaşım Sunucusu
Bilgisayarınızın ekranını yerel ağdaki diğer cihazlara web tarayıcısı üzerinden yayınlar.
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import base64
import json
import socket
from PIL import ImageGrab
import io
import threading
import time
import tkinter as tk
from tkinter import messagebox

class ScreenShareHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            # Ana sayfa - görüntüleyici
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Ekran Paylaşımı</title>
                <style>
                    * { margin: 0; padding: 0; box-sizing: border-box; }
                    body {
                        font-family: Arial, sans-serif;
                        background: #1a1a1a;
                        color: #fff;
                        display: flex;
                        flex-direction: column;
                        align-items: center;
                        padding: 20px;
                    }
                    h1 {
                        margin-bottom: 20px;
                        color: #4CAF50;
                    }
                    #screen {
                        max-width: 95vw;
                        max-height: 80vh;
                        border: 2px solid #4CAF50;
                        border-radius: 8px;
                        box-shadow: 0 4px 20px rgba(76, 175, 80, 0.3);
                    }
                    #status {
                        margin-top: 15px;
                        padding: 10px 20px;
                        background: #333;
                        border-radius: 5px;
                        font-size: 14px;
                    }
                    .connected { color: #4CAF50; }
                    .disconnected { color: #f44336; }
                    #fps {
                        margin-top: 10px;
                        color: #888;
                        font-size: 12px;
                    }
                </style>
            </head>
            <body>
                <h1>🖥️ Ekran Paylaşımı</h1>
                <img id="screen" alt="Ekran yükleniyor...">
                <div id="status" class="disconnected">Bağlanıyor...</div>
                <div id="fps">FPS: 0</div>
                
                <script>
                    const screen = document.getElementById('screen');
                    const status = document.getElementById('status');
                    const fpsDisplay = document.getElementById('fps');
                    let frameCount = 0;
                    let lastTime = Date.now();
                    
                    function updateScreen() {
                        fetch('/screen')
                            .then(response => response.json())
                            .then(data => {
                                screen.src = 'data:image/jpeg;base64,' + data.image;
                                status.textContent = 'Bağlı ✓';
                                status.className = 'connected';
                                
                                // FPS hesaplama
                                frameCount++;
                                const now = Date.now();
                                if (now - lastTime >= 1000) {
                                    fpsDisplay.textContent = `FPS: ${frameCount}`;
                                    frameCount = 0;
                                    lastTime = now;
                                }
                                
                                setTimeout(updateScreen, 100); // ~10 FPS
                            })
                            .catch(error => {
                                status.textContent = 'Bağlantı Kesildi ✗';
                                status.className = 'disconnected';
                                setTimeout(updateScreen, 2000);
                            });
                    }
                    
                    updateScreen();
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode())
            
        elif self.path == '/screen':
            # Ekran görüntüsü API
            try:
                # Ekran görüntüsü al
                screenshot = ImageGrab.grab()
                
                # JPEG formatına çevir (daha hızlı ve küçük)
                img_buffer = io.BytesIO()
                screenshot.save(img_buffer, format='JPEG', quality=75, optimize=True)
                img_buffer.seek(0)
                
                # Base64'e çevir
                img_base64 = base64.b64encode(img_buffer.read()).decode()
                
                # JSON yanıtı gönder
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                
                response = json.dumps({'image': img_base64})
                self.wfile.write(response.encode())
                
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                error = json.dumps({'error': str(e)})
                self.wfile.write(error.encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Sadece önemli logları göster
        if '200' in args[1]:
            return
        print(f"{self.address_string()} - {format % args}")

def get_local_ip():
    """Bilgisayarın yerel IP adresini bul"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "127.0.0.1"

def show_alert(server_url):
    """Sunucu adresini alert mesajı ile göster"""
    root = tk.Tk()
    root.withdraw()  # Ana pencereyi gizle
    messagebox.showinfo(
        "🖥️ Ekran Paylaşım Sunucusu",
        f"Sunucu başarıyla başlatıldı!\n\n"
        f"📡 Sunucu Adresi:\n{server_url}\n\n"
        f"🌐 Yerel ağınızdaki diğer cihazlardan bu adrese\n"
        f"erişerek ekranınızı izleyebilirler.\n\n"
        f"⏹️ Durdurmak için konsol penceresinde Ctrl+C'ye basın."
    )
    root.destroy()

def main():
    PORT = 8080
    local_ip = get_local_ip()
    server_url = f"http://{local_ip}:{PORT}"
    
    print("=" * 60)
    print("🖥️  EKRAN PAYLAŞIM SUNUCUSU BAŞLATILDI")
    print("=" * 60)
    print(f"\n📡 Sunucu adresi: {server_url}")
    print(f"\n🌐 Diğer cihazlardan erişim için:")
    print(f"   Tarayıcınızda şu adresi açın: {server_url}")
    print(f"\n💡 İpucu: Yerel ağınızdaki (aynı modemde) tüm cihazlar bu adrese")
    print(f"   erişerek ekranınızı canlı olarak izleyebilir.")
    print(f"\n⏹️  Durdurmak için Ctrl+C tuşlarına basın")
    print("=" * 60 + "\n")
    
    # Alert mesajını ayrı thread'de göster
    alert_thread = threading.Thread(target=show_alert, args=(server_url,))
    alert_thread.daemon = True
    alert_thread.start()
    
    try:
        server = HTTPServer(('0.0.0.0', PORT), ScreenShareHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Sunucu kapatılıyor...")
        server.shutdown()
        print("✅ Sunucu başarıyla kapatıldı!")

if __name__ == '__main__':
    main()
