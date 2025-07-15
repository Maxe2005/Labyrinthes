
class Lab_fen_crea (tk.Tk) :
    def __init__ (self, big_boss, x:int = 1000, y:int = 800) :
        tk.Tk.__init__(self)
        self.big_boss = big_boss
        self.x = x #= self.winfo_screenwidth() -200
        self.y = y #= self.winfo_screenheight() -100
        self.title("The Maze Builder")
        self.geometry (str(self.x)+"x"+str(self.y))
        self.min_x = 500
        self.min_y = 400
        self.minsize(self.min_x, self.min_y)
        self.init_config_grid()
        self.bind("<Button-3>", self.redimentionner)
    
    def init_entitees (self, grille, canvas, balle) :
        self.grille = grille
        self.canvas = canvas
        self.balle = balle
    
    def init_config_grid (self) :
        self.poids_canvas_x = 9
        self.poids_canvas_y = 9
        self.poids_barre_laterale_droite_x = 1
        self.poids_barre_principale_y = 1
        self.poids_total_x = self.poids_canvas_x + self.poids_barre_laterale_droite_x
        self.poids_total_y = self.poids_canvas_y + self.poids_barre_principale_y
        
        self.grid_columnconfigure(0, weight= self.poids_canvas_x)
        self.grid_columnconfigure(1, weight= self.poids_barre_laterale_droite_x)
        self.grid_rowconfigure(0, weight= self.poids_barre_principale_y)
        self.grid_rowconfigure(1, weight= self.poids_canvas_y)
    
    def init_barres_boutons_et_text (self) :
        self.barre_laterale_droite = tk.Frame(self)
        self.barre_laterale_droite.grid(column=1, row=0, rowspan=2, sticky=tk.NSEW)
        self.barre_laterale_droite.grid_columnconfigure(0, weight= 1)
        self.barre_laterale_droite.grid_rowconfigure(0, weight= 1)
        self.barre_laterale_droite.grid_rowconfigure(1, weight= 4)
        self.init_logo()
        self.boutons = Outils.Boutons(self.barre_laterale_droite, self.big_boss, self)
        self.init_configuration_barre_laterale_droite()
        self.boutons.grid(column=0, row=1, sticky=tk.NSEW)
        self.init_barres_text()
        self.refresh_barre_de_texte()
    
    def init_configuration_barre_laterale_droite (self) :
        """
        Définition de la configuration des boutons de la barre latérale droite
        """
        self.boutons.init_grid(nb_lignes=10)
        
        btn = self.boutons.def_bouton('Couleurs', self.canvas.couleurs, 1)
        com = btn.add_commentaire(self, "Change la couleur du canvas\n(raccourci : 'ctrl' + 'c')")
        self.big_boss.commentaires.append(com)
        self.bind("<Control-KeyRelease-c>", self.canvas.couleurs)
        
        btn = self.boutons.def_bouton('Aller à', self.big_boss.aller_a_start, 4)
        com = btn.add_commentaire(self, "Permet de déplacer la balle facilement\n(raccourci : 'a')")
        self.big_boss.commentaires.append(com)
        self.bind("<KeyRelease-a>", self.big_boss.aller_a_start)
        
        self.frame_dep = tk.Frame(self.boutons)
        self.frame_dep.grid(row= 5)
        btn = self.boutons.def_bouton("", self.big_boss.Change_type_deplacement, 1, nom_diminutif= 'type deplacement', boss= self.frame_dep)
        com = btn.add_commentaire(self, "Permet de switcher entre deux modes de déplacement :\n\n- Mode Créer : casse les murs (raccourci : 'c')\n- Mode Déplacement : traverse les murs (raccourci : 'd')\n\nLe mode affiché sur le bouton est le mode actif.\n(raccouci pour switcher de mode : <Espace>)", aligne_in="left")
        self.big_boss.commentaires.append(com)
        self.bind("<KeyRelease-space>", self.big_boss.Change_type_deplacement)
        self.bind("<KeyRelease-d>", partial(self.big_boss.def_type_deplacement, "Passe"))
        self.bind("<KeyRelease-c>", partial(self.big_boss.def_type_deplacement, "Casse"))
        self.big_boss.def_type_deplacement(self.big_boss.parametres["dep initial"])
        
        self.frame_entree = tk.Frame(self.boutons)
        self.frame_entree.grid(row= 8)
        btn = self.boutons.def_bouton('Créer une entrée', self.big_boss.entree, 1, boss= self.frame_entree)
        com = btn.add_commentaire(self, "Permet de définir la case d'entrée\npour le parcours du labyrinthe une fois terminé\n(raccourci : 'e')")
        self.big_boss.commentaires.append(com)
        self.bind("<KeyRelease-e>", self.big_boss.entree)
        
        self.frame_sortie = tk.Frame(self.boutons)
        self.frame_sortie.grid(row= 9)
        btn = self.boutons.def_bouton('Créer une sortie', self.big_boss.sortie_start, 1, boss= self.frame_sortie)
        com = btn.add_commentaire(self, "Permet de définir la sortie en cassant un mur exterieur\npour le parcours du labyrinthe une fois terminé\n(raccourci : 's')")
        self.big_boss.commentaires.append(com)
        self.bind("<KeyRelease-s>", self.big_boss.sortie_start)
        
        btn = self.boutons.def_bouton('Nouveau Labyrinthe', self.big_boss.new_lab, 3)
        com = btn.add_commentaire(self, "Ouvre un formulaire pour ouvrir un croquis\nou commencer un nouveau labyrinthe\n(raccourci : 'n')")
        self.big_boss.commentaires.append(com)
        self.bind("<KeyRelease-n>", self.big_boss.new_lab)
        
        btn = self.boutons.def_bouton('Sauvegarder', self.big_boss.save, 2)
        com = btn.add_commentaire(self, "Permet de sauvegarder le labyrinthe en cours d'édition\nsoit sous forme de croquis, soit\nsous forme de labyrinthe terminé\n(raccourci : 'ctrl' + 's')")
        self.big_boss.commentaires.append(com)
        self.bind("<Control-s>", self.big_boss.save)
        
        btn = self.boutons.def_bouton('Modifier lab', self.big_boss.Modification, 7)
        com = btn.add_commentaire(self, "Permet de reconstruire un mur détruit\n(raccourci : 'm')")
        self.big_boss.commentaires.append(com)
        self.bind("<KeyRelease-m>", self.big_boss.Modification)
        
        btn = self.boutons.def_bouton('Editer Zones', self.big_boss.editer_aires, 6, type_combobox = ["Détruire (tout vide)", "Reconstruire (quadrillage)"])
        self.big_boss.commentaires.append(com)
        com = btn.add_commentaire(self, "Permet d'éditer de grandes zones du labyrinthe :\n\n- Le mode Détruire permet d'effacer la zone\n- Le mode Reconstruire permet de retracer\nle quadrillage dans la zone", aligne_in="left")
    
        btn = self.boutons.def_bouton('Réglages', self.big_boss.reglages, 0)
        com = btn.add_commentaire(self, "Accès au réglages\n(raccourci : 'r')")
        self.big_boss.commentaires.append(com)
        self.bind("<KeyRelease-r>", self.big_boss.reglages)

    def init_logo (self) :
        #self.logo = tk.Label(self.big_boss.barre_laterale_droite)
        self.logo = tk.Button(self.barre_laterale_droite, command=self.big_boss.infos_generales)
        self.logo.grid(column=0, row=0)
        self.open_image()

    def open_image (self) :
        self.image = Image.open("Idées LOGO/"+self.big_boss.parametres["logo builder"])
        xx, yy = self.image.size
        ratio = xx / yy
        x_max = self.barre_laterale_droite.winfo_width()
        x = round(60/100 * x_max)
        y = round(x / ratio)
        self.image = self.image.resize((x,y))
        self.image_photo = ImageTk.PhotoImage(self.image)
        self.logo["image"] = self.image_photo

    def init_barres_text (self) :
        self.barre_de_texte = tk.StringVar()
        self.barre_de_texte.set("Début")
        self.barre_affichage_texte = tk.Label(self, textvariable= self.barre_de_texte)
        self.barre_affichage_texte.grid(column= 0, row= 0, sticky=tk.NSEW)

        self.position_sortie = tk.StringVar()
        self.position_sortie.set("Sortie")
        self.affichage_position_sortie = tk.Label(self.frame_sortie, textvariable= self.position_sortie)
        self.affichage_position_sortie.grid(column= 0, row= 0)

        self.position_entree = tk.StringVar()
        self.position_entree.set("Entrée")
        self.affichage_position_entree = tk.Label(self.frame_entree, textvariable= self.position_entree)
        self.affichage_position_entree.grid(column= 0, row= 0)
        
        self.affichage_mode = tk.Label(self.frame_dep, text= "Mode :")
        self.affichage_mode.grid(column= 0, row= 0)
        
    def refresh_barre_de_texte (self) :
        self.barre_de_texte.set("Labirinthe  "+self.big_boss.lab_name+" "*10+str(self.balle.x)+" "+str(self.balle.y))

    def redimentionner (self,event=None) :
        self.x = self.winfo_width()
        self.y = self.winfo_height()
        text_size = int(log(self.winfo_width()/100))
        self.barre_affichage_texte.config(font=("Verdana", text_size * 6))
        self.affichage_position_sortie.config(font=("Verdana", text_size * 4))
        self.affichage_position_entree.config(font=("Verdana", text_size * 4))
        self.affichage_mode.config(font=("Verdana", text_size * 5))
        self.canvas.redimentionner()
        self.boutons.redimentionner(text_size = int(text_size * 5.5))
        self.open_image()
