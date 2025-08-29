import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    import pyautogui
except Exception:
    pyautogui = None


class MacroStep:
    """Base class for macro steps."""

    def __init__(self, name: str):
        self.name = name

    def summary(self) -> str:
        return self.name

    def edit(self, parent: tk.Tk):
        """Override in subclasses to configure the step."""
        raise NotImplementedError


class ImageStep(MacroStep):
    def __init__(self):
        super().__init__("Image")
        self.path = ""
        self.mode = tk.StringVar(value="until_success")
        self.max_attempts = tk.IntVar(value=1)
        self.fail_action = tk.StringVar(value="stop")

    def summary(self) -> str:
        return f"Image: {self.path or 'unset'}"

    def edit(self, parent: tk.Tk):
        top = tk.Toplevel(parent)
        top.title("Image step")

        tk.Label(top, text="Image path:").grid(row=0, column=0, sticky="w")
        path_entry = tk.Entry(top, width=30)
        path_entry.insert(0, self.path)
        path_entry.grid(row=0, column=1)

        def browse():
            file = filedialog.askopenfilename(title="Select image")
            if file:
                path_entry.delete(0, tk.END)
                path_entry.insert(0, file)

        tk.Button(top, text="Browse", command=browse).grid(row=0, column=2)

        tk.Label(top, text="Mode:").grid(row=1, column=0, sticky="w")
        modes = [
            ("Until success", "until_success"),
            ("Max attempts", "max_attempts"),
            ("On fail branch", "fail_branch"),
        ]
        for i, (label, value) in enumerate(modes):
            tk.Radiobutton(top, text=label, variable=self.mode, value=value).grid(
                row=1, column=1 + i, sticky="w"
            )

        tk.Label(top, text="Attempts:").grid(row=2, column=0, sticky="w")
        attempts_entry = tk.Entry(top, width=5)
        attempts_entry.insert(0, str(self.max_attempts.get()))
        attempts_entry.grid(row=2, column=1, sticky="w")

        tk.Label(top, text="On fail:").grid(row=3, column=0, sticky="w")
        fail_opts = [
            ("Stop", "stop"),
            ("Branch", "branch"),
        ]
        for i, (label, value) in enumerate(fail_opts):
            tk.Radiobutton(top, text=label, variable=self.fail_action, value=value).grid(
                row=3, column=1 + i, sticky="w"
            )

        def ok():
            self.path = path_entry.get()
            try:
                self.max_attempts.set(int(attempts_entry.get()))
            except ValueError:
                messagebox.showerror("Error", "Attempts must be integer")
                return
            top.destroy()

        tk.Button(top, text="OK", command=ok).grid(row=4, column=1)
        tk.Button(top, text="Cancel", command=top.destroy).grid(row=4, column=2)
        top.grab_set()
        parent.wait_window(top)


