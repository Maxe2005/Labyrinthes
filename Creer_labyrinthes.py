# Created on 12/06/22
# Last modified on 11/03/24
# Author : Maxence CHOISEL

import Autres.Outils as Outils
if __name__ == "__main__" :
    import Labyrinthes_copy as Laby_parcoureur
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
            self.reglages_fen.init_entitees (self, self.fenetre, self.grille, self.canvas, self.balle)
            self.reglages_fen.lancement([Reglages_generaux_crea])
            self.reglages_fen.protocol("WM_DELETE_WINDOW", self.reglages_fen_on_closing)
            self.reglages_fen.mainloop()
    
    def reglages_fen_on_closing (self) :
        self.reglages_fen.destroy()
        self.reglages_fen = False


class Lab_fen_crea (tk.Tk) :
    def __init__ (self, big_boss, x:int = 1000, y:int = 800) :
        tk.Tk.__init__(self)
        self.big_boss = big_boss
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
        self.poids_canvas_x = 9
        self.poids_canvas_y = 9
        self.poids_barre_laterale_droite_x = 1
        self.poids_barre_principale_y = 1
        self.poids_total_x = self.poids_canvas_x + self.poids_barre_laterale_droite_x
        self.poids_total_y = self.poids_canvas_y + self.poids_barre_principale_y
        
        self.grid_columnconfigure(0, weight= self.poids_canvas_x)
        self.grid_columnconfigure(1, weight= self.poids_barre_laterale_droite_x)
        self.grid_rowconfigure(0, weight= self.poids_barre_principale_y)
        self.grid_rowconfigure(1, weight= self.poids_canvas_y)
    
    def init_barres_boutons_et_text (self) :
        self.barre_laterale_droite = tk.Frame(self)
        self.barre_laterale_droite.grid(column=1, row=0, rowspan=2, sticky=tk.NSEW)
        self.barre_laterale_droite.grid_columnconfigure(0, weight= 1)
        self.barre_laterale_droite.grid_rowconfigure(0, weight= 1)
        self.barre_laterale_droite.grid_rowconfigure(1, weight= 4)
        self.init_logo()
        self.boutons = Outils.Boutons(self.barre_laterale_droite, self.big_boss, self)
        self.init_configuration_barre_laterale_droite()
        self.boutons.grid(column=0, row=1, sticky=tk.NSEW)
        self.init_barres_text()
        self.refresh_barre_de_texte()
    
    def init_configuration_barre_laterale_droite (self) :
        """
        Définition de la configuration des boutons de la barre latérale droite
        """
        self.boutons.init_grid(nb_lignes=10)
        
        self.boutons.def_bouton('Couleurs', self.canvas.couleurs, 1, commentaire="Change la couleur du canvas\n(raccourci : 'ctrl' + 'c')")
        self.bind("<Control-KeyRelease-c>", self.canvas.couleurs)
        
        self.boutons.def_bouton('Aller à', self.big_boss.aller_a_start, 4, commentaire="Permet de déplacer la balle facilement\n(raccourci : 'a')")
        self.bind("<KeyRelease-a>", self.big_boss.aller_a_start)
        
        self.frame_dep = tk.Frame(self.boutons)
        self.frame_dep.grid(row= 5)
        self.boutons.def_bouton("", self.big_boss.Change_type_deplacement, 1, nom_diminutif= 'type deplacement', boss= self.frame_dep,\
            commentaire="Permet de switcher entre deux modes de déplacement :\n\n- Mode Créer : casse les murs (raccourci : 'c')\n- Mode Déplacement : traverse les murs (raccourci : 'd')\n\nLe mode affiché sur le bouton est le mode actif.\n(raccouci pour switcher de mode : 'Espace')", commentaire_aligne_in="left")
        self.bind("<KeyRelease-space>", self.big_boss.Change_type_deplacement)
        self.bind("<KeyRelease-d>", partial(self.big_boss.def_type_deplacement, "Passe"))
        self.bind("<KeyRelease-c>", partial(self.big_boss.def_type_deplacement, "Casse"))
        self.big_boss.def_type_deplacement(self.big_boss.parametres["dep initial"])
        
        self.frame_entree = tk.Frame(self.boutons)
        self.frame_entree.grid(row= 8)
        self.boutons.def_bouton('Créer une entrée', self.big_boss.entree, 1, boss= self.frame_entree, commentaire="Permet de définir la case d'entrée\npour le parcours du labyrinthe une fois terminé\n(raccourci : 'e')")
        self.bind("<KeyRelease-e>", self.big_boss.entree)
        
        self.frame_sortie = tk.Frame(self.boutons)
        self.frame_sortie.grid(row= 9)
        self.boutons.def_bouton('Créer une sortie', self.big_boss.sortie_start, 1, boss= self.frame_sortie, commentaire="Permet de définir la sortie en cassant un mur exterieur\npour le parcours du labyrinthe une fois terminé\n(raccourci : 's')")
        self.bind("<KeyRelease-s>", self.big_boss.sortie_start)
        
        self.boutons.def_bouton('Nouveau Labyrinthe', self.big_boss.new_lab, 3, commentaire="Ouvre un formulaire pour ouvrir un croquis\nou commencer un nouveau labyrinthe\n(raccourci : 'n')")
        self.bind("<KeyRelease-n>", self.big_boss.new_lab)
        
        self.boutons.def_bouton('Sauvegarder', self.big_boss.save, 2, commentaire="Permet de sauvegarder le labyrinthe en cours d'édition\nsoit sous forme de croquis, soit\nsous forme de labyrinthe terminé\n(raccourci : 'ctrl' + 's')")
        self.bind("<Control-s>", self.big_boss.save)
        
        self.boutons.def_bouton('Modifier lab', self.big_boss.Modification, 7, commentaire="Permet de reconstruire un mur détruit\n(raccourci : 'm')")
        self.bind("<KeyRelease-m>", self.big_boss.Modification)
        
        self.boutons.def_bouton('Editer Zones', self.big_boss.editer_aires, 6, type_combobox = ["Détruire (tout vide)", "Reconstruire (quadrillage)"], commentaire="Permet d'éditer de grandes zones du labyrinthe :\n\n- Le mode Détruire permet d'effacer la zone\n- Le mode Reconstruire permet de retracer\nle quadrillage dans la zone", commentaire_aligne_in="left")
    
        self.boutons.def_bouton('Réglages', self.big_boss.reglages, 0, commentaire="Accès au réglages\n(raccourci : 'r')")
        self.bind("<KeyRelease-r>", self.big_boss.reglages)

    def init_logo (self) :
        #self.logo = tk.Label(self.big_boss.barre_laterale_droite)
        self.logo = tk.Button(self.barre_laterale_droite, command=self.big_boss.infos_generales)
        self.logo.grid(column=0, row=0)
        self.open_image()

    def open_image (self) :
        self.image = Image.open("Idées LOGO/"+self.big_boss.parametres["logo builder"])
        xx, yy = self.image.size
        ratio = xx / yy
        x_max = self.barre_laterale_droite.winfo_width()
        x = round(60/100 * x_max)
        y = round(x / ratio)
        self.image = self.image.resize((x,y))
        self.image_photo = ImageTk.PhotoImage(self.image)
        self.logo["image"] = self.image_photo

    def init_barres_text (self) :
        self.barre_de_texte = tk.StringVar()
        self.barre_de_texte.set("Début")
        self.barre_affichage_texte = tk.Label(self, textvariable= self.barre_de_texte)
        self.barre_affichage_texte.grid(column= 0, row= 0, sticky=tk.NSEW)

        self.position_sortie = tk.StringVar()
        self.position_sortie.set("Sortie")
        self.affichage_position_sortie = tk.Label(self.frame_sortie, textvariable= self.position_sortie)
        self.affichage_position_sortie.grid(column= 0, row= 0)

        self.position_entree = tk.StringVar()
        self.position_entree.set("Entrée")
        self.affichage_position_entree = tk.Label(self.frame_entree, textvariable= self.position_entree)
        self.affichage_position_entree.grid(column= 0, row= 0)
        
        self.affichage_mode = tk.Label(self.frame_dep, text= "Mode :")
        self.affichage_mode.grid(column= 0, row= 0)
        
    def refresh_barre_de_texte (self) :
        self.barre_de_texte.set("Labirinthe  "+self.big_boss.lab_name+" "*10+str(self.balle.x)+" "+str(self.balle.y))

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


