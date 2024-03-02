# Créé le 10/02/23
# Dernière modification : 14/01/24
# Auteur : Maxence CHOISEL

from tkinter import*
import tkinter.messagebox as messagebox
from tkinter.simpledialog import askinteger, askstring
from math import log
from functools import partial
from random import randint
from csv import writer


class Laby_fen (Tk) :
    def __init__(self,x=1000 ,y=800 ):
        Tk.__init__(self)
        self.x = x = self.winfo_screenwidth() -200
        self.y = y = self.winfo_screenheight() -100
        self.title("The Labyrinthe")
        self.geometry (str(self.x)+"x"+str(self.y))
        self.minsize(500, 400)
        self.nb_lignes = 20
        self.nb_colones = 57
        for i in range (self.nb_colones) :
            self.grid_columnconfigure(i, weight= 1, minsize= 1/self.nb_colones*500)
        for i in range (self.nb_lignes) :
            self.grid_rowconfigure(i, weight= 1, minsize= 1/self.nb_lignes*400)
        self.canvas = Laby_canvas(self, x= x * (self.nb_colones-6)/self.nb_colones,
                                    y= y * (self.nb_lignes-1)/self.nb_lignes,
                                    param = [0,1,self.nb_colones-6,self.nb_lignes-1])
        self.grille = Laby_grille(self)
        self.init_boutons ()
        self.nb_lab = 1 # le premier Labyrinthe à afficher
        self.nombre_de_labs = len(self.grille.docu_lab) # le nombre de Labyrinthes "classiques" en tout
        self.Niveau = 1
        self.Difficultee = 1
        self.Niveau_max = False
        self.type_lab = "classique"
        self.texte_barre_principale = StringVar()
        self.texte_barre_principale.set("Début")
        self.barre_principale = Label(self, textvariable= self.texte_barre_principale)
        self.barre_principale.grid(column= 14, row= 0, columnspan= 21)
        self.bind("<Button-3>", self.redimentionner)
        self.chrono = Chrono(self)
        self.chrono.grid(column= 51, row= 0, columnspan= 6, rowspan=2)
        self.canvas.nouvelle_partie ()
            
    def init_boutons (self) :
        "Initalise et affiche tous les boutons de la fenêtre"
        self.boutons = [0]*17
        
        self.deplace = StringVar()
        self.deplace.set("Déplacement\nSec")
        self.dep = 0
        self.boutons[0] = Button (self, textvariable= self.deplace, command=self.deplacement)
        self.boutons[0].grid(column= 51, row= 16, columnspan= 6)
    
        self.boutons[1] = Button (self, text='Couleurs', command=self.canvas.couleurs)
        self.boutons[1].grid(column= 52, row= 2, columnspan= 4, sticky=EW)

        self.boutons[2] = self.button_aller_a = Button (self, text='Aller à', command=self.aller_a)
        self.button_aller_a.grid(column= 52, row= 5, columnspan= 4)
        
        self.texte_button_lab_alea = StringVar()
        self.texte_button_lab_alea.set("Labyrinthe\nAléatoire")
        self.boutons[3] = Button (self, textvariable= self.texte_button_lab_alea, command=self.type_labyrinthe)
        self.boutons[3].grid(column= 51, row= 4, columnspan= 6)
        self.boutons[4] = self.button_new_lab_alea = Button (self, text='New Lab Aléa', command=self.canvas.nouvelle_partie)
        self.button_new_lab_alea.grid_forget()
        self.boutons[5] = self.button_sauvegarder_lab_alea = Button (self, text='Sauvegarder Lab', command=self.grille.sauvegarder_lab_alea)
        self.button_sauvegarder_lab_alea.grid_forget()
        self.boutons[6] = self.button_reglages_lab_alea = Button (self, text='Réglages\nLab Aléa', command=self.grille.reglages_lab_alea)
        self.button_reglages_lab_alea.grid_forget()
        

        self.boutons[7] = Button (self, text='Suivant ->', command=self.suivant)
        self.boutons[7].grid(column= 46, row= 0, columnspan= 5,sticky=EW)
        self.boutons[8] = Button (self, text='Recommencer', command=self.recomencer)
        self.boutons[8].grid(column= 41, row= 0, columnspan= 5, sticky=EW)
        self.boutons[9] = Button (self, text='<- Précédent', command=self.precedent)
        self.boutons[9].grid(column= 36, row= 0, columnspan= 5, sticky=EW)

        self.boutons[10] = Button (self, text='Niveau Max', command=self.niveau_max)
        self.boutons[10].grid(column= 52, row= 18, columnspan= 4)
        
        self.boutons[11] = Button (self, text="->", command=self.difficulte_plus)
        self.boutons[11].grid(column= 12, row= 0, sticky=W)
        self.boutons[12] = Button (self, text="Difficultée", command=self.difficultees_fen)
        self.boutons[12].grid(column= 8, row= 0, columnspan= 4, sticky=EW)
        self.boutons[13] = Button (self, text="<-", command=self.difficulte_moins)
        self.boutons[13].grid(column= 7, row= 0, sticky=E)
        
        self.boutons[14] = Button (self, text="->", command=self.niveau_plus)
        self.boutons[14].grid(column= 5, row= 0, sticky=W)
        self.boutons[15] = Button (self, text="Niveau", command=partial(Niveaux_fen,self))
        self.boutons[15].grid(column= 2, row= 0, columnspan= 3, sticky=EW)
        self.boutons[16] = Button (self, text="<-", command=self.niveau_moins)
        self.boutons[16].grid(column= 1, row= 0, sticky=E)
 
    def redimentionner (self,event=None) :
        self.x = self.winfo_width()
        self.y = self.winfo_height()
        #text_size = int(self.winfo_width() / 140)
        text_size = int(5*log(self.winfo_width()/150))
        text_chrono_size = int(self.winfo_width() / 40)
        for bout in self.boutons :
            bout.config(font=("Verdana", text_size))
        self.barre_principale.config(font=("Verdana", text_size))
        self.chrono.label.config(font=("Arial", text_chrono_size))
        self.canvas.redimentionner()
      
    def aller_a (self) :
        "Permet d´aller directement au Labyrinthe de son choix"
        n = askinteger("Aller directement", f"Numéro du Labyrinthe (max: {self.nombre_de_labs})", parent = self, minvalue = 1, maxvalue = self.nombre_de_labs)
        if n is not(None):
            self.nb_lab = int(n)
            self.canvas.nouvelle_partie()

    def affichage_barre_principale (self) :
        if self.type_lab == "classique" :
            lab = "n° "+str(self.nb_lab)
        elif self.type_lab == "aleatoire" :
            lab = "aléatoire"
        if self.Niveau_max :
            niveau = difficultee = "max"
        else :
            niveau = self.Niveau
            if self.Niveau == 1 :
                difficultee = "0"
            else :
                difficultee = self.Difficultee
        espaces = round(self.x/self.nb_colones-14)
        self.texte_barre_principale.set(f"Labyrinthe {lab:<10}"+" "*espaces+f"Niveau : {niveau:<3}"+" "*espaces+f"Difficultée : {difficultee:<3}")
        #+" "*round(espaces/2)+str(self.canvas.balle.x)+" "+str(self.canvas.balle.y)

    def niveau_plus (self) :
        if self.Niveau_max == False :
            if self.Niveau < 4 :
                self.Niveau += 1
            else :
                self.Niveau = 1
            if not(self.niveaux()) :
                if self.Niveau == 1 :
                    self.Niveau = 4
                else :
                    self.Niveau -= 1
        else :
            self.messagebox.showinfo ('Changer de Niveau','Le Niveau est déjà au max !',icon = 'error')

    def niveau_moins (self) :
        if self.Niveau_max == False  :
            if self.Niveau == 1 :
                self.Niveau = 4
            else :
                self.Niveau -= 1
            if not(self.niveaux()) :
                if self.Niveau < 4 :
                    self.Niveau += 1
                else :
                    self.Niveau = 1
        else :
            self.messagebox.showinfo ('Changer de Niveau','Le Niveau est déjà au max !',icon = 'error')

    def niveaux (self) :
        if self.Niveau == 1 :
            self.grille.init_Partitions_lab()
        else :
            if self.Niveau == 2 :
                MsgBox = messagebox.askquestion ('Passer au Niveau 2','A partir du Niveau 2 le Labyrinthe se divise en plusieurs fragments. Dans le Niveau 2, à chaque fois que vous arriverez sur un nouveau fragment, il apparaitra et vous pourrez voir ainsi où vous allez. Mais attention !, si vous découvrez la moitié des partitions, toutes celles que vous avez découvert dissparaissent !'+" "*190+'Voulez-vous vraiment passer au Niveau 2 ?',icon = 'warning')
                if MsgBox == 'yes':
                    self.grille.init_taille_partition_par_difficultées ()
                else :
                    return False
            elif self.Niveau == 3 :
                MsgBox = messagebox.askquestion ('Passer au Niveau 3','Dans le Niveau 3 vous ne pouvez voir d´un fragment à la fois donc à chaque fois que vous arriverez sur un nouveau fragment, il apparaitra mais il sera le seul visible, tous les autres serons cachés.'+" "*180+'Voulez-vous vraiment passer au Niveau 3 ?',icon = 'warning')
                if MsgBox == 'yes':
                    self.grille.init_taille_partition_par_difficultées ()
                else :
                    return False
            elif self.Niveau == 4 :
                MsgBox = messagebox.askquestion ('Passer au Niveau 4','Dans le Niveau 4 les murs du Labyrinthe n´apparaissent que si vous les percutez ! Mais si vous en "découvez" plus de la moitié, tous ceux que vous aurez découverts disparaîtrons ! Alors attention et bon courage !'+" "*180+'Voulez-vous vraiment passer au Niveau 4 ?',icon = 'warning')
                if MsgBox == 'yes':
                    self.grille.Murs_lab = []
                    self.grille.init_taille_partition_par_difficultées ()
                    self.grille.decompte_nb_murs_dans_lab ()
                else :
                    return False
        self.canvas.refresh_lab()
        return True
    
    def niveau_max (self) :
        if self.Niveau_max == False :
            MsgBox = messagebox.askquestion ('Passer au Niveau max (impossible !!)','Dans le Niveau max tous les murs sont invisibles ! Alors bon courage !'+" "*180+'Voulez-vous vraiment passer au Niveau max ?',icon = 'warning')
            if MsgBox == 'yes':
                self.Niveau_max = True
                self.grille.Murs_lab = []
                self.canvas.balle.contours_visibles = False
                self.canvas.refresh_lab()
        else :
            self.Niveau_max = False
            if self.Niveau == 1 :
                self.grille.init_Partitions_lab ()
            else :
                if self.Niveau == 2 or self.Niveau == 3 :
                    self.grille.init_taille_partition_par_difficultées ()
                elif self.Niveau == 4 :
                    self.grille.Murs_lab = []
                    self.grille.decompte_nb_murs_dans_lab ()
            self.canvas.refresh_lab()
        return

    def difficulte_plus (self) :
        if self.Niveau_max is False :
            if self.Niveau > 1 :
                if self.Difficultee < 3 :
                    self.Difficultee += 1
                else :
                    self.Difficultee = 1
                if not(self.difficultees ()) :
                    if self.Difficultee == 1 :
                        self.Difficultee = 3
                    else :
                        self.Difficultee -= 1
            else :
                messagebox.showinfo ('Changer de difficultée','Il n´y a qu´une seule difficultée pour le niveau 1 !',icon = 'error')
        else :
            messagebox.showinfo ('Changer de difficultée','La Difficultée est déjà au max !',icon = 'error')

    def difficulte_moins (self) :
        if self.Niveau_max is False :
            if self.Niveau > 1 :
                if self.Difficultee == 1 :
                    self.Difficultee = 3
                else :
                    self.Difficultee -= 1
                if not(self.difficultees ()) :
                    if self.Difficultee < 3 :
                        self.Difficultee += 1
                    else :
                        self.Difficultee = 1
            else :
                messagebox.showinfo ('Changer de difficultée','Il n´y a qu´une seule difficultée pour le niveau 1 !',icon = 'error')
        else :
            messagebox.showinfo ('Changer de difficultée','La Difficultée est déjà au max !',icon = 'error')

    def difficultees (self) :
        if self.Difficultee == 2 :
            if self.Niveau == 2 or self.Niveau == 3 :
                MsgBox = messagebox.askquestion ('Passer à la Difficultée 2','Les Difficultés du niveau '+str(self.Niveau)+' modifient la taille des fragment (de plus petits fragments impliquent plus de fragments, donc moins de visibilité et donc une Difficultée accrue !).'+" "*120+'Voulez-vous vraiment passer à la Difficultée 2 ?',icon = 'warning')
            elif self.Niveau == 4 :
                MsgBox = messagebox.askquestion ('Passer à la Difficultée 2','La Difficultée 2 du niveau 4 supprimera tous les murs "découverts" quand seulement 1/5 des murs serons découverts ! (Attention c´est très frustrant mais vous allez y arriver !)'+" "*100+'Voulez-vous vraiment passer à la Difficultée 2 ?',icon = 'warning')
            if MsgBox != 'yes':
                return False
        elif self.Difficultee == 3 :
            if self.Niveau == 2 or self.Niveau == 3 :
                MsgBox = messagebox.askquestion ('Passer à la Difficultée 3','Les Difficultés du niveau '+str(self.Niveau)+' modifient la taille des fragment (de plus petits fragments impliquent plus de fragments, donc moins de visibilité et donc une Difficultée accrue !).'+" "*120+'Voulez-vous vraiment passer à la Difficultée 3 ?',icon = 'warning')
            elif self.Niveau == 4 :
                MsgBox = messagebox.askquestion ('Passer à la Difficultée 3','La Difficultée 3 du niveau 4 supprimera tous les murs "découverts" quand seulement 1/10 des murs serons découverts ! (Attention c´est très frustrant mais vous allez y arriver !)'+" "*100+'Voulez-vous vraiment passer à la Difficultée 3 ?',icon = 'warning')
            if MsgBox != 'yes':
                return False
        self.grille.init_taille_partition_par_difficultées ()
        self.canvas.refresh_lab()
        return True

    def deplacement (self) :
        if self.canvas.balle.dep == 0 :
            self.deplace.set("Déplacement\nLisse")
            self.canvas.balle.dep = 1
        else :
            self.deplace.set("Déplacement\nSec")
            self.canvas.balle.dep = 0
    
    def recomencer (self) :
        MsgBox = messagebox.askquestion ('Recommencer','Voulez-vous vraiment recommencer ce Labyrinthe depuis le début?',icon = 'warning')
        if MsgBox == 'yes':
            self.canvas.nouvelle_partie()

    def suivant (self) :
        MsgBox = messagebox.askquestion ('Labyrinthe suivant','Voulez-vous vraiment lancer le Labyrinthe suivant (plus difficile)?')
        if MsgBox == 'yes':
            if self.nb_lab != self.nombre_de_labs :
                self.nb_lab += 1
                self.canvas.nouvelle_partie()
            else :
                messagebox.showinfo ('Labyrinthe suivant','Vous êtes déjà sur le dernier Labyrinthe',icon = 'error')

    def precedent (self) :
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

    def type_labyrinthe (self) :
        if self.type_lab == "classique" :
            self.type_lab = "aleatoire"
            self.texte_button_lab_alea.set("Labyrinthe\nClassique")
            self.button_aller_a.grid_forget()
            self.button_new_lab_alea.grid(column= 52, row= 5, columnspan= 4)
            self.button_sauvegarder_lab_alea.grid(column= 51, row= 6, columnspan= 6)
            self.button_reglages_lab_alea.grid(column= 51, row= 7, columnspan= 6)
        elif self.type_lab == "aleatoire" :
            self.type_lab = "classique"
            self.texte_button_lab_alea.set("Labyrinthe\nAléatoire")
            self.button_new_lab_alea.grid_forget()
            self.button_sauvegarder_lab_alea.grid_forget()
            self.button_reglages_lab_alea.grid_forget()
            self.button_aller_a.grid(column= 52, row= 5, columnspan= 4)
        self.canvas.nouvelle_partie()

    def difficultees_fen (self) :
        return


