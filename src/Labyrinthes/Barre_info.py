
class Barre_info (tk.Frame) :
    def __init__ (self, boss, big_boss, grille) :
        tk.Frame.__init__(self, boss)
        self.big_boss = big_boss
        self.grille = grille
        for i in range (3) :
            self.grid_columnconfigure(i, weight= 1)
        self.grid_rowconfigure(0, weight= 1)

        self.text_laby = tk.StringVar()
        self.laby = tk.Label(self, textvariable=self.text_laby)
        self.laby.grid(column=0, row=0)
        
        self.text_nivaux = tk.StringVar()
        self.niveau = tk.Label(self, textvariable=self.text_nivaux)
        self.niveau.grid(column=1, row=0)
        
        self.text_difficultee = tk.StringVar()
        self.difficultee = tk.Label(self, textvariable=self.text_difficultee)
        self.difficultee.grid(column=2, row=0)
    
    def refresh_all (self) :
        """Affiche la barre principale avec les dernières informations à jour et sous le bon format"""
        self.refresh_laby()
        self.refresh_niveaux()
        self.refresh_difficultee()
        
    def refresh_laby (self) :
        "Met à jour l'affichage du numéro du labyrinthe"
        if self.big_boss.type_lab == "classique" :
            lab = "n° "+str(self.grille.num_lab)
        elif self.big_boss.type_lab == "aleatoire" :
            lab = "aléatoire n° "+str(self.grille.num_lab_alea)
        self.text_laby.set("Labyrinthe "+lab)
    
    def refresh_niveaux (self) :
        "Met à jour l'affichage du numéro du niveau"
        if self.big_boss.niveau.Niveau_max :
            niveau = "max"
        else :
            niveau = str(self.big_boss.niveau.numero)
        self.text_nivaux.set("Niveau : "+niveau)
        
    def refresh_difficultee (self) :
        "Met à jour l'affichage du numéro de la difficultée"
        if self.big_boss.niveau.Niveau_max :
            difficultee = "max"
        else :
            if self.big_boss.niveau.numero == 1 :
                difficultee = "-"
            else :
                difficultee = str(self.big_boss.difficultee.numero)
        self.text_difficultee.set("Difficultée : "+difficultee)

    def redimentionner (self, text_size:int, police:str = "Verdana") :
        self.laby.config(font=(police, text_size))
        self.niveau.config(font=(police, text_size))
        self.difficultee.config(font=(police, text_size))