class Lab_grille_crea () :
    def __init__(self, big_boss, fenetre, x=10, y=10) :
        self.big_boss = big_boss
        self.fenetre = fenetre
        self.Entree = "off"
        self.Sortie = "off"
        self.coutours_compris_dans_detruire_aire = False
        self.coutours_compris_dans_restorer_aire = False
        self.init_lab(x,y)
    
    def init_entitees (self, canvas, balle) :
        self.canvas = canvas
        self.balle = balle
    
    def init_lab (self, x,y, nom_lab:str = "<sans-nom>") :
        """
        Initialise le labirinthe à afficher
        """
        self.lab = self.grille_pleine (x,y)
        self.big_boss.lab_name = nom_lab
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
            self.big_boss.lab_name = nom_du_lab
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
                ecrire = writer (f, delimiter = ",", lineterminator = "\n")
                if i == -2 :
                    ecrire.writerow (entrée)
                elif i == -1 :
                    ecrire.writerow (sortie)
                else :
                    ecrire.writerow (lab[i])

    def detruire_aire (self, x1, y1, x2, y2) :
        if x1 > x2 :
            x1, x2 = x2, x1
        if y1 > y2 :
            y1, y2 = y2, y1
        if not(self.coutours_compris_dans_detruire_aire) :
            x1 += 1
            y1 += 1
        for y in range(y1, y2+1) :
            for x in range(x1, x2+1) :
                self.lab[y][x] = "0"
        if self.coutours_compris_dans_detruire_aire :
            if y2 + 1 < self.y :
                for x in range (x1, x2+1) :
                    if self.lab[y2+1][x] == "3" :
                        self.lab[y2+1][x] = "2"
                    elif self.lab[y2+1][x] == "1" :
                        self.lab[y2+1][x] = "0"
            if x2 + 1 < self.x :
                for y in range (y1, y2+1) :
                    if self.lab[y][x2+1] == "3" :
                        self.lab[y][x2+1] = "1"
                    elif self.lab[y][x2+1] == "2" :
                        self.lab[y][x2+1] = "0"
        else :
            for x in range (x1, x2+1) :
                if self.lab[y1-1][x] == "3" :
                    self.lab[y1-1][x] = "1"
                elif self.lab[y1-1][x] == "2" :
                    self.lab[y1-1][x] = "0"
            for y in range (y1, y2+1) :
                if self.lab[y][x1-1] == "3" :
                    self.lab[y][x1-1] = "2"
                elif self.lab[y][x1-1] == "1" :
                    self.lab[y][x1-1] = "0"
    
    def restorer_aire (self, x1, y1, x2, y2) :
        if x1 > x2 :
            x1, x2 = x2, x1
        if y1 > y2 :
            y1, y2 = y2, y1
        if not(self.coutours_compris_dans_restorer_aire) :
            y1 += 1
            x1 += 1
        for y in range(y1, y2+1) :
            for x in range(x1, x2+1) :
                self.lab[y][x] = "3"
        if self.coutours_compris_dans_restorer_aire :
            for x in range (x1, x2+1) :
                if self.lab[y2+1][x] == "0" :
                    self.lab[y2+1][x] = "1"
                elif self.lab[y2+1][x] == "2" :
                    self.lab[y2+1][x] = "3"
            for y in range (y1, y2+1) :
                if self.lab[y][x2+1] == "0" :
                    self.lab[y][x2+1] = "2"
                elif self.lab[y][x2+1] == "1" :
                    self.lab[y][x2+1] = "3"
        else :
            for x in range (x1, x2+1) :
                if self.lab[y1-1][x] == "0" :
                    self.lab[y1-1][x] = "2"
                elif self.lab[y1-1][x] == "1" :
                    self.lab[y1-1][x] = "3"
            for y in range (y1, y2+1) :
                if self.lab[y][x1-1] == "0" :
                    self.lab[y][x1-1] = "1"
                elif self.lab[y][x1-1] == "2" :
                    self.lab[y][x1-1] = "3"


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