class Niveaux_fen (Toplevel) :
    def __init__(self, boss=None, titre= "Informations Niveaux", color= "white") :
        Toplevel.__init__(self,boss)
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
        self.canvas = Canvas(self, width= str(self.canvas_x), height= str(self.canvas_y), bg=self.color_canvas)
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
        Button (self, text='Go', command=partial(self.go_niv,1)).grid(column= 1, row= 0)
        Button (self, text='Go', command=partial(self.go_niv,2)).grid(column= 1, row= 1)
        Button (self, text='Go', command=partial(self.go_niv,3)).grid(column= 1, row= 2)
        Button (self, text='Go', command=partial(self.go_niv,4)).grid(column= 1, row= 3)
        
        Button (self, text='Infos', command=self.info_niv1).grid(column= 2, row= 0)
        Button (self, text='Infos', command=self.info_niv2).grid(column= 2, row= 1)
        Button (self, text='Infos', command=self.info_niv3).grid(column= 2, row= 2)
        Button (self, text='Infos', command=self.info_niv4).grid(column= 2, row= 3)

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

        
class Infos (Toplevel) :
    def __init__(self, boss=None, x=400, y=200, titre="test", texte=["test"],
                positions=(2/10), pos_max=(9/10,9/10), police="arial", color="white") :
        Toplevel.__init__(self,boss)
        self.boss = boss
        self.canvas_x = self.x = x
        self.canvas_y = self.y = y
        self.resizable(False, False)
        self.color_canvas = color
        self.title(titre)
        self.geometry (f"{self.x}x{self.y}")
        self.canvas = Canvas(self, width= str(self.canvas_x), height= str(self.canvas_y), bg=self.color_canvas)
        self.canvas.pack()
        for i in range (len(texte)) :
            self.canvas.create_text(self.canvas_x/2, round(self.canvas_y*positions[i]), text= texte[i], font= police)
        self.canvas.create_text(self.canvas_x*pos_max[0], self.canvas_y*pos_max[1], text= "Max", font= police)
        self.mainloop()
    
    
