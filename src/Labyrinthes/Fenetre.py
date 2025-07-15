
class Laby_fen (ot.Structure_globale.Fenetre) :
    def __init__(self ,x=1000 ,y=800):
        tk.Tk.__init__(self)
        self.x = x # = self.winfo_screenwidth() -200
        self.y = y # = self.winfo_screenheight() -100
        self.title("The Labyrinthe")
        self.geometry (str(self.x)+"x"+str(self.y))
        self.min_x = 500
        self.min_y = 400
        self.minsize(self.min_x, self.min_y)
        self.init_config_grid()
        self.bind("<Button-3>", self.redimentionner)
    
    def init_config_grid (self) :
        self.poids_canvas_x = 9
        self.poids_canvas_y = 9
        self.poids_barre_laterale_droite_x = 1
        self.poids_barre_top_y = 1
        self.poids_total_x = self.poids_canvas_x + self.poids_barre_laterale_droite_x
        self.poids_total_y = self.poids_canvas_y + self.poids_barre_top_y
        
        self.grid_columnconfigure(0, weight= self.poids_canvas_x)
        self.grid_columnconfigure(1, weight= self.poids_barre_laterale_droite_x)
        self.grid_rowconfigure(0, weight= self.poids_barre_top_y)
        self.grid_rowconfigure(1, weight= self.poids_canvas_y)
    
    def init_entitees (self, big_boss, grille, canvas, balle) :
        self. big_boss = big_boss
        self. grille = grille
        self. canvas = canvas
        self. balle = balle
    
    def init_barres_boutons_et_text (self) :
        self.init_configuration_barre_laterale_droite()
        self.init_configuration_barre_top()
        self.barre_principale.refresh_all()
    
    def init_configuration_barre_laterale_droite (self) :
        self.barre_laterale_droite = tk.Frame(self)
        self.barre_laterale_droite.grid(column=1, row=0, rowspan=2, sticky=tk.NSEW)
        self.barre_laterale_droite.grid_columnconfigure(0, weight= 1)
        self.barre_laterale_droite.grid_rowconfigure(0, weight= 1)
        self.barre_laterale_droite.grid_rowconfigure(1, weight= 0)
        self.barre_laterale_droite.grid_rowconfigure(2, weight= 7)
        self.init_logo(self.barre_laterale_droite)
        self.open_image("Idées LOGO/"+self.big_boss.parametres["logo parcoureur"], x_max= self.barre_laterale_droite.winfo_width())
        self.boutons_lateraux_droits = ot.Boutons(self.barre_laterale_droite, self.big_boss, self, class_comentaire=ot.Commentaire)
        self.init_boutons_barre_laterale_droite()
        self.boutons_lateraux_droits.grid(column=0, row=2, sticky=tk.NSEW)
    
    def init_boutons_barre_laterale_droite (self) :
        """
        Définition de la configuration des boutons de la barre latérale droite
        """
        self.boutons_lateraux_droits.init_grid(nb_lignes=10)
        
        btn = self.boutons_lateraux_droits.def_bouton('Réglages', self.big_boss.reglages, 0)
        com = btn.add_commentaire(self, "Accès au réglages\n(raccourci : 'r')")
        self.big_boss.commentaires.append(com)
        self.bind("<KeyRelease-r>", self.big_boss.reglages)
        
        btn = self.boutons_lateraux_droits.def_bouton('Couleurs', self.canvas.couleurs, 1)
        com = btn.add_commentaire(self, "Change la couleur du canvas\n(raccourci : 'ctrl' + 'c')")
        self.big_boss.commentaires.append(com)
        self.bind("<Control-KeyRelease-c>", self.canvas.couleurs)
        
        btn = self.boutons_lateraux_droits.def_bouton('Aller à', self.big_boss.aller_a, 2)
        com = btn.add_commentaire(self, "Permet de se rendre rapidement\nsur le labyrinthe souhaité\n(raccourci : 'a')")
        self.big_boss.commentaires.append(com)
        self.bind("<KeyRelease-a>", self.big_boss.aller_a)
        
        btn = self.boutons_lateraux_droits.def_bouton('Labyrinthe\nAléatoire', self.big_boss.type_labyrinthe, 3, nom_diminutif="type lab")
        com = btn.add_commentaire(self, "Permet de switcher entre les Labyrinthes\nClassiques et les Labyrinthes Aléatoires.\nLe type affiché est le type non-actif.\n(raccourci : 't')")
        self.big_boss.commentaires.append(com)
        self.bind("<KeyRelease-t>", self.big_boss.type_labyrinthe)
        
        btn = self.boutons_lateraux_droits.def_bouton('New Lab\nAléatoire', self.big_boss.new_lab_alea, 4,  nom_diminutif="new lab alea", visibilite="Cache")
        com = btn.add_commentaire(self, "Génère un nouveau Labyrinthe aléatoire")
        self.big_boss.commentaires.append(com)
        
        btn = self.boutons_lateraux_droits.def_bouton('Déplacement\n'+self.big_boss.type_deplacement, self.big_boss.change_type_deplacement, 6, nom_diminutif= 'type deplacement')
        com = btn.add_commentaire(self, "Permet de switcher entre deux modes de déplacement :\n\n- Mode Lisse : permet de programmer à l'avance\n\tla prochaine direction (raccourci : 'l')\n- Mode Sec : déplacement case par case (raccourci : 's')\n\nLe mode affiché sur le bouton est le mode actif.", aligne_in="left")
        self.big_boss.commentaires.append(com)
        self.bind("<KeyRelease-s>", partial(self.big_boss.def_type_deplacement, "Sec"))
        self.bind("<KeyRelease-l>", partial(self.big_boss.def_type_deplacement, "Lisse"))
        
        btn = self.boutons_lateraux_droits.def_bouton('Niveau Max', self.big_boss.niveau.niveau_max, 8)
        com = btn.add_commentaire(self, "Permet d'activer (et désactiver) le Niveau Maximum :\nDans ce niveau les murs sont invisibles\n(raccourci : 'm')")
        self.big_boss.commentaires.append(com)
        self.bind("<KeyRelease-m>", self.big_boss.niveau.niveau_max)
        
        btn = self.boutons_lateraux_droits.def_bouton('Mode HARD', self.big_boss.mode_HARD, 9)
        com = btn.add_commentaire(self, "Permet d'activer (et désactiver) le mode HARD :\nDans ce mode la balle est invisible\n(raccourci : 'h')")
        self.big_boss.commentaires.append(com)
        self.bind("<KeyRelease-h>", self.big_boss.mode_HARD)
    
    def init_configuration_barre_top (self) :
        self.barre_top = tk.Frame(self)
        self.barre_top.grid(column=0, row=0, sticky=tk.NSEW)
        self.barre_top.grid_rowconfigure(0, weight= 1)
        self.barre_top.grid_columnconfigure(0, weight= 0)
        self.barre_top.grid_columnconfigure(1, weight= 1)
        self.barre_top.grid_columnconfigure(2, weight= 0)
        self.boutons_top_left = ot.Boutons(self.barre_top, self.big_boss, self, class_comentaire=ot.Commentaire)
        self.init_boutons_barre_top_left()
        self.boutons_top_left.grid(column=0, row=0, sticky=tk.NSEW, padx=10, ipadx=20)
        
        self.barre_principale = Barre_info(self.barre_top, self.big_boss, self.grille)
        self.barre_principale.grid(column= 1, row= 0, sticky=tk.NSEW)
        
        self.boutons_top_right = ot.Boutons(self.barre_top, self.big_boss, self, class_comentaire=ot.Commentaire)
        self.init_boutons_barre_top_right()
        self.boutons_top_right.grid(column=2, row=0, padx=20)#, sticky=tk.NSEW)
        
        #self.chrono = Chrono(self)
        #self.chrono.grid(column= 51, row= 0, columnspan= 6, rowspan=2)
    
    def init_boutons_barre_top_left (self) :
        """
        Définition de la configuration des boutons à gauche de la barre haute
        """
        #print("left :",self.boutons_top_left.winfo_width())
        min_y = 0
        self.boutons_top_left.init_grid(nb_colones=2)
        
        self.niveau_frame = tk.Frame(self.boutons_top_left)
        self.niveau_frame.grid(column=0, row=0)
        btn = self.boutons_top_left.def_bouton('<-', self.big_boss.niveau.moins, 0, boss=self.niveau_frame, sticky="e", nom_diminutif= "niveau moins")
        com = btn.add_commentaire(self, "Passer au niveau inférieur", position_out=["B","L","R","T"])
        self.big_boss.commentaires.append(com)
        
        btn = self.boutons_top_left.def_bouton('Niveau', self.big_boss.niveau.fenetre_presentation, 1, boss=self.niveau_frame, sticky="ew")
        com = btn.add_commentaire(self, "Présetation des niveaux", position_out=["B","L","R","T"])
        self.big_boss.commentaires.append(com)
        
        btn = self.boutons_top_left.def_bouton('->', self.big_boss.niveau.plus, 2, boss=self.niveau_frame, sticky="w", nom_diminutif= "niveau plus")
        com = btn.add_commentaire(self, "Passer au niveau supérieur", position_out=["B","L","R","T"])
        self.big_boss.commentaires.append(com)
        
        self.difficultee_frame = tk.Frame(self.boutons_top_left)
        if self.boutons_top_left.winfo_width() < min_y :
            self.difficultee_frame.grid(column=0, row=1)
        else :
            self.difficultee_frame.grid(column=1, row=0)
        btn = self.boutons_top_left.def_bouton('<-', self.big_boss.difficultee.moins, 0, boss=self.difficultee_frame, sticky="e", nom_diminutif= "difficultée moins")
        com = btn.add_commentaire(self, "Passer à la difficultée inférieure", position_out=["B","L","R","T"])
        self.big_boss.commentaires.append(com)
        
        btn = self.boutons_top_left.def_bouton('Difficultée', self.big_boss.difficultee.fenetre_presentation, 1, boss=self.difficultee_frame, sticky="ew")
        com = btn.add_commentaire(self, "Présetation des difficultées", position_out=["B","L","R","T"])
        self.big_boss.commentaires.append(com)
        
        btn = self.boutons_top_left.def_bouton('->', self.big_boss.difficultee.plus, 2, boss=self.difficultee_frame, sticky="w", nom_diminutif= "difficultée plus")
        com = btn.add_commentaire(self, "Passer à la difficultée supérieure", position_out=["B","L","R","T"])
        self.big_boss.commentaires.append(com)
    
    def init_boutons_barre_top_right (self) :
        """
        Définition de la configuration des boutons à droite de la barre haute
        """
        #print("right :",self.boutons_top_right.winfo_width())
        if False:#self.boutons_top_right.winfo_width() < 300 :
            self.boutons_top_right.init_grid(nb_lignes=3)
        else :
            self.boutons_top_right.init_grid(nb_colones=3)
        
        btn = self.boutons_top_right.def_bouton('<- Précédent', self.big_boss.precedent_lab, 0, sticky="e")
        com = btn.add_commentaire(self, "Accès au labyrinthe précédent\n(raccourci : 'p')", position_out=["B","L","R","T"])
        self.big_boss.commentaires.append(com)
        self.bind("<KeyRelease-p>", self.big_boss.precedent_lab)
        
        btn = self.boutons_top_right.def_bouton('Recomencer', self.big_boss.recomencer_lab, 1, sticky="ew")
        com = btn.add_commentaire(self, "Permet de recomencer le labyrinthe\nen retournant au début\n(raccourci : 'r')", position_out=["B","L","R","T"])
        self.big_boss.commentaires.append(com)
        self.bind("<KeyRelease-r>", self.big_boss.recomencer_lab)
        
        btn = self.boutons_top_right.def_bouton('Suivant ->', self.big_boss.suivant_lab, 2, sticky="w")
        com = btn.add_commentaire(self, "Accès au labyrinthe suivant", position_out=["B","L","R","T"])#\n(raccourci : 's')")
        self.big_boss.commentaires.append(com)
        #self.bind("<KeyRelease-s>", self.big_boss.suivant_lab)
    
    def redimentionner (self,event=None) :
        self.x = self.winfo_width()
        self.y = self.winfo_height()
        self.canvas.redimentionner()
        self.open_image("Idées LOGO/"+self.big_boss.parametres["logo parcoureur"], x_max= self.barre_laterale_droite.winfo_width())
        text_size = int(log(self.winfo_width()/100))
        self.barre_principale.redimentionner(text_size = int(text_size * 5))
        #self.chrono.label.config(font=("Arial", text_size/3))
        self.boutons_lateraux_droits.redimentionner(text_size = int(text_size * 5.5))
        self.boutons_top_right.redimentionner(text_size = int(text_size * 5))
        self.boutons_top_left.redimentionner(text_size = int(text_size * 5))
        #self.init_boutons_barre_top_right()
        #self.init_boutons_barre_top_left ()

