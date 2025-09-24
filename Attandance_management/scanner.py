import cv2
import time
from flask import Flask
from flask_mysqldb import MySQL 

# Flask app setup
app = Flask(__name__)
app.secret_key = 'abhishek'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'attan_manage'

# Initialize MySQL connection
con = MySQL(app)

# QR Scanner setup
detector = cv2.QRCodeDetector()
cap = cv2.VideoCapture(0)

cap.set(3, 1280)  # width
cap.set(4, 720)   # height

if not cap.isOpened():
    print("Error: Could not access the camera.")
    exit()

last_scanned = None  
last_scan_time = 0   # store last scan timestamp
cooldown = 1       # seconds (reduce delay here)

while True:
    ret, frame = cap.read()
    if not ret:
        print("Failed to grab frame")
        continue

    data, bbox, _ = detector.detectAndDecode(frame)

    if bbox is not None:
        bbox = bbox.astype(int)
        for i in range(len(bbox)):
            pt1 = tuple(bbox[i][0])
            pt2 = tuple(bbox[(i+1) % len(bbox)][0])
            cv2.line(frame, pt1, pt2, (0, 255, 0), 2)

        if data:
            now = time.time()
            if data != last_scanned or (now - last_scan_time) > cooldown:
                last_scanned = data
                last_scan_time = now
                print("QR Code Data:", data)

                with app.app_context():
                    cur = con.connection.cursor()
                    cur.execute("SELECT present FROM login_data WHERE username = %s", (data,))
                    result = cur.fetchone()
                    if result:
                        total = result[0] + 1
                        print("Updated total:", total)
                        cur.execute("""UPDATE login_data SET present=%s WHERE username=%s""", (total, data))
                        con.connection.commit()
                    cur.close()

            cv2.putText(frame, data, (bbox[0][0][0], bbox[0][0][1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 0, 0), 2)

    cv2.imshow("QR Scanner", frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()