class Laby_canvas (Canvas) :
    "Canvas d´affichage du labyrinthe"
    def __init__(self, boss=None, x=700, y=500, param=[0,1,10,7]) :
        Canvas.__init__(self)
        self.boss = boss
        """
        self.couleur_mode = "white"
        self.color_canvas = "white"
        self.color_grille = "black"
        self.color_balle = "blue"
        self.color_balle_out = "black"
        """
        self.couleur_mode = "black"
        self.color_canvas = "black"
        self.color_grille = "white"
        self.color_balle = "red"
        self.color_balle_out = "white"
        #"""
        self.configure(width=x, height=y, bg=self.color_canvas)
        self.x = x 
        self.y = y
        self.grid(column= param[0], row= param[1], columnspan= param[2], rowspan= param[3], sticky=NSEW)
        self.balle = Laby_balle(self)
        
    def nouvelle_partie (self) :
        self.boss.grille.init_lab()
        self.delete("all")
        self.taille_auto ()
        self.origines ()
        self.balle.init()
        self.trace_grille ()
        self.boss.affichage_barre_principale ()
        self.balle.init_var ()
        
    def taille_auto (self) :
        "Calcule la taille en pixel d'un coté des cases carré à partir de la hauteur h et le la longeur l de la grille de définition"
        if self.y / self.boss.grille.y < self.x / self.boss.grille.x :
            self.taille = self.y / (self.boss.grille.y+1)
        else :
            self.taille = self.x / (self.boss.grille.x+1)

    def origines (self) :
        "Calcule et renvoi sous forme de tuple les origines en x et y (en haut à gauche du canvas)"
        self.origine_x = (self.x - (self.taille * (self.boss.grille.x-1))) / 2
        self.origine_y = (self.y - (self.taille * (self.boss.grille.y-1))) / 2
        assert self.origine_x > 0 and self.origine_y > 0

    def trace_grille (self) :
        "Trace avec Tkinter un quadrillage de la grille g"
        if self.boss.Niveau == 4 :
            for el in self.boss.grille.Murs_lab :
                if el[2] == "1" :
                    self.barre_horizontale (self.origine_x + el[0]*self.taille, self.origine_y + el[1]*self.taille, self.taille, self.color_grille)
                if el[2] == "2" :
                    self.barre_verticale (self.origine_x + el[0]*self.taille, self.origine_y + el[1]*self.taille, self.taille, self.color_grille)
        elif self.boss.Niveau_max == False :
            for el in self.boss.grille.Partitions_lab :
                for y in range (el[0][1],el[1][1]) :
                    for x in range (el[0][0],el[1][0]) :
                        if self.boss.grille.lab[y][x] == "1" or self.boss.grille.lab[y][x] == "3" :
                            self.barre_horizontale (self.origine_x + x*self.taille, self.origine_y + y*self.taille, self.taille, self.color_grille)
                        if self.boss.grille.lab[y][x] == "2" or self.boss.grille.lab[y][x] == "3" :
                            self.barre_verticale (self.origine_x + x*self.taille, self.origine_y + y*self.taille, self.taille, self.color_grille)
        if self.boss.Niveau > 1 and self.boss.Niveau_max == False :
            self.trace_contours_lab ()

    def trace_contours_lab (self) :
        self.create_rectangle (self.origine_x,self.origine_y,self.origine_x+self.taille*(self.boss.grille.x-1),self.origine_y+self.taille*(self.boss.grille.y-1), outline= self.color_grille)
        if self.boss.grille.sortie_lab[0] == self.boss.grille.x-1 :
            self.barre_verticale (self.origine_x + self.taille * self.boss.grille.sortie_lab[0], self.origine_y + self.taille * self.boss.grille.sortie_lab[1], self.taille, self.color_canvas)
        if self.boss.grille.sortie_lab[0] == -1 :
            self.barre_verticale (self.origine_x, self.origine_y+self.taille*self.boss.grille.sortie_lab[1], self.taille, self.color_canvas)
        if self.boss.grille.sortie_lab[1] == self.boss.grille.y-1 :
            self.barre_horizontale (self.origine_x+self.taille*self.boss.grille.sortie_lab[0], self.origine_y+self.taille*self.boss.grille.sortie_lab[1], self.taille, self.color_canvas)
        if self.boss.grille.sortie_lab[1] == -1 :
            self.barre_horizontale (self.origine_x+self.taille*self.boss.grille.sortie_lab[0], self.origine_y, self.taille, self.color_canvas)

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
        self.boss.affichage_barre_principale ()
        return
     
    def couleurs (self) :
        if self.couleur_mode == "black" :
            self["bg"] = "white"
            self.color_grille = "black"
            self.color_balle = "blue"
            self.color_balle_out = "black"
            self.couleur_mode = "white"
        elif self.couleur_mode == "white" :
            self["bg"] = "black"
            self.color_grille = "white"
            self.color_balle = "red"
            self.color_balle_out = "white"
            self.couleur_mode = "black"
        self.refresh_lab()

    def redimentionner (self) :
        self.x = self.boss.x * (self.boss.nb_colones-6)/self.boss.nb_colones
        self.y = self.boss.y * (self.boss.nb_lignes-1)/self.boss.nb_lignes
        self.taille_auto ()
        self.origines ()
        self.refresh_lab ()
    

