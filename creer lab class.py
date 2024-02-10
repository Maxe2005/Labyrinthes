# Created on 12/06/22
# Last modified on 28/01/24
# Author : Maxence CHOISEL

import csv
import tkinter as tk
from tkinter.simpledialog import askinteger
from functools import partial
from math import log


class Lab_fen_crea (tk.Tk) :
    def __init__ (self, x_fen:int = 1000, y_fen:int = 800) :
        tk.Tk.__init__(self)
        self.x = x_fen #= self.winfo_screenwidth() -200
        self.y = y_fen #= self.winfo_screenheight() -100
        self.title("The Maze Builder")
        self.geometry (str(self.x)+"x"+str(self.y))
        self.minsize(500, 400)

        self.Modif = False
        self.dep = 1

        self.grille = Lab_grille_crea(self)
        self.canvas = Lab_canvas_crea(self, self.grille)
        self.balle = Lab_balle_crea(self, self.canvas, self.grille)
        self.grille.init_entitees(self.canvas, self.balle)
        self.canvas.init_entitees(self.balle)

        self.init_barres_text()
        self.boutons = Boutons(self, self.canvas, self.grille, self.balle)
        self.refresh_barre_de_texte()
        
        self.bind("<space>", self.Deplacement)
        self.bind("<KeyRelease-m>", self.Modification)
        
    def init_barres_text (self) :
        self.barre_de_texte = tk.StringVar()
        self.barre_de_texte.set("Début")
        self.barre_affichage_texte = tk.Label(self, textvariable= self.barre_de_texte)
        self.barre_affichage_texte.grid(column= 4, row= 1)

        self.position_sortie = tk.StringVar()
        self.position_sortie.set("Sortie")
        self.affichage_position_sortie = tk.Label(self, textvariable= self.position_sortie)
        self.affichage_position_sortie.grid(column= 8, row= 1)

        self.position_entree = tk.StringVar()
        self.position_entree.set("Entrée")
        self.affichage_position_entree = tk.Label(self, textvariable= self.position_entree)
        self.affichage_position_entree.grid(column= 7, row= 1)
        
    def refresh_barre_de_texte (self) :
        self.barre_de_texte.set("Labirinthe "+" "*10+str(self.balle.x)+" "+str(self.balle.y))
        
    def aller_a (self) :
        """
        Permet d'aller directement au labirinthe de son choix
        """
        n = tk.simpledialog.askstring ( title = "Aller directement à" , prompt = "Nouvelle position de la balle :" , initialvalue = "x,y")
        if n is not(None):
            n = n.split(",")
            x = int(n[0])
            y = int(n[1])
            if 0 <= x < self.grille.x and 0 <= y < self.grille.y :
                self.canvas.move(self.balle, (x-self.balle.x)*self.canvas.taille, (y-self.balle.y)*self.canvas.taille)
                self.balle.def_position(x,y)
                self.refresh_barre_de_texte()
            else :
                tk.messagebox.showinfo ('Aller directement à',"Cette position n'existe pas ! (Syntaxe : 'position_x,position_y')\navec 0 <= position_x <= "++", et ",icon = 'error')
        return

    def save (self) :
        n = tk.messagebox.askyesno ('Sauvegarder','Voulez-vous sauvegarder votre labirinthe comme un croquis (Yes : incomplet donc possibilité de le modifier plus tard) ou comme un labirinthe terminé (No : pas de possibilité de le modifier plus tard) ?')
        if n :
            e = tk.simpledialog.askstring ( title = "Numero du labirinthe"  , prompt = "Quel sera le numéro de votre croquis de labirinthe" , initialvalue = "")
            self.save_as (e, True, self.grille.lab, Entrée, Sortie)
        elif n is False :
            if Entrée == 0 or Sortie == 0 :
                if Entrée == 0 and type(Sortie) == tuple :
                    tk.messagebox.showinfo ('Sauvegarder','Pour sauvegrder la labirinthe il faut absolument une entrée valide !', icon= "error")
                elif Sortie == 0 and type(Entrée) == tuple :
                    tk.messagebox.showinfo ('Sauvegarder','Pour sauvegrder la labirinthe il faut absolument une sortie valide !', icon= "error")
                else :
                    tk.messagebox.showinfo ('Sauvegarder','Pour sauvegrder la labirinthe il faut absolument une entrée et une sortie valide !', icon= "error")
            else :
                n = tk.simpledialog.askstring ( title = "Numero du labirinthe"  , prompt = "Quel sera le numéro de votre labirinthe" , initialvalue = "")
                self.save_as (n, False, self.grille.lab, Entrée, Sortie)
        return

    def nouveau_lab (self) :
        n = tk.messagebox.askyesno ('Nouveau labirinthe','Voulez-vous ouvrir un croquis déjà existant (Yes) ou voulez-vous créer un nouveau labirinthe (No) ?')
        if n :
            a = False
            while not(a) :
                n = tk.simpledialog.askstring ( title = "Nouveau labirinthe" , prompt = "Entrez le nom du croquis que vous voulez récupérer (ce qui est écrit après 'Croquis ') :" , initialvalue = "")
                if n is None :
                    a = True
                else :
                    a = self.grille.ouvrir_lab(n)
                    if a == "fichier introuvable" :
                        a = False
                        tk.messagebox.showinfo ('Croqui introuvable','Le Croqui nommé : '+n+' est introuvable !',icon="error")
                    else :
                        lab = a
                        self.grille.x = len(lab[0])
                        self.grille.y = len(lab)
                        self.balle.def_position(Entrée[0], Entrée[1])
                        #programme()
                        deplace.set("Déplacement")
                        self.dep = 1
        elif n is False :
            n = tk.simpledialog.askstring ( title = "Nouveau labirinthe" , prompt = "Entrez le nombre de cases en largeur et en hauteur de votre labirinthe :" , initialvalue = "largeur,hauteur")
            if n is not None :
                n = n.split(",")
                x = int(n[0])
                y = int(n[1])
                if 2 < x < 51 and 2 < y < 36 :
                    self.grille.init_lab(x,y)
                    #programme()
                else :
                    tk.messagebox.showinfo ('Nouveau labirinthe','Ce labirinthe n´a pas de dimentions valides : x(min:3, max:50) et y(min:3, max:35) !', icon= "error")
        return

    def Quitter () :
        global fen
        MsgBox = tk.messagebox.askquestion ('Quitter','Voulez-vous vraiment quitter le jeu?',icon = 'error')
        if MsgBox == 'yes':
            fen.destroy()
        return

    def sortie (self) :
        if self.Modif :
            tk.messagebox.showinfo ('Instaler une sortie','Impossible car déjà en cours de création d´un mur !',icon = 'error')
        else :
            if type(self.Sortie) == tuple :
                tk.messagebox.showinfo ('Instaler une sortie','La sortie à déjà été définie !',icon = 'error')
            else :
                if self.balle.x == 0 or self.balle.x == self.grille.x-2 or self.balle.y == 0 or self.balle.y == self.grille.y-2 :
                    self.Sortie = 1
                    self.dep = 0
                    tk.messagebox.showinfo ('Instaler une sortie','Vous pouvez créer votre sortie avec les flèches !')
                    self.barre_de_texte.set("Vous pouver créer la sortie avec les flèches")
                else :
                    tk.messagebox.showinfo ('Instaler une sortie','Pour instaler une sortie vous devez psitionner la balle à l´endroit ou sera crée la sortie c´est à dire près d´un bord !',icon = 'error')
        return

    def sortie2 (self) :
        Sortie = (self.balle.x, self.balle.y)
        self.position_sortie.set("Sortie : {};{}".format(Sortie[0],Sortie[1]))
        self.refresh_barre_de_texte()
        self.Deplacement (None)
        return

    def entree (self) :
        if Entrée == 0 :
            Entrée = (self.balle.x, self.balle.y)
            self.position_entree.set("Entrée : {};{}".format(Entrée[0],Entrée[1]))
        else :
            MsgBox = tk.messagebox.askquestion ('Nouvelle entrée','Voulez-vous vraiment redefinir l\'entrée de votre labirinthe qui est à {};{} par {};{} ?'.format(Entrée[0],Entrée[1],self.balle.x,self.balle.y))
            if MsgBox == 'yes':
                Entrée = (self.balle.x, self.balle.y)
                self.position_entree.set("Entrée : {};{}".format(Entrée[0],Entrée[1]))
        return

    def Deplacement (self, event) :
        global deplace, dep
        if dep == 0 :
            deplace.set("Déplacement")
            dep = 1
        else :
            deplace.set("Créer")
            dep = 0
        return

    def Modifiant (self) :
        if self.Sortie == 1 :
            tk.messagebox.showinfo ('Créer un mur',"Impossible car déjà en cours de création d'une sortie !",icon = 'error')
        else :
            self.Modif =  True
            #MsgBox = tk.messagebox.showinfo ('Créer un mur','Vous pouvez restaurer un mur avec les flèches')
            self.barre_de_texte.set("Vous pouver créer un mur avec les flèches")
        return

    def Modification (self, event) :
        if self.Modif :
            self.Modif = False
        else :
            self.Modifiant ()
        return


