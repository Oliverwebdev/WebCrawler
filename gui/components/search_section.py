# gui/components/search_section.py
import tkinter as tk
from tkinter import ttk
import logging

logger = logging.getLogger('SearchSection')


class SearchSection:
    def __init__(self, parent, search_callback):
        """
        Initialisiert die Suchsektion.

        Args:
            parent: Übergeordnetes Tkinter-Widget
            search_callback: Callback-Funktion für die Suche
        """
        self.parent = parent
        self.search_callback = search_callback
        self.create_widgets()

    def create_widgets(self):
        """Erstellt die Such-Widgets."""
        # Hauptframe
        self.frame = ttk.LabelFrame(self.parent, text="Suche", padding="5")
        self.frame.pack(fill=tk.X, padx=5, pady=5)

        # Suchfeld
        search_frame = ttk.Frame(self.frame)
        search_frame.pack(fill=tk.X, pady=5)

        self.keyword_var = tk.StringVar()
        ttk.Label(search_frame, text="Suchbegriff:").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(
            search_frame, textvariable=self.keyword_var)
        self.search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Quelle mit Otto Option
        source_frame = ttk.Frame(search_frame)
        source_frame.pack(side=tk.LEFT, padx=(10, 0))

        ttk.Label(source_frame, text="Quelle:").pack(side=tk.LEFT)
        self.source_var = tk.StringVar(value="all")

        sources = [
            ("Alle", "all"),
            ("eBay", "ebay"),
            ("Amazon", "amazon"),
            ("Otto", "otto"),
            ("Kleinanzeigen", "kleinanzeigen")
        ]
        # alles einbauen was hingehört

        for text, value in sources:
            ttk.Radiobutton(
                source_frame,
                text=text,
                variable=self.source_var,
                value=value
            ).pack(side=tk.LEFT, padx=2)

        # Erweiterte Optionen
        options_frame = ttk.Frame(self.frame)
        options_frame.pack(fill=tk.X, pady=5)

        # Preisbereich
        price_frame = ttk.Frame(options_frame)
        price_frame.pack(side=tk.LEFT)

        ttk.Label(price_frame, text="Preis von:").pack(side=tk.LEFT)
        self.min_price_var = tk.StringVar()
        ttk.Entry(price_frame, textvariable=self.min_price_var,
                  width=8).pack(side=tk.LEFT, padx=5)

        ttk.Label(price_frame, text="bis:").pack(side=tk.LEFT)
        self.max_price_var = tk.StringVar()
        ttk.Entry(price_frame, textvariable=self.max_price_var,
                  width=8).pack(side=tk.LEFT, padx=5)

        # Zustand
        condition_frame = ttk.Frame(options_frame)
        condition_frame.pack(side=tk.LEFT, padx=20)

        ttk.Label(condition_frame, text="Zustand:").pack(side=tk.LEFT)
        self.condition_var = tk.StringVar(value="alle")
        ttk.Combobox(
            condition_frame,
            textvariable=self.condition_var,
            values=["alle", "neu", "gebraucht"],
            state="readonly",
            width=10
        ).pack(side=tk.LEFT, padx=5)

        # Suchbutton
        self.search_button = ttk.Button(
            self.frame,
            text="Suche starten",
            command=self.start_search,
            style='Search.TButton'
        )
        self.search_button.pack(pady=10)

        # Bind Enter-Taste zum Starten der Suche
        self.search_entry.bind('<Return>', lambda e: self.start_search())

    def start_search(self):
        """Startet die Suche mit den eingegebenen Parametern."""
        try:
            keyword = self.keyword_var.get().strip()
            source = self.source_var.get()
            min_price = self.min_price_var.get().strip()
            max_price = self.max_price_var.get().strip()
            condition = self.condition_var.get()

            # Validierung
            if not keyword:
                return

            # Konvertiere Preise wenn angegeben
            try:
                min_price = float(min_price) if min_price else None
                max_price = float(max_price) if max_price else None
            except ValueError:
                logger.error("Ungültige Preiseingabe")
                return

            condition = None if condition == "alle" else condition

            logger.debug(f"Starte Suche: Quelle={source}, Keyword={keyword}, "
                         f"Preis={min_price}-{max_price}, Zustand={condition}")

            self.search_callback(
                keyword=keyword,
                source=source,
                min_price=min_price,
                max_price=max_price,
                condition=condition
            )

        except Exception as e:
            logger.error(f"Fehler beim Starten der Suche: {e}")
