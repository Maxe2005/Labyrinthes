# Created on 10/02/23
# Author : Maxence CHOISEL

import Outils_Tkinter as ot
#if __name__ == "__main__" :
#    import .Creer_labyrinthes as Laby_builder
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter.simpledialog import askinteger, askstring
from math import log
from typing import Literal
from functools import partial
from PIL import Image,ImageTk
from random import randint
from csv import writer
import copy



class ES_laby (ot.Entite_superieure) :
    def __init__(self, lab_builtder=None) -> None :
        """Constructeur, initialise les instances"""
        self.init_variables_globales()
        
        if lab_builtder is not None :
            self.Lab_builtder = lab_builtder
        
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
        
        self.fenetre.init_barres_boutons_et_text()
        self.init_mode_hard()
        self.init_reglages([Reglages_generaux,\
                            Reglages_lab_alea,\
                            Reglages_apparence,\
                            Reglages_balle,\
                            Reglages_question_confirmation])
        self.init_infos_generales(Fen_infos_generales)
    
    def lancement (self) :
        """Permet de lancer la fenêtre du jeu"""
        self.canvas.nouvelle_partie ()
        self.lancement_fenetre(self.commentaires, fonction_on_closing_save_param=True)
    
    def lancement_builder_labs (self) :
        global Lab_builtder
        if __name__ == "__main__" :
            #Lab_builtder = Laby_builder.Entite_superieure_crea(self)
            #Lab_builtder.lancement()
            pass
        else :
            Lab_builtder.fenetre.lift()
            Lab_builtder.fenetre.focus()
    
    def init_variables_globales (self) :
        """Permet de donner des valeurs arbitraires aux paramètres globaux (params par défaut)"""
        self.ouvrir_param_defaut("Autres/Parametres_defaut.csv", "parcoureur")
        self.type_lab = "classique"
        self.commentaires = []
        self.type_deplacement = self.parametres["type deplacement initial"]
        self.init_variables_tres_globales()
    
    def aller_a (self, event=None) :
        "Permet d´aller directement au Labyrinthe de son choix"
        n = askinteger("Aller directement", f"Numéro du Labyrinthe (max: {self.grille.nombre_de_labs})", parent = self.fenetre, minvalue = 1, maxvalue = self.grille.nombre_de_labs)
        if n is not(None):
            self.grille.num_lab = int(n)
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
        if int(self.parametres["question confirmation recomencer lab"]) :
            MsgBox = messagebox.askquestion ('Recommencer','Voulez-vous vraiment recommencer ce Labyrinthe depuis le début?',icon = 'warning')
        else :
            MsgBox = 'yes'
        if MsgBox == 'yes':
            self.canvas.nouvelle_partie()
    
    def suivant_lab (self, event=None) :
        if int(self.parametres["question confirmation lab suivant"]) :
            MsgBox = messagebox.askquestion ('Labyrinthe suivant','Voulez-vous vraiment lancer le Labyrinthe suivant (plus difficile)?')
        else :
            MsgBox = 'yes'
        if MsgBox == 'yes':
            if self.type_lab == "classique" and self.grille.num_lab != self.grille.nombre_de_labs :
                self.grille.num_lab += 1
                self.canvas.nouvelle_partie()
            elif self.type_lab == "aleatoire" :
                self.grille.num_lab_alea += 1
                self.canvas.nouvelle_partie()
            else :
                messagebox.showinfo ('Labyrinthe suivant','Vous êtes déjà sur le dernier Labyrinthe',icon = 'error')
    
    def precedent_lab (self, event=None) :
        if int(self.parametres["question confirmation lab precedent"]) :
            MsgBox = messagebox.askquestion ('Labyrinthe précédent','Voulez-vous vraiment revenir au Labyrinthe précédent?')
        else :
            MsgBox = 'yes'
        if MsgBox == 'yes':
            if self.type_lab == "classique" and self.grille.num_lab > 1 :
                self.grille.num_lab -= 1
                self.canvas.nouvelle_partie()
            elif self.type_lab == "aleatoire" and self.grille.num_lab_alea > 1 :
                self.grille.num_lab_alea -= 1
                self.canvas.nouvelle_partie()
            else :
                messagebox.showinfo ('Labyrinthe précédent','Vous êtes déjà sur le 1er Labyrinthe',icon = 'error')
    
    def new_lab_alea (self, even=None) :
        self.grille.num_lab_alea = self.grille.nombre_de_lab_alea + 1
        self.canvas.nouvelle_partie()
    
    def win (self) :
        if self.canvas.balle.x == self.grille.sortie_lab[0] and self.canvas.balle.y == self.grille.sortie_lab[1] :
            messagebox.showinfo ("Félicitations !","Vous avez GAGNÉ !")
            Message_fin_lab (self.fenetre, self.grille, self)
    
    def type_labyrinthe (self, event=None) :
        if self.type_lab == "classique" :
            self.type_lab = "aleatoire"
            self.fenetre.boutons_lateraux_droits.renommer("type lab", "Labyrinthe\nClassique")
            self.fenetre.boutons_lateraux_droits.afficher("new lab alea")
            if self.grille.num_lab_alea == 0 :
                self.grille.num_lab_alea = 1
            self.canvas.nouvelle_partie()
        elif self.type_lab == "aleatoire" :
            self.type_lab = "classique"
            self.fenetre.boutons_lateraux_droits.renommer("type lab", "Labyrinthe\nAléatoire")
            self.fenetre.boutons_lateraux_droits.cacher("new lab alea")
            self.canvas.nouvelle_partie()
    
    def init_mode_hard (self) :
        self.mode_hard = False
        self.voyant_mode_hard = tk.Canvas(self.fenetre.barre_laterale_droite, border=10, bg="green")
        self.voyant_mode_hard.configure(width=50, height=50)
        impossible = self.parametres["color mode hard impossible"]
        ready = self.parametres["color mode hard ready"]
        moving = ", ".join(self.parametres["colors mode hard moving"])
        ot.Commentaire(self.fenetre, self.voyant_mode_hard, "Voyant du Mode HARD affichant les états de la balle :\n\n- 'Ready' : balle à l'arrêt ("+ready+")\n- 'Impossible' : balle face à un mur ("+impossible+")\n- 'Moving' : balle en mouvement ("+moving+")\n\nIl y a plusieurs couleurs à l'état 'Moving' pour signaler\nles changement de dirrections (pour le déplacement Lisse)", aligne_in="left")
        #self.voyant_mode_hard = self.canvas_voyant_mode_hard.create_oval (20, 20, 70, 70,  fill= "green", outline= "black")
    
    def mode_HARD (self, event=None) :
        if self.mode_hard :
            self.mode_hard = False
            self.voyant_mode_hard.grid_forget()
        else :
            self.mode_hard = True
            self.voyant_mode_hard.grid(column=0, row=1)
        self.canvas.refresh_lab()
    
    def change_voyant_mode_hard (self, etat:str | Literal["ready", "impossible", "moving", "stop"], latence="") :
        if not(latence) or latence == self.voyant_mode_hard["bg"] :
            if etat == "ready" :
                color = self.parametres["color mode hard ready"]
            elif etat == "moving" :
                color = self.parametres["colors mode hard moving"][0]
                self.index_color_mode_hard_moving = 0
            elif etat == "change direction" :
                self.index_color_mode_hard_moving = (self.index_color_mode_hard_moving + 1) % len(self.parametres["colors mode hard moving"])
                color = self.parametres["colors mode hard moving"][self.index_color_mode_hard_moving]
            elif etat == "impossible" :
                color = self.parametres["color mode hard impossible"]
                self.fenetre.after(1000, self.change_voyant_mode_hard, "ready", color)
            self.voyant_mode_hard.configure(bg=color)
    
    def get_extra_entitees (self, entitees_names:list) :
        entitees = {}
        entitees["fenetre"] = self.fenetre
        entitees["canvas"] = self.canvas
        entitees["grille"] = self.grille
        entitees["balle"] = self.balle
        
        sortie = []
        for el in entitees_names :
            sortie.append(entitees[el])
        return sortie




if __name__ == "__main__" :
    fen_lab = ES_laby()
    fen_lab.lancement()


