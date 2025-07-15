
class Laby_balle () :
    "La balle (le joueur) qui se déplace dans le labyrinthe"
    def __init__(self,big_boss, fenetre, x=0, y=0) :
        self. big_boss = big_boss
        self.fenetre = fenetre
        self.x = x
        self.y = y
        self.init_variables()
        
        self.fenetre.bind("<Up>", self.haut)
        self.fenetre.bind("<Down>", self.bas)
        self.fenetre.bind("<Right>", self.droite)
        self.fenetre.bind("<Left>", self.gauche)
        """
        self.fenetre.bind("<o>", self.haut)
        self.fenetre.bind("<l>", self.bas)
        self.fenetre.bind("<m>", self.droite)
        self.fenetre.bind("<k>", self.gauche)
        """
    
    def init_entitees (self, grille, canvas) :
        self. grille = grille
        self. canvas = canvas
    
    def init_variables (self) :
        self.decoupe_dep = int(self.big_boss.parametres["decoupe du deplacement"]) # Nombre de sous-déplacement pour rendre le déplacement fluide
        self.vitesse = int(self.big_boss.parametres["vitesse deplacement"]) #temps d'attente (milisecondes) entre les différentes découpes du déplacement
    
    def init (self) :
        if not(self.big_boss.mode_hard) :
            bordure = 1/10 *self.canvas.taille
            o_x = round(self.canvas.origine_x + bordure)
            o_y = round(self.canvas.origine_y + bordure)
            pos_x = o_x + self.x * self.canvas.taille
            pos_y = o_y + self.y * self.canvas.taille
            t_balle = round(self.canvas.taille-2*bordure)
            self.balle = self.canvas.create_oval (pos_x, pos_y, pos_x+t_balle, pos_y+t_balle,  fill= self.canvas.color_balle, outline= self.canvas.color_balle_out)
            self.canvas.lift(self.balle)
        self.ou_aller()
    
    def def_position (self,x,y) :
        self.x = x
        self.y = y
    
    def init_var (self) :
        self.next_dir = None
        self.en_deplacement = False
        self.count_x = 0
        self.count_y = 0
    
    def mouve (self,x,y,deplacement_reel=True) :
        "Déplace la balle et toutes les autres choses à faire en même temps (pour ne pas avoir à les répéter dans haut, bas, gauche et droite)"
        if deplacement_reel :
            self.mouve_lisse(x*self.canvas.taille, y*self.canvas.taille)
            if self.big_boss.mode_hard :
                self.big_boss.change_voyant_mode_hard("moving")
                self.fenetre.after(200, self.big_boss.change_voyant_mode_hard, "ready", "blue")
        self.y += y
        self.x += x
        if self.big_boss.niveau.Niveau_max and self.contours_visibles :
            self.canvas.refresh_lab ()
            self.contours_visibles = False
        #else :
            #self.fenetre.barre_principale.refresh_all()
        if self.big_boss.niveau.numero > 1 :
            self.grille.Position_joueur_sur_back_lab_partition ()
        self.big_boss.win()
        self.ou_aller()
    
    def mouve_lisse (self, x, y) :
        if not(self.big_boss.mode_hard) :
            self.canvas.move(self.balle, x, y)
    
    def ou_aller (self) :
        "Rentre dans les variables booleenes les possiblilités de mouvement de la balle"
        if self.y >= 0 :
            self.aller_haut = self.grille.lab[self.y][self.x] != "1" and self.grille.lab[self.y][self.x] != "3"
        if self.y < self.grille.y -1 : # Pour éviter l´erreur out of range avec self.y+1
            self.aller_bas = self.grille.lab[self.y+1][self.x] != "1" and self.grille.lab[self.y+1][self.x] != "3"
        if self.x < self.grille.x -1:
            self.aller_droite = self.grille.lab[self.y][self.x+1] != "2" and self.grille.lab[self.y][self.x+1] != "3"
        if self.x >= 0 :
            self.aller_gauche = self.grille.lab[self.y][self.x] != "2" and self.grille.lab[self.y][self.x] != "3"
        return
    
    def fonction_dep (self,x=0,y=0,interne=False) :
        if interne :
            if self.en_deplacement :
                #c = self.canvas.coords(self.balle)
                if self.count_x % self.decoupe_dep == 0 and self.count_y % self.decoupe_dep == 0 : # arrivé sur une case (pas en plein mouvement)
                    self.mouve(x, y, deplacement_reel= False)
                    if (self.next_dir == (0,1) and self.aller_bas) or \
                        (self.next_dir == (0,-1) and self.aller_haut) or \
                        (self.next_dir == (1,0) and self.aller_droite) or \
                        (self.next_dir == (-1,0) and self.aller_gauche) : # prise en compte de la nouvelle direction voulue
                        self.mouve_lisse(self.next_dir[0]*self.canvas.taille/self.decoupe_dep, self.next_dir[1]*self.canvas.taille/self.decoupe_dep)
                        self.count_x += self.next_dir[0]
                        self.count_y += self.next_dir[1]
                        self.fenetre.after(self.vitesse, self.fonction_dep, self.next_dir[0], self.next_dir[1], True)
                        self.next_dir = None
                        if self.big_boss.mode_hard :
                            self.big_boss.change_voyant_mode_hard("change direction")
                    elif ((x,y) == (0,1) and self.aller_bas) or \
                        ((x,y) == (0,-1) and self.aller_haut) or \
                        ((x,y) == (1,0) and self.aller_droite) or \
                        ((x,y) == (-1,0) and self.aller_gauche) : # continuation du mouvement
                        self.mouve_lisse(x*self.canvas.taille/self.decoupe_dep, y*self.canvas.taille/self.decoupe_dep)
                        self.count_x += x
                        self.count_y += y
                        self.fenetre.after(self.vitesse, self.fonction_dep, x, y, True)
                    else : # arrêt car mur rencontré
                        self.en_deplacement = False
                        if self.big_boss.mode_hard :
                            self.big_boss.change_voyant_mode_hard("ready")
                else : # continuer le mouvement
                    self.mouve_lisse(x*self.canvas.taille/self.decoupe_dep, y*self.canvas.taille/self.decoupe_dep)
                    self.count_x += x
                    self.count_y += y
                    self.fenetre.after(self.vitesse,self.fonction_dep,x,y,True)
        elif self.en_deplacement : # affectation de la prochaine direction demandée
                self.next_dir = (x,y)
        elif ((x,y) == (0,1) and self.aller_bas) or \
            ((x,y) == (0,-1) and self.aller_haut) or \
            ((x,y) == (1,0) and self.aller_droite) or \
            ((x,y) == (-1,0) and self.aller_gauche) : # début du mouvement
                self.en_deplacement = True
                self.mouve_lisse(x*self.canvas.taille/self.decoupe_dep, y*self.canvas.taille/self.decoupe_dep)
                self.count_x += x
                self.count_y += y
                self.fenetre.after(self.vitesse, self.fonction_dep, x, y, True)
                if self.big_boss.mode_hard :
                    self.big_boss.change_voyant_mode_hard("moving")
        elif self.big_boss.mode_hard :
            self.big_boss.change_voyant_mode_hard("impossible")
    
    def fleches (self, direction) :
        dif_x = 0
        dif_y = 0
        if direction == "right" :
            x = 1
            y = 0
            dif_x = 1
            condition_1 = self.x == self.grille.x-2
            condition_2 = self.x < self.grille.x-2
            type_mur = "2"
            condition_aller = self.aller_droite
        elif direction == "left" :
            x = -1
            y = 0
            condition_1 = self.x == 0
            condition_2 = self.x > 0
            type_mur = "2"
            condition_aller = self.aller_gauche
        elif direction == "up" :
            x = 0
            y = -1
            condition_1 = self.y == 0
            condition_2 = self.y > 0
            type_mur = "1"
            condition_aller = self.aller_haut
        elif direction == "down" :
            x = 0
            y = 1
            dif_y = 1
            condition_1 = self.y == self.grille.y-2
            condition_2 = self.y < self.grille.y-2
            type_mur = "1"
            condition_aller = self.aller_bas
        if self.x != self.grille.sortie_lab[0] or self.y != self.grille.sortie_lab[1] :
            if self.big_boss.type_deplacement == "Lisse" :
                self.fonction_dep (x=x, y=y)
            if self.big_boss.type_deplacement == "Sec"  :
                if condition_aller :
                    self.mouve(x, y)
                elif self.big_boss.mode_hard :
                    self.big_boss.change_voyant_mode_hard("impossible")
            if not(condition_aller) :
                if self.big_boss.niveau.Niveau_max and condition_1 :
                    self.canvas.delete("all")
                    self.init()
                    self.canvas.trace_contours_lab ()
                    self.contours_visibles = True
                elif self.big_boss.niveau.numero == 4 and not(self.big_boss.niveau.Niveau_max) and condition_2 and (self.x+dif_x, self.y+dif_y, type_mur) not in self.grille.Murs_lab :
                    self.grille.Murs_lab.append((self.x+dif_x, self.y+dif_y, type_mur))
                    if type_mur == "1" :
                        self.canvas.barre_horizontale (self.canvas.origine_x + (self.x+dif_x)*self.canvas.taille, self.canvas.origine_y + (self.y+dif_y)*self.canvas.taille, self.canvas.taille, self.canvas.color_grille)
                    elif type_mur == "2" :
                        self.canvas.barre_verticale (self.canvas.origine_x + (self.x+dif_x)*self.canvas.taille, self.canvas.origine_y + (self.y+dif_y)*self.canvas.taille, self.canvas.taille, self.canvas.color_grille)
                    self.grille.test_nb_murs_niv_4 ()
    
    def haut (self, event) :
        self.fleches("up")
    
    def bas (self, event) :
        self.fleches("down")
    
    def droite (self, event) :
        self.fleches("right")

    def gauche (self, event) :
        self.fleches("left")
