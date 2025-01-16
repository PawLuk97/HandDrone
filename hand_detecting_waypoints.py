"""
author: Pawel Lukowicz
pawellukowicz97@gmail.com
"""

import cv2
import mediapipe as mp
import time
import math
import numpy as np

def calculate_distance(point1, point2):
    """Oblicza odległość między dwoma punktami."""
    return math.sqrt((point1[0] - point2[0]) ** 2 + (point1[1] - point2[1]) ** 2)

def hand_tracking(mode, num_points=4, alt=0):
    if mode not in ["time", "gestures"]:
        print("Nieprawidłowy argument. Użyj 'time' lub 'gestures'.")
        return

    # Inicjalizacja MediaPipe Hands
    mp_hands = mp.solutions.hands
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=2, min_detection_confidence=0.5,
                           min_tracking_confidence=0.5)
    mp_drawing = mp.solutions.drawing_utils

    # Inicjalizacja kamery
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("Nie można otworzyć kamery.")
        return

    # Lista do przechowywania współrzędnych
    finger_coordinates = []

    # Zmienna do kontrolowania czasu
    last_time = time.time()
    total_time = 0  # Łączny czas, gdy palec wskazujący jest wykrywany
    start_timer = None
    last_saved_time = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Nie udało się pobrać klatki wideo.")
            break

        # Obrót obrazu (jeśli kamera odwraca obraz)
        frame = cv2.flip(frame, 1)

        # Pobranie rozmiarów obrazu
        height, width, _ = frame.shape

        # Przesunięcie współrzędnych tak, aby środek obrazu był (0, 0)
        center_x = width // 2
        center_y = height // 2

        # Konwersja koloru na RGB (MediaPipe wymaga obrazu w RGB)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Przetwarzanie obrazu w celu wykrycia dłoni
        results = hands.process(rgb_frame)

        # Inicjalizacja zmiennej hand_detected
        hand_detected = False

        if mode == "time":
            current_time = time.time()

            if results.multi_hand_landmarks:
                for hand_landmarks in results.multi_hand_landmarks:
                    # Rysowanie wykrytych dłoni
                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Pobieranie współrzędnych czubka wskazującego palca
                    index_finger_tip = hand_landmarks.landmark[8]
                    index_x = int(index_finger_tip.x * frame.shape[1])
                    index_y = int(index_finger_tip.y * frame.shape[0])

                    # Przesunięcie współrzędnych na środek ekranu
                    index_x -= center_x
                    index_y -= center_y

                    hand_detected = True

                    # Rozpoczęcie odliczania, jeśli nie trwa
                    if start_timer is None:
                        start_timer = current_time

                    # Aktualizacja czasu
                    elapsed = current_time - start_timer
                    if elapsed >= 3 and len(finger_coordinates) < num_points:
                        finger_coordinates.append([index_x, index_y, alt])
                        print(f"Punkt zapisany: ({index_x}, {index_y}, {alt}])")
                        start_timer = None

                        # Zakończenie programu po zapisaniu wymaganej liczby punktów
                        if len(finger_coordinates) == num_points:
                            print(f"Zapisano {num_points} punktów:", finger_coordinates)
                            cap.release()
                            cv2.destroyAllWindows()
                            hands.close()

                            # Dodanie wektora z zerami na końcu
                            finger_coordinates.append([0, 0, 0])
                            coordinates_array = np.array(finger_coordinates)
                            return coordinates_array

                # Wyświetlanie współrzędnych obok czubka palca wskazującego
                if hand_detected:
                    cv2.putText(frame, f"({index_x}, {index_y})", (index_x + center_x + 10, index_y + center_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

                # Aktualizacja łącznego czasu, gdy palec wskazujący jest widoczny
                if hand_detected:
                    total_time += current_time - last_time

            else:
                start_timer = None  # Pauza, gdy palec nie jest wykrywany

            # Wyświetlanie informacji na ekranie
            cv2.putText(frame, f"Zebrane punkty: {len(finger_coordinates)}/{int(num_points)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                        (255, 255, 0), 2)
            y_offset = 70
            for i, coords in enumerate(finger_coordinates):
                cv2.putText(frame, f"{i + 1}: ({coords[0]}, {coords[1]})", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (255, 255, 0), 2)
                y_offset += 30
            if start_timer:
                cv2.putText(frame, f"{int(3 - (current_time - start_timer))}", (frame.shape[1] // 2 - 50, frame.shape[0] // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 5, (255, 255, 255), 2)


        elif mode == "gestures":

            if results.multi_hand_landmarks:

                for hand_landmarks in results.multi_hand_landmarks:

                    mp_drawing.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                    # Pobieranie współrzędnych czubka wskazującego palca i kciuka

                    index_finger_tip = hand_landmarks.landmark[8]

                    thumb_tip = hand_landmarks.landmark[4]

                    index_x = int(index_finger_tip.x * frame.shape[1])

                    index_y = int(index_finger_tip.y * frame.shape[0])

                    thumb_x = int(thumb_tip.x * frame.shape[1])

                    thumb_y = int(thumb_tip.y * frame.shape[0])

                    # Przesunięcie współrzędnych na środek ekranu

                    index_x -= center_x

                    index_y -= center_y

                    thumb_x -= center_x

                    thumb_y -= center_y

                    # Obliczanie odległości

                    distance = calculate_distance((index_x, index_y), (thumb_x, thumb_y))

                    current_time = time.time()  # Aktualny czas

                    # Warunek na zapis punktu (uwzględniający minimalny czas od ostatniego zapisu)

                    if distance < 20 and len(finger_coordinates) < num_points:

                        if last_saved_time is None or current_time - last_saved_time > 1:  # Sprawdzenie, czy minęło co najmniej 1 sekunda

                            finger_coordinates.append([index_x, index_y, alt])  # Dodajemy współrzędne + alt

                            print(f"Punkt zapisany: ({index_x}, {index_y}, {alt})")

                            last_saved_time = current_time  # Aktualizacja czasu ostatniego zapisu

                            # Zakończenie programu po zapisaniu wymaganej liczby punktów

                            if len(finger_coordinates) == num_points:
                                print(f"Zapisano {num_points} punktów:", finger_coordinates)

                                cap.release()

                                cv2.destroyAllWindows()

                                hands.close()

                                # Dodanie wektora z zerami na końcu

                                finger_coordinates.append([0, 0, 0])

                                coordinates_array = np.array(finger_coordinates)

                                return coordinates_array

                # Wyświetlanie współrzędnych obok czubka palca wskazującego

                if hand_detected:
                    cv2.putText(frame, f"({index_x}, {index_y})",

                                (index_x + center_x + 10, index_y + center_y),

                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            # Wyświetlanie punktów
            cv2.putText(frame, f"Zebrane punkty: {len(finger_coordinates)}/{int(num_points)}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 2)
            y_offset = 70
            for i, coords in enumerate(finger_coordinates):
                cv2.putText(frame, f"{i + 1}: ({coords[0]}, {coords[1]})", (10, y_offset), cv2.FONT_HERSHEY_SIMPLEX, 0.5,
                            (255, 255, 0), 2)
                y_offset += 30

        # Wyświetlanie wyników
        cv2.imshow("Detekcja dłoni - MediaPipe", frame)

        # Przerwanie działania po wciśnięciu klawisza 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        last_time = time.time()

    # Zwolnienie zasobów
    cap.release()
    cv2.destroyAllWindows()
    hands.close()


# Wywołanie funkcji z odpowiednim trybem i liczbą punktów
#wp = hand_tracking("time", 2, 2)
# print(wp)
