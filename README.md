# CTU-CC RFID MANAGEMENT SYSTEM

A desktop application for managing RFID-based access and user registration, built with Python and PyQt5.

## Features
- Admin login system
- Register users with RFID cards (students/employees)
- Store user info, photo, and card data in SQLite database
- Manage users (activate, deactivate, delete)
- View and export access logs
- Serial communication with Arduino-based RFID reader

## Dependencies
- Python 3.x
- PyQt5
- pyserial
- sqlite3 (standard with Python)

Install dependencies with:
```
pip install pyqt5 pyserial
```

## Hardware Requirements
- Arduino Board
- MFRC522 RFID Reader
- Jumper Wires
- Buzzer, LEDs

## How to Run
1. Connect your Arduino and RFID reader as described in the hardware section.
2. Make sure your Arduino is running the correct sketch to output card IDs over serial.
3. Place `icon.ico` in the project directory for the app icon.
4. Run the app:
   ```
   python rfid.py
   ```
5. Login with the default credentials:
   - Username: `admin`
   - Password: `admin123`

## Developer
Sandie G

This System still on the development phase

