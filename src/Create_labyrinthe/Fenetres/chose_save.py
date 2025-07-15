
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
