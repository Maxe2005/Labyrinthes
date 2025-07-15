# Created on 12/06/22
# Author : Maxence CHOISEL

from ..Outils_Tkinter import Outils as Outils
if __name__ == "__main__" :
    import Labyrinthes as Laby_parcoureur
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from functools import partial
from PIL import Image,ImageTk
from math import log
from os import path
from csv import writer


class Entite_superieure_crea () :
    def __init__(self, parcoureur_labs=None) -> None:
        if parcoureur_labs is not None :
            self.Parcoureur_labs = parcoureur_labs
            
        self.init_variables_globales()
        
        self.fenetre = Lab_fen_crea(self)
        self.grille = Lab_grille_crea(self, self.fenetre)
        self.canvas = Lab_canvas_crea(self, self.fenetre, self.grille)
        self.balle = Lab_balle_crea(self, self.fenetre, self.canvas, self.grille)
        self.fenetre.init_entitees(self.grille, self.canvas, self.balle)
        self.grille.init_entitees(self.canvas, self.balle)
        self.canvas.init_entitees(self.balle)
    
    def lancement (self) :
        self.fenetre.init_barres_boutons_et_text()
        self.canvas.init_affichage_grille()
        for i in range (3) :
            self.fenetre.after(500+(i*100), self.fenetre.redimentionner)
        self.fenetre.focus()
        for com in self.commentaires :
            self.fenetre.after(500, com.test)
        self.fenetre.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.fenetre.mainloop()
    
    def lancement_parcoureur_labs (self) :
        global Parcoureur_labs
        if __name__ == "__main__" :
            Parcoureur_labs = Laby_parcoureur.Entite_superieure(self)
            Parcoureur_labs.lancement()
        else :
            Parcoureur_labs.fenetre.lift()
            Parcoureur_labs.fenetre.focus()
    
    def init_variables_globales (self) :
        self.ouvrir_param_defaut()
        self.type_deplacement = self.parametres["dep initial"]
        self.mode_actif = ""
        self.commentaires = []
        self.reglages_fen = False
    
    def ouvrir_param_defaut (self) :
        """Télécharge les paramètres par défauts """
        self.parametres = {}
        self.parametres_parcoureur = []
        with open("Autres/Parametres_defaut.csv") as f :
            for ligne in f.readlines()[1:] :
                l = ligne.split("\n")[0].split(",")
                if l[0] == "builder" :
                    if len(l[2:]) == 1 :
                        self.parametres[l[1]] = l[2]
                    else :
                        self.parametres[l[1]] = l[2:]
                else :
                    self.parametres_parcoureur.append(ligne)
    
    def save_param_defaut (self) :
        with open("Autres/Parametres_defaut.csv", "w") as f :
            f.write("# Entitee du parametre, Nom du parametre, valeur du parametre\n")
            for param in self.parametres_parcoureur :
                f.write(param)
            for param in self.parametres :
                if type(self.parametres[param]) == list :
                    f.write("builder,"+param+","+",".join(self.parametres[param])+"\n")
                else :
                    f.write("builder,"+param+","+str(self.parametres[param])+"\n")
    
    def on_closing (self) :
        self.save_param_defaut()
        self.fenetre.destroy()
    
    def aller_a_start (self, event=None) :
        if self.mode_actif :
            if self.mode_actif == "Aller à" :
                self.fenetre.barre_de_texte.set("Le mode '"+self.mode_actif+"' à été arrêté")
                self.mode_actif = ""
                self.fenetre.after(2000, self.fenetre.refresh_barre_de_texte)
            else :
                messagebox.showinfo ('Aller à',"Impossible car le mode '"+self.mode_actif+"' est actif !",icon = 'error')
        else :
            #self.aller_a_coord()
            self.mode_actif = "Aller à"
            self.fenetre.barre_de_texte.set("Cliquez sur la case sur laquelle se rendre !")
            self.canvas.lancement_phase_1()
    
    def aller_a_end (self, x, y) :
        self.mode_actif = ""
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
        self.chose_save = Fen_chose_save(self.fenetre, self, self.grille)
        self.chose_save.mainloop()
    
    def new_lab (self, event=None) :
        self.chose_new_lab = Fen_chose_new_lab(self.fenetre, self)
        self.chose_new_lab.mainloop()
    
    def open_lab_croquis (self, selector:ttk.Combobox) :
        name_lab = selector.get()
        self.grille.ouvrir_lab(name_lab)
        self.chose_new_lab.destroy()
        self.grille.x = len(self.grille.lab[0]) - 1
        self.grille.y = len(self.grille.lab) - 1
        self.balle.def_position(self.grille.Entree[0], self.grille.Entree[1])
        self.fenetre.boutons.renommer("type deplacement", "Déplacement")
        self.def_type_deplacement("Passe")
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
        if self.mode_actif :
            if self.mode_actif == "Création de Sortie" :
                self.fenetre.barre_de_texte.set("Le mode '"+self.mode_actif+"' à été arrêté")
                self.mode_actif = ""
                self.fenetre.after(2000, self.fenetre.refresh_barre_de_texte)
            else :
                messagebox.showinfo ('Créer un mur',"Impossible car le mode '"+self.mode_actif+"' est actif !",icon = 'error')
        elif self.balle.x == self.grille.Sortie[0] and self.balle.y == self.grille.Sortie[1] :
            messagebox.showinfo ('Instaler une sortie','Impossible car vous êtes dans la sortie !',icon = 'error')
        elif self.balle.x == 0 or self.balle.x == self.grille.x-1 or self.balle.y == 0 or self.balle.y == self.grille.y-1 :
            self.mode_actif = "Création de Sortie"
            self.fenetre.barre_de_texte.set("Vous pouver créer la sortie avec les flèches")
        else :
            messagebox.showinfo ('Instaler une sortie',"Pour instaler une sortie vous devez positionner la balle à l'endroit ou sera crée la sortie c'est à dire près d'un bord !",icon = 'error')

    def sortie_end (self) :
        if  self.grille.Sortie != (self.balle.x, self.balle.y) :
            if self.grille.Sortie[0] == -1 :
                if self.grille.lab[self.grille.Sortie[1]][0] == "0" :
                    self.grille.lab[self.grille.Sortie[1]][0] = "2"
                elif self.grille.lab[self.grille.Sortie[1]][0] == "1" :
                    self.grille.lab[self.grille.Sortie[1]][0] = "3"
            elif self.grille.Sortie[1] == -1 :
                if self.grille.lab[0][self.grille.Sortie[0]] == "0" :
                    self.grille.lab[0][self.grille.Sortie[0]] = "1"
                elif self.grille.lab[0][self.grille.Sortie[0]] == "2" :
                    self.grille.lab[0][self.grille.Sortie[0]] = "3"
            elif self.grille.Sortie[0] == self.grille.x :
                self.grille.lab[self.grille.Sortie[1]][self.grille.Sortie[0]] = "2"
            elif self.grille.Sortie[1] == self.grille.y :
                self.grille.lab[self.grille.Sortie[1]][self.grille.Sortie[0]] = "1"
            self.canvas.refresh_lab()
        self.grille.Sortie = (self.balle.x, self.balle.y)
        self.fenetre.position_sortie.set("Sortie : {};{}".format(self.grille.Sortie[0],self.grille.Sortie[1]))
        self.fenetre.refresh_barre_de_texte()
        self.mode_actif = ""

    def entree (self, event=None) :
        if self.grille.Entree == "off" :
            self.grille.Entree = (self.balle.x, self.balle.y)
            self.fenetre.position_entree.set("Entrée : {};{}".format(self.grille.Entree[0],self.grille.Entree[1]))
        else :
            MsgBox = messagebox.askquestion ('Nouvelle entrée','Voulez-vous vraiment redefinir l\'entrée de votre labirinthe qui est à {};{} par {};{} ?'.format(self.grille.Entree[0],self.grille.Entree[1],self.balle.x,self.balle.y))
            if MsgBox == 'yes':
                self.grille.Entree = (self.balle.x, self.balle.y)
                self.fenetre.position_entree.set("Entrée : {};{}".format(self.grille.Entree[0],self.grille.Entree[1]))
        return

    def Change_type_deplacement (self, event=None) :
        if self.type_deplacement == "Casse" :
            self.def_type_deplacement("Passe")
        else :
            self.def_type_deplacement("Casse")

    def def_type_deplacement (self, dep, event=None) :
        if dep == "Passe" :
            self.type_deplacement = "Passe"
            self.fenetre.boutons.renommer("type deplacement", "Déplacement")
        elif dep == "Casse" :
            self.type_deplacement = "Casse"
            self.fenetre.boutons.renommer("type deplacement", "Créer")
        else :
            print("ERREUR")

    def Modification (self, event=None) :
        if self.mode_actif :
            if self.mode_actif == "Modification" :
                self.fenetre.barre_de_texte.set("Le mode '"+self.mode_actif+"' à été arrêté")
                self.mode_actif = ""
                self.fenetre.after(2000, self.fenetre.refresh_barre_de_texte)
            else :
                messagebox.showinfo ('Créer un mur',"Impossible car le mode '"+self.mode_actif+"' est actif !",icon = 'error')
        else :
            self.mode_actif = "Modification"
            self.fenetre.barre_de_texte.set("Vous pouver créer un mur avec les flèches")

    def editer_aires (self, selector:ttk.Combobox, event=None) :
        self.fenetre.focus()
        if selector.get() == "Détruire (tout vide)" :
            selector.set("Détruire")
            self.editer_aires_detruire_start()
        elif selector.get() == "Reconstruire (quadrillage)" :
            selector.set("Reconstruire")
            self.editer_aires_restorer_start()
        
    def editer_aires_detruire_start (self) :
        if self.mode_actif :
            if self.mode_actif == "Détruire Aires" :
                self.fenetre.barre_de_texte.set("Le mode '"+self.mode_actif+"' à été arrêté")
                self.mode_actif = ""
                self.fenetre.after(2000, self.fenetre.refresh_barre_de_texte)
            else :
                messagebox.showinfo ('Editer Zones : Détruire',"Impossible car le mode '"+self.mode_actif+"' est actif !",icon = 'error')
                if self.mode_actif == "Restorer Aires" :
                    self.fenetre.boutons.renommer("Editer Zones", "Reconstruire")
        else :
            self.mode_actif = "Détruire Aires"
            self.fenetre.barre_de_texte.set("Vous pouver séléctionner la zone avec le curseur")
            self.canvas.lancement_phase_1()
    
    def editer_aires_detruire_end (self, coord_1, coord_2) :
        self.mode_actif = ""
        self.fenetre.boutons.renommer("Editer Zones", "Editer Zones")
        self.grille.detruire_aire(coord_1[0], coord_1[1], coord_2[0], coord_2[1])
    
    def editer_aires_restorer_start (self) :
        if self.mode_actif :
            if self.mode_actif == "Restorer Aires" :
                self.fenetre.barre_de_texte.set("Le mode '"+self.mode_actif+"' à été arrêté")
                self.mode_actif = ""
                self.fenetre.after(2000, self.fenetre.refresh_barre_de_texte)
            else :
                messagebox.showinfo ('Editer Zones : Restorer',"Impossible car le mode '"+self.mode_actif+"' est actif !",icon = 'error')
                if self.mode_actif == "Détruire Aires" :
                    self.fenetre.boutons.renommer("Editer Zones", "Détruire")
        else :
            self.mode_actif = "Restorer Aires"
            self.fenetre.barre_de_texte.set("Vous pouver séléctionner la zone avec le curseur")
            self.canvas.lancement_phase_1()
    
    def editer_aires_restorer_end (self, coord_1, coord_2) :
        self.mode_actif = ""
        self.fenetre.boutons.renommer("Editer Zones", "Editer Zones")
        self.grille.restorer_aire(coord_1[0], coord_1[1], coord_2[0], coord_2[1])

    def infos_generales (self) :
        infos = Fen_infos_generales(self.fenetre, self)
        infos.mainloop()

    def reglages (self) :
        if self.reglages_fen :
            self.reglages_fen.lift()
            self.reglages_fen.focus()
        else :
            self.reglages_fen = Outils.Reglages(self.fenetre)
            self.reglages_fen.init_entitees (self, self.fenetre)
            self.reglages_fen.lancement([Reglages_generaux_crea], grille=self.grille, canvas=self.canvas, balle=self.balle)
            self.reglages_fen.protocol("WM_DELETE_WINDOW", self.reglages_fen_on_closing)
            self.reglages_fen.mainloop()
    
    def reglages_fen_on_closing (self) :
        self.reglages_fen.destroy()
        self.reglages_fen = False








if __name__ == "__main__" :
    lab_builder = Entite_superieure_crea()
    lab_builder.lancement()
