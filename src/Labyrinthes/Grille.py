
class Laby_grille () :
    "Effectue diverses opérations sur la grille contenant le labyrinthe"
    def __init__(self, big_boss, lab=[[]]) :
        self. big_boss = big_boss
        self.docu_lab = self.ouvrir_doc("Labyrinthes_classiques/#_Doc_index.csv")
        self.lab = lab
        self.x = len(lab[0])
        self.y = len(lab)
        self.Partitions_lab = []
        self.num_lab = 1 # le premier Labyrinthe à afficher
        self.nombre_de_labs = len(self.docu_lab) # le nombre de Labyrinthes "classiques" en tout
        self.num_lab_alea = 0
        self.nombre_de_lab_alea = 0
        self.labs_alea = []
        self.init_variables()
    
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
    
    def init_entitees (self, fenetre, canvas, balle) :
        self. fenetre = fenetre
        self. canvas = canvas
        self. balle = balle
    
    def init_variables (self) :
        self.lab_alea_x = int(self.big_boss.parametres["lab alea x"])
        self.lab_alea_y = int(self.big_boss.parametres["lab alea y"])
        self.lab_alea_entrée_lab = [int(self.big_boss.parametres["lab alea entree x"]), int(self.big_boss.parametres["lab alea entree y"])]
        self.nb_colones_min = int(self.big_boss.parametres["nb colones min"])
        self.nb_colones_max = int(self.big_boss.parametres["nb colones max"])
        self.nb_lignes_min = int(self.big_boss.parametres["nb lignes min"])
        self.nb_lignes_max = int(self.big_boss.parametres["nb lignes max"])
    
    def init_lab (self) :
        "Initialise le Labyrinthe à afficher"
        if self.big_boss.type_lab == "classique" :
            self.lab = self.ouvrir_lab (self.num_lab)
        elif self.big_boss.type_lab == "aleatoire" :
            if self.num_lab_alea > self.nombre_de_lab_alea :
                self.nombre_de_lab_alea = self.num_lab_alea
                self.entrée_lab = self.lab_alea_entrée_lab
                self.lab = self.generateur_lab(self.lab_alea_x, self.lab_alea_y)
                self.labs_alea.append([self.entrée_lab, self.sortie_lab, copy.deepcopy(self.lab)])
            else :
                self.entrée_lab = self.labs_alea[self.num_lab_alea-1][0]
                self.sortie_lab = self.labs_alea[self.num_lab_alea-1][1]
                self.lab = self.labs_alea[self.num_lab_alea-1][2]
        self.x = len(self.lab[0])
        self.y = len(self.lab)
        self.canvas.balle.def_position(self.entrée_lab[0],self.entrée_lab[1])
        if self.big_boss.niveau.numero == 1 :
            self.init_Partitions_lab()
        elif self.big_boss.niveau.numero == 2 or self.big_boss.niveau.numero == 3 :
            self.init_taille_partition_par_difficultées ()
        elif self.big_boss.niveau.numero == 4 :
            self.Murs_lab = []
            self.decompte_nb_murs_dans_lab ()
    
    def init_Partitions_lab (self) :
        self.Partitions_lab = [((0,0),(self.x, self.y))]
    
    def grille_pleine (self,x,y) :
        "Crée une grille sans trous"
        assert type(x) and type(y) is int
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
        nom = "Labyrinthes_classiques/"+self.docu_lab[numéro_du_lab-1]
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
        if self.big_boss.difficultee.numero == 1 :
            taille_x = taille_y = petit_cote//2
        elif self.big_boss.difficultee.numero == 2 :
            taille_x = taille_y = grand_cote//4
        elif self.big_boss.difficultee.numero == 3 :
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
        x = self.canvas.balle.x // self.taille_partition_x
        y = self.canvas.balle.y // self.taille_partition_y
        if self.x % self.taille_partition_x < self.taille_partition_x/2 and x >= self.x // self.taille_partition_x :
            x -= 1
        if self.y % self.taille_partition_y < self.taille_partition_y/2 and y >= self.y // self.taille_partition_y :
            y -= 1
        if x != self.position_joueur_back_lab_x or y != self.position_joueur_back_lab_y :
            if self.big_boss.niveau.numero == 2 and not(self.back_lab_partition_grille_position_joueur[y][x]) :
                count = 1
                for el in self.back_lab_partition_grille_position_joueur :
                    for i in el :
                        if i :
                            count += 1
                self.Partitions_lab = [self.back_lab_partition_grille[y][x]]
                lab_xx = len(self.back_lab_partition_grille_position_joueur[0])
                lab_yy = len(self.back_lab_partition_grille_position_joueur)
                if count > round(lab_xx * lab_yy / (self.big_boss.difficultee.numero + 1)) :
                    self.back_lab_partition_grille_position_joueur = []
                    for i in range (lab_yy) :
                        a = []
                        for e in range (lab_xx) :
                            a.append(False)
                        self.back_lab_partition_grille_position_joueur.append(a)
                    self.canvas.refresh_lab ()
                self.back_lab_partition_grille_position_joueur[y][x] = True
                self.canvas.trace_grille()
            elif self.big_boss.niveau.numero == 3 :
                self.back_lab_partition_grille_position_joueur[self.position_joueur_back_lab_y][self.position_joueur_back_lab_x] = False
                self.back_lab_partition_grille_position_joueur[y][x] = True
                self.Partitions_lab = [self.back_lab_partition_grille[y][x]]
                self.canvas.refresh_lab ()
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
        #cases_contact_ext_list = []
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
                if (pos_x, pos_y-1) not in cases_visitées and pos_y > 0 :
                    a.append("N")
                if (pos_x, pos_y+1) not in cases_visitées and pos_y < y-1 :
                    a.append("S")
                if (pos_x+1, pos_y) not in cases_visitées and pos_x < x-1 :
                    a.append("E")
                if (pos_x-1, pos_y) not in cases_visitées and pos_x > 0 :
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
            if nom is None :
                return
            else :
                self.save_as (nom, self.lab, self.entrée_lab, self.sortie_lab)
                fichier_nom_labs_alea = open("Labyrinthes aléatoires enregistrés/Noms labyrinthes aléatoires","a")
                fichier_nom_labs_alea.write("Labyrinthe "+nom+"\n")
                fichier_nom_labs_alea.close()
                messagebox.showinfo ('Labyrinthe aléatoire enregistré','Le Labyrinthe aléatoire actuel à bien été enregisté sous le nom : Labyrinthe '+nom+' !')
    
    def test_nb_murs_niv_4 (self) :
        if self.big_boss.difficultee.numero == 1 :
            limite = self.nb_murs_dans_lab / 2
            message = "la moitié"
        elif self.big_boss.difficultee.numero == 2 :
            limite = self.nb_murs_dans_lab /5
            message = "1/5"
        elif self.big_boss.difficultee.numero == 3 :
            limite = self.nb_murs_dans_lab /10
            message = "1/10"
        if len(self.Murs_lab) >= limite :
            self.Murs_lab = []
            messagebox.showinfo ("Dommage !","Vous avez découvert plus de "+message+" des murs, ils vont donc tous disparaître !", icon = "error")
            self.canvas.refresh_lab ()
        return
    
    def reglages_lab_alea (self) :
        return