class Lab_canvas_crea (tk.Canvas) :
    def __init__ (self, fenetre, grille, x=700, y=500, param=[0,1,10,7]) :
        """
        Initialise le canvas de travail dans la fenêtre fen
        :param x: (int) la largueur du canvas à créer
        :param y: (int) la longueur du canvas à créer
        :param color: (int) la couleur du canvas à créer
        """
        tk.Canvas.__init__(self)
        self.fenetre = fenetre
        self.grille = grille
        self.x = x 
        self.y = y
        self.configure(width=self.x, height=self.y)
        self.couleurs(change=False, initial_value="white")
        self.grid(column= param[0], row= param[1], columnspan= param[2], rowspan= param[3], sticky=tk.NSEW)
        
    def init_entitees (self, balle) :
        self.balle = balle

    def taille_auto (self) :
        "Calcule la taille en pixel d'un coté des cases carré à partir de la hauteur h et le la longeur l de la grille de définition"
        if self.y / self.grille.y < self.x / self.grille.x :
            self.taille = self.y / (self.grille.y+1)
        else :
            self.taille = self.x / (self.grille.x+1)

    def origines (self) :
        "Calcule et renvoi sous forme de tuple les origines en x et y (en haut à gauche du canvas)"
        self.origine_x = (self.x - (self.taille * (self.grille.x-1))) / 2
        self.origine_y = (self.y - (self.taille * (self.grille.y-1))) / 2
        assert self.origine_x > 0 and self.origine_y > 0

    def trace_grille (self) :
        "Trace avec Tkinter un quadrillage de la grille g"
        for y in range (len(self.grille.lab)) :
            for x in range (len(self.grille.lab[0])) :
                if self.grille.lab[y][x] == "1" or self.grille.lab[y][x] == "3" :
                    self.barre_horizontale (self.origine_x + x*self.taille, self.origine_y + y*self.taille, self.taille, self.color_grille)
                if self.grille.lab[y][x] == "2" or self.grille.lab[y][x] == "3" :
                    self.barre_verticale (self.origine_x + x*self.taille, self.origine_y + y*self.taille, self.taille, self.color_grille)
        self.create_rectangle (self.origine_x,self.origine_y,self.origine_x+self.taille*(self.grille.x-1),self.origine_y+self.taille*(self.grille.y-1), outline= self.color_grille)

    def barre_verticale (self, ox, oy, t, color) :
        "Trace dans le canvas une ligne verticale"
        self.create_line (ox,oy,ox,oy+t, fill= color)

    def barre_horizontale (self, ox, oy, t, color) :
        "Trace dans le canvas une ligne verticale"
        self.create_line (ox,oy,ox+t,oy, fill= color)
    
    def refresh_lab (self) :
        self.delete("all")
        self.balle.init()
        self.trace_grille ()
        self.fenetre.affichage_barre_principale ()

    def couleurs (self, change=True, initial_value=False) :
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
            self.color_balle_out = "black"
        elif self.couleur_mode == "black" :
            self["bg"] = "black"
            self.color_grille = "white"
            self.color_balle = "red"
            self.color_balle_out = "white"
        if change :
            self.refresh_lab()

    def redimentionner (self) :
        self.x = self.fenetre.x * (self.fenetre.nb_colones-6)/self.fenetre.nb_colones
        self.y = self.fenetre.y * (self.fenetre.nb_lignes-1)/self.fenetre.nb_lignes
        self.taille_auto ()
        self.origines ()
        self.refresh_lab ()
    

