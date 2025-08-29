import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import os
import tempfile

try:
    import pyautogui
except Exception:
    pyautogui = None

try:
    from PIL import Image, ImageTk
except Exception:
    Image = ImageTk = None


class MacroStep:
    """Base class for macro steps."""

    def __init__(self, name: str):
        self.name = name

    def summary(self) -> str:
        return self.name

    def build_editor(self, parent: tk.Widget):
        """Create editor widgets inside *parent*."""
        raise NotImplementedError

    def apply_editor(self) -> bool:
        """Apply values from editor widgets.

        Returns True on success, False if validation failed.
        """
        return True


class ImageStep(MacroStep):
    def __init__(self):
        super().__init__("이미지")
        self.path = ""
        self.mode = tk.StringVar(value="until_success")
        self.max_attempts = tk.IntVar(value=1)
        self.fail_action = tk.StringVar(value="stop")

    def summary(self) -> str:
        mode = self.mode.get()
        if mode == "until_success":
            cond = "성공할 때까지"
        elif mode == "max_attempts":
            fail = "중지" if self.fail_action.get() == "stop" else "분기"
            cond = f"최대 {self.max_attempts.get()}회 실패 시 {fail}"
        elif mode == "fail_branch":
            cond = "실패 시 분기"
        else:
            cond = ""
        prefix = f"[{cond}] " if cond else ""
        return f"{prefix}이미지: {self.path or '미설정'}"

    def build_editor(self, parent: tk.Widget):
        tk.Label(parent, text="이미지 경로:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self._path_entry = tk.Entry(parent, width=30)
        self._path_entry.insert(0, self.path)
        self._path_entry.grid(row=0, column=1, padx=5, pady=5)

        def browse():
            file = filedialog.askopenfilename(title="이미지 선택")
            if file:
                self._path_entry.delete(0, tk.END)
                self._path_entry.insert(0, file)

        tk.Button(parent, text="찾아보기", command=browse).grid(row=0, column=2, padx=5, pady=5)

        def capture():
            if pyautogui is None:
                messagebox.showerror("오류", "pyautogui가 필요합니다")
                return
            parent.winfo_toplevel().iconify()

            overlay = tk.Toplevel()
            overlay.attributes("-fullscreen", True)
            overlay.attributes("-topmost", True)
            canvas = tk.Canvas(overlay, cursor="cross")
            canvas.pack(fill=tk.BOTH, expand=True)

            bg = None
            if Image and ImageTk:
                shot = pyautogui.screenshot()
                bg = ImageTk.PhotoImage(shot)
                canvas.create_image(0, 0, image=bg, anchor="nw")

            start = {"x": 0, "y": 0}
            rect = {"id": None}

            def on_press(event):
                start["x"], start["y"] = event.x, event.y
                rect["id"] = canvas.create_rectangle(event.x, event.y, event.x, event.y, outline="red")

            def on_drag(event):
                if rect["id"]:
                    canvas.coords(rect["id"], start["x"], start["y"], event.x, event.y)

            def on_release(event):
                overlay.destroy()
                x1 = overlay.winfo_rootx() + start["x"]
                y1 = overlay.winfo_rooty() + start["y"]
                x2 = overlay.winfo_rootx() + event.x
                y2 = overlay.winfo_rooty() + event.y
                region = (min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1))
                img = pyautogui.screenshot(region=region)
                fd, tmp = tempfile.mkstemp(suffix=".png")
                os.close(fd)
                img.save(tmp)
                self._path_entry.delete(0, tk.END)
                self._path_entry.insert(0, tmp)
                parent.winfo_toplevel().deiconify()

            overlay.bind("<ButtonPress-3>", on_press)
            overlay.bind("<B3-Motion>", on_drag)
            overlay.bind("<ButtonRelease-3>", on_release)
            overlay.bind("<ButtonPress-1>", lambda e: (overlay.destroy(), parent.winfo_toplevel().deiconify()))
            overlay.grab_set()
            parent.wait_window(overlay)

        tk.Button(parent, text="캡쳐", command=capture).grid(row=0, column=3, padx=5, pady=5)

        tk.Label(parent, text="모드:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        modes = [
            ("성공할 때까지", "until_success"),
            ("최대 시도 횟수", "max_attempts"),
            ("실패 시 분기", "fail_branch"),
        ]
        for i, (label, value) in enumerate(modes):
            tk.Radiobutton(parent, text=label, variable=self.mode, value=value).grid(
                row=1, column=1 + i, sticky="w", padx=5, pady=5
            )

        tk.Label(parent, text="시도 횟수:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self._attempts_entry = tk.Entry(parent, width=5)
        self._attempts_entry.insert(0, str(self.max_attempts.get()))
        self._attempts_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        tk.Label(parent, text="실패 시:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        fail_opts = [
            ("중지", "stop"),
            ("분기", "branch"),
        ]
        for i, (label, value) in enumerate(fail_opts):
            tk.Radiobutton(parent, text=label, variable=self.fail_action, value=value).grid(
                row=3, column=1 + i, sticky="w", padx=5, pady=5
            )

    def apply_editor(self) -> bool:
        self.path = self._path_entry.get()
        try:
            self.max_attempts.set(int(self._attempts_entry.get()))
        except ValueError:
            messagebox.showerror("오류", "시도 횟수는 정수여야 합니다")
            return False
        return True



class MouseStep(MacroStep):
    def __init__(self):
        super().__init__("마우스")
        self.x = tk.IntVar(value=0)
        self.y = tk.IntVar(value=0)
        self.button = tk.StringVar(value="left")
        self.action = tk.StringVar(value="click")
        self.double = tk.BooleanVar(value=False)
        self.interval = tk.DoubleVar(value=0.1)

    def summary(self) -> str:
        btn_names = {"left": "왼쪽", "right": "오른쪽", "middle": "가운데"}
        act_names = {"click": "클릭", "press": "누르기", "release": "떼기"}
        dbl = " 더블" if self.double.get() else ""
        return (
            f"마우스 {act_names.get(self.action.get(), self.action.get())}{dbl} "
            f"{btn_names.get(self.button.get(), self.button.get())} "
            f"@({self.x.get()}, {self.y.get()})"
        )

    def build_editor(self, parent: tk.Widget):
        tk.Label(parent, text="X:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self._x_entry = tk.Entry(parent, width=6)
        self._x_entry.insert(0, str(self.x.get()))
        self._x_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(parent, text="Y:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        self._y_entry = tk.Entry(parent, width=6)
        self._y_entry.insert(0, str(self.y.get()))
        self._y_entry.grid(row=0, column=3, padx=5, pady=5)

        def capture(event=None):
            if pyautogui:
                pos = pyautogui.position()
                self._x_entry.delete(0, tk.END)
                self._x_entry.insert(0, str(pos.x))
                self._y_entry.delete(0, tk.END)
                self._y_entry.insert(0, str(pos.y))
            else:
                messagebox.showinfo("정보", "pyautogui를 사용할 수 없습니다")

        parent.bind("<F10>", capture)

        tk.Label(parent, text="버튼:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        buttons = {"왼쪽": "left", "오른쪽": "right", "가운데": "middle"}
        self._button_combo = ttk.Combobox(parent, values=list(buttons.keys()), state="readonly")
        self._button_combo.set(next(k for k, v in buttons.items() if v == self.button.get()))
        self._button_combo.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(parent, text="동작:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        actions = {"클릭": "click", "누르기": "press", "떼기": "release"}
        self._action_combo = ttk.Combobox(parent, values=list(actions.keys()), state="readonly")
        self._action_combo.set(next(k for k, v in actions.items() if v == self.action.get()))
        self._action_combo.grid(row=1, column=3, padx=5, pady=5)

        tk.Checkbutton(parent, text="더블", variable=self.double).grid(row=2, column=0, sticky="w", padx=5, pady=5)

        tk.Label(parent, text="간격(초):").grid(row=2, column=1, sticky="w", padx=5, pady=5)
        self._interval_entry = tk.Entry(parent, width=6)
        self._interval_entry.insert(0, str(self.interval.get()))
        self._interval_entry.grid(row=2, column=2, padx=5, pady=5)

    def apply_editor(self) -> bool:
        buttons = {"왼쪽": "left", "오른쪽": "right", "가운데": "middle"}
        actions = {"클릭": "click", "누르기": "press", "떼기": "release"}
        try:
            self.x.set(int(self._x_entry.get()))
            self.y.set(int(self._y_entry.get()))
            self.interval.set(float(self._interval_entry.get()))
        except ValueError:
            messagebox.showerror("오류", "잘못된 숫자 값")
            return False
        self.button.set(buttons[self._button_combo.get()])
        self.action.set(actions[self._action_combo.get()])
        return True


class KeyboardStep(MacroStep):
    def __init__(self):
        super().__init__("키보드")
        self.key = tk.StringVar(value="")
        self.action = tk.StringVar(value="press_release")

    def summary(self) -> str:
        act_names = {
            "press_release": "누르고 떼기",
            "press": "누르기",
            "release": "떼기",
        }
        return f"키보드 {act_names.get(self.action.get(), self.action.get())} {self.key.get()}"

    def build_editor(self, parent: tk.Widget):
        tk.Label(parent, text="키:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self._key_entry = tk.Entry(parent, width=10)
        self._key_entry.insert(0, self.key.get())
        self._key_entry.grid(row=0, column=1, padx=5, pady=5)

        capturing = tk.BooleanVar(value=False)

        def capture_key(event):
            if capturing.get():
                self.key.set(event.keysym)
                self._key_entry.delete(0, tk.END)
                self._key_entry.insert(0, self.key.get())
                capturing.set(False)
                parent.unbind("<Key>")

        def start_capture():
            capturing.set(True)
            parent.bind("<Key>", capture_key)

        tk.Button(parent, text="입력", command=start_capture).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(parent, text="동작:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        actions = [
            ("누르고 떼기", "press_release"),
            ("누르기", "press"),
            ("떼기", "release"),
        ]
        for i, (label, value) in enumerate(actions):
            tk.Radiobutton(parent, text=label, variable=self.action, value=value).grid(
                row=1, column=1 + i, sticky="w", padx=5, pady=5
            )

    def apply_editor(self) -> bool:
        self.key.set(self._key_entry.get())
        return True


class DelayStep(MacroStep):
    def __init__(self):
        super().__init__("지연")
        self.duration = tk.DoubleVar(value=1.0)

    def summary(self) -> str:
        return f"지연 {self.duration.get():.3f}초"

    def build_editor(self, parent: tk.Widget):
        tk.Label(parent, text="초:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self._entry = tk.Entry(parent, width=10)
        self._entry.insert(0, str(self.duration.get()))
        self._entry.grid(row=0, column=1, padx=5, pady=5)

    def apply_editor(self) -> bool:
        try:
            val = float(self._entry.get())
        except ValueError:
            messagebox.showerror("오류", "잘못된 숫자")
            return False
        if val < 0.001:
            messagebox.showerror("오류", "0.001 이상이어야 합니다")
            return False
        self.duration.set(val)
        return True


class TextStep(MacroStep):
    def __init__(self):
        super().__init__("텍스트")
        self.text = tk.StringVar(value="")

    def summary(self) -> str:
        txt = self.text.get()
        return f"텍스트: {txt[:10]}" + ("..." if len(txt) > 10 else "")

    def build_editor(self, parent: tk.Widget):
        tk.Label(parent, text="텍스트:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self._entry = tk.Entry(parent, width=40)
        self._entry.insert(0, self.text.get())
        self._entry.grid(row=0, column=1, padx=5, pady=5)

    def apply_editor(self) -> bool:
        self.text.set(self._entry.get())
        return True


class RepeatStep(MacroStep):
    def __init__(self):
        super().__init__("반복")
        self.count = tk.IntVar(value=1)

    def summary(self) -> str:
        return f"반복 {self.count.get()}회"

    def build_editor(self, parent: tk.Widget):
        tk.Label(parent, text="횟수:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self._entry = tk.Entry(parent, width=5)
        self._entry.insert(0, str(self.count.get()))
        self._entry.grid(row=0, column=1, padx=5, pady=5)

    def apply_editor(self) -> bool:
        try:
            self.count.set(int(self._entry.get()))
        except ValueError:
            messagebox.showerror("오류", "잘못된 숫자")
            return False
        return True


class MacroApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.steps: list[MacroStep] = []

        self.editor_width = 250
        self.editor = tk.Frame(root, width=self.editor_width, bd=1, relief=tk.SUNKEN)
        self.editor.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        self.editor.pack_propagate(False)

        buttons = tk.Frame(root)
        buttons.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        tk.Button(buttons, text="이미지 추가", command=self.add_image).pack(fill=tk.X, pady=5)
        tk.Button(buttons, text="마우스 추가", command=self.add_mouse).pack(fill=tk.X, pady=5)
        tk.Button(buttons, text="키보드 추가", command=self.add_keyboard).pack(fill=tk.X, pady=5)
        tk.Button(buttons, text="지연 추가", command=self.add_delay).pack(fill=tk.X, pady=5)
        tk.Button(buttons, text="텍스트 추가", command=self.add_text).pack(fill=tk.X, pady=5)
        tk.Button(buttons, text="반복 추가", command=self.add_repeat).pack(fill=tk.X, pady=5)
        tk.Button(buttons, text="삭제", command=self.delete_selected).pack(fill=tk.X, pady=5)

        self.listbox = tk.Listbox(root)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.listbox.bind('<Double-Button-1>', self.edit_selected)
        self.listbox.bind('<ButtonPress-1>', self.start_drag)
        self.listbox.bind('<B1-Motion>', self.on_drag)
        self.listbox.bind('<Delete>', self.delete_selected)
        self.drag_index = None

        self.editing_step: MacroStep | None = None
        self.editing_index: int | None = None

    def open_editor(self, step: MacroStep, index: int | None):
        if self.editing_step is not None:
            self.close_editor()
        for w in self.editor.winfo_children():
            w.destroy()
        self.editing_step = step
        self.editing_index = index
        form = tk.Frame(self.editor)
        form.pack(fill=tk.BOTH, expand=True)
        step.build_editor(form)
        btns = tk.Frame(self.editor)
        btns.pack(fill=tk.X, pady=5)
        tk.Button(btns, text="확인", command=self.confirm_edit).pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="취소", command=self.cancel_edit).pack(side=tk.LEFT, padx=5)
        self.editor.update_idletasks()
        req_width = self.editor.winfo_reqwidth()
        if req_width > self.editor_width:
            self.editor_width = req_width
        self.editor.config(width=self.editor_width)

    def confirm_edit(self):
        if not self.editing_step or not self.editing_step.apply_editor():
            return
        if self.editing_index is None:
            self.steps.append(self.editing_step)
            self.listbox.insert(tk.END, self.editing_step.summary())
        else:
            self.listbox.delete(self.editing_index)
            self.listbox.insert(self.editing_index, self.editing_step.summary())
        self.close_editor()

    def cancel_edit(self):
        self.close_editor()

    def close_editor(self):
        for w in self.editor.winfo_children():
            w.destroy()
        self.editing_step = None
        self.editing_index = None

    def add_step(self, step: MacroStep):
        self.open_editor(step, None)

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

    def delete_selected(self, event=None):
        idx = self.listbox.curselection()
        if not idx:
            return
        if self.editing_step is not None:
            self.close_editor()
        i = idx[0]
        del self.steps[i]
        self.listbox.delete(i)

    def edit_selected(self, event=None):
        idx = self.listbox.curselection()
        if not idx:
            return
        i = idx[0]
        self.open_editor(self.steps[i], i)

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
        if self.editing_index is not None:
            if self.drag_index == self.editing_index:
                self.editing_index = i
            elif self.drag_index < self.editing_index <= i:
                self.editing_index -= 1
            elif i <= self.editing_index < self.drag_index:
                self.editing_index += 1
        self.drag_index = i


def main():
    root = tk.Tk()
    root.title("이미지 매크로 빌더")
    root.geometry("600x400")
    app = MacroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
