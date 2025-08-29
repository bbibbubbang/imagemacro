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

    def edit(self, parent: tk.Tk):
        top = tk.Toplevel(parent)
        top.title("이미지 단계")
        top.geometry("400x200")

        tk.Label(top, text="이미지 경로:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        path_entry = tk.Entry(top, width=30)
        path_entry.insert(0, self.path)
        path_entry.grid(row=0, column=1, padx=5, pady=5)

        def browse():
            file = filedialog.askopenfilename(title="이미지 선택")
            if file:
                path_entry.delete(0, tk.END)
                path_entry.insert(0, file)

        tk.Button(top, text="찾아보기", command=browse).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(top, text="모드:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        modes = [
            ("성공할 때까지", "until_success"),
            ("최대 시도 횟수", "max_attempts"),
            ("실패 시 분기", "fail_branch"),
        ]
        for i, (label, value) in enumerate(modes):
            tk.Radiobutton(top, text=label, variable=self.mode, value=value).grid(
                row=1, column=1 + i, sticky="w", padx=5, pady=5
            )

        tk.Label(top, text="시도 횟수:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        attempts_entry = tk.Entry(top, width=5)
        attempts_entry.insert(0, str(self.max_attempts.get()))
        attempts_entry.grid(row=2, column=1, sticky="w", padx=5, pady=5)

        tk.Label(top, text="실패 시:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        fail_opts = [
            ("중지", "stop"),
            ("분기", "branch"),
        ]
        for i, (label, value) in enumerate(fail_opts):
            tk.Radiobutton(top, text=label, variable=self.fail_action, value=value).grid(
                row=3, column=1 + i, sticky="w", padx=5, pady=5
            )

        def ok():
            self.path = path_entry.get()
            try:
                self.max_attempts.set(int(attempts_entry.get()))
            except ValueError:
                messagebox.showerror("오류", "시도 횟수는 정수여야 합니다")
                return
            top.destroy()

        tk.Button(top, text="확인", command=ok).grid(row=4, column=1, padx=5, pady=5)
        tk.Button(top, text="취소", command=top.destroy).grid(row=4, column=2, padx=5, pady=5)
        top.grab_set()
        parent.wait_window(top)


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

    def edit(self, parent: tk.Tk):
        top = tk.Toplevel(parent)
        top.title("마우스 단계")
        top.geometry("400x200")

        tk.Label(top, text="X:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        x_entry = tk.Entry(top, width=6)
        x_entry.insert(0, str(self.x.get()))
        x_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(top, text="Y:").grid(row=0, column=2, sticky="w", padx=5, pady=5)
        y_entry = tk.Entry(top, width=6)
        y_entry.insert(0, str(self.y.get()))
        y_entry.grid(row=0, column=3, padx=5, pady=5)

        def capture(event=None):
            if pyautogui:
                pos = pyautogui.position()
                x_entry.delete(0, tk.END)
                x_entry.insert(0, str(pos.x))
                y_entry.delete(0, tk.END)
                y_entry.insert(0, str(pos.y))
            else:
                messagebox.showinfo("정보", "pyautogui를 사용할 수 없습니다")

        top.bind("<F10>", capture)

        tk.Label(top, text="버튼:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        buttons = {"왼쪽": "left", "오른쪽": "right", "가운데": "middle"}
        button_combo = ttk.Combobox(top, values=list(buttons.keys()), state="readonly")
        current_button = next(k for k, v in buttons.items() if v == self.button.get())
        button_combo.set(current_button)
        button_combo.grid(row=1, column=1, padx=5, pady=5)

        tk.Label(top, text="동작:").grid(row=1, column=2, sticky="w", padx=5, pady=5)
        actions = {"클릭": "click", "누르기": "press", "떼기": "release"}
        action_combo = ttk.Combobox(top, values=list(actions.keys()), state="readonly")
        current_action = next(k for k, v in actions.items() if v == self.action.get())
        action_combo.set(current_action)
        action_combo.grid(row=1, column=3, padx=5, pady=5)

        double_chk = tk.Checkbutton(top, text="더블", variable=self.double)
        double_chk.grid(row=2, column=0, sticky="w", padx=5, pady=5)

        tk.Label(top, text="간격(초):").grid(row=2, column=1, sticky="w", padx=5, pady=5)
        interval_entry = tk.Entry(top, width=6)
        interval_entry.insert(0, str(self.interval.get()))
        interval_entry.grid(row=2, column=2, padx=5, pady=5)

        def ok():
            try:
                self.x.set(int(x_entry.get()))
                self.y.set(int(y_entry.get()))
                self.interval.set(float(interval_entry.get()))
            except ValueError:
                messagebox.showerror("오류", "잘못된 숫자 값")
                return
            self.button.set(buttons[button_combo.get()])
            self.action.set(actions[action_combo.get()])
            top.unbind("<F10>")
            top.destroy()

        tk.Button(top, text="확인", command=ok).grid(row=3, column=1, padx=5, pady=5)
        tk.Button(top, text="취소", command=top.destroy).grid(row=3, column=2, padx=5, pady=5)
        top.grab_set()
        parent.wait_window(top)


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

    def edit(self, parent: tk.Tk):
        top = tk.Toplevel(parent)
        top.title("키보드 단계")
        top.geometry("400x200")

        tk.Label(top, text="키:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        key_entry = tk.Entry(top, width=10)
        key_entry.insert(0, self.key.get())
        key_entry.grid(row=0, column=1, padx=5, pady=5)

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

        tk.Button(top, text="입력", command=start_capture).grid(row=0, column=2, padx=5, pady=5)

        tk.Label(top, text="동작:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        actions = [
            ("누르고 떼기", "press_release"),
            ("누르기", "press"),
            ("떼기", "release"),
        ]
        for i, (label, value) in enumerate(actions):
            tk.Radiobutton(top, text=label, variable=self.action, value=value).grid(
                row=1, column=1 + i, sticky="w", padx=5, pady=5
            )

        def ok():
            self.key.set(key_entry.get())
            top.destroy()

        tk.Button(top, text="확인", command=ok).grid(row=2, column=1, padx=5, pady=5)
        tk.Button(top, text="취소", command=top.destroy).grid(row=2, column=2, padx=5, pady=5)
        top.grab_set()
        parent.wait_window(top)


class DelayStep(MacroStep):
    def __init__(self):
        super().__init__("지연")
        self.duration = tk.DoubleVar(value=1.0)

    def summary(self) -> str:
        return f"지연 {self.duration.get():.3f}초"

    def edit(self, parent: tk.Tk):
        top = tk.Toplevel(parent)
        top.title("지연 단계")
        top.geometry("300x120")

        tk.Label(top, text="초:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        entry = tk.Entry(top, width=10)
        entry.insert(0, str(self.duration.get()))
        entry.grid(row=0, column=1, padx=5, pady=5)

        def ok():
            try:
                val = float(entry.get())
            except ValueError:
                messagebox.showerror("오류", "잘못된 숫자")
                return
            if val < 0.001:
                messagebox.showerror("오류", "0.001 이상이어야 합니다")
                return
            self.duration.set(val)
            top.destroy()

        tk.Button(top, text="확인", command=ok).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(top, text="취소", command=top.destroy).grid(row=1, column=2, padx=5, pady=5)
        top.grab_set()
        parent.wait_window(top)


class TextStep(MacroStep):
    def __init__(self):
        super().__init__("텍스트")
        self.text = tk.StringVar(value="")

    def summary(self) -> str:
        txt = self.text.get()
        return f"텍스트: {txt[:10]}" + ("..." if len(txt) > 10 else "")

    def edit(self, parent: tk.Tk):
        top = tk.Toplevel(parent)
        top.title("텍스트 단계")
        top.geometry("400x150")

        tk.Label(top, text="텍스트:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        entry = tk.Entry(top, width=40)
        entry.insert(0, self.text.get())
        entry.grid(row=0, column=1, padx=5, pady=5)

        def ok():
            self.text.set(entry.get())
            top.destroy()

        tk.Button(top, text="확인", command=ok).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(top, text="취소", command=top.destroy).grid(row=1, column=2, padx=5, pady=5)
        top.grab_set()
        parent.wait_window(top)


class RepeatStep(MacroStep):
    def __init__(self):
        super().__init__("반복")
        self.count = tk.IntVar(value=1)

    def summary(self) -> str:
        return f"반복 {self.count.get()}회"

    def edit(self, parent: tk.Tk):
        top = tk.Toplevel(parent)
        top.title("반복 단계")
        top.geometry("300x120")

        tk.Label(top, text="횟수:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        entry = tk.Entry(top, width=5)
        entry.insert(0, str(self.count.get()))
        entry.grid(row=0, column=1, padx=5, pady=5)

        def ok():
            try:
                val = int(entry.get())
            except ValueError:
                messagebox.showerror("오류", "잘못된 숫자")
                return
            self.count.set(val)
            top.destroy()

        tk.Button(top, text="확인", command=ok).grid(row=1, column=1, padx=5, pady=5)
        tk.Button(top, text="취소", command=top.destroy).grid(row=1, column=2, padx=5, pady=5)
        top.grab_set()
        parent.wait_window(top)


class MacroApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.steps: list[MacroStep] = []

        left = tk.Frame(root)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=5)

        tk.Button(left, text="이미지 추가", command=self.add_image).pack(fill=tk.X, pady=2)
        tk.Button(left, text="마우스 추가", command=self.add_mouse).pack(fill=tk.X, pady=2)
        tk.Button(left, text="키보드 추가", command=self.add_keyboard).pack(fill=tk.X, pady=2)
        tk.Button(left, text="지연 추가", command=self.add_delay).pack(fill=tk.X, pady=2)
        tk.Button(left, text="텍스트 추가", command=self.add_text).pack(fill=tk.X, pady=2)
        tk.Button(left, text="반복 추가", command=self.add_repeat).pack(fill=tk.X, pady=2)
        tk.Button(left, text="삭제", command=self.delete_selected).pack(fill=tk.X, pady=2)

        self.listbox = tk.Listbox(root)
        self.listbox.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.listbox.bind('<Double-Button-1>', self.edit_selected)
        self.listbox.bind('<ButtonPress-1>', self.start_drag)
        self.listbox.bind('<B1-Motion>', self.on_drag)
        self.listbox.bind('<Delete>', self.delete_selected)
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

    def delete_selected(self, event=None):
        idx = self.listbox.curselection()
        if not idx:
            return
        i = idx[0]
        del self.steps[i]
        self.listbox.delete(i)

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
    root.title("이미지 매크로 빌더")
    root.geometry("800x600")
    app = MacroApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
