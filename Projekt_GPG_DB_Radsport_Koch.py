# =====================================================================
# IMPORTE: Hier holen wir uns die Werkzeuge, die Python von Haus aus
# nicht direkt geladen hat, um Speicherplatz zu sparen.
# =====================================================================
import sqlite3  # Importiert die Datenbank-Funktion (SQLite braucht keinen extra Server!)

# Importiert alle GUI-Elemente (Knöpfe, Tabellen, Textfelder) aus der PySide6-Bibliothek
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                               QHBoxLayout, QPushButton, QLineEdit, QLabel,
                               QTableWidget, QTableWidgetItem, QTabWidget,
                               QComboBox, QMessageBox, QHeaderView, QStatusBar,
                               QCheckBox)
from PySide6.QtCore import Qt


# =====================================================================
# 1. DATENBANK-SETUP (Wird ganz unten beim Programmstart aufgerufen)
# =====================================================================
def init_db():
    # 'with' öffnet die Datei radsport_koch.db und schließt sie am Ende automatisch sicher ab.
    with sqlite3.connect("radsport_koch.db") as conn:
        cursor = conn.cursor()  # Der Cursor ist unser "Schreibstift" für die Datenbank

        # Schaltet den Schutz für Fremdschlüssel ein (verhindert Bestellungen ohne Kunden)
        cursor.execute("PRAGMA foreign_keys = ON;")

        # --- TABELLE KUNDEN ---
        # 'aktiv INTEGER DEFAULT 1' ist der Trick für unseren Papierkorb (Soft Delete).
        # 1 bedeutet sichtbar, 0 bedeutet im Papierkorb.
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS kunden
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           name
                           TEXT
                           NOT
                           NULL,
                           email
                           TEXT,
                           aktiv
                           INTEGER
                           DEFAULT
                           1
                       )
                       """)

        # --- TABELLE ARTIKEL ---
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS artikel
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           bezeichnung
                           TEXT
                           NOT
                           NULL,
                           preis
                           REAL,
                           aktiv
                           INTEGER
                           DEFAULT
                           1
                       )
                       """)

        # --- TABELLE BESTELLUNGEN ---
        # Verknüpft (REFERENCES) die Kunden-ID und Artikel-ID, um das relationale Modell aufzubauen.
        cursor.execute("""
                       CREATE TABLE IF NOT EXISTS bestellungen
                       (
                           id
                           INTEGER
                           PRIMARY
                           KEY
                           AUTOINCREMENT,
                           kunde_id
                           INTEGER,
                           artikel_id
                           INTEGER,
                           menge
                           INTEGER,
                           aktiv
                           INTEGER
                           DEFAULT
                           1,
                           FOREIGN
                           KEY
                       (
                           kunde_id
                       ) REFERENCES kunden
                       (
                           id
                       ),
                           FOREIGN KEY
                       (
                           artikel_id
                       ) REFERENCES artikel
                       (
                           id
                       )
                           )
                       """)
        conn.commit()  # Speichert die Tabellenstruktur fest auf der Festplatte


