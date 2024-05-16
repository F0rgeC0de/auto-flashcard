import customtkinter
import tkinter as tk
from tkinter import StringVar, filedialog
import sqlite3
import os
import re



# Variables
current_dictionary = {"default_term": "default_definition"}
data_file_directory = None

import_window_on = 0 # 0=off, 1=on
gameplay_on = 0 # 0=in menu, 1=in game
gameplay_stage = 0 # 0=term, 1=definition




class BackEnd:
    def __init__(self):
        # Non Play Variables
        self.card_number_selection = [0]
        self.available_glossaries = [None]
        self.current_glossary = ["None"]
        self.current_glossary_index = [0]

        # Gameplay Variables
        self.game_on = [0]
        self.test_estimate = []
        self.total_correct = [0]
        self.total_terms = [0] # Total Terms in Glossary
        self.test_estimate = [0.0]
        self.active_term = ''
        self.active_definition = ''
        self.active_card = []

        # Database Variables
        database_name = "Default"
        self.database_namedef = "Data" + ".db"
        database_nameinput = "Default"
        database_tablenamedef = "Default"
        database_tablenameinput = "Default"
        self.max_index_value = [0]
        self.add_term = []
        self.add_definition = []
        self.folder_path = "auto-flashcard"
        self.data_folder = f"{self.folder_path}" + "/Data"
        self.database_path = os.path.join(self.data_folder, self.database_namedef)

    # Database Related Functions
    def sanitize_input(self, input):
        if isinstance(input, list) and len(input) == 1:
            input = input[0]
        elif not isinstance(input,str):
            raise ValueError("Input must be string or list containing one string!")
        
        return re.sub(r'\W+', '', input)
        
    def setup_database(self):
        # Ensure db folder exists
        if not os.path.exists(self.data_folder):
            os.makedirs(self.data_folder)

        # Create db file if it doesnt exist
        if not os.path.exists(self.database_path):
            connection = sqlite3.connect(self.database_path)

            cursor = connection.cursor()
            # Creates Default Glossary Template
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS "DefaultGlossary" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL DEFAULT 'blank',
                definition TEXT NOT NULL DEFAULT 'blank'
            )                      
            ''')
                        # id = Table Sequence
                        # term = glossary word
                        # definiton = glossary word definition
                        # seen = 0 or 1 ; used to remove flash cards after presentation (Not Implemented)
                        # known = 0, 1, or 2 ; Used to guage confidents and allow cards to enter the pool again (Not Implemented)
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS "Statistics" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Glossary_id INTEGER NOT NULL,
                Glossary_name TEXT NOT NULL,           
                total_correct INTEGER NOT NULL,
                total_cards INTEGER NOT NULL,
                correct_ratio INTEGER NOT NULL,           
                test_estimate INTEGER NOT NULL
            )                      
            ''')
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS "GlossaryIndex" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Glossary NOT NULL
            )                      
            ''')

            connection.commit()
            connection.close()
            print("Database Initialized")
        else:
            self.get_glossaries()
            print("Database Connected")

    def create_glossary_term_table(self, glossary_name):
        sanitized_glossary_name = self.sanitize_input(glossary_name)
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        insert_term_list = f"CREATE TABLE IF NOT EXISTS {sanitized_glossary_name} (" \
                             "id INTEGER PRIMARY KEY AUTOINCREMENT, " \
                             "term TEXT NOT NULL DEFAULT 'blank', " \
                             "definition TEXT NOT NULL DEFAULT 'blank')"
        #insert_term_list = f"CREATE TABLE IF NOT EXISTS {glossary_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, term TEXT NOT NULL DEFAULT 'blank', definition TEXT NOT NULL DEFAULT 'blank')"
        try:
            cursor.execute(insert_term_list)
            print("Added New Glossary")
        except Exception as e:
            print("Term Table Creation Error!", e)
        conn.commit()
        cursor.close()
        conn.close()

    def add_glossary_term_definition(self):
        glossary = self.sanitize_input(self.current_glossary[0])
        term = self.add_term
        definition = self.add_definition
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        insert_term_definition = f"INSERT INTO {glossary} (term, definition) VALUES ('{term}', '{definition}');"
        cursor.execute(insert_term_definition)
        conn.commit()
        cursor.close()
        conn.close()

    def escape_quotes(self, input):
        return input.replace("'", "''")

    def add_glossary_term_definition_import(self):
        glossary = self.sanitize_input(self.current_glossary[0])
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        for term in self.glossary_dict.keys():
            definition = self.glossary_dict[term]
            safe_term = self.escape_quotes(term)
            safe_def = self.escape_quotes(definition)
            insert_term_definition = f"INSERT INTO {glossary} (term, definition) VALUES ('{safe_term}', '{safe_def}');"
            cursor.execute(insert_term_definition)
        conn.commit()
        cursor.close()
        conn.close()

    def input_term(self, input_term):
        self.add_term = input_term

    def input_definition(self, input_definition):
        self.add_definition = input_definition

    def get_glossaries(self):
        self.available_glossaries.clear()
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        cursor.execute("SELECT Glossary FROM GlossaryIndex")
        fetch_glossaries = cursor.fetchall()
        for name in fetch_glossaries:
            self.available_glossaries.append(name[0])
        cursor.close()
        conn.close()

    def increment_value_test(self):
        self.max_index_value[0] += 1

    def get_glossary_id(self, current_glossary):
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        glossary_id = f"SELECT id FROM GlossaryIndex WHERE Glossary='{current_glossary}';"
        try:
            cursor.execute(glossary_id)
            self.current_glossary_index = cursor.fetchone()[0]
        except Exception as e:
            print("Glossary Number Error!", e)
        cursor.close()
        conn.close()

    def get_max_term_number(self, input_glossary):
        self.max_index_value.clear()
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        maxid_query = f"SELECT MAX(id) FROM ({input_glossary});"
        try:
            cursor.execute(maxid_query)
            max_term = cursor.fetchone()[0]
            self.max_index_value.append(max_term)
        except Exception as e:
            print("Max ID Error!", e)
        if max_term == None:
            self.max_index_value.clear()
            self.max_index_value.append(1)
        else:
            pass 
        cursor.close()
        conn.close()

    def get_max_glossary_index(self, input_glossary):
        self.max_index_value.clear()
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        maxid_query = f"SELECT MAX(id) FROM ({input_glossary});"
        try:
            cursor.execute(maxid_query)
            maxid = cursor.fetchone()[0]
            self.max_index_value[0] = maxid
        except Exception as e:
            print("Max ID Error!", e)
        if maxid == None:
            self.max_index_value.clear()
            self.max_index_value.append(0)
        else:
            pass 
        cursor.close()
        conn.close()

    def get_card_total(self, input_glossary):
        if self.current_glossary[0] != 'None':
            sanitized_glossary_input = self.sanitize_input(input_glossary)
            conn = sqlite3.connect(self.database_path)
            cursor = conn.cursor()
            maxid_query = f"SELECT MAX(id) FROM ({sanitized_glossary_input});"
            try:
                cursor.execute(maxid_query)
                total_terms = cursor.fetchone()[0]
                self.total_terms[0] = total_terms
            except Exception as e:
                print("Card Number Error!", e)
            cursor.close()
            conn.close()
        else:
            print("Card Total 0, No Glossary")

    def insert_test_glossary_name(self):
        self.get_max_glossary_index("GlossaryIndex")
        new_glossary_index = self.max_index_value[0] + 1
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        test_glossary = "Test Glossary " + str(new_glossary_index)
        glossary_query = f"INSERT INTO 'GlossaryIndex' (Glossary) VALUES ('{test_glossary}');"
        try:    
            cursor.execute(glossary_query)
            self.get_max_glossary_index("GlossaryIndex")
            print("Added Glossary ID " + str(new_glossary_index))
            
        except Exception as e:
            print("Database Error Occured!", e)
        conn.commit()
        cursor.close()
        conn.close()

    def insert_glossary_name(self, glossary_name):
        self.get_max_glossary_index("GlossaryIndex")
        # new_glossary_index = self.max_index_value[0] + 1
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        glossary_query = f"INSERT INTO 'GlossaryIndex' (Glossary) VALUES ('{glossary_name}');"
        try:    
            cursor.execute(glossary_query)
            print("Added Glossary ID:" + ' "' + glossary_name + '"')
            
        except Exception as e:
            print("Database Error Occured!", e)
        conn.commit()
        cursor.close()
        conn.close()

    def insert_statistics(self, glossary_index, glossary_name, total_known, total_cards, test_estimate):
        correct_ratio = (total_known/total_cards)*100
        print(correct_ratio)
        conn = sqlite3.connect(self.database_path)
        cursor = conn.cursor()
        statistics_query = f"INSERT INTO 'Statistics' (Glossary_id, Glossary_name, total_correct, total_cards, correct_ratio, test_estimate) VALUES ('{glossary_index}', '{glossary_name}', '{total_known}', '{total_cards}', '{correct_ratio}', '{test_estimate}');"
        try:
            cursor.execute(statistics_query)
            print("Stats Saved")

        except Exception as e:
            print("Statistics Error Occured!", e)
        conn.commit()
        cursor.close()
        conn.close()
    
    # Gameplay functions
    def create_game_dictionary(self, number_of_cards):
        sanitized_input = self.sanitize_input(self.current_glossary)
        conn = sqlite3.connect(self.database_path)
        self.get_card_total(self.current_glossary[0])
        cursor = conn.cursor()
        create_game_dictionary_query = f"SELECT DISTINCT term, definition FROM {sanitized_input} ORDER BY RANDOM() LIMIT ?;"
        # print("Debug SQL Query:", create_game_dictionary_query)
        cursor.execute(create_game_dictionary_query, number_of_cards)
        play_terms = cursor.fetchall()
        #print(play_terms)
        self.game_dictionary = []
        for term in play_terms:
           self.game_dictionary.append(term)
        print(self.game_dictionary)
        pass ## Finish this

    def get_term(self):
        self.active_card = self.game_dictionary[0]
        self.active_term = self.active_card[0]

    def get_definition(self):
        self.active_definition = self.active_card[1]

    def pop_first_card(self):
        self.game_dictionary.pop[0]
    
    def calculate_test_estimate(self, confidence_score):
        # Confidence_score = 1, 2, or 3
        if confidence_score == 1:
            self.test_estimate[0] += 0.25
        elif confidence_score == 2:
            self.test_estimate[0] += 0.6
        elif confidence_score == 3:
            self.test_estimate[0] += 1
        else:
            print("Test Estimate Error! Invalid Input!")

    def analyze_test_estimate(self):
        self.test_estimate_input = self.test_estimate[0] / self.card_number_selection[0]
        self.test_estimate_output = round((round(self.test_estimate_input, 2) * 100), 0)
        return int(self.test_estimate_output)

    def reset_test_estimate(self):
        self.test_estimate[0] = 0.0

    def select_five_cards(self):
        self.card_number_selection[0] = 5

    def select_ten_cards(self):
        self.card_number_selection[0] = 10 

    def select_fifteen_cards(self):
        self.card_number_selection[0] = 15

    def add_five_cards(self):
        self.card_number_selection[0] += 5

    def select_all_cards(self, current_glossary):
        self.get_card_total(current_glossary)
        if self.current_glossary[0] == "None":
            self.card_number_selection[0] = 0
        elif self.total_terms[0] != None:
            self.card_number_selection[0] = self.total_terms[0]
        elif self.total_terms[0] == None:
            self.card_number_selection[0] = 0
            print("No Terms Available!")

    # Button Event Funtions
    def get_glossaries_event(self):
        self.get_glossaries()
        print(self.available_glossaries)

    def add_test_glossaries(self):
        self.insert_glossary_name()

    def setup_database_button(self):
        self.setup_database()
        print("Database Initialized")

    def choose_file(self):
        file_path = filedialog.askopenfilename(title="Select a file",
                                           filetypes=(("Markdown files", "*.md"), ("All files", "*.*")))
        self.chosen_file = file_path
    
    # Debug / Test Methods
    def add_50_test_terms(self):
        term_number = 1
        while term_number < 51:
            self.add_term = "Term " + str(term_number)
            self.add_definition = "Definition " + str(term_number)
            self.add_glossary_term_definition()
            term_number += 1
 
    def parse_highlight_1_line(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()

        self.glossary_dict = {}
        pattern = re.compile(r'<mark style="background: #[A-Fa-f0-9]{8};">(.*?):</mark>\s*(.*)')

        for line_number, line in enumerate(lines):
            match = pattern.search(line)
            if match:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                self.glossary_dict[term] = definition
            else:
                print(f"No glossary entry found in line {line_number}: {line.strip()}")

        return self.glossary_dict, print(self.glossary_dict)

class MyTabView(customtkinter.CTkTabview):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(height=500, width=500)
        self.backend = BackEnd()
        self.backend.setup_database()
        # Frame Variables
        self.game_frame_on = False
        self.glossary_selection_on = False

        # Gameplay Variables 
        self.game_state = 'term' # 'term', 'definition', 'next' or 'stats'
        self.running_total_known = 0
        self.current_card_number = 0

        # create tabs
        self.play_tab = self.add("Play")
        self.settings_tab = self.add("Settings")
        # Dynamic Variables
        self.glossary_text_variable = StringVar()
        if self.backend.current_glossary[0] != "None":
            self.glossary_text_variable.set(self.backend.current_glossary)
        if self.backend.current_glossary[0] == "None":
            self.glossary_text_variable.set("None")
        self.select_glossary_text = self.glossary_text_variable.get()
        self.string_card_number = str(self.backend.card_number_selection[0])
        self.card_number_variable = StringVar()
        self.card_number_variable.set(self.string_card_number)
        self.card_number_text = self.card_number_variable.get()

        # play_tab Widgets
        self.available_glossaries_button = customtkinter.CTkButton(self.play_tab, text="Select Glossary", command=self.open_glossary_selection, font=('TkDefaultFont', 16), height=50, width=250)
        self.available_glossaries_button.grid (row=1, column=2, padx=10, pady=10)
        self.available_glossaries_label = customtkinter.CTkLabel(self.play_tab, text=self.select_glossary_text)
        self.available_glossaries_label.grid (row=2, column=2, padx=10, pady=10)
        self.add_glossary = customtkinter.CTkButton(self.play_tab, text="Add Custom Glossary", command=self.add_glossary_manually)
        self.add_glossary.grid (row=3, column=1, padx=10, pady=10)
        self.import_glossary_button = customtkinter.CTkButton(self.play_tab, text="Import Glossary", command=self.backend.add_test_glossaries)
        self.import_glossary_button.grid (row=3, column=2, padx=10, pady=10)
        self.add_term_manually = customtkinter.CTkButton(self.play_tab, text="Add Term", command=self.add_card_manually)
        self.add_term_manually.grid (row=3,column=3, padx=10, pady=10)
        self.test_button3 = customtkinter.CTkButton(self.play_tab, text="Test Button", command=self.open_glossary_selection)
        self.test_button3.grid (row=4, column=2, padx=10, pady=10)
        self.select_five_cards = customtkinter.CTkButton(self.play_tab, text="5 Cards", command=self.select_five, height=50, width=200)
        self.select_five_cards.grid (row=5, column=1, padx=10, pady=10)
        self.select_ten_cards = customtkinter.CTkButton(self.play_tab, text="10 Cards", command=self.select_ten, height=50, width=200)
        self.select_ten_cards.grid (row=5, column=2, padx=10, pady=10)
        self.select_fifteen_cards = customtkinter.CTkButton(self.play_tab, text="15 Cards", command=self.select_fifteen, height=50, width=200)
        self.select_fifteen_cards.grid (row=5, column=3, padx=10, pady=10)
        self.card_number_selection_label = customtkinter.CTkLabel(self.play_tab, text=self.card_number_text)
        self.card_number_selection_label.grid (row=6, column=1, padx=10, pady=10)
        self.add_five_cards = customtkinter.CTkButton(self.play_tab, text="+ 5", command=self.add_five, height=50, width=125)
        self.add_five_cards.grid (row=6, column=2, padx=10, pady=10)
        self.play_all_cards = customtkinter.CTkButton(self.play_tab, text="All Cards", command=lambda: self.select_all(self.backend.current_glossary[0]), height=50, width=375)
        self.play_all_cards.grid (row=6, column=3, padx=10, pady=10)


        self.play_game_button = customtkinter.CTkButton(self.play_tab, text="Play Game", command=self.open_game_frame, height=50, width=500)
        self.play_game_button.grid (row=7, column=2, padx=10, pady=10)

        # settings_tab Widgets
        self.add_50_test_terms_button = customtkinter.CTkButton(self.settings_tab, text="Add 50 Test Terms", command=self.backend.add_50_test_terms, height=50, width=125)
        self.add_50_test_terms_button.grid (row=1, column=2, padx=10, pady=10)
        self.add_test_glossary = customtkinter.CTkButton(self.settings_tab, text="Add Test Glossary", command=self.backend.add_test_glossaries)
        self.add_test_glossary.grid (row=2, column=2, padx=10, pady=10)
        self.import_highlight_1_line = customtkinter.CTkButton(self.settings_tab, text="Import Highlight 1 Line", command=self.import_glossary)
        self.import_highlight_1_line.grid (row=3, column=2, padx=10, pady=10)

       # self.textbox = customtkinter.CTkTextbox(self.settings_tab, width=100, height=100, corner_radius=0)
       # self.textbox.grid(row=4, column=4, padx=100, pady=10)


        # Label Template
        # self.add_five_cards = customtkinter.CTkButton(self.play_tab, text="+ 5", command=self.backend.add_five_cards, height=50, width=125)
        #  self.add_five_cards.grid (row=6, column=2, padx=10, pady=10)


        # Button Template
        # self.test_button4 = customtkinter.CTkButton(self.play_tab, text="Play Game", command=self.open_game_frame, height=50, width=125)
        # self.test_button4.grid (row=5, column=4, padx=100, pady=10)

    # Import Functions
    def import_glossary(self):
        self.backend.choose_file()
        self.backend.parse_highlight_1_line(self.backend.chosen_file)
        self.backend.add_glossary_term_definition_import()

        

    # Manual Glossary Input
    def add_glossary_manually(self):
        validate_input = 0
        while validate_input <= 0:
            if validate_input == -1:
                input_dialog = customtkinter.CTkInputDialog(text="Please Enter Glossary Name: ", title="Input Glossary Name")
                glossary_input = str(input_dialog.get_input())
            else:
                input_dialog = customtkinter.CTkInputDialog(text="Glossary Name: ", title="Input Glossary Name")
                glossary_input = str(input_dialog.get_input())
                pass

            if len(glossary_input) != 0 and glossary_input != "None":
                validate_input = 1
                self.backend.create_glossary_term_table(glossary_input)
                self.backend.insert_glossary_name(glossary_input)
                print("Glossary Name: " + glossary_input)
            elif glossary_input == "None":
                validate_input = 2
                print("Glossary Addition Cancelled")
            else: 
                validate_input = -1   
                glossary_input = "Blank Glossary" # Just in case something fails, string to placehold in database
                print("No Input! Try Again")
                pass
            
    def add_card_manually(self):
        validate_input = 0
        while validate_input <= 0:
            if validate_input == -1:
                input_dialog = customtkinter.CTkInputDialog(text="Please Enter Term: ", title="Input Term")
                term_input = str(input_dialog.get_input())
            else:
                input_dialog = customtkinter.CTkInputDialog(text="Term: ", title="Input Term")
                term_input = str(input_dialog.get_input())
                pass

            if len(term_input) != 0 and term_input != "None":
                validate_input = 1
                print("Input Term: " + term_input)
            elif term_input == "None":
                validate_input = 2
                print("Term Addition Cancelled")
            else: 
                validate_input = -1   
                term_input = "Blank Term" # Just in case something fails, string to placehold in database
                print("No Input! Try Again")
                pass

        validate_definition = 0
        while validate_input == 1 and validate_definition <= 0:
            if validate_definition == -1:
                definition_dialog = customtkinter.CTkInputDialog(text="Please Enter Definition:", title="Enter Definition")
                definition_input = str(definition_dialog.get_input())
            else:
                definition_dialog = customtkinter.CTkInputDialog(text="Definition:", title="Enter Definition")
                definition_input = str(definition_dialog.get_input())
                pass
            # Checks for closed, and enter with no input
            if len(definition_input) != 0 and definition_input != "None":
                validate_definition = 1
                print("Input Definition: " + definition_input)
            elif definition_input == "None":
                validate_definition = 2
                print("Term Addition Cancelled")
            else:
                validate_definition = -1
                definition_input = "Blank Definition"
                print("No Input! Try Again")


        if self.backend.current_glossary[0] == "None":
            print("No Glossary Selected!")
        elif validate_input == 1 and validate_definition == 1:
            self.backend.input_term(term_input)
            self.backend.input_definition(definition_input)
            try:
                self.backend.add_glossary_term_definition()
                print("Added Term: " + term_input) 
            except Exception as e:
                print("Input Error!", e)
        elif validate_input == 2 or validate_definition == 2:
            print("Cancelled! No Term Added")
        else:
            print("Invalid Input! No Term Added")
            pass

    # Glossary Selection
    def close_glossary_selection(self):
        self.glossary_selection_on = False
        self.glossary_selection_window.attributes('-topmost', False)
        self.glossary_selection_window.destroy()

    def update_current_glossary(self, current_glossary):
        self.backend.current_glossary.clear()
        self.backend.current_glossary.append(current_glossary)
        self.backend.create_glossary_term_table(self.backend.current_glossary[0])
        self.backend.get_glossary_id(self.backend.current_glossary[0])
        self.backend.get_card_total(current_glossary)
        self.available_glossaries_label = customtkinter.CTkLabel(self.play_tab, text=self.backend.current_glossary, font=('TkDefaultFont', 16))
        self.available_glossaries_label.grid (row=2, column=2, padx=10, pady=10)
        print(self.backend.current_glossary_index)
        print("Selected Glossary: " + current_glossary)
        self.close_glossary_selection()

    def change_glossary_selection(self):
        pass

    def open_glossary_selection(self):
        self.backend.get_glossaries()
        if not self.glossary_selection_on:
            self.glossary_selection_window = customtkinter.CTkToplevel(master=self)
            self.glossary_selection_window.title('Select Glossary')
            self.glossary_selection_window.geometry('340x240')
            self.glossary_selection_window.lift()
            self.glossary_selection_window.focus_force()
            self.glossary_selection_window.attributes('-topmost', True)
            self.glossary_selection_window.protocol("WM_DELETE_WINDOW", self.close_glossary_selection)
            self.glossary_selection_frame = customtkinter.CTkScrollableFrame(master=self.glossary_selection_window, width=340, height=240)
            self.glossary_selection_frame.grid(column=0, row=0)
            self.glossary_selection_on = True
            self.glossary_number = [0]
            for glossary in self.backend.available_glossaries:
                self.glossary_number[0] += 1
                glossary_selection_button = customtkinter.CTkButton(self.glossary_selection_frame,text=glossary, command=lambda glossary=glossary: self.update_current_glossary(glossary), width=290)
                glossary_selection_button.grid(column=0, row = self.glossary_number, padx=20, pady=5)

    # Card Number Selection
    def select_five(self):
        self.backend.select_five_cards()
        self.card_number_variable.set(str(self.backend.card_number_selection[0]))
        self.card_number_text = self.card_number_variable.get()
        self.card_number_selection_label.configure(text=self.card_number_text)
        print(self.card_number_text + " Cards")
        #self.card_number_selection_label.configure(text=5)

    def select_ten(self):
        self.backend.select_ten_cards()
        self.card_number_variable.set(str(self.backend.card_number_selection[0]))
        self.card_number_text = self.card_number_variable.get()
        self.card_number_selection_label.configure(text=self.card_number_text)
        print(self.card_number_text + " Cards")


    def select_fifteen(self):
        self.backend.select_fifteen_cards()
        self.card_number_variable.set(str(self.backend.card_number_selection[0]))
        self.card_number_text = self.card_number_variable.get()
        self.card_number_selection_label.configure(text=self.card_number_text)
        print(self.card_number_text + " Cards")


    def select_all(self, current_glossary):
        self.backend.select_all_cards(current_glossary)
        self.card_number_variable.set(str(self.backend.card_number_selection[0]))
        self.card_number_text = self.card_number_variable.get()
        self.card_number_selection_label.configure(text=self.card_number_text)
        print(self.card_number_text + " Cards")


    def add_five(self):
        self.backend.add_five_cards()
        self.card_number_variable.set(str(self.backend.card_number_selection[0]))
        self.card_number_text = self.card_number_variable.get()
        self.card_number_selection_label.configure(text=self.card_number_text)
        print("+5 Cards, " + self.card_number_text + " Cards Selected")




    # Gameplay Window Functions
    def close_game_frame(self): 
        self.game_frame_on = False
        self.game_frame.attributes('-topmost', False)
        self.game_frame.destroy()

    def open_game_frame(self): 
        if not self.game_frame_on and self.backend.current_glossary[0] == "None":     
            self.game_frame = customtkinter.CTkToplevel(master=self, height = 500, width=700)
            self.game_frame.title("Gameplay Window")
            self.game_frame.geometry("700x700")
            self.game_frame.lift()
            self.game_frame.focus_force()
            self.game_frame.attributes('-topmost', True)
            self.game_frame.protocol("WM_DELETE_WINDOW", self.close_game_frame)
            self.game_frame_cards = customtkinter.CTkFrame(self.game_frame, width=500, height=350, border_width=5)
            self.game_frame_cards.pack(padx=100, pady=20)
            self.game_frame_cards.propagate(False) # Stops from resizing based on label
            self.term_label = customtkinter.CTkLabel(master=self.game_frame_cards, text="No Glossary Selected!", font=("CTkFont", 26))
            self.term_label.pack(expand=True, fill="both",padx=20, pady=20)
            # Quit Button
            self.game_quit_button = customtkinter.CTkButton(self.game_frame, text="Quit", command=self.close_game_frame)
            self.game_quit_button.pack(pady=20)
            self.game_frame_on = True

        elif not self.game_frame_on:
            self.running_total_known = [0]
            self.current_card_number = 0
            self.backend.test_estimate = [0.0]
            self.game_state = 'term'
            self.active_term = StringVar()
            self.active_term.set("No Term Selected!")
            self.active_definition = StringVar()
            self.game_frame_on = True

            self.backend.create_game_dictionary(self.backend.card_number_selection)
            self.game_frame = customtkinter.CTkToplevel(master=self, height = 500, width=700)
            self.game_frame.title("Gameplay Window")
            self.game_frame.geometry("700x500")
            self.game_frame.lift()
            self.game_frame.focus_force()
            self.game_frame.attributes('-topmost', True)
            self.game_frame.protocol("WM_DELETE_WINDOW", self.close_game_frame)
            self.game_frame_cards = customtkinter.CTkFrame(self.game_frame, width=500, height=350, border_width=5)
            self.game_frame_cards.place(x=100, y=20)
            self.game_frame_cards.propagate(False) # Stops from resizing based on label
            self.term_label = customtkinter.CTkLabel(master=self.game_frame_cards, text=self.active_term.get(), font=("CTkFont", 26))
            self.term_label.pack(expand=True, fill='both', pady=5, padx=5)

            # Game Buttons Manipulated by Formulas
            self.next_button = customtkinter.CTkButton(self.game_frame, width=125, height=40, text="Show Definition", command=self.show_definition_button_event)
            self.nope_button = customtkinter.CTkButton(self.game_frame, width=80, height=40, text="NOPE!", command=self.nope_button_event)
            self.needs_work_button = customtkinter.CTkButton(self.game_frame,width=80, height=40, text="Needs Work", command=self.needs_work_button_event)
            self.got_it_button = customtkinter.CTkButton(self.game_frame, width=80, height=40, text="Got It!", command=self.got_it_button_event)
            self.next_term_button = customtkinter.CTkButton(self.game_frame, width=125, height=40, text="Next Term", command=self.show_next_term_button_event)
            self.play_again_button = customtkinter.CTkButton(self.game_frame, width=125, height=40, text="Play Again", command=self.play_again_button_event)

            self.game_quit_button = customtkinter.CTkButton(self.game_frame, text="Quit", width=125, height=40, command=self.close_game_frame)
            self.game_quit_button.place(x=95, y=400)
            self.update_game_ui()

    def nope_button_event(self):
        self.backend.calculate_test_estimate(1)
        self.game_state = 'term'
        self.current_card_number += 1
        self.backend.game_dictionary.pop(0)
        self.update_game_ui()

    def needs_work_button_event(self):
        self.backend.calculate_test_estimate(2)
        self.game_state = 'term'
        self.current_card_number += 1
        self.backend.game_dictionary.pop(0)
        self.update_game_ui()
    
    def got_it_button_event(self):
        self.backend.calculate_test_estimate(3)
        self.game_state = 'term'
        self.current_card_number += 1
        self.running_total_known[0] += 1
        self.backend.game_dictionary.pop(0)
        self.update_game_ui()

    def show_definition_button_event(self):
        self.game_state = 'definition'
        self.update_game_ui()

    def show_next_term_button_event(self):
        self.game_state = 'term'
        self.update_game_ui()

    def show_stats(self):
        self.game_state = 'stats'
        self.update_game_ui()

    def play_again_button_event(self):
        self.close_game_frame()
        self.open_game_frame()

    def update_game_ui(self):
        if self.game_state == 'term':
            if self.current_card_number == 0:
                self.backend.get_term()
                self.active_term.set(self.backend.active_term)
                self.term_label.configure(text=self.active_term.get())
                self.next_button.place(x=480, y=400)
                pass
            elif self.current_card_number == self.backend.card_number_selection[0]:
                test_score = self.backend.analyze_test_estimate()
                self.backend.insert_statistics(self.backend.current_glossary_index, self.backend.current_glossary[0], self.running_total_known[0], self.backend.card_number_selection[0], test_score)
                self.nope_button.place_forget()
                self.needs_work_button.place_forget()
                self.got_it_button.place_forget()
                self.show_stats()
            else:
                self.nope_button.place_forget()
                self.needs_work_button.place_forget()
                self.got_it_button.place_forget()
                self.backend.get_term()
                self.active_term.set(self.backend.active_term)
                self.term_label.configure(text=self.active_term.get())
                self.next_button.place(x=480, y=400)

        elif self.game_state == 'definition':
            self.next_button.place_forget()
            self.backend.get_definition()
            self.active_definition.set(self.backend.active_definition)
            self.term_label.configure(text=self.active_definition.get())
            self.nope_button.place(x=230, y=400)
            self.needs_work_button.place(x=315, y=400)
            self.got_it_button.place(x=404, y=400)

        elif self.game_state == 'stats':
            known = str(self.running_total_known[0])
            total = str(self.backend.card_number_selection[0])
            test_estimate = str(self.backend.analyze_test_estimate())
            self.stats_label_content = f'Total Correct: {known} / {total} | Test Estimate = {test_estimate}'
            self.term_label.configure(text=self.stats_label_content)
            self.play_again_button.place(x=480, y=400)
            pass


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.tab_view = MyTabView(master=self)
        self.tab_view.grid(row=0, column=0, padx=20, pady=20)

auto_flash_backend = BackEnd()
auto_flash_gui = App()
auto_flash_gui.mainloop()