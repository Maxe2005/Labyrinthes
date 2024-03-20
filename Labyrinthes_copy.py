# Created on 10/02/23
# Last modified on 11/03/24
# Author : Maxence CHOISEL

import Creer_labyrinthes as Laby_builder
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.simpledialog import askinteger, askstring
from math import log
from functools import partial
from PIL import Image,ImageTk
from random import randint
from csv import writer



class Entite_superieure () :
    def __init__(self, lab_builtder=None) -> None:
        """Constructeur, initialise les instances"""
        if lab_builtder is not None :
            self.Lab_builtder = lab_builtder
        self.init_variables_globales()
        
        self.fenetre = Laby_fen()
        self.grille = Laby_grille(self)
        self.canvas = Laby_canvas(self)
        self.balle = Laby_balle(self, self.fenetre)
        self.niveau = Niveaux()
        self.difficultee = Difficultee()
        
        self.fenetre.init_entitees(self, self.grille, self.canvas, self.balle)
        self.grille.init_entitees(self.fenetre, self.canvas, self.balle)
        self.canvas.init_entitees(self.fenetre, self.grille, self.balle)
        self.balle.init_entitees(self.grille, self.canvas)
        self.niveau.init_entitees(self, self.fenetre, self.grille, self.canvas, self.balle)
        self.difficultee.init_entitees(self, self.fenetre, self.grille, self.canvas, self.balle, self.niveau)
        
        self.nombre_de_labs = len(self.grille.docu_lab) # Fin de init_variables_globales (le nombre de Labyrinthes "classiques" en tout)
    
    def lancement (self) :
        """Permet de lancer la fenêtre du jeu"""
        self.fenetre.init_barres_boutons_et_text()
        self.canvas.nouvelle_partie ()
        for i in range (3) :
            self.fenetre.after(500+(i*100), self.fenetre.redimentionner)
        self.fenetre.focus()
        for com in self.commentaires :
            self.fenetre.after(500, com.test)
        self.fenetre.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.fenetre.mainloop()
    
    def lancement_builder_labs (self) :
        if __name__ == "__main__" :
            self.Lab_builtder = Laby_builder.Entite_superieure_crea(self)
            self.Lab_builtder.lancement()
        else :
            self.Lab_builtder.fenetre.lift()
            self.Lab_builtder.fenetre.focus()
    
    def init_variables_globales (self) :
        """Permet de donner des valeurs arbitraires aux paramètres globaux (params par défaut)"""
        self.ouvrir_param_defaut()
        self.nb_lab = 1 # le premier Labyrinthe à afficher
        self.type_lab = "classique"
        self.commentaires = []
        self.type_deplacement = self.parametres["type deplacement initial"]
    
    def ouvrir_param_defaut (self) :
        """Télécharge les paramètres par défauts """
        self.parametres = {}
        with open("Parametres_defaut.csv") as f :
            for ligne in f.readlines()[1:] :
                l = ligne.split("\n")[0].split(",")
                self.parametres[l[0]] = l[1]
    
    def save_param_defaut (self) :
        with open("Parametres_defaut.csv", "w") as f :
            f.write("#Nom du parametre, valeur du parametre\n")
            for param in self.parametres :
                f.write(param+","+str(self.parametres[param])+"\n")
    
    def on_closing (self) :
        self.save_param_defaut()
        self.fenetre.destroy()
    
    def aller_a (self, event=None) :
        "Permet d´aller directement au Labyrinthe de son choix"
        n = askinteger("Aller directement", f"Numéro du Labyrinthe (max: {self.nombre_de_labs})", parent = self.fenetre, minvalue = 1, maxvalue = self.nombre_de_labs)
        if n is not(None):
            self.nb_lab = int(n)
            self.canvas.nouvelle_partie()
    
    def change_type_deplacement (self, event=None) :
        """Permet de switcher entre les deux modes de déplacement de la balle : sec ou lisse"""
        if self.type_deplacement == "Sec" :
            self.def_type_deplacement("Lisse")
        else :
            self.def_type_deplacement("Sec")
    
    def def_type_deplacement (self, dep, event=None) :
        """Défini le mode de déplacement de la balle (soit sec, soit lisse) et modifie l'écriture sur le bouton associé"""
        if dep == "Sec" :
            self.type_deplacement = "Sec"
            self.fenetre.boutons_lateraux_droits.renommer("type deplacement", "Déplacement\nSec")
        elif dep == "Lisse" :
            self.type_deplacement = "Lisse"
            self.fenetre.boutons_lateraux_droits.renommer("type deplacement", "Déplacement\nLisse")
        else :
            print("ERREUR")
    
    def recomencer_lab (self, event=None) :
        MsgBox = messagebox.askquestion ('Recommencer','Voulez-vous vraiment recommencer ce Labyrinthe depuis le début?',icon = 'warning')
        if MsgBox == 'yes':
            self.canvas.nouvelle_partie()
    
    def suivant_lab (self, event=None) :
        MsgBox = messagebox.askquestion ('Labyrinthe suivant','Voulez-vous vraiment lancer le Labyrinthe suivant (plus difficile)?')
        if MsgBox == 'yes':
            if self.nb_lab != self.nombre_de_labs :
                self.nb_lab += 1
                self.canvas.nouvelle_partie()
            else :
                messagebox.showinfo ('Labyrinthe suivant','Vous êtes déjà sur le dernier Labyrinthe',icon = 'error')
    
    def precedent_lab (self, event=None) :
        MsgBox = messagebox.askquestion ('Labyrinthe précédent','Voulez-vous vraiment revenir au Labyrinthe précédent?')
        if MsgBox == 'yes':
            if self.nb_lab != 1 :
                self.nb_lab -= 1
                self.canvas.nouvelle_partie()
            else :
                messagebox.showinfo ('Labyrinthe précédent','Vous êtes déjà sur le 1er Labyrinthe',icon = 'error')
    
    def win (self) :
        if self.canvas.balle.x == self.grille.sortie_lab[0] and self.canvas.balle.y == self.grille.sortie_lab[1] :
            messagebox.showinfo ("Félicitations !","Vous avez GAGNÉ !")
            Message_fin_lab (self)
    
    def type_labyrinthe (self, event=None) :
        if self.type_lab == "classique" :
            self.type_lab = "aleatoire"
            self.fenetre.boutons_lateraux_droits.renommer("type lab", "Labyrinthe\nClassique")
            self.fenetre.boutons_lateraux_droits.afficher("new lab alea")
        elif self.type_lab == "aleatoire" :
            self.type_lab = "classique"
            self.fenetre.boutons_lateraux_droits.renommer("type lab", "Labyrinthe\nAléatoire")
            self.fenetre.boutons_lateraux_droits.cacher("new lab alea")
        self.canvas.nouvelle_partie()
    
    def infos_generales (self) :
        infos = Fen_infos_generales(self.fenetre, self)
        infos.mainloop()
    
    def reglages (self) :
        reglages = Reglages(self.fenetre)
        reglages.init_entitees (self, self.fenetre, self.grille, self.canvas, self.balle)
        reglages.lancement()
        reglages.mainloop()
    
    def mode_HARD (self, event=None) :
        pass