# =====================================================================
# 2. GRAFISCHE OBERFLÄCHE (Das Hauptfenster der App)
# =====================================================================
class RadsportApp(QMainWindow):  # Erbt alle Eigenschaften eines Standard-Fensters
    def __init__(self):
        super().__init__()

        # Fenstertitel und Startgröße in Pixeln festlegen
        self.setWindowTitle("Verwaltung Radsport Koch GmbH - ULTIMATE")
        self.resize(1050, 700)

        # Variablen, um sich zu merken, ob wir gerade "Neuanlegen" oder "Bearbeiten"
        self.k_edit_id = None
        self.a_edit_id = None

        # Die kleine Leiste ganz unten für "Erfolgreich gespeichert"-Meldungen
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("System bereit.", 5000)  # Text verschwindet nach 5 Sekunden

        # Baut das Karteikartensystem (Reiter) für die drei Kategorien
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.tab_kunden = QWidget()
        self.tab_artikel = QWidget()
        self.tab_bestellungen = QWidget()

        self.tabs.addTab(self.tab_kunden, "👥 Kunden")
        self.tabs.addTab(self.tab_artikel, "🚲 Artikel")
        self.tabs.addTab(self.tab_bestellungen, "🛒 Bestellungen & Umsatz")

        # Ruft die Unterfunktionen auf, um Textfelder und Knöpfe auf die Reiter zu malen
        self.setup_kunden_tab()
        self.setup_artikel_tab()
        self.setup_bestellungen_tab()

        # Lädt sofort nach dem Zeichnen des Fensters die Daten aus der SQLite-Datei
        self.load_kunden()
        self.load_artikel()
        self.load_bestellungen()

    # Kleine Hilfsfunktion für schickere, gestreifte Tabellen, die sich der Fensterbreite anpassen
    def style_table(self, table):
        header = table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        table.setSelectionBehavior(QTableWidget.SelectRows)  # Ein Klick markiert die ganze Zeile

    # --- KUNDEN TAB DESIGN ---
    def setup_kunden_tab(self):
        layout = QVBoxLayout()  # Haupt-Layout: Ordnet alles von oben nach unten an (Vertikal)

        # 1. Zeile: Eingabefelder (Horizontal angeordnet)
        input_layout = QHBoxLayout()
        self.k_name_input = QLineEdit()
        self.k_name_input.setPlaceholderText("Name des Kunden")
        self.k_email_input = QLineEdit()
        self.k_email_input.setPlaceholderText("E-Mail Adresse")
        self.btn_add_k = QPushButton("➕ Kunde anlegen")

        # SIGNAL: Wenn der Button geklickt wird, starte die Funktion 'save_kunde'
        self.btn_add_k.clicked.connect(self.save_kunde)

        input_layout.addWidget(self.k_name_input)
        input_layout.addWidget(self.k_email_input)
        input_layout.addWidget(self.btn_add_k)

        # 2. Zeile: Suchfeld und Aktions-Knöpfe
        search_layout = QHBoxLayout()
        self.k_search_input = QLineEdit()
        self.k_search_input.setPlaceholderText("Suchen nach Name...")
        self.k_search_input.textChanged.connect(self.search_kunde)  # Live-Suche beim Tippen

        # Die Checkbox für den Papierkorb
        self.cb_k_trash = QCheckBox("🗑️ Papierkorb anzeigen")
        self.cb_k_trash.stateChanged.connect(self.toggle_k_trash)

        btn_edit = QPushButton("✏️ Bearbeiten")
        btn_edit.clicked.connect(self.edit_kunde)

        self.btn_del_k = QPushButton("🗑️ Löschen")
        self.btn_del_k.setObjectName("deleteButton")  # Gibt dem Button intern einen Namen fürs rote CSS-Design
        self.btn_del_k.clicked.connect(self.delete_kunde)

        # Der rote "Endgültig löschen"-Button (am Anfang unsichtbar mit .hide())
        self.btn_hard_del_k = QPushButton("🔥 Endgültig löschen")
        self.btn_hard_del_k.setObjectName("deleteButton")
        self.btn_hard_del_k.clicked.connect(self.hard_delete_kunde)
        self.btn_hard_del_k.hide()

        search_layout.addWidget(self.k_search_input)
        search_layout.addWidget(self.cb_k_trash)
        search_layout.addWidget(btn_edit)
        search_layout.addWidget(self.btn_del_k)
        search_layout.addWidget(self.btn_hard_del_k)

        # 3. Zeile: Die große Tabelle
        self.table_kunden = QTableWidget(0, 3)  # Startet mit 0 Zeilen und 3 Spalten
        self.table_kunden.setHorizontalHeaderLabels(["ID", "Name", "E-Mail"])
        self.style_table(self.table_kunden)

        # Packt alle drei Zeilen in das Hauptlayout des Reiters
        layout.addLayout(input_layout)
        layout.addLayout(search_layout)
        layout.addWidget(self.table_kunden)
        self.tab_kunden.setLayout(layout)

    # --- ARTIKEL TAB DESIGN --- (Logik ist fast 1:1 identisch zu Kunden)
    def setup_artikel_tab(self):
        layout = QVBoxLayout()

        input_layout = QHBoxLayout()
        self.a_bez_input = QLineEdit()
        self.a_bez_input.setPlaceholderText("Artikelbezeichnung")
        self.a_preis_input = QLineEdit()
        self.a_preis_input.setPlaceholderText("Preis (z.B. 499.99)")
        self.btn_add_a = QPushButton("➕ Artikel anlegen")
        self.btn_add_a.clicked.connect(self.save_artikel)
        input_layout.addWidget(self.a_bez_input)
        input_layout.addWidget(self.a_preis_input)
        input_layout.addWidget(self.btn_add_a)

        search_layout = QHBoxLayout()
        self.a_search_input = QLineEdit()
        self.a_search_input.setPlaceholderText("Suchen nach Artikel...")
        self.a_search_input.textChanged.connect(self.search_artikel)

        self.cb_a_trash = QCheckBox("🗑️ Papierkorb anzeigen")
        self.cb_a_trash.stateChanged.connect(self.toggle_a_trash)

        btn_edit = QPushButton("✏️ Bearbeiten")
        btn_edit.clicked.connect(self.edit_artikel)

        self.btn_del_a = QPushButton("🗑️ Löschen")
        self.btn_del_a.setObjectName("deleteButton")
        self.btn_del_a.clicked.connect(self.delete_artikel)

        self.btn_hard_del_a = QPushButton("🔥 Endgültig löschen")
        self.btn_hard_del_a.setObjectName("deleteButton")
        self.btn_hard_del_a.clicked.connect(self.hard_delete_artikel)
        self.btn_hard_del_a.hide()

        search_layout.addWidget(self.a_search_input)
        search_layout.addWidget(self.cb_a_trash)
        search_layout.addWidget(btn_edit)
        search_layout.addWidget(self.btn_del_a)
        search_layout.addWidget(self.btn_hard_del_a)

        self.table_artikel = QTableWidget(0, 3)
        self.table_artikel.setHorizontalHeaderLabels(["ID", "Bezeichnung", "Preis (€)"])
        self.style_table(self.table_artikel)

        layout.addLayout(input_layout)
        layout.addLayout(search_layout)
        layout.addWidget(self.table_artikel)
        self.tab_artikel.setLayout(layout)

    # --- BESTELLUNGEN TAB DESIGN ---
    def setup_bestellungen_tab(self):
        layout = QVBoxLayout()

        # Dropdown-Menüs (QComboBox) statt normaler Textfelder
        input_layout = QHBoxLayout()
        self.cb_kunden = QComboBox()
        self.cb_artikel = QComboBox()
        self.b_menge_input = QLineEdit()
        self.b_menge_input.setPlaceholderText("Menge (z.B. 2)")

        btn_add = QPushButton("➕ Bestellung anlegen")
        btn_add.clicked.connect(self.add_bestellung)

        input_layout.addWidget(QLabel("Kunde:"))
        input_layout.addWidget(self.cb_kunden, stretch=2)
        input_layout.addWidget(QLabel("Artikel:"))
        input_layout.addWidget(self.cb_artikel, stretch=2)
        input_layout.addWidget(self.b_menge_input, stretch=1)
        input_layout.addWidget(btn_add)

        action_layout = QHBoxLayout()

        # Das mehrzeilige Info-Feld für die Umsatzberechnung
        self.umsatz_label = QLabel()
        self.umsatz_label.setStyleSheet("""
            font-size: 14px; 
            font-weight: bold; 
            color: #1f2937; 
            background-color: #f3f4f6; 
            padding: 10px; 
            border-radius: 6px;
            border: 1px solid #d1d5db;
        """)

        self.cb_b_trash = QCheckBox("🗑️ Stornierte anzeigen")
        self.cb_b_trash.stateChanged.connect(self.toggle_b_trash)

        self.btn_del_b = QPushButton("🗑️ Stornieren")
        self.btn_del_b.setObjectName("deleteButton")
        self.btn_del_b.clicked.connect(self.delete_bestellung)

        self.btn_hard_del_b = QPushButton("🔥 Endgültig löschen")
        self.btn_hard_del_b.setObjectName("deleteButton")
        self.btn_hard_del_b.clicked.connect(self.hard_delete_bestellung)
        self.btn_hard_del_b.hide()

        action_layout.addWidget(self.umsatz_label)
        action_layout.addStretch()  # Schiebt alle folgenden Buttons ganz nach rechts
        action_layout.addWidget(self.cb_b_trash)
        action_layout.addWidget(self.btn_del_b)
        action_layout.addWidget(self.btn_hard_del_b)

        self.table_bestellungen = QTableWidget(0, 5)
        self.table_bestellungen.setHorizontalHeaderLabels(
            ["Bestell-ID", "Kundenname", "Artikel", "Menge", "Gesamtpreis"])
        self.style_table(self.table_bestellungen)

        layout.addLayout(input_layout)
        layout.addLayout(action_layout)
        layout.addWidget(self.table_bestellungen)
        self.tab_bestellungen.setLayout(layout)

    # =====================================================================
    # 3. DATENBANK-FUNKTIONEN (Die echte Logik des Programms)
    # =====================================================================

    # Zentrale Hilfsfunktion: Nimmt einen SQL-Befehl, schickt ihn an SQLite und fängt Fehler ab.
    # So müssen wir nicht vor jedem Befehl 'try/except' schreiben.
    def execute_query(self, query, params=()):
        with sqlite3.connect("radsport_koch.db") as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA foreign_keys = ON;")
            try:
                cursor.execute(query, params)
                conn.commit()
                return cursor.fetchall()  # Gibt die gefundenen Daten (z.B. bei SELECT) zurück
            except sqlite3.Error as e:
                # Pop-up bei Datenbankfehlern (z.B. Foreign Key Constraint Failed)
                QMessageBox.critical(self, "Datenbankfehler", f"Ein Fehler ist aufgetreten:\n{e}")
                return None

    # --- KUNDEN LOGIK ---

    # Wird aufgerufen, wenn man das Papierkorb-Häkchen anklickt
    def toggle_k_trash(self):
        if self.cb_k_trash.isChecked():
            # Wechsel in den Papierkorb-Modus
            self.btn_del_k.setText("♻️ Wiederherstellen")
            self.btn_del_k.setStyleSheet("background-color: #f59e0b; color: white;")  # Wird orange
            self.btn_hard_del_k.show()  # Der "echte" Löschen-Button taucht auf
        else:
            # Zurück in den Normal-Modus
            self.btn_del_k.setText("🗑️ Löschen")
            self.btn_del_k.setStyleSheet("")
            self.btn_hard_del_k.hide()  # "Echte" Löschen-Button wird wieder versteckt
        self.load_kunden()

        # Lade-Funktion (READ)

    def load_kunden(self, search_term=""):
        # Ternärer Operator: Wenn Checkbox an ist, suche nach 0 (gelöscht), sonst 1 (aktiv)
        aktiv_status = 0 if self.cb_k_trash.isChecked() else 1

        # Der SQL Befehl mit oder ohne Suchbegriff (LIKE %)
        query = "SELECT id, name, email FROM kunden WHERE aktiv = ? AND name LIKE ?" if search_term else "SELECT id, name, email FROM kunden WHERE aktiv = ?"
        params = (aktiv_status, '%' + search_term + '%') if search_term else (aktiv_status,)

        daten = self.execute_query(query, params)
        self.table_kunden.setRowCount(0)  # Tabelle erst leer räumen

        if daten:
            for row_idx, row_data in enumerate(daten):  # Schleife durch alle gefundenen Kunden
                self.table_kunden.insertRow(row_idx)
                for col_idx, cell_data in enumerate(row_data):
                    self.table_kunden.setItem(row_idx, col_idx, QTableWidgetItem(str(cell_data)))
        self.update_dropdowns()  # Wichtig: Aktualisiert die Dropdowns für Neubestellungen

    # Holt den angeklickten Kunden aus der Tabelle in die Textfelder oben
    def edit_kunde(self):
        row = self.table_kunden.currentRow()
        if row >= 0:
            if self.cb_k_trash.isChecked():
                QMessageBox.warning(self, "Info", "Bitte stelle den Kunden erst wieder her, um ihn zu bearbeiten.")
                return

            # Liest die Werte aus der Tabelle aus und merkt sich die ID
            self.k_edit_id = self.table_kunden.item(row, 0).text()
            self.k_name_input.setText(self.table_kunden.item(row, 1).text())
            self.k_email_input.setText(self.table_kunden.item(row, 2).text())

            # Verwandelt den Anlegen-Button in einen grünen Speichern-Button
            self.btn_add_k.setText("💾 Änderungen speichern")
            self.btn_add_k.setStyleSheet("background-color: #10b981;")
        else:
            QMessageBox.warning(self, "Achtung", "Bitte wähle einen Kunden aus!")

    # CREATE & UPDATE kombiniert in einem Button
    def save_kunde(self):
        name = self.k_name_input.text().strip()
        email = self.k_email_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Fehler", "Bitte gib einen Namen ein!")
            return

        if self.k_edit_id:
            # Wenn eine ID gemerkt wurde -> Mache ein UPDATE (Bearbeiten)
            self.execute_query("UPDATE kunden SET name = ?, email = ? WHERE id = ?", (name, email, self.k_edit_id))
            self.k_edit_id = None
            self.btn_add_k.setText("➕ Kunde anlegen")
            self.btn_add_k.setStyleSheet("")
            self.status_bar.showMessage("Änderungen gespeichert!", 3000)
        else:
            # Wenn keine ID gemerkt wurde -> Mache ein INSERT (Neuer Kunde)
            self.execute_query("INSERT INTO kunden (name, email) VALUES (?, ?)", (name, email))
            self.status_bar.showMessage(f"Kunde '{name}' erfolgreich hinzugefügt!", 3000)

        # Felder leeren und Tabelle neu laden
        self.k_name_input.clear()
        self.k_email_input.clear()
        self.load_kunden()
        self.load_bestellungen()

    def search_kunde(self):
        self.load_kunden(self.k_search_input.text())

    # SOFT DELETE (Nur den Status auf 0 oder 1 setzen)
    def delete_kunde(self):
        row = self.table_kunden.currentRow()
        if row >= 0:
            k_id = self.table_kunden.item(row, 0).text()
            if self.cb_k_trash.isChecked():
                # WIEDERHERSTELLEN (Status zurück auf 1)
                self.execute_query("UPDATE kunden SET aktiv = 1 WHERE id = ?", (k_id,))
                self.status_bar.showMessage("Kunde erfolgreich wiederhergestellt!", 3000)
            else:
                # IN DEN PAPIERKORB (Status auf 0)
                antwort = QMessageBox.question(self, "Löschen", "Kunde in den Papierkorb verschieben?",
                                               QMessageBox.Yes | QMessageBox.No)
                if antwort == QMessageBox.Yes:
                    self.execute_query("UPDATE kunden SET aktiv = 0 WHERE id = ?", (k_id,))
                    self.status_bar.showMessage("Kunde in den Papierkorb verschoben.", 3000)
            self.load_kunden()
            self.load_bestellungen()
        else:
            QMessageBox.warning(self, "Achtung", "Bitte wähle zuerst einen Kunden aus!")

    # HARD DELETE (Endgültig von der Festplatte fegen)
    def hard_delete_kunde(self):
        row = self.table_kunden.currentRow()
        if row >= 0:
            k_id = self.table_kunden.item(row, 0).text()
            antwort = QMessageBox.warning(self, "Achtung!",
                                          "Willst du diesen Kunden wirklich ENDGÜLTIG aus der Datenbank löschen?\nDas kann nicht rückgängig gemacht werden!",
                                          QMessageBox.Yes | QMessageBox.No)
            if antwort == QMessageBox.Yes:
                # WICHTIG: Damit SQLite nicht meckert, müssen erst alle Bestellungen des Kunden gelöscht werden!
                self.execute_query("DELETE FROM bestellungen WHERE kunde_id = ?", (k_id,))
                # Danach kann der Kunde selbst gefahrlos gelöscht werden.
                self.execute_query("DELETE FROM kunden WHERE id = ?", (k_id,))

                self.load_kunden()
                self.load_bestellungen()
                self.status_bar.showMessage("Kunde endgültig gelöscht.", 3000)
        else:
            QMessageBox.warning(self, "Achtung", "Bitte wähle zuerst einen Kunden aus!")

    # --- ARTIKEL LOGIK --- (Gleiches Prinzip wie bei Kunden)
    def toggle_a_trash(self):
        if self.cb_a_trash.isChecked():
            self.btn_del_a.setText("♻️ Wiederherstellen")
            self.btn_del_a.setStyleSheet("background-color: #f59e0b; color: white;")
            self.btn_hard_del_a.show()
        else:
            self.btn_del_a.setText("🗑️ Löschen")
            self.btn_del_a.setStyleSheet("")
            self.btn_hard_del_a.hide()
        self.load_artikel()

    def load_artikel(self, search_term=""):
        aktiv_status = 0 if self.cb_a_trash.isChecked() else 1
        query = "SELECT id, bezeichnung, preis FROM artikel WHERE aktiv = ? AND bezeichnung LIKE ?" if search_term else "SELECT id, bezeichnung, preis FROM artikel WHERE aktiv = ?"
        params = (aktiv_status, '%' + search_term + '%') if search_term else (aktiv_status,)

        daten = self.execute_query(query, params)
        self.table_artikel.setRowCount(0)
        if daten:
            for row_idx, row_data in enumerate(daten):
                self.table_artikel.insertRow(row_idx)
                for col_idx, cell_data in enumerate(row_data):
                    # Formatiert die Zahl in Spalte 2 als schicken Euro-Betrag (z.B. 499.00 €)
                    text = f"{cell_data:.2f} €" if col_idx == 2 else str(cell_data)
                    self.table_artikel.setItem(row_idx, col_idx, QTableWidgetItem(text))
        self.update_dropdowns()

    def edit_artikel(self):
        row = self.table_artikel.currentRow()
        if row >= 0:
            if self.cb_a_trash.isChecked():
                QMessageBox.warning(self, "Info", "Bitte stelle den Artikel erst wieder her, um ihn zu bearbeiten.")
                return
            self.a_edit_id = self.table_artikel.item(row, 0).text()
            self.a_bez_input.setText(self.table_artikel.item(row, 1).text())
            # Entfernt das " €"-Zeichen aus dem Textfeld, da es beim Speichern als Zahl stört
            preis_sauber = self.table_artikel.item(row, 2).text().replace(" €", "")
            self.a_preis_input.setText(preis_sauber)
            self.btn_add_a.setText("💾 Änderungen speichern")
            self.btn_add_a.setStyleSheet("background-color: #10b981;")
        else:
            QMessageBox.warning(self, "Achtung", "Bitte wähle einen Artikel aus!")

    def save_artikel(self):
        bez = self.a_bez_input.text().strip()
        preis_text = self.a_preis_input.text().replace(',',
                                                       '.')  # Ersetzt Komma durch Punkt, falls der User ein Komma tippt
        if not bez or not preis_text:
            QMessageBox.warning(self, "Fehler", "Bitte Bezeichnung und Preis eingeben!")
            return
        try:
            preis = float(preis_text)  # Prüft, ob es wirklich eine gültige Zahl ist
        except ValueError:
            QMessageBox.warning(self, "Fehler", "Der Preis muss eine gültige Zahl sein!")
            return

        if self.a_edit_id:
            self.execute_query("UPDATE artikel SET bezeichnung = ?, preis = ? WHERE id = ?",
                               (bez, preis, self.a_edit_id))
            self.a_edit_id = None
            self.btn_add_a.setText("➕ Artikel anlegen")
            self.btn_add_a.setStyleSheet("")
            self.status_bar.showMessage("Artikel aktualisiert!", 3000)
        else:
            self.execute_query("INSERT INTO artikel (bezeichnung, preis) VALUES (?, ?)", (bez, preis))
            self.status_bar.showMessage(f"Artikel '{bez}' angelegt!", 3000)

        self.a_bez_input.clear()
        self.a_preis_input.clear()
        self.load_artikel()
        self.load_bestellungen()

    def search_artikel(self):
        self.load_artikel(self.a_search_input.text())

    def delete_artikel(self):
        row = self.table_artikel.currentRow()
        if row >= 0:
            a_id = self.table_artikel.item(row, 0).text()
            if self.cb_a_trash.isChecked():
                self.execute_query("UPDATE artikel SET aktiv = 1 WHERE id = ?", (a_id,))
                self.status_bar.showMessage("Artikel wiederhergestellt!", 3000)
            else:
                antwort = QMessageBox.question(self, "Löschen", "Artikel in den Papierkorb verschieben?",
                                               QMessageBox.Yes | QMessageBox.No)
                if antwort == QMessageBox.Yes:
                    self.execute_query("UPDATE artikel SET aktiv = 0 WHERE id = ?", (a_id,))
                    self.status_bar.showMessage("Artikel in den Papierkorb verschoben.", 3000)
            self.load_artikel()
            self.load_bestellungen()
        else:
            QMessageBox.warning(self, "Achtung", "Bitte wähle zuerst einen Artikel aus!")

    def hard_delete_artikel(self):
        row = self.table_artikel.currentRow()
        if row >= 0:
            a_id = self.table_artikel.item(row, 0).text()
            antwort = QMessageBox.warning(self, "Achtung!",
                                          "Willst du diesen Artikel wirklich ENDGÜLTIG aus der Datenbank löschen?",
                                          QMessageBox.Yes | QMessageBox.No)
            if antwort == QMessageBox.Yes:
                # Auch hier: Erst alle Bestellungen stornieren/löschen, in denen der Artikel vorkommt
                self.execute_query("DELETE FROM bestellungen WHERE artikel_id = ?", (a_id,))
                self.execute_query("DELETE FROM artikel WHERE id = ?", (a_id,))
                self.load_artikel()
                self.load_bestellungen()
                self.status_bar.showMessage("Artikel endgültig gelöscht.", 3000)
        else:
            QMessageBox.warning(self, "Achtung", "Bitte wähle zuerst einen Artikel aus!")

    # --- BESTELLUNGEN LOGIK ---
    def toggle_b_trash(self):
        if self.cb_b_trash.isChecked():
            self.btn_del_b.setText("♻️ Wiederherstellen")
            self.btn_del_b.setStyleSheet("background-color: #f59e0b; color: white;")
            self.btn_hard_del_b.show()
        else:
            self.btn_del_b.setText("🗑️ Stornieren")
            self.btn_del_b.setStyleSheet("")
            self.btn_hard_del_b.hide()
        self.load_bestellungen()

    # Lädt die aktuellen, nicht gelöschten Kunden und Artikel in die Dropdown-Menüs
    def update_dropdowns(self):
        self.cb_kunden.clear()
        kunden = self.execute_query("SELECT id, name FROM kunden WHERE aktiv = 1")
        if kunden:
            for k in kunden:
                # Zeigt dem Nutzer den Namen an, speichert aber intern die ID des Kunden ab!
                self.cb_kunden.addItem(f"{k[1]}", k[0])

        self.cb_artikel.clear()
        artikel = self.execute_query("SELECT id, bezeichnung FROM artikel WHERE aktiv = 1")
        if artikel:
            for a in artikel:
                self.cb_artikel.addItem(f"{a[1]}", a[0])

    def load_bestellungen(self):
        aktiv_status = 0 if self.cb_b_trash.isChecked() else 1

        # Ein Meisterstück: Der SQL-JOIN.
        # Verbindet die 3 Tabellen miteinander, damit wir in der Liste Namen statt nackter IDs sehen.
        # Gleichzeitig berechnet SQL schon den Preis pro Zeile ((b.menge * a.preis))
        query = """
                SELECT b.id, k.name, a.bezeichnung, b.menge, (b.menge * a.preis)
                FROM bestellungen b
                         JOIN kunden k ON b.kunde_id = k.id
                         JOIN artikel a ON b.artikel_id = a.id
                WHERE b.aktiv = ? \
                """
        daten = self.execute_query(query, (aktiv_status,))
        self.table_bestellungen.setRowCount(0)

        if daten:
            for row_idx, row_data in enumerate(daten):
                self.table_bestellungen.insertRow(row_idx)
                for col_idx, cell_data in enumerate(row_data):
                    text = f"{cell_data:.2f} €" if col_idx == 4 else str(cell_data)
                    self.table_bestellungen.setItem(row_idx, col_idx, QTableWidgetItem(text))

        self.calculate_revenue()  # Aktualisiert die grüne Umsatz-Box unten

    # Berechnet den Brutto- und Netto-Umsatz aller aktiven Rechnungen
    def calculate_revenue(self):
        # Lässt die Datenbank alle Mengen mal alle Preise addieren (SUM)
        query = """
                SELECT SUM(b.menge * a.preis)
                FROM bestellungen b
                         JOIN artikel a ON b.artikel_id = a.id
                WHERE b.aktiv = 1 \
                """
        result = self.execute_query(query)
        brutto_umsatz = result[0][0] if result and result[0][0] else 0.0  # Falls nichts da ist, nimm 0.0

        # Mathematik: Bruttowert durch 1,19 teilen ergibt den Nettowert (ohne 19% MwSt)
        netto_umsatz = brutto_umsatz / 1.19
        mwst = brutto_umsatz - netto_umsatz

        # Baut den Text zusammen und formatiert die Zahlen (z.B. 1.500,00)
        text = (f"💰 Brutto-Umsatz:  {brutto_umsatz:,.2f} €\n"
                f"➖ 19% MwSt:         {mwst:,.2f} €\n"
                f"📊 Netto-Umsatz:    {netto_umsatz:,.2f} €")

        # Python macht Tausender-Trennpunkte englisch (1,000.00). Das hier übersetzt es ins Deutsche (1.000,00).
        text = text.replace(',', 'X').replace('.', ',').replace('X', '.')
        self.umsatz_label.setText(text)

    def add_bestellung(self):
        # Holt sich die versteckten IDs aus den Dropdown-Menüs
        kunde_id = self.cb_kunden.currentData()
        artikel_id = self.cb_artikel.currentData()
        menge = self.b_menge_input.text().strip()

        if not kunde_id or not artikel_id:
            QMessageBox.warning(self, "Fehler", "Bitte erst Kunden und Artikel anlegen!")
            return

        if not menge.isdigit() or int(menge) <= 0:
            QMessageBox.warning(self, "Fehler", "Die Menge muss eine ganze Zahl sein!")
            return

        self.execute_query("INSERT INTO bestellungen (kunde_id, artikel_id, menge) VALUES (?, ?, ?)",
                           (kunde_id, artikel_id, int(menge)))
        self.b_menge_input.clear()
        self.load_bestellungen()
        self.status_bar.showMessage("Bestellung erfolgreich gespeichert!", 3000)

    def delete_bestellung(self):
        row = self.table_bestellungen.currentRow()
        if row >= 0:
            b_id = self.table_bestellungen.item(row, 0).text()
            if self.cb_b_trash.isChecked():
                self.execute_query("UPDATE bestellungen SET aktiv = 1 WHERE id = ?", (b_id,))
                self.status_bar.showMessage("Bestellung wiederhergestellt.", 3000)
            else:
                antwort = QMessageBox.question(self, "Stornieren", "Bestellung stornieren?",
                                               QMessageBox.Yes | QMessageBox.No)
                if antwort == QMessageBox.Yes:
                    self.execute_query("UPDATE bestellungen SET aktiv = 0 WHERE id = ?", (b_id,))
                    self.status_bar.showMessage("Bestellung storniert.", 3000)
            self.load_bestellungen()
        else:
            QMessageBox.warning(self, "Achtung", "Bitte wähle zuerst eine Bestellung in der Tabelle aus!")

    def hard_delete_bestellung(self):
        row = self.table_bestellungen.currentRow()
        if row >= 0:
            b_id = self.table_bestellungen.item(row, 0).text()
            antwort = QMessageBox.warning(self, "Achtung!", "Willst du diese Bestellung wirklich ENDGÜLTIG löschen?",
                                          QMessageBox.Yes | QMessageBox.No)
            if antwort == QMessageBox.Yes:
                self.execute_query("DELETE FROM bestellungen WHERE id = ?", (b_id,))
                self.load_bestellungen()
                self.status_bar.showMessage("Bestellung endgültig gelöscht.", 3000)
        else:
            QMessageBox.warning(self, "Achtung", "Bitte wähle zuerst eine Bestellung aus!")


