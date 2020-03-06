import tkinter as tk
from tkinter import simpledialog


class CaptchaSolverFacade:
    __captchaText = ""

    def __init__(self):
        self.__captchaText = ""

    def solve_captcha(self, base64_image):
        root = tk.Tk()
        root.withdraw()
        usr_input = simpledialog.askstring(title="Captcha Text", prompt="Please type the captcha text?:")
        self.__captchaText = usr_input
        return self.__captchaText
