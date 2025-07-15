
class Fen_infos_generales (tk.Toplevel) :
    def __init__ (self, boss, big_boss) :
        tk.Toplevel.__init__(self, boss)
        self.big_boss = big_boss
        self.title("Informations Générales")
        self.nb_lignes = 2
        self.nb_colones = 1
        for i in range (self.nb_colones) :
            self.grid_columnconfigure(i, weight= 1) 
        for i in range (self.nb_lignes) :
            self.grid_rowconfigure(i, weight= 1)
        
        self.init_contenu()
        
        self.resizable(False, False)
        self.focus_set()
    
    def init_contenu (self) :
        text = tk.Text(self, wrap= tk.WORD, width=55, height=8, padx=50, pady=30, font=("Helvetica", 15))
        text.insert(0.1, "Bienvenu dans le Constructeur de Labyrinthes !\n\n\nC'est ici que vous pouvez créer vos propres labyrinthes puis les essayer dans le parcoureur de labyrinthes.")
        text['state'] = 'disabled'
        text.grid(column=0, row=0, sticky=tk.NSEW)
        text.tag_add("titre", "1.0", "1.46")
        text.tag_config("titre", foreground="red", font=("Helvetica", 20), justify='center')
        
        
        bouton_1 = tk.Button (self, text="Ouvrir le Parcoureur de Labyrinthes", padx=20, pady=10, font=("Helvetica", 13), bg="blue", fg= "white", \
            command=self.big_boss.lancement_parcoureur_labs)
        bouton_1.configure(state = 'disabled', bg="grey")
        bouton_1.grid(column=0, row=1)