# =====================================================================
# 4. PROGRAMM START & DESIGN
# =====================================================================
init_db()  # Ruft die Datenbank-Funktion ganz oben auf, um zu prüfen, ob die Datei radsport_koch.db existiert

app = QApplication([])  # Der unsichtbare Motor, der das Fenster antreibt
app.setStyle("Fusion")  # Zwingt das Programm, auf Mac und Windows gleich modern auszusehen

# Modernes CSS-Design (Cascading Style Sheets, wie beim Webdesign)
# Macht die Buttons farbig, rundet Ecken ab und gibt Hover-Effekte (Verfärben beim Drüberfahren)
modern_style = """
    QMainWindow { background-color: #f8f9fa; }
    QTableWidget { background-color: #ffffff; border-radius: 8px; border: 1px solid #dee2e6; gridline-color: #f1f3f5; font-size: 13px; }
    QHeaderView::section { background-color: #e9ecef; padding: 6px; border: none; font-weight: bold; color: #495057; }
    QPushButton { background-color: #3b82f6; color: white; border-radius: 6px; padding: 8px 15px; font-weight: bold; font-size: 13px; border: none; }
    QPushButton:hover { background-color: #2563eb; } 
    QPushButton#deleteButton { background-color: #ef4444; } /* Rote Farbe für Löschen-Buttons */
    QPushButton#deleteButton:hover { background-color: #dc2626; }
    QLineEdit, QComboBox { padding: 8px; border: 1px solid #ced4da; border-radius: 6px; background-color: #ffffff; font-size: 13px; }
    QLineEdit:focus, QComboBox:focus { border: 1px solid #3b82f6; } /* Blauer Rand, wenn man rein klickt */
    QMessageBox { background-color: #ffffff; }
    QCheckBox { font-size: 13px; color: #4b5563; font-weight: bold; }
"""
app.setStyleSheet(modern_style)  # Wendet das Design an

window = RadsportApp()  # Erzeugt das Fenster
window.show()  # Macht das Fenster auf dem Bildschirm sichtbar
app.exec()  # Die Endlosschleife: Hält das Programm offen und wartet auf Mausklicks