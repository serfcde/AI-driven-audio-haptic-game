AI-Driven Audio-Haptic Game (ESP8266 Project)
This file contains all the steps to build and execute your project.
Project Goal
To build a self-contained game on the Wemos D1 Mini (ESP8266) that uses a joystick module to control a "player." The player gets audio-haptic (sound and touch) feedback to find a hidden target. An "AI" detects erratic movements and changes the feedback to help the user.
Phase 1: Software & Driver Setup (Do this FIRST)
This is the most critical step. Your "no ports available" error must be solved.
1.	Install Arduino IDE: If you haven't, download and install the free Arduino IDE from the official website.
2.	Install ESP8266 Boards:
o	Open Arduino IDE, go to File > Preferences.
o	In the "Additional Board Manager URLs" box, paste this: http://arduino.esp8266.com/stable/package_esp8266com_index.json
o	Go to Tools > Board > Boards Manager..., search for "esp8266", and install the package.
3.	FIX THE "NO PORTS" ERROR:
o	Get a Data Cable: The #1 reason for this error is using a "charge-only" USB cable. Find a cable you know works for data (like a smartphone sync cable).
o	Install Drivers: Your Wemos D1 Mini needs a driver. Look at the small black chip on the board.
	If it says CH340, install the CH340 driver.
	If it says CP2102, install the CP2102 driver.
o	Verify: Plug in your board with the data cable. Go to your computer's Device Manager. You must see a new device under "Ports (COM & LPT)" (e.g., USB-SERIAL (COM3)). If you see this, you are ready.
Phase 2: Hardware Assembly
Use your components and follow this exact wiring plan based on your board's layout.
Component List:
•	Wemos D1 Mini (ESP8266)
•	Breadboard
•	Joystick Module (HW-504)
•	Micro Vibration Motor
•	Piezo Buzzer
•	2N2222A NPN Transistor
•	1N4007 Diode
•	1kΩ Resistor (Brown-Black-Red)
•	Jumper Wires
Wiring Instructions (based on your board b1 = 5V):
1.	Power Rails:
o	b1 (5V) → RED (+) rail
o	b2 (GND) → BLUE (-) rail
2.	Joystick Module:
o	GND pin → BLUE (-) rail
o	+5V pin → RED (+) rail
o	VRx pin → b3 (A0 pin on ESP)
o	SW pin → i5 (D6 pin on ESP)
3.	Vibration Motor (use row 15):
o	Note: This circuit uses a 2N2222A Transistor as a basic switch. While a dedicated motor driver IC (like an L293D, as mentioned in the report) is recommended for reliably handling high-frequency pulses and preventing back-voltage, this transistor circuit is a viable substitute for basic prototyping.
o	Place Transistor in e15 (Emitter), e16 (Base), e17 (Collector).
o	Wire from e15 (Emitter) → BLUE (-) rail.
o	Connect 1kΩ Resistor from e16 (Base) to e20 (empty row).
o	Wire from e20 → i4 (D5 pin on ESP).
o	Connect Motor Wire 1 → RED (+) rail.
o	Connect Motor Wire 2 → e17 (Collector).
o	Connect 1N4007 Diode:
	BLACK end (no stripe) → e17 (Collector).
	SILVER STRIPE end → RED (+) rail.
4.	Piezo Buzzer:
o	Buzzer RED wire → i6 (D7 pin on ESP).
o	Buzzer BLACK wire → BLUE (-) rail.
Phase 3: Code Upload & Execution
1.	Open Source File: Open the esp8266_haptic_game.ino file in your Arduino IDE.
2.	Select Board: Go to Tools > Board > ESP8266 Boards and select "LOLIN(WEMOS) D1 R2 & mini".
3.	Select Port: Go to Tools > Port and select the COM port that appeared in Phase 1 (e.g., COM3).
4.	Upload: Click the Upload button (the arrow pointing right). Wait for it to say "Done uploading."
Phase 4: How to Play
1.	The project will start running immediately.
2.	Open Serial Monitor: To see the "AI" and "Proximity" values, click the "Serial Monitor" button (top right) and set the speed to 115200 baud.
3.	The Game:
o	Move the joystick left and right.
o	The "hidden target" is a random position. The closer you get to it, the stronger the STEADY vibration will be.
o	If you move the joystick erratically (shake it), the "AI" will detect this (jerk) and change the feedback to a "jittery" PULSE and a beep. This tells you to slow down.
o	Press the joystick button down to set a new random target. The buzzer will play a "new target" sound.

