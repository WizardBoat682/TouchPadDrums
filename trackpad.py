import tkinter as tk

def hit(drum):
    print("Hit:", drum)

window = tk.Tk()
window.title("TrackPad Drums")
window.geometry("500x400")

positions = [
    ("KICK", 0, 0),
    ("SNARE", 0, 1),
    ("HI-HAT", 1, 0),
    ("TOM", 1, 1)
]

for drum, row, column in positions:
    button = tk.Button(
        window,
        text=drum,
        command=lambda d=drum: hit(d),
        width=20,
        height=8
    )
    
    button.grid(row=row, column=column)

window.mainloop()
