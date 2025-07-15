
class Laby_canvas (ot.Structure_globale.Canvas) :
    "Canvas d´affichage du labyrinthe"
    def __init__(self, big_boss, param=[0,1]) :
        self.big_boss = big_boss
        ot.Structure_globale.Canvas.__init__(self, self.big_boss.parametres["initial color mode"])
        self.grid(column= param[0], row= param[1], sticky=tk.NSEW)
    
    def init_entitees (self, fenetre, grille, balle) :
        self. fenetre = fenetre
        self. grille = grille
        self. balle = balle
    
    def nouvelle_partie (self) :
        self.grille.init_lab()
        self.delete("all")
        self.taille_auto ()
        self.origines ()
        self.balle.init()
        self.trace_grille ()
        self.fenetre.barre_principale.refresh_all()
        self.balle.init_var ()
    
    def trace_grille (self) :
        "Trace avec Tkinter un quadrillage de la grille g"
        if self.big_boss.niveau.numero == 4 :
            for el in self.grille.Murs_lab :
                if el[2] == "1" :
                    self.barre_horizontale (self.origine_x + el[0]*self.taille, self.origine_y + el[1]*self.taille, self.taille, self.color_grille)
                if el[2] == "2" :
                    self.barre_verticale (self.origine_x + el[0]*self.taille, self.origine_y + el[1]*self.taille, self.taille, self.color_grille)
        elif not(self.big_boss.niveau.Niveau_max) :
            for el in self.grille.Partitions_lab :
                for y in range (el[0][1],el[1][1]) :
                    for x in range (el[0][0],el[1][0]) :
                        if self.grille.lab[y][x] == "1" or self.grille.lab[y][x] == "3" :
                            self.barre_horizontale (self.origine_x + x*self.taille, self.origine_y + y*self.taille, self.taille, self.color_grille)
                        if self.grille.lab[y][x] == "2" or self.grille.lab[y][x] == "3" :
                            self.barre_verticale (self.origine_x + x*self.taille, self.origine_y + y*self.taille, self.taille, self.color_grille)
        if self.big_boss.niveau.numero > 1 and not(self.big_boss.niveau.Niveau_max) :
            self.trace_contours_lab ()
    
    def trace_contours_lab (self) :
        self.create_rectangle (self.origine_x,self.origine_y,self.origine_x+self.taille*(self.grille.x-1),self.origine_y+self.taille*(self.grille.y-1), outline= self.color_grille)
        if self.grille.sortie_lab[0] == self.grille.x-1 :
            self.barre_verticale (self.origine_x + self.taille * self.grille.sortie_lab[0], self.origine_y + self.taille * self.grille.sortie_lab[1], self.taille, self.color_canvas)
        if self.grille.sortie_lab[0] == -1 :
            self.barre_verticale (self.origine_x, self.origine_y+self.taille*self.grille.sortie_lab[1], self.taille, self.color_canvas)
        if self.grille.sortie_lab[1] == self.grille.y-1 :
            self.barre_horizontale (self.origine_x+self.taille*self.grille.sortie_lab[0], self.origine_y+self.taille*self.grille.sortie_lab[1], self.taille, self.color_canvas)
        if self.grille.sortie_lab[1] == -1 :
            self.barre_horizontale (self.origine_x+self.taille*self.grille.sortie_lab[0], self.origine_y, self.taille, self.color_canvas)
    
    def refresh_lab (self) :
        self.delete("all")
        self.balle.init()
        self.trace_grille ()
        self.fenetre.barre_principale.refresh_all()
    
    def redimentionner (self) :
        self.taille_auto ()
        self.origines ()
        self.refresh_lab ()

