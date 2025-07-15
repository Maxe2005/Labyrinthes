
class Lab_grille_crea () :
    def __init__(self, big_boss, fenetre, x=10, y=10) :
        self.big_boss = big_boss
        self.fenetre = fenetre
        self.Entree = "off"
        self.Sortie = "off"
        self.coutours_compris_dans_detruire_aire = False
        self.coutours_compris_dans_restorer_aire = False
        self.init_lab(x,y)
    
    def init_entitees (self, canvas, balle) :
        self.canvas = canvas
        self.balle = balle
    
    def init_lab (self, x,y, nom_lab:str = "<sans-nom>") :
        """
        Initialise le labirinthe à afficher
        """
        self.lab = self.grille_pleine (x,y)
        self.big_boss.lab_name = nom_lab
        self.x = x
        self.y = y
        
    def ouvrir_lab (self, nom_du_lab) :
        nom = "Labyrinthes_croquis/Croquis__"+nom_du_lab+".csv"
        try :
            fichier = open (nom, "r")
        except :  
            return "fichier introuvable"
        else :
            table = []
            count = 1
            for ligne in fichier :
                ligne = ligne.rstrip()
                tab = ligne.split(",")
                if count != 3 :
                    if count == 1 :
                        if tab == ["o","f","f"] :
                            self.Entree = "off"
                            self.fenetre.position_entree.set("Entrée")
                        else :
                            self.Entree = [int(tab[0]), int(tab[1])]
                            self.fenetre.position_entree.set("Entrée : {};{}".format(self.Entree[0],self.Entree[1]))
                    elif count == 2 :
                        if tab == ["o","f","f"] :
                            self.Sortie = "off"
                            self.fenetre.position_entree.set("Sortie")
                        else :
                            self.Sortie = [int(tab[0]), int(tab[1])]
                            self.fenetre.position_sortie.set("Sortie : {};{}".format(self.Sortie[0],self.Sortie[1]))
                    count += 1
                else :
                    table.append(tab)
            fichier.close()
            self.big_boss.lab_name = nom_du_lab
            self.lab = table
            return
        
    def grille_pleine (self, x:int ,y:int) :
        """
        Crée une grille sans trous
        :param x: (int) le nombre de cases en largeur
        :param y: (int) le nombre de cases en hauteur
        """
        assert x > 0 and y > 0
        g = []
        for i in range (y) :
            g.append(["3"]*x+["2"])
        g.append(["1"]*x+["0"])
        return g

    def inser_grille (self) :
        """
        Permet d'entrer une grille de labirinte (codé en 0,1,2,3) depuis la console
        """
        g = []
        count = 1
        while count != "fin" :
            a = input("Inserez la ligne n°"+str(count)+" de votre labirinthe ")
            if a != "fin" :
                if count == 1 :
                    t = len(a)
                if len(a) == t :
                    g.append(a)
                    count += 1
                else :
                    print ("Il y a une erreur dans la longueur de votre ligne, elle n'a pas la même longueur que la précédente !")
            else :
                count = "fin"
        return g

    def save_as (self, nom_du_lab, croquis, lab, entrée, sortie) :
        if croquis:
            nom = "Labyrinthes_croquis/Croquis__"+nom_du_lab+".csv"
            if not(path.exists(nom)) :
                with open("Labyrinthes_croquis/#_Doc_index.csv", "a") as d :
                    d.write(nom_du_lab+"\n")
        else :
            nom = "Labyrinthes_creation/Labyrinthe__"+nom_du_lab+".csv"
            if not(path.exists(nom)) :
                with open("Labyrinthes_creation/#_Doc_index.csv", "a") as d :
                    d.write(nom_du_lab+"\n")
        with open (nom, "w", newline = "") as f :
            for i in range (-2,len(lab)) :
                ecrire = writer (f, delimiter = ",", lineterminator = "\n")
                if i == -2 :
                    ecrire.writerow (entrée)
                elif i == -1 :
                    ecrire.writerow (sortie)
                else :
                    ecrire.writerow (lab[i])

    def detruire_aire (self, x1, y1, x2, y2) :
        if x1 > x2 :
            x1, x2 = x2, x1
        if y1 > y2 :
            y1, y2 = y2, y1
        if not(self.coutours_compris_dans_detruire_aire) :
            x1 += 1
            y1 += 1
        for y in range(y1, y2+1) :
            for x in range(x1, x2+1) :
                self.lab[y][x] = "0"
        if self.coutours_compris_dans_detruire_aire :
            if y2 + 1 < self.y :
                for x in range (x1, x2+1) :
                    if self.lab[y2+1][x] == "3" :
                        self.lab[y2+1][x] = "2"
                    elif self.lab[y2+1][x] == "1" :
                        self.lab[y2+1][x] = "0"
            if x2 + 1 < self.x :
                for y in range (y1, y2+1) :
                    if self.lab[y][x2+1] == "3" :
                        self.lab[y][x2+1] = "1"
                    elif self.lab[y][x2+1] == "2" :
                        self.lab[y][x2+1] = "0"
        else :
            for x in range (x1, x2+1) :
                if self.lab[y1-1][x] == "3" :
                    self.lab[y1-1][x] = "1"
                elif self.lab[y1-1][x] == "2" :
                    self.lab[y1-1][x] = "0"
            for y in range (y1, y2+1) :
                if self.lab[y][x1-1] == "3" :
                    self.lab[y][x1-1] = "2"
                elif self.lab[y][x1-1] == "1" :
                    self.lab[y][x1-1] = "0"
    
    def restorer_aire (self, x1, y1, x2, y2) :
        if x1 > x2 :
            x1, x2 = x2, x1
        if y1 > y2 :
            y1, y2 = y2, y1
        if not(self.coutours_compris_dans_restorer_aire) :
            y1 += 1
            x1 += 1
        for y in range(y1, y2+1) :
            for x in range(x1, x2+1) :
                self.lab[y][x] = "3"
        if self.coutours_compris_dans_restorer_aire :
            for x in range (x1, x2+1) :
                if self.lab[y2+1][x] == "0" :
                    self.lab[y2+1][x] = "1"
                elif self.lab[y2+1][x] == "2" :
                    self.lab[y2+1][x] = "3"
            for y in range (y1, y2+1) :
                if self.lab[y][x2+1] == "0" :
                    self.lab[y][x2+1] = "2"
                elif self.lab[y][x2+1] == "1" :
                    self.lab[y][x2+1] = "3"
        else :
            for x in range (x1, x2+1) :
                if self.lab[y1-1][x] == "0" :
                    self.lab[y1-1][x] = "2"
                elif self.lab[y1-1][x] == "1" :
                    self.lab[y1-1][x] = "3"
            for y in range (y1, y2+1) :
                if self.lab[y][x1-1] == "0" :
                    self.lab[y][x1-1] = "1"
                elif self.lab[y][x1-1] == "2" :
                    self.lab[y][x1-1] = "3"