class Laby_fen (tk.Tk) :
    def __init__(self, x=1000 ,y=800):
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
        self.refresh_barre_principale()
    
    def init_configuration_barre_laterale_droite (self) :
        self.barre_laterale_droite = tk.Frame(self)
        self.barre_laterale_droite.grid(column=1, row=0, rowspan=2, sticky=tk.NSEW)
        self.barre_laterale_droite.grid_columnconfigure(0, weight= 1)
        self.barre_laterale_droite.grid_rowconfigure(0, weight= 1)
        self.barre_laterale_droite.grid_rowconfigure(1, weight= 7)
        self.init_logo(self.barre_laterale_droite)
        self.boutons_lateraux_droits = Laby_builder.Boutons(self.barre_laterale_droite, self.big_boss, self, class_comentaire=Laby_builder.Commentaire)
        self.init_boutons_barre_laterale_droite()
        self.boutons_lateraux_droits.grid(column=0, row=1, sticky=tk.NSEW)
    
    def init_boutons_barre_laterale_droite (self) :
        """
        Définition de la configuration des boutons de la barre latérale droite
        """
        self.boutons_lateraux_droits.init_grid(nb_lignes=10)
        
        self.boutons_lateraux_droits.def_bouton('Réglages', self.big_boss.reglages, 0, commentaire="Accès au réglages\n(raccourci : 'r')")
        self.bind("<KeyRelease-r>", self.big_boss.reglages)
        
        self.boutons_lateraux_droits.def_bouton('Couleurs', self.canvas.couleurs, 1, commentaire="Change la couleur du canvas\n(raccourci : 'ctrl' + 'c')")
        self.bind("<Control-KeyRelease-c>", self.canvas.couleurs)
        
        self.boutons_lateraux_droits.def_bouton('Aller à', self.big_boss.aller_a, 2, commentaire="Permet de se rendre rapidement\nsur le labyrinthe souhaité\n(raccourci : 'a')")
        self.bind("<KeyRelease-a>", self.big_boss.aller_a)
        
        self.boutons_lateraux_droits.def_bouton('Labyrinthe\nAléatoire', self.big_boss.type_labyrinthe, 3, nom_diminutif="type lab", commentaire="Permet de switcher entre les Labyrinthes\nClassiques et les Labyrinthes Aléatoires.\nLe type affiché est le type non-actif.\n(raccourci : 't')")
        self.bind("<KeyRelease-t>", self.big_boss.type_labyrinthe)
        
        self.boutons_lateraux_droits.def_bouton('New Lab\nAléatoire', self.canvas.nouvelle_partie, 4,  nom_diminutif="new lab alea", visibilite="Cache", commentaire="Génère un nouveau Labyrinthe aléatoire")
        
        self.boutons_lateraux_droits.def_bouton('Déplacement\nSec', self.big_boss.change_type_deplacement, 6, nom_diminutif= 'type deplacement', commentaire="Permet de switcher entre deux modes de déplacement :\n\n- Mode Lisse : permet de programmer à l'avance\n\tla prochaine direction (raccourci : 'l')\n- Mode Sec : déplacement case par case (raccourci : 's')\n\nLe mode affiché sur le bouton est le mode actif.", commentaire_aligne="left")
        self.bind("<KeyRelease-s>", partial(self.big_boss.def_type_deplacement, "Sec"))
        self.bind("<KeyRelease-l>", partial(self.big_boss.def_type_deplacement, "Lisse"))
        
        self.boutons_lateraux_droits.def_bouton('Niveau Max', self.big_boss.niveau.niveau_max, 8, commentaire="Permet d'activer (et désactiver) le Niveau Maximum :\nDans ce niveau les murs sont invisibles\n(raccourci : 'm')")
        self.bind("<KeyRelease-m>", self.big_boss.niveau.niveau_max)
        
        self.boutons_lateraux_droits.def_bouton('Mode HARD', self.big_boss.mode_HARD, 9, commentaire="Permet d'activer (et désactiver) le mode HARD :\nDans ce mode la balle est invisible\n(raccourci : 'h')")
        self.bind("<KeyRelease-h>", self.big_boss.mode_HARD)
    
    def init_logo (self, boss, params=[0,0]) :
        #self.logo = tk.Label(self.big_boss.barre_laterale_droite)
        self.logo = tk.Button(boss, command=self.big_boss.infos_generales)
        self.logo.grid(column=params[0], row=params[1])
        self.open_image()
    
    def open_image (self) :
        self.image = Image.open("Idées LOGO/logo 2.jpg")
        xx, yy = self.image.size
        ratio = xx / yy
        x_max = self.barre_laterale_droite.winfo_width()
        x = round(70/100 * x_max)
        y = round(x / ratio)
        self.image = self.image.resize((x,y))
        self.image_photo = ImageTk.PhotoImage(self.image)
        self.logo["image"] = self.image_photo
    
    def init_configuration_barre_top (self) :
        self.barre_top = tk.Frame(self)
        self.barre_top.grid(column=0, row=0, sticky=tk.NSEW)
        self.barre_top.grid_rowconfigure(0, weight= 1)
        self.barre_top.grid_columnconfigure(0, weight= 1)
        self.barre_top.grid_columnconfigure(1, weight= 1)
        self.barre_top.grid_columnconfigure(2, weight= 1)
        self.boutons_top_left = Laby_builder.Boutons(self.barre_top, self.big_boss, self, class_comentaire=Laby_builder.Commentaire)
        self.init_boutons_barre_top_left()
        self.boutons_top_left.grid(column=0, row=0, sticky=tk.NSEW)
        
        self.texte_barre_principale = tk.StringVar()
        self.texte_barre_principale.set("Début")
        self.barre_principale = tk.Label(self.barre_top, textvariable= self.texte_barre_principale)
        self.barre_principale.grid(column= 1, row= 0, sticky=tk.NSEW)
        
        self.boutons_top_right = Laby_builder.Boutons(self.barre_top, self.big_boss, self, class_comentaire=Laby_builder.Commentaire)
        self.init_boutons_barre_top_right()
        self.boutons_top_right.grid(column=2, row=0)#, sticky=tk.NSEW)
        
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
        self.boutons_top_left.def_bouton('<-', self.big_boss.niveau.moins, 0, boss=self.niveau_frame, sticky="e", nom_diminutif= "niveau moins", commentaire="Passer au niveau inférieur")
        self.boutons_top_left.def_bouton('Niveau', self.big_boss.niveau.fenetre_presentation, 1, boss=self.niveau_frame, sticky="ew", commentaire="Présetation des niveaux")
        self.boutons_top_left.def_bouton('->', self.big_boss.niveau.plus, 2, boss=self.niveau_frame, sticky="w", nom_diminutif= "niveau plus", commentaire="Passer au niveau supérieur")
        
        self.difficultee_frame = tk.Frame(self.boutons_top_left)
        if self.boutons_top_left.winfo_width() < min_y :
            self.difficultee_frame.grid(column=0, row=1)
        else :
            self.difficultee_frame.grid(column=1, row=0)
        self.boutons_top_left.def_bouton('<-', self.big_boss.difficultee.moins, 0, boss=self.difficultee_frame, sticky="e", nom_diminutif= "difficultée moins", commentaire="Passer à la difficultée inférieure")
        self.boutons_top_left.def_bouton('Difficultée', self.big_boss.difficultee.fenetre_presentation, 1, boss=self.difficultee_frame, sticky="ew", commentaire="Présetation des difficultées")
        self.boutons_top_left.def_bouton('->', self.big_boss.difficultee.plus, 2, boss=self.difficultee_frame, sticky="w", nom_diminutif= "difficultée plus", commentaire="Passer à la difficultée supérieure")
    
    def init_boutons_barre_top_right (self) :
        """
        Définition de la configuration des boutons à droite de la barre haute
        """
        #print("right :",self.boutons_top_right.winfo_width())
        if False:#self.boutons_top_right.winfo_width() < 300 :
            self.boutons_top_right.init_grid(nb_lignes=3)
        else :
            self.boutons_top_right.init_grid(nb_colones=3)
        
        self.boutons_top_right.def_bouton('<- Précédent', self.big_boss.precedent_lab, 0, sticky="e", commentaire="Accès au labyrinthe précédent\n(raccourci : 'p')")
        self.bind("<KeyRelease-p>", self.big_boss.precedent_lab)
        
        self.boutons_top_right.def_bouton('Recomencer', self.big_boss.recomencer_lab, 1, sticky="ew", commentaire="Permet de recomencer le labyrinthe\nen retournant au début\n(raccourci : 'r')")
        self.bind("<KeyRelease-r>", self.big_boss.recomencer_lab)
        
        self.boutons_top_right.def_bouton('Suivant ->', self.big_boss.suivant_lab, 2, sticky="w", commentaire="Accès au labyrinthe suivant")#\n(raccourci : 's')")
        #self.bind("<KeyRelease-s>", self.big_boss.suivant_lab)
    
    def redimentionner (self,event=None) :
        self.x = self.winfo_width()
        self.y = self.winfo_height()
        self.canvas.redimentionner()
        self.open_image()
        text_size = int(log(self.winfo_width()/100))
        self.barre_principale.config(font=("Verdana", text_size * 5))
        #self.chrono.label.config(font=("Arial", text_size/3))
        self.boutons_lateraux_droits.redimentionner(text_size = int(text_size * 5.5))
        self.boutons_top_right.redimentionner(text_size = int(text_size * 5))
        self.boutons_top_left.redimentionner(text_size = int(text_size * 5))
        #self.init_boutons_barre_top_right()
        #self.init_boutons_barre_top_left ()
    
    def refresh_barre_principale (self) :
        """Affiche la barre principale avec les dernières informations à jour et sous le bon format"""
        if self.big_boss.type_lab == "classique" :
            lab = "n° "+str(self.big_boss.nb_lab)
        elif self.big_boss.type_lab == "aleatoire" :
            lab = "aléatoire"
        if self.big_boss.niveau.Niveau_max :
            niveau = difficultee = "max"
        else :
            niveau = self.big_boss.niveau.numero
            if self.big_boss.niveau.numero == 1 :
                difficultee = "-"
            else :
                difficultee = self.big_boss.difficultee.numero
        espaces = round(self.barre_principale.winfo_width()/30 - 10)
        self.texte_barre_principale.set(f"Labyrinthe {lab:<10}"+" "*espaces+f"Niveau : {niveau:<3}"+" "*espaces+f"Difficultée : {difficultee:<3}")
        #+" "*round(espaces/2)+str(self.canvas.balle.x)+" "+str(self.canvas.balle.y)


class Laby_canvas (tk.Canvas) :
    "Canvas d´affichage du labyrinthe"
    def __init__(self, big_boss, param=[0,1]) :
        tk.Canvas.__init__(self)
        self. big_boss = big_boss
        self.couleurs(change=False, initial_value=self.big_boss.parametres["initial color mode"])
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
        self.fenetre.refresh_barre_principale ()
        self.balle.init_var ()
    
    def taille_auto (self) :
        "Calcule la taille en pixel d'un coté des cases carré à partir de la hauteur h et le la longeur l de la grille de définition"
        if self.winfo_height() / self.grille.y < self.winfo_width() / self.grille.x :
            self.taille = self.winfo_height() / (self.grille.y+1)
        else :
            self.taille = self.winfo_width() / (self.grille.x+1)
    
    def origines (self) :
        "Calcule et renvoi sous forme de tuple les origines en x et y (en haut à gauche du canvas)"
        self.origine_x = (self.winfo_width() - (self.taille * (self.grille.x-1))) / 2
        self.origine_y = (self.winfo_height() - (self.taille * (self.grille.y-1))) / 2
        assert self.origine_x > 0 and self.origine_y > 0
    
    def trace_grille (self) :
        "Trace avec Tkinter un quadrillage de la grille g"
        if self.big_boss.niveau.numero == 4 :
            for el in self.grille.Murs_lab :
                if el[2] == "1" :
                    self.barre_horizontale (self.origine_x + el[0]*self.taille, self.origine_y + el[1]*self.taille, self.taille, self.color_grille)
                if el[2] == "2" :
                    self.barre_verticale (self.origine_x + el[0]*self.taille, self.origine_y + el[1]*self.taille, self.taille, self.color_grille)
        elif self.big_boss.niveau.Niveau_max == False :
            for el in self.grille.Partitions_lab :
                for y in range (el[0][1],el[1][1]) :
                    for x in range (el[0][0],el[1][0]) :
                        if self.grille.lab[y][x] == "1" or self.grille.lab[y][x] == "3" :
                            self.barre_horizontale (self.origine_x + x*self.taille, self.origine_y + y*self.taille, self.taille, self.color_grille)
                        if self.grille.lab[y][x] == "2" or self.grille.lab[y][x] == "3" :
                            self.barre_verticale (self.origine_x + x*self.taille, self.origine_y + y*self.taille, self.taille, self.color_grille)
        if self.big_boss.niveau.numero > 1 and self.big_boss.niveau.Niveau_max == False :
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
        self.fenetre.refresh_barre_principale ()
    
    def couleurs (self, change=True, initial_value=False, event=None) :
        if change :
            if self.couleur_mode == "white" :
                self.couleur_mode = "black"
            else :
                self.couleur_mode = "white"
        elif initial_value :
            self.couleur_mode = initial_value
        if self.couleur_mode == "white" :
            self.color_canvas = "white"
            self["bg"] = self.color_canvas
            self.color_grille = "black"
            self.color_balle = "blue"
            self.oposit_color_balle = "red"
            self.color_balle_out = "black"
        elif self.couleur_mode == "black" :
            self.color_canvas = "black"
            self["bg"] = self.color_canvas
            self.color_grille = "white"
            self.color_balle = "red"
            self.oposit_color_balle = "blue"
            self.color_balle_out = "white"
        if change :
            self.refresh_lab()
    
    def redimentionner (self) :
        self.taille_auto ()
        self.origines ()
        self.refresh_lab ()