class MouseStep(MacroStep):
    def __init__(self):
        super().__init__("Mouse")
        self.x = tk.IntVar(value=0)
        self.y = tk.IntVar(value=0)
        self.button = tk.StringVar(value="left")
        self.action = tk.StringVar(value="click")
        self.double = tk.BooleanVar(value=False)
        self.interval = tk.DoubleVar(value=0.1)

    def summary(self) -> str:
        dbl = " double" if self.double.get() else ""
        return (
            f"Mouse {self.action.get()}{dbl} {self.button.get()} "
            f"@({self.x.get()}, {self.y.get()})"
        )

    def edit(self, parent: tk.Tk):
        top = tk.Toplevel(parent)
        top.title("Mouse step")

        tk.Label(top, text="X:").grid(row=0, column=0, sticky="w")
        x_entry = tk.Entry(top, width=6)
        x_entry.insert(0, str(self.x.get()))
        x_entry.grid(row=0, column=1)

        tk.Label(top, text="Y:").grid(row=0, column=2, sticky="w")
        y_entry = tk.Entry(top, width=6)
        y_entry.insert(0, str(self.y.get()))
        y_entry.grid(row=0, column=3)

        def capture(event=None):
            if pyautogui:
                pos = pyautogui.position()
                x_entry.delete(0, tk.END)
                x_entry.insert(0, str(pos.x))
                y_entry.delete(0, tk.END)
                y_entry.insert(0, str(pos.y))
            else:
                messagebox.showinfo("Info", "pyautogui not available")

        top.bind("<F10>", capture)

        tk.Label(top, text="Button:").grid(row=1, column=0, sticky="w")
        buttons = ["left", "right", "middle"]
        button_combo = ttk.Combobox(top, values=buttons, state="readonly")
        button_combo.set(self.button.get())
        button_combo.grid(row=1, column=1)

        tk.Label(top, text="Action:").grid(row=1, column=2, sticky="w")
        actions = ["click", "press", "release"]
        action_combo = ttk.Combobox(top, values=actions, state="readonly")
        action_combo.set(self.action.get())
        action_combo.grid(row=1, column=3)

        double_chk = tk.Checkbutton(top, text="Double", variable=self.double)
        double_chk.grid(row=2, column=0, sticky="w")

        tk.Label(top, text="Interval(s):").grid(row=2, column=1, sticky="w")
        interval_entry = tk.Entry(top, width=6)
        interval_entry.insert(0, str(self.interval.get()))
        interval_entry.grid(row=2, column=2)

        def ok():
            try:
                self.x.set(int(x_entry.get()))
                self.y.set(int(y_entry.get()))
                self.interval.set(float(interval_entry.get()))
            except ValueError:
                messagebox.showerror("Error", "Invalid numeric value")
                return
            self.button.set(button_combo.get())
            self.action.set(action_combo.get())
            top.unbind("<F10>")
            top.destroy()

        tk.Button(top, text="OK", command=ok).grid(row=3, column=1)
        tk.Button(top, text="Cancel", command=top.destroy).grid(row=3, column=2)
        top.grab_set()
        parent.wait_window(top)


class KeyboardStep(MacroStep):
    def __init__(self):
        super().__init__("Keyboard")
        self.key = tk.StringVar(value="")
        self.action = tk.StringVar(value="press_release")

    def summary(self) -> str:
        return f"Keyboard {self.action.get()} {self.key.get()}"

    def edit(self, parent: tk.Tk):
        top = tk.Toplevel(parent)
        top.title("Keyboard step")

        tk.Label(top, text="Key:").grid(row=0, column=0, sticky="w")
        key_entry = tk.Entry(top, width=10)
        key_entry.insert(0, self.key.get())
        key_entry.grid(row=0, column=1)

        capturing = tk.BooleanVar(value=False)

        def capture_key(event):
            if capturing.get():
                self.key.set(event.keysym)
                key_entry.delete(0, tk.END)
                key_entry.insert(0, self.key.get())
                capturing.set(False)
                top.unbind("<Key>")

        def start_capture():
            capturing.set(True)
            top.bind("<Key>", capture_key)

        tk.Button(top, text="Input", command=start_capture).grid(row=0, column=2)

        tk.Label(top, text="Action:").grid(row=1, column=0, sticky="w")
        actions = [
            ("Press+Release", "press_release"),
            ("Press", "press"),
            ("Release", "release"),
        ]
        for i, (label, value) in enumerate(actions):
            tk.Radiobutton(top, text=label, variable=self.action, value=value).grid(
                row=1, column=1 + i, sticky="w"
            )

        def ok():
            self.key.set(key_entry.get())
            top.destroy()

        tk.Button(top, text="OK", command=ok).grid(row=2, column=1)
        tk.Button(top, text="Cancel", command=top.destroy).grid(row=2, column=2)
        top.grab_set()
        parent.wait_window(top)


class DelayStep(MacroStep):
    def __init__(self):
        super().__init__("Delay")
        self.duration = tk.DoubleVar(value=1.0)

    def summary(self) -> str:
        return f"Delay {self.duration.get():.3f}s"

    def edit(self, parent: tk.Tk):
        top = tk.Toplevel(parent)
        top.title("Delay step")

        tk.Label(top, text="Seconds:").grid(row=0, column=0, sticky="w")
        entry = tk.Entry(top, width=10)
        entry.insert(0, str(self.duration.get()))
        entry.grid(row=0, column=1)

        def ok():
            try:
                val = float(entry.get())
            except ValueError:
                messagebox.showerror("Error", "Invalid number")
                return
            if val < 0.001:
                messagebox.showerror("Error", "Must be >= 0.001")
                return
            self.duration.set(val)
            top.destroy()

        tk.Button(top, text="OK", command=ok).grid(row=1, column=1)
        tk.Button(top, text="Cancel", command=top.destroy).grid(row=1, column=2)
        top.grab_set()
        parent.wait_window(top)