class Laby_grille () :
    "Effectue diverses opérations sur la grille contenant le labyrinthe"
    def __init__(self, boss=None, lab=[[]]) :
        self.boss = boss
        self.docu_lab = self.ouvrir_doc("Labyrinthes classiques/#docu lab")
        self.lab = lab
        self.x = len(lab[0])
        self.y = len(lab)
        self.Partitions_lab = []
    
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

    def init_lab (self) :
        "Initialise le Labyrinthe à afficher"
        if self.boss.type_lab == "classique" :
            self.lab = self.ouvrir_lab (self.boss.nb_lab)
        elif self.boss.type_lab == "aleatoire" :
            x = 40
            y = 25
            self.entrée_lab = [0,0]
            self.lab = self.generateur_lab(x,y)
        self.x = len(self.lab[0])
        self.y = len(self.lab)
        self.boss.canvas.balle.def_position(self.entrée_lab[0],self.entrée_lab[1])
        if self.boss.Niveau == 1 :
            self.init_Partitions_lab()
        elif self.boss.Niveau == 2 or self.boss.Niveau == 3 :
            self.init_taille_partition_par_difficultées ()
        elif self.boss.Niveau == 4 :
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
        nom = "Labyrinthes classiques/"+self.docu_lab[numéro_du_lab-1]
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
        if self.boss.Difficultee == 1 :
            taille_x = taille_y = petit_cote//2
        elif self.boss.Difficultee == 2 :
            taille_x = taille_y = grand_cote//4
        elif self.boss.Difficultee == 3 :
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
        x = self.boss.canvas.balle.x // self.taille_partition_x
        y = self.boss.canvas.balle.y // self.taille_partition_y
        if self.x % self.taille_partition_x < self.taille_partition_x/2 and x >= self.x // self.taille_partition_x :
            x -= 1
        if self.y % self.taille_partition_y < self.taille_partition_y/2 and y >= self.y // self.taille_partition_y :
            y -= 1
        if x != self.position_joueur_back_lab_x or y != self.position_joueur_back_lab_y :
            if self.boss.Niveau == 2 and self.back_lab_partition_grille_position_joueur[y][x] == False :
                count = 1
                for el in self.back_lab_partition_grille_position_joueur :
                    for i in el :
                        if i :
                            count += 1
                self.Partitions_lab = [self.back_lab_partition_grille[y][x]]
                lab_xx = len(self.back_lab_partition_grille_position_joueur[0])
                lab_yy = len(self.back_lab_partition_grille_position_joueur)
                if count > round(lab_xx * lab_yy / (self.boss.Difficultee+1)) :
                    self.back_lab_partition_grille_position_joueur = []
                    for i in range (lab_yy) :
                        a = []
                        for e in range (lab_xx) :
                            a.append(False)
                        self.back_lab_partition_grille_position_joueur.append(a)
                    self.boss.canvas.refresh_lab ()
                self.back_lab_partition_grille_position_joueur[y][x] = True
                self.boss.canvas.trace_grille()
            elif self.boss.Niveau == 3 :
                self.back_lab_partition_grille_position_joueur[self.position_joueur_back_lab_y][self.position_joueur_back_lab_x] = False
                self.back_lab_partition_grille_position_joueur[y][x] = True
                self.Partitions_lab = [self.back_lab_partition_grille[y][x]]
                self.boss.canvas.refresh_lab ()
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
        if self.boss.Difficultee == 1 :
            limite = self.nb_murs_dans_lab / 2
            message = "la moitié"
        elif self.boss.Difficultee == 2 :
            limite = self.nb_murs_dans_lab /5
            message = "1/5"
        elif self.boss.Difficultee == 3 :
            limite = self.nb_murs_dans_lab /10
            message = "1/10"
        if len(self.Murs_lab) >= limite :
            self.Murs_lab = []
            messagebox.showinfo ("Dommage !","Vous avez découvert plus de "+message+" des murs, ils vont donc tous disparaître !", icon = "error")
            self.boss.canvas.refresh_lab ()
        return
    
    def reglages_lab_alea (self) :
        return


