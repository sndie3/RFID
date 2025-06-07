import serial
import time
from PyQt5.QtCore import QThread, pyqtSignal

class SerialReader(QThread):
    card_detected = pyqtSignal(str)
    
    def __init__(self, port='COM3', baud_rate=9600):
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.running = False
        self.serial_connection = None
    
    def run(self):
        try:
            self.serial_connection = serial.Serial(self.port, self.baud_rate, timeout=1)
            self.running = True
            
            while self.running:
                if self.serial_connection.in_waiting > 0:
                    card_id = self.serial_connection.readline().decode('utf-8').strip()
                    if card_id and len(card_id) > 0:
                        self.card_detected.emit(card_id)
                time.sleep(0.1)
                
        except serial.SerialException as e:
            print(f"Serial connection error: {e}")
        except Exception as e:
            print(f"Error in serial reader: {e}")
    
    def stop(self):
        self.running = False
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.wait() 