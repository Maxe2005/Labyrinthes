
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
        if not(self.Niveau_max) :
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
        if not(self.Niveau_max)  :
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
                if int(self.big_boss.parametres["question confirmation passage niveau 2"]) :
                    MsgBox = messagebox.askquestion ('Passer au Niveau 2','A partir du Niveau 2 le Labyrinthe se divise en plusieurs fragments. Dans le Niveau 2, à chaque fois que vous arriverez sur un nouveau fragment, il apparaitra et vous pourrez voir ainsi où vous allez. Mais attention !, si vous découvrez la moitié des partitions, toutes celles que vous avez découvert dissparaissent !'+" "*190+'Voulez-vous vraiment passer au Niveau 2 ?',icon = 'warning')
                else :
                    MsgBox = 'yes'
                if MsgBox == 'yes':
                    self.grille.init_taille_partition_par_difficultées ()
                else :
                    return False
            elif self.numero == 3 :
                if int(self.big_boss.parametres["question confirmation passage niveau 3"]) :
                    MsgBox = messagebox.askquestion ('Passer au Niveau 3','Dans le Niveau 3 vous ne pouvez voir d´un fragment à la fois donc à chaque fois que vous arriverez sur un nouveau fragment, il apparaitra mais il sera le seul visible, tous les autres serons cachés.'+" "*180+'Voulez-vous vraiment passer au Niveau 3 ?',icon = 'warning')
                else :
                    MsgBox = 'yes'
                if MsgBox == 'yes':
                    self.grille.init_taille_partition_par_difficultées ()
                else :
                    return False
            elif self.numero == 4 :
                if int(self.big_boss.parametres["question confirmation passage niveau 4"]) :
                    MsgBox = messagebox.askquestion ('Passer au Niveau 4','Dans le Niveau 4 les murs du Labyrinthe n´apparaissent que si vous les percutez ! Mais si vous en "découvez" plus de la moitié, tous ceux que vous aurez découverts disparaîtrons ! Alors attention et bon courage !'+" "*180+'Voulez-vous vraiment passer au Niveau 4 ?',icon = 'warning')
                else :
                    MsgBox = 'yes'
                if MsgBox == 'yes':
                    self.grille.Murs_lab = []
                    self.grille.init_taille_partition_par_difficultées ()
                    self.grille.decompte_nb_murs_dans_lab ()
                else :
                    return False
        self.canvas.refresh_lab()
        return True
    
    def niveau_max (self, event=None) :
        if not(self.Niveau_max) :
            if int(self.big_boss.parametres["question confirmation passage niveau max"]) :
                MsgBox = messagebox.askquestion ('Passer au Niveau max (impossible !!)','Dans le Niveau max tous les murs sont invisibles ! Alors bon courage !'+" "*180+'Voulez-vous vraiment passer au Niveau max ?',icon = 'warning')
            else :
                MsgBox = 'yes'
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
        self.fenetre_presentation = Niveaux_fen(self.fenetre, self.big_boss)
