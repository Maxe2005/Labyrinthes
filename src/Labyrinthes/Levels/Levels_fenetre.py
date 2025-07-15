
class Niveaux_fen (tk.Toplevel) :
    def __init__(self, boss, big_boss, titre= "Informations Niveaux", color= "white") :
        tk.Toplevel.__init__(self,boss)
        self.boss = boss
        self.big_boss = big_boss
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
        self.big_boss.niveau.numero = n
        self.big_boss.niveau.niveaux()
        self.destroy()
    
    def info_niv1 (self) :
        titre = "Informations Niveau 1"
        texte = """Le Niveau 1 permet de parcourir les labyrinthes 'normalement'
c'est à dire sans aucune gène particulière.
\nLe Niveau 1 ne contient pas de Difficultées"""
        ot.Infos(self, titre, texte)
    
    def info_niv2 (self) :
        titre = "Informations Niveau 2"
        texte = """Dans le Niveau 2 les labyrinthes (qui sont les mêmes qu'au niveau 1!)
sont divisés/découpés en plusieurs morceaux. Au début, seul un morceau est visible,
puis à chaque fois que vous 'découvrez' un nouveaux morceau, il apparait.
Cependant, si vous découvrez plus de la moitié des morceaux, ils re-disparaissent !

Dans ce niveau, plus on augmente la Difficultée, plus les labyrinthes sont
divisés/découpés en plus de morceaux (et donc les morceaux sont plus petits).
A la Difficultée 1(respectivement 2 et 3), les morceaux découverts disparaissent
quand la moitiée (respectivement 1/4 et 1/8) des morceaux ont été découverts."""
        ot.Infos(self, titre, texte, pourcentage_largeur=85)
    
    def info_niv3 (self) :
        titre = "Informations Niveau 3"
        texte = """Dans le Niveau 3 les labyrinthes (qui sont les mêmes qu´au niveau 1!)
sont divisés/découpés en plusieurs morceaux. UN seul morceau est
visible : à chaque fois que vous vous déplacez vers un nouveaux
morceau, seul le morceau que vous parcourez est visible.

Dans ce niveau, plus on augmente la Difficultée,
plus les labyrinthes sont divisés/découpés en plus de
morceaux (et donc les morceaux sont plus petits)"""
        ot.Infos(self, titre, texte, pourcentage_largeur=85)
    
    def info_niv4 (self) :
        titre = "Informations Niveau 4"
        texte = """Dans le Niveau 4 les labyrinthes sont les mêmes qu'à tous les niveaux,
mais au début, aucun mur n'est visible, puis à chaque fois que vous
rentrez dans un nouveau mur, il apparait. Cependant, si vous
découvrez plus de la moitié des murs, ils re-disparaissent !

Dans ce niveau, plus on augmente la Difficultée, plus les murs disparaissent tôt :
à la Difficultée 1(respectivement 2 et 3), les murs découverts disparaissent
quand la moitiée (respectivement 1/4 et 1/8) des murs ont été découverts."""
        ot.Infos(self, titre, texte, pourcentage_largeur=80)
