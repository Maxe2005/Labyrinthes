
class Reglages_apparence (ot.Base_Reglages) :
    def __init__ (self, boss) :
        ot.Base_Reglages.__init__(self, boss, "Apparence Générale")
    
    def init_entitees (self) :
        entitees = self.big_boss.get_extra_entitees(["grille", "canvas", "balle"])
        self.grille = entitees[0]
        self.canvas = entitees[1]
        self.balle = entitees[2]
    
    def lancement (self) :
        ot.Base_Reglages.lancement(self, "Réglages apparence générale")
        
        self.initial_couleur_mode(1)
        self.logo(2)
    
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
        self.open_image(self.big_boss.parametres["logo parcoureur"])
        
        choix_logo_et_titre = tk.Label(logo)
        choix_logo_et_titre.grid(column=0, row=0)
        text_taille_lab = tk.Label(choix_logo_et_titre, text="Logo :", font=("Helvetica", 14))
        text_taille_lab.grid(column=0, row=0)
        
        choix_logo = tk.Frame(choix_logo_et_titre, border=10)
        choix_logo.grid(column=0, row=1)
        self.liste_nom_logos = list(self.nom_logos.keys())
        self.combobox_nom_logo = ttk.Combobox(choix_logo, values=self.liste_nom_logos, state="readonly", justify="center", width=12, height=10, takefocus=False, style="TCombobox", font=("Helvetica", 13))
        self.combobox_nom_logo.set(self.nom_logos_reverse[self.big_boss.parametres["logo parcoureur"]])
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
        with open("Idées LOGO/#Index_logos_parcoureur.csv") as f :
            for ligne in f.readlines()[1:] :
                li = ligne.split("\n")[0].split(",")
                if len(li) == 1 :
                    self.nom_logos[li[0]] = li[0]
                    self.nom_logos_reverse[li[0]] = li[0]
                elif len(li) == 2 :
                    self.nom_logos[li[1]] = li[0]
                    self.nom_logos_reverse[li[0]] = li[1]
                else :
                    print("Erreur fichier 'Index_logos_parcoureur'")
    
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
        self.big_boss.parametres["initial color mode"] = self.combobox_initial_couleur_mode.get()
        self.big_boss.parametres["logo parcoureur"] = self.nom_logos[self.combobox_nom_logo.get()]
        self.big_boss.fenetre.open_image()