class Lab_grille_crea () :
    def __init__(self, fenetre, x=10, y=10) :
        self.fenetre = fenetre
        self.Entrée = 0
        self.Sortie = 0
        self.init_lab(x,y)
    
    def init_entitees (self, canvas, balle) :
        self.canvas = canvas
        self.balle = balle
    
    def init_lab (self, x,y) :
        """
        Initialise le labirinthe à afficher
        """
        self.lab = self.grille_pleine (x,y)
        self.x = x + 1
        self.y = y + 1
        
    def ouvrir_lab (self, nom_du_lab) :
        global Entrée, Sortie
        nom = "Labyrinthes croquis/Croquis "+nom_du_lab
        try :
            fichier = open (nom, "r")
        except :  
            return "fichier introuvable"
        else :
            table = []
            count = 1
            for ligne in fichier :
                ligne = ligne.rstrip()
                tab = ligne.split(",")
                if count != 3 :
                    for i in range (len(tab)) :
                        tab[i] = int(tab[i])
                    if count == 1 :
                        Entrée = tab
                        self.fenetre.position_entree.set("Entrée : {};{}".format(Entrée[0],Entrée[1]))
                        count += 1
                    elif count == 2 :
                        Sortie = tab
                        self.position_sortie.set("Sortie : {};{}".format(Sortie[0],Sortie[1]))
                        count += 1
                else :
                    table.append(tab)
            fichier.close()
            return table
        
    def grille_pleine (self, x:int ,y:int) :
        """
        Crée une grille sans trous
        :param x: (int) le nombre de cases en largeur
        :param y: (int) le nombre de cases en hauteur
        """
        assert x > 0 and y > 0
        g = []
        for i in range (y) :
            g.append(["3"]*x+["2"])
        g.append(["1"]*x+["0"])
        return g

    def inser_grille (self) :
        """
        Permet d'entrer une grille de labirinte (codé en 0,1,2,3) depuis la console
        """
        g = []
        count = 1
        while count != "fin" :
            a = input("Inserez la ligne n°"+str(count)+" de votre labirinthe ")
            if a != "fin" :
                if count == 1 :
                    t = len(a)
                if len(a) == t :
                    g.append(a)
                    count += 1
                else :
                    print ("Il y a une erreur dans la longueur de votre ligne, elle n'a pas la même longueur que la précédente !")
            else :
                count = "fin"
        return g

    def save_as (self, numéro_du_lab, croquis, lab, entrée, sortie) :
        if croquis == True :
            nom = "Labyrinthes croquis\Croquis "+numéro_du_lab
        else :
            nom = "Labyrinthes classiques\Labyrinthe "+numéro_du_lab
        with open (nom, "w", newline = "") as f :
            for i in range (-2,len(lab)) :
                writer = csv.writer (f, delimiter = ",", lineterminator = "\n")
                if i == -2 :
                    writer.writerow (entrée)
                elif i == -1 :
                    writer.writerow (sortie)
                else :
                    writer.writerow (lab[i])


