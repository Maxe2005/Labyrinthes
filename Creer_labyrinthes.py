# Created on 12/06/22
# Last modified on 02/03/24
# Author : Maxence CHOISEL

import csv
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from functools import partial
from PIL import Image,ImageTk
from math import log
from os import path


class Entite_superieure () :
    def __init__(self) -> None:
        self.fenetre = Lab_fen_crea(self)
        self.grille = Lab_grille_crea(self, self.fenetre)
        self.canvas = Lab_canvas_crea(self, self.fenetre, self.grille, 
            x= self.fenetre.x * round(self.fenetre.nb_colones * self.fenetre.proportion_canvas_x)/self.fenetre.nb_colones,
            y= self.fenetre.y * round(self.fenetre.nb_lignes * self.fenetre.proportion_canvas_y)/self.fenetre.nb_lignes,
            param = [0, round(self.fenetre.nb_lignes * (1 - self.fenetre.proportion_canvas_y)), round(self.fenetre.nb_colones * self.fenetre.proportion_canvas_x), round(self.fenetre.nb_lignes * self.fenetre.proportion_canvas_y)])
        self.balle = Lab_balle_crea(self, self.fenetre, self.canvas, self.grille)
        self.fenetre.init_entitees(self.grille, self.canvas, self.balle)
        self.grille.init_entitees(self.canvas, self.balle)
        self.canvas.init_entitees(self.balle)
        self.init_variables_globales()
        
    def lancement (self) :
        self.init_barres_boutons_et_text()
        self.canvas.init_affichage_grille()
        self.fenetre.mainloop()
    
    def init_variables_globales (self) :
        self.Modif = False
        self.dep = "Casse"
        self.mode_aller_a = False
        self.mode_actif = ""
        
    def init_barres_boutons_et_text (self) :
        self.barre_laterale = tk.Frame(self.fenetre)
        self.barre_laterale.grid(column=round(self.fenetre.nb_colones * self.fenetre.proportion_canvas_x), row=0,
                                columnspan= round(self.fenetre.nb_colones * (1 - self.fenetre.proportion_canvas_x)), rowspan=self.fenetre.nb_lignes, sticky=tk.NSEW)
        self.barre_laterale.grid_columnconfigure(0, weight= 1)
        self.barre_laterale.grid_rowconfigure(0, weight= 1)
        self.barre_laterale.grid_rowconfigure(1, weight= 4)
        self.fenetre.init_logo()
        self.boutons = Boutons(self.barre_laterale, self, self.fenetre, self.canvas, self.grille, self.balle)
        self.boutons.grid(column=0, row=1, sticky=tk.NSEW)
        self.fenetre.init_barres_text()
        self.fenetre.refresh_barre_de_texte()
    
    def aller_a_start (self, event=None) :
        #self.aller_a_coord()
        self.mode_aller_a = True
        self.fenetre.barre_de_texte.set("Cliquez sur la case sur laquelle se rendre !")
        
    def aller_a_end (self, x, y) :
        self.mode_aller_a = False
        self.canvas.move(self.balle, (x-self.balle.x)*self.canvas.taille, (y-self.balle.y)*self.canvas.taille)
        self.balle.def_position(x,y)
        self.fenetre.refresh_barre_de_texte()
        
    def aller_a_coord (self, event=None) :
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
                self.fenetre.refresh_barre_de_texte()
                self.canvas.refresh_lab()
            else :
                messagebox.showinfo ('Aller directement à',"Cette position n'existe pas ! (Syntaxe : 'position_x,position_y')\navec 0 <= position_x <= "+str(self.grille.x-1)+", et 0 <= position_y <= "+str(self.grille.y-1), icon = 'error')
        return

    def save (self, event=None) :
        self.chose_save = Fen_chose_save(self, self, self.grille)
        self.chose_save.mainloop()
    
    def new_lab (self, event=None) :
        self.chose_new_lab = Fen_chose_new_lab(self, self)
        self.chose_new_lab.mainloop()
    
    def open_lab_croquis (self, selector:ttk.Combobox) :
        name_lab = selector.get()
        self.grille.ouvrir_lab(name_lab)
        self.chose_new_lab.destroy()
        self.grille.x = len(self.grille.lab[0]) - 1
        self.grille.y = len(self.grille.lab) - 1
        self.balle.def_position(self.grille.Entree[0], self.grille.Entree[1])
        self.boutons.renommer("type deplacement", "Déplacement")
        self.dep = "Passe"
        self.fenetre.redimentionner()

    def init_new_lab (self, nb_colones, nb_lignes, nb_colones_min:int, nb_colones_max:int, nb_lignes_min:int, nb_lignes_max:int, nom_lab:tk.Entry) :
        try :
            nb_colones = int(nb_colones.get())
            nb_lignes = int(nb_lignes.get())
            assert nb_colones_min <= nb_colones <= nb_colones_max
            assert nb_lignes_min <= nb_lignes <= nb_lignes_max
        except :
            messagebox.showinfo ('Nouveau labirinthe','Ce labirinthe n\'a pas de dimentions valides : x(min:'+str(nb_colones_min)+', max:'+str(nb_colones_max)+') et y(min:'+str(nb_lignes_min)+', max:'+str(nb_lignes_max)+') !', icon= "error")
        else :
            lab_nom = nom_lab.get()
            if " " in lab_nom :
                lab_nom = "_".join(lab_nom.split(" "))
            self.grille.init_lab(nb_colones, nb_lignes, nom_lab=lab_nom)
            self.balle.def_position(0,0)
            self.chose_new_lab.destroy()
            self.fenetre.redimentionner()

    def sortie_start (self, event=None) :
        if self.Modif :
            messagebox.showinfo ('Instaler une sortie','Impossible car déjà en cours de création d\'un mur !',icon = 'error')
        elif self.balle.x == self.grille.Sortie[0] and self.balle.y == self.grille.Sortie[1] :
            messagebox.showinfo ('Instaler une sortie','Impossible car vous êtes dans la sortie !',icon = 'error')
        elif self.grille.Sortie == "on" :
            self.grille.Sortie = self.sortie_precedante
            self.fenetre.barre_de_texte.set("Le mode 'Création de Sortie' à été arrêté")
            self.fenetre.after(2000, self.refresh_barre_de_texte)
        elif self.balle.x == 0 or self.balle.x == self.grille.x-1 or self.balle.y == 0 or self.balle.y == self.grille.y-1 :
            self.sortie_precedante = self.grille.Sortie
            self.grille.Sortie = "on"
            self.fenetre.barre_de_texte.set("Vous pouver créer la sortie avec les flèches")
        else :
            messagebox.showinfo ('Instaler une sortie',"Pour instaler une sortie vous devez positionner la balle à l'endroit ou sera crée la sortie c'est à dire près d'un bord !",icon = 'error')

    def sortie_end (self) :
        self.grille.Sortie = (self.balle.x, self.balle.y)
        if type(self.sortie_precedante) == tuple and self.sortie_precedante != self.grille.Sortie :
            if self.sortie_precedante[0] == -1 :
                if self.grille.lab[self.sortie_precedante[1]][0] == "0" :
                    self.grille.lab[self.sortie_precedante[1]][0] = "2"
                elif self.grille.lab[self.sortie_precedante[1]][0] == "1" :
                    self.grille.lab[self.sortie_precedante[1]][0] = "3"
            elif self.sortie_precedante[1] == -1 :
                if self.grille.lab[0][self.sortie_precedante[0]] == "0" :
                    self.grille.lab[0][self.sortie_precedante[0]] = "1"
                elif self.grille.lab[0][self.sortie_precedante[0]] == "2" :
                    self.grille.lab[0][self.sortie_precedante[0]] = "3"
            elif self.sortie_precedante[0] == self.grille.x :
                self.grille.lab[self.sortie_precedante[1]][self.sortie_precedante[0]] = "2"
            elif self.sortie_precedante[1] == self.grille.y :
                self.grille.lab[self.sortie_precedante[1]][self.sortie_precedante[0]] = "1"
            self.canvas.refresh_lab()
        self.position_sortie.set("Sortie : {};{}".format(self.grille.Sortie[0],self.grille.Sortie[1]))
        self.refresh_barre_de_texte()

    def entree (self, event=None) :
        if self.grille.Entree == "off" :
            self.grille.Entree = (self.balle.x, self.balle.y)
            self.position_entree.set("Entrée : {};{}".format(self.grille.Entree[0],self.grille.Entree[1]))
        else :
            MsgBox = messagebox.askquestion ('Nouvelle entrée','Voulez-vous vraiment redefinir l\'entrée de votre labirinthe qui est à {};{} par {};{} ?'.format(self.grille.Entree[0],self.grille.Entree[1],self.balle.x,self.balle.y))
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
            self.fenetre.barre_de_texte.set("Le mode 'Modification' à été arrêté")
            self.fenetre.after(2000, self.fenetre.refresh_barre_de_texte)
        elif self.grille.Sortie == "on" :
            messagebox.showinfo ('Créer un mur',"Impossible car déjà en cours de création d'une sortie !",icon = 'error')
        else :
            self.Modif =  True
            self.fenetre.barre_de_texte.set("Vous pouver créer un mur avec les flèches")



