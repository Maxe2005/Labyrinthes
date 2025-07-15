
class Reglages_generaux (ot.Base_Reglages) :
    def __init__ (self, boss) :
        ot.Base_Reglages.__init__(self, boss, "Généraux")
    
    def init_entitees (self) :
        entitees = self.big_boss.get_extra_entitees(["grille", "canvas", "balle"])
        self.grille = entitees[0]
        self.canvas = entitees[1]
        self.balle = entitees[2]
    
    def lancement (self) :
        ot.Base_Reglages.lancement(self, "Réglages Généraux")
        
        self.initial_type_deplacement(1)
    
    def initial_type_deplacement (self, position) :
        type_dep = tk.Frame(self, pady=20)
        type_dep.grid(column=0, row=position, sticky=tk.NSEW)
        type_dep.grid_columnconfigure(0, weight= 1)
        type_dep.grid_columnconfigure(1, weight= 1)
        
        text = tk.Label(type_dep, text="Type de déplacement initial :", font=("Helvetica", 13))
        text.grid(column=0, row=0)
        
        types_dep = ["Lisse", "Sec"]
        self.combobox_type_dep = ttk.Combobox(type_dep, values=types_dep, state="readonly", justify="center", width=12, height=2, takefocus=False, style="TCombobox", font=("Helvetica", 15))
        self.combobox_type_dep.set(self.big_boss.parametres["type deplacement initial"])
        self.combobox_type_dep.grid(column=1, row=0)
    
    def appliquer_modifications (self) :
        self.big_boss.parametres["type deplacement initial"] = self.combobox_type_dep.get()
