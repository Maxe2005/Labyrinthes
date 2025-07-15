
class Fen_chose_new_lab (tk.Toplevel) :
    def __init__ (self, boss, big_boss) :
        tk.Toplevel.__init__(self, boss)
        self.big_boss = big_boss
        self.title("Nouveau labyrinthe")
        self.nb_lignes = 2
        self.nb_colones = 2
        for i in range (self.nb_colones) :
            self.grid_columnconfigure(i, weight= 1) 
        for i in range (self.nb_lignes) :
            self.grid_rowconfigure(i, weight= 1)
        
        self.init_premier_choix()
        self.partie_premier_choix.grid(column=0, row=0, sticky=tk.NSEW)
        
        self.is_open_lab_croquis = False
        self.is_init_new_lab = False
        self.is_separation = False
        
        self.nb_colones_min = 3
        self.nb_colones_max = 50
        self.nb_lignes_min = 3
        self.nb_lignes_max = 35
        
        self.init_lab_croquis()
        self.init_new_lab()
        
        self.resizable(False, False)
        self.focus_set()
    
    def init_premier_choix (self) :
        self.partie_premier_choix = tk.Frame(self, border=10)
        text = tk.Text(self.partie_premier_choix, wrap= tk.WORD, width=25, height=3, padx=50, pady=20, font=("Helvetica", 15))
        text.insert(0.1, "Voulez-vous ouvrir un Croquis déjà existant ou voulez-vous créer un nouveau Labirinthe ?")
        text['state'] = 'disabled'
        text.grid(column=0, row=0, columnspan=2)
        
        bouton_2 = tk.Button (self.partie_premier_choix, text="Croquis", padx=20, pady=10, font=("Helvetica", 13), bg="green", fg="white", command=self.lab_croquis)
        bouton_2.grid(column=0, row=1)
        bouton_1 = tk.Button (self.partie_premier_choix, text="Nouveau", padx=20, pady=10, font=("Helvetica", 13), bg="blue", fg="white", command=self.new_lab)
        bouton_1.grid(column=1, row=1)
    
    def ajout_separation (self) :
        separation = tk.Text(self, bg="grey", pady=5, height=1, font=("Helvetica", 1))
        separation['state'] = 'disabled'
        separation.grid(column=0, row=1, sticky=tk.NSEW)
        self.is_separation = True
    
    def lab_croquis (self) :
        if self.is_init_new_lab :
            self.partie_init_new_lab.grid_forget()
            self.is_init_new_lab = False
        if not(self.is_open_lab_croquis) :
            if not(self.is_separation) :
                self.ajout_separation()
            self.partie_open_lab_croquis.grid(column=0, row=2, sticky=tk.NSEW)
            self.is_open_lab_croquis = True
    
    def init_lab_croquis (self) :
        self.partie_open_lab_croquis = tk.Frame(self, border=10)
        self.text_open_lab_croquis = tk.Text(self.partie_open_lab_croquis, wrap= tk.WORD, width=25, height=1, padx=50, pady=20, font=("Helvetica", 15))
        self.text_open_lab_croquis.insert(0.1, "Choisissez le Croquis à éditer :")
        self.text_open_lab_croquis['state'] = 'disabled'
        self.text_open_lab_croquis.grid(column=0, row=0, sticky=tk.NSEW)
        
        liste_nom = []
        with open("Labyrinthes_croquis/#_Doc_index.csv", "r") as f :
            for el in f.readlines() :
                liste_nom.append(el[:-1])
        self.liste_frame = tk.Frame(self.partie_open_lab_croquis, pady=30)
        liste = ttk.Combobox(self.liste_frame, values=liste_nom, state="readonly", justify="left", width=20, height=10, font=("Helvetica", 15))
        liste.current(0)
        liste.pack()
        self.liste_frame.grid(column=0, row=1)
        self.bouton_go_croquis = tk.Button (self.partie_open_lab_croquis, text="Ouvrir le Croquis", padx=20, pady=10, font=("Helvetica", 13),\
            command=partial(self.big_boss.open_lab_croquis, liste), bg="green", fg="white")
        self.bouton_go_croquis.grid(column=0, row=2)
    
    def new_lab (self) :
        if self.is_open_lab_croquis :
            self.partie_open_lab_croquis.grid_forget()
            self.is_open_lab_croquis = False
        if not(self.is_init_new_lab) :
            if not(self.is_separation) :
                self.ajout_separation()
            self.partie_init_new_lab.grid(column=0, row=2, sticky=tk.NSEW)
            self.is_init_new_lab = True
    
    def init_new_lab (self) :
        self.partie_init_new_lab = tk.Frame(self, border=10)
        text_init_new_lab = tk.Text(self.partie_init_new_lab, wrap= tk.WORD, width=25, height=3, padx=50, pady=20, font=("Helvetica", 15))
        text_init_new_lab.insert(0.1, "Entrez le nombre de colones et de lignes de votre nouveau labyrinthe :")
        text_init_new_lab['state'] = 'disabled'
        text_init_new_lab.grid(column=0, row=0, columnspan=2, sticky=tk.NSEW)
        
        largeur = tk.Frame(self.partie_init_new_lab, pady=20)
        largeur.grid(column=0, row=1)
        text_largeur = tk.Label(largeur, text="Colones :", font=("Helvetica", 13))
        text_largeur.grid(column=0, row=0)
        valeur_largeur = ttk.Spinbox(largeur, from_= self.nb_colones_min, to= self.nb_colones_max, wrap=True, font=("Helvetica", 15), width=4)
        valeur_largeur.set(10)
        valeur_largeur.grid(column=0, row=1)
        
        hauteur = tk.Frame(self.partie_init_new_lab, pady=20)
        hauteur.grid(column=1, row=1)
        text_hauteur = tk.Label(hauteur, text="Lignes :", font=("Helvetica", 13))
        text_hauteur.grid(column=0, row=0)
        valeur_hauteur = ttk.Spinbox(hauteur, from_= self.nb_lignes_min, to= self.nb_lignes_max, wrap=True, font=("Helvetica", 15), width=4)
        valeur_hauteur.set(10)
        valeur_hauteur.grid(column=0, row=1)
        
        nom_lab_frame = tk.Frame(self.partie_init_new_lab, pady=20)
        nom_lab_frame.grid(column=0, row=2, columnspan=2)
        texte_nom_lab = tk.Label(nom_lab_frame, text="Nom du Labyrinthe :", font=("Helvetica", 13))
        texte_nom_lab.grid(column=0, row=0)
        nom_lab = tk.Entry(nom_lab_frame, justify="center", font=("Helvetica", 15))
        nom_lab.insert(0,"<sans-nom>")
        nom_lab.grid(column=0, row=1)
        
        self.bouton_go_new_lab = tk.Button (self.partie_init_new_lab, text="Créer le Labyrinthe", padx=20, pady=10, font=("Helvetica", 13), bg="blue", fg="white",\
            command=partial(self.big_boss.init_new_lab, valeur_largeur, valeur_hauteur, self.nb_colones_min, self.nb_colones_max, self.nb_lignes_min, self.nb_lignes_max, nom_lab))
        self.bouton_go_new_lab.grid(column=0, row=3, columnspan=2)