class Lab_fen_crea (tk.Tk) :
    def __init__ (self, master, x:int = 1000, y:int = 800) :
        tk.Tk.__init__(self)
        self.master = master
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
        self.nb_lignes = 20
        self.nb_colones = 10
        self.proportion_canvas_x = 95/100
        self.proportion_canvas_y = 90/100
        for i in range (self.nb_colones) :
            self.grid_columnconfigure(i, weight= 1, minsize= 1/self.nb_colones*self.min_x)
        for i in range (self.nb_lignes) :
            self.grid_rowconfigure(i, weight= 1, minsize= 1/self.nb_lignes*self.min_y)

    def init_logo (self) :
        self.logo = tk.Label(self.master.barre_laterale)
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
        self.barre_de_texte.set("Labirinthe  "+self.lab_name+" "*10+str(self.balle.x)+" "+str(self.balle.y))

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


class Lab_canvas_crea (tk.Canvas) :
    def __init__ (self, master, fenetre, grille, x=700, y=500, param=[0,1,10,7]) :
        """
        Initialise le canvas de travail dans la fenêtre fen
        :param x: (int) la largueur du canvas à créer
        :param y: (int) la longueur du canvas à créer
        :param color: (int) la couleur du canvas à créer
        """
        tk.Canvas.__init__(self)
        self.master = master
        self.fenetre = fenetre
        self.grille = grille
        self.x = x 
        self.y = y
        self.couleurs(change=False, initial_value="white")
        self.grid(column= param[0], row= param[1], columnspan= param[2], rowspan= param[3], sticky=tk.NSEW)
        
        self.bind("<Motion>", self.mouv_enca_colo)
        self.bind("<Button-1>", self.clic)

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

    def clic (self, event) :
        if self.fenetre.mode_aller_a :
            x = int((event.x - self.origine_x) // self.taille)
            y = int((event.y - self.origine_y) // self.taille)
            if 0 <= x <= self.grille.x-1 and 0 <= y <= self.grille.y-1 :
                self.fenetre.aller_a_end(x,y)
                self.refresh_lab()
                self.encadrement_coloré(x, y, self.color_balle)
                self.after("1000", self.refresh_lab)
            else :
                self.fenetre.mode_aller_a = False
                self.fenetre.barre_de_texte.set("Le mode 'Aller à' à été arrêté")
                self.after(2000, self.fenetre.refresh_barre_de_texte)
                
    def mouv_enca_colo (self, event) :
        if self.fenetre.mode_aller_a :
            x = int((event.x - self.origine_x) // self.taille)
            y = int((event.y - self.origine_y) // self.taille)
            if 0 <= x <= self.grille.x-1 and 0 <= y <= self.grille.y-1 :
                self.refresh_lab(refresh_barre_de_texte=False)
                self.encadrement_coloré(x, y, self.oposit_color_balle)
            else :
                self.refresh_lab(refresh_barre_de_texte=False)
    
    def encadrement_coloré (self, x, y, color) :
        self.barre_verticale (self.origine_x+x*self.taille, self.origine_y+y*self.taille, self.taille, color, 5)
        self.barre_horizontale (self.origine_x+x*self.taille, self.origine_y+y*self.taille, self.taille, color, 5)
        self.barre_verticale (self.origine_x+(x+1)*self.taille, self.origine_y+y*self.taille, self.taille, color, 5)
        self.barre_horizontale (self.origine_x+x*self.taille, self.origine_y+(y+1)*self.taille, self.taille, color, 5)


class Lab_grille_crea () :
    def __init__(self, master, fenetre, x=10, y=10) :
        self.master = master
        self.fenetre = fenetre
        self.Entree = "off"
        self.Sortie = "off"
        self.init_lab(x,y)
    
    def init_entitees (self, canvas, balle) :
        self.canvas = canvas
        self.balle = balle
    
    def init_lab (self, x,y, nom_lab:str = "<sans-nom>") :
        """
        Initialise le labirinthe à afficher
        """
        self.lab = self.grille_pleine (x,y)
        self.fenetre.lab_name = nom_lab
        self.x = x
        self.y = y
        
    def ouvrir_lab (self, nom_du_lab) :
        nom = "Labyrinthes_croquis/Croquis__"+nom_du_lab+".csv"
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
            self.fenetre.lab_name = nom_du_lab
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

    def save_as (self, nom_du_lab, croquis, lab, entrée, sortie) :
        if croquis:
            nom = "Labyrinthes_croquis/Croquis__"+nom_du_lab+".csv"
            if not(path.exists(nom)) :
                with open("Labyrinthes_croquis/#_Doc_index.csv", "a") as d :
                    d.write(nom_du_lab+"\n")
        else :
            nom = "Labyrinthes_creation/Labyrinthe__"+nom_du_lab+".csv"
            if not(path.exists(nom)) :
                with open("Labyrinthes_creation/#_Doc_index.csv", "a") as d :
                    d.write(nom_du_lab+"\n")
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
    def __init__(self, master, fenetre, canvas, grille, x=0, y=0) :
        self.master = master
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
            if self.fenetre.Modif :
                if self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[0] :
                    self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[1]
                elif self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[2] :
                    self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[3]
                else :
                    messagebox.askquestion ('Ajouter un mur','On ne peut pas créer un mur quand il existe déjà !',icon = 'warning')
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
                    self.fenetre.sortie_start ()
        elif self.grille.Sortie == "on" and creation_sortie :
            if self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[1] :
                self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[0]
            elif self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] == conbinaisons[3] :
                self.grille.lab[self.y + y_ciblage][self.x + x_ciblage] = conbinaisons[2]
            self.canvas.refresh_lab ()
            self.move(mouvement_x, mouvement_y)
            self.fenetre.sortie_end ()
        elif type(self.grille.Sortie) == tuple and (self.y + mouvement_y) == self.grille.Sortie[1] and (self.x + mouvement_x) == self.grille.Sortie[0] :
            self.move(mouvement_x, mouvement_y)

    def haut (self, event) :
        self.fleches("up")
    
    def bas (self, event) :
        self.fleches("down")
    
    def droite (self, event) :
        self.fleches("right")

    def gauche (self, event) :
        self.fleches("left")


class Boutons(tk.Frame) :
    def __init__(self, boss, master, fenetre, canvas, grille, balle) :
        self.master = master
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
        self.init_configuration_barre_laterale_droite()
        self.init_visible_debut ()
    
    def init_configuration_barre_laterale_droite (self) :
        # Définition de la configuration :
        self.def_bouton('Couleurs', self.canvas.couleurs, 0, commentaire="Change la couleur du canvas\n(raccourci : 'ctrl' + 'c')")
        self.fenetre.bind("<Control-KeyRelease-c>", self.canvas.couleurs)
        
        self.def_bouton('Aller à', self.master.aller_a_start, 4, commentaire="Permet de déplacer la balle facilement\n(raccourci : 'a')")
        self.fenetre.bind("<KeyRelease-a>", self.master.aller_a_start)
        
        self.frame_dep = tk.Frame(self)
        self.frame_dep.grid(row= 5)
        self.def_bouton('Créer', self.master.Change_type_deplacement, 1, nom_diminutif= 'type deplacement', boss= self.frame_dep,\
            commentaire="Permet de switcher entre deux modes de déplacement :\n\n- Mode Créer : casse les murs (raccourci : 'c')\n- Mode Déplacement : traverse les murs (raccourci : 'd')\n\nLe mode affiché sur le bouton est le mode actif.\n(raccouci pour switcher de mode : 'Espace')", commentaire_aligne="left")
        self.fenetre.bind("<KeyRelease-space>", self.master.Change_type_deplacement)
        self.fenetre.bind("<KeyRelease-d>", partial(self.master.def_type_deplacement, "Passe"))
        self.fenetre.bind("<KeyRelease-c>", partial(self.master.def_type_deplacement, "Casse"))
        
        self.frame_entree = tk.Frame(self)
        self.frame_entree.grid(row= 8)
        self.def_bouton('Créer une entrée', self.master.entree, 1, boss= self.frame_entree, commentaire="Permet de définir la case d'entrée\npour le parcours du labyrinthe une fois terminé\n(raccourci : 'e')")
        self.fenetre.bind("<KeyRelease-e>", self.master.entree)
        
        self.frame_sortie = tk.Frame(self)
        self.frame_sortie.grid(row= 9)
        self.def_bouton('Créer une sortie', self.master.sortie_start, 1, boss= self.frame_sortie, commentaire="Permet de définir la sortie en cassant un mur exterieur\npour le parcours du labyrinthe une fois terminé\n(raccourci : 's')")
        self.fenetre.bind("<KeyRelease-s>", self.master.sortie_start)
        
        self.def_bouton('Nouveau Labyrinthe', self.master.new_lab, 3, commentaire="Ouvre un formulaire pour ouvrir un croquis\nou commencer un nouveau labyrinthe\n(raccourci : 'n')")
        self.fenetre.bind("<KeyRelease-n>", self.master.new_lab)
        
        self.def_bouton('Sauvegarder', self.master.save, 2, commentaire="Permet de sauvegarder le labyrinthe en cours d'édition\nsoit sous forme de croquis, soit\nsous forme de labyrinthe terminé\n(raccourci : 'ctrl' + 's')")
        self.fenetre.bind("<Control-s>", self.master.save)
        
        self.def_bouton('Modifier lab', self.master.Modification, 7, commentaire="Permet de reconstruire un mur détruit\n(raccourci : 'm')")
        self.fenetre.bind("<KeyRelease-m>", self.master.Modification)

    def init_visible_debut (self) :
        self.is_visible_debut = []
        for bout in self.items :
            if self.items[bout][2] == "Visible" :
                self.is_visible_debut.append(bout)

    def def_bouton (self, nom_affiche:str, effet, position:int, boss=None, nom_diminutif:str = "", visibilite:str = "Visible", commentaire:str = "", commentaire_aligne:str = "center") :
        if not(nom_diminutif) :
            nom_diminutif = nom_affiche
        if boss is None :
            boss = self
        self.items[nom_diminutif] = [tk.Button (boss, text=nom_affiche, command=effet), position, visibilite]
        if commentaire :
            self.items[nom_diminutif].append(Commentaire(self.fenetre, self.items[nom_diminutif][0], commentaire, commentaire_aligne))
        if visibilite == "Visible" :
            self.items[nom_diminutif][0].grid(row= self.items[nom_diminutif][1])

    def redimentionner (self, text_size = None) :
        if text_size is None :
            text_size = int(5*log(self.fenetre.winfo_width()/100))
        for bout in self.items :
            self.items[bout][0].config(font=("Verdana", text_size))
            if len(self.items[bout]) > 3 :
                self.items[bout][3].commentaire_label.config(font=("Verdana", text_size-2))

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

class Commentaire (tk.Toplevel) :
    def __init__(self, fenetre, bouton, texte, aligne="center") -> None :
        tk.Toplevel.__init__(self, fenetre)
        self.fenetre = fenetre
        self.bouton = bouton
        self.withdraw()  # Masquer initialement le commentaire
        self.overrideredirect(True)  # Supprimer la bordure de la fenêtre
        if aligne == "center" :
            just = tk.CENTER
        elif aligne == "left" :
            just = tk.LEFT
        self.commentaire_label = tk.Label(self, text=texte, justify=just, bg="grey", fg="white")
        self.commentaire_label.grid()
        self.marge_bouton = 10  # En pixels
        self.bouton.bind("<Enter>", self.attendre_avant_afficher)

        self.bouton.bind("<Leave>", self.effacer_commentaire)

    def attendre_avant_afficher (self, event=None) :
        self.affichage_possible = True
        self.after(1000, self.afficher_commentaire)
    
    def afficher_commentaire(self) :
        if self.affichage_possible :
            x, y = self.bouton.winfo_rootx(), self.bouton.winfo_rooty()
            ordre = [self.def_pos_left, self.def_pos_right, self.def_pos_bottom, self.def_pos_top]
            ordre[0](x, y)
            self.verif_not_out_window()
            i = 1
            while (self.pos_x < x < self.pos_x + self.winfo_width() or self.pos_x < x + self.bouton.winfo_width() < self.pos_x + self.winfo_width()) and\
                    (self.pos_y < y < self.pos_y + self.winfo_height() or self.pos_y < y + self.bouton.winfo_height() < self.pos_y + self.winfo_height()) :
                ordre[i](x, y)
                self.verif_not_out_window()
                i += 1
            self.geometry(f"+{self.pos_x}+{self.pos_y}") 
            self.deiconify()  # Afficher le commentaire
    
    def def_pos_left (self, x, y) :
        self.pos_x = x - self.winfo_width() - self.marge_bouton
        self.pos_y = round(y + (self.bouton.winfo_height()/2) - self.winfo_height()/2)
    
    def def_pos_right (self, x, y) :
        self.pos_x = x + self.bouton.winfo_width() + self.marge_bouton
        self.pos_y = round(y + (self.bouton.winfo_height()/2) - self.winfo_height()/2)
    
    def def_pos_bottom (self, x, y) :
        self.pos_x = round(x + (self.bouton.winfo_width() / 2) - (self.winfo_width() / 2))
        self.pos_y = y + self.bouton.winfo_height() + self.marge_bouton
    
    def def_pos_top (self, x, y) :
        self.pos_x = round(x + (self.bouton.winfo_width() / 2) - (self.winfo_width() / 2))
        self.pos_y = y - self.winfo_height() - self.marge_bouton
    
    def verif_not_out_window(self) :
        marge = 10  # En pixels
        if self.pos_x - marge < self.fenetre.winfo_rootx() :
            self.pos_x = self.fenetre.winfo_rootx() + marge
        elif self.pos_x + self.winfo_width() + marge > self.fenetre.winfo_rootx() + self.fenetre.winfo_width() :
            self.pos_x = self.fenetre.winfo_rootx() + self.fenetre.winfo_width() - self.winfo_width() - marge
        if self.pos_y < self.fenetre.winfo_rooty() - marge :
            self.pos_y = self.fenetre.winfo_rooty() + marge
        elif self.pos_y + self.winfo_height() + marge > self.fenetre.winfo_rooty() + self.fenetre.winfo_height() :
            self.pos_y = self.fenetre.winfo_rooty() + self.fenetre.winfo_height() - self.winfo_height() - marge
    
    def effacer_commentaire(self, event):
        self.affichage_possible = False
        self.withdraw()  # Masquer le commentaire lorsque le curseur quitte le bouton




class Fen_chose_new_lab (tk.Toplevel) :
    def __init__ (self, boss, fenetre) :
        tk.Toplevel.__init__(self, boss)
        self.fenetre = fenetre
        self.title("Nouveau labyrinthe")
        self.nb_lignes = 2
        self.nb_colones = 2
        for i in range (self.nb_colones) :
            self.grid_columnconfigure(i, weight= 1) 
        for i in range (self.nb_lignes) :
            self.grid_rowconfigure(i, weight= 1)
        
        self.init_premier_choix()
        self.partie_premier_choix.grid(column=0, row=0, sticky=tk.NSEW)
        
        self.is_open_lab_croquis = False
        self.is_init_new_lab = False
        self.is_separation = False
        
        self.nb_colones_min = 3
        self.nb_colones_max = 50
        self.nb_lignes_min = 3
        self.nb_lignes_max = 35
        
        self.init_open_lab_croquis()
        self.init_init_new_lab()
        
        self.resizable(False, False)
        self.focus_set()
    
    def init_premier_choix (self) :
        self.partie_premier_choix = tk.Frame(self, border=10)
        text = tk.Text(self.partie_premier_choix, wrap= tk.WORD, width=25, height=3, padx=50, pady=20, font=("Helvetica", 15))
        text.insert(0.1, "Voulez-vous ouvrir un Croquis déjà existant ou voulez-vous créer un nouveau Labirinthe ?")
        text['state'] = 'disabled'
        text.grid(column=0, row=0, columnspan=2)
        
        bouton_2 = tk.Button (self.partie_premier_choix, text="Croquis", padx=20, pady=10, font=("Helvetica", 13), bg="green", fg="white", command=self.open_lab_croquis)
        bouton_2.grid(column=0, row=1)
        bouton_1 = tk.Button (self.partie_premier_choix, text="Nouveau", padx=20, pady=10, font=("Helvetica", 13), bg="blue", fg="white", command=self.init_new_lab)
        bouton_1.grid(column=1, row=1)
    
    def ajout_separation (self) :
        separation = tk.Text(self, bg="grey", pady=5, height=1, font=("Helvetica", 1))
        separation['state'] = 'disabled'
        separation.grid(column=0, row=1, sticky=tk.NSEW)
        self.is_separation = True
    
    def open_lab_croquis (self) :
        if self.is_init_new_lab :
            self.partie_init_new_lab.grid_forget()
            self.is_init_new_lab = False
        if not(self.is_open_lab_croquis) :
            if not(self.is_separation) :
                self.ajout_separation()
            self.partie_open_lab_croquis.grid(column=0, row=2, sticky=tk.NSEW)
            self.is_open_lab_croquis = True
    
    def init_open_lab_croquis (self) :
        self.partie_open_lab_croquis = tk.Frame(self, border=10)
        self.text_open_lab_croquis = tk.Text(self.partie_open_lab_croquis, wrap= tk.WORD, width=25, height=1, padx=50, pady=20, font=("Helvetica", 15))
        self.text_open_lab_croquis.insert(0.1, "Choisissez le Croquis à éditer :")
        self.text_open_lab_croquis['state'] = 'disabled'
        self.text_open_lab_croquis.grid(column=0, row=0, sticky=tk.NSEW)
        
        liste_nom = []
        with open("Labyrinthes_croquis/#_Doc_index.csv", "r") as f :
            for el in f.readlines() :
                liste_nom.append(el[:-1])
        self.liste_frame = tk.Frame(self.partie_open_lab_croquis, pady=30)
        liste = ttk.Combobox(self.liste_frame, values=liste_nom, state="readonly", justify="left", width=20, height=10, font=("Helvetica", 15))
        liste.current(0)
        liste.pack()
        self.liste_frame.grid(column=0, row=1)
        self.bouton_go_croquis = tk.Button (self.partie_open_lab_croquis, text="Ouvrir le Croquis", padx=20, pady=10, font=("Helvetica", 13),\
            command=partial(self.fenetre.open_lab_croquis, liste), bg="green", fg="white")
        self.bouton_go_croquis.grid(column=0, row=2)
    
    def init_new_lab (self) :
        if self.is_open_lab_croquis :
            self.partie_open_lab_croquis.grid_forget()
            self.is_open_lab_croquis = False
        if not(self.is_init_new_lab) :
            if not(self.is_separation) :
                self.ajout_separation()
            self.partie_init_new_lab.grid(column=0, row=2, sticky=tk.NSEW)
            self.is_init_new_lab = True
    
    def init_init_new_lab (self) :
        self.partie_init_new_lab = tk.Frame(self)
        text_init_new_lab = tk.Text(self.partie_init_new_lab, wrap= tk.WORD, width=25, height=3, padx=50, pady=20, font=("Helvetica", 15))
        text_init_new_lab.insert(0.1, "Entrez le nombre de colones et de lignes de votre nouveau labyrinthe :")
        text_init_new_lab['state'] = 'disabled'
        text_init_new_lab.grid(column=0, row=0, columnspan=2)
        
        largeur = tk.Frame(self.partie_init_new_lab, pady=20)
        largeur.grid(column=0, row=1)
        text_largeur = tk.Label(largeur, text="Colones :", font=("Helvetica", 13))
        text_largeur.grid(column=0, row=0)
        valeur_largeur = ttk.Spinbox(largeur, from_= self.nb_colones_min, to= self.nb_colones_max, wrap=True, font=("Helvetica", 15), width=4)
        valeur_largeur.set(10)
        valeur_largeur.grid(column=0, row=1)
        
        hauteur = tk.Frame(self.partie_init_new_lab, pady=20)
        hauteur.grid(column=1, row=1)
        text_hauteur = tk.Label(hauteur, text="Lignes :", font=("Helvetica", 13))
        text_hauteur.grid(column=0, row=0)
        valeur_hauteur = ttk.Spinbox(hauteur, from_= self.nb_lignes_min, to= self.nb_lignes_max, wrap=True, font=("Helvetica", 15), width=4)
        valeur_hauteur.set(10)
        valeur_hauteur.grid(column=0, row=1)
        
        nom_lab_frame = tk.Frame(self.partie_init_new_lab, pady=20)
        nom_lab_frame.grid(column=0, row=2, columnspan=2)
        texte_nom_lab = tk.Label(nom_lab_frame, text="Nom du Labyrinthe :", font=("Helvetica", 13))
        texte_nom_lab.grid(column=0, row=0)
        nom_lab = tk.Entry(nom_lab_frame, justify="center", font=("Helvetica", 15))
        nom_lab.insert(0,"<sans-nom>")
        nom_lab.grid(column=0, row=1)
        
        self.bouton_go_new_lab = tk.Button (self.partie_init_new_lab, text="Créer le Labyrinthe", padx=20, pady=10, font=("Helvetica", 13), bg="blue", fg="white",\
            command=partial(self.fenetre.init_new_lab, valeur_largeur, valeur_hauteur, self.nb_colones_min, self.nb_colones_max, self.nb_lignes_min, self.nb_lignes_max, nom_lab))
        self.bouton_go_new_lab.grid(column=0, row=3, columnspan=2)

class Fen_chose_save (tk.Toplevel) :
    def __init__ (self, boss, fenetre, grille) :
        tk.Toplevel.__init__(self, boss)
        self.fenetre = fenetre
        self.grille = grille
        self.title("Enregistrer Labyrinthe")
        self.nb_lignes = 3
        self.nb_colones = 2
        for i in range (self.nb_colones) :
            self.grid_columnconfigure(i, weight= 1) 
        for i in range (self.nb_lignes) :
            self.grid_rowconfigure(i, weight= 1)
        
        self.init_questionnaire()
        
        self.resizable(False, False)
        self.focus_set()
    
    def init_questionnaire (self) :
        nom_lab_frame = tk.Frame(self, pady=20)
        nom_lab_frame.grid(column=0, row=0, sticky=tk.NSEW)
        texte_nom_lab = tk.Label(nom_lab_frame, text="Nom du Labyrinthe :", font=("Helvetica", 13))
        texte_nom_lab.pack(side="top")
        self.nom_lab = tk.Entry(nom_lab_frame, justify="center", font=("Helvetica", 15))
        self.nom_lab.insert(0,self.fenetre.lab_name)
        self.nom_lab.pack(side="bottom")
        
        question = tk.Frame(self, border=10)
        question.grid(column=0, row=1, sticky=tk.NSEW)
        text = tk.Text(question, wrap= tk.WORD, width=33, height=8, padx=50, pady=20, font=("Helvetica", 15))
        text.insert(0.1, "Comment voulez-vous sauvegarder votre labirinthe ?\n\n- Comme un Croquis : INCOMPLET donc possibilité de le modifier plus tard\n\n- Comme un Labyrinthe : TERMINÉ donc possibilité de l'ouvrir avec le jeu Laby")
        text['state'] = 'disabled'
        text.grid(column=0, row=0, columnspan=2, sticky=tk.NSEW)
        text.tag_add("croquis", "3.11", "3.18")
        text.tag_add("labyrinthe", "5.11", "5.21")
        text.tag_config("croquis", foreground="green")
        text.tag_config("labyrinthe", foreground="blue")
        
        bouton_2 = tk.Button (question, text="Croquis", padx=20, pady=10, font=("Helvetica", 13), bg="green", fg= "white", \
            command=partial(self.save, True))
        bouton_2.grid(column=0, row=1)
        bouton_1 = tk.Button (question, text="Labyrinthe", padx=20, pady=10, font=("Helvetica", 13), bg="blue", fg= "white", \
            command=partial(self.save, False))
        bouton_1.grid(column=1, row=1)
    
    def save (self, is_croquis:bool) :
        name_lab = self.nom_lab.get()
        if is_croquis :
            type_ = "Croquis"
            path = "Labyrinthes_croquis/#_Doc_index.csv"
        else :
            type_ = "Labyrinthe"
            path = "Labyrinthes_creation/#_Doc_index.csv"
        if name_lab == "<sans-nom>" :
            messagebox.showinfo ('Enregistrement Labirinthe',"Il faut donner un nom au "+type_+" !", icon="warning", parent=self)
        else :
            if " " in name_lab :
                name_lab = "_".join(name_lab.split(" "))
            liste_nom = []
            with open(path, "r") as f :
                for el in f.readlines() :
                    liste_nom.append(el[:-1])
            if name_lab in liste_nom :
                reponse = messagebox.askquestion ('Enregistrement Labirinthe',"Le nom '"+name_lab+"' existe déjà !\nVoulez-vous le remplacer ?", icon="warning", parent=self)
                if reponse == "yes" :
                    self.grille.save_as (name_lab, is_croquis, self.grille.lab, self.grille.Entree, self.grille.Sortie)
                    self.destroy()
                    messagebox.showinfo ('Enregistrement Labirinthe',"Le "+type_+" "+name_lab+" à bien été enregistré !", icon="info")
            else :
                self.grille.save_as (name_lab, is_croquis, self.grille.lab, self.grille.Entree, self.grille.Sortie)
                self.destroy()
                messagebox.showinfo ('Enregistrement Labirinthe',"Le "+type_+" "+name_lab+" à bien été enregistré !", icon="info")




if __name__ == "__main__" :
    lab_builder = Entite_superieure()
    lab_builder.lancement()