class Laby_grille () :
    "Effectue diverses opérations sur la grille contenant le labyrinthe"
    def __init__(self, big_boss, lab=[[]]) :
        self. big_boss = big_boss
        self.docu_lab = self.ouvrir_doc("Labyrinthes_classiques/#_Doc_index.csv")
        self.lab = lab
        self.x = len(lab[0])
        self.y = len(lab)
        self.Partitions_lab = []
        self.init_variables()
    
    def ouvrir_doc (self, nom) :
        fichier = open (nom, "r")
        table = []
        for ligne in fichier :
            ligne = ligne.rstrip()
            if "," in ligne :
                ligne = ligne.split(",")
            table.append(ligne)
        fichier.close()
        return table
    
    def init_entitees (self, fenetre, canvas, balle) :
        self. fenetre = fenetre
        self. canvas = canvas
        self. balle = balle
    
    def init_variables (self) :
        self.lab_alea_x = int(self.big_boss.parametres["lab alea x"])
        self.lab_alea_y = int(self.big_boss.parametres["lab alea y"])
        self.lab_alea_entrée_lab = [int(self.big_boss.parametres["lab alea entree x"]), int(self.big_boss.parametres["lab alea entree y"])]
        self.nb_colones_min = int(self.big_boss.parametres["nb colones min"])
        self.nb_colones_max = int(self.big_boss.parametres["nb colones max"])
        self.nb_lignes_min = int(self.big_boss.parametres["nb lignes min"])
        self.nb_lignes_max = int(self.big_boss.parametres["nb lignes max"])
    
    def init_lab (self) :
        "Initialise le Labyrinthe à afficher"
        if self.big_boss.type_lab == "classique" :
            self.lab = self.ouvrir_lab (self.big_boss.nb_lab)
        elif self.big_boss.type_lab == "aleatoire" :
            self.entrée_lab = self.lab_alea_entrée_lab
            self.lab = self.generateur_lab(self.lab_alea_x, self.lab_alea_y)
        self.x = len(self.lab[0])
        self.y = len(self.lab)
        self.canvas.balle.def_position(self.entrée_lab[0],self.entrée_lab[1])
        if self.big_boss.niveau.numero == 1 :
            self.init_Partitions_lab()
        elif self.big_boss.niveau.numero == 2 or self.big_boss.niveau.numero == 3 :
            self.init_taille_partition_par_difficultées ()
        elif self.big_boss.niveau.numero == 4 :
            self.Murs_lab = []
            self.decompte_nb_murs_dans_lab ()
    
    def init_Partitions_lab (self) :
        self.Partitions_lab = [((0,0),(self.x, self.y))]
    
    def grille_pleine (self,x,y) :
        "Crée une grille sans trous"
        assert type(x) and type(y) == int
        assert x > 0 and y > 0
        g = []
        for j in range (y) :
            a = []
            for i in range (x) :
                a.append("3")
            a.append("2")
            g.append(a)
        a = []
        for i in range (x) :
            a.append("1")
        a.append("0")
        g.append(a)
        return g
    
    def inser_grille (self) :
        "Permet d´entrer une grille de labirinte (codé en 0,1,2,3) depuis la console"
        g = []
        count = 1
        while count != "fin" :
            a = input("Inserez la ligne n°"+str(count)+" de votre Labyrinthe ")
            if a != "fin" :
                if count == 1 :
                    t = len(a)
                if len(a) == t :
                    g.append(a)
                    count += 1
                else :
                    print ("Il y a une erreur dans la longueur de votre ligne, elle peut seulement valoire 4 ou 9 !")
            else :
                count = "fin"
        return g
    
    def ouvrir_lab (self,numéro_du_lab) :
        nom = "Labyrinthes_classiques/"+self.docu_lab[numéro_du_lab-1]
        fichier = open (nom, "r")
        table = []
        count = 1
        for ligne in fichier :
            ligne = ligne.rstrip()
            tab = ligne.split(",")
            if count != 3 :
                for i in range (len(tab)) :
                    tab[i] = int(tab[i])
                if count == 1 :
                    self.entrée_lab = tab
                elif count == 2 :
                    self.sortie_lab = tab
                count += 1
            else :
                table.append(tab)
        fichier.close()
        return table
    
    def decompte_nb_murs_dans_lab (self) :
        self.nb_murs_dans_lab = 0
        for ligne in self.lab :
            for el in ligne :
                if el == "1" or el == "2" :
                    self.nb_murs_dans_lab += 1
                elif el == "3" :
                    self.nb_murs_dans_lab += 2
        self.nb_murs_dans_lab -= self.x*2 + (self.y-2)*2 + 1 # On ne compte pas les bordures car déjà dessinées
    
    def decoupage_du_lab (self,x,y) :
        """
        :param x: (int) largeur en nombre de cases d´une partition du lab
        :param y: (int) hauteur en nombre de cases d´une partition du lab
        """
        lab_decoupe = []
        if self.y % y != 0 and self.y % y < y/2 :
            y_modif = 1
        else :
            y_modif = 0
        o = -1
        for o in range ((self.y//y)-y_modif) :
            ligne_lab_decoupe = []
            if self.x % x != 0 and self.x % x < x/2 :
                x_modif = 1
            else :
                x_modif = 0
            a = -1
            for a in range ((self.x//x)-x_modif) :
                b = ((a*x,o*y),((a+1)*x,(o+1)*y))
                ligne_lab_decoupe.append(b)
            if self.x % x != 0 :
                b = (((a+1)*x,o*y),(((a+1+x_modif)*x)+(self.x % x),(o+1)*y))
                ligne_lab_decoupe.append(b)
            lab_decoupe.append(ligne_lab_decoupe)
        if self.y % y != 0 :
            ligne_lab_decoupe = []
            if self.x % x != 0 and self.x % x < x/2 :
                x_modif = 1
            else :
                x_modif = 0
            a = -1
            for a in range ((self.x//x)-x_modif) :
                b = ((a*x,(o+1)*y),((a+1)*x,((o+1+self.y)*y)+(self.y % y)))
                ligne_lab_decoupe.append(b)
            if self.x % x != 0 :
                b = (((a+1)*x,(o+1)*y),(((a+1+self.x)*x)+(self.x % x),((o+1+self.y)*y)+(self.y % y)))
                ligne_lab_decoupe.append(b)
            lab_decoupe.append(ligne_lab_decoupe)
        return lab_decoupe
    
    def creation_partitions_lab (self) :
        global position_joueur_back_lab_x, position_joueur_back_lab_y, back_lab_partition_grille, back_lab_partition_grille_position_joueur
        x = self.taille_partition_x
        y = self.taille_partition_y
        self.back_lab_partition_grille = self.decoupage_du_lab(x,y)
        self.back_lab_partition_grille_position_joueur = []
        if self.y % y >= y/2 :
            nb_partitions_y = (self.y // y) + 1
        else :
            nb_partitions_y = self.y // y
        if self.x % x >= x/2 :
            nb_partitions_x = (self.x // x) + 1
        else :
            nb_partitions_x = self.x // x
        for o in range (nb_partitions_y) :
            b = []
            for a in range (nb_partitions_x) :
                b.append(False)
            self.back_lab_partition_grille_position_joueur.append(b)
        assert len(self.back_lab_partition_grille) == len(self.back_lab_partition_grille_position_joueur)
        assert len(self.back_lab_partition_grille[0]) == len(self.back_lab_partition_grille_position_joueur[0])
        self.position_joueur_back_lab_x = -1
        self.position_joueur_back_lab_y = -1
        self.Position_joueur_sur_back_lab_partition ()
        return
    
    def init_taille_partition_par_difficultées (self) :
        if self.x > self.y :
            grand_cote = self.x
            petit_cote = self.y
        else :
            grand_cote = self.y
            petit_cote = self.x
        taille_min = 2
        self.Partitions_lab = []
        if self.big_boss.difficultee.numero == 1 :
            taille_x = taille_y = petit_cote//2
        elif self.big_boss.difficultee.numero == 2 :
            taille_x = taille_y = grand_cote//4
        elif self.big_boss.difficultee.numero == 3 :
            taille_x = taille_y = grand_cote//8
        if taille_x <= taille_min :
            self.taille_partition_x = taille_min
        else :
            self.taille_partition_x = taille_x
        if taille_y <= taille_min :
            self.taille_partition_y = taille_min
        else :
            self.taille_partition_y = taille_y
        self.creation_partitions_lab ()
    
    def Position_joueur_sur_back_lab_partition (self) :
        x = self.canvas.balle.x // self.taille_partition_x
        y = self.canvas.balle.y // self.taille_partition_y
        if self.x % self.taille_partition_x < self.taille_partition_x/2 and x >= self.x // self.taille_partition_x :
            x -= 1
        if self.y % self.taille_partition_y < self.taille_partition_y/2 and y >= self.y // self.taille_partition_y :
            y -= 1
        if x != self.position_joueur_back_lab_x or y != self.position_joueur_back_lab_y :
            if self.big_boss.niveau.numero == 2 and self.back_lab_partition_grille_position_joueur[y][x] == False :
                count = 1
                for el in self.back_lab_partition_grille_position_joueur :
                    for i in el :
                        if i :
                            count += 1
                self.Partitions_lab = [self.back_lab_partition_grille[y][x]]
                lab_xx = len(self.back_lab_partition_grille_position_joueur[0])
                lab_yy = len(self.back_lab_partition_grille_position_joueur)
                if count > round(lab_xx * lab_yy / (self.big_boss.difficultee.numero + 1)) :
                    self.back_lab_partition_grille_position_joueur = []
                    for i in range (lab_yy) :
                        a = []
                        for e in range (lab_xx) :
                            a.append(False)
                        self.back_lab_partition_grille_position_joueur.append(a)
                    self.canvas.refresh_lab ()
                self.back_lab_partition_grille_position_joueur[y][x] = True
                self.canvas.trace_grille()
            elif self.big_boss.niveau.numero == 3 :
                self.back_lab_partition_grille_position_joueur[self.position_joueur_back_lab_y][self.position_joueur_back_lab_x] = False
                self.back_lab_partition_grille_position_joueur[y][x] = True
                self.Partitions_lab = [self.back_lab_partition_grille[y][x]]
                self.canvas.refresh_lab ()
        self.position_joueur_back_lab_x = x
        self.position_joueur_back_lab_y = y
        return
    
    def generateur_lab (self,x,y) :
        "Génère et initialise un Labyrinthe, défini la sortie_lab comme la plus éloignée de l´entrée"
        #sauvegarde = []
        #save =
        #x = 40
        #y = 25
        #self.entrée_lab = [0,0]
        lab = self.grille_pleine (x,y)
        cases_visitées = [(self.entrée_lab[0],self.entrée_lab[1])]
        cases_contact_ext = {}
        cases_contact_ext_list = []
        pos_x = self.entrée_lab[0]
        pos_y = self.entrée_lab[1]
        potentiel_sorties = []
        a = []
        if self.entrée_lab[0] != 0 :
            a.append("O")
        if self.entrée_lab[1] != 0 :
            a.append("N")
        if self.entrée_lab[0] != x :
            a.append("E")
        if self.entrée_lab[1] != y :
            a.append("S")
        cases_contact_ext[(self.entrée_lab[0],self.entrée_lab[1])] = a

        for i in range (x*y-1) :
            b = randint(0,len(cases_contact_ext[(pos_x,pos_y)])-1)
            #sauvegarde.append(b)
            #print(i)
            #print(sauvegarde)
            #print()
            #b = save[i]
            if cases_contact_ext[(pos_x,pos_y)][b] == "N" :
                if lab[pos_y][pos_x] == "3" :
                    lab[pos_y][pos_x] = "2"
                elif lab[pos_y][pos_x] == "1" :
                    lab[pos_y][pos_x] = "0"
                pos_y -= 1
            elif cases_contact_ext[(pos_x,pos_y)][b] == "S" :
                if lab[pos_y+1][pos_x] == "3" :
                    lab[pos_y+1][pos_x] = "2"
                elif lab[pos_y+1][pos_x] == "1" :
                    lab[pos_y+1][pos_x] = "0"
                pos_y += 1
            elif cases_contact_ext[(pos_x,pos_y)][b] == "E" :
                if lab[pos_y][pos_x+1] == "3" :
                    lab[pos_y][pos_x+1] = "1"
                elif lab[pos_y][pos_x+1] == "2" :
                    lab[pos_y][pos_x+1] = "0"
                pos_x += 1
            elif cases_contact_ext[(pos_x,pos_y)][b] == "O" :
                if lab[pos_y][pos_x] == "3" :
                    lab[pos_y][pos_x] = "1"
                elif lab[pos_y][pos_x] == "2" :
                    lab[pos_y][pos_x] = "0"
                pos_x -= 1

            if pos_y > 0 and (pos_x,pos_y-1) in cases_contact_ext :
                if "S" in cases_contact_ext[(pos_x,pos_y-1)] :
                    d = cases_contact_ext[(pos_x,pos_y-1)].index("S")
                    cases_contact_ext[(pos_x,pos_y-1)].pop(d)
                if len(cases_contact_ext[(pos_x,pos_y-1)]) == 0 :
                    cases_contact_ext.pop((pos_x,pos_y-1))
            if pos_y < y-1 and (pos_x,pos_y+1) in cases_contact_ext :
                if "N" in cases_contact_ext[(pos_x,pos_y+1)] :
                    d = cases_contact_ext[(pos_x,pos_y+1)].index("N")
                    cases_contact_ext[(pos_x,pos_y+1)].pop(d)
                if len(cases_contact_ext[(pos_x,pos_y+1)]) == 0 :
                    cases_contact_ext.pop((pos_x,pos_y+1))
            if pos_x < x+1 and (pos_x+1,pos_y) in cases_contact_ext :
                if "O" in cases_contact_ext[(pos_x+1,pos_y)] :
                    d = cases_contact_ext[(pos_x+1,pos_y)].index("O")
                    cases_contact_ext[(pos_x+1,pos_y)].pop(d)
                if len(cases_contact_ext[(pos_x+1,pos_y)]) == 0 :
                    cases_contact_ext.pop((pos_x+1,pos_y))
            if pos_x > 0 and (pos_x-1,pos_y) in cases_contact_ext :
                if "E" in cases_contact_ext[(pos_x-1,pos_y)] :
                    d = cases_contact_ext[(pos_x-1,pos_y)].index("E")
                    cases_contact_ext[(pos_x-1,pos_y)].pop(d)
                if len(cases_contact_ext[(pos_x-1,pos_y)]) == 0 :
                    cases_contact_ext.pop((pos_x-1,pos_y))

            cases_visitées.append((pos_x,pos_y))
            if i < x*y-2 :
                a = []
                if not((pos_x, pos_y-1) in cases_visitées) and pos_y > 0 :
                    a.append("N")
                if not((pos_x, pos_y+1) in cases_visitées) and pos_y < y-1 :
                    a.append("S")
                if not((pos_x+1, pos_y) in cases_visitées) and pos_x < x-1 :
                    a.append("E")
                if not((pos_x-1, pos_y) in cases_visitées) and pos_x > 0 :
                    a.append("O")
                if a == [] :
                    if pos_x in (0, x-1) or pos_y in (0, y-1) :
                        potentiel_sorties.append((abs(pos_x-self.entrée_lab[0])+abs(pos_y-self.entrée_lab[1]), pos_x, pos_y))
                    c = list(cases_contact_ext)
                    #pos_x, pos_y = c[0][0], c[0][1]
                    #pos_x, pos_y = c[len(c)-1][0], c[len(c)-1][1]
                    b = randint(0,len(c)-1)
                    pos_x, pos_y = c[b][0], c[b][1]
                else :
                    cases_contact_ext[(pos_x, pos_y)] = a
        if len(potentiel_sorties) > 0 :
            potentiel_sorties.sort()
            e = potentiel_sorties.pop()
            if e[1] == x-1 :
                sortie_lab = [e[1]+1, e[2]]
            elif e[1] == 0 :
                sortie_lab = [e[1]-1, e[2]]
            elif e[2] == y-1 :
                sortie_lab = [e[1], e[2]+1]
            elif e[2] == 0 :
                sortie_lab = [e[1], e[2]-1]
        if sortie_lab[0] == x :
            lab[sortie_lab[1]][sortie_lab[0]] = "0"
        elif sortie_lab[0] == -1 :
            if lab[sortie_lab[1]][0] == "2" :
                lab[sortie_lab[1]][0] = "0"
            elif lab[sortie_lab[1]][0] == "3" :
                lab[sortie_lab[1]][0] = "1"
        elif sortie_lab[1] == y :
            lab[sortie_lab[1]][sortie_lab[0]] = "0"
        elif sortie_lab[1] == -1 :
            if lab[0][sortie_lab[0]] == "1" :
                lab[0][sortie_lab[0]] = "0"
            elif lab[0][sortie_lab[0]] == "3" :
                lab[0][sortie_lab[0]] = "2"
        self.sortie_lab = sortie_lab
        #print(sauvegarde)
        return lab
    
    def save_as (self,nom_du_lab, lab, entrée, sortie) :
        nom = "Labyrinthes aléatoires enregistrés/Labirinthe "+nom_du_lab+".csv"
        with open (nom, "w", newline = "") as f :
            ecrire = writer (f, delimiter = ",", lineterminator = "\n")
            for i in range (-2,len(lab)) :
                if i == -2 :
                    ecrire.writerow (entrée)
                elif i == -1 :
                    ecrire.writerow (sortie)
                else :
                    ecrire.writerow (lab[i])
    
    def sauvegarder_lab_alea (self) :
        MsgBox = messagebox.askquestion ('Enregistrer un labyrinthe généré aléatoirement','Voulez-vous vraiment enregistrer le labyrinthe actuel ?',icon = 'warning')
        if MsgBox == 'yes':
            nom = askstring ( title = "Nom du labirinthe"  , prompt = "Quel sera le nom du labyrinthe à enregistrer ?" , initialvalue = "")
            if nom == None :
                return
            else :
                self.save_as (nom, self.lab, self.entrée_lab, self.sortie_lab)
                fichier_nom_labs_alea = open("Labyrinthes aléatoires enregistrés/Noms labyrinthes aléatoires","a")
                fichier_nom_labs_alea.write("Labyrinthe "+nom+"\n")
                fichier_nom_labs_alea.close()
                messagebox.showinfo ('Labyrinthe aléatoire enregistré','Le Labyrinthe aléatoire actuel à bien été enregisté sous le nom : Labyrinthe '+nom+' !')
    
    def test_nb_murs_niv_4 (self) :
        if self.big_boss.difficultee.numero == 1 :
            limite = self.nb_murs_dans_lab / 2
            message = "la moitié"
        elif self.big_boss.difficultee.numero == 2 :
            limite = self.nb_murs_dans_lab /5
            message = "1/5"
        elif self.big_boss.difficultee.numero == 3 :
            limite = self.nb_murs_dans_lab /10
            message = "1/10"
        if len(self.Murs_lab) >= limite :
            self.Murs_lab = []
            messagebox.showinfo ("Dommage !","Vous avez découvert plus de "+message+" des murs, ils vont donc tous disparaître !", icon = "error")
            self.canvas.refresh_lab ()
        return
    
    def reglages_lab_alea (self) :
        return


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
            self.canvas.move(self.balle, x*self.canvas.taille, y*self.canvas.taille)
        self.y += y
        self.x += x
        if self.big_boss.niveau.Niveau_max and self.contours_visibles :
            self.canvas.refresh_lab ()
            self.contours_visibles = False
        #else :
            #self.fenetre.refresh_barre_principale ()
        if self.big_boss.niveau.numero > 1 :
            self.grille.Position_joueur_sur_back_lab_partition ()
        self.big_boss.win()
        self.ou_aller()
    
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
                if self.count_x % self.decoupe_dep == 0 and self.count_y % self.decoupe_dep == 0 :
                    self.mouve(x, y, deplacement_reel= False)
                    if (self.next_dir == (0,1) and self.aller_bas) or \
                        (self.next_dir == (0,-1) and self.aller_haut) or \
                        (self.next_dir == (1,0) and self.aller_droite) or \
                        (self.next_dir == (-1,0) and self.aller_gauche) :
                        self.canvas.move(self.balle, self.next_dir[0]*self.canvas.taille/self.decoupe_dep, self.next_dir[1]*self.canvas.taille/self.decoupe_dep)
                        self.count_x += self.next_dir[0]
                        self.count_y += self.next_dir[1]
                        self.fenetre.after(self.vitesse, self.fonction_dep, self.next_dir[0], self.next_dir[1], True)
                        self.next_dir = None
                    elif ((x,y) == (0,1) and self.aller_bas) or \
                        ((x,y) == (0,-1) and self.aller_haut) or \
                        ((x,y) == (1,0) and self.aller_droite) or \
                        ((x,y) == (-1,0) and self.aller_gauche) :
                        self.canvas.move(self.balle, x*self.canvas.taille/self.decoupe_dep, y*self.canvas.taille/self.decoupe_dep)
                        self.count_x += x
                        self.count_y += y
                        self.fenetre.after(self.vitesse, self.fonction_dep, x, y, True)
                    else :
                        self.en_deplacement = False
                else :
                    self.canvas.move(self.balle, x*self.canvas.taille/self.decoupe_dep, y*self.canvas.taille/self.decoupe_dep)
                    self.count_x += x
                    self.count_y += y
                    self.fenetre.after(self.vitesse,self.fonction_dep,x,y,True)
        elif self.en_deplacement :
                self.next_dir = (x,y)
        elif ((x,y) == (0,1) and self.aller_bas) or \
            ((x,y) == (0,-1) and self.aller_haut) or \
            ((x,y) == (1,0) and self.aller_droite) or \
            ((x,y) == (-1,0) and self.aller_gauche) :
                self.en_deplacement = True
                self.canvas.move(self.balle, x*self.canvas.taille/self.decoupe_dep, y*self.canvas.taille/self.decoupe_dep)
                self.count_x += x
                self.count_y += y
                self.fenetre.after(self.vitesse, self.fonction_dep, x, y, True)
    
    def haut (self,event) :
        if self.x != self.grille.sortie_lab[0] or self.y != self.grille.sortie_lab[1] :
            if self.big_boss.type_deplacement == "Lisse" :
                self.fonction_dep (y=-1)
            if self.aller_haut :
                if self.big_boss.type_deplacement == "Sec"  :
                    self.mouve(0,-1)
            elif self.big_boss.niveau.Niveau_max and self.y == 0 :
                self.canvas.delete("all")
                self.init()
                self.canvas.trace_contours_lab ()
                self.contours_visibles = True
            elif self.big_boss.niveau.numero == 4 and not(self.big_boss.niveau.Niveau_max) and self.y > 0 and not((self.x,self.y,"1") in self.grille.Murs_lab) :
                self.grille.Murs_lab.append((self.x,self.y,"1"))
                self.canvas.barre_horizontale (self.canvas.origine_x + self.x*self.canvas.taille, self.canvas.origine_y + self.y*self.canvas.taille, self.canvas.taille, self.canvas.color_grille)
                self.grille.test_nb_murs_niv_4 ()
    
    def bas (self,event) :
        if self.x != self.grille.sortie_lab[0] or self.y != self.grille.sortie_lab[1] :
            if self.big_boss.type_deplacement == "Lisse" :
                self.fonction_dep (y=1)
            if self.aller_bas :
                if self.big_boss.type_deplacement == "Sec" :
                    self.mouve(0,1)
            elif self.big_boss.niveau.Niveau_max and self.y == self.grille.y-2 :
                self.canvas.delete("all")
                self.init()
                self.canvas.trace_contours_lab ()
                self.contours_visibles = True
            elif self.big_boss.niveau.numero == 4 and not(self.big_boss.niveau.Niveau_max) and self.y < self.grille.y-2 and not((self.x,self.y+1,"1") in self.grille.Murs_lab) :
                self.grille.Murs_lab.append((self.x,self.y+1,"1"))
                self.canvas.barre_horizontale (self.canvas.origine_x + self.x*self.canvas.taille, self.canvas.origine_y + (self.y+1)*self.canvas.taille, self.canvas.taille, self.canvas.color_grille)
                self.grille.test_nb_murs_niv_4 ()
    
    def droite (self,event) :
        if self.x != self.grille.sortie_lab[0] or self.y != self.grille.sortie_lab[1] :
            if self.big_boss.type_deplacement == "Lisse" :
                self.fonction_dep (x=1)
            if self.aller_droite :
                if self.big_boss.type_deplacement == "Sec" :
                    self.mouve(1,0)
            elif self.big_boss.niveau.Niveau_max and self.x == self.grille.x-2 :
                self.canvas.delete("all")
                self.init()
                self.canvas.trace_contours_lab ()
                self.contours_visibles = True
            elif self.big_boss.niveau.numero == 4 and not(self.big_boss.niveau.Niveau_max) and self.x < self.grille.x-2 and not((self.x+1,self.y,"2") in self.grille.Murs_lab) :
                self.grille.Murs_lab.append((self.x+1,self.y,"2"))
                self.canvas.barre_verticale (self.canvas.origine_x + (self.x+1)*self.canvas.taille, self.canvas.origine_y + self.y*self.canvas.taille, self.canvas.taille, self.canvas.color_grille)
                self.grille.test_nb_murs_niv_4 ()
    
    def gauche (self,event) :
        if self.x != self.grille.sortie_lab[0] or self.y != self.grille.sortie_lab[1] :
            if self.big_boss.type_deplacement == "Lisse" :
                self.fonction_dep (x=-1)
            if self.aller_gauche :
                if self.big_boss.type_deplacement == "Sec" :
                    self.mouve(-1,0)
            elif self.big_boss.niveau.Niveau_max and self.x == 0 :
                self.canvas.delete("all")
                self.init()
                self.canvas.trace_contours_lab ()
                self.contours_visibles = True
            elif self.big_boss.niveau.numero == 4 and not(self.big_boss.niveau.Niveau_max) and self.x > 0 and not((self.x,self.y,"2") in self.grille.Murs_lab):
                self.grille.Murs_lab.append((self.x,self.y,"2"))
                self.canvas.barre_verticale (self.canvas.origine_x + self.x*self.canvas.taille, self.canvas.origine_y + self.y*self.canvas.taille, self.canvas.taille, self.canvas.color_grille)
                self.grille.test_nb_murs_niv_4 ()




class Niveaux_fen (tk.Toplevel) :
    def __init__(self, boss=None, titre= "Informations Niveaux", color= "white") :
        tk.Toplevel.__init__(self,boss)
        self.boss = boss
        self.x = 300
        self.y = 200
        self.canvas_x = self.x * 1/3
        self.canvas_y = self.y
        self.resizable(False, False)
        self.color_canvas = color
        self.title(titre)
        self.geometry (f"{self.x}x{self.y}")
        nb_colones = 3
        nb_lignes = 4
        for i in range (nb_colones) :
            self.grid_columnconfigure(i, weight= 1, minsize= 1/nb_colones*self.x)
        for i in range (nb_lignes) :
            self.grid_rowconfigure(i, weight= 1, minsize= 1/nb_lignes*self.y)
        self.canvas = tk.Canvas(self, width= str(self.canvas_x), height= str(self.canvas_y), bg=self.color_canvas)
        self.canvas.grid(column= 0, row= 0, columnspan= 1, rowspan=4)
        y1 = round(self.canvas_y*1/8)
        y3 = round(self.canvas_y*3/8)
        y5 = round(self.canvas_y*5/8)
        y7 = round(self.canvas_y*7/8)
        self.canvas.create_text(self.canvas_x/2, y1, text= "Niveau 1 :", font= "arial")
        self.canvas.create_text(self.canvas_x/2, y3, text= "Niveau 2 :", font= "arial")
        self.canvas.create_text(self.canvas_x/2, y5, text= "Niveau 3 :", font= "arial")
        self.canvas.create_text(self.canvas_x/2, y7, text= "Niveau 4 :", font= "arial")
        self.init_boutons ()
        self.mainloop()

    def init_boutons (self) :
        tk.Button (self, text='Go', command=partial(self.go_niv,1)).grid(column= 1, row= 0)
        tk.Button (self, text='Go', command=partial(self.go_niv,2)).grid(column= 1, row= 1)
        tk.Button (self, text='Go', command=partial(self.go_niv,3)).grid(column= 1, row= 2)
        tk.Button (self, text='Go', command=partial(self.go_niv,4)).grid(column= 1, row= 3)
        
        tk.Button (self, text='Infos', command=self.info_niv1).grid(column= 2, row= 0)
        tk.Button (self, text='Infos', command=self.info_niv2).grid(column= 2, row= 1)
        tk.Button (self, text='Infos', command=self.info_niv3).grid(column= 2, row= 2)
        tk.Button (self, text='Infos', command=self.info_niv4).grid(column= 2, row= 3)

    def go_niv (self,n) :
        self.boss.Niveau = n
        self.boss.niveaux()
        self.destroy()
    
    def info_niv1 (self) :
        x = 475
        y = 150
        titre = "Informations Niveau 1"
        texte = ["Le Niveau 1 permet de parcourir les labyrinthes 'normalement'",
                "c'est à dire sans aucune gène particulière.",
                "Le Niveau 1 ne contient pas de Difficultées"]
        division = 10
        positions = [2,4,6]
        for i in range (len(positions)) :
            positions[i] /= division
        pos_max=(9/10,8/10)
        Infos(self,x,y,titre,texte,positions,pos_max)
    
    def info_niv2 (self) :
        x = 800
        y = 300
        titre = "Informations Niveau 2"
        texte = ["Dans le Niveau 2 les labyrinthes (qui sont les mêmes qu'au niveau 1!) sont divisés/découpés ",
                "en plusieurs morceaux. Au début, seul un morceau est visible, puis à chaque fois que vous ",
                "'découvrez' un nouveaux morceau, il apparait. Cependant, si vous découvrez plus de ",
                "la moitié des morceaux, ils re-disparaissent !",
                "Dans ce niveau, plus on augmente la Difficultée, plus les labyrinthes sont divisés/découpés en plus de ",
                "morceaux (et donc les morceaux sont plus petits). A la Difficultée 1(respectivement 2 et 3), les morceaux ",
                "découverts disparaissent quand la moitiée (respectivement 1/4 et 1/8) des morceaux ont été découverts."]
        division = 10
        positions = [1,2,3,4,6,7,8]
        for i in range (len(positions)) :
            positions[i] /= division
        Infos(self,x,y,titre,texte,positions)
        
    def info_niv3 (self) :
        x = 550
        y = 300
        titre = "Informations Niveau 3"
        texte = ["Dans le Niveau 3 les labyrinthes (qui sont les mêmes qu´au niveau 1!) ",
                "sont divisés/découpés en plusieurs morceaux. UN seul morceau est ",
                "visible : à chaque fois que vous vous déplacez vers un nouveaux ",
                "morceau, seul le morceau que vous parcourez est visible. ",
                "Dans ce niveau, plus on augmente la Difficultée, ",
                "plus les labyrinthes sont divisés/découpés en plus de",
                "morceaux (et donc les morceaux sont plus petits)"]
        division = 10
        positions = [1,2,3,4,6,7,8]
        for i in range (len(positions)) :
            positions[i] /= division
        Infos(self,x,y,titre,texte,positions)
        
    def info_niv4 (self) :
        x = 600
        y = 300
        titre = "Informations Niveau 4"
        texte = ["Dans le Niveau 4 les labyrinthes sont les mêmes qu'à tous les niveaux, ",
                "mais au début, aucun mur n'est visible, puis à chaque fois que vous ",
                "rentrez dans un nouveau mur, il apparait. Cependant, si vous ",
                "découvrez plus de la moitié des murs, ils re-disparaissent !",
                "Dans ce niveau, plus on augmente la Difficultée, plus les murs disparaissent tôt :",
                "à la Difficultée 1(respectivement 2 et 3), les murs découverts disparaissent ",
                "quand la moitiée (respectivement 1/4 et 1/8) des murs ont été découverts."]
        division = 10
        positions = [1,2,3,4,6,7,8]
        for i in range (len(positions)) :
            positions[i] /= division
        Infos(self,x,y,titre,texte,positions)

class Infos (tk.Toplevel) :
    def __init__(self, boss=None, x=400, y=200, titre="test", texte=["test"],
                positions=(2/10), pos_max=(9/10,9/10), police="arial", color="white") :
        tk.Toplevel.__init__(self,boss)
        self.boss = boss
        self.canvas_x = self.x = x
        self.canvas_y = self.y = y
        self.resizable(False, False)
        self.color_canvas = color
        self.title(titre)
        self.geometry (f"{self.x}x{self.y}")
        self.canvas = tk.Canvas(self, width= str(self.canvas_x), height= str(self.canvas_y), bg=self.color_canvas)
        self.canvas.pack()
        for i in range (len(texte)) :
            self.canvas.create_text(self.canvas_x/2, round(self.canvas_y*positions[i]), text= texte[i], font= police)
        self.canvas.create_text(self.canvas_x*pos_max[0], self.canvas_y*pos_max[1], text= "Max", font= police)
        self.mainloop()

class Fen_infos_generales (tk.Toplevel) :
    def __init__ (self, boss, big_boss) :
        tk.Toplevel.__init__(self, boss)
        self.big_boss = big_boss
        self.title("Informations Générales")
        self.nb_lignes = 2
        self.nb_colones = 1
        for i in range (self.nb_colones) :
            self.grid_columnconfigure(i, weight= 1) 
        for i in range (self.nb_lignes) :
            self.grid_rowconfigure(i, weight= 1)
        
        self.init_contenu()
        
        self.resizable(False, False)
        self.focus_set()
    
    def init_contenu (self) :
        text = tk.Text(self, wrap= tk.WORD, width=55, height=8, padx=50, pady=30, font=("Helvetica", 15))
        text.insert(0.1, "Bienvenu dans le Parcoureur de Labyrinthes !\n\n\nC'est ici que vous pouvez jouer avec les labyrinthes dans différents modes.")
        text['state'] = 'disabled'
        text.grid(column=0, row=0, sticky=tk.NSEW)
        text.tag_add("titre", "1.0", "1.46")
        text.tag_config("titre", foreground="red", font=("Helvetica", 20), justify='center')
        
        
        bouton_1 = tk.Button (self, text="Ouvrir le Builder de Labyrinthes", padx=20, pady=10, font=("Helvetica", 13), bg="blue", fg= "white", \
            command=self.big_boss.lancement_builder_labs)
        bouton_1.grid(column=0, row=1)

class Message_fin_lab (tk.Toplevel) :

    def __init__ (self, boss=None) :
        tk.Toplevel.__init__(self)
        self.boss = boss
        self.canvas_x = 300
        self.canvas_y = 100
        self.x = self.canvas_x + 50
        self.y = self.canvas_y + 90
        self.title("Labyrinthe Réussi !")
        self.geometry (f"{self.x}x{self.y}")
        self.canvas = tk.Canvas(self, width= str(self.canvas_x), height= str(self.canvas_y), bg= "white")
        self.canvas.pack()
        y30 = round(self.canvas_y*30/100)
        y50 = round(self.canvas_y*50/100)
        y70 = round(self.canvas_y*70/100)
        y90 = round(self.canvas_y*90/100)
        txt1 = "Tu as réussi le Labyrinthe n°"+str(self.boss.nb_lab)
        txt2 = "Que fait tu maintenant : "
        if self.boss.type_lab == "classique" :
            txt3 = "passer au suivant, revenir au précédent, "
        elif self.boss.type_lab == "aleatoire" :
            txt3 = "passer au suivant, sauvegarder ce labirinthe, "
        txt4 = "refaire celui-ci ou quitter le jeu ?"
        self.canvas.create_text(self.canvas_x/2, y30, text= txt1, font= "arial")
        self.canvas.create_text(self.canvas_x/2, y50, text= txt2, font= "arial")
        self.canvas.create_text(self.canvas_x/2, y70, text= txt3, font= "arial")
        self.canvas.create_text(self.canvas_x/2, y90, text= txt4, font= "arial")
        self.init_boutons_page_win ()
        self.bind("<Up>", self.recomencer)
        self.bind("<Down>", self.recomencer)
        self.bind("<Right>", self.suivant)
        self.bind("<o>", self.recomencer)
        self.bind("<l>", self.recomencer)
        self.bind("<m>", self.suivant)
        self.bind("<Return>", self.suivant)
        if self.boss.type_lab == "classique" :
            self.bind("<Left>", self.precedent)
            self.bind("<k>", self.precedent)
        elif self.boss.type_lab == "aleatoire" :
            self.bind("<Left>", self.boss.grille.sauvegarder_lab_alea)
            self.bind("<k>", self.boss.grille.sauvegarder_lab_alea)
        self.focus_set()
        self.mainloop()

    def init_boutons_page_win (self) :
        "Initalise et affiche dans la fenêtre fen_message_fin_lab les boutons quitter, suivant, recommencer et precedent"
        tk.Button (self, text='Quitter', command=self.quitter).pack(side= "left")

        tk.Button (self, text='Suivant ->', command=self.suivant).pack(side= "right") 

        tk.Button (self, text='Recommencer', command=self.recomencer).pack(side= "right")

        tk.Button (self, text='<- Précédent', command=self.precedent).pack(side= "right")

    def quitter (self) :
        "Permet de quitter le jeu"
        MsgBox = messagebox.askquestion ('Quitter','Voulez-vous vraiment quitter le jeu?',icon = 'error')
        if MsgBox == 'yes':
            self.destroy()
            self.boss.destroy()

    def recomencer (self,event=None) :
        "Permet de recommencer le labyrinthe"
        self.boss.canvas.nouvelle_partie()
        self.destroy()

    def suivant (self,event=None) :
        "Permet de passer au labyrinthe suivant"
        if self.boss.nb_lab != self.boss.nombre_de_labs :
            if self.boss.type_lab == "classique" :
                self.boss.nb_lab += 1
            self.boss.canvas.nouvelle_partie()
            self.destroy()
        else :
            messagebox.showinfo ('Labyrinthe suivant','Vous êtes déjà sur le dernier Labyrinthe',icon = 'error')

    def precedent (self,event=None) :
        "Permet de revenir au labyrinthe précédent"
        if self.boss.nb_lab != 1 :
            self.boss.nb_lab -= 1
            self.boss.canvas.nouvelle_partie()
            self.destroy()
        else :
            messagebox.showinfo ('Labyrinthe précédent','Vous êtes déjà sur le 1er Labyrinthe',icon = 'error')

class Chrono(tk.Frame):
    def __init__(self, boss=None, max_time=3600):
        tk.Frame.__init__(self,boss)
        self.boss = boss
        self.time = 0
        self.max_time = max_time
        self.running = False
        self.create_widgets()
    
    def create_widgets(self):
        self.label = tk.Label(self, text="00:00", fg="red", font=("Arial", 30))
        self.label.pack()
        self.boss.bind("<q>",self.start)
        self.boss.bind("<w>",self.stop)
        self.boss.bind("<e>",self.reset)
    
    def start(self,event=None):
        if not(self.running) :
            self.running = True
            self.update_time()
    
    def stop(self,event=None):
        self.running = False
    
    def reset(self,event=None):
        self.running = False
        self.time = 0
        self.update_label()
    
    def update_time(self):
        if self.running:
            self.time += 1
            self.update_label()
            self.test_fin()
            self.after(1000, self.update_time)
    
    def update_label(self):
        hours = self.time // 3600
        minutes = (self.time // 60) % 60
        seconds = self.time % 60
        self.label.config(text=f"{minutes:02d}:{seconds:02d}")
        
    def test_fin (self) :
        if self.max_time == self.time :
            self.running = False
            messagebox.showinfo ('Fin du temps impartis','Le temps accordé est dépassé !',icon = 'error')


class Reglages (tk.Toplevel) :
    def __init__ (self, boss) :
        tk.Toplevel.__init__(self, boss)
        self.x = 550
        self.y = 500
        self.title("Réglages")
        self.geometry(str(self.x)+"x"+str(self.y))
        self.grid_columnconfigure(0, weight= 1)
        self.grid_columnconfigure(1, weight= 0)
        self.grid_rowconfigure(0, weight= 0)
        self.grid_rowconfigure(1, weight= 0)
        self.grid_rowconfigure(2, weight= 0)
        self.grid_rowconfigure(3, weight= 1)
        self.grid_rowconfigure(4, weight= 0)
        
        self.width_titres = 35
    
    def lancement (self) :
        self.canvas = tk.Canvas(self)
        self.content = tk.Frame(self.canvas)
        self.content.bind("<Configure>", self.resize_frame)
        #self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.bind('<Enter>', self._bound_to_mousewheel)
        self.bind('<Leave>', self._unbound_to_mousewheel)
        
        scrollbar_y=tk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar_x=tk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.create_window((0, 0), window=self.content)
        self.canvas.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        self.lancement_tous_les_reglages()
        
        self.init_header()
        self.ajout_separation(position=2, boss=self, color="green", is_separation_principale=True)
        self.canvas.grid(column=0, row=3)
        scrollbar_x.grid(column=0, row=4, columnspan=2, sticky=tk.EW)
        scrollbar_y.grid(column=1, row=0, rowspan=4, sticky=tk.NS)
        
        self.after(100, self.canvas.yview_moveto, '0')
        self.after(100, self.resize_canvas)
        #self.resizable(False, True)
        self.focus_set()
    
    def lancement_tous_les_reglages (self) :
        reglages = [Reglages_lab_alea, Reglages_apparence, Reglages_balle]
        self.tous_les_reglages = {}
        self.separations = []
        i = 0
        for regl in reglages :
            if i > 0 :
                self.ajout_separation(position=i)
                i += 1
            reglage = regl(self.content, self.big_boss)
            self.tous_les_reglages[reglage.name] = reglage
            self.tous_les_reglages[reglage.name].init_entitees(self, self.grille, self.balle)
            self.tous_les_reglages[reglage.name].lancement()
            self.tous_les_reglages[reglage.name].grid(row=i)
            i += 1
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def _bound_to_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _unbound_to_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")
    
    def resize_canvas(self) :
        self.canvas.configure(width=self.content.winfo_width(),\
            height=self.content.winfo_height())
    
    def init_entitees (self, big_boss, fenetre, grille, canvas, balle) :
        self.big_boss = big_boss
        self.fenetre = fenetre
        self.grille = grille
        self.canvas = canvas
        self.balle = balle
    
    def resize_frame(self, e):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))        
    
    def ajout_separation (self, position, boss=None, color="grey", is_separation_principale=False) :
        if boss is None :
            boss = self.content
        separation = tk.Text(boss, bg=color, pady=5, height=1, font=("Helvetica", 1))
        separation['state'] = 'disabled'
        if is_separation_principale :
            separation.grid(column=0, row=position, sticky=tk.NSEW)
        else :
            self.separations.append(separation)
            separation.grid(column=0, row=position, pady=30, sticky=tk.NSEW)
    
    def init_header (self) :        
        self.header = tk.Frame(self, border=10)
        self.header.grid(column=0, row=0, sticky=tk.NSEW)
        self.header.grid_columnconfigure(0, weight= 1)
        self.header.grid_columnconfigure(1, weight= 1)
        self.header.grid_columnconfigure(2, weight= 1)
        
        btn = tk.Button(self.header, text="Tout", command=self.afficher_tous_params, font=("Helvetica", 14), bg="green", fg="white")
        btn.grid(column=0, row=0, sticky=tk.W)
        
        noms_reglages = list(self.tous_les_reglages.keys())
        self.combobox_header = ttk.Combobox(self.header, values=noms_reglages, state="readonly", justify="center", width=15, height=2, style="TCombobox", font=("Helvetica", 13))
        self.combobox_header.set("Réglages")
        self.combobox_header.bind("<<ComboboxSelected>>", self.affiche_type_reglage_particulier)
        self.combobox_header.grid(column=1, row=0)
        
        btn = tk.Button(self.header, text="Appliquer", command=self.appliquer_modifications, font=("Helvetica", 14), bg="blue", fg="white")
        btn.grid(column=2, row=0, sticky=tk.E)
        
        self.alerte_mauvaise_entree = bool(int(self.big_boss.parametres["lab alea alerte mauvaise entree"]))
        self.var_alerte_mauvaise_entree = tk.IntVar()
        self.var_alerte_mauvaise_entree.set(int(self.alerte_mauvaise_entree))
        checkbtn_alerte_mauvaise_entree = tk.Checkbutton(self, variable= self.var_alerte_mauvaise_entree, command=self.change_alerte_mauvaise_entree ,compound=tk.LEFT, text="Alerte pour mauvaise entrée", border=10, font=("Helvetica", 13))
        checkbtn_alerte_mauvaise_entree.grid(column=0, row=1, sticky=tk.W)
    
    def change_alerte_mauvaise_entree (self) :
        self.alerte_mauvaise_entree = bool(self.var_alerte_mauvaise_entree.get())
    
    def effacer_tous_reglages (self) :
        for nom_reg in self.tous_les_reglages :
            self.tous_les_reglages[nom_reg].grid_forget()
        for sep in self.separations :
            sep.grid_forget()
        self.separations = []
    
    def affiche_type_reglage_particulier (self, event=None) :
        reglage = self.combobox_header.get()
        self.combobox_header.set("Réglages")
        self.effacer_tous_reglages()
        self.tous_les_reglages[reglage].grid(row=0)
        self.after(100, self.resize_canvas)
        self.after(100, self.canvas.yview_moveto, '0')
    
    def afficher_tous_params (self) :
        self.effacer_tous_reglages()
        i = 0
        for name_reg in self.tous_les_reglages :
            if i > 0 :
                self.ajout_separation(position=i)
                i += 1
            self.tous_les_reglages[name_reg].grid(row=i)
            i += 1
        self.after(100, self.resize_canvas)
        self.after(100, self.canvas.yview_moveto, '0')
    
    def appliquer_modifications (self) :
        for reg_name in self.tous_les_reglages :
            self.tous_les_reglages[reg_name].appliquer_modifications()
        self.big_boss.parametres["lab alea alerte mauvaise entree"] = int(self.alerte_mauvaise_entree)

class Base_Reglages (tk.Frame) :
    def __init__ (self, boss, big_boss, name) :
        tk.Frame.__init__(self, boss, border=10)
        self.big_boss = big_boss
        self.name = name
    
    def init_entitees (self, boss, grille, balle) :
        self.boss = boss
        self.grille = grille
        self.balle = balle
    
    def lancement (self, titre) :
        self.text = tk.Text(self, wrap= tk.WORD, width=self.boss.width_titres, height=1, padx=50, pady=30, font=("Helvetica", 15))
        self.text.insert(0.1, titre)
        self.text['state'] = 'disabled'
        self.text.tag_add('entier','1.0',tk.END)
        self.text.tag_config('entier', justify=tk.CENTER)
        self.text.grid(column=0, row=0, sticky=tk.NSEW)

class Reglages_lab_alea (Base_Reglages) :
    def __init__ (self, boss, big_boss) :
        Base_Reglages.__init__(self, boss, big_boss, "Générateur de labyrinthes")
    
    def lancement (self) :
        Base_Reglages.lancement(self, "Réglages du générateur de labyrinthes")
        
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
        except :
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
        except :
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
        except :
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
        except :
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
    
    def appliquer_modifications (self, save=True) :
        if self.verif_nb_colone() and self.verif_nb_ligne() and self.verif_depart_x() and self.verif_depart_y() :
            self.big_boss.parametres["lab alea x"] = self.valeur_colone.get()
            self.big_boss.parametres["lab alea y"] = self.valeur_ligne.get()
            self.big_boss.parametres["lab alea entree x"] = self.valeur_x.get()
            self.big_boss.parametres["lab alea entree y"] = self.valeur_y.get()
            self.grille.init_variables()

class Reglages_apparence (Base_Reglages) :
    def __init__ (self, boss, big_boss) :
        tk.Frame.__init__(self, boss, border=10)
        self.big_boss = big_boss
        self.name = "Apparence Générale"
    
    def lancement (self) :
        Base_Reglages.lancement(self, "Réglages apparence générale")
        
        self.initial_couleur_mode(1)
    
    def initial_couleur_mode (self, position) :
        couleur_mode = tk.Frame(self, pady=20)
        couleur_mode.grid(column=0, row=position, sticky=tk.NSEW)
        couleur_mode.grid_columnconfigure(0, weight= 1)
        couleur_mode.grid_columnconfigure(1, weight= 1)
        
        text_taille_lab = tk.Label(couleur_mode, text="Couleur glabale initiale:", font=("Helvetica", 13))
        text_taille_lab.grid(column=0, row=0)
        
        color_modes = ["black", "white"]
        self.combobox_initial_couleur_mode = ttk.Combobox(couleur_mode, values=color_modes, state="readonly", justify="center", width=12, height=2, takefocus=False, style="TCombobox", font=("Helvetica", 15))
        self.combobox_initial_couleur_mode.set(self.big_boss.parametres["initial color mode"])
        self.combobox_initial_couleur_mode.grid(column=1, row=0)
    
    def appliquer_modifications (self, save=True) :
        self.big_boss.parametres["initial color mode"] = self.combobox_initial_couleur_mode.get()

class Reglages_balle (Base_Reglages) :
    def __init__ (self, boss, big_boss) :
        tk.Frame.__init__(self, boss, border=10)
        self.big_boss = big_boss
        self.name = "Balle (joueur)"
    
    def lancement (self) :
        Base_Reglages.lancement(self, "Réglages de la Balle")
        
        self.deplacement(1)
    
    def deplacement (self, position) :
        deplacement_balle = tk.Frame(self, pady=20)
        deplacement_balle.grid(column=0, row=position, sticky=tk.NSEW)
        deplacement_balle.grid_columnconfigure(0, weight= 1)
        deplacement_balle.grid_columnconfigure(1, weight= 1)
        deplacement_balle.grid_columnconfigure(2, weight= 1)
        text_taille_lab = tk.Label(deplacement_balle, text="Déplacement\nde la Balle :", font=("Helvetica", 13))
        text_taille_lab.grid(column=0, row=0)
        
        decoupe = tk.Frame(deplacement_balle)
        decoupe.grid(column=1, row=0)
        text_decoupe = tk.Label(decoupe, text="Découpe\ndu mouvement :", font=("Helvetica", 13))
        text_decoupe.grid(column=0, row=0)
        self.decoupe_min = 2
        self.valeur_decoupe = ttk.Spinbox(decoupe, from_= self.decoupe_min, to=50, wrap=True, font=("Helvetica", 15), width=4, command=self.verif_decoupe)
        self.valeur_decoupe.set(self.balle.decoupe_dep)
        self.valeur_decoupe.grid(column=0, row=1)
        self.valeur_decoupe.bind("<Return>", self.verif_decoupe)
        
        vitesse = tk.Frame(deplacement_balle)
        vitesse.grid(column=2, row=0)
        text_vitesse = tk.Label(vitesse, text="Vitesse :", font=("Helvetica", 13))
        text_vitesse.grid(column=0, row=0)
        Laby_builder.Commentaire(self.boss, text_vitesse, "Temps d'attente (en milisecondes)\nentre deux partitions du mouvement\nde la balle entre deux cases")
        self.valeur_vitesse = ttk.Spinbox(vitesse, from_=10, to=1000, wrap=True, font=("Helvetica", 15), width=5, command=self.verif_vitesse)
        self.valeur_vitesse.set(self.balle.vitesse)
        self.valeur_vitesse.grid(column=0, row=1)
        self.valeur_vitesse.bind("<Return>", self.verif_vitesse)
    
    def verif_decoupe (self, event=None) :
        valable = False
        decoupe = self.valeur_decoupe.get()
        try :
            decoupe = int(decoupe)
        except :
            if self.boss.alerte_mauvaise_entree :
                messagebox.showinfo ('Valeur de découpe','La valeur "'+decoupe+'" n\'est pas conforme pour un nombre découpe du mouvement !',parent=self.boss ,icon = 'error')
        else :
            if decoupe < self.decoupe_min :
                decoupe = self.decoupe_min
                if self.boss.alerte_mauvaise_entree :
                    messagebox.showinfo ('Valeur de découpe','Le valeur de découpe minimum est de '+str(self.decoupe_min)+' !\nCar sinon, 0 c\'est de la téléportation et 1 c\'est déjà le déplacement Sec',parent=self.boss ,icon = 'error')
            else :
                valable = True
            self.valeur_decoupe.set(decoupe)
        return valable
    
    def verif_vitesse (self, event=None) :
        valable = False
        vitesse = self.valeur_vitesse.get()
        try :
            vitesse = int(vitesse)
        except :
            if self.boss.alerte_mauvaise_entree :
                messagebox.showinfo ('Vitesse','La vitesse "'+vitesse+'" n\'est pas conforme !',parent=self.boss ,icon = 'error')
        else :
            if vitesse < 1 :
                vitesse = 1
                if self.boss.alerte_mauvaise_entree :
                    messagebox.showinfo ('Vitesse','La vitesse minimum est de 1 mais il est recomendé de prendre au moins 10 car il est ici question de temps en miliseconde entre chaque partition de mouvement !',parent=self.boss ,icon = 'error')
            else :
                valable = True
            self.valeur_vitesse.set(vitesse)
        return valable
    
    def appliquer_modifications (self, save=True) :
        if self.verif_decoupe() and self.verif_vitesse() :
            self.big_boss.parametres["decoupe du deplacement"] = self.valeur_decoupe.get()
            self.big_boss.parametres["vitesse deplacement"] = self.valeur_vitesse.get()
            self.balle.init_variables()



class Niveaux () :
    def __init__(self) -> None:
        self.Niveau_max = False
        self.nombre_de_niveaux = 4
        self.numero = 1
    
    def init_entitees (self, big_boss, fenetre, grille, canvas, balle) :
        self. big_boss = big_boss
        self. fenetre = fenetre
        self. grille = grille
        self. canvas = canvas
        self. balle = balle
    
    def plus (self, event=None) :
        if self.Niveau_max == False :
            if self.numero < self.nombre_de_niveaux :
                self.numero += 1
            else :
                self.numero = 1
            if not(self.niveaux()) :
                if self.numero == 1 :
                    self.numero = self.nombre_de_niveaux
                else :
                    self.numero -= 1
        else :
            messagebox.showinfo ('Changer de Niveau','Le Niveau est déjà au max !',icon = 'error')
    
    def moins (self, event=None) :
        if self.Niveau_max == False  :
            if self.numero == 1 :
                self.numero = self.nombre_de_niveaux
            else :
                self.numero -= 1
            if not(self.niveaux()) :
                if self.numero < self.nombre_de_niveaux :
                    self.numero += 1
                else :
                    self.numero = 1
        else :
            messagebox.showinfo ('Changer de Niveau','Le Niveau est déjà au max !',icon = 'error')
    
    def niveaux (self) :
        if self.numero == 1 :
            self.grille.init_Partitions_lab()
        else :
            if self.numero == 2 :
                MsgBox = messagebox.askquestion ('Passer au Niveau 2','A partir du Niveau 2 le Labyrinthe se divise en plusieurs fragments. Dans le Niveau 2, à chaque fois que vous arriverez sur un nouveau fragment, il apparaitra et vous pourrez voir ainsi où vous allez. Mais attention !, si vous découvrez la moitié des partitions, toutes celles que vous avez découvert dissparaissent !'+" "*190+'Voulez-vous vraiment passer au Niveau 2 ?',icon = 'warning')
                if MsgBox == 'yes':
                    self.grille.init_taille_partition_par_difficultées ()
                else :
                    return False
            elif self.numero == 3 :
                MsgBox = messagebox.askquestion ('Passer au Niveau 3','Dans le Niveau 3 vous ne pouvez voir d´un fragment à la fois donc à chaque fois que vous arriverez sur un nouveau fragment, il apparaitra mais il sera le seul visible, tous les autres serons cachés.'+" "*180+'Voulez-vous vraiment passer au Niveau 3 ?',icon = 'warning')
                if MsgBox == 'yes':
                    self.grille.init_taille_partition_par_difficultées ()
                else :
                    return False
            elif self.numero == 4 :
                MsgBox = messagebox.askquestion ('Passer au Niveau 4','Dans le Niveau 4 les murs du Labyrinthe n´apparaissent que si vous les percutez ! Mais si vous en "découvez" plus de la moitié, tous ceux que vous aurez découverts disparaîtrons ! Alors attention et bon courage !'+" "*180+'Voulez-vous vraiment passer au Niveau 4 ?',icon = 'warning')
                if MsgBox == 'yes':
                    self.grille.Murs_lab = []
                    self.grille.init_taille_partition_par_difficultées ()
                    self.grille.decompte_nb_murs_dans_lab ()
                else :
                    return False
        self.canvas.refresh_lab()
        return True
    
    def niveau_max (self, event=None) :
        if self.Niveau_max == False :
            MsgBox = messagebox.askquestion ('Passer au Niveau max (impossible !!)','Dans le Niveau max tous les murs sont invisibles ! Alors bon courage !'+" "*180+'Voulez-vous vraiment passer au Niveau max ?',icon = 'warning')
            if MsgBox == 'yes':
                self.Niveau_max = True
                self.grille.Murs_lab = []
                self.canvas.balle.contours_visibles = False
                self.canvas.refresh_lab()
        else :
            self.Niveau_max = False
            if self.numero == 1 :
                self.grille.init_Partitions_lab ()
            else :
                if self.numero == 2 or self.numero == 3 :
                    self.grille.init_taille_partition_par_difficultées ()
                elif self.numero == 4 :
                    self.grille.Murs_lab = []
                    self.grille.decompte_nb_murs_dans_lab ()
            self.canvas.refresh_lab()
    
    def fenetre_presentation (self) :
        self.fenetre_presentation = Niveaux_fen(self.fenetre)

class Difficultee () :
    def __init__(self) -> None:
        self.numero = 1
    
    def init_entitees (self, big_boss, fenetre, grille, canvas, balle, niveau) :
        self. big_boss = big_boss
        self. fenetre = fenetre
        self. grille = grille
        self. canvas = canvas
        self. balle = balle
        self.niveau = niveau
    
    def plus (self, event=None) :
        if self.niveau.Niveau_max is False :
            if self.niveau.numero > 1 :
                if self.numero < 3 :
                    self.numero += 1
                else :
                    self.numero = 1
                if not(self.difficultees ()) :
                    if self.numero == 1 :
                        self.numero = 3
                    else :
                        self.numero -= 1
            else :
                messagebox.showinfo ('Changer de difficultée','Il n´y a qu´une seule difficultée pour le niveau 1 !',icon = 'error')
        else :
            messagebox.showinfo ('Changer de difficultée','La Difficultée est déjà au max !',icon = 'error')
    
    def moins (self, event=None) :
        if self.niveau.Niveau_max is False :
            if self.niveau.numero > 1 :
                if self.numero == 1 :
                    self.numero = 3
                else :
                    self.numero -= 1
                if not(self.difficultees ()) :
                    if self.numero < 3 :
                        self.numero += 1
                    else :
                        self.numero = 1
            else :
                messagebox.showinfo ('Changer de difficultée','Il n´y a qu´une seule difficultée pour le niveau 1 !',icon = 'error')
        else :
            messagebox.showinfo ('Changer de difficultée','La Difficultée est déjà au max !',icon = 'error')
    
    def difficultees (self) :
        if self.numero == 2 :
            if self.niveau.numero == 2 or self.niveau.numero == 3 :
                MsgBox = messagebox.askquestion ('Passer à la Difficultée 2','Les Difficultés du niveau '+str(self.niveau.numero)+' modifient la taille des fragment (de plus petits fragments impliquent plus de fragments, donc moins de visibilité et donc une Difficultée accrue !).'+" "*120+'Voulez-vous vraiment passer à la Difficultée 2 ?',icon = 'warning')
            elif self.niveau.numero == 4 :
                MsgBox = messagebox.askquestion ('Passer à la Difficultée 2','La Difficultée 2 du niveau 4 supprimera tous les murs "découverts" quand seulement 1/5 des murs serons découverts ! (Attention c´est très frustrant mais vous allez y arriver !)'+" "*100+'Voulez-vous vraiment passer à la Difficultée 2 ?',icon = 'warning')
            if MsgBox != 'yes':
                return False
        elif self.numero == 3 :
            if self.niveau.numero == 2 or self.niveau.numero == 3 :
                MsgBox = messagebox.askquestion ('Passer à la Difficultée 3','Les Difficultés du niveau '+str(self.niveau.numero)+' modifient la taille des fragment (de plus petits fragments impliquent plus de fragments, donc moins de visibilité et donc une Difficultée accrue !).'+" "*120+'Voulez-vous vraiment passer à la Difficultée 3 ?',icon = 'warning')
            elif self.niveau.numero == 4 :
                MsgBox = messagebox.askquestion ('Passer à la Difficultée 3','La Difficultée 3 du niveau 4 supprimera tous les murs "découverts" quand seulement 1/10 des murs serons découverts ! (Attention c´est très frustrant mais vous allez y arriver !)'+" "*100+'Voulez-vous vraiment passer à la Difficultée 3 ?',icon = 'warning')
            if MsgBox != 'yes':
                return False
        self.grille.init_taille_partition_par_difficultées ()
        self.canvas.refresh_lab()
        return True
    
    def fenetre_presentation (self) :
        self.fenetre_presentation = Niveaux_fen(self.fenetre)



"""

    self.boutons[5] = self.button_sauvegarder_lab_alea = tk.Button (self, text='Sauvegarder Lab', command=self.grille.sauvegarder_lab_alea)
    self.button_sauvegarder_lab_alea.grid_forget()
    self.boutons[6] = self.button_reglages_lab_alea = tk.Button (self, text='Réglages\nLab Aléa', command=self.grille.reglages_lab_alea)
    self.button_reglages_lab_alea.grid_forget()
"""



if __name__ == "__main__" :
    fen_lab = Entite_superieure()
    fen_lab.lancement()