class Laby_balle () :
    "La balle (le joueur) qui se déplace dans le labyrinthe"
    def __init__(self, boss=None, x=0, y=0) :
        self.boss = boss
        self.x = x
        self.y = y
        self.decoupe_dep = 5
        self.vitesse = 50
        self.dep = 0
        self.boss.boss.bind("<Up>", self.haut)
        self.boss.boss.bind("<Down>", self.bas)
        self.boss.boss.bind("<Right>", self.droite)
        self.boss.boss.bind("<Left>", self.gauche)
        
        self.boss.boss.bind("<o>", self.haut)
        self.boss.boss.bind("<l>", self.bas)
        self.boss.boss.bind("<m>", self.droite)
        self.boss.boss.bind("<k>", self.gauche)
        
    def init (self) :
        bordure = 1/10 *self.boss.taille
        o_x = round(self.boss.origine_x + bordure)
        o_y = round(self.boss.origine_y + bordure)
        pos_x = o_x + self.x * self.boss.taille
        pos_y = o_y + self.y * self.boss.taille
        t_balle = round(self.boss.taille-2*bordure)
        self.balle = self.boss.create_oval (pos_x, pos_y, pos_x+t_balle, pos_y+t_balle,  fill= self.boss.color_balle, outline= self.boss.color_balle_out)
        self.boss.lift(self.balle)
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
            self.boss.move(self.balle, x*self.boss.taille, y*self.boss.taille)
        self.y += y
        self.x += x
        if self.boss.boss.Niveau_max and self.contours_visibles :
            self.boss.refresh_lab ()
            self.contours_visibles = False
        #else :
            #self.boss.boss.affichage_barre_principale ()
        if self.boss.boss.Niveau > 1 :
            self.boss.boss.grille.Position_joueur_sur_back_lab_partition ()
        self.boss.boss.win()
        self.ou_aller()
        return

    def ou_aller (self) :
        "Rentre dans les variables booleenes les possiblilités de mouvement de la balle"
        if self.y >= 0 :
            self.aller_haut = self.boss.boss.grille.lab[self.y][self.x] != "1" and self.boss.boss.grille.lab[self.y][self.x] != "3"
        if self.y < self.boss.boss.grille.y -1 : # Pour éviter l´erreur out of range avec self.y+1
            self.aller_bas = self.boss.boss.grille.lab[self.y+1][self.x] != "1" and self.boss.boss.grille.lab[self.y+1][self.x] != "3"
        if self.x < self.boss.boss.grille.x -1:
            self.aller_droite = self.boss.boss.grille.lab[self.y][self.x+1] != "2" and self.boss.boss.grille.lab[self.y][self.x+1] != "3"
        if self.x >= 0 :
            self.aller_gauche = self.boss.boss.grille.lab[self.y][self.x] != "2" and self.boss.boss.grille.lab[self.y][self.x] != "3"
        return

    def fonction_dep (self,x=0,y=0,interne=False) :
        if interne :
            if self.en_deplacement :
                #c = self.boss.coords(self.balle)
                if self.count_x % self.decoupe_dep == 0 and self.count_y % self.decoupe_dep == 0 :
                    self.mouve(x, y, deplacement_reel= False)
                    if (self.next_dir == (0,1) and self.aller_bas) or \
                         (self.next_dir == (0,-1) and self.aller_haut) or \
                         (self.next_dir == (1,0) and self.aller_droite) or \
                         (self.next_dir == (-1,0) and self.aller_gauche) :
                        self.boss.move(self.balle, self.next_dir[0]*self.boss.taille/self.decoupe_dep, self.next_dir[1]*self.boss.taille/self.decoupe_dep)
                        self.count_x += self.next_dir[0]
                        self.count_y += self.next_dir[1]
                        self.boss.boss.after(self.vitesse, self.fonction_dep, self.next_dir[0], self.next_dir[1], True)
                        self.next_dir = None
                    elif ((x,y) == (0,1) and self.aller_bas) or \
                         ((x,y) == (0,-1) and self.aller_haut) or \
                         ((x,y) == (1,0) and self.aller_droite) or \
                         ((x,y) == (-1,0) and self.aller_gauche) :
                        self.boss.move(self.balle, x*self.boss.taille/self.decoupe_dep, y*self.boss.taille/self.decoupe_dep)
                        self.count_x += x
                        self.count_y += y
                        self.boss.boss.after(self.vitesse, self.fonction_dep, x, y, True)
                    else :
                        self.en_deplacement = False
                else :
                    self.boss.move(self.balle, x*self.boss.taille/self.decoupe_dep, y*self.boss.taille/self.decoupe_dep)
                    self.count_x += x
                    self.count_y += y
                    self.boss.boss.after(self.vitesse,self.fonction_dep,x,y,True)
        elif self.en_deplacement :
                self.next_dir = (x,y)
        elif ((x,y) == (0,1) and self.aller_bas) or \
             ((x,y) == (0,-1) and self.aller_haut) or \
             ((x,y) == (1,0) and self.aller_droite) or \
             ((x,y) == (-1,0) and self.aller_gauche) :
                self.en_deplacement = True
                self.boss.move(self.balle, x*self.boss.taille/self.decoupe_dep, y*self.boss.taille/self.decoupe_dep)
                self.count_x += x
                self.count_y += y
                self.boss.boss.after(self.vitesse, self.fonction_dep, x, y, True)

    def haut (self,event) :
        if self.x != self.boss.boss.grille.sortie_lab[0] or self.y != self.boss.boss.grille.sortie_lab[1] :
            if self.dep == 1 :
                self.fonction_dep (y=-1)
            if self.aller_haut :
                if self.dep == 0 :
                    self.mouve(0,-1)
            elif self.boss.boss.Niveau_max and self.y == 0 :
                self.boss.delete("all")
                self.init()
                self.boss.trace_contours_lab ()
                self.contours_visibles = True
            elif self.boss.boss.Niveau == 4 and not(self.boss.boss.Niveau_max) and self.y > 0 and not((self.x,self.y,"1") in self.boss.boss.grille.Murs_lab) :
                self.boss.boss.grille.Murs_lab.append((self.x,self.y,"1"))
                self.boss.barre_horizontale (self.boss.origine_x + self.x*self.boss.taille, self.boss.origine_y + self.y*self.boss.taille, self.boss.taille, self.boss.color_grille)
                self.boss.boss.grille.test_nb_murs_niv_4 ()

    def bas (self,event) :
        if self.x != self.boss.boss.grille.sortie_lab[0] or self.y != self.boss.boss.grille.sortie_lab[1] :
            if self.dep == 1 :
                self.fonction_dep (y=1)
            if self.aller_bas :
                if self.dep == 0 :
                    self.mouve(0,1)
            elif self.boss.boss.Niveau_max and self.y == self.boss.boss.grille.y-2 :
                self.boss.delete("all")
                self.init()
                self.boss.trace_contours_lab ()
                self.contours_visibles = True
            elif self.boss.boss.Niveau == 4 and not(self.boss.boss.Niveau_max) and self.y < self.boss.boss.grille.y-2 and not((self.x,self.y+1,"1") in self.boss.boss.grille.Murs_lab) :
                self.boss.boss.grille.Murs_lab.append((self.x,self.y+1,"1"))
                self.boss.barre_horizontale (self.boss.origine_x + self.x*self.boss.taille, self.boss.origine_y + (self.y+1)*self.boss.taille, self.boss.taille, self.boss.color_grille)
                self.boss.boss.grille.test_nb_murs_niv_4 ()
            
    def droite (self,event) :
        if self.x != self.boss.boss.grille.sortie_lab[0] or self.y != self.boss.boss.grille.sortie_lab[1] :
            if self.dep == 1 :
                self.fonction_dep (x=1)
            if self.aller_droite :
                if self.dep == 0 :
                    self.mouve(1,0)
            elif self.boss.boss.Niveau_max and self.x == self.boss.boss.grille.x-2 :
                self.boss.delete("all")
                self.init()
                self.boss.trace_contours_lab ()
                self.contours_visibles = True
            elif self.boss.boss.Niveau == 4 and not(self.boss.boss.Niveau_max) and self.x < self.boss.boss.grille.x-2 and not((self.x+1,self.y,"2") in self.boss.boss.grille.Murs_lab) :
                self.boss.boss.grille.Murs_lab.append((self.x+1,self.y,"2"))
                self.boss.barre_verticale (self.boss.origine_x + (self.x+1)*self.boss.taille, self.boss.origine_y + self.y*self.boss.taille, self.boss.taille, self.boss.color_grille)
                self.boss.boss.grille.test_nb_murs_niv_4 ()
            
    def gauche (self,event) :
        if self.x != self.boss.boss.grille.sortie_lab[0] or self.y != self.boss.boss.grille.sortie_lab[1] :
            if self.dep == 1 :
                self.fonction_dep (x=-1)
            if self.aller_gauche :
                if self.dep == 0 :
                    self.mouve(-1,0)
            elif self.boss.boss.Niveau_max and self.x == 0 :
                self.boss.delete("all")
                self.init()
                self.boss.trace_contours_lab ()
                self.contours_visibles = True
            elif self.boss.boss.Niveau == 4 and not(self.boss.boss.Niveau_max) and self.x > 0 and not((self.x,self.y,"2") in self.boss.boss.grille.Murs_lab):
                self.boss.boss.grille.Murs_lab.append((self.x,self.y,"2"))
                self.boss.barre_verticale (self.boss.origine_x + self.x*self.boss.taille, self.boss.origine_y + self.y*self.boss.taille, self.boss.taille, self.boss.color_grille)
                self.boss.boss.grille.test_nb_murs_niv_4 ()
            

