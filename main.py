import tkinter as tk
from gui import EbayScraperGUI

def main():
    root = tk.Tk()
    app = EbayScraperGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()