class TextStep(MacroStep):
    def __init__(self):
        super().__init__("Text")
        self.text = tk.StringVar(value="")

    def summary(self) -> str:
        txt = self.text.get()
        return f"Text: {txt[:10]}" + ("..." if len(txt) > 10 else "")

    def edit(self, parent: tk.Tk):
        top = tk.Toplevel(parent)
        top.title("Text step")

        tk.Label(top, text="Text:").grid(row=0, column=0, sticky="w")
        entry = tk.Entry(top, width=40)
        entry.insert(0, self.text.get())
        entry.grid(row=0, column=1)

        def ok():
            self.text.set(entry.get())
            top.destroy()

        tk.Button(top, text="OK", command=ok).grid(row=1, column=1)
        tk.Button(top, text="Cancel", command=top.destroy).grid(row=1, column=2)
        top.grab_set()
        parent.wait_window(top)


class RepeatStep(MacroStep):
    def __init__(self):
        super().__init__("Repeat")
        self.count = tk.IntVar(value=2)

    def summary(self) -> str:
        return f"Repeat x{self.count.get()}"

    def edit(self, parent: tk.Tk):
        top = tk.Toplevel(parent)
        top.title("Repeat step")

        tk.Label(top, text="Count:").grid(row=0, column=0, sticky="w")
        entry = tk.Entry(top, width=5)
        entry.insert(0, str(self.count.get()))
        entry.grid(row=0, column=1)

        def ok():
            try:
                val = int(entry.get())
            except ValueError:
                messagebox.showerror("Error", "Invalid number")
                return
            self.count.set(val)
            top.destroy()

        tk.Button(top, text="OK", command=ok).grid(row=1, column=1)
        tk.Button(top, text="Cancel", command=top.destroy).grid(row=1, column=2)
        top.grab_set()
        parent.wait_window(top)


class MacroApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.steps: list[MacroStep] = []

        left = tk.Frame(root)
        left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Button(left, text="Add Image", command=self.add_image).pack(fill=tk.X)
        tk.Button(left, text="Add Mouse", command=self.add_mouse).pack(fill=tk.X)
        tk.Button(left, text="Add Keyboard", command=self.add_keyboard).pack(fill=tk.X)
        tk.Button(left, text="Add Delay", command=self.add_delay).pack(fill=tk.X)
        tk.Button(left, text="Add Text", command=self.add_text).pack(fill=tk.X)
        tk.Button(left, text="Add Repeat", command=self.add_repeat).pack(fill=tk.X)

        self.listbox = tk.Listbox(root)
        self.listbox.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.listbox.bind('<Double-Button-1>', self.edit_selected)
        self.listbox.bind('<ButtonPress-1>', self.start_drag)
        self.listbox.bind('<B1-Motion>', self.on_drag)
        self.drag_index = None

    def add_step(self, step: MacroStep):
        step.edit(self.root)
        self.steps.append(step)
        self.listbox.insert(tk.END, step.summary())

    def add_image(self):
        self.add_step(ImageStep())

    def add_mouse(self):
        self.add_step(MouseStep())

    def add_keyboard(self):
        self.add_step(KeyboardStep())

    def add_delay(self):
        self.add_step(DelayStep())

    def add_text(self):
        self.add_step(TextStep())

    def add_repeat(self):
        self.add_step(RepeatStep())

    def edit_selected(self, event=None):
        idx = self.listbox.curselection()
        if not idx:
            return
        i = idx[0]
        step = self.steps[i]
        step.edit(self.root)
        self.listbox.delete(i)
        self.listbox.insert(i, step.summary())

    def start_drag(self, event):
        self.drag_index = self.listbox.nearest(event.y)

    def on_drag(self, event):
        i = self.listbox.nearest(event.y)
        if self.drag_index is None or i == self.drag_index:
            return
        item = self.steps.pop(self.drag_index)
        text = self.listbox.get(self.drag_index)
        self.listbox.delete(self.drag_index)
        self.steps.insert(i, item)
        self.listbox.insert(i, text)
        self.drag_index = i


def main():
    root = tk.Tk()
    root.title("Image Macro Builder")
    app = MacroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