class Message_fin_lab (Toplevel) :

    def __init__ (self, boss=None) :
        Toplevel.__init__(self)
        self.boss = boss
        self.canvas_x = 300
        self.canvas_y = 100
        self.x = self.canvas_x + 50
        self.y = self.canvas_y + 90
        self.title("Labyrinthe Réussi !")
        self.geometry (f"{self.x}x{self.y}")
        self.canvas = Canvas(self, width= str(self.canvas_x), height= str(self.canvas_y), bg= "white")
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
        Button (self, text='Quitter', command=self.quitter).pack(side= "left")

        Button (self, text='Suivant ->', command=self.suivant).pack(side= "right") 

        Button (self, text='Recommencer', command=self.recomencer).pack(side= "right")

        Button (self, text='<- Précédent', command=self.precedent).pack(side= "right")

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


class Chrono(Frame):
    def __init__(self, boss=None, max_time=3600):
        Frame.__init__(self,boss)
        self.boss = boss
        self.time = 0
        self.max_time = max_time
        self.running = False
        self.create_widgets()
    
    def create_widgets(self):
        self.label = Label(self, text="00:00", fg="red", font=("Arial", 30))
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
        

class Boutons(Frame) :
    def __init__(self, boss=None, master=None) :
        Frame.__init__(self,boss)
        self.boss = master
        self.nb_lignes = 10
        self.grid_columnconfigure(0, weight= 1, minsize= (1-self.boss.proportion_canvas_x)*self.boss.min_x)
        for i in range (self.nb_lignes) :
            self.grid_rowconfigure(i, weight= 1, minsize= 1/self.nb_lignes*self.boss.min_y)
        
        self.items = {}
        
        self.def_bouton('Affichage :\n'+self.boss.type_affichage, self.boss.change_type_affichage, 2,\
                         nom_diminutif= 'change_affi')
        self.def_bouton('Invoquer\nCromwell', self.boss.cromwell, 3, nom_diminutif= 'cromwell')
        self.def_bouton('Se couvrir', self.boss.abriter_al, 4)
        self.def_bouton('Transformation :\nChauve-souris', self.boss.chauve_souris_al, 5,\
                         nom_diminutif= 'chauve_souris')
        self.def_bouton('Aller dans\nle Cercueil', self.boss.aller_cercueil_al, 6,\
                         nom_diminutif= 'aller_cercueil', visibilite="Caché")
        self.def_bouton('Recommencer', self.boss.recommencer, 10)

        self.init_visible_debut ()

    def init_visible_debut (self) :
        self.is_visible_debut = []
        for bout in self.items :
            if self.items[bout][2] == "Visible" :
                self.is_visible_debut.append(bout)

    def def_bouton (self, nom_affiche, effet, position, nom_diminutif=None, visibilite="Visible") :
        if nom_diminutif == None :
            nom_diminutif = nom_affiche
        self.items[nom_diminutif] = [Button (self, text=nom_affiche, command=effet), position, visibilite]
        if visibilite == "Visible" :
            self.items[nom_diminutif][0].grid(row= self.items[nom_diminutif][1])

    def redimentionner (self) :
        text_size = int(5*log(self.boss.winfo_width()/100))
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
            if not(bout in ele) :
                self.cacher(bout)
    
    def renommer (self, nom_bouton:str, new_nom_bouton:str) :
        self.items[nom_bouton][0]["text"] = new_nom_bouton

    def is_visible (self, nom_bouton:str) :
        return self.items[nom_bouton][2] == "Visible"


    
if __name__ == "__main__" :
    fen_lab = Laby_fen()
    fen_lab.mainloop()