class Fen_chose_new_lab (tk.Toplevel) :
    def __init__ (self, boss, big_boss) :
        tk.Toplevel.__init__(self, boss)
        self.big_boss = big_boss
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
        
        self.init_lab_croquis()
        self.init_new_lab()
        
        self.resizable(False, False)
        self.focus_set()
    
    def init_premier_choix (self) :
        self.partie_premier_choix = tk.Frame(self, border=10)
        text = tk.Text(self.partie_premier_choix, wrap= tk.WORD, width=25, height=3, padx=50, pady=20, font=("Helvetica", 15))
        text.insert(0.1, "Voulez-vous ouvrir un Croquis déjà existant ou voulez-vous créer un nouveau Labirinthe ?")
        text['state'] = 'disabled'
        text.grid(column=0, row=0, columnspan=2)
        
        bouton_2 = tk.Button (self.partie_premier_choix, text="Croquis", padx=20, pady=10, font=("Helvetica", 13), bg="green", fg="white", command=self.lab_croquis)
        bouton_2.grid(column=0, row=1)
        bouton_1 = tk.Button (self.partie_premier_choix, text="Nouveau", padx=20, pady=10, font=("Helvetica", 13), bg="blue", fg="white", command=self.new_lab)
        bouton_1.grid(column=1, row=1)
    
    def ajout_separation (self) :
        separation = tk.Text(self, bg="grey", pady=5, height=1, font=("Helvetica", 1))
        separation['state'] = 'disabled'
        separation.grid(column=0, row=1, sticky=tk.NSEW)
        self.is_separation = True
    
    def lab_croquis (self) :
        if self.is_init_new_lab :
            self.partie_init_new_lab.grid_forget()
            self.is_init_new_lab = False
        if not(self.is_open_lab_croquis) :
            if not(self.is_separation) :
                self.ajout_separation()
            self.partie_open_lab_croquis.grid(column=0, row=2, sticky=tk.NSEW)
            self.is_open_lab_croquis = True
    
    def init_lab_croquis (self) :
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
            command=partial(self.big_boss.open_lab_croquis, liste), bg="green", fg="white")
        self.bouton_go_croquis.grid(column=0, row=2)
    
    def new_lab (self) :
        if self.is_open_lab_croquis :
            self.partie_open_lab_croquis.grid_forget()
            self.is_open_lab_croquis = False
        if not(self.is_init_new_lab) :
            if not(self.is_separation) :
                self.ajout_separation()
            self.partie_init_new_lab.grid(column=0, row=2, sticky=tk.NSEW)
            self.is_init_new_lab = True
    
    def init_new_lab (self) :
        self.partie_init_new_lab = tk.Frame(self, border=10)
        text_init_new_lab = tk.Text(self.partie_init_new_lab, wrap= tk.WORD, width=25, height=3, padx=50, pady=20, font=("Helvetica", 15))
        text_init_new_lab.insert(0.1, "Entrez le nombre de colones et de lignes de votre nouveau labyrinthe :")
        text_init_new_lab['state'] = 'disabled'
        text_init_new_lab.grid(column=0, row=0, columnspan=2, sticky=tk.NSEW)
        
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
            command=partial(self.big_boss.init_new_lab, valeur_largeur, valeur_hauteur, self.nb_colones_min, self.nb_colones_max, self.nb_lignes_min, self.nb_lignes_max, nom_lab))
        self.bouton_go_new_lab.grid(column=0, row=3, columnspan=2)

