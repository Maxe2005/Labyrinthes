

class Reglages_question_confirmation (ot.Base_Reglages) :
    def __init__ (self, boss) :
        ot.Base_Reglages.__init__(self, boss, "Alertes de confirmation")
    
    def init_entitees (self) :
        entitees = self.big_boss.get_extra_entitees(["grille", "canvas", "balle"])
        self.grille = entitees[0]
        self.canvas = entitees[1]
        self.balle = entitees[2]
    
    def lancement (self) :
        ot.Base_Reglages.lancement(self, "Réglages des Alertes de Confirmation")
        
        self.lab_suivant(1)
        self.lab_precedent(2)
        self.recomencer_lab(3)
        self.niveau_2(4)
        self.niveau_3(5)
        self.niveau_4(6)
        self.niveau_max(7)
        
    def lab_suivant (self, position) :
        self.var_confirmation_lab_suivant = tk.IntVar()
        self.var_confirmation_lab_suivant.set(int(self.big_boss.parametres["question confirmation lab suivant"]))
        checkbtn = tk.Checkbutton(self, variable= self.var_confirmation_lab_suivant, text="Alerte pour confirmation passage labyrinthe suivant", compound=tk.LEFT, border=10, font=("Helvetica", 13))
        checkbtn.grid(column=0, row=position)
    
    def lab_precedent (self, position) :
        self.var_confirmation_lab_precedent = tk.IntVar()
        self.var_confirmation_lab_precedent.set(int(self.big_boss.parametres["question confirmation lab precedent"]))
        checkbtn = tk.Checkbutton(self, variable= self.var_confirmation_lab_precedent, text="Alerte pour confirmation retour labyrinthe précédent", compound=tk.LEFT, border=10, font=("Helvetica", 13))
        checkbtn.grid(column=0, row=position)
    
    def recomencer_lab (self, position) :
        self.var_confirmation_recomencer_lab = tk.IntVar()
        self.var_confirmation_recomencer_lab.set(int(self.big_boss.parametres["question confirmation recomencer lab"]))
        checkbtn = tk.Checkbutton(self, variable= self.var_confirmation_recomencer_lab, text="Alerte pour confirmation recomencer le labyrinthe au début", compound=tk.LEFT, border=10, font=("Helvetica", 13))
        checkbtn.grid(column=0, row=position)
    
    def niveau_2 (self, position) :
        self.var_confirmation_niveau_2 = tk.IntVar()
        self.var_confirmation_niveau_2.set(int(self.big_boss.parametres["question confirmation passage niveau 2"]))
        checkbtn = tk.Checkbutton(self, variable= self.var_confirmation_niveau_2, text="Alerte pour confirmation passage au niveau 2", compound=tk.LEFT, border=10, font=("Helvetica", 13))
        checkbtn.grid(column=0, row=position)
    
    def niveau_3 (self, position) :
        self.var_confirmation_niveau_3 = tk.IntVar()
        self.var_confirmation_niveau_3.set(int(self.big_boss.parametres["question confirmation passage niveau 3"]))
        checkbtn = tk.Checkbutton(self, variable= self.var_confirmation_niveau_3, text="Alerte pour confirmation passage au niveau 3", compound=tk.LEFT, border=10, font=("Helvetica", 13))
        checkbtn.grid(column=0, row=position)
    
    def niveau_4 (self, position) :
        self.var_confirmation_niveau_4 = tk.IntVar()
        self.var_confirmation_niveau_4.set(int(self.big_boss.parametres["question confirmation passage niveau 4"]))
        checkbtn = tk.Checkbutton(self, variable= self.var_confirmation_niveau_4, text="Alerte pour confirmation passage au niveau 4", compound=tk.LEFT, border=10, font=("Helvetica", 13))
        checkbtn.grid(column=0, row=position)
    
    def niveau_max (self, position) :
        self.var_confirmation_niveau_max = tk.IntVar()
        self.var_confirmation_niveau_max.set(int(self.big_boss.parametres["question confirmation passage niveau max"]))
        checkbtn = tk.Checkbutton(self, variable= self.var_confirmation_niveau_max, text="Alerte pour confirmation passage au niveau max", compound=tk.LEFT, border=10, font=("Helvetica", 13))
        checkbtn.grid(column=0, row=position)
    
    def appliquer_modifications (self) :
        self.big_boss.parametres["question confirmation lab suivant"] = self.var_confirmation_lab_suivant.get()
        self.big_boss.parametres["question confirmation lab precedent"] = self.var_confirmation_lab_precedent.get()
        self.big_boss.parametres["question confirmation recomencer lab"] = self.var_confirmation_recomencer_lab.get()
        self.big_boss.parametres["question confirmation passage niveau 2"] = self.var_confirmation_niveau_2.get()
        self.big_boss.parametres["question confirmation passage niveau 3"] = self.var_confirmation_niveau_3.get()
        self.big_boss.parametres["question confirmation passage niveau 4"] = self.var_confirmation_niveau_4.get()
        self.big_boss.parametres["question confirmation passage niveau max"] = self.var_confirmation_niveau_max.get()
