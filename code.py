import tkinter as tk
from tkinter import messagebox, ttk
import requests
import datetime
import threading
from PIL import Image, ImageTk
import io
import base64

connected = False
streaming = False
stream_url = ""
upload_timer = None


# === Connect / Disconnect logic ===
def toggle_connection():
    global connected, stream_url

    ip = ip_entry.get().strip()
    if not ip:
        messagebox.showerror("Error", "Enter ESP32-CAM IP address.") #Don't enter IP address here, enter it on GUI
        return

    stream_url = f"http://{ip}/stream"
    capture_url = f"http://{ip}/capture"

    if not connected:
        try:
            test = requests.get(capture_url, timeout=3)
            if test.status_code == 200:
                connected_label.config(text=f"Status: Connected to {ip}")
                connect_btn.config(text="Disconnect")
                start_stream()
                connected = True
        except:
            messagebox.showerror("Connection Error", f"Could not connect to {ip}")
    else:
        connected = False
        connected_label.config(text="Status: Disconnected")
        connect_btn.config(text="Connect")
        stop_stream()


# === Capture photo ===
def take_photo():
    if not connected:
        messagebox.showwarning("Warning", "Connect to ESP32-CAM first.")
        return

    ip = ip_entry.get().strip()
    try:
        response = requests.get(f"http://{ip}/capture", timeout=5)
        if response.status_code == 200:
            now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"photo_{now}.jpg"
            with open(filename, 'wb') as f:
                f.write(response.content)

            messagebox.showinfo("Saved", f"Photo saved as {filename}")

            if upload_enable.get():
                upload_to_drive(filename)

        else:
            messagebox.showerror("Error", "Failed to capture image.")
    except Exception as e:
        messagebox.showerror("Error", str(e))


# === Upload to Google Drive ===


def upload_to_drive(filepath):
    gdrive_url = gdrive_entry.get().strip()  # Paste the Apps Script URL in the field that is GUI

    if not gdrive_url:
        messagebox.showerror("Missing URL", "Enter your Google Apps Script web app URL.") #Dont enter here, enter it in GUI
        return

    try:
        with open(filepath, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()

        data = {
            "file": encoded,
            "filename": filepath.split("/")[-1]
        }

        response = requests.post(gdrive_url, data=data)
        messagebox.showinfo("Upload", f"Uploaded {filepath} to Google Drive.\nResponse: {response.text}")
    except Exception as e:
        messagebox.showerror("Upload Failed", str(e))



    # Simulate upload or use your Apps Script here


# === Timed Upload logic ===
def start_timed_upload():
    global upload_timer

    try:
        interval = int(timed_entry.get())
    except:
        messagebox.showerror("Error", "Enter valid time in seconds.")
        return

    def repeat_capture():
        take_photo()
        global upload_timer
        if timed_upload.get():
            upload_timer = threading.Timer(interval, repeat_capture)
            upload_timer.start()

    repeat_capture()


def stop_timed_upload():
    global upload_timer
    if upload_timer:
        upload_timer.cancel()


# === Stream display ===
def start_stream():
    global streaming
    streaming = True
    update_stream()


def stop_stream():
    global streaming
    streaming = False
    cam_label.config(image="")  # Clear


def update_stream():
    if not streaming:
        return
    try:
        img_bytes = requests.get(f"http://{ip_entry.get().strip()}/capture", timeout=5).content
        img = Image.open(io.BytesIO(img_bytes))
        img = img.resize((320, 240))
        img = ImageTk.PhotoImage(img)
        cam_label.config(image=img)
        cam_label.image = img
    except:
        pass
    root.after(1000, update_stream)


# === GUI SETUP ===
root = tk.Tk()
root.title("ESP32 CAM Control")
root.geometry("1000x500") #enter according to your requirements
root.configure(bg="gold") #enter according to your requirements

# === LEFT PANEL ===
left_frame = tk.Frame(root, bg="gold") #enter according to your requirements
left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=20, pady=20)

tk.Label(left_frame, text="ESP32 CAM Control", bg="blue", fg="white", #enter according to your requirements
         font=("Helvetica", 18, "bold"), width=40).pack(pady=(0, 20))

connect_btn = tk.Button(left_frame, text="Connect", command=toggle_connection, width=30, bg="royalblue", fg="white", font=("Helvetica", 12, "bold"))
connect_btn.pack(pady=5)

connected_label = tk.Label(left_frame, text="Status: Disconnected", bg="gold", font=("Arial", 10, "italic")) #enter according to your requirements 
connected_label.pack(pady=(0, 10))

tk.Label(left_frame, text="Gdrive Path:", bg="gold", anchor="w").pack(fill="x")
gdrive_entry = tk.Entry(left_frame, width=30)
gdrive_entry.pack(pady=5)

tk.Label(left_frame, text="IP Address:", bg="gold", anchor="w").pack(fill="x")
ip_entry = tk.Entry(left_frame, width=30)
ip_entry.pack(pady=5)

upload_enable = tk.BooleanVar(value=True)
tk.Checkbutton(left_frame, text="Upload Enable", bg="gold", variable=upload_enable).pack(pady=5)

tk.Button(left_frame, text="Take Photo", command=take_photo, width=30, bg="royalblue", fg="white").pack(pady=10)

# Timed upload options
timed_upload = tk.BooleanVar(value=False)
tk.Checkbutton(left_frame, text="Timed Upload", bg="gold", variable=timed_upload,
               command=lambda: start_timed_upload() if timed_upload.get() else stop_timed_upload()).pack(pady=5)

tk.Label(left_frame, text="Timed in Seconds:", bg="gold", anchor="w").pack(fill="x")
timed_entry = tk.Entry(left_frame, width=30)
timed_entry.pack(pady=5)

# === RIGHT PANEL ===
right_frame = tk.Frame(root, bg="tan", width=480, height=360)
right_frame.pack(side=tk.LEFT, padx=10, pady=20)

cam_label = tk.Label(right_frame, text="ESP32 CAM Stream", bg="tan")
cam_label.pack()

root.mainloop()
