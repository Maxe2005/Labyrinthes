
class Fen_infos_generales (ot.Infos_generales) :
    def __init__ (self, boss, big_boss) :
        ot.Infos_generales.__init__(self, boss)
        self.big_boss = big_boss
        self.init_contenu()
    
    def init_contenu (self) :
        self.init_titre_et_texte("Bienvenu dans le Parcoureur de Labyrinthes !",\
            "C'est ici que vous pouvez jouer avec les labyrinthes dans différents modes.")
        
        bouton_1 = tk.Button (self, text="Ouvrir le Builder de Labyrinthes", padx=20, pady=10, font=("Helvetica", 13), bg="blue", fg= "white", \
            command=self.big_boss.lancement_builder_labs)
        bouton_1.configure(state = 'disabled', bg="grey")
        bouton_1.grid(column=0, row=1)