class Fen_chose_save (tk.Toplevel) :
    def __init__ (self, boss, big_boss, grille) :
        tk.Toplevel.__init__(self, boss)
        self.big_boss = big_boss
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
        self.nom_lab.insert(0,self.big_boss.lab_name)
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
        text.insert(0.1, "Bienvenu dans le Constructeur de Labyrinthes !\n\n\nC'est ici que vous pouvez créer vos propres labyrinthes puis les essayer dans le parcoureur de labyrinthes.")
        text['state'] = 'disabled'
        text.grid(column=0, row=0, sticky=tk.NSEW)
        text.tag_add("titre", "1.0", "1.46")
        text.tag_config("titre", foreground="red", font=("Helvetica", 20), justify='center')
        
        
        bouton_1 = tk.Button (self, text="Ouvrir le Parcoureur de Labyrinthes", padx=20, pady=10, font=("Helvetica", 13), bg="blue", fg= "white", \
            command=self.big_boss.lancement_parcoureur_labs)
        bouton_1.configure(state = 'disabled', bg="grey")
        bouton_1.grid(column=0, row=1)


class Reglages_generaux_crea (Outils.Base_Reglages) :
    def __init__ (self, boss, big_boss) :
        Outils.Base_Reglages.__init__(self, boss, big_boss, "Généraux")
    
    def lancement (self) :
        Outils.Base_Reglages.lancement(self, "Réglages Généraux")
        
        self.initial_type_deplacement(1)
        self.initial_couleur_mode(2)
        self.logo(3)
    
    def initial_type_deplacement (self, position) :
        type_dep = tk.Frame(self, pady=20)
        type_dep.grid(column=0, row=position, sticky=tk.NSEW)
        type_dep.grid_columnconfigure(0, weight= 1)
        type_dep.grid_columnconfigure(1, weight= 1)
        
        text = tk.Label(type_dep, text="Type de déplacement initial :", font=("Helvetica", 13))
        text.grid(column=0, row=0)
        
        self.type_dep = {"Casser murs (Créer)":"Casse", "Déplacement":"Passe"}
        type_dep_reverse = {}
        for el in self.type_dep :
            type_dep_reverse[self.type_dep[el]] = el
        nom_types_dep = list(self.type_dep.keys())
        self.combobox_type_dep = ttk.Combobox(type_dep, values=nom_types_dep, state="readonly", justify="center", width=20, height=2, takefocus=False, style="TCombobox", font=("Helvetica", 12))
        self.combobox_type_dep.set(type_dep_reverse[self.big_boss.parametres["dep initial"]])
        self.combobox_type_dep.grid(column=1, row=0)
    
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
    
    def logo (self, position) :
        logo = tk.Frame(self, border=10)
        logo.grid(column=0, row=position, sticky=tk.NSEW)
        logo.grid_columnconfigure(0, weight= 1)
        logo.grid_columnconfigure(1, weight= 1)
        logo.grid_rowconfigure(0, weight= 1)
        logo.grid_rowconfigure(1, weight= 1)
        
        self.ouvrir_nom_logos()
        self.label_image = tk.Label(logo, font=("Helvetica", 14))
        self.label_image.grid(column=1, row=0, rowspan=2)
        self.open_image(self.big_boss.parametres["logo builder"])
        
        choix_logo_et_titre = tk.Label(logo)
        choix_logo_et_titre.grid(column=0, row=0)
        text_taille_lab = tk.Label(choix_logo_et_titre, text="Logo :", font=("Helvetica", 14))
        text_taille_lab.grid(column=0, row=0)
        
        choix_logo = tk.Frame(choix_logo_et_titre, border=10)
        choix_logo.grid(column=0, row=1)
        self.liste_nom_logos = list(self.nom_logos.keys())
        self.combobox_nom_logo = ttk.Combobox(choix_logo, values=self.liste_nom_logos, state="readonly", justify="center", width=15, height=10, takefocus=False, style="TCombobox", font=("Helvetica", 13))
        self.combobox_nom_logo.set(self.nom_logos_reverse[self.big_boss.parametres["logo builder"]])
        self.combobox_nom_logo.bind("<<ComboboxSelected>>", self.change_visuel_logo)
        self.combobox_nom_logo.grid(column=1, row=0)
        bouton_moins = tk.Button(choix_logo, text="<-", command=self.logo_moins)
        bouton_moins.grid(column=0, row=0)
        bouton_plus = tk.Button(choix_logo, text="->", command=self.logo_plus)
        bouton_plus.grid(column=3, row=0)
    
    def change_visuel_logo (self, event=None, nom_logo=None) :
        if nom_logo is None :
            nom_logo = self.combobox_nom_logo.get()
        self.open_image(self.nom_logos[nom_logo])
        self.combobox_nom_logo.set(nom_logo)
    
    def logo_moins (self) :
        index = self.liste_nom_logos.index(self.combobox_nom_logo.get())
        self.change_visuel_logo(nom_logo=self.liste_nom_logos[(index-1) % len(self.liste_nom_logos)])
    
    def logo_plus (self) :
        index = self.liste_nom_logos.index(self.combobox_nom_logo.get())
        self.change_visuel_logo(nom_logo=self.liste_nom_logos[(index+1) % len(self.liste_nom_logos)])
    
    def ouvrir_nom_logos (self) :
        """Télécharge les nom des logos possibles"""
        self.nom_logos = {}
        self.nom_logos_reverse = {}
        with open("Idées LOGO/#Index_logos_builder.csv") as f :
            for ligne in f.readlines()[1:] :
                l = ligne.split("\n")[0].split(",")
                if len(l) == 1 :
                    self.nom_logos[l[0]] = l[0]
                    self.nom_logos_reverse[l[0]] = l[0]
                elif len(l) == 2 :
                    self.nom_logos[l[1]] = l[0]
                    self.nom_logos_reverse[l[0]] = l[1]
                else :
                    print("Erreur fichier 'Index_logos_builder'")
    
    def open_image (self, nom) :
        self.image = Image.open("Idées LOGO/"+nom)
        xx, yy = self.image.size
        ratio = xx / yy
        x_max = 200
        x = round(70/100 * x_max)
        y = round(x / ratio)
        self.image = self.image.resize((x,y))
        self.image_photo = ImageTk.PhotoImage(self.image)
        self.label_image["image"] = self.image_photo
    
    def appliquer_modifications (self) :
        self.big_boss.parametres["dep initial"] = self.type_dep[self.combobox_type_dep.get()]
        self.big_boss.parametres["initial color mode"] = self.combobox_initial_couleur_mode.get()
        self.big_boss.parametres["logo builder"] = self.nom_logos[self.combobox_nom_logo.get()]
        self.big_boss.fenetre.open_image()



if __name__ == "__main__" :
    lab_builder = Entite_superieure_crea()
    lab_builder.lancement()
