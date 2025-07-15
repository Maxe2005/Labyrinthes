
class Message_fin_lab (tk.Toplevel) :
    def __init__ (self, fenetre, grille, big_boss, police:str = "arial", taille_police:int = 13) :
        tk.Toplevel.__init__(self, fenetre, border=10)
        self.big_boss = big_boss
        self.fenetre = fenetre
        self.grille = grille
        self.police = police
        self.taille_police = taille_police
        
        self.title("Labyrinthe Réussi !")
        self.grid_columnconfigure(0, weight= 1)
        self.grid_rowconfigure(0, weight= 1)
        self.grid_rowconfigure(1, weight= 1)
        
        self.text = tk.Text(self, wrap= tk.WORD, width=40, height=6, padx=30, pady=30, font=(self.police, self.taille_police))
        self.init_text()
        self.text.grid(column=0, row=0, sticky=tk.NSEW)
        
        self.boutons = ot.Boutons(self, self.big_boss, self, class_comentaire=ot.Commentaire)
        self.init_boutons()
        self.boutons.grid(column=0, row=1, sticky=tk.NSEW)
        
        self.focus_set()
        self.resizable(False, False)
        self.mainloop()
    
    def init_text (self) :
        if self.big_boss.type_lab == "aleatoire" :
            titre = "Tu as réussi le Labyrinthe aléatoire n°"+str(self.grille.num_lab_alea)
        else :
            titre = "Tu as réussi le Labyrinthe n°"+str(self.grille.num_lab)
        texte = "Que fait tu maintenant ? :\npasser au suivant, "
        if self.big_boss.type_lab == "aleatoire" :
            texte += "sauvegarder ce labirinthe, "
        texte += "revenir au précédent ou refaire celui-ci ?"
        self.text.insert(1.0, titre+"\n\n", ("titre"))
        self.text.insert("end", texte, ("content"))
        self.text.tag_config('titre', font=self.police+" "+str(self.taille_police+2), justify=tk.CENTER)
        self.text.tag_config('content', justify=tk.CENTER)
    
    def init_boutons (self) :
        "Initalise et affiche dans la fenêtre fen_message_fin_lab les boutons"
        nb_boutons = 3
        if self.big_boss.type_lab == "aleatoire" :
            nb_boutons += 1
        self.boutons.init_grid(nb_colones=nb_boutons)
        
        if self.big_boss.type_lab == "aleatoire" :
            btn = self.boutons.def_bouton("Sauvegarder", self.sauvegarder, 3)
            com = btn.add_commentaire(self, "Engage le processus de sauvegarde du labyrinthe\n(raccourci : <flèche du bas>)", position_out=["B","L","R","T"])
            self.big_boss.commentaires.append(com)
            self.bind("<Down>", self.sauvegarder)
            
        if self.big_boss.type_lab == "aleatoire" :
            text_com = "Génère un nouveau labyrinthe"
        else :
            text_com = "Passage au labyrinthe suivant"
        btn = self.boutons.def_bouton("Suivant ->", self.suivant, 2)
        com = btn.add_commentaire(self, text_com+"\n(raccourci : <flèche de droite> ou <Entrée>)", position_out=["B","L","R","T"])
        self.big_boss.commentaires.append(com)
        self.bind("<Right>", self.suivant)
        self.bind("<Return>", self.suivant)
        
        self.boutons.def_bouton("Recommencer", self.recomencer, 1)
        com = btn.add_commentaire(self, "Relance ce labyrinthe \n(raccourci : <flèche du haut>)", position_out=["B","L","R","T"])
        self.big_boss.commentaires.append(com)
        self.bind("<Up>", self.recomencer)
        
        self.boutons.def_bouton("<- Précédent", self.precedent, 0)
        com = btn.add_commentaire(self, "Reviens au labyrinthe précédent\n(raccourci : <flèche de gauche>)", position_out=["B","L","R","T"])
        self.big_boss.commentaires.append(com)
        self.bind("<Left>", self.precedent)
        
        self.boutons.redimentionner(self.taille_police-2)
    
    def sauvegarder (self,event=None) :
        "Permet de recommencer le labyrinthe"
        self.grille.sauvegarder_lab_alea()
        self.destroy()
    
    def recomencer (self,event=None) :
        "Permet de recommencer le labyrinthe"
        self.big_boss.recomencer_lab()
        self.destroy()
    
    def suivant (self,event=None) :
        "Permet de passer au labyrinthe suivant"
        self.big_boss.suivant_lab()
        self.destroy()
    
    def precedent (self,event=None) :
        "Permet de revenir au labyrinthe précédent"
        self.big_boss.precedent_lab()
        self.destroy()
