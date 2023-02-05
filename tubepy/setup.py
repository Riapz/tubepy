import tkinter
import customtkinter as ctk
from app import audio_download
from settings import download_path_settings

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")
# ctk.set_widget_scaling(float_value)  # widget dimensions and text size
# ctk.set_window_scaling(float_value)  # window geometry dimensions 

app = ctk.CTk()
app.geometry("840x640")
app.title("Tubepy")

# #009999 is a placeholder color for the app
entry = ctk.CTkEntry(master=app, border_color="#009999", text_color="#009999", placeholder_text="Enter Youtube URL here", width=500, height=50, border_width=2, corner_radius=50)
entry.place(relx=0.5, rely=0.125, anchor=tkinter.CENTER)

def button_event():
    url = entry.get()
    
    # TODO: length of url shouldnt be less than 20 and not greater than 2048
    print(url)
    print(len(url))
    
button = ctk.CTkButton(master=app, text="Download", command=button_event, width=150, height=50, border_width=0, corner_radius=50)
button.place(relx=0.5, rely=0.28, anchor=tkinter.CENTER)

app.mainloop()