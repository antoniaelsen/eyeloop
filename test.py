import cv2
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk

# def open_file():
#     """Open a file for editing."""
#     filepath = askopenfilename(
#         filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
#     )
#     if not filepath:
#         return
#     txt_edit.delete("1.0", tk.END)
#     with open(filepath, mode="r", encoding="utf-8") as input_file:
#         text = input_file.read()
#         txt_edit.insert(tk.END, text)
#     window.title(f"Simple Text Editor - {filepath}")


# def save_file():
#     """Save the current file as a new file."""
#     filepath = asksaveasfilename(
#         defaultextension=".txt",
#         filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
#     )
#     if not filepath:
#         return
#     with open(filepath, mode="w", encoding="utf-8") as output_file:
#         text = txt_edit.get("1.0", tk.END)
#         output_file.write(text)
#     window.title(f"Simple Text Editor - {filepath}")



# window = tk.Tk()
# window.title("Simple Text Editor")


# window.rowconfigure(0, minsize=800, weight=1)
# window.columnconfigure(1, minsize=800, weight=1)

# txt_edit = tk.Text(window)
# frm_buttons = tk.Frame(window, relief=tk.RAISED, bd=2)
# btn_open = tk.Button(frm_buttons, text="Open", command=open_file)
# btn_save = tk.Button(frm_buttons, text="Save As...", command=save_file)

# btn_open.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
# btn_save.grid(row=1, column=0, sticky="ew", padx=5)

# frm_buttons.grid(row=0, column=0, sticky="ns")
# txt_edit.grid(row=0, column=1, sticky="nsew") 

# def motion(event):
#   print("Mouse position: (%s %s)" % (event.x, event.y))
#   return
# frm_buttons.bind('<Motion>', motion)

# window.mainloop()


def on_mouse_move(event):
    print("Mouse position: (%s %s)" % (event.x, event.y))
    return

def on_click(event):
    print("Mouse position: (%s %s)" % (event.x, event.y))
    return


# window = tk.Tk()
# window.title("Simple Text Editor")


# # window.rowconfigure(0, minsize=800, weight=1)
# # window.columnconfigure(1, minsize=800, weight=1)
# s = ttk.Style()
# s.configure('My.TFrame', background='red')

# frm = tk.Frame(window)
# # frm.grid()

# frm_raw = tk.Frame(frm, bd=2)
# frm_raw.grid(column=0, row=0)
# frm_binary = tk.Frame(frm, bd=2)
# frm_binary.grid(column=1, row=0)
# frm_binary.bind('<Motion>', on_mouse_move)
# frm_binary.bind('<Button-1>', on_click)

# btn_open = tk.Button(frm_binary, text="Open")
# btn_open.grid(row=0, column=0, sticky="ew", padx=5, pady=5)


# window.mainloop()

def key_release(e):
    print(f'release {e.char}')

def motion(event):
  print("Mouse position: (%s %s)" % (event.x, event.y))
  return


capture = cv2.VideoCapture(0)

window = tk.Tk()
window.title("Simple Text Editor")
window.rowconfigure(0, minsize=800, weight=1)
window.columnconfigure(1, minsize=1280, weight=1)


frm_raw = tk.Frame(window, width=480, height=360, relief=tk.RAISED)
frm_raw.grid(row=0, column=0, sticky="ns")
frm_raw.configure(bg='red')
frm_binary = tk.Frame(window,  relief=tk.RAISED)
frm_binary.grid(row=0, column=1, sticky="ns")

img_raw = tk.Label(frm_raw)
img_raw.grid(row=0, column=0)


# btn_open = tk.Button(frm_raw, text="Open")
# btn_save = tk.Button(frm_raw, text="Save As...")
# btn_open.grid(row=0, column=0, rowspan=1, sticky="ew", padx=5, pady=5)
# btn_save.grid(row=1, column=0, rowspan=1, sticky="ew", padx=5)


frm_raw.bind('<Motion>', motion)
window.bind("<KeyRelease>", key_release)


while(True):
    ret, frame = capture.read()
    # frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    # print(frame)
    
    img = Image.fromarray(frame)
    target_width = 720

    factor_width = (target_width / float(img.size[0]))
    height = int((float(img.size[1]) * float(factor_width)))
    img = img.resize((target_width, height), Image.ANTIALIAS)

    img_tk = ImageTk.PhotoImage(image=img)
    img_raw.configure(image=img_tk)
    img_raw.image = img_tk

    window.update()

# window.mainloop()

