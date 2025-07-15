

class Reglages_balle (ot.Base_Reglages) :
    def __init__ (self, boss) :
        ot.Base_Reglages.__init__(self, boss, "Balle (joueur)")
    
    def init_entitees (self) :
        entitees = self.big_boss.get_extra_entitees(["grille", "canvas", "balle"])
        self.grille = entitees[0]
        self.canvas = entitees[1]
        self.balle = entitees[2]
    
    def lancement (self) :
        ot.Base_Reglages.lancement(self, "Réglages de la Balle")
        
        self.deplacement(1)
    
    def deplacement (self, position) :
        deplacement_balle = tk.Frame(self, pady=20)
        deplacement_balle.grid(column=0, row=position, sticky=tk.NSEW)
        deplacement_balle.grid_columnconfigure(0, weight= 1)
        deplacement_balle.grid_columnconfigure(1, weight= 1)
        deplacement_balle.grid_columnconfigure(2, weight= 1)
        text_taille_lab = tk.Label(deplacement_balle, text="Déplacement Lisse\nde la Balle :", font=("Helvetica", 13))
        text_taille_lab.grid(column=0, row=0)
        
        decoupe = tk.Frame(deplacement_balle)
        decoupe.grid(column=1, row=0)
        text_decoupe = tk.Label(decoupe, text="Découpe\ndu mouvement :", font=("Helvetica", 13))
        text_decoupe.grid(column=0, row=0)
        self.decoupe_min = 2
        self.valeur_decoupe = ttk.Spinbox(decoupe, from_= self.decoupe_min, to=50, wrap=True, font=("Helvetica", 15), width=4, command=self.verif_decoupe)
        self.valeur_decoupe.set(self.balle.decoupe_dep)
        self.valeur_decoupe.grid(column=0, row=1)
        self.valeur_decoupe.bind("<Return>", self.verif_decoupe)
        
        vitesse = tk.Frame(deplacement_balle)
        vitesse.grid(column=2, row=0)
        text_vitesse = tk.Label(vitesse, text="Vitesse :", font=("Helvetica", 13))
        text_vitesse.grid(column=0, row=0)
        ot.Commentaire(self.boss, text_vitesse, "Temps d'attente (en milisecondes)\nentre deux partitions du mouvement\nde la balle entre deux cases")
        self.valeur_vitesse = ttk.Spinbox(vitesse, from_=10, to=1000, wrap=True, font=("Helvetica", 15), width=5, command=self.verif_vitesse)
        self.valeur_vitesse.set(self.balle.vitesse)
        self.valeur_vitesse.grid(column=0, row=1)
        self.valeur_vitesse.bind("<Return>", self.verif_vitesse)
    
    def verif_decoupe (self, event=None) :
        valable = False
        decoupe = self.valeur_decoupe.get()
        try :
            decoupe = int(decoupe)
        except TypeError :
            if self.boss.alerte_mauvaise_entree :
                messagebox.showinfo ('Valeur de découpe','La valeur "'+decoupe+'" n\'est pas conforme pour un nombre découpe du mouvement !',parent=self.boss ,icon = 'error')
        else :
            if decoupe < self.decoupe_min :
                decoupe = self.decoupe_min
                if self.boss.alerte_mauvaise_entree :
                    messagebox.showinfo ('Valeur de découpe','Le valeur de découpe minimum est de '+str(self.decoupe_min)+' !\nCar sinon, 0 c\'est de la téléportation et 1 c\'est déjà le déplacement Sec',parent=self.boss ,icon = 'error')
            else :
                valable = True
            self.valeur_decoupe.set(decoupe)
        return valable
    
    def verif_vitesse (self, event=None) :
        valable = False
        vitesse = self.valeur_vitesse.get()
        try :
            vitesse = int(vitesse)
        except TypeError :
            if self.boss.alerte_mauvaise_entree :
                messagebox.showinfo ('Vitesse','La vitesse "'+vitesse+'" n\'est pas conforme !',parent=self.boss ,icon = 'error')
        else :
            if vitesse < 1 :
                vitesse = 1
                if self.boss.alerte_mauvaise_entree :
                    messagebox.showinfo ('Vitesse','La vitesse minimum est de 1 mais il est recomendé de prendre au moins 10 car il est ici question de temps en miliseconde entre chaque partition de mouvement !',parent=self.boss ,icon = 'error')
            else :
                valable = True
            self.valeur_vitesse.set(vitesse)
        return valable
    
    def appliquer_modifications (self) :
        if self.verif_decoupe() and self.verif_vitesse() :
            self.big_boss.parametres["decoupe du deplacement"] = self.valeur_decoupe.get()
            self.big_boss.parametres["vitesse deplacement"] = self.valeur_vitesse.get()
            self.balle.init_variables()