class Lab_balle_crea () :
    "La balle (le joueur) qui se déplace dans le labyrinthe"
    def __init__(self, fenetre, canvas, grille, x=0, y=0) :
        self.fenetre = fenetre
        self.canvas = canvas
        self.grille = grille
        self.x = x
        self.y = y
        self.fenetre.bind("<KeyRelease-Up>", self.haut)
        self.fenetre.bind("<KeyRelease-Down>", self.bas)
        self.fenetre.bind("<KeyRelease-Right>", self.droite)
        self.fenetre.bind("<KeyRelease-Left>", self.gauche)
        
        self.fenetre.bind("<KeyRelease-o>", self.haut)
        self.fenetre.bind("<KeyRelease-l>", self.bas)
        self.fenetre.bind("<KeyRelease-m>", self.droite)
        self.fenetre.bind("<KeyRelease-k>", self.gauche)
        
    def init (self) :
        bordure = 1/10 *self.canvas.taille
        o_x = round(self.canvas.origine_x + bordure)
        o_y = round(self.canvas.origine_y + bordure)
        pos_x = o_x + self.x * self.canvas.taille
        pos_y = o_y + self.y * self.canvas.taille
        t_balle = round(self.canvas.taille-2*bordure)
        self.balle = self.canvas.create_oval (pos_x, pos_y, pos_x+t_balle, pos_y+t_balle,  fill= self.canvas.color_balle, outline= self.canvas.color_balle_out)
    
    def def_position (self,x,y) :
        self.x = x
        self.y = y
    
    def move (self, x, y) :
        """
        Déplace la balle et toutes les autres choses à faire en même temps (pour ne pas avoir à les répéter dans haut, bas, gauche et droite)
        """
        self.canvas.move(self.balle, x*self.canvas.taille, y*self.canvas.taille)
        self.y += y
        self.x += x
        self.fenetre.refresh_barre_de_texte()

    def haut (self, event) :
        if self.y > 0 and 0 <= self.x <= self.grille.x-2 or Sortie == 1 :
            if self.fenetre.Modif :
                if self.grille.lab[self.y][self.x] == "2" :
                    self.grille.lab[self.y][self.x] = "3"
                elif self.grille.lab[self.y][self.x] == "0" :
                    self.grille.lab[self.y][self.x] = "1"
                else :
                    tk.messagebox.askquestion ('Ajouter un mur','On ne peut pas créer un mur quand il existe déjà !',icon = 'warning')
                self.fenetre.Modif = False
                self.fenetre.refresh_barre_de_texte()
                self.canvas.refresh_lab ()
            else :
                if dep == 0 :
                    if self.grille.lab[self.y][self.x] == "3" :
                        self.grille.lab[self.y][self.x] = "2"
                    elif self.grille.lab[self.y][self.x] == "1" :
                        self.grille.lab[self.y][self.x] = "0"
                    self.canvas.refresh_lab ()
                self.move(0,-1)
                if Sortie == 1 :
                    self.fenetre.sortie2 ()
        elif type(Sortie) == tuple :
            if self.y-1 == Sortie[1] and self.x == Sortie[0] :
                MsgBox = tk.messagebox.askquestion ('Supprimer une sortie','Ceci est la sortie, voulez-vous la supprimer pour en recréer une autre par la suite ?',icon = 'warning')
                if MsgBox == 'yes':
                    if self.grille.lab[self.y][self.x] == "2" :
                        self.grille.lab[self.y][self.x] = "3"
                    elif self.grille.lab[self.y][self.x] == "0" :
                        self.grille.lab[self.y][self.x] = "1"
                    self.canvas.refresh_lab ()
                    Sortie = 0
                    self.position_sortie.set("Sortie")

    def bas (self, event) :
        if self.y < self.grille.y-2 and 0 <= self.x <= self.grille.x-2 or Sortie == 1 :
            if self.fenetre.Modif :
                if self.grille.lab[self.y+1][self.x] == "2" :
                    self.grille.lab[self.y+1][self.x] = "3"
                elif self.grille.lab[self.y+1][self.x] == "0" :
                    self.grille.lab[self.y+1][self.x] = "1"
                else :
                    MsgBox = tk.messagebox.askquestion ('Ajouter un mur','On ne peut pas créer un mur quand il existe déjà !',icon = 'warning')
                self.fenetre.Modif = False
                self.fenetre.refresh_barre_de_texte()
                self.canvas.refresh_lab ()
                if dep == 0 :
                    if self.grille.lab[self.y+1][self.x] == "3" :
                        self.grille.lab[self.y+1][self.x] = "2"
                    elif self.grille.lab[self.y+1][self.x] == "1" :
                        self.grille.lab[self.y+1][self.x] = "0"
                    self.canvas.refresh_lab ()
                self.move(0,1)
                if Sortie == 1 :
                    self.fenetre.sortie2 ()
        elif type(Sortie) == tuple :
            if self.y+1 == Sortie[1] and self.x == Sortie[0]:
                MsgBox = tk.messagebox.askquestion ('Supprimer une sortie','Ceci est la sortie, voulez-vous la supprimer pour en recréer une autre par la suite ?',icon = 'warning')
                if MsgBox == 'yes':
                    self.grille.lab[self.y+1][self.x] = "1"
                    self.canvas.refresh_lab ()
                    Sortie = 0
                    self.position_sortie.set("Sortie")

    def droite (self, event) :
        if self.x < self.grille.x-2 and 0 <= self.y <= self.grille.y-2 or Sortie == 1 :
            if self.fenetre.Modif :
                if self.grille.lab[self.y][self.x+1] == "1" :
                    self.grille.lab[self.y][self.x+1] = "3"
                elif self.grille.lab[self.y][self.x+1] == "0" :
                    self.grille.lab[self.y][self.x+1] = "2"
                else :
                    MsgBox = tk.messagebox.askquestion ('Ajouter un mur','On ne peut pas créer un mur quand il existe déjà !',icon = 'warning')
                self.fenetre.Modif = False
                self.fenetre.refresh_barre_de_texte()
                self.canvas.refresh_lab ()
            else :
                if dep == 0 :
                    if self.grille.lab[self.y][self.x+1] == "3" :
                        self.grille.lab[self.y][self.x+1] = "1"
                    elif self.grille.lab[self.y][self.x+1] == "2" :
                        self.grille.lab[self.y][self.x+1] = "0"
                    self.canvas.refresh_lab ()
                self.move(1,0)
                if Sortie == 1 :
                    self.fenetre.sortie2 ()
        elif type(Sortie) == tuple :
            if self.x+1 == Sortie[0] and self.y == Sortie[1] :
                MsgBox = tk.messagebox.askquestion ('Supprimer une sortie','Ceci est la sortie, voulez-vous la supprimer pour en recréer une autre par la suite ?',icon = 'warning')
                if MsgBox == 'yes':
                    self.grille.lab[self.y][self.x+1] = "2"
                    self.canvas.refresh_lab ()
                    Sortie = 0
                    self.position_sortie.set("Sortie")

    def gauche (self, event) :
        if self.x > 0 and 0 <= self.y <= self.grille.y-2 or Sortie == 1 :
            if self.fenetre.Modif :
                if self.grille.lab[self.y][self.x] == "1" :
                    self.grille.lab[self.y][self.x] = "3"
                elif self.grille.lab[self.y][self.x] == "0" :
                    self.grille.lab[self.y][self.x] = "2"
                else :
                    MsgBox = tk.messagebox.askquestion ('Ajouter un mur','On ne peut pas créer un mur quand il existe déjà !',icon = 'warning')
                self.fenetre.Modif = False
                self.fenetre.refresh_barre_de_texte()
                self.canvas.refresh_lab ()
            else :
                if dep == 0 :
                    if self.grille.lab[self.y][self.x] == "3" :
                        self.grille.lab[self.y][self.x] = "1"
                    elif self.grille.lab[self.y][self.x] == "2" :
                        self.grille.lab[self.y][self.x] = "0"
                    self.canvas.refresh_lab ()
                self.move(-1,0)
                if Sortie == 1 :
                    self.fenetre.sortie2 ()
        elif type(Sortie) == tuple :
            if self.x-1 == Sortie[0] and self.y == Sortie[1] :
                MsgBox = tk.messagebox.askquestion ('Supprimer une sortie','Ceci est la sortie, voulez-vous la supprimer pour en recréer une autre par la suite ?',icon = 'warning')
                if MsgBox == 'yes':
                    if self.grille.lab[self.y][self.x] == "1" :
                        self.grille.lab[self.y][self.x] = "3"
                    elif self.grille.lab[self.y][self.x] == "0" :
                        self.grille.lab[self.y][self.x] = "2"
                    self.canvas.refresh_lab ()
                    Sortie = 0
                    self.position_sortie.set("Sortie")



