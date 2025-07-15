
class Lab_canvas_crea (tk.Canvas) :
    def __init__ (self, big_boss, fenetre, grille, param=[0,1]) :
        """
        Initialise le canvas de travail dans la fenêtre fen
        :param x: (int) la largueur du canvas à créer
        :param y: (int) la longueur du canvas à créer
        :param color: (int) la couleur du canvas à créer
        """
        tk.Canvas.__init__(self)
        self.big_boss = big_boss
        self.fenetre = fenetre
        self.grille = grille
        self.couleurs(change=False, initial_value=self.big_boss.parametres["initial color mode"])
        self.grid(column= param[0], row= param[1], sticky=tk.NSEW)
        self.mode_phase = 0
        self.bind("<Motion>", self.mouv_enca_colo)
        self.bind("<Button-1>", self.clic)

    def init_entitees (self, balle) :
        self.balle = balle

    def taille_auto (self) :
        "Calcule la taille en pixel d'un coté des cases carré à partir de la hauteur h et le la longeur l de la grille de définition"
        if self.winfo_height() / (self.grille.y + 1) < self.winfo_width() / (self.grille.x + 1) :
            self.taille = self.winfo_height() / (self.grille.y+2)
        else :
            self.taille = self.winfo_width() / (self.grille.x+2)

    def origines (self) :
        "Calcule et renvoi sous forme de tuple les origines en x et y (en haut à gauche du canvas)"
        self.origine_x = (self.winfo_width() - (self.taille * (self.grille.x))) / 2
        self.origine_y = (self.winfo_height() - (self.taille * (self.grille.y))) / 2
        assert self.origine_x > 0 and self.origine_y > 0

    def trace_grille (self) :
        "Trace avec Tkinter un quadrillage de la grille g"
        for y in range (len(self.grille.lab)) :
            for x in range (len(self.grille.lab[0])) :
                if self.grille.lab[y][x] == "1" or self.grille.lab[y][x] == "3" :
                    self.barre_horizontale (self.origine_x + x*self.taille, self.origine_y + y*self.taille, self.taille, self.color_grille)
                if self.grille.lab[y][x] == "2" or self.grille.lab[y][x] == "3" :
                    self.barre_verticale (self.origine_x + x*self.taille, self.origine_y + y*self.taille, self.taille, self.color_grille)

    def barre_verticale (self, ox, oy, t, color, taille=1) :
        "Trace dans le canvas une ligne verticale"
        self.create_line (ox,oy,ox,oy+t, fill= color, width=taille)

    def barre_horizontale (self, ox, oy, t, color, taille=1) :
        "Trace dans le canvas une ligne verticale"
        self.create_line (ox,oy,ox+t,oy, fill= color, width=taille)
    
    def refresh_lab (self, refresh_barre_de_texte = True) :
        self.delete("all")
        self.trace_grille ()
        self.balle.init()
        if refresh_barre_de_texte :
            self.fenetre.refresh_barre_de_texte ()

    def couleurs (self, change=True, initial_value=False, event=None) :
        if change :
            if self.couleur_mode == "white" :
                self.couleur_mode = "black"
            else :
                self.couleur_mode = "white"
        elif initial_value :
            self.couleur_mode = initial_value
        if self.couleur_mode == "white" :
            self["bg"] = "white"
            self.color_grille = "black"
            self.color_balle = "blue"
            self.oposit_color_balle = "red"
            self.color_balle_out = "black"
        elif self.couleur_mode == "black" :
            self["bg"] = "black"
            self.color_grille = "white"
            self.color_balle = "red"
            self.oposit_color_balle = "blue"
            self.color_balle_out = "white"
        if change :
            self.refresh_lab()

    def redimentionner (self) :
        self.y = self.winfo_height()
        self.x = self.winfo_width()
        self.init_affichage_grille()
    
    def init_affichage_grille (self) :
        self.taille_auto ()
        self.origines ()
        self.refresh_lab ()

    def lancement_phase_1 (self) :
        assert self.mode_phase == 0
        self.mode_phase = 1
    
    def clic (self, event) :
        if self.big_boss.mode_actif :
            x = int((event.x - self.origine_x) // self.taille)
            y = int((event.y - self.origine_y) // self.taille)
            if 0 <= x <= self.grille.x-1 and 0 <= y <= self.grille.y-1 :
                if self.big_boss.mode_actif == "Aller à" :
                    self.mode_phase = 0
                    self.big_boss.aller_a_end(x,y)
                    self.refresh_lab()
                    self.encadrement_coloré(x, y, self.color_balle)
                    self.after("1000", self.refresh_lab)
                elif self.big_boss.mode_actif == "Détruire Aires" or self.big_boss.mode_actif == "Restorer Aires" :
                    if self.mode_phase == 1 :
                        self.coords_1_sur_2 = (x,y)
                        self.mode_phase = 2
                    elif self.mode_phase == 2 :
                        self.mode_phase = 0
                        if self.big_boss.mode_actif == "Détruire Aires" :
                            self.big_boss.editer_aires_detruire_end(self.coords_1_sur_2, (x,y))
                        if self.big_boss.mode_actif == "Restorer Aires" :
                            self.big_boss.editer_aires_restorer_end(self.coords_1_sur_2, (x,y))
                        self.refresh_lab()
                        self.zone_coloree(self.coords_1_sur_2[0], self.coords_1_sur_2[1], x, y, self.color_balle, self.color_balle)
                        self.after("1000", self.refresh_lab)
            else : #Pour arrêter le mode
                self.mode_phase = 0
                if self.big_boss.mode_actif == "Aller à" :
                    self.big_boss.aller_a_start() 
                elif self.big_boss.mode_actif == "Détruire Aires" :
                    self.big_boss.editer_aires_detruire_start()
                elif self.big_boss.mode_actif == "Restorer Aires" :
                    self.big_boss.editer_aires_restorer_start()
    
    def mouv_enca_colo (self, event) :
        if self.big_boss.mode_actif :
            x = int((event.x - self.origine_x) // self.taille)
            y = int((event.y - self.origine_y) // self.taille)
            if 0 <= x <= self.grille.x-1 and 0 <= y <= self.grille.y-1 :
                self.refresh_lab(refresh_barre_de_texte=False)
                if self.mode_phase == 1 :
                    self.encadrement_coloré(x, y, self.oposit_color_balle)
                elif self.mode_phase == 2 :
                    self.zone_coloree(self.coords_1_sur_2[0], self.coords_1_sur_2[1], x, y, self.color_balle, self.color_balle)
            else :
                self.refresh_lab(refresh_barre_de_texte=False)
    
    def encadrement_coloré (self, x:int, y:int, color:str) :
        self.barre_verticale (self.origine_x+x*self.taille, self.origine_y+y*self.taille, self.taille, color, 5)
        self.barre_horizontale (self.origine_x+x*self.taille, self.origine_y+y*self.taille, self.taille, color, 5)
        self.barre_verticale (self.origine_x+(x+1)*self.taille, self.origine_y+y*self.taille, self.taille, color, 5)
        self.barre_horizontale (self.origine_x+x*self.taille, self.origine_y+(y+1)*self.taille, self.taille, color, 5)

    def zone_coloree (self, x1:int, y1:int, x2:int, y2:int, color:str, outline:str = "black") :
        if x1 <= x2 :
            x2 += 1
        else :
            x1, x2 = x2, x1 + 1
        if y1 <= y2 :
            y2 += 1
        else :
            y1, y2 = y2, y1 + 1
        x1 = round(self.origine_x + (x1 * self.taille))
        y1 = round(self.origine_y + (y1 * self.taille))
        x2 = round(self.origine_x + (x2 * self.taille))
        y2 = round(self.origine_y + (y2 * self.taille))
        self.create_rectangle2 (x1, y1, x2, y2, fill=color, outline=outline, alpha=.5)
    
    def create_rectangle2 (self, x1, y1, x2, y2, **kwargs):
        if 'alpha' in kwargs:
            alpha = int(kwargs.pop('alpha') * 255)
            fill = kwargs.pop('fill')
            fill = self.fenetre.winfo_rgb(fill) + (alpha,)
            image = Image.new('RGBA', (abs(x2-x1), abs(y2-y1)), fill)
            self.image = ImageTk.PhotoImage(image)
            self.create_image(x1, y1, image=self.image, anchor='nw')
        self.create_rectangle(x1, y1, x2, y2, **kwargs)

