import tkinter as tk
import Creer_labyrinthes as Cl

class test (tk.Tk) :
    def __init__ (self) :
        tk.Tk.__init__(self)
        self.nb_lignes = 1
        self.nb_colones = 1
        for i in range (self.nb_colones) :
            self.grid_columnconfigure(i, weight= 1) 
        for i in range (self.nb_lignes) :
            self.grid_rowconfigure(i, weight= 1)
        
        """
        self.text = tk.Text(self, wrap= tk.WORD, width=31, height=3, padx=50, pady=20, font=("Helvetica", 15))
        self.text.insert(0.1, "Comment voulez-vous sauvegarder votre labirinthe ?\n\n- Comme un Croquis (INCOMPLET donc possibilité de le modifier plus tard)\n\n- Comme un Labyrinthe (TERMINÉ donc possibilité de l'ouvrir avec le jeu Laby)")
        self.text.grid(column=0, row=0, columnspan=2, sticky=tk.NSEW)
        """
        self.commentaires = []
        btns = Cl.Boutons(self,self,self,class_comentaire=Cl.Commentaire)
        btns.init_grid(nb_colones=2)
        btns.def_bouton("ceci est un bouton", self.affiche, 0, commentaire="Coougbeobeooerb\neigrbiebgrge")
        btns.def_bouton("bouton2", self.affiche, 1, commentaire="Coougbeobeooerb\neigrbiebgrge")
        btns.grid()
        
        self.bind("<space>",self.affiche)
    
    def affiche (self, event=None) :
        a = self.text.get(1,2)
        print(a)

teste = test()
teste.mainloop()