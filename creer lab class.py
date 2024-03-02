# Created on 12/06/22
# Last modified on 02/03/24
# Author : Maxence CHOISEL

import csv
import tkinter as tk
from tkinter.simpledialog import askinteger
from functools import partial
from PIL import Image,ImageTk
from math import log


class Lab_fen_crea (tk.Tk) :
    def __init__ (self, x:int = 1000, y:int = 800) :
        tk.Tk.__init__(self)
        self.x = x #= self.winfo_screenwidth() -200
        self.y = y #= self.winfo_screenheight() -100
        self.title("The Maze Builder")
        self.geometry (str(self.x)+"x"+str(self.y))
        self.min_x = 500
        self.min_y = 400
        self.minsize(self.min_x, self.min_y)
        self.init_config_grid()
        self.init_autres_classes()
        self.init_variables_globales()
        self.init_barres_boutons_et_text()
        self.bind("<Button-3>", self.redimentionner)
        
        self.canvas.init_affichage_grille()
    
    def init_config_grid (self) :
        self.nb_lignes = 20
        self.nb_colones = 10
        self.proportion_canvas_x = 90/100
        self.proportion_canvas_y = 90/100
        for i in range (self.nb_colones) :
            self.grid_columnconfigure(i, weight= 1, minsize= 1/self.nb_colones*self.min_x)
        for i in range (self.nb_lignes) :
            self.grid_rowconfigure(i, weight= 1, minsize= 1/self.nb_lignes*self.min_y)

    def init_autres_classes (self) :
        self.grille = Lab_grille_crea(self)
        self.canvas = Lab_canvas_crea(self, self.grille, 
                                    x= self.x * round(self.nb_colones * self.proportion_canvas_x)/self.nb_colones,
                                    y= self.y * round(self.nb_lignes * self.proportion_canvas_y)/self.nb_lignes,
                                    param = [0, round(self.nb_lignes * (1 - self.proportion_canvas_y)),
                                            round(self.nb_colones * self.proportion_canvas_x), round(self.nb_lignes * self.proportion_canvas_y)])
        self.balle = Lab_balle_crea(self, self.canvas, self.grille)
        self.grille.init_entitees(self.canvas, self.balle)
        self.canvas.init_entitees(self.balle)

    def init_barres_boutons_et_text (self) :
        self.barre_laterale = tk.Frame(self)
        self.barre_laterale.grid(column=round(self.nb_colones * self.proportion_canvas_x), row=0,
                                columnspan= round(self.nb_colones * (1 - self.proportion_canvas_x)), rowspan=self.nb_lignes, sticky=tk.NSEW)
        self.barre_laterale.grid_columnconfigure(0, weight= 1)
        self.barre_laterale.grid_rowconfigure(0, weight= 1)
        self.barre_laterale.grid_rowconfigure(1, weight= 4)
        self.init_logo()
        self.boutons = Boutons(self.barre_laterale, self, self.canvas, self.grille, self.balle)
        self.boutons.grid(column=0, row=1, sticky=tk.NSEW)

        self.init_barres_text()
        self.refresh_barre_de_texte()

    def init_logo (self) :
        self.logo = tk.Label(self.barre_laterale)
        self.logo.grid(column=0, row=0, sticky=tk.NSEW)
        self.open_image()

    def open_image (self) :
        self.image = Image.open("Idées LOGO/logo buitder 3.jpg")
        xx, yy = self.image.size
        ratio = xx / yy
        x_max = self.x * round(self.nb_colones * (1 - self.proportion_canvas_x)) / self.nb_colones
        x = round(160/100 * x_max)
        y = round(x / ratio)
        self.image = self.image.resize((x,y))
        self.image_photo = ImageTk.PhotoImage(self.image)
        self.logo["image"] = self.image_photo
        
    def init_variables_globales (self) :
        self.Modif = False
        self.dep = "Casse"

    def init_barres_text (self) :
        self.barre_de_texte = tk.StringVar()
        self.barre_de_texte.set("Début")
        self.barre_affichage_texte = tk.Label(self, textvariable= self.barre_de_texte)
        self.barre_affichage_texte.grid(column= 0, row= 0,
                                        columnspan= round(self.nb_colones * self.proportion_canvas_x),
                                        rowspan= round(self.nb_lignes * (1 - self.proportion_canvas_y)))

        self.position_sortie = tk.StringVar()
        self.position_sortie.set("Sortie")
        self.affichage_position_sortie = tk.Label(self.boutons.frame_sortie, textvariable= self.position_sortie)
        self.affichage_position_sortie.grid(column= 0, row= 0)

        self.position_entree = tk.StringVar()
        self.position_entree.set("Entrée")
        self.affichage_position_entree = tk.Label(self.boutons.frame_entree, textvariable= self.position_entree)
        self.affichage_position_entree.grid(column= 0, row= 0)
        
        self.affichage_mode = tk.Label(self.boutons.frame_dep, text= "Mode :")
        self.affichage_mode.grid(column= 0, row= 0)
        
    def refresh_barre_de_texte (self) :
        self.barre_de_texte.set("Labirinthe "+" "*10+str(self.balle.x)+" "+str(self.balle.y))
        
    def aller_a (self, event=None) :
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
                self.canvas.refresh_lab()
            else :
                tk.messagebox.showinfo ('Aller directement à',"Cette position n'existe pas ! (Syntaxe : 'position_x,position_y')\navec 0 <= position_x <= "+str(self.grille.x-1)+", et 0 <= position_y <= "+str(self.grille.y-1), icon = 'error')
        return

    def save (self, event=None) :
        n = tk.messagebox.askyesno ('Sauvegarder','Voulez-vous sauvegarder votre labirinthe comme un croquis (Yes : incomplet donc possibilité de le modifier plus tard) ou comme un labirinthe terminé (No : pas de possibilité de le modifier plus tard) ?')
        if n :
            e = tk.simpledialog.askstring ( title = "Numero du labirinthe"  , prompt = "Quel sera le numéro de votre croquis de labirinthe" , initialvalue = "")
            self.grille.save_as (e, True, self.grille.lab, self.grille.Entree, self.grille.Sortie)
        elif n is False :
            if self.grille.Entree == "off" or self.grille.Sortie == "off" :
                if self.grille.Entree == "off" and type(self.grille.Sortie) == tuple :
                    tk.messagebox.showinfo ('Sauvegarder','Pour sauvegrder la labirinthe il faut absolument une entrée valide !', icon= "error")
                elif self.grille.Sortie == "off" and type(self.grille.Entree) == tuple :
                    tk.messagebox.showinfo ('Sauvegarder','Pour sauvegrder la labirinthe il faut absolument une sortie valide !', icon= "error")
                else :
                    tk.messagebox.showinfo ('Sauvegarder','Pour sauvegrder la labirinthe il faut absolument une entrée et une sortie valide !', icon= "error")
            else :
                n = tk.simpledialog.askstring ( title = "Numero du labirinthe"  , prompt = "Quel sera le numéro de votre labirinthe" , initialvalue = "")
                self.grille.save_as (n, False, self.grille.lab, self.grille.Entree, self.grille.Sortie)
        return

    def new_lab (self, event=None) :
        self.chose_new_lab = Fen_chose_new_lab(self, self)
        self.chose_new_lab.mainloop()
    
    def open_lab_croquis (self) :
        self.chose_new_lab.destroy()
        n = tk.simpledialog.askstring ( title = "Nouveau labirinthe" , prompt = "Entrez le nom du croquis que vous voulez récupérer (ce qui est écrit après 'Croquis ') :" , initialvalue = "")
        if n is None :
            a = True
        else :
            a = self.grille.ouvrir_lab(n)
            print(a)
            if a == "fichier introuvable" :
                a = False
                tk.messagebox.showinfo ('Croqui introuvable','Le Croqui nommé : '+n+' est introuvable !',icon="error")
            else :
                self.grille.x = len(self.grille.lab[0]) - 1
                self.grille.y = len(self.grille.lab) - 1
                self.balle.def_position(self.grille.Entree[0], self.grille.Entree[1])
                self.canvas.init_affichage_grille()
                self.boutons.renommer("type deplacement", "Déplacement")
                self.dep = "Passe"

    def init_new_lab (self) :
        self.chose_new_lab.destroy()
        n = tk.simpledialog.askstring ( title = "Nouveau labirinthe" , prompt = "Entrez le nombre de cases en largeur et en hauteur de votre labirinthe :" , initialvalue = "largeur,hauteur")
        if n is not None :
            n = n.split(",")
            x = int(n[0])
            y = int(n[1])
            if 3 <= x <= 50 and 3 <= y <= 35 :
                self.grille.init_lab(x,y)
                self.canvas.init_affichage_grille()
            else :
                tk.messagebox.showinfo ('Nouveau labirinthe','Ce labirinthe n\'a pas de dimentions valides : x(min:3, max:50) et y(min:3, max:35) !', icon= "error")

    def sortie (self, event=None) :
        if self.Modif :
            tk.messagebox.showinfo ('Instaler une sortie','Impossible car déjà en cours de création d\'un mur !',icon = 'error')
        else :
            if type(self.grille.Sortie) == tuple :
                tk.messagebox.showinfo ('Instaler une sortie','La sortie à déjà été définie !',icon = 'error')
            else :
                if self.balle.x == 0 or self.balle.x == self.grille.x-1 or self.balle.y == 0 or self.balle.y == self.grille.y-1 :
                    self.grille.Sortie = "on"
                    self.dep = "Casse"
                    tk.messagebox.showinfo ('Instaler une sortie','Vous pouvez créer votre sortie avec les flèches !')
                    self.barre_de_texte.set("Vous pouver créer la sortie avec les flèches")
                else :
                    tk.messagebox.showinfo ('Instaler une sortie',"Pour instaler une sortie vous devez positionner la balle à l'endroit ou sera crée la sortie c'est à dire près d'un bord !",icon = 'error')
        return

    def sortie2 (self) :
        self.grille.Sortie = (self.balle.x, self.balle.y)
        self.position_sortie.set("Sortie : {};{}".format(self.grille.Sortie[0],self.grille.Sortie[1]))
        self.refresh_barre_de_texte()
        self.Change_type_deplacement ()
        return

    def entree (self, event=None) :
        if self.grille.Entree == "off" :
            self.grille.Entree = (self.balle.x, self.balle.y)
            self.position_entree.set("Entrée : {};{}".format(self.grille.Entree[0],self.grille.Entree[1]))
        else :
            MsgBox = tk.messagebox.askquestion ('Nouvelle entrée','Voulez-vous vraiment redefinir l\'entrée de votre labirinthe qui est à {};{} par {};{} ?'.format(self.grille.Entree[0],self.grille.Entree[1],self.balle.x,self.balle.y))
            if MsgBox == 'yes':
                self.grille.Entree = (self.balle.x, self.balle.y)
                self.position_entree.set("Entrée : {};{}".format(self.grille.Entree[0],self.grille.Entree[1]))
        return

    def Change_type_deplacement (self, event=None) :
        if self.dep == "Casse" :
            self.def_type_deplacement("Passe")
        else :
            self.def_type_deplacement("Casse")
            
    def def_type_deplacement (self, dep, event=None) :
        if dep == "Passe" :
            self.dep = "Passe"
            self.boutons.renommer("type deplacement", "Déplacement")
        elif dep == "Casse" :
            self.dep = "Casse"
            self.boutons.renommer("type deplacement", "Créer")
        else :
            print("ERREUR")

    def Modification (self, event=None) :
        if self.Modif :
            self.Modif = False
            self.barre_de_texte.set("Le mode modification à été arrêté")
        elif self.grille.Sortie == "on" :
            tk.messagebox.showinfo ('Créer un mur',"Impossible car déjà en cours de création d'une sortie !",icon = 'error')
        else :
            self.Modif =  True
            #MsgBox = tk.messagebox.showinfo ('Créer un mur','Vous pouvez restaurer un mur avec les flèches')
            self.barre_de_texte.set("Vous pouver créer un mur avec les flèches")
        return

    def redimentionner (self,event=None) :
        self.x = self.winfo_width()
        self.y = self.winfo_height()
        text_size_1 = int(5*log(self.winfo_width()/100))
        text_size_2 = int(4*log(self.winfo_width()/100))
        self.barre_affichage_texte.config(font=("Verdana", text_size_1))
        self.affichage_position_sortie.config(font=("Verdana", text_size_2))
        self.affichage_position_entree.config(font=("Verdana", text_size_2))
        self.affichage_mode.config(font=("Verdana", text_size_1))
        self.canvas.redimentionner()
        self.boutons.redimentionner(text_size = text_size_1)
        self.open_image()

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
        self.couleurs(change=False, initial_value="white")
        self.grid(column= param[0], row= param[1], columnspan= param[2], rowspan= param[3], sticky=tk.NSEW)
        
    def init_entitees (self, balle) :
        self.balle = balle

    def taille_auto (self) :
        "Calcule la taille en pixel d'un coté des cases carré à partir de la hauteur h et le la longeur l de la grille de définition"
        if self.y / (self.grille.y + 1) < self.x / (self.grille.x + 1) :
            self.taille = self.y / (self.grille.y+2)
        else :
            self.taille = self.x / (self.grille.x+2)

    def origines (self) :
        "Calcule et renvoi sous forme de tuple les origines en x et y (en haut à gauche du canvas)"
        self.origine_x = (self.x - (self.taille * (self.grille.x))) / 2
        self.origine_y = (self.y - (self.taille * (self.grille.y))) / 2
        assert self.origine_x > 0 and self.origine_y > 0

    def trace_grille (self) :
        "Trace avec Tkinter un quadrillage de la grille g"
        for y in range (len(self.grille.lab)) :
            for x in range (len(self.grille.lab[0])) :
                if self.grille.lab[y][x] == "1" or self.grille.lab[y][x] == "3" :
                    self.barre_horizontale (self.origine_x + x*self.taille, self.origine_y + y*self.taille, self.taille, self.color_grille)
                if self.grille.lab[y][x] == "2" or self.grille.lab[y][x] == "3" :
                    self.barre_verticale (self.origine_x + x*self.taille, self.origine_y + y*self.taille, self.taille, self.color_grille)

    def barre_verticale (self, ox, oy, t, color) :
        "Trace dans le canvas une ligne verticale"
        self.create_line (ox,oy,ox,oy+t, fill= color)

    def barre_horizontale (self, ox, oy, t, color) :
        "Trace dans le canvas une ligne verticale"
        self.create_line (ox,oy,ox+t,oy, fill= color)
    
    def refresh_lab (self) :
        self.delete("all")
        self.trace_grille ()
        self.balle.init()
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
            self.color_balle_out = "black"
        elif self.couleur_mode == "black" :
            self["bg"] = "black"
            self.color_grille = "white"
            self.color_balle = "red"
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

    def clic (self, event) :
        if self.boss.mode_chauve_souris :
            x = int((event.x - self.origine_x) // self.taille)
            y = int((event.y - self.origine_y) // self.taille)
            if 0 <= x <= self.grille.x-1 and 0 <= y <= self.grille.y-1 :
                pass

class Lab_grille_crea () :
    def __init__(self, fenetre, x=10, y=10) :
        self.fenetre = fenetre
        self.Entree = "off"
        self.Sortie = "off"
        self.init_lab(x,y)
    
    def init_entitees (self, canvas, balle) :
        self.canvas = canvas
        self.balle = balle
    
    def init_lab (self, x,y) :
        """
        Initialise le labirinthe à afficher
        """
        self.lab = self.grille_pleine (x,y)
        self.x = x
        self.y = y
        
    def ouvrir_lab (self, nom_du_lab) :
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
                    if count == 1 :
                        if tab == ["o","f","f"] :
                            self.Entree = "off"
                            self.fenetre.position_entree.set("Entrée")
                        else :
                            self.Entree = [int(tab[0]), int(tab[1])]
                            self.fenetre.position_entree.set("Entrée : {};{}".format(self.Entree[0],self.Entree[1]))
                    elif count == 2 :
                        if tab == ["o","f","f"] :
                            self.Sortie = "off"
                            self.fenetre.position_entree.set("Sortie")
                        else :
                            self.Sortie = [int(tab[0]), int(tab[1])]
                            self.fenetre.position_sortie.set("Sortie : {};{}".format(self.Sortie[0],self.Sortie[1]))
                    count += 1
                else :
                    table.append(tab)
            fichier.close()
            self.lab = table
            return
        
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

    def save_as (self, numero_du_lab, croquis, lab, entrée, sortie) :
        if croquis is True :
            nom = "Labyrinthes croquis/Croquis "+numero_du_lab
        else :
            nom = "Labyrinthes classiques/Labyrinthe "+numero_du_lab
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
        elif direction == "left" :
            condition_de_non_sortie = self.x > 0 and 0 <= self.y <= self.grille.y-1
            conbinaisons = ["1", "3", "0", "2"]
            x_ciblage, y_ciblage = 0, 0
            mouvement_x, mouvement_y = -1, 0
        elif direction == "up" :
            condition_de_non_sortie = self.y > 0 and 0 <= self.x <= self.grille.x-1
            conbinaisons = ["2", "3", "0", "1"]
            x_ciblage, y_ciblage = 0, 0
            mouvement_x, mouvement_y = 0, -1
        elif direction == "down" :
            condition_de_non_sortie = self.y < self.grille.y-1 and 0 <= self.x <= self.grille.x-1
            conbinaisons = ["2", "3", "0", "1"]
            x_ciblage, y_ciblage = 0, 1
            mouvement_x, mouvement_y = 0, 1
        if condition_de_non_sortie or self.grille.Sortie == "on" :
            if self.fenetre.Modif :
                if self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[0] :
                    self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[1]
                elif self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[2] :
                    self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[3]
                else :
                    tk.messagebox.askquestion ('Ajouter un mur','On ne peut pas créer un mur quand il existe déjà !',icon = 'warning')
                self.fenetre.Modif = False
                self.fenetre.refresh_barre_de_texte()
                self.canvas.refresh_lab ()
            else :
                if self.fenetre.dep == "Casse" :
                    if self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[1] :
                        self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[0]
                    elif self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[3] :
                        self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[2]
                    self.canvas.refresh_lab ()
                self.move(mouvement_x, mouvement_y)
                if self.grille.Sortie == "on" :
                    self.fenetre.sortie2 ()
        elif type(self.grille.Sortie) == tuple and (self.y + mouvement_y) == self.grille.Sortie[1] and (self.x + mouvement_x) == self.grille.Sortie[0] :
            MsgBox = tk.messagebox.askquestion ('Supprimer une sortie','Ceci est la sortie, voulez-vous la supprimer pour en recréer une autre par la suite ?',icon = 'warning')
            if MsgBox == 'yes':
                if self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[0] :
                    self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[1]
                elif self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[2] :
                    self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[3]
                self.canvas.refresh_lab ()
                self.grille.Sortie = "off"
                self.fenetre.position_sortie.set("Sortie")

    def haut (self, event) :
        self.fleches("up")
    
    def bas (self, event) :
        self.fleches("down")
    
    def droite (self, event) :
        self.fleches("right")

    def gauche (self, event) :
        self.fleches("left")



class Boutons(tk.Frame) :
    def __init__(self, boss, fenetre, canvas, grille, balle) :
        self.fenetre = fenetre
        self.canvas = canvas
        self.grille = grille
        self.balle = balle
        tk.Frame.__init__(self, boss)
        self.nb_lignes = 10
        self.grid_columnconfigure(0, weight= 1, minsize= (1-self.fenetre.proportion_canvas_x)*self.fenetre.min_x)
        for i in range (self.nb_lignes) :
            self.grid_rowconfigure(i, weight= 1, minsize= 1/self.nb_lignes*self.fenetre.min_y)
        
        self.items = {}
        
        # Définition de la configuration :
        self.def_bouton('Couleurs', self.canvas.couleurs, 0)
        self.fenetre.bind("<Control-KeyRelease-c>", self.canvas.couleurs)
        
        self.def_bouton('Aller à', self.fenetre.aller_a, 4)
        self.fenetre.bind("<KeyRelease-a>", self.fenetre.aller_a)
        
        self.frame_dep = tk.Frame(self)
        self.frame_dep.grid(row= 5)
        self.def_bouton('Créer', self.fenetre.Change_type_deplacement, 1, nom_diminutif= 'type deplacement', boss= self.frame_dep)
        self.fenetre.bind("<KeyRelease-space>", self.fenetre.Change_type_deplacement)
        self.fenetre.bind("<KeyRelease-d>", partial(self.fenetre.def_type_deplacement, "Passe"))
        self.fenetre.bind("<KeyRelease-c>", partial(self.fenetre.def_type_deplacement, "Casse"))
        
        self.frame_entree = tk.Frame(self)
        self.frame_entree.grid(row= 8)
        self.def_bouton('Créer une entrée', self.fenetre.entree, 1, boss= self.frame_entree)
        self.fenetre.bind("<KeyRelease-e>", self.fenetre.entree)
        
        self.frame_sortie = tk.Frame(self)
        self.frame_sortie.grid(row= 9)
        self.def_bouton('Créer une sortie', self.fenetre.sortie, 1, boss= self.frame_sortie)
        self.fenetre.bind("<KeyRelease-s>", self.fenetre.sortie)
        
        self.def_bouton('Nouveau Labyrinthe', self.fenetre.new_lab, 3)
        self.fenetre.bind("<KeyRelease-n>", self.fenetre.new_lab)
        
        self.def_bouton('Sauvegarder', self.fenetre.save, 2)
        self.fenetre.bind("<Control-s>", self.fenetre.save)
        
        self.def_bouton('Modifier lab', self.fenetre.Modification, 7)
        self.fenetre.bind("<KeyRelease-m>", self.fenetre.Modification)
        
        # Fin def configuration :
        self.init_visible_debut ()

    def init_visible_debut (self) :
        self.is_visible_debut = []
        for bout in self.items :
            if self.items[bout][2] == "Visible" :
                self.is_visible_debut.append(bout)

    def def_bouton (self, nom_affiche, effet, position, boss=None, nom_diminutif=None, visibilite="Visible") :
        if nom_diminutif is None :
            nom_diminutif = nom_affiche
        if boss is None :
            boss = self
        self.items[nom_diminutif] = [tk.Button (boss, text=nom_affiche, command=effet), position, visibilite]
        if visibilite == "Visible" :
            self.items[nom_diminutif][0].grid(row= self.items[nom_diminutif][1])

    def redimentionner (self, text_size = None) :
        if text_size is None :
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


class Fen_chose_new_lab (tk.Toplevel) :
    def __init__ (self, boss, fenetre) :
        tk.Toplevel.__init__(self, boss)
        self.fenetre = fenetre
        self.title("Nouveau labirinthe")
        self.nb_lignes = 2
        self.nb_colones = 2
        for i in range (self.nb_colones) :
            self.grid_columnconfigure(i, weight= 1) 
        for i in range (self.nb_lignes) :
            self.grid_rowconfigure(i, weight= 1)
            
        self.text = tk.Text(self, wrap= tk.WORD, width=25, height=3, padx=50, pady=20, font=("Helvetica", 15))
        self.text.insert(0.1, "Voulez-vous ouvrir un croquis déjà existant ou voulez-vous créer un nouveau labirinthe ?")
        self.text['state'] = 'disabled'
        self.text.grid(column=0, row=0, columnspan=2)
        
        self.bouton_2 = tk.Button (self, text="Croquis", padx=20, pady=10, font=("Helvetica", 13), command=self.fenetre.open_lab_croquis)
        self.bouton_2.grid(column=0, row=1)
        self.bouton_1 = tk.Button (self, text="Nouveau", padx=20, pady=10, font=("Helvetica", 13), command=self.fenetre.init_new_lab)
        self.bouton_1.grid(column=1, row=1)
        
        self.resizable(False, False)
        self.focus_set()
        
        



if __name__ == "__main__" :
    fen_lab = Lab_fen_crea()
    fen_lab.mainloop()
