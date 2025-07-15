

class Reglages_lab_alea (ot.Base_Reglages) :
    def __init__ (self, boss) :
        ot.Base_Reglages.__init__(self, boss, "Générateur de labyrinthes")
    
    def init_entitees (self) :
        entitees = self.big_boss.get_extra_entitees(["grille", "canvas", "balle"])
        self.grille = entitees[0]
        self.canvas = entitees[1]
        self.balle = entitees[2]
    
    def lancement (self) :
        ot.Base_Reglages.lancement(self, "Réglages du Générateur de Labyrinthes")
        
        self.init_taille_lab(1)
        self.init_position_start(2)
    
    def init_taille_lab (self, position) :
        taille_lab = tk.Frame(self, pady=20)
        taille_lab.grid(column=0, row=position, sticky=tk.NSEW)
        taille_lab.grid_columnconfigure(0, weight= 1)
        taille_lab.grid_columnconfigure(1, weight= 1)
        taille_lab.grid_columnconfigure(2, weight= 1)
        text_taille_lab = tk.Label(taille_lab, text="Taille du Labyrinthe :", font=("Helvetica", 13))
        text_taille_lab.grid(column=0, row=0)
        
        colones = tk.Frame(taille_lab)
        colones.grid(column=1, row=0)
        text_colone = tk.Label(colones, text="Colones :", font=("Helvetica", 13))
        text_colone.grid(column=0, row=0)
        self.valeur_colone = ttk.Spinbox(colones, from_= self.grille.nb_colones_min, to= self.grille.nb_colones_max, wrap=True, font=("Helvetica", 15), width=4, command=self.verif_nb_colone)
        self.valeur_colone.set(self.grille.lab_alea_x)
        self.nb_colones = self.grille.lab_alea_x
        self.valeur_colone.grid(column=0, row=1)
        self.valeur_colone.bind("<Return>", self.verif_nb_colone)
        
        lignes = tk.Frame(taille_lab)
        lignes.grid(column=2, row=0)
        text_ligne = tk.Label(lignes, text="Lignes :", font=("Helvetica", 13))
        text_ligne.grid(column=0, row=0)
        self.valeur_ligne = ttk.Spinbox(lignes, from_= self.grille.nb_lignes_min, to= self.grille.nb_lignes_max, wrap=True, font=("Helvetica", 15), width=4, command=self.verif_nb_ligne)
        self.valeur_ligne.set(self.grille.lab_alea_y)
        self.nb_lignes = self.grille.lab_alea_y
        self.valeur_ligne.grid(column=0, row=1)
        self.valeur_ligne.bind("<Return>", self.verif_nb_ligne)
    
    def verif_nb_colone (self, event=None) :
        valable = False
        nb_colones = self.valeur_colone.get()
        try :
            nb_colones = int(nb_colones)
        except TypeError :
            if self.boss.alerte_mauvaise_entree :
                messagebox.showinfo ('Nombre de colones','L\'entrée "'+nb_colones+'" n\'est pas conforme pour un nombre de colones !',parent=self.boss ,icon = 'error')
        else :
            if nb_colones < self.grille.nb_colones_min :
                nb_colones = self.grille.nb_colones_min
                if self.boss.alerte_mauvaise_entree :
                    messagebox.showinfo ('Nombre de colones','Le nombre de colones minimum est de '+str(self.grille.nb_colones_min)+' !',parent=self.boss ,icon = 'error')
            elif nb_colones > self.grille.nb_colones_max :
                nb_colones = self.grille.nb_colones_max
                if self.boss.alerte_mauvaise_entree :
                    messagebox.showinfo ('Nombre de colones','Le nombre de colones maximum est de '+str(self.grille.nb_colones_max)+' !',parent=self.boss ,icon = 'error')
            else :
                valable = True
            self.nb_colones = nb_colones
        self.valeur_colone.set(self.nb_colones)
        self.valeur_x.configure(to=self.nb_colones)
        return valable
    
    def verif_nb_ligne (self, event=None) :
        valable = False
        nb_lignes = self.valeur_ligne.get()
        try :
            nb_lignes = int(nb_lignes)
        except TypeError :
            if self.boss.alerte_mauvaise_entree :
                messagebox.showinfo ('Nombre de lignes','L\'entrée "'+nb_lignes+'" n\'est pas conforme pour un nombre de lignes !',parent=self.boss ,icon = 'error')
        else :
            if nb_lignes < self.grille.nb_lignes_min :
                nb_lignes = self.grille.nb_lignes_min
                if self.boss.alerte_mauvaise_entree :
                    messagebox.showinfo ('Nombre de lignes','Le nombre de lignes minimum est de '+str(self.grille.nb_lignes_min)+' !',parent=self.boss ,icon = 'error')
            elif nb_lignes > self.grille.nb_lignes_max :
                nb_lignes = self.grille.nb_lignes_max
                if self.boss.alerte_mauvaise_entree :
                    messagebox.showinfo ('Nombre de lignes','Le nombre de lignes maximum est de '+str(self.grille.nb_lignes_max)+' !',parent=self.boss ,icon = 'error')
            else :
                valable = True
            self.nb_lignes = nb_lignes
        self.valeur_ligne.set(self.nb_lignes)
        self.valeur_y.configure(to=self.nb_lignes)
        return valable
    
    def init_position_start (self, position) :
        """Définie la position de départ de la balle sur le labyrinthe"""
        position_start = tk.Frame(self, pady=20)
        position_start.grid(column=0, row=position, sticky=tk.NSEW)
        position_start.grid_columnconfigure(0, weight= 1)
        position_start.grid_columnconfigure(1, weight= 1)
        position_start.grid_columnconfigure(2, weight= 1)
        text_taille_lab = tk.Label(position_start, text="Position du départ\ndu Labyrinthe :", font=("Helvetica", 13))
        text_taille_lab.grid(column=0, row=0)
        
        x = tk.Frame(position_start)
        x.grid(column=1, row=0)
        text_x = tk.Label(x, text="X :", font=("Helvetica", 13))
        text_x.grid(column=0, row=0)
        self.valeur_x = ttk.Spinbox(x, from_= 0, to= self.nb_colones, wrap=True, font=("Helvetica", 15), width=4)
        self.valeur_x.set(self.grille.lab_alea_entrée_lab[0])
        self.valeur_x.grid(column=1, row=0)
        self.valeur_x.bind("<Return>", self.verif_depart_x)
        
        y = tk.Frame(position_start)
        y.grid(column=2, row=0)
        text_y = tk.Label(y, text="Y :", font=("Helvetica", 13))
        text_y.grid(column=0, row=0)
        self.valeur_y = ttk.Spinbox(y, from_= 0, to= self.nb_lignes, wrap=True, font=("Helvetica", 15), width=4)
        self.valeur_y.set(self.grille.lab_alea_entrée_lab[1])
        self.valeur_y.grid(column=1, row=0)
        self.valeur_y.bind("<Return>", self.verif_depart_y)
    
    def verif_depart_x (self, event=None) :
        valable = False
        x = self.valeur_x.get()
        try :
            x = int(x)
        except TypeError :
            if self.boss.alerte_mauvaise_entree :
                messagebox.showinfo ('Position x du départ','L\'entrée "'+x+'" n\'est pas conforme pour une position sur le labyrinthe !',parent=self.boss ,icon = 'error')
            self.valeur_x.set(0)
        else :
            if x < 0 :
                x = 0
                if self.boss.alerte_mauvaise_entree :
                    messagebox.showinfo ('Position x du départ','La position minimum est de 0 !',parent=self.boss ,icon = 'error')
            elif x > self.nb_colones :
                x = self.nb_colones
                if self.boss.alerte_mauvaise_entree :
                    messagebox.showinfo ('Position x du départ','La position maximum est de '+str(self.nb_colones)+' !',parent=self.boss ,icon = 'error')
            else :
                valable = True
            self.valeur_x.set(x)
        return valable
    
    def verif_depart_y (self, event=None) :
        valable = False
        y = self.valeur_y.get()
        try :
            y = int(y)
        except TypeError :
            if self.boss.alerte_mauvaise_entree :
                messagebox.showinfo ('Position y du départ','L\'entrée "'+y+'" n\'est pas conforme pour une position sur le labyrinthe !',parent=self.boss ,icon = 'error')
            self.valeur_y.set(0)
        else :
            if y < 0 :
                y = 0
                if self.boss.alerte_mauvaise_entree :
                    messagebox.showinfo ('Position y du départ','La position minimum est de 0 !',parent=self.boss ,icon = 'error')
            elif y > self.nb_lignes :
                y = self.nb_lignes
                if self.boss.alerte_mauvaise_entree :
                    messagebox.showinfo ('Position y du départ','La position maximum est de '+str(self.nb_lignes)+' !',parent=self.boss ,icon = 'error')
            else :
                valable = True
            self.valeur_y.set(y)
        return valable
    
    def appliquer_modifications (self) :
        if self.verif_nb_colone() and self.verif_nb_ligne() and self.verif_depart_x() and self.verif_depart_y() :
            self.big_boss.parametres["lab alea x"] = self.valeur_colone.get()
            self.big_boss.parametres["lab alea y"] = self.valeur_ligne.get()
            self.big_boss.parametres["lab alea entree x"] = self.valeur_x.get()
            self.big_boss.parametres["lab alea entree y"] = self.valeur_y.get()
            self.grille.init_variables()
