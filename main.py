import tkinter as tk

# Есептеу функциясы
def esepteu():
    try:
        san = float(entry.get())

        kvadrat = san ** 2
        kub = san ** 3

        result_label.config(
            text=f"Квадраты: {kvadrat}\nКубы: {kub}",
            fg="green"
        )

    except ValueError:
        result_label.config(
            text="Қате: Сан енгізіңіз!",
            fg="red"
        )

# Терезе құру
window = tk.Tk()
window.title("Санның квадраты және кубы")
window.geometry("300x200")

# Жазу
label = tk.Label(window, text="Санды енгізіңіз:")
label.pack(pady=5)

# Енгізу өрісі
entry = tk.Entry(window)
entry.pack(pady=5)

# Батырма
button = tk.Button(window, text="Есептеу", command=esepteu)
button.pack(pady=10)

# Нәтиже өрісі
result_label = tk.Label(window, text="Нәтиже:")
result_label.pack(pady=10)

# Бағдарламаны іске қосу
window.mainloop()