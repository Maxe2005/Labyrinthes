
class Lab_balle_crea () :
    "La balle (le joueur) qui se déplace dans le labyrinthe"
    def __init__(self, big_boss, fenetre, canvas, grille, x=0, y=0) :
        self.big_boss = big_boss
        self.fenetre = fenetre
        self.canvas = canvas
        self.grille = grille
        self.x = x
        self.y = y
        self.fenetre.bind("<KeyRelease-Up>", self.haut)
        self.fenetre.bind("<KeyRelease-Down>", self.bas)
        self.fenetre.bind("<KeyRelease-Right>", self.droite)
        self.fenetre.bind("<KeyRelease-Left>", self.gauche)
        
        self.fenetre.bind("<KeyRelease-i>", self.haut)
        self.fenetre.bind("<KeyRelease-k>", self.bas)
        self.fenetre.bind("<KeyRelease-l>", self.droite)
        self.fenetre.bind("<KeyRelease-j>", self.gauche)
        
    def init (self) :
        bordure = 1/10 *self.canvas.taille
        o_x = round(self.canvas.origine_x + bordure)
        o_y = round(self.canvas.origine_y + bordure)
        pos_x = o_x + self.x * self.canvas.taille
        pos_y = o_y + self.y * self.canvas.taille
        t_balle = round(self.canvas.taille-2*bordure)
        self.balle = self.canvas.create_oval (pos_x, pos_y, pos_x+t_balle, pos_y+t_balle,  fill= self.canvas.color_balle, outline= self.canvas.color_balle_out)
    
    def def_position (self,x,y) :
        if type(x) == int and type(y) == int :
            self.x = x
            self.y = y
        else :
            self.x = 0
            self.y = 0
    
    def move (self, x, y) :
        """
        Déplace la balle et toutes les autres choses à faire en même temps (pour ne pas avoir à les répéter dans haut, bas, gauche et droite)
        """
        self.canvas.move(self.balle, x*self.canvas.taille, y*self.canvas.taille)
        self.y += y
        self.x += x
        self.fenetre.refresh_barre_de_texte()

    def fleches (self, direction) :
        if direction == "right" :
            condition_de_non_sortie = self.x < self.grille.x-1 and 0 <= self.y <= self.grille.y-1
            conbinaisons = ["1", "3", "0", "2"]
            x_ciblage, y_ciblage = 1, 0
            mouvement_x, mouvement_y = 1, 0
            creation_sortie = self.x == self.grille.x-1
        elif direction == "left" :
            condition_de_non_sortie = self.x > 0 and 0 <= self.y <= self.grille.y-1
            conbinaisons = ["1", "3", "0", "2"]
            x_ciblage, y_ciblage = 0, 0
            mouvement_x, mouvement_y = -1, 0
            creation_sortie = self.x == 0
        elif direction == "up" :
            condition_de_non_sortie = self.y > 0 and 0 <= self.x <= self.grille.x-1
            conbinaisons = ["2", "3", "0", "1"]
            x_ciblage, y_ciblage = 0, 0
            mouvement_x, mouvement_y = 0, -1
            creation_sortie = self.y == 0
        elif direction == "down" :
            condition_de_non_sortie = self.y < self.grille.y-1 and 0 <= self.x <= self.grille.x-1
            conbinaisons = ["2", "3", "0", "1"]
            x_ciblage, y_ciblage = 0, 1
            mouvement_x, mouvement_y = 0, 1
            creation_sortie = self.y == self.grille.y-1
        if condition_de_non_sortie :
            if self.big_boss.mode_actif == "Modification" :
                if self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[0] :
                    self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[1]
                elif self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[2] :
                    self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[3]
                else :
                    messagebox.askquestion ('Ajouter un mur','On ne peut pas créer un mur quand il existe déjà !',icon = 'warning')
                self.big_boss.mode_actif = ""
                self.fenetre.refresh_barre_de_texte()
                self.canvas.refresh_lab ()
            else :
                if self.big_boss.type_deplacement == "Casse" :
                    if self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[1] :
                        self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[0]
                    elif self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[3] :
                        self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[2]
                    self.canvas.refresh_lab ()
                self.move(mouvement_x, mouvement_y)
                if self.big_boss.mode_actif == "Création de Sortie" :
                    self.big_boss.sortie_start () # Pour arrêter le mode
        elif self.big_boss.mode_actif == "Création de Sortie" and creation_sortie :
            if self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[1] :
                self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[0]
            elif self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[3] :
                self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[2]
            self.canvas.refresh_lab ()
            self.move(mouvement_x, mouvement_y)
            self.big_boss.sortie_end ()
        elif type(self.grille.Sortie) == tuple and (self.y + mouvement_y) == self.grille.Sortie[1] and (self.x + mouvement_x) == self.grille.Sortie[0] :
            self.move(mouvement_x, mouvement_y)
        if self.big_boss.mode_actif == "Aller à" :
            self.big_boss.aller_a_start() # Pour arrêter le mode

    def haut (self, event) :
        self.fleches("up")
    
    def bas (self, event) :
        self.fleches("down")
    
    def droite (self, event) :
        self.fleches("right")

    def gauche (self, event) :
        self.fleches("left")
