
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
        self.fenetre_presentation = Niveaux_fen(self.fenetre, self.big_boss)