class Boutons(tk.Frame) :
    def __init__(self, fenetre, canvas, grille, balle) :
        self.fenetre = fenetre
        self.canvas = canvas
        self.grille = grille
        self.balle = balle
        tk.Frame.__init__(self,self.fenetre)
        self.nb_lignes = 10
        #self.grid_columnconfigure(0, weight= 1, minsize= (1-self.fenetre.proportion_canvas_x)*self.fenetre.min_x)
        #for i in range (self.nb_lignes) :
            #self.grid_rowconfigure(i, weight= 1, minsize= 1/self.nb_lignes*self.fenetre.min_y)
        
        self.items = {}
        
        self.def_bouton('Aller à', self.fenetre.aller_a, 4)
        self.def_bouton('Créer', partial(self.fenetre.Deplacement,None), 5, nom_diminutif= 'type deplacement')
        self.def_bouton('Créer une entrée', self.fenetre.entree, 7)
        self.def_bouton('Créer une sortie', self.fenetre.sortie, 8)
        #self.def_bouton('Nouveau Labyrinthe', self.fenetre.new_lab, 3)
        self.def_bouton('Sauvegarder', self.fenetre.save, 2)
        self.def_bouton('Modifier lab', self.fenetre.Modifiant, 0)

        self.init_visible_debut ()

    def init_visible_debut (self) :
        self.is_visible_debut = []
        for bout in self.items :
            if self.items[bout][2] == "Visible" :
                self.is_visible_debut.append(bout)

    def def_bouton (self, nom_affiche, effet, position, nom_diminutif=None, visibilite="Visible") :
        if nom_diminutif is None :
            nom_diminutif = nom_affiche
        self.items[nom_diminutif] = [tk.Button (self, text=nom_affiche, command=effet), position, visibilite]
        if visibilite == "Visible" :
            self.items[nom_diminutif][0].grid(row= self.items[nom_diminutif][1])

    def redimentionner (self) :
        text_size = int(5*log(self.fenetre.winfo_width()/100))
        for bout in self.items :
            self.items[bout][0].config(font=("Verdana", text_size))
                
    def afficher (self, nom_bouton) :
        self.items[nom_bouton][0].grid(row= self.items[nom_bouton][1])
        self.items[nom_bouton][2] = "Visible"

    def cacher (self, nom_bouton) :
        self.items[nom_bouton][0].grid_forget()
        self.items[nom_bouton][2] = "Caché"

    def affiche_boutons_debut (self) :
        for bout in self.is_visible_debut :
            self.afficher(bout)
    
    def cache_tout_sauf (self, ele=[]) :
        for bout in self.items :
            if bout not in ele :
                self.cacher(bout)
    
    def renommer (self, nom_bouton:str, new_nom_bouton:str) :
        self.items[nom_bouton][0]["text"] = new_nom_bouton

    def is_visible (self, nom_bouton:str) :
        return self.items[nom_bouton][2] == "Visible"


    
if __name__ == "__main__" :
    fen_lab = Lab_fen_crea()
    fen_lab.mainloop()
