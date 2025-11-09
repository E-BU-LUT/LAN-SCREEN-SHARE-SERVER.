import cv2
import numpy as np
import pyautogui
import time

# Ayarlar
ENABLE_MOUSE_CONTROL = True  # Fare kontrolünü aktifleştir
SHOW_DEBUG_TEXT = True  # Test yazılarını göster

# Ekran boyutunu al
screen_width, screen_height = pyautogui.size()

# PyAutoGUI güvenlik özelliğini kapat
pyautogui.FAILSAFE = False

# Kamera başlat
cap = cv2.VideoCapture(0)

# Tıklama için değişkenler
previous_aspect_ratio = None
click_threshold = 0.3  # En-boy oranındaki değişim eşiği
click_cooldown = 0.5  # Tıklamalar arası bekleme süresi (saniye)
last_click_time = 0

# Smoothing için değişkenler
smooth_factor = 0.5  # 0-1 arası, yüksek değer daha yumuşak hareket
prev_x, prev_y = screen_width // 2, screen_height // 2

print("Program başlatıldı...")
print(f"Fare kontrolü: {'AÇIK' if ENABLE_MOUSE_CONTROL else 'KAPALI'}")
print(f"Test yazıları: {'AÇIK' if SHOW_DEBUG_TEXT else 'KAPALI'}")
print("Çıkmak için 'q' tuşuna basın")

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Aynalama
    frame = cv2.flip(frame, 1)
    
    # HSV'ye dönüştür
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    
    # Yeşil renk aralığı (geniş aralık)
    lower_green = np.array([25, 40, 40])
    upper_green = np.array([85, 255, 255])
    lower_purple = np.array([135, 60, 130])
    upper_purple = np.array([255, 255, 255])
    
    # Maske oluştur
    mask = cv2.inRange(hsv, lower_green, upper_green)
    #mask = cv2.inRange(hsv, lower_purple, upper_purple)
    
    # Morfolojik işlemler (gürültü azaltma)
    kernel = np.ones((5, 5), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    
    # Konturları bul
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if contours:
        # En büyük konturu bul
        largest_contour = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest_contour)
        
        # Minimum alan kontrolü
        if area > 1000:
            # Dörtgen yaklaşımı
            epsilon = 0.02 * cv2.arcLength(largest_contour, True)
            approx = cv2.approxPolyDP(largest_contour, epsilon, True)
            
            # Merkez noktasını hesapla
            M = cv2.moments(largest_contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                # Sınırlayıcı kutu
                x, y, w, h = cv2.boundingRect(largest_contour)
                
                # En-boy oranı hesapla
                aspect_ratio = float(w) / h if h != 0 else 0
                
                # Konturu çiz
                cv2.drawContours(frame, [largest_contour], 0, (0, 255, 0), 2)
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
                cv2.circle(frame, (cx, cy), 5, (0, 0, 255), -1)
                
                # Test yazıları
                if SHOW_DEBUG_TEXT:
                    cv2.putText(frame, f"Alan: {int(area)}", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.putText(frame, f"En-Boy: {aspect_ratio:.2f}", (10, 60),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.putText(frame, f"Konum: ({cx}, {cy})", (10, 90),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                    cv2.putText(frame, f"Genislik: {w}, Yukseklik: {h}", (10, 120),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
                
                # Fare kontrolü
                if ENABLE_MOUSE_CONTROL:
                    # Kamera koordinatlarını ekran koordinatlarına dönüştür
                    frame_height, frame_width = frame.shape[:2]
                    screen_x = int(np.interp(cx, [0, frame_width], [0, screen_width]))
                    screen_y = int(np.interp(cy, [0, frame_height], [0, screen_height]))
                    
                    # Smoothing uygula
                    screen_x = int(prev_x * smooth_factor + screen_x * (1 - smooth_factor))
                    screen_y = int(prev_y * smooth_factor + screen_y * (1 - smooth_factor))
                    
                    prev_x, prev_y = screen_x, screen_y
                    
                    # Fareyi hareket ettir
                    pyautogui.moveTo(screen_x, screen_y)
                
                # Tıklama algılama (yükseklik azaldığında)
                if previous_aspect_ratio is not None:
                    current_time = time.time()
                    
                    # En-boy oranı artıyorsa (yükseklik azalıyor)
                    if aspect_ratio > previous_aspect_ratio + click_threshold:
                        if current_time - last_click_time > click_cooldown:
                            if SHOW_DEBUG_TEXT:
                                cv2.putText(frame, "TIKLAMA ALGILANDI!", (10, 150),
                                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
                            
                            if ENABLE_MOUSE_CONTROL:
                                pyautogui.click()
                            
                            last_click_time = current_time
                
                previous_aspect_ratio = aspect_ratio
    
    # Durumu göster
    status_text = f"Fare: {'ON' if ENABLE_MOUSE_CONTROL else 'OFF'} | Test: {'ON' if SHOW_DEBUG_TEXT else 'OFF'}"
    cv2.putText(frame, status_text, (10, frame.shape[0] - 20),
               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
    
    # Göster
    cv2.imshow('Yesil Dortgen Takip', frame)
    cv2.imshow('Maske', mask)
    
    # Çıkış
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Temizle
cap.release()
cv2.destroyAllWindows()